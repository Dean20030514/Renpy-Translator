#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Translation state tests — ProgressTracker (cleanup / resume / normalize / concurrent flush / write ordering), TranslationDB (roundtrip / concurrent upsert / atomic save / line=0), deduplicate_translations, match_string_entry_fallback, progress bar rendering, review HTML integration.

Split from the monolithic ``tests/test_all.py`` in round 29; every test
function is copied byte-identical from its original location so test
behaviour is preserved.  Run standalone via ``python tests/test_translation_state.py``
or collectively via ``python tests/test_all.py`` (which delegates to
``run_all()`` in each split module).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import api_client
import file_processor
from core import glossary
from core import prompts

def test_progress_cleanup():
    """测试进度文件 results 清理"""
    import tempfile, os
    from core.translation_utils import ProgressTracker
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        p = ProgressTracker(Path(tmp) / "progress.json")
        p.mark_chunk_done("test.rpy", 1, [{"line": 1, "original": "hi", "zh": "你好"}])
        assert "test.rpy" in p.data.get("results", {})
        p.mark_file_done("test.rpy")
        # results 应该被清理
        assert "test.rpy" not in p.data.get("results", {})
        assert "test.rpy" in p.data["completed_files"]
        print("[OK] progress cleanup")


def test_progress_resume():
    """T43: ProgressTracker 写入后重载，数据一致"""
    import tempfile, os
    from pathlib import Path
    from core.translation_utils import ProgressTracker
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        tmp_path = f.name
    try:
        p = ProgressTracker(Path(tmp_path))
        p.mark_chunk_done("test.rpy", 1, [{"line": 1, "zh": "你好"}])
        p.save()  # 强制刷盘

        p2 = ProgressTracker(Path(tmp_path))
        assert p2.is_chunk_done("test.rpy", 1)
        assert not p2.is_chunk_done("test.rpy", 2)
        print("[OK] progress_resume")
    finally:
        os.unlink(tmp_path)


def test_progress_normalize():
    """T44: 加载损坏/缺key的 progress.json 不崩溃"""
    import tempfile, os
    from pathlib import Path
    from core.translation_utils import ProgressTracker
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode='w') as f:
        f.write('{"completed_files": ["a.rpy"]}')  # 缺 completed_chunks 和 stats
        tmp_path = f.name
    try:
        p = ProgressTracker(Path(tmp_path))
        assert "a.rpy" in p.data["completed_files"]
        assert "completed_chunks" in p.data
        assert "stats" in p.data
        print("[OK] progress_normalize")
    finally:
        os.unlink(tmp_path)


def test_deduplicate_translations():
    """T48: _deduplicate_translations 去重"""
    from core.translation_utils import _deduplicate_translations
    items = [
        {"line": 1, "original": "Hello", "zh": "你好"},
        {"line": 1, "original": "Hello", "zh": "你好啊"},  # 重复 key
        {"line": 2, "original": "World", "zh": "世界"},
    ]
    result = _deduplicate_translations(items)
    assert len(result) == 2
    assert result[0]["zh"] == "你好"  # 保留首次
    # 空列表
    assert _deduplicate_translations([]) == []
    print("[OK] deduplicate_translations")


def test_match_string_entry_fallback():
    """T49: _match_string_entry_fallback 五层 fallback (round 31 Tier A-3 adds L5)"""
    from core.translation_utils import _match_string_entry_fallback, _build_fallback_dicts
    ft = {
        "Save Game": "保存游戏",
        "  Load Game  ": "读取存档",
        '__RENPY_PH_0__ Settings': "设置",
        'He said \\"hello\\"': "他说了你好",
        # Round 31 Tier A-3: tag-wrapped variant for the L5 fallback test
        "{b}Bold Warning{/b}": "加粗警告",
    }
    ft_stripped, ft_clean, ft_norm, ft_tagstripped = _build_fallback_dicts(ft)

    # L1: 精确匹配
    zh, level = _match_string_entry_fallback("Save Game", ft, ft_stripped, ft_clean, ft_norm, ft_tagstripped)
    assert zh == "保存游戏" and level == 0

    # L2: strip 匹配
    zh, level = _match_string_entry_fallback("Load Game", ft, ft_stripped, ft_clean, ft_norm, ft_tagstripped)
    assert zh == "读取存档" and level == 2

    # L3: 去占位符匹配
    zh, level = _match_string_entry_fallback("Settings", ft, ft_stripped, ft_clean, ft_norm, ft_tagstripped)
    assert zh == "设置" and level == 3

    # L4: 转义规范化匹配
    zh, level = _match_string_entry_fallback('He said "hello"', ft, ft_stripped, ft_clean, ft_norm, ft_tagstripped)
    assert zh == "他说了你好" and level == 4

    # L5 (round 31 Tier A-3): tag-stripped匹配 — lookup key lost the {b}/{/b} wrappers.
    zh, level = _match_string_entry_fallback(
        "Bold Warning", ft, ft_stripped, ft_clean, ft_norm, ft_tagstripped,
    )
    assert zh == "加粗警告" and level == 5, f"L5 tag-strip failed: zh={zh!r}, level={level}"

    # Backward compat: calling without the 4th dict (pre-round-31 shape) must still work.
    zh, level = _match_string_entry_fallback("Save Game", ft, ft_stripped, ft_clean, ft_norm)
    assert zh == "保存游戏" and level == 0, "pre-round-31 call shape broke"

    # 无匹配
    zh, level = _match_string_entry_fallback("Unknown", ft, ft_stripped, ft_clean, ft_norm, ft_tagstripped)
    assert zh is None and level == 0
    print("[OK] match_string_entry_fallback")


def test_progress_bar_render():
    """ProgressBar 渲染不崩溃（含 ASCII fallback）"""
    from core.translation_utils import ProgressBar
    bar = ProgressBar(total=10, width=20)
    bar.update(3, cost=0.5)
    bar.update(7, cost=1.2)
    bar.finish()
    assert bar.current == 10
    assert bar.cost == 1.7
    print("[OK] progress_bar_render")


