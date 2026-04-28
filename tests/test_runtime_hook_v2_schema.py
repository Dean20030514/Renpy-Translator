#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Runtime-hook translations.json v2 schema tests — split from
``tests/test_runtime_hook.py`` in round 46 Step 3 to keep both files
comfortably below the CLAUDE.md 800-line soft limit and to isolate the
v2 schema surface so future ``schema_version=3`` evolution lives in one
focused suite.

Covers ``core/runtime_hook_emitter.build_translations_map`` (v1 / v2
shapes), ``emit_runtime_hook(schema_version=2, ...)``,
``emit_if_requested`` reading ``args.runtime_hook_schema``, and the
inject_hook.rpy v2 reader markers — round 32 Subtask C entirely.

Tests in this module are byte-identical to their pre-split forms; the
extraction was a pure refactor with no behavioural change.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


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


def run_all() -> int:
    """Run every v2 schema test in this module; return test count."""
    tests = [
        test_build_translations_map_v1_unchanged,
        test_build_translations_map_v2_structure,
        test_build_translations_map_v2_respects_target_lang,
        test_build_translations_map_v2_empty_entries,
        test_emit_runtime_hook_v2_schema_kwarg_produces_nested_json,
        test_emit_if_requested_respects_runtime_hook_schema_flag,
        test_inject_hook_contains_v2_reader_markers,
    ]
    for t in tests:
        t()
    return len(tests)


if __name__ == "__main__":
    n = run_all()
    print()
    print("=" * 40)
    print(f"ALL {n} V2 SCHEMA TESTS PASSED")
    print("=" * 40)
