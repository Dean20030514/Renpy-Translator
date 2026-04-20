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


def test_tl_chunk_reads_alias_field_from_mocked_response():
    """Round 41 audit tail: verify the *response-read* side of r39
    per-language dispatch.

    ``test_tl_system_prompt_per_language_branch`` only asserts the
    prompt tells the AI to use ``"ja"`` field.  This test feeds a
    mocked ``_translate_one_tl_chunk`` a response where both the
    "zh" placeholder (required by :func:`check_response_item`) and
    the real target alias ("ja" / "jp") are populated with distinct
    strings, and asserts ``kept_items`` takes the alias-resolved
    value — proving ``ctx.lang_config`` actually drives
    :func:`core.lang_config.resolve_translation_field`.

    The "zh" field is a honeypot: if the r39 dispatch regressed to
    the legacy ``t.get("zh", "")`` path, ``kept_items`` would contain
    the "zh-honeypot-*" strings instead of the Japanese translations.
    """
    import unittest.mock as mock

    from core.api_client import APIClient, APIConfig
    from core.lang_config import get_language_config
    from core.translation_utils import TranslationContext
    from translators.tl_mode import _translate_one_tl_chunk

    def fake_translate(_system_prompt, _user_prompt):
        # "original" + "zh" are required by file_processor.checker
        # (check_response_item looks only at those two fields).
        # "ja" / "jp" are the real target-language aliases we expect
        # resolve_translation_field to pick up.
        return [
            {"id": "e1", "line": 1, "original": "Hello",
             "ja": "こんにちは", "zh": "zh-honeypot-1"},
            {"id": "e2", "line": 2, "original": "World",
             "jp": "世界", "zh": "zh-honeypot-2"},
        ]

    cfg = APIConfig(
        provider="xai", api_key="test", model="grok",
        max_retries=1, rpm=0, rps=0, use_connection_pool=False,
    )
    client = APIClient(cfg)
    client.translate = mock.MagicMock(side_effect=fake_translate)

    ctx = TranslationContext(
        client=client,
        system_prompt="test system prompt",
        rel_path="script.rpy",
        locked_terms_map={},
        lang_config=get_language_config("ja"),
    )

    _rel, _ci, kept, dropped, _warns = _translate_one_tl_chunk(
        ctx, "script.rpy", 0, "dummy chunk text",
        [{"id": "e1"}, {"id": "e2"}],
    )

    assert dropped == 0, (
        f"checker should not drop any item (both have original+zh); "
        f"got dropped={dropped}"
    )
    assert kept.get("e1") == "こんにちは", (
        "primary alias 'ja' not resolved via resolve_translation_field; "
        f"got kept['e1']={kept.get('e1')!r} — if it is "
        f"'zh-honeypot-1' the r39 dispatch regressed to legacy zh path"
    )
    assert kept.get("e2") == "世界", (
        "secondary alias 'jp' not resolved via field_aliases chain; "
        f"got kept['e2']={kept.get('e2')!r} — if it is "
        f"'zh-honeypot-2' the r39 dispatch regressed to legacy zh path"
    )
    print("[OK] test_tl_chunk_reads_alias_field_from_mocked_response")


def test_check_response_item_lang_config_none_backward_compat():
    """Round 42 M2 phase-4: default ``lang_config=None`` preserves the
    r41 byte-identical behaviour — translation field is read from the
    hard-coded ``"zh"`` key.  Validates the no-regression guarantee for
    the ~6 existing callers that have not yet been updated.
    """
    from file_processor import check_response_item

    # zh happy path with no lang_config → pass
    assert check_response_item(
        {"line": 1, "original": "Hello", "zh": "你好"},
    ) == []

    # Empty zh with no lang_config → "译文为空" warning
    warns = check_response_item(
        {"line": 2, "original": "Hello", "zh": ""},
    )
    assert any("译文为空" in w for w in warns), (
        f"empty zh must be flagged, got: {warns}"
    )
    print("[OK] test_check_response_item_lang_config_none_backward_compat")


