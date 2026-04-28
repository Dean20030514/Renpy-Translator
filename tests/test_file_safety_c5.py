#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round 49 Step 2 (Commit C5) expansion: TOCTOU regressions for the
11 tools-and-internal JSON loader sites that adopted check_fstat_size
in C5, complementing the 12 C4 core-site regressions in
``test_file_safety.py``.

This file is a peer of ``test_file_safety.py`` — split out solely
because the combined 17 + 11 = 28 expansion tests would push the
single host file past the project-wide 800-line soft cap (round 48
audit-tail incident).  Both files share the same convention:

  Mock target MUST be ``core.file_safety.os.fstat`` (NOT each caller
  module's ``os.fstat``).  See r48 Step 3 CRITICAL fix (commit
  34d9707) for the stale-mock-target trap that motivates centralising
  expansion regressions in this small set of files: r49+ audits run a
  ``grep "mock.patch.*os.fstat" tests/test_file_safety*.py`` over two
  files to verify mock-target consistency across all 23 sites.

C5 sites covered (11 total, 8 modules):
  1. tools/merge_translations_v2.py::_load_v2_envelope
  2. tools/translation_editor.py::_extract_from_db
  3. tools/translation_editor.py::import_edits
  4. tools/translation_editor.py::_apply_v2_edits
  5. tools/review_generator.py::generate_review_html
  6. tools/analyze_writeback_failures.py::analyze
  7. engines/generic_pipeline.py::_load_progress
  8. core/translation_utils.py::ProgressTracker._load
  9. translators/_screen_patch.py::_load_progress
  10. pipeline/stages.py::tl_mode_report read (lightweight)
  11. pipeline/stages.py::full report read (lightweight)

Two of the 11 are lightweight (import + constant + source-grep)
because their full e2e test would require a complete pipeline-stage
fixture (translated_root, gate config, prior stage outputs) that
massively outweighs the benefit of a single-site regression.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from contextlib import contextmanager
from unittest import mock


@contextmanager
def _patch_fstat_oversize(cap_byte: int):
    """Helper: patch ``core.file_safety.os.fstat`` so it returns a
    fake stat with ``st_size = cap_byte + 1`` — the smallest size
    that triggers the helper's > cap branch.

    Mock target is intentionally ``core.file_safety.os.fstat`` (NOT
    the caller module's os.fstat).  See module-level docstring for
    why r48 Step 3 made this distinction load-bearing.
    """
    class _FakeStat:
        st_size = cap_byte + 1
    with mock.patch("core.file_safety.os.fstat",
                    lambda fd: _FakeStat()):
        yield


def test_merge_v2_load_envelope_rejects_toctou_growth_attack():
    """C5 site 1/11: tools/merge_translations_v2.py::_load_v2_envelope."""
    import json as _json
    import tempfile
    from tools.merge_translations_v2 import (
        _load_v2_envelope, MergeError, _MAX_V2_ENVELOPE_SIZE,
    )

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "v2.json"
        p.write_text(_json.dumps({
            "_schema_version": 2,
            "default_lang": "zh",
            "translations": {},
        }), encoding="utf-8")

        with _patch_fstat_oversize(_MAX_V2_ENVELOPE_SIZE):
            try:
                _load_v2_envelope(p)
                raised = False
            except MergeError as e:
                raised = True
                msg = str(e)

        assert raised, "TOCTOU > cap must raise MergeError"
        assert "TOCTOU" in msg, (
            f"MergeError message must mention TOCTOU; got {msg!r}"
        )
    print("[OK] merge_v2_load_envelope_rejects_toctou_growth_attack")


def test_translation_editor_extract_from_db_rejects_toctou_growth_attack():
    """C5 site 2/11: tools/translation_editor.py::_extract_from_db."""
    import json as _json
    import tempfile
    from tools.translation_editor import (
        _extract_from_db, _MAX_EDITOR_INPUT_SIZE,
    )

    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "tr.json"
        db_path.write_text(_json.dumps({
            "entries": [{"file": "a.rpy", "line": 1,
                          "original": "Hi", "translation": "你好"}],
        }), encoding="utf-8")

        with _patch_fstat_oversize(_MAX_EDITOR_INPUT_SIZE):
            entries = _extract_from_db(db_path)

        assert entries == [], (
            f"TOCTOU > cap must return empty entries; got {len(entries)}"
        )
    print("[OK] translation_editor_extract_from_db_rejects_toctou_growth_attack")


