#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round 34 Commit 2 — TranslationDB schema v2 language-field tests.

Covers the round 34 Subtask 1 schema change: constructor gains
``default_language`` kwarg, ``_index`` key becomes a 4-tuple with the
language slot, ``has_entry``/``filter_by_status`` gain optional
``language`` parameters, and ``load()`` performs a forced v1→v2
backfill when called against an older file with a caller-supplied
default language (prevents ``(file, line, orig, None)`` +
``(file, line, orig, "zh")`` duplicate-bucket drift on upgrade).

Standalone suite (not in ``test_all.py`` meta-runner) so the file
stays small + focused.  Run via ``python tests/test_translation_db_language.py``.
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.translation_db import TranslationDB


def _entry(file: str, line: int, original: str, translation: str, **extra) -> dict:
    """Shorthand for a basic TranslationDB entry used across the tests."""
    e = {"file": file, "line": line, "original": original,
         "translation": translation, "status": "ok"}
    e.update(extra)
    return e


def test_upsert_with_explicit_language():
    """Round 34 C2: entry that already carries ``language`` preserves it
    verbatim — constructor default does not override caller-supplied
    language strings.
    """
    with tempfile.TemporaryDirectory() as td:
        db = TranslationDB(Path(td) / "db.json", default_language="zh")
        db.upsert_entry(_entry("a.rpy", 1, "Hello", "こんにちは", language="ja"))
        assert len(db.entries) == 1
        # Caller's ja wins over DB default zh.
        assert db.entries[0]["language"] == "ja"
        assert db.has_entry("a.rpy", 1, "Hello", language="ja")
        # Default-language query misses: explicit lang buckets are distinct.
        assert not db.has_entry("a.rpy", 1, "Hello", language="zh")
    print("[OK] test_upsert_with_explicit_language")


def test_upsert_autofills_from_default_language():
    """Round 34 C2: when constructor has ``default_language``, entries
    upserted without a ``language`` field get it auto-filled; the
    original caller dict is NOT mutated (shallow-copy contract).
    """
    with tempfile.TemporaryDirectory() as td:
        db = TranslationDB(Path(td) / "db.json", default_language="zh")
        caller_entry = _entry("a.rpy", 1, "Hello", "你好")
        db.upsert_entry(caller_entry)
        assert db.entries[0]["language"] == "zh"
        # Caller's dict untouched — the DB shallow-copied before stamping.
        assert "language" not in caller_entry
        assert db.has_entry("a.rpy", 1, "Hello", language="zh")
        # 3-arg has_entry matches the NONE bucket, which is empty after
        # auto-fill — this is the "exact match" contract.
        assert not db.has_entry("a.rpy", 1, "Hello", language=None)
    print("[OK] test_upsert_autofills_from_default_language")


def test_has_entry_exact_language_match():
    """Round 34 C2: same (file, line, original) with different language
    values must be STORED as separate entries with distinct index keys.
    Guards against accidental wildcarding in the index.
    """
    with tempfile.TemporaryDirectory() as td:
        db = TranslationDB(Path(td) / "db.json")
        db.upsert_entry(_entry("a.rpy", 1, "Hello", "你好", language="zh"))
        db.upsert_entry(_entry("a.rpy", 1, "Hello", "こんにちは", language="ja"))
        assert len(db.entries) == 2
        assert db.has_entry("a.rpy", 1, "Hello", language="zh")
        assert db.has_entry("a.rpy", 1, "Hello", language="ja")
        assert not db.has_entry("a.rpy", 1, "Hello", language="ko")
        assert not db.has_entry("a.rpy", 1, "Hello", language=None)
    print("[OK] test_has_entry_exact_language_match")


def test_has_entry_none_vs_string_language():
    """Round 34 C2: ``language=None`` bucket is a distinct index slot
    from any named-language bucket.  Legacy v1-era entries (no language
    field) land in the None bucket; a subsequent upsert of the same
    (file, line, original) with a named language creates a separate
    row rather than overwriting the legacy entry.
    """
    with tempfile.TemporaryDirectory() as td:
        db = TranslationDB(Path(td) / "db.json")  # no default_language
        # Entry without language field → None bucket.
        db.upsert_entry(_entry("a.rpy", 1, "Hello", "legacy_zh"))
        assert db.has_entry("a.rpy", 1, "Hello", language=None)
        # Entry with explicit language → separate bucket.
        db.upsert_entry(_entry("a.rpy", 1, "Hello", "你好", language="zh"))
        assert len(db.entries) == 2
        assert db.has_entry("a.rpy", 1, "Hello", language=None)
        assert db.has_entry("a.rpy", 1, "Hello", language="zh")
    print("[OK] test_has_entry_none_vs_string_language")


