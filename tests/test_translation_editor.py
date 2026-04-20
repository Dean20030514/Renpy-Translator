#!/usr/bin/env python3
"""Tests for tools.translation_editor — HTML export/import roundtrip."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.translation_editor import (
    export_html,
    import_edits,
    _extract_from_tl_dir,
    _extract_from_db,
    _escape_for_rpy,
)


# ============================================================
# Helpers
# ============================================================

def _make_tl_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


_SAMPLE_TL = """\
translate chinese start_abc12345:
    # game/script.rpy:10
    # e "Hello, world!"
    e ""

translate chinese strings:
    old "Start"
    new ""
"""

_SAMPLE_TL_FILLED = """\
translate chinese start_abc12345:
    # game/script.rpy:10
    # e "Hello, world!"
    e "你好世界"

translate chinese strings:
    old "Start"
    new "开始"
"""


# ============================================================
# Export tests
# ============================================================

def test_export_basic():
    """Export entries to HTML, verify it contains expected content."""
    entries = [
        {"source": "tl", "file": "game/tl/chinese/script.rpy", "line": 4,
         "original": "Hello, world!", "translation": "", "character": "e",
         "identifier": "start_abc", "source_file": "game/script.rpy", "source_line": 10},
    ]
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "test.html"
        count = export_html(entries, out)
        assert count == 1
        html_content = out.read_text(encoding="utf-8")
        assert "Hello, world!" in html_content
        assert "contenteditable" in html_content
        assert "exportEdits" in html_content
        assert "__METADATA__" not in html_content  # placeholder replaced
    print("[OK] test_export_basic")


def test_export_multiple():
    """Export multiple entries, verify metadata JSON is embedded."""
    entries = [
        {"source": "tl", "file": "a.rpy", "line": 1, "original": "One",
         "translation": "壹", "character": "", "identifier": "id1",
         "source_file": "a.rpy", "source_line": 1},
        {"source": "tl", "file": "a.rpy", "line": 5, "original": "Two",
         "translation": "", "character": "mc", "identifier": "id2",
         "source_file": "a.rpy", "source_line": 5},
        {"source": "db", "file": "b.rpy", "line": 3, "original": "Three",
         "translation": "叁", "character": "", "identifier": "",
         "source_file": "b.rpy", "source_line": 3},
    ]
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "multi.html"
        count = export_html(entries, out)
        assert count == 3
        html_content = out.read_text(encoding="utf-8")
        # Verify metadata JSON is parseable
        start = html_content.index('id="metadata">') + len('id="metadata">')
        end = html_content.index("</script>", start)
        meta = json.loads(html_content[start:end])
        assert len(meta) == 3
        assert meta[1]["character"] == "mc"
    print("[OK] test_export_multiple")


def test_export_empty():
    """Export with no entries returns 0."""
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "empty.html"
        count = export_html([], out)
        assert count == 0
    print("[OK] test_export_empty")


def test_export_html_escaping():
    """Special characters in text are properly HTML-escaped."""
    entries = [
        {"source": "tl", "file": "a.rpy", "line": 1,
         "original": '<script>alert("xss")</script>',
         "translation": '{color=#f00}red{/color}', "character": "",
         "identifier": "", "source_file": "", "source_line": 0},
    ]
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "xss.html"
        export_html(entries, out)
        content = out.read_text(encoding="utf-8")
        # The script tag should be escaped in the JSON metadata, not rendered
        assert "<script>alert" not in content.split("</head>")[1].split('<script type="application/json"')[0]
    print("[OK] test_export_html_escaping")


# ============================================================
# Extract from tl tests
# ============================================================

def test_extract_from_tl():
    """Extract entries from tl directory using tl_parser."""
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        tl_dir = td / "tl" / "chinese"
        _make_tl_file(tl_dir / "script.rpy", _SAMPLE_TL)

        entries = _extract_from_tl_dir(tl_dir)
        assert len(entries) >= 1  # At least the dialogue entry
        # Check dialogue entry exists
        dialogue = [e for e in entries if e["original"] == "Hello, world!"]
        assert len(dialogue) == 1
        assert dialogue[0]["character"] == "e"
        assert dialogue[0]["source"] == "tl"
    print("[OK] test_extract_from_tl")


def test_extract_from_db():
    """Extract entries from translation_db.json."""
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        db_data = {
            "version": 1,
            "entries": [
                {"file": "script.rpy", "line": 10, "original": "Hello",
                 "translation": "你好", "status": "ok"},
                {"file": "script.rpy", "line": 20, "original": "World",
                 "translation": "", "status": "ok"},
            ],
        }
        db_path = td / "translation_db.json"
        db_path.write_text(json.dumps(db_data), encoding="utf-8")

        entries = _extract_from_db(db_path)
        assert len(entries) == 2
        assert entries[0]["original"] == "Hello"
        assert entries[0]["translation"] == "你好"
        assert entries[1]["translation"] == ""
    print("[OK] test_extract_from_db")


# ============================================================
# Import tests
# ============================================================

def test_import_tl_mode():
    """Import edits back into a tl file — replace existing translation."""
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        tl_file = td / "script.rpy"
        tl_file.write_text(_SAMPLE_TL_FILLED, encoding="utf-8")

        edits = [
            {
                "source": "tl",
                "file": str(tl_file),
                "line": 4,  # Line with e "你好世界"
                "original": "Hello, world!",
                "old_translation": "你好世界",
                "new_translation": "你好，世界！",
                "identifier": "start_abc12345",
            },
        ]
        edits_path = td / "edits.json"
        edits_path.write_text(json.dumps(edits), encoding="utf-8")

        result = import_edits(edits_path, create_backup=True)
        assert result["applied"] == 1
        assert result["files_modified"] == 1

        content = tl_file.read_text(encoding="utf-8")
        assert '你好，世界！' in content
        assert '你好世界' not in content

        # Backup created
        assert (tl_file.with_suffix(".rpy.bak")).exists()
    print("[OK] test_import_tl_mode")


def test_import_empty_slot():
    """Import into empty tl slot (replace "")."""
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        tl_file = td / "script.rpy"
        tl_file.write_text(_SAMPLE_TL, encoding="utf-8")

        edits = [
            {
                "source": "tl",
                "file": str(tl_file),
                "line": 4,  # Line with e ""
                "original": "Hello, world!",
                "old_translation": "",
                "new_translation": "你好世界",
            },
        ]
        edits_path = td / "edits.json"
        edits_path.write_text(json.dumps(edits), encoding="utf-8")

        result = import_edits(edits_path)
        assert result["applied"] == 1
        content = tl_file.read_text(encoding="utf-8")
        assert '"你好世界"' in content
    print("[OK] test_import_empty_slot")


def test_import_no_overwrite_backup():
    """Second import does not overwrite existing .bak."""
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        tl_file = td / "script.rpy"
        tl_file.write_text(_SAMPLE_TL, encoding="utf-8")
        bak = tl_file.with_suffix(".rpy.bak")
        bak.write_text("original backup content", encoding="utf-8")

        edits = [{"source": "tl", "file": str(tl_file), "line": 4,
                   "original": "Hello", "old_translation": "", "new_translation": "你好"}]
        edits_path = td / "edits.json"
        edits_path.write_text(json.dumps(edits), encoding="utf-8")

        import_edits(edits_path)
        assert bak.read_text(encoding="utf-8") == "original backup content"
    print("[OK] test_import_no_overwrite_backup")


def test_import_db_mode():
    """Import edits with source='db' — match original text and replace."""
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        rpy_file = td / "script.rpy"
        rpy_file.write_text(
            'label start:\n    mc "Hello world"\n    mc "Goodbye"\n',
            encoding="utf-8",
        )

        edits = [
            {
                "source": "db",
                "file": str(rpy_file),
                "line": 2,  # Line with "Hello world"
                "original": "Hello world",
                "old_translation": "",
                "new_translation": "你好世界",
            },
        ]
        edits_path = td / "edits.json"
        edits_path.write_text(json.dumps(edits), encoding="utf-8")

        result = import_edits(edits_path)
        assert result["applied"] == 1

        content = rpy_file.read_text(encoding="utf-8")
        assert "你好世界" in content
        assert "Goodbye" in content  # Other lines untouched
    print("[OK] test_import_db_mode")


def test_import_missing_file():
    """Import skips edits for non-existent files."""
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        edits = [{"source": "tl", "file": str(td / "ghost.rpy"), "line": 1,
                   "original": "x", "old_translation": "", "new_translation": "y"}]
        edits_path = td / "edits.json"
        edits_path.write_text(json.dumps(edits), encoding="utf-8")

        result = import_edits(edits_path)
        assert result["skipped"] == 1
        assert result["applied"] == 0
    print("[OK] test_import_missing_file")


def test_import_empty_new_translation():
    """Import skips edits with empty new_translation."""
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        tl_file = td / "script.rpy"
        tl_file.write_text(_SAMPLE_TL, encoding="utf-8")

        edits = [{"source": "tl", "file": str(tl_file), "line": 4,
                   "original": "Hello", "old_translation": "", "new_translation": ""}]
        edits_path = td / "edits.json"
        edits_path.write_text(json.dumps(edits), encoding="utf-8")

        result = import_edits(edits_path)
        assert result["skipped"] == 1
    print("[OK] test_import_empty_new_translation")


# ============================================================
# Utility tests
# ============================================================

def test_escape_for_rpy():
    """Escape quotes and backslashes for Ren'Py strings."""
    assert _escape_for_rpy('hello') == 'hello'
    assert _escape_for_rpy('he said "hi"') == 'he said \\"hi\\"'
    assert _escape_for_rpy('path\\to\\file') == 'path\\\\to\\\\file'
    print("[OK] test_escape_for_rpy")


