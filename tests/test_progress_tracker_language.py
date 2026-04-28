#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ProgressTracker language-aware tests — split from
``tests/test_translation_state.py`` in round 47 Step 4 to keep both
files comfortably below the CLAUDE.md 800-line soft limit and to
isolate the multi-language ProgressTracker surface (r35 C1 + r36 H1).

Covers ``core/translation_utils.ProgressTracker`` language-aware
behaviour:

- namespace isolation (``<lang>:<rel_path>`` key partitioning)
- legacy bare-key backward compat (no language kwarg, pre-r35 shape)
- pre-r35 progress.json resume under ``language="zh"`` (the implicit
  legacy bare-key owner)
- r36 H1 cross-language bare-key pollution defense (non-zh tracker
  must not inherit zh's bare-key state, mark_file_done must not
  clean zh's bare bucket)

Tests are byte-identical to their pre-split forms in
test_translation_state.py; the extraction was a pure refactor with
no behavioural change.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_progress_tracker_language_namespace_isolation():
    """Round 35 C1: two ProgressTracker instances sharing the same
    progress.json but constructed with different ``language`` kwargs
    must NOT see each other's chunk state — each language's progress
    lives under its own ``"<lang>:<rel_path>"`` key.
    """
    import tempfile
    from pathlib import Path
    from core.translation_utils import ProgressTracker

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "progress.json"

        pt_zh = ProgressTracker(p, language="zh")
        pt_zh.mark_chunk_done("a.rpy", 1, [{"line": 1, "zh": "你好"}])
        pt_zh.save()

        pt_ja = ProgressTracker(p, language="ja")
        # ja run sees NO zh chunk state — isolated namespaces.
        assert not pt_ja.is_chunk_done("a.rpy", 1), (
            "language namespace bleed: ja run saw zh's completed chunk"
        )
        pt_ja.mark_chunk_done("a.rpy", 1, [{"line": 1, "zh": "こんにちは"}])
        pt_ja.save()

        # Reload both; each sees ONLY its own namespace.
        pt_zh2 = ProgressTracker(p, language="zh")
        pt_ja2 = ProgressTracker(p, language="ja")
        assert pt_zh2.is_chunk_done("a.rpy", 1)
        assert pt_ja2.is_chunk_done("a.rpy", 1)
        # get_file_translations returns only the current namespace's entries.
        zh_trans = pt_zh2.get_file_translations("a.rpy")
        ja_trans = pt_ja2.get_file_translations("a.rpy")
        assert len(zh_trans) == 1 and zh_trans[0]["zh"] == "你好"
        assert len(ja_trans) == 1 and ja_trans[0]["zh"] == "こんにちは"
    print("[OK] test_progress_tracker_language_namespace_isolation")


def test_progress_tracker_legacy_no_language_backward_compat():
    """Round 35 C1: constructing WITHOUT ``language`` kwarg (round-34 style)
    preserves the exact pre-r35 on-disk shape — bare ``rel_path`` keys in
    ``completed_files`` / ``completed_chunks`` / ``results``.
    """
    import json
    import tempfile
    from pathlib import Path
    from core.translation_utils import ProgressTracker

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "progress.json"
        pt = ProgressTracker(p)  # no language
        pt.mark_chunk_done("a.rpy", 1, [{"line": 1, "zh": "你好"}])
        pt.save()

        # On-disk bare keys, no "<lang>:" prefix.
        on_disk = json.loads(p.read_text(encoding="utf-8"))
        assert "a.rpy" in on_disk["completed_chunks"]
        assert all(":" not in k for k in on_disk["completed_chunks"].keys()), (
            "no-language mode must not write namespaced keys"
        )

        # Reload preserves bare-key behaviour.
        pt2 = ProgressTracker(p)
        assert pt2.is_chunk_done("a.rpy", 1)
    print("[OK] test_progress_tracker_legacy_no_language_backward_compat")


def test_progress_tracker_legacy_bare_keys_resume_under_language():
    """Round 35 C1: opening a PRE-r35 progress.json (bare keys, no lang
    prefix) under a language-aware ProgressTracker must still resume
    the bare keys via the fallback read path.  Critical migration
    scenario — operator upgrades tool, re-runs on existing output dir,
    progress picks up where round-34 left off.
    """
    import json
    import tempfile
    from pathlib import Path
    from core.translation_utils import ProgressTracker

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "progress.json"
        # Handcraft a pre-r35 progress file with bare keys.
        p.write_text(json.dumps({
            "completed_files": ["a.rpy"],
            "completed_chunks": {"b.rpy": [1, 2, 3]},
            "results": {"b.rpy": [{"line": 1, "zh": "你好"}]},
            "stats": {},
        }, ensure_ascii=False), encoding="utf-8")

        # Open with language="zh" — fallback reads must find legacy bare keys.
        pt = ProgressTracker(p, language="zh")
        assert pt.is_file_done("a.rpy"), (
            "language-aware tracker must fall back to bare key on miss"
        )
        assert pt.is_chunk_done("b.rpy", 1)
        legacy_trans = pt.get_file_translations("b.rpy")
        assert len(legacy_trans) == 1
        assert legacy_trans[0]["zh"] == "你好"
    print("[OK] test_progress_tracker_legacy_bare_keys_resume_under_language")


def test_progress_tracker_language_switch_does_not_leak_across_langs():
    """Round 36 H1: opening a pre-r35 bare-key progress.json under a
    non-zh language MUST NOT inherit the bare keys (which implicitly
    belonged to zh, the only pre-r35 target language).  Without the
    fix, ja's ``is_chunk_done`` would fall through to zh's bare bucket
    and return True, silently skipping translation and leaving ja's
    DB bucket empty.  Mirror guard: ``mark_file_done`` under a non-zh
    tracker MUST NOT clean the bare bucket either — a hypothetical zh
    resume on the same file needs the bare data intact.
    """
    import json
    import tempfile
    from pathlib import Path
    from core.translation_utils import ProgressTracker

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "progress.json"
        # Pre-r35 bare-key state (historical zh run).
        p.write_text(json.dumps({
            "completed_files": ["a.rpy"],
            "completed_chunks": {"b.rpy": [1, 2, 3]},
            "results": {"b.rpy": [{"line": 1, "zh": "你好"}]},
            "stats": {},
        }, ensure_ascii=False), encoding="utf-8")

        # ja (non-zh) MUST NOT inherit zh's bare keys.
        pt_ja = ProgressTracker(p, language="ja")
        assert not pt_ja.is_file_done("a.rpy"), (
            "H1: ja tracker must not see zh's bare completed_files"
        )
        for part in (1, 2, 3):
            assert not pt_ja.is_chunk_done("b.rpy", part), (
                f"H1: ja tracker must not see zh's bare chunk {part}"
            )
        assert pt_ja.get_file_translations("b.rpy") == [], (
            "H1: ja tracker must not inherit zh's bare results"
        )

        # Mirror guard: ja's mark_file_done must NOT touch zh's bare bucket.
        pt_ja.mark_chunk_done("b.rpy", 1, [{"line": 1, "zh": "こんにちは"}])
        pt_ja.mark_file_done("b.rpy")
        assert pt_ja.data["completed_chunks"].get("b.rpy") == [1, 2, 3], (
            "H1 mirror: ja's mark_file_done must not clean zh's bare chunks"
        )
        bare_results = pt_ja.data["results"].get("b.rpy", [])
        assert len(bare_results) == 1 and bare_results[0].get("zh") == "你好", (
            "H1 mirror: ja's mark_file_done must not clean zh's bare results"
        )

        # zh control on a fresh pre-r35 file must still resume (legacy
        # semantics preserved — ``_LEGACY_BARE_LANG`` is "zh").
        p2 = Path(td) / "progress_zh.json"
        p2.write_text(json.dumps({
            "completed_files": ["a.rpy"],
            "completed_chunks": {"b.rpy": [1, 2, 3]},
            "results": {"b.rpy": [{"line": 1, "zh": "你好"}]},
            "stats": {},
        }, ensure_ascii=False), encoding="utf-8")
        pt_zh = ProgressTracker(p2, language="zh")
        assert pt_zh.is_file_done("a.rpy")
        assert pt_zh.is_chunk_done("b.rpy", 1)
        assert len(pt_zh.get_file_translations("b.rpy")) == 1
    print("[OK] test_progress_tracker_language_switch_does_not_leak_across_langs")


def run_all() -> int:
    """Run every ProgressTracker language-aware test; return test count."""
    tests = [
        # Round 35 C1: ProgressTracker language namespace
        test_progress_tracker_language_namespace_isolation,
        test_progress_tracker_legacy_no_language_backward_compat,
        test_progress_tracker_legacy_bare_keys_resume_under_language,
        # Round 36 H1: non-zh language must not inherit bare-key state
        test_progress_tracker_language_switch_does_not_leak_across_langs,
    ]
    for t in tests:
        t()
    return len(tests)


if __name__ == "__main__":
    n = run_all()
    print()
    print("=" * 40)
    print(f"ALL {n} PROGRESS TRACKER LANGUAGE TESTS PASSED")
    print("=" * 40)