def test_translation_editor_import_edits_rejects_toctou_growth_attack():
    """C5 site 3/11: tools/translation_editor.py::import_edits."""
    import json as _json
    import tempfile
    from tools.translation_editor import (
        import_edits, _MAX_EDITOR_INPUT_SIZE,
    )

    with tempfile.TemporaryDirectory() as td:
        edits_path = Path(td) / "edits.json"
        edits_path.write_text(_json.dumps([
            {"source": "db", "file": "a.rpy", "line": 1,
             "original": "Hi", "translation": "你好"},
        ]), encoding="utf-8")

        with _patch_fstat_oversize(_MAX_EDITOR_INPUT_SIZE):
            result = import_edits(edits_path)

        assert result == {"applied": 0, "skipped": 0, "files_modified": 0}, (
            f"TOCTOU > cap must return zero-result; got {result!r}"
        )
    print("[OK] translation_editor_import_edits_rejects_toctou_growth_attack")


def test_translation_editor_apply_v2_edits_rejects_toctou_growth_attack():
    """C5 site 4/11: tools/translation_editor.py::_apply_v2_edits.

    Verifies the per-path TOCTOU rejection inside the v2-edits loop:
    a single edit pointing at a small v2 file with mocked fstat > cap
    must be SKIPPED (not applied), with skipped count == 1.
    """
    import json as _json
    import os
    import tempfile
    from tools.translation_editor import (
        _apply_v2_edits, _MAX_V2_APPLY_SIZE,
    )

    # _apply_v2_edits paths must be inside the trust root (CWD-resolved
    # via Path.cwd()), so chdir into the temp dir for the test.  Restore
    # cwd BEFORE the TemporaryDirectory cleanup runs (Windows holds the
    # cwd directory; rmtree fails on it otherwise).
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        cwd_before = os.getcwd()
        try:
            os.chdir(td_path)
            v2_file = td_path / "v2.json"
            v2_file.write_text(_json.dumps({
                "_schema_version": 2,
                "default_lang": "zh",
                "translations": {"zh": {"Hi": "你好"}},
            }), encoding="utf-8")

            edits = [{
                "source": "v2",
                "v2_path": str(v2_file),
                "v2_lang": "zh",
                "original": "Hi",
                "translation": "你好你好",
            }]

            with _patch_fstat_oversize(_MAX_V2_APPLY_SIZE):
                result = _apply_v2_edits(edits, create_backup=False)

            assert result["applied"] == 0 and result["skipped"] == 1 \
                    and result["files_modified"] == 0, (
                f"TOCTOU > cap must skip the v2 edit; got result={result!r}"
            )
        finally:
            os.chdir(cwd_before)
    print("[OK] translation_editor_apply_v2_edits_rejects_toctou_growth_attack")


def test_review_generator_rejects_toctou_growth_attack():
    """C5 site 5/11: tools/review_generator.py::generate_review_html."""
    import json as _json
    import tempfile
    from tools.review_generator import (
        generate_review_html, _MAX_REVIEW_DB_SIZE,
    )

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        db_path = td_path / "tr.json"
        db_path.write_text(_json.dumps({
            "entries": [{"file": "a.rpy", "line": 1,
                          "original": "Hi", "translation": "你好",
                          "status": "ok"}],
        }), encoding="utf-8")
        out_path = td_path / "review.html"

        with _patch_fstat_oversize(_MAX_REVIEW_DB_SIZE):
            count = generate_review_html(db_path, out_path)

        assert count == 0, (
            f"TOCTOU > cap must return 0 entries; got count={count}"
        )
    print("[OK] review_generator_rejects_toctou_growth_attack")


