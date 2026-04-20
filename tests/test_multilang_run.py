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


def test_tl_system_prompt_per_language_branch():
    """Round 39: ``build_tl_system_prompt`` branches on
    ``lang_config.code``.  zh / zh-tw / None → existing Chinese template
    (byte-identical r38).  Other languages → generic English template
    substituting ``{target_language}`` / ``{native_name}`` /
    ``{translation_instruction}`` / ``{field}`` from the lang_config.
    """
    from core.prompts import build_tl_system_prompt
    from core.lang_config import get_language_config

    # zh default — byte-identical Chinese template.
    zh_prompt = build_tl_system_prompt(lang_config=None)
    assert "简体中文" in zh_prompt, "r38 Chinese template must contain 简体中文"
    assert "Target language:" not in zh_prompt, "zh must NOT use generic English template"

    # Explicit zh-tw → still Chinese template path (preserves existing semantics).
    zh_tw_prompt = build_tl_system_prompt(lang_config=get_language_config("zh-tw"))
    assert "简体中文" in zh_tw_prompt

    # ja → generic English template with Japanese metadata.
    ja_prompt = build_tl_system_prompt(lang_config=get_language_config("ja"))
    assert "Target language: Japanese (日本語)" in ja_prompt, (
        "r39: ja must use generic template with Japanese native_name"
    )
    assert "日本語に翻訳してください" in ja_prompt, (
        "r39: ja prompt must include translation_instruction"
    )
    assert '"ja": "…"' in ja_prompt, (
        "r39: ja prompt JSON example must use 'ja' field name"
    )

    # ko → same shape for Korean.
    ko_prompt = build_tl_system_prompt(lang_config=get_language_config("ko"))
    assert "Target language: Korean (한국어)" in ko_prompt
    assert '"ko": "…"' in ko_prompt
    print("[OK] test_tl_system_prompt_per_language_branch")


def test_retranslate_system_prompt_per_language_branch():
    """Round 39: ``build_retranslate_system_prompt`` also branches by
    ``lang_config.code``.  Same contract as ``build_tl_system_prompt``.
    """
    from core.prompts import build_retranslate_system_prompt
    from core.lang_config import get_language_config

    # zh → existing Chinese template.
    zh_prompt = build_retranslate_system_prompt()
    assert ">>>" in zh_prompt, "retranslate marker syntax must appear"
    assert "补翻" in zh_prompt or "遗漏" in zh_prompt or "必须" in zh_prompt, (
        "zh template must contain Chinese task phrasing"
    )

    # ja → generic template.
    ja_prompt = build_retranslate_system_prompt(
        lang_config=get_language_config("ja"),
    )
    assert "Target language: Japanese (日本語)" in ja_prompt
    assert '"ja": "…"' in ja_prompt
    assert ">>>" in ja_prompt, "retranslate >>> marker must be in both paths"
    print("[OK] test_retranslate_system_prompt_per_language_branch")


def run_all() -> int:
    tests = [
        test_parse_target_langs_single_language,
        test_parse_target_langs_bcp47_hyphen_preserved,
        test_parse_target_langs_comma_separated,
        test_parse_target_langs_whitespace_trimmed,
        test_parse_target_langs_empty_falls_back_to_zh,
        test_parse_target_langs_duplicates_preserved,
        # Round 39 — tl-mode + retranslate per-language prompt
        test_tl_system_prompt_per_language_branch,
        test_retranslate_system_prompt_per_language_branch,
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