# ============================================================
# Round 33 Subtask 3 — v2 envelope support
# ============================================================

def _make_v2_envelope(
    path: Path, translations: dict, default_lang: str = "zh",
) -> None:
    """Write a v2 translations.json envelope to ``path`` for tests."""
    path.write_text(
        json.dumps({
            "_schema_version": 2,
            "_format": "renpy-translate",
            "default_lang": default_lang,
            "translations": translations,
        }, ensure_ascii=False, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def test_extract_from_v2_envelope():
    """Round 33 Subtask 3: ``_extract_from_db`` auto-detects a v2 envelope
    and returns entries keyed to the target language bucket, with v2
    routing fields preserved so save-back can locate the source file.
    """
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        v2_path = td_path / "merged.json"
        _make_v2_envelope(v2_path, {
            "Hello": {"zh": "你好", "ja": "こんにちは"},
            "World": {"zh": "世界", "ja": "世界"},
            "Orphan": {"fr": "Bonjour"},  # no zh bucket
        }, default_lang="zh")

        # Default: target_lang = envelope's default_lang = "zh"
        entries = _extract_from_db(v2_path)
        assert len(entries) == 3
        # All entries are flagged as v2 source + share the v2_path.
        for e in entries:
            assert e["source"] == "v2"
            assert e["v2_path"] == str(v2_path)
            assert e["v2_lang"] == "zh"
            assert e["v2_default_lang"] == "zh"
            assert e["v2_langs_seen"] == ["fr", "ja", "zh"]
        entries_by_orig = {e["original"]: e for e in entries}
        assert entries_by_orig["Hello"]["translation"] == "你好"
        assert entries_by_orig["World"]["translation"] == "世界"
        # Orphan has no zh bucket → empty translation.
        assert entries_by_orig["Orphan"]["translation"] == ""

        # Explicit v2_lang = "ja" pivots the translation column.
        entries_ja = _extract_from_db(v2_path, v2_lang="ja")
        ja_by_orig = {e["original"]: e for e in entries_ja}
        assert ja_by_orig["Hello"]["translation"] == "こんにちは"
        assert ja_by_orig["Hello"]["v2_lang"] == "ja"
        assert ja_by_orig["Orphan"]["translation"] == ""

        # v1 translation_db.json still works via the same entry point.
        v1_path = td_path / "v1_db.json"
        v1_path.write_text(json.dumps({
            "version": 1,
            "entries": [
                {"file": "a.rpy", "line": 1, "original": "Legacy",
                 "translation": "遗留", "status": "ok"},
            ],
        }), encoding="utf-8")
        v1_entries = _extract_from_db(v1_path)
        assert len(v1_entries) == 1
        assert v1_entries[0]["source"] == "db"
        assert "v2_path" not in v1_entries[0]
    print("[OK] test_extract_from_v2_envelope")


def test_import_to_v2_envelope():
    """Round 33 Subtask 3: ``import_edits`` with ``source: "v2"`` edits
    writes back to the target ``translations.json`` file, updating the
    selected language bucket of the named original.

    Round 37 M4: the tempdir MUST be allocated under CWD so the
    ``_apply_v2_edits`` path whitelist (CWD-rooted only) accepts the
    legitimate test-generated v2_path.
    """
    with tempfile.TemporaryDirectory(dir=str(Path.cwd())) as td:
        td_path = Path(td)
        v2_path = td_path / "merged.json"
        _make_v2_envelope(v2_path, {
            "Hello": {"zh": "你好", "ja": "こんにちは"},
            "World": {"zh": "世界"},
        }, default_lang="zh")

        edits = [
            {
                "source": "v2",
                "v2_path": str(v2_path),
                "v2_lang": "zh",
                "file": str(v2_path),
                "line": 1,
                "original": "Hello",
                "old_translation": "你好",
                "new_translation": "你好呀",
            },
            {
                "source": "v2",
                "v2_path": str(v2_path),
                "v2_lang": "ja",
                "file": str(v2_path),
                "line": 1,
                "original": "Hello",
                "old_translation": "こんにちは",
                "new_translation": "こんにちは～",
            },
        ]
        edits_path = td_path / "edits.json"
        edits_path.write_text(json.dumps(edits), encoding="utf-8")

        result = import_edits(edits_path, create_backup=True)
        assert result["applied"] == 2
        assert result["files_modified"] == 1
        assert result["skipped"] == 0

        loaded = json.loads(v2_path.read_text(encoding="utf-8"))
        assert loaded["_schema_version"] == 2
        assert loaded["translations"]["Hello"]["zh"] == "你好呀"
        assert loaded["translations"]["Hello"]["ja"] == "こんにちは～"
        # Untouched entries preserved.
        assert loaded["translations"]["World"]["zh"] == "世界"

        # Backup exists alongside the v2 file.
        bak = v2_path.with_suffix(".json.bak")
        assert bak.exists()
        bak_data = json.loads(bak.read_text(encoding="utf-8"))
        assert bak_data["translations"]["Hello"]["zh"] == "你好"  # original
    print("[OK] test_import_to_v2_envelope")


def test_extract_from_v2_exposes_full_languages_dict():
    """Round 34 C3: ``_extract_from_v2_envelope`` populates a per-entry
    ``languages`` dict containing every language bucket for that original,
    not just the single ``--v2-lang`` target.  Needed so the in-page
    dropdown can swap translations without re-running the CLI.
    """
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        v2_path = td_path / "multi.json"
        _make_v2_envelope(v2_path, {
            "Hello": {"zh": "你好", "ja": "こんにちは", "ko": "안녕하세요"},
            "World": {"zh": "世界"},  # only zh bucket
        }, default_lang="zh")

        entries = _extract_from_db(v2_path)
        by_orig = {e["original"]: e for e in entries}

        # "Hello" has 3 languages — all present in the per-entry dict.
        assert by_orig["Hello"]["languages"] == {
            "zh": "你好", "ja": "こんにちは", "ko": "안녕하세요",
        }
        # "World" has just zh — the dict reflects that.
        assert by_orig["World"]["languages"] == {"zh": "世界"}
        # v2_langs_seen still present (round 33 compat) — reflects union
        # across every original's buckets.
        assert by_orig["Hello"]["v2_langs_seen"] == ["ja", "ko", "zh"]
    print("[OK] test_extract_from_v2_exposes_full_languages_dict")


def test_v2_html_includes_language_switch_dropdown():
    """Round 34 C3: exported HTML contains the ``<select id="v2-lang-switch">``
    dropdown element + the ``switchV2Language`` JS function + the
    ``_edits`` state object.  Regression guard against a future edit
    silently removing the in-page language switch.
    """
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        v2_path = td_path / "multi.json"
        _make_v2_envelope(v2_path, {
            "Hello": {"zh": "你好", "ja": "こんにちは"},
        }, default_lang="zh")
        entries = _extract_from_db(v2_path)

        out = td_path / "review.html"
        count = export_html(entries, out)
        assert count == 1
        html = out.read_text(encoding="utf-8")
        # Dropdown + label wiring present.
        assert 'id="v2-lang-switch"' in html
        assert 'id="v2-lang-switch-label"' in html
        # Per-row language state machine present.
        assert "switchV2Language" in html
        assert "_edits" in html
        assert "_currentV2Lang" in html
        # ``languages`` dict gets embedded into the metadata JSON.
        meta_start = html.index('id="metadata">') + len('id="metadata">')
        meta_end = html.index("</script>", meta_start)
        meta = json.loads(html[meta_start:meta_end])
        assert meta[0]["languages"] == {"zh": "你好", "ja": "こんにちは"}

        # Non-v2 HTML (tl mode): dropdown element is still there (static
        # HTML) but label wrapper stays ``display:none`` via CSS.
        tl_entries = [
            {"source": "tl", "file": "game/tl/chinese/a.rpy", "line": 1,
             "original": "Hi", "translation": "嗨",
             "character": "", "identifier": "",
             "source_file": "a.rpy", "source_line": 1},
        ]
        out2 = td_path / "tl.html"
        export_html(tl_entries, out2)
        html2 = out2.read_text(encoding="utf-8")
        # Label starts hidden; JS only reveals it when a v2 entry exists.
        assert 'id="v2-lang-switch-label" style="display:none;"' in html2
    print("[OK] test_v2_html_includes_language_switch_dropdown")


def test_export_edits_multi_language_produces_per_lang_records():
    """Round 34 C3: when the exported edits JSON contains records for the
    SAME original with DIFFERENT ``v2_lang`` values, ``_apply_v2_edits``
    writes each to its own bucket and leaves sibling buckets untouched.
    Simulates the browser-side multi-language edit flow.

    Round 37 M4: tempdir under CWD so the ``_apply_v2_edits`` path
    whitelist accepts the test-generated v2_path.
    """
    with tempfile.TemporaryDirectory(dir=str(Path.cwd())) as td:
        td_path = Path(td)
        v2_path = td_path / "multi.json"
        _make_v2_envelope(v2_path, {
            "Hello": {"zh": "你好", "ja": "こんにちは"},
        }, default_lang="zh")

        # Synthesise the shape exportEdits() emits when the user edits
        # both language buckets for the same original.
        edits = [
            {"source": "v2", "file": str(v2_path), "line": 1,
             "original": "Hello", "old_translation": "你好",
             "new_translation": "您好", "identifier": "",
             "v2_path": str(v2_path), "v2_lang": "zh"},
            {"source": "v2", "file": str(v2_path), "line": 1,
             "original": "Hello", "old_translation": "こんにちは",
             "new_translation": "こんにちは〜", "identifier": "",
             "v2_path": str(v2_path), "v2_lang": "ja"},
        ]
        edits_path = td_path / "edits.json"
        edits_path.write_text(json.dumps(edits), encoding="utf-8")

        result = import_edits(edits_path, create_backup=False)
        assert result["applied"] == 2
        assert result["files_modified"] == 1

        loaded = json.loads(v2_path.read_text(encoding="utf-8"))
        assert loaded["translations"]["Hello"] == {
            "zh": "您好", "ja": "こんにちは〜",
        }
    print("[OK] test_export_edits_multi_language_produces_per_lang_records")


def test_side_by_side_toggle_and_styles_present_in_html():
    """Round 35 C3: exported HTML includes the side-by-side checkbox
    element, ``toggleSideBySide`` JS function, ``col-trans-multi`` CSS
    class, and the per-cell event-binding helper.  Regression guard so
    a future edit silently removing any of these pieces gets caught.
    """
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        v2_path = td_path / "multi.json"
        _make_v2_envelope(v2_path, {
            "Hello": {"zh": "你好", "ja": "こんにちは"},
        }, default_lang="zh")
        entries = _extract_from_db(v2_path)
        out = td_path / "review.html"
        export_html(entries, out)
        html = out.read_text(encoding="utf-8")
        # Checkbox + toggle JS + side-by-side helper exist.
        assert 'id="v2-side-by-side"' in html
        assert 'onchange="toggleSideBySide(this.checked)"' in html
        assert "toggleSideBySide" in html
        assert "_bindSideBySideCellEvents" in html
        assert "_sideBySideOn" in html
        # Dedicated CSS class for multi-column translation cells.
        assert ".col-trans-multi" in html
    print("[OK] test_side_by_side_toggle_and_styles_present_in_html")


def test_side_by_side_label_hidden_by_default():
    """Round 35 C3: the side-by-side toggle label is rendered with
    ``style="display:none;"`` in the base HTML; JS reveals it only
    when the envelope has 2+ languages (so single-bucket v2 files /
    v1 / tl-mode exports see zero multi-language chrome).
    """
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        # Single-language v2 — dropdown visible but side-by-side stays hidden.
        v2_path = td_path / "one.json"
        _make_v2_envelope(v2_path, {
            "Hello": {"zh": "你好"},
        }, default_lang="zh")
        entries = _extract_from_db(v2_path)
        out = td_path / "single.html"
        export_html(entries, out)
        html = out.read_text(encoding="utf-8")
        # Label wrapper starts display:none in the static HTML.
        assert 'id="v2-side-by-side-label" style="display:none;"' in html
        # The JS reveal-predicate references the 2+ threshold.
        assert "langsSeen.length >= 2" in html
    print("[OK] test_side_by_side_label_hidden_by_default")


def test_side_by_side_preserves_dropdown_coexistence():
    """Round 35 C3: side-by-side checkbox does NOT replace the round-34
    dropdown — both live in the toolbar so operators can still use the
    single-language focus mode after toggling off.  Regression guard so
    nobody optimises the dropdown out by mistake.
    """
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        v2_path = td_path / "multi.json"
        _make_v2_envelope(v2_path, {
            "Hello": {"zh": "你好", "ja": "こんにちは"},
        }, default_lang="zh")
        entries = _extract_from_db(v2_path)
        out = td_path / "review.html"
        export_html(entries, out)
        html = out.read_text(encoding="utf-8")
        # Both UI elements present in the toolbar.
        assert 'id="v2-lang-switch"' in html
        assert 'id="v2-side-by-side"' in html
        # Dropdown's switchV2Language still wired up.
        assert "switchV2Language" in html
        # Flush-before-toggle logic (dropdown edits go into _edits before
        # side-by-side rebuilds the DOM) prevents work loss.
        assert "flush any in-flight DOM edit" in html
    print("[OK] test_side_by_side_preserves_dropdown_coexistence")


def test_v2_envelope_preserves_non_edited_languages():
    """Round 33 Subtask 3: editing one language bucket must not disturb
    any other language bucket in the same original's dict, nor any
    untouched original's translations, nor top-level envelope metadata.

    Round 37 M4: tempdir under CWD so the ``_apply_v2_edits`` path
    whitelist accepts the test-generated v2_path.
    """
    with tempfile.TemporaryDirectory(dir=str(Path.cwd())) as td:
        td_path = Path(td)
        v2_path = td_path / "merged.json"
        _make_v2_envelope(v2_path, {
            "Hello": {"zh": "你好", "ja": "こんにちは", "ko": "안녕하세요"},
            "World": {"zh": "世界", "ja": "世界"},
        }, default_lang="zh")

        edits = [{
            "source": "v2",
            "v2_path": str(v2_path),
            "v2_lang": "zh",
            "file": str(v2_path),
            "line": 1,
            "original": "Hello",
            "old_translation": "你好",
            "new_translation": "您好",
        }]
        edits_path = td_path / "edits.json"
        edits_path.write_text(json.dumps(edits), encoding="utf-8")

        result = import_edits(edits_path, create_backup=False)
        assert result["applied"] == 1

        loaded = json.loads(v2_path.read_text(encoding="utf-8"))
        # Envelope top-level keys intact.
        assert loaded["_schema_version"] == 2
        assert loaded["_format"] == "renpy-translate"
        assert loaded["default_lang"] == "zh"
        # Edited bucket changed.
        assert loaded["translations"]["Hello"]["zh"] == "您好"
        # Sibling language buckets UNCHANGED byte-for-byte.
        assert loaded["translations"]["Hello"]["ja"] == "こんにちは"
        assert loaded["translations"]["Hello"]["ko"] == "안녕하세요"
        # Other originals UNCHANGED.
        assert loaded["translations"]["World"] == {"zh": "世界", "ja": "世界"}
    print("[OK] test_v2_envelope_preserves_non_edited_languages")


def test_apply_v2_edits_rejects_path_outside_cwd():
    """Round 37 M4: ``_apply_v2_edits`` must skip edits whose ``v2_path``
    resolves to a file outside the current working directory.  Prevents
    a crafted / stale ``translation_edits.json`` from hijacking writes
    over arbitrary filesystem paths on the operator's machine.

    A corresponding edit with an under-CWD path is kept in the same call
    so the test also confirms that legitimate edits still apply when
    mixed with a rejected one.
    """
    import shutil
    import tempfile
    from tools.translation_editor import _apply_v2_edits

    # Write an under-CWD v2 envelope so the legit edit can apply.
    ok_dir = Path(tempfile.mkdtemp(prefix="_m4_ok_", dir=str(Path.cwd())))
    # Write a sibling envelope outside CWD (system tempdir on every
    # platform we support is NOT under project CWD).
    outside_dir = Path(tempfile.mkdtemp(prefix="_m4_out_"))
    try:
        envelope = {
            "_schema_version": 2,
            "_format": "renpy-translate",
            "default_lang": "zh",
            "translations": {"Hi": {"zh": "原始"}},
        }
        ok_path = ok_dir / "ok.json"
        outside_path = outside_dir / "out.json"
        ok_path.write_text(json.dumps(envelope), encoding="utf-8")
        outside_path.write_text(json.dumps(envelope), encoding="utf-8")

        edits = [
            {"v2_path": str(outside_path), "v2_lang": "zh",
             "original": "Hi", "new_translation": "攻击者控制"},
            {"v2_path": str(ok_path), "v2_lang": "zh",
             "original": "Hi", "new_translation": "合法编辑"},
        ]
        result = _apply_v2_edits(edits, create_backup=False)
        assert result["applied"] == 1, (
            "M4: legit under-CWD edit must still apply"
        )
        assert result["skipped"] == 1, (
            "M4: outside-CWD edit must be skipped"
        )
        assert result["files_modified"] == 1, (
            "M4: only the under-CWD file must be modified"
        )
        # Outside-CWD file must be byte-identical (untouched).
        outside_loaded = json.loads(outside_path.read_text(encoding="utf-8"))
        assert outside_loaded["translations"]["Hi"]["zh"] == "原始", (
            "M4: outside-CWD file must not be written to"
        )
        # Under-CWD file must have the legit new translation.
        ok_loaded = json.loads(ok_path.read_text(encoding="utf-8"))
        assert ok_loaded["translations"]["Hi"]["zh"] == "合法编辑"
    finally:
        shutil.rmtree(ok_dir, ignore_errors=True)
        shutil.rmtree(outside_dir, ignore_errors=True)


# ============================================================
# Runner
# ============================================================

ALL_TESTS = [
    test_export_basic,
    test_export_multiple,
    test_export_empty,
    test_export_html_escaping,
    test_extract_from_tl,
    test_extract_from_db,
    test_import_tl_mode,
    test_import_empty_slot,
    test_import_db_mode,
    test_import_no_overwrite_backup,
    test_import_missing_file,
    test_import_empty_new_translation,
    test_escape_for_rpy,
    # Round 33 Subtask 3 — v2 envelope read/write
    test_extract_from_v2_envelope,
    test_import_to_v2_envelope,
    test_v2_envelope_preserves_non_edited_languages,
    # Round 34 Commit 3 — in-page multi-language switch
    test_extract_from_v2_exposes_full_languages_dict,
    test_v2_html_includes_language_switch_dropdown,
    test_export_edits_multi_language_produces_per_lang_records,
    # Round 35 Commit 3 — side-by-side multi-column display
    test_side_by_side_toggle_and_styles_present_in_html,
    test_side_by_side_label_hidden_by_default,
    test_side_by_side_preserves_dropdown_coexistence,
    # Round 37 M4 — v2_path CWD whitelist
    test_apply_v2_edits_rejects_path_outside_cwd,
]


if __name__ == "__main__":
    passed = 0
    failed = 0
    for t in ALL_TESTS:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {t.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    total = passed + failed
    if failed:
        print(f"\n{passed}/{total} PASSED, {failed} FAILED")
        sys.exit(1)
    else:
        print(f"\nALL {total} TRANSLATION EDITOR TESTS PASSED")
