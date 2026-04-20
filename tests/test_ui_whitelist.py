#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UI whitelist tests — split from ``tests/test_file_processor.py`` in
round 45 because the parent file reached 830 lines (over CLAUDE.md 800
soft limit) after the r32 configurable-whitelist feature plus the
r44 audit-tail oversize-file test.  The UI whitelist is a
self-contained public-API slice (``is_common_ui_button`` /
``load_ui_button_whitelist`` / ``clear_ui_button_whitelist`` /
``add_ui_button_whitelist`` / ``get_ui_button_whitelist_extensions`` /
``COMMON_UI_BUTTONS``) — a clean cut point.

Coverage (byte-identical copies of the r31 / r32 / r44 tests):
  * Round 31 Tier A-1: ``is_common_ui_button`` detector
    (case / whitespace / non-string)
  * Round 32 Commit 2: configurable sidecar loaders (.txt / .json),
    builtin-baseline isolation, clear/rebuild semantics,
    frozenset-rebind thread-safety contract
  * Round 44 audit-tail: 50 MB size cap on whitelist files

Leaves the r31 Tier A-2 placeholder-drift tests (``fix_chinese_
placeholder_drift`` + ``_filter_checked_translations_fixes_
placeholder_drift``) in ``test_file_processor.py`` — those cover
a different feature (placeholder normalisation), not UI whitelist.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_is_common_ui_button():
    """Round 31 Tier A-1: common UI button detector normalises case + whitespace."""
    from file_processor import is_common_ui_button, COMMON_UI_BUTTONS

    # Curated buttons from the imported competitor hook list must match.
    for word in ("OK", "Cancel", "Save", "Quit", "Main Menu", "Preferences"):
        assert is_common_ui_button(word), f"{word!r} should be detected"

    # Case-insensitive.
    assert is_common_ui_button("ok")
    assert is_common_ui_button("OK")
    assert is_common_ui_button("Ok")

    # Whitespace normalisation.
    assert is_common_ui_button("  Save  ")
    assert is_common_ui_button("main   menu")  # collapsed to "main menu"

    # Genuine dialogue must NOT match.
    assert not is_common_ui_button("Hello world")
    assert not is_common_ui_button("Save the cat")  # "save" alone matches, multi-word shouldn't

    # Empty / non-string handled gracefully.
    assert not is_common_ui_button("")
    assert not is_common_ui_button("   ")
    assert not is_common_ui_button(None)  # type: ignore[arg-type]
    assert not is_common_ui_button(42)    # type: ignore[arg-type]

    # Whitelist export has the expected shape.
    assert isinstance(COMMON_UI_BUTTONS, frozenset)
    assert "cancel" in COMMON_UI_BUTTONS  # all entries lowercased
    print("[OK] is_common_ui_button")


def test_load_ui_button_whitelist_txt():
    """Round 32 Commit 2: .txt whitelist loader honours UTF-8-sig, skips
    ``#`` comments + blank lines, and feeds ``is_common_ui_button``.
    """
    import tempfile
    from pathlib import Path
    from file_processor import (
        clear_ui_button_whitelist,
        load_ui_button_whitelist,
        is_common_ui_button,
        get_ui_button_whitelist_extensions,
    )

    clear_ui_button_whitelist()

    # Content includes a BOM, a comment, a blank line, mixed case, and
    # whitespace variants we expect to normalise to the same token.
    content = "\ufeff# customised UI buttons\n存档\n读档\n\n  Main Hub  \n# trailing comment\nProceed\n"
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8") as f:
        f.write(content)
        tmp_path = f.name
    try:
        added = load_ui_button_whitelist([tmp_path])
        # 4 distinct tokens: 存档 / 读档 / main hub / proceed (comments + blanks skipped)
        assert added == 4, f"expected 4 new entries, got {added}"

        # Python-side lookups must now succeed (including normalisation).
        assert is_common_ui_button("存档")
        assert is_common_ui_button("读档")
        assert is_common_ui_button("main hub")
        assert is_common_ui_button("Main Hub")  # case-insensitive
        assert is_common_ui_button("  main   hub  ")  # whitespace collapse
        assert is_common_ui_button("Proceed")
        assert is_common_ui_button("proceed")

        # Baseline entries are still recognised.
        assert is_common_ui_button("OK")
        assert is_common_ui_button("Save")

        # Unrelated strings still fail.
        assert not is_common_ui_button("Hello world")

        # Replaying the same file is a no-op.
        added_again = load_ui_button_whitelist([tmp_path])
        assert added_again == 0

        # Extensions snapshot is a frozenset containing just the new tokens.
        ext = get_ui_button_whitelist_extensions()
        assert isinstance(ext, frozenset)
        assert "存档" in ext
        assert "main hub" in ext
        # Baseline must NOT leak into the extension snapshot.
        assert "ok" not in ext
    finally:
        Path(tmp_path).unlink()
        clear_ui_button_whitelist()
    print("[OK] load_ui_button_whitelist_txt")