def test_analyze_writeback_failures_rejects_toctou_growth_attack():
    """C5 site 6/11: tools/analyze_writeback_failures.py::analyze."""
    import json as _json
    import tempfile
    from tools.analyze_writeback_failures import (
        analyze, _MAX_ANALYSIS_DB_SIZE,
    )

    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "tr.json"
        db_path.write_text(_json.dumps({
            "entries": [{"file": "a.rpy", "line": 1,
                          "original": "Hi", "status": "writeback_failed"}],
        }), encoding="utf-8")

        with _patch_fstat_oversize(_MAX_ANALYSIS_DB_SIZE):
            result = analyze(db_path)

        assert result == {"total": 0, "by_type": {}, "samples": {}}, (
            f"TOCTOU > cap must return empty analysis; got {result!r}"
        )
    print("[OK] analyze_writeback_failures_rejects_toctou_growth_attack")


def test_generic_pipeline_load_progress_rejects_toctou_growth_attack():
    """C5 site 7/11: engines/generic_pipeline.py::_load_progress."""
    import json as _json
    import tempfile
    from engines.generic_pipeline import (
        _load_progress, _MAX_PROGRESS_JSON_SIZE,
    )

    with tempfile.TemporaryDirectory() as td:
        progress_path = Path(td) / "progress.json"
        progress_path.write_text(_json.dumps({
            "completed_chunks": [1, 2, 3],
        }), encoding="utf-8")

        with _patch_fstat_oversize(_MAX_PROGRESS_JSON_SIZE):
            result = _load_progress(progress_path)

        assert result == set(), (
            f"TOCTOU > cap must return empty set (treat as corrupted); "
            f"got {result!r}"
        )
    print("[OK] generic_pipeline_load_progress_rejects_toctou_growth_attack")


def test_translation_utils_progress_tracker_rejects_toctou_growth_attack():
    """C5 site 8/11: core/translation_utils.py::ProgressTracker._load."""
    import json as _json
    import tempfile
    from core.translation_utils import (
        ProgressTracker, _MAX_PROGRESS_JSON_SIZE,
    )

    with tempfile.TemporaryDirectory() as td:
        progress_path = Path(td) / "progress.json"
        progress_path.write_text(_json.dumps({
            "completed_files": ["a.rpy"],
            "completed_chunks": {"a.rpy": [0, 1]},
            "stats": {"chunks_translated": 2},
        }), encoding="utf-8")

        with _patch_fstat_oversize(_MAX_PROGRESS_JSON_SIZE):
            tracker = ProgressTracker(progress_path)

        # _load() runs in __init__; cap rejection must wipe data to {}
        # then re-seed required keys via setdefault.
        assert tracker.data.get("completed_files") == [], (
            f"TOCTOU > cap must reset progress data; got "
            f"completed_files={tracker.data.get('completed_files')!r}"
        )
        assert tracker.data.get("stats") == {}, (
            f"TOCTOU > cap must reset stats to empty; got "
            f"stats={tracker.data.get('stats')!r}"
        )
    print("[OK] translation_utils_progress_tracker_rejects_toctou_growth_attack")


def test_screen_patch_load_progress_rejects_toctou_growth_attack():
    """C5 site 9/11: translators/_screen_patch.py::_load_progress."""
    import json as _json
    import tempfile
    from translators._screen_patch import (
        _load_progress, _MAX_PROGRESS_JSON_SIZE,
    )

    with tempfile.TemporaryDirectory() as td:
        progress_path = Path(td) / "screen_progress.json"
        progress_path.write_text(_json.dumps({
            "completed_texts": {"hash1": "你好"},
            "completed_chunks": [0, 1],
            "stats": {"texts_translated": 1},
        }), encoding="utf-8")

        with _patch_fstat_oversize(_MAX_PROGRESS_JSON_SIZE):
            result = _load_progress(progress_path)

        # Cap rejection returns the empty default shape.
        assert result == {
            "completed_texts": {},
            "completed_chunks": [],
            "stats": {},
        }, (
            f"TOCTOU > cap must return empty default progress shape; "
            f"got {result!r}"
        )
    print("[OK] screen_patch_load_progress_rejects_toctou_growth_attack")


