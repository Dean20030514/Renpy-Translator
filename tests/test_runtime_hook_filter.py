#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Runtime-hook emitter micro-tests — safety / filter overflow suite.

- Round 34 Commit 1: ``entry_language_filter`` tests for
  ``core.runtime_hook_emitter.build_translations_map`` (prevents multi-
  language DB bucket leakage in v2 emit).
- Round 36 H2: ``_sanitise_overrides`` non-finite float rejection
  (inf / -inf / nan).  Placed here rather than ``test_translation_state.py``
  (where r34/r35 override tests live) because that file hit the CLAUDE.md
  800-line soft limit after round 36 H1 added a regression test.
  Conceptually adjacent: both guard the emit pipeline from bad input.

Kept in a dedicated file because ``tests/test_runtime_hook.py`` is already
at 794 lines and cannot absorb new tests without overflow.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_build_translations_map_filters_by_language():
    """Round 34 C1: ``entry_language_filter`` keeps matching + None-bucket
    entries, drops mismatched language strings.  Prevents multi-language
    DB bucket leakage in v2 emit.
    """
    from core.runtime_hook_emitter import build_translations_map

    entries = [
        {"file": "a.rpy", "line": 1, "original": "Hello", "translation": "你好",
         "status": "ok", "language": "zh"},
        {"file": "a.rpy", "line": 1, "original": "Hello", "translation": "こんにちは",
         "status": "ok", "language": "ja"},
        # Legacy None bucket — kept universally so old v1 DB files still emit.
        {"file": "b.rpy", "line": 1, "original": "World", "translation": "世界",
         "status": "ok"},
        {"file": "c.rpy", "line": 1, "original": "Goodbye", "translation": "さようなら",
         "status": "ok", "language": "ja"},
    ]
    assert build_translations_map(entries, entry_language_filter="zh") == {
        "Hello": "你好", "World": "世界",
    }
    assert build_translations_map(entries, entry_language_filter="ja") == {
        "Hello": "こんにちは", "World": "世界", "Goodbye": "さようなら",
    }
    v2_zh = build_translations_map(
        entries, schema_version=2, target_lang="zh", entry_language_filter="zh",
    )
    assert v2_zh["translations"] == {"Hello": {"zh": "你好"}, "World": {"zh": "世界"}}
    print("[OK] build_translations_map_filters_by_language")


def test_build_translations_map_filter_none_means_no_filter():
    """Round 34 C1: ``entry_language_filter=None`` (default) must preserve
    round-33 behaviour byte-identically.  Regression guard so a future
    change doesn't silently tighten the opt-in default.
    """
    from core.runtime_hook_emitter import build_translations_map

    entries = [
        {"file": "a.rpy", "line": 1, "original": "Hello", "translation": "你好",
         "status": "ok", "language": "zh"},
        {"file": "a.rpy", "line": 1, "original": "Hello", "translation": "こんにちは",
         "status": "ok", "language": "ja"},
        {"file": "b.rpy", "line": 1, "original": "World", "translation": "世界",
         "status": "ok"},
    ]
    expected = {"Hello": "你好", "World": "世界"}  # first-wins collapse
    assert build_translations_map(entries) == expected
    assert build_translations_map(entries, entry_language_filter=None) == expected
    # Round-33 legacy shape (no language field at all) still works.
    legacy = [{"file": "a.rpy", "line": 1, "original": "Hello",
               "translation": "你好", "status": "ok"}]
    assert build_translations_map(legacy) == {"Hello": "你好"}
    print("[OK] build_translations_map_filter_none_means_no_filter")


def test_sanitise_overrides_rejects_non_finite_floats():
    """Round 36 H2: ``_sanitise_overrides`` must reject inf / -inf / nan.

    Python's ``json.loads`` accepts JSON ``Infinity`` / ``NaN`` as
    ``float('inf')`` / ``float('nan')`` by default — these pass the
    ``isinstance(raw_val, (int, float))`` check but ``repr(inf) == 'inf'``
    is not a valid identifier in Ren'Py's ``init python:`` block, so
    emitting them crashes game startup with NameError.  The filter
    covers both registered categories (``gui_overrides`` / ``config_
    overrides``) since the shared ``_sanitise_overrides`` helper gates
    all of them.
    """
    import tempfile
    from pathlib import Path
    from core.runtime_hook_emitter import emit_runtime_hook

    entries = [{"file": "a.rpy", "line": 1, "original": "Hi",
                "translation": "你好", "status": "ok"}]
    cfg = {
        "gui_overrides": {
            "gui.text_size": 22,                       # safe — kept
            "gui.bad_inf": float("inf"),               # H2 — rejected
            "gui.bad_nan": float("nan"),               # H2 — rejected
        },
        "config_overrides": {
            "config.thoughtbubble_width": 400,         # safe — kept
            "config.bad_ninf": float("-inf"),          # H2 — rejected
        },
    }
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "game"
        emit_runtime_hook(out, entries, font_config=cfg)
        content = (out / "zz_tl_inject_gui.rpy").read_text(encoding="utf-8")
        assert "gui.text_size = 22" in content
        assert "config.thoughtbubble_width = 400" in content
        for bad in ("= inf", "= -inf", "= nan"):
            assert bad not in content, f"H2 leak: {bad!r} in emitted rpy"

        # All-non-finite font_config → no aux rpy (combined map empty).
        cfg_all_bad = {"gui_overrides": {"gui.x": float("inf"),
                                          "gui.y": float("nan")}}
        out2 = Path(td) / "game2"
        emit_runtime_hook(out2, entries, font_config=cfg_all_bad)
        assert not (out2 / "zz_tl_inject_gui.rpy").exists(), (
            "H2: all-non-finite font_config must not emit aux rpy"
        )
    print("[OK] sanitise_overrides_rejects_non_finite_floats")


def run_all() -> int:
    """Run every test in this module; return test count."""
    tests = [
        test_build_translations_map_filters_by_language,
        test_build_translations_map_filter_none_means_no_filter,
        # Round 36 H2: non-finite float rejection in _sanitise_overrides
        test_sanitise_overrides_rejects_non_finite_floats,
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