def test_load_ui_button_whitelist_json():
    """Round 32 Commit 2: .json whitelist loader accepts top-level list of
    strings and rejects other shapes with a warning.
    """
    import json as _json
    import tempfile
    from pathlib import Path
    from file_processor import (
        clear_ui_button_whitelist,
        load_ui_button_whitelist,
        is_common_ui_button,
    )

    clear_ui_button_whitelist()

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w", encoding="utf-8") as f:
        _json.dump(["存档", "读档", "Proceed", 42, None, "  back to menu  "], f, ensure_ascii=False)
        good_path = f.name
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w", encoding="utf-8") as f:
        _json.dump({"not": "a list"}, f)
        bad_path = f.name
    try:
        # Good file: list with 3 strings (non-strings silently dropped).
        added = load_ui_button_whitelist([good_path])
        # 存档 / 读档 / proceed / back to menu = 4 distinct tokens
        assert added == 4, f"expected 4 new entries, got {added}"
        assert is_common_ui_button("存档")
        assert is_common_ui_button("Proceed")
        assert is_common_ui_button("Back to Menu")

        # Bad shape: warning path, nothing added.
        added_bad = load_ui_button_whitelist([bad_path])
        assert added_bad == 0

        # Missing file: warning path, nothing added.
        added_missing = load_ui_button_whitelist(["/does/not/exist/ever.json"])
        assert added_missing == 0
    finally:
        Path(good_path).unlink()
        Path(bad_path).unlink()
        clear_ui_button_whitelist()
    print("[OK] load_ui_button_whitelist_json")


def test_ui_button_whitelist_builtin_untouched():
    """Round 32 Commit 2: loading extensions must not mutate the baseline
    ``COMMON_UI_BUTTONS`` frozenset — it stays the same object identity
    and the same contents.
    """
    from file_processor import (
        clear_ui_button_whitelist,
        add_ui_button_whitelist,
        COMMON_UI_BUTTONS,
    )

    clear_ui_button_whitelist()
    baseline_id = id(COMMON_UI_BUTTONS)
    baseline_len = len(COMMON_UI_BUTTONS)

    add_ui_button_whitelist(["扩展按钮 A", "扩展按钮 B"])

    # Re-import to simulate a fresh reader — the module-level constant
    # must still be the exact same frozenset object.
    from file_processor import COMMON_UI_BUTTONS as COMMON_UI_BUTTONS_RELOADED
    assert id(COMMON_UI_BUTTONS_RELOADED) == baseline_id
    assert len(COMMON_UI_BUTTONS_RELOADED) == baseline_len
    assert "扩展按钮 A".lower() not in COMMON_UI_BUTTONS_RELOADED

    clear_ui_button_whitelist()
    print("[OK] ui_button_whitelist_builtin_untouched")