def test_filter_by_status_with_language():
    """Round 34 C2: ``filter_by_status`` ``language`` kwarg restricts
    output to the named language bucket; ``language=None`` (default)
    returns all entries regardless of language.
    """
    with tempfile.TemporaryDirectory() as td:
        db = TranslationDB(Path(td) / "db.json")
        db.upsert_entry(_entry("a.rpy", 1, "Hello", "你好", language="zh"))
        db.upsert_entry(_entry("a.rpy", 2, "World", "世界", language="zh"))
        db.upsert_entry(_entry("a.rpy", 1, "Hello", "こんにちは", language="ja"))
        db.upsert_entry(_entry("b.rpy", 1, "Legacy", "遗留"))  # None bucket

        all_ok = db.filter_by_status(statuses=["ok"])
        assert len(all_ok) == 4  # no language filter

        zh_only = db.filter_by_status(statuses=["ok"], language="zh")
        assert len(zh_only) == 2
        assert all(e.get("language") == "zh" for e in zh_only)

        ja_only = db.filter_by_status(statuses=["ok"], language="ja")
        assert len(ja_only) == 1
        assert ja_only[0]["translation"] == "こんにちは"

        # Named-language filter excludes the None-bucket legacy entry.
        ko_only = db.filter_by_status(statuses=["ok"], language="ko")
        assert ko_only == []
    print("[OK] test_filter_by_status_with_language")


def test_save_load_v2_schema_roundtrip():
    """Round 34 C2: saved DB has version=2 in JSON; reloading it
    preserves all entries + language fields byte-identically.
    """
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "db.json"
        db = TranslationDB(db_path, default_language="zh")
        db.upsert_entry(_entry("a.rpy", 1, "Hello", "你好"))
        db.upsert_entry(_entry("a.rpy", 2, "World", "世界", language="zh-tw"))
        db.save()

        # Inspect on-disk version.
        on_disk = json.loads(db_path.read_text(encoding="utf-8"))
        assert on_disk["version"] == 2
        assert len(on_disk["entries"]) == 2

        # Reload into a fresh instance; entries + buckets survive.
        db2 = TranslationDB(db_path)
        db2.load()
        assert len(db2.entries) == 2
        assert db2.has_entry("a.rpy", 1, "Hello", language="zh")
        assert db2.has_entry("a.rpy", 2, "World", language="zh-tw")
    print("[OK] test_save_load_v2_schema_roundtrip")


def test_load_v1_without_default_preserves_none():
    """Round 34 C2: opening an old v1 DB file WITHOUT passing
    ``default_language`` preserves the missing-language state as the
    None bucket — round-33 behaviour byte-identical.  This is the
    "pure read" path for tools like ``verify_alignment`` that don't
    want to trigger the backfill side effect.
    """
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "db.json"
        # Handcraft a v1-shaped file on disk.
        db_path.write_text(json.dumps({
            "version": 1,
            "entries": [
                {"file": "a.rpy", "line": 1, "original": "Hello",
                 "translation": "你好", "status": "ok"},
            ],
        }, ensure_ascii=False), encoding="utf-8")

        db = TranslationDB(db_path)  # no default_language
        db.load()
        assert len(db.entries) == 1
        # Language stays absent — no backfill without a caller default.
        assert "language" not in db.entries[0]
        assert db.has_entry("a.rpy", 1, "Hello", language=None)
        assert not db.has_entry("a.rpy", 1, "Hello", language="zh")
        # _dirty stays False since load did no mutation.
        assert db._dirty is False
    print("[OK] test_load_v1_without_default_preserves_none")