def test_progress_concurrent_flush():
    """Concurrent ``mark_chunk_done`` across workers must not deadlock or lose chunks.

    Round 21 (P-H-2) moved disk I/O out of the main data lock. This test
    exercises 4 threads × 50 marks each, then verifies every chunk is
    present after ``save()``. A deadlock in the new two-lock scheme would
    cause this test to hang past the join timeout.
    """
    import threading
    import tempfile
    from pathlib import Path
    from core.translation_utils import ProgressTracker

    with tempfile.TemporaryDirectory() as td:
        pt = ProgressTracker(Path(td) / "progress.json")

        def worker(thread_id: int) -> None:
            for i in range(50):
                pt.mark_chunk_done(
                    f"file_{thread_id}.rpy",
                    i,
                    [{"original": f"x{i}", "zh": f"y{i}"}],
                )

        threads = [threading.Thread(target=worker, args=(tid,)) for tid in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=15)

        for t in threads:
            assert not t.is_alive(), "ProgressTracker deadlock: thread still alive after 15s"

        pt.save()

        for tid in range(4):
            chunks = pt.data["completed_chunks"][f"file_{tid}.rpy"]
            assert sorted(chunks) == list(range(50)), (
                f"file_{tid}.rpy missing chunks (got {len(chunks)}/50): {chunks}"
            )
    print("[OK] test_progress_concurrent_flush")


def test_progress_write_ordering_monotonic():
    """Disk writes under concurrent flushing must be monotonically non-decreasing.

    Locks down the round 22 P1 fix: before the fix, ``_flush_to_disk`` took the
    data lock for the snapshot and then **released it** before acquiring
    ``_save_lock`` — so two threads could each snapshot independently and then
    race into the save lock, with the slower-to-write one clobbering the fresher
    snapshot. After the fix, ``_save_lock`` wraps the ``_lock`` + snapshot +
    write sequence atomically, guaranteeing the on-disk state never regresses.
    """
    import threading
    import tempfile
    import json as _json
    from pathlib import Path
    from core.translation_utils import ProgressTracker

    writes_sizes: list[int] = []
    writes_sizes_lock = threading.Lock()

    with tempfile.TemporaryDirectory() as td:
        pt = ProgressTracker(Path(td) / "progress.json")

        real_write = pt._write_atomic

        def spy_write(json_str: str) -> None:
            data = _json.loads(json_str)
            total_chunks = sum(
                len(c) for c in data.get("completed_chunks", {}).values()
            )
            with writes_sizes_lock:
                writes_sizes.append(total_chunks)
            real_write(json_str)

        pt._write_atomic = spy_write

        def worker(tid: int) -> None:
            for i in range(30):
                pt.mark_chunk_done(f"file_{tid}.rpy", i, [])

        threads = [threading.Thread(target=worker, args=(tid,)) for tid in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=15)

        assert len(writes_sizes) >= 3, (
            f"expected at least 3 flushes across 180 marks, got {len(writes_sizes)}"
        )
        for i in range(1, len(writes_sizes)):
            assert writes_sizes[i] >= writes_sizes[i - 1], (
                f"non-monotonic write at index {i}: "
                f"writes_sizes[{i - 1}]={writes_sizes[i - 1]} > "
                f"writes_sizes[{i}]={writes_sizes[i]} — snapshot ordering violated"
            )
    print("[OK] test_progress_write_ordering_monotonic")


# ============================================================
# HTTP connection pool tests (round 21 — PF-C-1)
# ============================================================

def test_translation_db_roundtrip():
    """T10: TranslationDB save/load 往返 + upsert 去重"""
    import tempfile, os
    from pathlib import Path
    from core.translation_db import TranslationDB
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        tmp_path = f.name
    try:
        db = TranslationDB(Path(tmp_path))
        entries = [
            {"file": "test.rpy", "line": 1, "original": "Hello", "translation": "你好", "status": "ok"},
            {"file": "test.rpy", "line": 2, "original": "World", "translation": "世界", "status": "ok"},
        ]
        db.add_entries(entries)
        assert len(db.entries) == 2
        db.save()

        # Reload
        db2 = TranslationDB(Path(tmp_path))
        db2.load()
        assert len(db2.entries) == 2

        # Upsert：相同 file+line 应更新
        db2.add_entries([
            {"file": "test.rpy", "line": 1, "original": "Hello", "translation": "你好啊", "status": "ok"},
        ])
        assert len(db2.entries) == 2  # 不应增加
        print("[OK] translation_db_roundtrip")
    finally:
        os.unlink(tmp_path)


