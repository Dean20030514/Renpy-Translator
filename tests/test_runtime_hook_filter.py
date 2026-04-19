#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round 34 Commit 1 — ``entry_language_filter`` tests for
``core.runtime_hook_emitter.build_translations_map``.

Kept in a dedicated file (rather than appended to ``tests/test_runtime_hook.py``)
because the parent file is already at 791 lines post round-33 Commit 4 prep
and adding these tests would push it over the CLAUDE.md 800-line soft limit.
The filter behaviour is a self-contained slice of the emitter surface —
well-suited to a standalone micro-suite.
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


def run_all() -> int:
    """Run every test in this module; return test count."""
    tests = [
        test_build_translations_map_filters_by_language,
        test_build_translations_map_filter_none_means_no_filter,
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
