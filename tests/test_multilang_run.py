#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round 35 Commit 2 — multi-language outer-loop helper tests.

Standalone suite covering ``main._parse_target_langs`` (the parser that
feeds ``args.target_langs`` to the outer translation loop).  End-to-end
integration of the loop itself is verified by running the tool against
a real game — out of scope for a unit test that can't mock the API.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import _parse_target_langs


def test_parse_target_langs_single_language():
    """Round 35 C2: round-34 ``--target-lang zh`` stays a 1-element list
    so the outer loop iterates exactly once (byte-identical behaviour)."""
    assert _parse_target_langs("zh") == ["zh"]
    assert _parse_target_langs("ja") == ["ja"]
    print("[OK] test_parse_target_langs_single_language")


def test_parse_target_langs_bcp47_hyphen_preserved():
    """Round 35 C2: ``zh-tw`` is ONE language (hyphen not comma).  Round 34
    users relying on ``--target-lang zh-tw`` must see identical behaviour."""
    assert _parse_target_langs("zh-tw") == ["zh-tw"]
    assert _parse_target_langs("en-US") == ["en-US"]
    print("[OK] test_parse_target_langs_bcp47_hyphen_preserved")


def test_parse_target_langs_comma_separated():
    """Round 35 C2: the new syntax — comma splits into the list that
    drives the outer language loop."""
    assert _parse_target_langs("zh,ja") == ["zh", "ja"]
    assert _parse_target_langs("zh,ja,zh-tw,ko") == ["zh", "ja", "zh-tw", "ko"]
    print("[OK] test_parse_target_langs_comma_separated")


def test_parse_target_langs_whitespace_trimmed():
    """Round 35 C2: operators paste ``zh, ja, zh-tw`` with spaces around
    commas; parser strips whitespace but preserves hyphens."""
    assert _parse_target_langs("zh, ja, zh-tw") == ["zh", "ja", "zh-tw"]
    assert _parse_target_langs("  zh  ,  ja  ") == ["zh", "ja"]
    print("[OK] test_parse_target_langs_whitespace_trimmed")


def test_parse_target_langs_empty_falls_back_to_zh():
    """Round 35 C2: missing / empty / pathological input safely falls
    back to the round-34 default (``["zh"]``) — never returns empty."""
    assert _parse_target_langs("") == ["zh"]
    assert _parse_target_langs(",,,") == ["zh"]
    assert _parse_target_langs(",  ,  ,") == ["zh"]
    # ``None`` guarded by the ``if not raw`` early exit.
    assert _parse_target_langs(None) == ["zh"]  # type: ignore[arg-type]
    print("[OK] test_parse_target_langs_empty_falls_back_to_zh")


def test_parse_target_langs_duplicates_preserved():
    """Round 35 C2: operator passing ``zh,zh`` (e.g. typo / CI script
    bug) sees both; outer loop would translate twice — visible waste
    rather than silent dedup so the mistake is obvious."""
    assert _parse_target_langs("zh,zh") == ["zh", "zh"]
    print("[OK] test_parse_target_langs_duplicates_preserved")


def run_all() -> int:
    tests = [
        test_parse_target_langs_single_language,
        test_parse_target_langs_bcp47_hyphen_preserved,
        test_parse_target_langs_comma_separated,
        test_parse_target_langs_whitespace_trimmed,
        test_parse_target_langs_empty_falls_back_to_zh,
        test_parse_target_langs_duplicates_preserved,
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