def test_load_v1_with_default_language_backfills():
    """Round 34 C2: the critical migration path — opening an old v1
    DB with ``default_language`` set causes every entry missing
    ``language`` to adopt the caller's default.  Without this,
    subsequent upserts of the same (file, line, original) with the
    default language would create parallel None-bucket + named-bucket
    duplicates and the DB would grow monotonically on every re-run.
    """
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "db.json"
        db_path.write_text(json.dumps({
            "version": 1,
            "entries": [
                {"file": "a.rpy", "line": 1, "original": "Hello",
                 "translation": "你好", "status": "ok"},
                # One entry ALREADY has a language — must NOT be overwritten
                # by the backfill (caller-supplied value always wins).
                {"file": "a.rpy", "line": 2, "original": "World",
                 "translation": "世界", "status": "ok", "language": "zh-tw"},
            ],
        }, ensure_ascii=False), encoding="utf-8")

        db = TranslationDB(db_path, default_language="zh")
        db.load()
        assert len(db.entries) == 2
        # Missing-language entry backfilled from default.
        assert db.entries[0]["language"] == "zh"
        # Already-tagged entry preserved.
        assert db.entries[1]["language"] == "zh-tw"
        # Both are now reachable via their respective language bucket.
        assert db.has_entry("a.rpy", 1, "Hello", language="zh")
        assert db.has_entry("a.rpy", 2, "World", language="zh-tw")
        # Dirty flag ON so the backfill persists on next save() —
        # one-way upgrade, on-disk file moves to v2 after save.
        assert db._dirty is True

        # The CRITICAL duplicate-prevention check: re-upserting the same
        # (file, line, original) with a bare entry (no language) should
        # overwrite the backfilled entry, NOT create a new one.
        before = len(db.entries)
        db.upsert_entry(_entry("a.rpy", 1, "Hello", "你好 updated"))
        assert len(db.entries) == before, (
            "re-upsert after v1→v2 backfill must NOT create a duplicate row"
        )
    print("[OK] test_load_v1_with_default_language_backfills")


def test_default_language_none_means_legacy_behavior():
    """Round 34 C2: constructor without ``default_language`` produces
    round-33 byte-identical behaviour.  Regression guard so a future
    change doesn't silently flip the default.
    """
    with tempfile.TemporaryDirectory() as td:
        db = TranslationDB(Path(td) / "db.json")  # no default_language
        assert db.default_language is None
        db.upsert_entry(_entry("a.rpy", 1, "Hello", "你好"))
        # No auto-fill — entry stays in None bucket.
        assert "language" not in db.entries[0]
        assert db.has_entry("a.rpy", 1, "Hello")  # legacy 3-arg form works

        # Legacy filter_by_status (no language kwarg) returns everything.
        results = db.filter_by_status(statuses=["ok"])
        assert len(results) == 1
    print("[OK] test_default_language_none_means_legacy_behavior")


def test_save_load_roundtrip_version_bumps_to_2():
    """Round 34 C2: every successful save writes ``version = 2`` even
    if the DB was loaded from a v1 file (one-way upgrade).  Subsequent
    loads see the new version.
    """
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "db.json"
        # Seed with a v1 file.
        db_path.write_text(json.dumps({
            "version": 1,
            "entries": [{"file": "a.rpy", "line": 1, "original": "Hi",
                         "translation": "嗨", "status": "ok"}],
        }, ensure_ascii=False), encoding="utf-8")

        db = TranslationDB(db_path, default_language="zh")
        db.load()
        assert db.version == 1  # loaded-version snapshot
        db.save()
        # After save(), on-disk version is 2 and in-memory version updated.
        assert db.version == 2
        on_disk = json.loads(db_path.read_text(encoding="utf-8"))
        assert on_disk["version"] == 2
    print("[OK] test_save_load_roundtrip_version_bumps_to_2")


def run_all() -> int:
    """Run every test in this module; return test count."""
    tests = [
        test_upsert_with_explicit_language,
        test_upsert_autofills_from_default_language,
        test_has_entry_exact_language_match,
        test_has_entry_none_vs_string_language,
        test_filter_by_status_with_language,
        test_save_load_v2_schema_roundtrip,
        test_load_v1_without_default_preserves_none,
        test_load_v1_with_default_language_backfills,
        test_default_language_none_means_legacy_behavior,
        test_save_load_roundtrip_version_bumps_to_2,
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