def test_translation_db_concurrent_upsert():
    """``TranslationDB.upsert_entry`` must be safe under concurrent access.

    Round 26 C-1: with ``threading.RLock`` added, 32 worker threads each
    inserting 100 unique entries must converge to 3200 distinct entries
    with the index intact (no lost updates, no index corruption).
    """
    import tempfile
    import threading
    from pathlib import Path
    from core.translation_db import TranslationDB

    with tempfile.TemporaryDirectory() as td:
        db = TranslationDB(Path(td) / "db.json")

        n_threads = 32
        per_thread = 100
        barrier = threading.Barrier(n_threads)

        def worker(tid: int) -> None:
            barrier.wait()
            for i in range(per_thread):
                db.upsert_entry({
                    "file": f"file_{tid}.rpy",
                    "line": i + 1,
                    "original": f"text_{tid}_{i}",
                    "translation": f"trans_{tid}_{i}",
                    "status": "ok",
                })

        threads = [threading.Thread(target=worker, args=(tid,)) for tid in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        expected = n_threads * per_thread
        assert len(db.entries) == expected, (
            f"expected {expected} entries, got {len(db.entries)} (race condition?)"
        )
        # Every (file, line, original) must be looked up via has_entry.
        for tid in range(n_threads):
            for i in range(per_thread):
                assert db.has_entry(f"file_{tid}.rpy", i + 1, f"text_{tid}_{i}"), (
                    f"missing entry ({tid}, {i})"
                )
        # Index and entries must be consistent.
        assert len(db._index) == expected, (
            f"index size {len(db._index)} != entries size {expected}"
        )
    print("[OK] test_translation_db_concurrent_upsert")


def test_translation_db_save_atomic():
    """``TranslationDB.save`` must not corrupt an existing on-disk DB when the
    atomic replace step fails mid-way (round 26 C-2).
    """
    import json as _json
    import os as _os
    import tempfile
    from pathlib import Path
    from core.translation_db import TranslationDB

    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "db.json"
        db = TranslationDB(db_path)
        db.upsert_entry({
            "file": "a.rpy", "line": 1, "original": "hello",
            "translation": "你好", "status": "ok",
        })
        db.save()  # writes a valid DB

        # Snapshot original bytes for later compare.
        original_bytes = db_path.read_bytes()

        # Add a second entry and force save to fail at os.replace.
        db.upsert_entry({
            "file": "b.rpy", "line": 2, "original": "world",
            "translation": "世界", "status": "ok",
        })

        real_replace = _os.replace
        calls = {"n": 0}

        def broken_replace(src, dst):  # noqa: ANN001
            calls["n"] += 1
            raise OSError("simulated replace failure")

        _os.replace = broken_replace
        try:
            raised = False
            try:
                db.save()
            except OSError:
                raised = True
            assert raised, "save() should propagate OSError when os.replace fails"
        finally:
            _os.replace = real_replace

        # Original DB file content must be unchanged.
        assert db_path.read_bytes() == original_bytes, (
            "db.json content changed after failed atomic save"
        )
        # The temp file should have been cleaned up.
        tmp_path = db_path.with_suffix(db_path.suffix + ".tmp")
        assert not tmp_path.exists(), f"stale temp file remains: {tmp_path}"

        # The on-disk JSON must still be valid with a single entry.
        persisted = _json.loads(db_path.read_text(encoding="utf-8"))
        assert len(persisted["entries"]) == 1, (
            f"expected 1 persisted entry, got {len(persisted['entries'])}"
        )
    print("[OK] test_translation_db_save_atomic")


def test_translation_db_accepts_line_zero():
    """``line=0`` is a legitimate placeholder (generic engines use it for
    formats without meaningful line numbers); it must no longer be silently
    dropped (round 26 C-3).
    """
    import tempfile
    from pathlib import Path
    from core.translation_db import TranslationDB

    with tempfile.TemporaryDirectory() as td:
        db = TranslationDB(Path(td) / "db.json")
        db.upsert_entry({
            "file": "generic.csv", "line": 0,
            "original": "Hello, world!",
            "translation": "你好，世界！",
            "status": "ok",
        })
        assert db.has_entry("generic.csv", 0, "Hello, world!"), (
            "entry with line=0 must be stored and retrievable"
        )
        results = db.filter_by_status(statuses=["ok"])
        assert any(e["file"] == "generic.csv" and e["line"] == 0 for e in results), (
            "filter_by_status should include line=0 entries"
        )
        # Round-trip through save/load.
        db.save()
        db2 = TranslationDB(Path(td) / "db.json")
        db2.load()
        assert db2.has_entry("generic.csv", 0, "Hello, world!"), (
            "line=0 entry must survive save/load round-trip"
        )
    print("[OK] test_translation_db_accepts_line_zero")


def test_review_generator_html():
    """review_generator 生成 HTML 不崩溃"""
    from tools.review_generator import generate_review_html
    from pathlib import Path as _Path
    import tempfile, json, os
    # 创建临时 translation_db
    tmpdir = tempfile.mkdtemp()
    db_path = _Path(tmpdir) / "test_db.json"
    db_path.write_text(json.dumps({
        "version": 1,
        "entries": [
            {"file": "test.rpy", "line": 1, "original": "Hello", "translation": "你好",
             "status": "ok", "error_codes": [], "warning_codes": []},
            {"file": "test.rpy", "line": 2, "original": "World", "translation": "世界",
             "status": "warning", "error_codes": [], "warning_codes": ["W430"]},
        ]
    }), encoding="utf-8")
    out_path = _Path(tmpdir) / "review.html"
    try:
        count = generate_review_html(db_path, out_path)
        assert count == 2
        html_content = out_path.read_text(encoding="utf-8")
        assert "Hello" in html_content
        assert "W430" in html_content
        assert "test.rpy" in html_content
        print("[OK] review_generator_html")
    finally:
        db_path.unlink(missing_ok=True)
        out_path.unlink(missing_ok=True)
        os.rmdir(tmpdir)


def test_runtime_hook_emit_builds_map_and_copies_template():
    """Round 31 Tier C: ``emit_runtime_hook`` writes a sorted JSON map and
    copies the hook .rpy; only ``status == 'ok'`` entries contribute.
    """
    import json as _json
    import tempfile
    from pathlib import Path
    from core.runtime_hook_emitter import emit_runtime_hook

    with tempfile.TemporaryDirectory() as td:
        out_game = Path(td) / "game"
        entries = [
            {"file": "a.rpy", "line": 1, "original": "Hello", "translation": "你好", "status": "ok"},
            {"file": "a.rpy", "line": 2, "original": "World", "translation": "世界", "status": "ok"},
            # status != "ok" must be filtered out
            {"file": "a.rpy", "line": 3, "original": "Fail",  "translation": "",    "status": "dropped"},
            # missing translation must be filtered
            {"file": "a.rpy", "line": 4, "original": "Empty", "translation": "",    "status": "ok"},
            # duplicate original keeps first
            {"file": "b.rpy", "line": 1, "original": "Hello", "translation": "别的", "status": "ok"},
        ]

        json_path, hook_path, count = emit_runtime_hook(out_game, entries)

        assert count == 2, f"expected 2 unique ok entries, got {count}"
        assert json_path.exists() and hook_path.exists()

        # JSON content: sorted keys, Unicode preserved, dedup kept first.
        loaded = _json.loads(json_path.read_text(encoding="utf-8"))
        assert loaded == {"Hello": "你好", "World": "世界"}, f"unexpected map: {loaded!r}"

        # Hook file is a verbatim copy of the template — check a sentinel
        # comment from the template header.
        hook_content = hook_path.read_text(encoding="utf-8")
        assert "Inject Hook" in hook_content
        assert "RENPY_TL_INJECT" in hook_content
        assert "_tl_lookup" in hook_content
    print("[OK] runtime_hook_emit_builds_map_and_copies_template")


def test_runtime_hook_emit_if_requested_respects_flag():
    """Round 31 Tier C: ``emit_if_requested`` is a no-op unless the
    argparse namespace has ``emit_runtime_hook=True``.
    """
    import tempfile
    from pathlib import Path
    from types import SimpleNamespace
    from core.runtime_hook_emitter import emit_if_requested
    from core.translation_db import TranslationDB

    with tempfile.TemporaryDirectory() as td:
        out_dir = Path(td)
        db = TranslationDB(out_dir / "translation_db.json")
        db.upsert_entry({
            "file": "a.rpy", "line": 1, "original": "Hello",
            "translation": "你好", "status": "ok",
        })

        # Flag off → no files emitted.
        args_off = SimpleNamespace(emit_runtime_hook=False)
        emit_if_requested(args_off, out_dir, db)
        assert not (out_dir / "game" / "translations.json").exists()
        assert not (out_dir / "game" / "zz_tl_inject_hook.rpy").exists()

        # Flag missing entirely → still no-op.
        args_none = SimpleNamespace()
        emit_if_requested(args_none, out_dir, db)
        assert not (out_dir / "game" / "translations.json").exists()

        # Flag on → emit.
        args_on = SimpleNamespace(emit_runtime_hook=True)
        emit_if_requested(args_on, out_dir, db)
        assert (out_dir / "game" / "translations.json").exists()
        assert (out_dir / "game" / "zz_tl_inject_hook.rpy").exists()
    print("[OK] runtime_hook_emit_if_requested_respects_flag")


def test_emit_runtime_hook_writes_ui_sidecar_when_extensions_set():
    """Round 32 Subtask A: ``emit_runtime_hook`` writes a sidecar
    ``ui_button_whitelist.json`` next to ``translations.json`` when
    ``ui_button_extensions`` is non-empty.  File has canonical
    ``{"extensions": [...]}`` shape with sorted tokens.
    """
    import json as _json
    import tempfile
    from pathlib import Path
    from core.runtime_hook_emitter import emit_runtime_hook

    entries = [{
        "file": "a.rpy", "line": 1, "original": "Hello",
        "translation": "你好", "status": "ok",
    }]

    with tempfile.TemporaryDirectory() as td:
        out_game = Path(td) / "game"
        # Deliberately mixed-case / whitespace: emitter must pass through the
        # already-normalised tokens verbatim (the normalisation happens on
        # the Python-side ``add_ui_button_whitelist`` path before we get here).
        emit_runtime_hook(
            out_game, entries,
            ui_button_extensions=["存档", "读档", "main hub"],
        )
        sidecar = out_game / "ui_button_whitelist.json"
        assert sidecar.is_file(), "sidecar ui_button_whitelist.json must be emitted"
        data = _json.loads(sidecar.read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        assert "extensions" in data
        # Sorted for stable diffs.
        assert data["extensions"] == sorted(["存档", "读档", "main hub"])
        # Primary translations.json + hook still emitted.
        assert (out_game / "translations.json").is_file()
        assert (out_game / "zz_tl_inject_hook.rpy").is_file()
    print("[OK] emit_runtime_hook_writes_ui_sidecar_when_extensions_set")


def test_emit_runtime_hook_skips_ui_sidecar_when_empty():
    """Round 32 Subtask A: empty / None ``ui_button_extensions`` must NOT
    create a sidecar file — default output stays byte-compatible with
    round 31 (translations.json + hook only).
    """
    import tempfile
    from pathlib import Path
    from core.runtime_hook_emitter import emit_runtime_hook

    entries = [{
        "file": "a.rpy", "line": 1, "original": "Hello",
        "translation": "你好", "status": "ok",
    }]

    for ext in (None, [], (), frozenset(), {""}):
        with tempfile.TemporaryDirectory() as td:
            out_game = Path(td) / "game"
            emit_runtime_hook(out_game, entries, ui_button_extensions=ext)
            assert not (out_game / "ui_button_whitelist.json").exists(), (
                f"sidecar must not be created for ui_button_extensions={ext!r}"
            )
            # But translations.json + hook still get emitted.
            assert (out_game / "translations.json").is_file()
            assert (out_game / "zz_tl_inject_hook.rpy").is_file()
    print("[OK] emit_runtime_hook_skips_ui_sidecar_when_empty")


def test_emit_runtime_hook_copies_font_when_path_given():
    """Round 32 Subtask B: ``emit_runtime_hook`` with a valid ``font_path``
    copies the font to ``<output_game>/fonts/tl_inject.ttf`` with bytes
    identical to the source.
    """
    import tempfile
    from pathlib import Path
    from core.runtime_hook_emitter import emit_runtime_hook

    entries = [{
        "file": "a.rpy", "line": 1, "original": "Hello",
        "translation": "你好", "status": "ok",
    }]

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        # Build a synthetic font file so the test doesn't depend on the
        # real ``resources/fonts/`` content (avoids ~10 MB I/O per run).
        fake_font = td_path / "MyFont.ttf"
        fake_font.write_bytes(b"TTF\x00MOCK-FONT-BYTES\x01\x02\x03")

        out_game = td_path / "output" / "game"
        emit_runtime_hook(out_game, entries, font_path=fake_font)

        dst = out_game / "fonts" / "tl_inject.ttf"
        assert dst.is_file(), "bundled font must land at fonts/tl_inject.ttf"
        assert dst.read_bytes() == fake_font.read_bytes()
        # Other artefacts still present.
        assert (out_game / "translations.json").is_file()
        assert (out_game / "zz_tl_inject_hook.rpy").is_file()
    print("[OK] emit_runtime_hook_copies_font_when_path_given")


def test_emit_runtime_hook_skips_font_when_none():
    """Round 32 Subtask B: ``font_path=None`` (default) and ``font_path``
    pointing at a non-existent file must NOT create the fonts directory —
    keeps round 31 default output byte-compatible.
    """
    import tempfile
    from pathlib import Path
    from core.runtime_hook_emitter import emit_runtime_hook

    entries = [{
        "file": "a.rpy", "line": 1, "original": "Hello",
        "translation": "你好", "status": "ok",
    }]

    for font in (None, Path("/does/not/exist/font.ttf")):
        with tempfile.TemporaryDirectory() as td:
            out_game = Path(td) / "game"
            emit_runtime_hook(out_game, entries, font_path=font)
            assert not (out_game / "fonts").exists(), (
                f"fonts dir must not exist for font_path={font!r}"
            )
            # Primary artefacts still present.
            assert (out_game / "translations.json").is_file()
            assert (out_game / "zz_tl_inject_hook.rpy").is_file()
    print("[OK] emit_runtime_hook_skips_font_when_none")


def test_emit_runtime_hook_font_same_file_tolerated():
    """Round 32 Subtask B: passing a ``font_path`` that happens to equal the
    destination (e.g. user re-ran the emitter against its own output) must
    not raise ``shutil.SameFileError``.
    """
    import tempfile
    from pathlib import Path
    from core.runtime_hook_emitter import emit_runtime_hook

    entries = [{
        "file": "a.rpy", "line": 1, "original": "Hello",
        "translation": "你好", "status": "ok",
    }]

    with tempfile.TemporaryDirectory() as td:
        out_game = Path(td) / "game"
        out_game.mkdir(parents=True, exist_ok=True)
        fonts_dir = out_game / "fonts"
        fonts_dir.mkdir(parents=True, exist_ok=True)
        same_file = fonts_dir / "tl_inject.ttf"
        same_file.write_bytes(b"MOCK-FONT")

        # Must not raise SameFileError; idempotent success.
        emit_runtime_hook(out_game, entries, font_path=same_file)
        assert same_file.read_bytes() == b"MOCK-FONT"
    print("[OK] emit_runtime_hook_font_same_file_tolerated")


def test_emit_if_requested_resolves_font_from_args_font_file():
    """Round 32 Subtask B: ``emit_if_requested`` resolves the font via
    ``core.font_patch.resolve_font`` (honouring ``args.font_file``) and
    forwards to the emitter so the bundled font appears in the output
    game directory even without a direct kwarg.
    """
    import tempfile
    from pathlib import Path
    from types import SimpleNamespace
    from core.runtime_hook_emitter import emit_if_requested
    from core.translation_db import TranslationDB

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        fake_font = td_path / "CustomFont.ttf"
        fake_font.write_bytes(b"TTF\x00CUSTOM\x04\x05\x06")

        db = TranslationDB(td_path / "translation_db.json")
        db.upsert_entry({
            "file": "a.rpy", "line": 1, "original": "Hello",
            "translation": "你好", "status": "ok",
        })

        args = SimpleNamespace(
            emit_runtime_hook=True,
            font_file=str(fake_font),
        )
        emit_if_requested(args, td_path, db)

        dst = td_path / "game" / "fonts" / "tl_inject.ttf"
        assert dst.is_file()
        assert dst.read_bytes() == fake_font.read_bytes()
    print("[OK] emit_if_requested_resolves_font_from_args_font_file")


def test_build_translations_map_v1_unchanged():
    """Round 32 Subtask C: default ``schema_version=1`` must return the
    identical flat ``{original: translation}`` shape round 31 produced —
    this is a regression guard against a future default-flip breaking
    existing runtime-hook deployments.
    """
    from core.runtime_hook_emitter import build_translations_map

    entries = [
        {"file": "a.rpy", "line": 1, "original": "Hello",
         "translation": "你好", "status": "ok"},
        {"file": "a.rpy", "line": 2, "original": "World",
         "translation": "世界", "status": "ok"},
        # Non-ok entries must be dropped in v1 just as before.
        {"file": "a.rpy", "line": 3, "original": "Skip me",
         "translation": "跳过", "status": "failed"},
    ]
    result = build_translations_map(entries)
    assert result == {"Hello": "你好", "World": "世界"}
    # Explicit schema_version=1 also returns flat shape.
    assert build_translations_map(entries, schema_version=1) == result
    print("[OK] build_translations_map_v1_unchanged")


def test_build_translations_map_v2_structure():
    """Round 32 Subtask C: ``schema_version=2`` wraps the translations in
    the documented envelope with ``_schema_version``, ``_format``,
    ``default_lang``, and a ``translations`` nested dict.
    """
    from core.runtime_hook_emitter import build_translations_map

    entries = [
        {"file": "a.rpy", "line": 1, "original": "Hello",
         "translation": "你好", "status": "ok"},
        {"file": "a.rpy", "line": 2, "original": "World",
         "translation": "世界", "status": "ok"},
    ]
    v2 = build_translations_map(entries, schema_version=2)

    assert isinstance(v2, dict)
    assert v2.get("_schema_version") == 2
    assert v2.get("_format") == "renpy-translate"
    # Default target_lang kwarg is "zh".
    assert v2.get("default_lang") == "zh"
    nested = v2.get("translations")
    assert isinstance(nested, dict)
    assert nested == {"Hello": {"zh": "你好"}, "World": {"zh": "世界"}}

    # Invalid schema_version raises.
    import pytest  # noqa: F401 — only used to document intent; we call directly
    raised = False
    try:
        build_translations_map(entries, schema_version=3)
    except ValueError:
        raised = True
    assert raised, "schema_version=3 must raise ValueError"
    print("[OK] build_translations_map_v2_structure")


def test_build_translations_map_v2_respects_target_lang():
    """Round 32 Subtask C: v2 key within each bucket + ``default_lang`` are
    driven by the caller's ``target_lang`` argument.
    """
    from core.runtime_hook_emitter import build_translations_map

    entries = [
        {"file": "a.rpy", "line": 1, "original": "Hello",
         "translation": "こんにちは", "status": "ok"},
    ]
    v2 = build_translations_map(entries, target_lang="ja", schema_version=2)

    assert v2.get("default_lang") == "ja"
    assert v2.get("translations") == {"Hello": {"ja": "こんにちは"}}

    # Also try zh-tw to confirm arbitrary BCP-47 tags pass through.
    v2_tw = build_translations_map(entries, target_lang="zh-tw", schema_version=2)
    assert v2_tw.get("default_lang") == "zh-tw"
    assert v2_tw.get("translations") == {"Hello": {"zh-tw": "こんにちは"}}
    print("[OK] build_translations_map_v2_respects_target_lang")


def test_build_translations_map_v2_empty_entries():
    """Round 32 Subtask C: v2 envelope with zero input entries still has a
    valid structure — ``translations`` is an empty dict, not missing.
    Important so hook-side type checks (``isinstance(..., dict)``) succeed
    on the empty-translation-db edge case.
    """
    from core.runtime_hook_emitter import build_translations_map

    v2 = build_translations_map([], schema_version=2)
    assert v2.get("_schema_version") == 2
    assert v2.get("_format") == "renpy-translate"
    assert v2.get("default_lang") == "zh"
    assert v2.get("translations") == {}
    print("[OK] build_translations_map_v2_empty_entries")


def test_emit_runtime_hook_v2_schema_kwarg_produces_nested_json():
    """Round 32 Subtask C: ``emit_runtime_hook(schema_version=2)`` writes
    the envelope to ``translations.json``; the file round-trips through
    ``json.loads`` as a dict with the expected keys.
    """
    import json as _json
    import tempfile
    from pathlib import Path
    from core.runtime_hook_emitter import emit_runtime_hook

    entries = [
        {"file": "a.rpy", "line": 1, "original": "Hello",
         "translation": "你好", "status": "ok"},
    ]
    with tempfile.TemporaryDirectory() as td:
        out_game = Path(td) / "game"
        _, _, count = emit_runtime_hook(
            out_game, entries,
            schema_version=2, target_lang="zh",
        )
        # entry_count reflects translations count, not envelope keys.
        assert count == 1

        loaded = _json.loads((out_game / "translations.json").read_text(encoding="utf-8"))
        assert loaded.get("_schema_version") == 2
        assert loaded.get("default_lang") == "zh"
        assert loaded.get("translations") == {"Hello": {"zh": "你好"}}
    print("[OK] emit_runtime_hook_v2_schema_kwarg_produces_nested_json")


def test_emit_if_requested_respects_runtime_hook_schema_flag():
    """Round 32 Subtask C: ``emit_if_requested`` reads
    ``args.runtime_hook_schema`` ("v1" or "v2") and routes to the
    corresponding schema.  Missing / malformed flag defaults to v1.
    """
    import json as _json
    import tempfile
    from pathlib import Path
    from types import SimpleNamespace
    from core.runtime_hook_emitter import emit_if_requested
    from core.translation_db import TranslationDB

    def _run(schema_arg, expected_schema):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            db = TranslationDB(td_path / "translation_db.json")
            db.upsert_entry({
                "file": "a.rpy", "line": 1, "original": "Hello",
                "translation": "你好", "status": "ok",
            })
            kwargs = {"emit_runtime_hook": True, "target_lang": "zh"}
            if schema_arg is not None:
                kwargs["runtime_hook_schema"] = schema_arg
            args = SimpleNamespace(**kwargs)
            emit_if_requested(args, td_path, db)
            loaded = _json.loads((td_path / "game" / "translations.json").read_text(encoding="utf-8"))
            if expected_schema == 1:
                assert loaded == {"Hello": "你好"}
            else:
                assert loaded.get("_schema_version") == 2
                assert loaded.get("translations") == {"Hello": {"zh": "你好"}}

    # Flag on → v1.
    _run("v1", 1)
    # Flag on → v2.
    _run("v2", 2)
    # Flag missing → default v1.
    _run(None, 1)
    # Unknown flag value → treated as v1 (safe fallback).
    _run("garbage", 1)
    print("[OK] emit_if_requested_respects_runtime_hook_schema_flag")


def test_inject_hook_contains_v2_reader_markers():
    """Round 32 Subtask C: structural smoke-test on the hook .rpy file.

    Ren'Py syntax (``init python early:`` blocks) is not parseable by the
    stdlib ``ast``/``py_compile`` modules, so we rely on regex markers to
    guard against future edits silently removing the v2 reader.  If this
    fails the hook file was likely edited without updating the schema
    detection branch.
    """
    import re
    from core.runtime_hook_emitter import Path as _Path  # reuse pathlib ctx
    from pathlib import Path

    hook = Path(__file__).resolve().parent.parent / "resources" / "hooks" / "inject_hook.rpy"
    content = hook.read_text(encoding="utf-8")

    required_markers = (
        "_schema_version",     # v2 detection key
        "RENPY_TL_INJECT_LANG",  # v2 env var name
        "_TL_TRANSLATIONS",    # unified lookup table
        "_tl_resolve_lang",    # runtime language picker
        "_tl_resolve_bucket",  # v2 bucket lookup
        "default_lang",        # v2 envelope key
        "_format",             # v2 envelope key
    )
    for marker in required_markers:
        assert marker in content, f"inject_hook.rpy must still reference {marker!r}"

    # env var precedence: RENPY_TL_INJECT_LANG must be consulted BEFORE
    # renpy.preferences.language (plan priority (a) > (b)).
    env_pos = content.find("RENPY_TL_INJECT_LANG")
    prefs_pos = content.find("renpy.preferences")
    assert env_pos > 0 and prefs_pos > 0
    assert env_pos < prefs_pos, (
        "RENPY_TL_INJECT_LANG check must appear before renpy.preferences "
        "lookup so the env var overrides user preferences"
    )
    print("[OK] inject_hook_contains_v2_reader_markers")


def test_emit_gui_overrides_rpy_when_font_config_has_overrides():
    """Round 33 Subtask 2: ``emit_runtime_hook(font_config=...)`` with a
    non-empty ``gui_overrides`` sub-dict produces
    ``zz_tl_inject_gui.rpy`` containing an ``init 999 python:`` block
    that assigns each override and is guarded by ``RENPY_TL_INJECT=1``.
    """
    import tempfile
    from pathlib import Path
    from core.runtime_hook_emitter import emit_runtime_hook

    entries = [{
        "file": "a.rpy", "line": 1, "original": "Hello",
        "translation": "你好", "status": "ok",
    }]
    font_config = {
        "gui_overrides": {
            "gui.text_size": 22,
            "gui.name_text_size": 24,
            "gui.interface_text_size": 20.5,
        }
    }

    with tempfile.TemporaryDirectory() as td:
        out_game = Path(td) / "game"
        emit_runtime_hook(out_game, entries, font_config=font_config)

        gui_rpy = out_game / "zz_tl_inject_gui.rpy"
        assert gui_rpy.is_file(), "aux gui override .rpy must be emitted"
        content = gui_rpy.read_text(encoding="utf-8")
        assert "init 999 python:" in content
        # Env var guard so deploying the file with the game is safe.
        assert 'os.environ.get("RENPY_TL_INJECT") == "1"' in content
        assert "gui.text_size = 22" in content
        assert "gui.name_text_size = 24" in content
        assert "gui.interface_text_size = 20.5" in content
        # Sorted output for stable diffs.
        idx_interface = content.find("gui.interface_text_size")
        idx_name = content.find("gui.name_text_size")
        idx_text = content.find("gui.text_size")
        assert 0 < idx_interface < idx_name < idx_text
        # Primary artefacts still present.
        assert (out_game / "translations.json").is_file()
        assert (out_game / "zz_tl_inject_hook.rpy").is_file()
    print("[OK] emit_gui_overrides_rpy_when_font_config_has_overrides")


def test_emit_gui_overrides_rpy_skips_when_empty():
    """Round 33 Subtask 2: empty / None / missing ``gui_overrides`` must
    NOT create the aux .rpy — default output stays byte-compatible with
    round 32 when no gui tuning is requested.
    """
    import tempfile
    from pathlib import Path
    from core.runtime_hook_emitter import emit_runtime_hook

    entries = [{
        "file": "a.rpy", "line": 1, "original": "Hello",
        "translation": "你好", "status": "ok",
    }]

    for cfg in (
        None,
        {},
        {"gui_overrides": {}},
        {"gui_overrides": None},
        {"no_gui_overrides_key": {"gui.text_size": 22}},
    ):
        with tempfile.TemporaryDirectory() as td:
            out_game = Path(td) / "game"
            emit_runtime_hook(out_game, entries, font_config=cfg)
            assert not (out_game / "zz_tl_inject_gui.rpy").exists(), (
                f"aux gui rpy must not exist for font_config={cfg!r}"
            )
            # Primary artefacts still present.
            assert (out_game / "translations.json").is_file()
            assert (out_game / "zz_tl_inject_hook.rpy").is_file()
    print("[OK] emit_gui_overrides_rpy_skips_when_empty")


def test_emit_gui_overrides_rpy_rejects_unsafe_keys():
    """Round 33 Subtask 2: keys that don't match ``^gui\\.[A-Za-z_]`` must
    be filtered out.  Guards against arbitrary-code injection via a
    malicious ``font_config.json``.
    """
    import tempfile
    from pathlib import Path
    from core.runtime_hook_emitter import emit_runtime_hook

    entries = [{
        "file": "a.rpy", "line": 1, "original": "Hello",
        "translation": "你好", "status": "ok",
    }]
    hostile_config = {
        "gui_overrides": {
            # Safe: should land in the output.
            "gui.text_size": 22,
            # Unsafe: statement injection.
            "gui.test; import os; os.system(\"echo pwn\")": 1,
            # Unsafe: not under gui.
            "import sys": 1,
            # Unsafe: expression.
            "gui.text_size + foo": 1,
            # Unsafe: empty.
            "": 99,
            # Unsafe: whitespace.
            "gui.text size": 1,
        }
    }

    with tempfile.TemporaryDirectory() as td:
        out_game = Path(td) / "game"
        emit_runtime_hook(out_game, entries, font_config=hostile_config)

        gui_rpy = out_game / "zz_tl_inject_gui.rpy"
        assert gui_rpy.is_file()
        content = gui_rpy.read_text(encoding="utf-8")
        # Only the safe key should appear.
        assert "gui.text_size = 22" in content
        # Attack vectors must NOT have leaked into the generated code.
        # (``import os`` legitimately appears in the env-guard wrapper,
        # so assert on the malicious payloads themselves.)
        assert "os.system" not in content
        assert "import sys" not in content
        assert "echo pwn" not in content
        assert "gui.text_size + foo" not in content
        assert "gui.test;" not in content  # the ``gui.test;`` injection key
        assert "gui.text size" not in content  # whitespace variant
    print("[OK] emit_gui_overrides_rpy_rejects_unsafe_keys")


def test_emit_gui_overrides_rpy_rejects_unsafe_values():
    """Round 33 Subtask 2: non-numeric values (str / list / dict / bool /
    None) must be filtered; bool is rejected even though Python's type
    system says ``isinstance(True, int)``.
    """
    import tempfile
    from pathlib import Path
    from core.runtime_hook_emitter import emit_runtime_hook

    entries = [{
        "file": "a.rpy", "line": 1, "original": "Hello",
        "translation": "你好", "status": "ok",
    }]
    mixed_config = {
        "gui_overrides": {
            "gui.text_size": 22,          # ok — int
            "gui.name_text_size": 24.0,   # ok — float
            "gui.choice_text_size": "25", # reject — str
            "gui.icon_size": [22],         # reject — list
            "gui.nvl_text_size": {"x": 22},  # reject — dict
            "gui.hide_bold": True,         # reject — bool
            "gui.hide_italic": False,      # reject — bool
            "gui.maybe_none": None,        # reject — None
        }
    }

    with tempfile.TemporaryDirectory() as td:
        out_game = Path(td) / "game"
        emit_runtime_hook(out_game, entries, font_config=mixed_config)

        content = (out_game / "zz_tl_inject_gui.rpy").read_text(encoding="utf-8")
        # Numeric values land.
        assert "gui.text_size = 22" in content
        assert "gui.name_text_size = 24.0" in content
        # Everything else is filtered out.
        assert "gui.choice_text_size" not in content
        assert "gui.icon_size" not in content
        assert "gui.nvl_text_size" not in content
        assert "gui.hide_bold" not in content
        assert "gui.hide_italic" not in content
        assert "gui.maybe_none" not in content
    print("[OK] emit_gui_overrides_rpy_rejects_unsafe_values")


def test_emit_if_requested_resolves_font_config():
    """Round 33 Subtask 2: ``emit_if_requested`` reads ``args.font_config``
    path, loads it via ``core.font_patch.load_font_config``, and forwards
    the dict to the emitter so ``zz_tl_inject_gui.rpy`` appears in output.
    """
    import json as _json
    import tempfile
    from pathlib import Path
    from types import SimpleNamespace
    from core.runtime_hook_emitter import emit_if_requested
    from core.translation_db import TranslationDB

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        # Write a minimal font_config.json with gui_overrides.
        cfg_path = td_path / "font_config.json"
        cfg_path.write_text(
            _json.dumps({"gui_overrides": {"gui.text_size": 26}}, ensure_ascii=False),
            encoding="utf-8",
        )

        db = TranslationDB(td_path / "translation_db.json")
        db.upsert_entry({
            "file": "a.rpy", "line": 1, "original": "Hello",
            "translation": "你好", "status": "ok",
        })

        args = SimpleNamespace(
            emit_runtime_hook=True,
            font_config=str(cfg_path),
            target_lang="zh",
        )
        emit_if_requested(args, td_path, db)

        gui_rpy = td_path / "game" / "zz_tl_inject_gui.rpy"
        assert gui_rpy.is_file()
        content = gui_rpy.read_text(encoding="utf-8")
        assert "gui.text_size = 26" in content

        # Absent args.font_config → no gui rpy.
        with tempfile.TemporaryDirectory() as td2:
            td2_path = Path(td2)
            db2 = TranslationDB(td2_path / "translation_db.json")
            db2.upsert_entry({
                "file": "a.rpy", "line": 1, "original": "Hi",
                "translation": "你好", "status": "ok",
            })
            args_noconfig = SimpleNamespace(
                emit_runtime_hook=True,
                font_config="",
            )
            emit_if_requested(args_noconfig, td2_path, db2)
            assert not (td2_path / "game" / "zz_tl_inject_gui.rpy").exists()
            assert (td2_path / "game" / "translations.json").is_file()
    print("[OK] emit_if_requested_resolves_font_config")


def test_default_resources_fonts_dir_points_to_project_root():
    """Round 32 Commit 1: ``default_resources_fonts_dir`` resolves to
    ``<project_root>/resources/fonts`` regardless of which caller imports it.

    Guards against the round 29 / round 32 class of bug where callers in
    subpackages used ``Path(__file__).parent`` with one too few ``.parent``
    steps and silently fell through to ``resolve_font``'s "fonts dir not
    found" warning branch on source-code runs (the bug only disappeared
    after PyInstaller bundled ``resources/`` at the expected relative path).
    """
    from core.font_patch import default_resources_fonts_dir

    fonts_dir = default_resources_fonts_dir()
    # Must be absolute so callers do not depend on process cwd.
    assert fonts_dir.is_absolute()
    # Must resolve to ``<project_root>/resources/fonts``.
    assert fonts_dir.name == "fonts"
    assert fonts_dir.parent.name == "resources"
    project_root = fonts_dir.parent.parent
    # Sanity: at project root we should see the canonical entry points.
    assert (project_root / "main.py").is_file()
    assert (project_root / "core" / "font_patch.py").is_file()
    # Directory should actually exist in a checked-out tree and contain at
    # least one bundled font (NotoSansSC-Regular.ttf per round 32 layout).
    assert fonts_dir.is_dir()
    ttf_files = list(fonts_dir.glob("*.ttf"))
    assert ttf_files, "resources/fonts/ must contain at least one .ttf"
    print("[OK] default_resources_fonts_dir_points_to_project_root")


def run_all() -> int:
    """Run every test in this module; return test count."""
    tests = [
        test_progress_cleanup,
        test_progress_resume,
        test_progress_normalize,
        test_deduplicate_translations,
        test_match_string_entry_fallback,
        test_progress_bar_render,
        test_progress_concurrent_flush,
        test_progress_write_ordering_monotonic,
        test_translation_db_roundtrip,
        test_translation_db_concurrent_upsert,
        test_translation_db_save_atomic,
        test_translation_db_accepts_line_zero,
        test_review_generator_html,
        # Round 31 Tier C (runtime-hook emitter)
        test_runtime_hook_emit_builds_map_and_copies_template,
        test_runtime_hook_emit_if_requested_respects_flag,
        # Round 32 Commit 1 (default_resources_fonts_dir helper)
        test_default_resources_fonts_dir_points_to_project_root,
        # Round 32 Commit 2 (UI whitelist sidecar)
        test_emit_runtime_hook_writes_ui_sidecar_when_extensions_set,
        test_emit_runtime_hook_skips_ui_sidecar_when_empty,
        # Round 32 Commit 3 (font auto-bundle in emit_runtime_hook)
        test_emit_runtime_hook_copies_font_when_path_given,
        test_emit_runtime_hook_skips_font_when_none,
        test_emit_runtime_hook_font_same_file_tolerated,
        test_emit_if_requested_resolves_font_from_args_font_file,
        # Round 32 Commit 4 (translations.json v2 nested schema)
        test_build_translations_map_v1_unchanged,
        test_build_translations_map_v2_structure,
        test_build_translations_map_v2_respects_target_lang,
        test_build_translations_map_v2_empty_entries,
        test_emit_runtime_hook_v2_schema_kwarg_produces_nested_json,
        test_emit_if_requested_respects_runtime_hook_schema_flag,
        test_inject_hook_contains_v2_reader_markers,
        # Round 33 Commit 2 (--font-config → zz_tl_inject_gui.rpy)
        test_emit_gui_overrides_rpy_when_font_config_has_overrides,
        test_emit_gui_overrides_rpy_skips_when_empty,
        test_emit_gui_overrides_rpy_rejects_unsafe_keys,
        test_emit_gui_overrides_rpy_rejects_unsafe_values,
        test_emit_if_requested_resolves_font_config,
    ]
    for t in tests:
        t()
    return len(tests)


if __name__ == "__main__":
    n = run_all()
    print()
    print("=" * 40)
    print(f"ALL {n} TESTS PASSED")
    print("=" * 40)
