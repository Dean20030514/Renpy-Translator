#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for ``tools.merge_translations_v2`` — multi-language v2 envelope merge.

Added in round 33 Subtask 1 to cover the new standalone CLI tool that
collapses several per-language ``translations.json`` files produced by
``--runtime-hook-schema v2`` runs into a single multi-language envelope.
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.merge_translations_v2 import (
    MergeError,
    merge_v2_translations,
    main,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_v2(path: Path, translations: dict, default_lang: str = "zh") -> None:
    """Write a v2 envelope JSON file for test input."""
    envelope = {
        "_schema_version": 2,
        "_format": "renpy-translate",
        "default_lang": default_lang,
        "translations": translations,
    }
    path.write_text(
        json.dumps(envelope, ensure_ascii=False, sort_keys=True, indent=2),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Library-level tests (merge_v2_translations)
# ---------------------------------------------------------------------------

def test_merge_two_languages():
    """Two inputs with disjoint language buckets merge into a single
    multi-language envelope where every original has every language."""
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        zh_path = td_path / "zh.json"
        ja_path = td_path / "ja.json"
        _write_v2(zh_path, {"Hello": {"zh": "你好"}, "World": {"zh": "世界"}}, default_lang="zh")
        _write_v2(ja_path, {"Hello": {"ja": "こんにちは"}, "World": {"ja": "世界"}}, default_lang="ja")

        result = merge_v2_translations([zh_path, ja_path])

        assert result["_schema_version"] == 2
        assert result["_format"] == "renpy-translate"
        # First input's default_lang wins when no override given.
        assert result["default_lang"] == "zh"
        assert result["translations"] == {
            "Hello": {"zh": "你好", "ja": "こんにちは"},
            "World": {"zh": "世界", "ja": "世界"},
        }
    print("[OK] test_merge_two_languages")


def test_merge_same_language_first_wins():
    """When two inputs cover the same (original, lang) with different
    translations, the first input's value is kept (non-strict mode)."""
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        first = td_path / "first.json"
        second = td_path / "second.json"
        _write_v2(first, {"Hello": {"zh": "你好"}})
        _write_v2(second, {"Hello": {"zh": "哈喽"}})  # conflict

        result = merge_v2_translations([first, second])

        assert result["translations"] == {"Hello": {"zh": "你好"}}
    print("[OK] test_merge_same_language_first_wins")


def test_merge_preserves_envelope():
    """Output envelope retains every top-level v2 key required by the hook."""
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        single = td_path / "single.json"
        _write_v2(single, {"Hello": {"zh": "你好"}}, default_lang="zh")

        result = merge_v2_translations([single])

        assert set(result.keys()) == {
            "_schema_version", "_format", "default_lang", "translations",
        }
        assert result["_schema_version"] == 2
        assert result["_format"] == "renpy-translate"
        assert result["default_lang"] == "zh"
        assert isinstance(result["translations"], dict)
    print("[OK] test_merge_preserves_envelope")


def test_merge_rejects_v1_input():
    """Flat v1 ``{en: zh}`` inputs must be rejected — merge is v2-only."""
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        v1_path = td_path / "v1_flat.json"
        v1_path.write_text(
            json.dumps({"Hello": "你好", "World": "世界"}, ensure_ascii=False),
            encoding="utf-8",
        )

        raised = None
        try:
            merge_v2_translations([v1_path])
        except MergeError as e:
            raised = e
        assert raised is not None
        assert "v2 envelope" in str(raised)
    print("[OK] test_merge_rejects_v1_input")


def test_merge_rejects_malformed_json():
    """Broken JSON must surface as a MergeError, not an unhandled
    ValueError from json.loads."""
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        bad = td_path / "bad.json"
        bad.write_text("{not valid json", encoding="utf-8")

        raised = None
        try:
            merge_v2_translations([bad])
        except MergeError as e:
            raised = e
        assert raised is not None
        assert "malformed JSON" in str(raised)
    print("[OK] test_merge_rejects_malformed_json")


def test_merge_rejects_missing_file():
    """Non-existent path must surface as a MergeError with a clear message."""
    missing = Path(tempfile.gettempdir()) / "__does_not_exist_r33__.json"
    if missing.exists():
        missing.unlink()

    raised = None
    try:
        merge_v2_translations([missing])
    except MergeError as e:
        raised = e
    assert raised is not None
    assert "not found" in str(raised)
    print("[OK] test_merge_rejects_missing_file")


def test_merge_explicit_default_lang_override():
    """``default_lang`` kwarg takes precedence over any input's value."""
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        a = td_path / "a.json"
        b = td_path / "b.json"
        _write_v2(a, {"Hello": {"zh": "你好"}}, default_lang="zh")
        _write_v2(b, {"Hello": {"ja": "こんにちは"}}, default_lang="ja")

        result = merge_v2_translations([a, b], default_lang="ja")
        assert result["default_lang"] == "ja"

        # Also confirm empty/None override falls back to first-input rule.
        result2 = merge_v2_translations([a, b], default_lang=None)
        assert result2["default_lang"] == "zh"  # first input's
    print("[OK] test_merge_explicit_default_lang_override")


def test_merge_strict_mode_rejects_conflict():
    """``strict=True`` raises on conflict instead of warning + first-wins."""
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        a = td_path / "a.json"
        b = td_path / "b.json"
        _write_v2(a, {"Hello": {"zh": "你好"}})
        _write_v2(b, {"Hello": {"zh": "哈喽"}})  # conflict

        raised = None
        try:
            merge_v2_translations([a, b], strict=True)
        except MergeError as e:
            raised = e
        assert raised is not None
        assert "conflict" in str(raised).lower()

        # Same inputs in non-strict still succeed.
        result = merge_v2_translations([a, b], strict=False)
        assert result["translations"] == {"Hello": {"zh": "你好"}}
    print("[OK] test_merge_strict_mode_rejects_conflict")


def test_merge_fallback_default_lang_zh():
    """When no input has a ``default_lang`` string, fall back to ``"zh"``."""
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        p = td_path / "no_default.json"
        # Craft an envelope whose default_lang is missing entirely.
        p.write_text(
            json.dumps({
                "_schema_version": 2,
                "_format": "renpy-translate",
                "translations": {"Hello": {"zh": "你好"}},
            }, ensure_ascii=False),
            encoding="utf-8",
        )
        result = merge_v2_translations([p])
        assert result["default_lang"] == "zh"
    print("[OK] test_merge_fallback_default_lang_zh")


# ---------------------------------------------------------------------------
# CLI-level tests (main function with argv)
# ---------------------------------------------------------------------------

def test_main_cli_happy_path():
    """End-to-end: main() with real argv writes the merged file and
    returns exit code 0."""
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        zh_path = td_path / "zh.json"
        ja_path = td_path / "ja.json"
        out_path = td_path / "merged.json"
        _write_v2(zh_path, {"Hello": {"zh": "你好"}}, default_lang="zh")
        _write_v2(ja_path, {"Hello": {"ja": "こんにちは"}}, default_lang="ja")

        rc = main([str(zh_path), str(ja_path), "-o", str(out_path)])
        assert rc == 0
        assert out_path.is_file()

        loaded = json.loads(out_path.read_text(encoding="utf-8"))
        assert loaded["_schema_version"] == 2
        assert loaded["translations"] == {"Hello": {"zh": "你好", "ja": "こんにちは"}}
    print("[OK] test_main_cli_happy_path")


def test_main_cli_missing_file_returns_1():
    """main() returns exit code 1 on missing input file without raising."""
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        out_path = td_path / "merged.json"
        bogus = td_path / "does_not_exist.json"

        rc = main([str(bogus), "-o", str(out_path)])
        assert rc == 1
        assert not out_path.exists()
    print("[OK] test_main_cli_missing_file_returns_1")


def test_main_cli_strict_conflict_returns_1():
    """main() with --strict returns 1 on conflict instead of proceeding."""
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        a = td_path / "a.json"
        b = td_path / "b.json"
        out_path = td_path / "merged.json"
        _write_v2(a, {"Hello": {"zh": "你好"}})
        _write_v2(b, {"Hello": {"zh": "哈喽"}})

        rc = main([str(a), str(b), "-o", str(out_path), "--strict"])
        assert rc == 1
        assert not out_path.exists()

        # Non-strict writes the file and returns 0.
        rc2 = main([str(a), str(b), "-o", str(out_path)])
        assert rc2 == 0
        assert out_path.is_file()
    print("[OK] test_main_cli_strict_conflict_returns_1")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_merge_two_languages()
    test_merge_same_language_first_wins()
    test_merge_preserves_envelope()
    test_merge_rejects_v1_input()
    test_merge_rejects_malformed_json()
    test_merge_rejects_missing_file()
    test_merge_explicit_default_lang_override()
    test_merge_strict_mode_rejects_conflict()
    test_merge_fallback_default_lang_zh()
    test_main_cli_happy_path()
    test_main_cli_missing_file_returns_1()
    test_main_cli_strict_conflict_returns_1()
    print("\n=== 全部 v2 merge tool 测试通过 ===")