def test_check_response_item_lang_config_ja_accepts_japanese_alias():
    """Round 42 M2 phase-4: when ``lang_config=get_language_config("ja")``
    is supplied, the checker resolves the translation field through the
    ``field_aliases`` chain (``["ja", "japanese", "jp"]``).  An entry that
    populates ``"ja"`` passes; an entry that only populates ``"zh"`` is
    flagged as empty because ``"zh"`` is not in the ja alias chain.
    """
    from file_processor import check_response_item
    from core.lang_config import get_language_config

    ja = get_language_config("ja")

    # Primary ja alias — pass
    assert check_response_item(
        {"line": 1, "original": "Hello", "ja": "こんにちは"},
        lang_config=ja,
    ) == []

    # Secondary jp alias — pass
    assert check_response_item(
        {"line": 2, "original": "World", "jp": "世界"},
        lang_config=ja,
    ) == []

    # Only zh populated — should be rejected (zh not in ja aliases)
    warns = check_response_item(
        {"line": 3, "original": "Hi", "zh": "你好"},
        lang_config=ja,
    )
    assert any("译文为空" in w for w in warns), (
        f"ja lang_config must not accept a zh-only response (checker "
        f"previously hard-coded 'zh' and let this through); got: {warns}"
    )
    print("[OK] test_check_response_item_lang_config_ja_accepts_japanese_alias")


def test_check_response_item_lang_config_ko_accepts_korean_alias():
    """Round 42 M2 phase-4: Korean (ko / korean / kr) alias chain."""
    from file_processor import check_response_item
    from core.lang_config import get_language_config

    ko = get_language_config("ko")
    assert check_response_item(
        {"line": 1, "original": "Hello", "ko": "안녕하세요"},
        lang_config=ko,
    ) == []
    assert check_response_item(
        {"line": 2, "original": "World", "korean": "세계"},
        lang_config=ko,
    ) == []
    print("[OK] test_check_response_item_lang_config_ko_accepts_korean_alias")


def test_check_response_item_lang_config_falls_back_to_generic_field():
    """Round 42 M2 phase-4: when an entry has no match in the
    language-specific aliases, ``resolve_translation_field`` falls back
    to the generic keys ``["translation", "target", "trans"]`` — so a
    model that returns ``"translation": "..."`` still validates.
    """
    from file_processor import check_response_item
    from core.lang_config import get_language_config

    ja = get_language_config("ja")
    # Neither ja/jp/japanese present, but generic "translation" key is
    assert check_response_item(
        {"line": 1, "original": "Hi", "translation": "こんにちは"},
        lang_config=ja,
    ) == []
    print("[OK] test_check_response_item_lang_config_falls_back_to_generic_field")


def test_filter_checked_translations_forwards_lang_config():
    """Round 42 M2 phase-4: ``_filter_checked_translations`` forwards the
    ``lang_config`` kwarg to ``check_response_item``.  Mixed batch of
    ja-populated (kept) + zh-only (dropped) proves the forwarding works
    — if the kwarg weren't threaded through, the zh-only entry would be
    wrongly kept (the r41 hard-coded path).
    """
    from file_processor import _filter_checked_translations
    from core.lang_config import get_language_config

    ja = get_language_config("ja")
    translations = [
        {"line": 1, "original": "Hello", "ja": "こんにちは"},    # ja-populated → keep
        {"line": 2, "original": "World", "zh": "世界"},           # zh-only → drop under ja
        {"line": 3, "original": "Foo", "japanese": "フー"},       # japanese alias → keep
    ]
    kept, dropped_count, dropped_items, warns = _filter_checked_translations(
        translations, lang_config=ja,
    )
    assert len(kept) == 2, f"expected 2 kept, got {len(kept)}: {kept}"
    assert dropped_count == 1, (
        f"expected 1 dropped under ja lang_config, got {dropped_count}; "
        f"warnings: {warns}"
    )
    # The kept entries are the ja + japanese ones; the zh-only entry
    # was correctly routed to dropped.
    kept_lines = sorted(k.get("line") for k in kept)
    assert kept_lines == [1, 3], f"wrong lines kept: {kept_lines}"
    print("[OK] test_filter_checked_translations_forwards_lang_config")


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
        # Round 41 audit tail — response-side integration for r39 dispatch
        test_tl_chunk_reads_alias_field_from_mocked_response,
        # Round 42 M2 phase-4 — checker per-language field resolution
        test_check_response_item_lang_config_none_backward_compat,
        test_check_response_item_lang_config_ja_accepts_japanese_alias,
        test_check_response_item_lang_config_ko_accepts_korean_alias,
        test_check_response_item_lang_config_falls_back_to_generic_field,
        test_filter_checked_translations_forwards_lang_config,
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
