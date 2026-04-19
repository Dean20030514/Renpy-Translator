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