def test_clear_ui_button_whitelist_restores_baseline():
    """Round 32 Commit 2: ``clear_ui_button_whitelist`` drops every
    extension while keeping the baseline untouched.
    """
    from file_processor import (
        clear_ui_button_whitelist,
        add_ui_button_whitelist,
        is_common_ui_button,
        get_ui_button_whitelist_extensions,
    )

    clear_ui_button_whitelist()
    add_ui_button_whitelist(["存档", "读档"])
    assert is_common_ui_button("存档")
    assert len(get_ui_button_whitelist_extensions()) == 2

    clear_ui_button_whitelist()
    assert not is_common_ui_button("存档")
    assert not is_common_ui_button("读档")
    assert get_ui_button_whitelist_extensions() == frozenset()

    # Baseline must still be reachable after clear.
    assert is_common_ui_button("OK")
    assert is_common_ui_button("Save")
    print("[OK] clear_ui_button_whitelist_restores_baseline")


def test_ui_button_whitelist_rebinds_frozenset():
    """Round 32 Commit 2: ``_ui_button_extensions`` is REBOUND, not mutated,
    on every add/clear.  This is the thread-safety contract — a worker
    thread that captured a reference to the previous frozenset must still
    see a stable snapshot while the main thread extends the whitelist.
    """
    from file_processor import (
        clear_ui_button_whitelist,
        add_ui_button_whitelist,
        get_ui_button_whitelist_extensions,
    )

    clear_ui_button_whitelist()
    snap_empty = get_ui_button_whitelist_extensions()
    assert isinstance(snap_empty, frozenset)

    add_ui_button_whitelist(["alpha"])
    snap_alpha = get_ui_button_whitelist_extensions()
    # Rebind: different object identity from the empty snapshot.
    assert snap_alpha is not snap_empty
    # Prior snapshot is unchanged (frozenset, not mutated).
    assert snap_empty == frozenset()
    assert snap_alpha == frozenset({"alpha"})

    add_ui_button_whitelist(["beta"])
    snap_both = get_ui_button_whitelist_extensions()
    assert snap_both is not snap_alpha
    assert snap_alpha == frozenset({"alpha"})  # still immutable
    assert snap_both == frozenset({"alpha", "beta"})

    clear_ui_button_whitelist()
    print("[OK] ui_button_whitelist_rebinds_frozenset")


def test_load_ui_button_whitelist_rejects_oversized_file():
    """Round 44 audit-tail: load_ui_button_whitelist skips
    operator-supplied UI whitelist files above the 50 MB cap with a
    warning rather than loading the whole file into memory.  Missed by
    the r37-r43 M2 phases because r32's whitelist loader pre-dated the
    size-gate idiom.  Uses a 51 MB sparse file to exercise the cap
    without consuming disk."""
    import tempfile
    from pathlib import Path
    from file_processor import (
        clear_ui_button_whitelist,
        load_ui_button_whitelist,
        get_ui_button_whitelist_extensions,
    )

    clear_ui_button_whitelist()

    with tempfile.TemporaryDirectory() as td:
        # Oversized .json whitelist — should be skipped entirely.
        big_path = Path(td) / "huge_whitelist.json"
        with open(big_path, "wb") as f:
            f.seek(51 * 1024 * 1024 - 1)
            f.write(b"\0")

        added = load_ui_button_whitelist([str(big_path)])
        assert added == 0, (
            f"oversized whitelist file must be skipped (no entries added), "
            f"got added={added}"
        )
        # Extensions snapshot should remain empty (no new entries).
        assert get_ui_button_whitelist_extensions() == frozenset(), (
            "oversized whitelist must not populate extensions"
        )

    clear_ui_button_whitelist()
    print("[OK] load_ui_button_whitelist_rejects_oversized_file")


ALL_TESTS = [
    # Round 31 Tier A-1
    test_is_common_ui_button,
    # Round 32 Commit 2
    test_load_ui_button_whitelist_txt,
    test_load_ui_button_whitelist_json,
    test_ui_button_whitelist_builtin_untouched,
    test_clear_ui_button_whitelist_restores_baseline,
    test_ui_button_whitelist_rebinds_frozenset,
    # Round 44 audit-tail
    test_load_ui_button_whitelist_rejects_oversized_file,
]


if __name__ == "__main__":
    for t in ALL_TESTS:
        t()
    print()
    print("=" * 40)
    print(f"ALL {len(ALL_TESTS)} UI WHITELIST TESTS PASSED")
    print("=" * 40)
