#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round 51 contract test - GitHub repo rename + logger namespace sync.

Why:
    Round 51 renamed the GitHub repo Renpy-Translator ->
    Multi-Engine-Game-Translator and renamed the project-wide logger
    namespace renpy_translator -> multi_engine_translator (17 sites).
    This test pins the rename so a future commit cannot accidentally
    reintroduce the old names while remaining type/lint-clean.

    It also guards against the inverse failure mode: an over-eager
    sed/grep replacement removing the upstream attribution to
    anonymousException's renpy-translator (MIT, 2024) project, which
    must remain intact in 6 hooks/tools files for license compliance.

How to apply:
    Independent CI step (.github/workflows/test.yml).  Top-level
    ``def test_*`` functions matching the project convention so
    ``scripts/verify_docs_claims.py`` AST counter sees them.
    Stdlib-only.
"""

from __future__ import annotations

import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SELF_PATH = pathlib.Path(__file__).resolve()

# 6 upstream attribution files - reference anonymousException's
# unrelated-but-similarly-named MIT project; must stay verbatim.
UPSTREAM_ATTRIBUTION_FILES = (
    "resources/hooks/extract_hook.rpy",
    "resources/hooks/inject_hook.rpy",
    "resources/hooks/language_switcher.rpy",
    "tools/renpy_lint_fixer.py",
    "tools/rpa_unpacker.py",
    "tools/rpyc_decompiler.py",
)

# Directories excluded from the orphan-logger scan (build artifacts /
# vcs / output trees / venv-style locations).
SKIP_PARTS = ("__pycache__", "output", ".git", "build", "dist", ".venv", "venv")


def test_pyproject_no_orphan_repo_refs():
    """pyproject.toml must not reference the old repo / package name."""
    content = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "Renpy-Translator" not in content, (
        "pyproject.toml still contains old repo name 'Renpy-Translator'"
    )
    assert 'name = "renpy-translator"' not in content, (
        "pyproject.toml still uses old package name 'renpy-translator'"
    )
    assert 'name = "multi-engine-game-translator"' in content, (
        "pyproject.toml missing new package name 'multi-engine-game-translator'"
    )
    assert (
        "https://github.com/Dean20030514/Multi-Engine-Game-Translator" in content
    ), "pyproject.toml Repository URL not updated to new GitHub repo"
    print("[OK] test_pyproject_no_orphan_repo_refs")


def test_example_json_no_orphan_repo_refs():
    """renpy_translate.example.json $schema must use the new URL."""
    content = (REPO_ROOT / "renpy_translate.example.json").read_text(encoding="utf-8")
    assert "Renpy-Translator" not in content, (
        "renpy_translate.example.json still contains old repo URL"
    )
    assert (
        "https://github.com/Dean20030514/Multi-Engine-Game-Translator" in content
    ), "renpy_translate.example.json $schema not updated to new repo URL"
    print("[OK] test_example_json_no_orphan_repo_refs")


def test_logger_namespace_renamed_no_orphan_callsites():
    """No file may use getLogger("renpy_translator") - all 17 sites moved."""
    pattern = re.compile(r"""getLogger\(["']renpy_translator["']\)""")
    offenders = []
    for py in REPO_ROOT.glob("**/*.py"):
        if any(part in py.parts for part in SKIP_PARTS):
            continue
        # Skip this file - it contains the regex pattern as a string
        # literal which would otherwise self-flag.
        if py.resolve() == SELF_PATH:
            continue
        try:
            content = py.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if pattern.search(content):
            offenders.append(str(py.relative_to(REPO_ROOT)))
    assert offenders == [], (
        f"orphan getLogger('renpy_translator') still present in: {offenders} "
        f"- Round 51 A4 should have moved every site to "
        f"'multi_engine_translator'."
    )
    print("[OK] test_logger_namespace_renamed_no_orphan_callsites")


def test_upstream_attribution_preserved():
    """6 upstream attribution refs to anonymousException must stay verbatim."""
    for rel in UPSTREAM_ATTRIBUTION_FILES:
        path = REPO_ROOT / rel
        assert path.exists(), f"upstream attribution file missing: {rel}"
        content = path.read_text(encoding="utf-8", errors="ignore")
        assert "renpy-translator" in content, (
            f"upstream attribution to anonymousException's renpy-translator "
            f"(MIT, 2024) removed from {rel} - this is a license-compliance "
            f"violation; the rename only applies to self-references."
        )
        assert "anonymousException" in content, (
            f"upstream author attribution removed from {rel}"
        )
    print("[OK] test_upstream_attribution_preserved")


TESTS = [
    test_pyproject_no_orphan_repo_refs,
    test_example_json_no_orphan_repo_refs,
    test_logger_namespace_renamed_no_orphan_callsites,
    test_upstream_attribution_preserved,
]


def run_all() -> int:
    """Run every registered test in registration order and return
    the count for the ``ALL N PASSED`` summary line."""
    for t in TESTS:
        t()
    return len(TESTS)


if __name__ == "__main__":
    n = run_all()
    print()
    print("=" * 40)
    print(f"ALL {n} REPO RENAME CONSISTENCY TESTS PASSED")
    print("=" * 40)