def test_stages_tl_mode_report_uses_check_fstat_size_pattern():
    """C5 site 10/11: pipeline/stages.py tl_mode_report read (lightweight).

    Full e2e test would require a complete prior pipeline-stage fixture
    (stage1 / stage2 outputs); this test pins the structural contract:
      1. pipeline.stages imports check_fstat_size
      2. _MAX_REPORT_JSON_SIZE is the 50 MB family cap
      3. tl_mode_report read body uses the helper
    """
    import inspect
    import pipeline.stages as stages_mod

    assert hasattr(stages_mod, "check_fstat_size"), (
        "pipeline.stages must import check_fstat_size from core.file_safety"
    )
    assert stages_mod._MAX_REPORT_JSON_SIZE == 50 * 1024 * 1024, (
        f"_MAX_REPORT_JSON_SIZE must be 50 MB family cap; "
        f"got {stages_mod._MAX_REPORT_JSON_SIZE}"
    )

    src = inspect.getsource(stages_mod)
    # Two distinct sites in stages.py — both must use the helper.
    helper_call = "check_fstat_size(f, _MAX_REPORT_JSON_SIZE)"
    occurrences = src.count(helper_call)
    assert occurrences >= 2, (
        f"pipeline.stages must use check_fstat_size at BOTH report-read "
        f"sites (tl_mode_report + full report); found {occurrences} usages"
    )
    print("[OK] stages_tl_mode_report_uses_check_fstat_size_pattern")


def test_stages_full_report_uses_check_fstat_size_pattern():
    """C5 site 11/11: pipeline/stages.py full report read (lightweight).

    Companion to site 10 — pins the structural contract for the
    second stages.py read site (full report.json) and confirms its
    TOCTOU branch raises ValueError so the existing except handler
    (per round 26 H-3 contract) surfaces the failure to the operator
    rather than silently zeroing checker_dropped.
    """
    import inspect
    import pipeline.stages as stages_mod

    src = inspect.getsource(stages_mod)
    # Full report read must raise ValueError on TOCTOU growth so the
    # existing except (..., ValueError) branch produces report_error.
    assert (
        "raise ValueError" in src and "TOCTOU" in src
        and "full report.json" in src
    ), (
        "pipeline.stages full-report TOCTOU branch must raise ValueError "
        "with TOCTOU and 'full report.json' in the message so the r26 H-3 "
        "except branch surfaces the failure"
    )
    print("[OK] stages_full_report_uses_check_fstat_size_pattern")


ALL_TESTS = [
    # C5 site 1: tools/merge_translations_v2.py
    test_merge_v2_load_envelope_rejects_toctou_growth_attack,
    # C5 sites 2-4: tools/translation_editor.py (3 callers)
    test_translation_editor_extract_from_db_rejects_toctou_growth_attack,
    test_translation_editor_import_edits_rejects_toctou_growth_attack,
    test_translation_editor_apply_v2_edits_rejects_toctou_growth_attack,
    # C5 site 5: tools/review_generator.py
    test_review_generator_rejects_toctou_growth_attack,
    # C5 site 6: tools/analyze_writeback_failures.py
    test_analyze_writeback_failures_rejects_toctou_growth_attack,
    # C5 site 7: engines/generic_pipeline.py
    test_generic_pipeline_load_progress_rejects_toctou_growth_attack,
    # C5 site 8: core/translation_utils.py
    test_translation_utils_progress_tracker_rejects_toctou_growth_attack,
    # C5 site 9: translators/_screen_patch.py
    test_screen_patch_load_progress_rejects_toctou_growth_attack,
    # C5 sites 10-11: pipeline/stages.py (2 sites; lightweight)
    test_stages_tl_mode_report_uses_check_fstat_size_pattern,
    test_stages_full_report_uses_check_fstat_size_pattern,
]


def run_all() -> int:
    """Run every C5 expansion regression in this module."""
    for t in ALL_TESTS:
        t()
    return len(ALL_TESTS)


if __name__ == "__main__":
    n = run_all()
    print()
    print("=" * 40)
    print(f"ALL {n} FILE SAFETY C5 EXPANSION TESTS PASSED")
    print("=" * 40)
