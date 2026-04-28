#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round 49: cross-doc claim drift checker.

Breaks the r45-r48 "HANDOFF / CHANGELOG / CLAUDE / .cursorrules
all claim slightly different numbers because each round used the
*previous round's claim* as a baseline" cycle.  See
``CHANGELOG_RECENT.md`` round 48 audit-tail for the four drift
incidents that motivated this tool (test count / file count /
CI step / line count) — each one was caught by the user running
independent ``find/wc/grep`` and noticing the docs disagreed
with reality.

Source-of-truth contract
------------------------

The fenced ``<!-- VERIFIED-CLAIMS-START -->...<!-- END -->`` block
in ``HANDOFF.md`` is the *only* place numbers are declared.  Every
other doc (``CHANGELOG_RECENT.md`` / ``CLAUDE.md`` / ``.cursorrules``
/ this file's docstring even) references those declared numbers in
prose but does not re-declare them.  When the round-end docs sync
runs, only the fenced block needs updating; the prose around it
points the reader at "see VERIFIED-CLAIMS block".

Four checked dimensions
-----------------------

1. ``tests_total`` — sum of ``ALL N`` across every CI ``Run *`` step
   in ``.github/workflows/test.yml``.  Re-derived by ``--full`` only
   (running suites takes ~30-60s).  ``--fast`` skips this.
2. ``test_files`` — count of ``tests/test_*.py`` plus the legacy
   ``tests/smoke_test.py`` (which doesn't match the ``test_*.py``
   prefix but is part of the suite).  Cheap to derive.
3. ``ci_steps`` — ``len(jobs.test.steps)`` in the workflow yaml.
   Cheap.
4. ``assertion_points`` — ``tests_total + tl_parser self-tests +
   screen self-tests``.  The latter two are parsed from step names
   like ``Run tl_parser self-tests (75 assertions)``.  Re-derived
   by ``--full`` only.

Plus a fifth fail-fast guard:

5. **No .py file > 800 lines** — equivalent to the user-supplied
   ``find . -name "*.py" -not -path "./.git/*" -not -path
   "./_archive/*" | xargs wc -l | awk '$1>800 && $2!="total"'``
   one-liner, but in stdlib Python so it works the same on
   Windows / Linux / macOS without bash dependencies.

Usage
-----

::

    python scripts/verify_docs_claims.py            # equivalent to --fast
    python scripts/verify_docs_claims.py --fast     # explicit
    python scripts/verify_docs_claims.py --full     # CI / pre-push depth
    python scripts/verify_docs_claims.py --repo-root /tmp/fixture --fast

Exits 0 on no drift, 1 on any drift.  Prints a summary table
identifying which dimensions disagree.

Dependencies
------------

PyYAML for the workflow parse — same as ``scripts/verify_workflow.py``.
This is the project's only dev-tool exception to the zero-dependency
policy (production code stays stdlib-only; see CLAUDE.md).
"""

from __future__ import annotations

import argparse
import ast
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable

try:
    import yaml
except ImportError:
    print(
        "[verify-docs-claims] ERROR: PyYAML not installed.  Install with:\n"
        "    pip install pyyaml --break-system-packages",
        file=sys.stderr,
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

REPO_ROOT_DEFAULT = Path(__file__).resolve().parent.parent
DEFAULT_MAX_LINES = 800
DEFAULT_IGNORE_PATH_PARTS = (".git", "_archive", "__pycache__", "output")
CLAIM_BLOCK_START = "<!-- VERIFIED-CLAIMS-START -->"
CLAIM_BLOCK_END = "<!-- VERIFIED-CLAIMS-END -->"

# All four canonical claim keys are derived statically (AST + yaml) so
# both ``--fast`` and ``--full`` can verify them without the 30-60s
# subprocess sweep.  ``--full`` additionally executes every CI test
# step as a passing-suite sanity check.
ALL_CLAIM_KEYS = ("tests_total", "test_files", "ci_steps", "assertion_points")


# ---------------------------------------------------------------------------
# Helpers — each returns a primitive that ``main`` can compare against
# the parsed claim dict.
# ---------------------------------------------------------------------------


def find_oversized_py_files(
    root: Path,
    max_lines: int = DEFAULT_MAX_LINES,
    ignore_path_parts: Iterable[str] = DEFAULT_IGNORE_PATH_PARTS,
) -> list[tuple[Path, int]]:
    """Walk ``root`` recursively, return ``(path, line_count)`` for
    every ``.py`` whose newline count strictly exceeds ``max_lines``.

    Path filtering matches the user-supplied awk one-liner: any
    component of the relative path equal to one of the ignore parts
    skips the file.  This lines up with ``find ... -not -path
    "./_archive/*"`` semantics.
    """
    ignore_set = set(ignore_path_parts)
    oversized: list[tuple[Path, int]] = []
    for py in root.rglob("*.py"):
        try:
            rel_parts = py.relative_to(root).parts
        except ValueError:
            rel_parts = py.parts
        if any(part in ignore_set for part in rel_parts):
            continue
        # Count newline bytes — equivalent to ``wc -l`` and avoids
        # decoding / list-building on large files.
        try:
            with open(py, "rb") as f:
                line_count = 0
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    line_count += chunk.count(b"\n")
        except OSError:
            continue
        if line_count > max_lines:
            oversized.append((py, line_count))
    return oversized


def _is_test_module(entry: Path) -> bool:
    """``test_*.py`` plus the legacy ``smoke_test.py`` (which doesn't
    use the standard prefix but is part of the suite)."""
    if not entry.is_file() or entry.suffix != ".py":
        return False
    name = entry.name
    return name.startswith("test_") or name == "smoke_test.py"


def count_test_files(tests_dir: Path) -> int:
    """Count test modules directly under ``tests_dir`` (non-recursive
    — fixtures / artifacts subdirs do not contribute to the suite
    count)."""
    if not tests_dir.is_dir():
        return 0
    return sum(1 for entry in tests_dir.iterdir() if _is_test_module(entry))


def count_test_functions_in_module(test_file: Path) -> int:
    """AST-count top-level ``def test_*`` (and ``async def test_*``)
    in ``test_file``.  This is the canonical per-file test count: it
    does not require running the file, handles every test-naming
    convention used in this project (``ALL N PASSED`` literal, Chinese
    ``=== 全部 X 测试通过 ===`` literal, no terminal print at all),
    and matches the way ``def test_*`` is registered in the per-file
    ``TESTS = [...]`` registries.

    Returns 0 on syntax error (the build hooks catch syntax errors
    via ``py_compile`` upstream — this fail-open keeps the drift
    checker resilient to in-progress edits)."""
    try:
        tree = ast.parse(test_file.read_text(encoding="utf-8"))
    except (SyntaxError, OSError):
        return 0
    n = 0
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test_"):
                n += 1
    return n


def derive_tests_total(tests_dir: Path) -> int:
    """Sum ``count_test_functions_in_module`` across every test module
    in ``tests_dir``.  Pre-r49 this lived as a runtime ``ALL N``
    parser, but six suites in this project print Chinese summary
    lines (``=== 全部 X 测试通过 ===``) instead of ``ALL N PASSED``,
    so AST is the only universally-correct counter."""
    if not tests_dir.is_dir():
        return 0
    total = 0
    for entry in tests_dir.iterdir():
        if _is_test_module(entry):
            total += count_test_functions_in_module(entry)
    return total


def count_ci_steps(workflow_path: Path) -> int:
    """Parse the workflow yaml and return ``len(jobs.test.steps)``.

    Raises ``KeyError`` if the structure is missing required keys —
    callers should treat that as a structural error rather than a
    soft drift (the workflow is broken, not the claim).
    """
    with open(workflow_path, encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    steps = doc["jobs"]["test"]["steps"]
    return len(steps)


_CLAIM_LINE_RE = re.compile(r"^\s*([a-z_]+)\s*:\s*(\d+)\b")


def parse_claims(handoff_path: Path) -> dict[str, int]:
    """Return ``{key: int}`` parsed from the fenced
    ``VERIFIED-CLAIMS`` block in ``handoff_path``.

    Raises ``ValueError`` if the block is missing — without it the
    verifier has no source of truth to compare reality against, so
    callers must surface the absence as a setup failure.

    Inline comments after the value (``key: 33  # comment``) are
    tolerated by the regex, which only consumes leading whitespace,
    the key, the colon, and the int.
    """
    text = handoff_path.read_text(encoding="utf-8")
    start = text.find(CLAIM_BLOCK_START)
    end = text.find(CLAIM_BLOCK_END)
    if start < 0 or end < 0 or end <= start:
        raise ValueError(
            f"VERIFIED-CLAIMS block not found in {handoff_path}.  "
            f"Add the fenced block:\n"
            f"    {CLAIM_BLOCK_START}\n"
            f"    tests_total: <int>\n"
            f"    test_files: <int>\n"
            f"    ci_steps: <int>\n"
            f"    assertion_points: <int>\n"
            f"    {CLAIM_BLOCK_END}"
        )
    body = text[start + len(CLAIM_BLOCK_START) : end]
    claims: dict[str, int] = {}
    for line in body.splitlines():
        m = _CLAIM_LINE_RE.match(line)
        if m:
            claims[m.group(1)] = int(m.group(2))
    return claims


# ---------------------------------------------------------------------------
# Assertion point derivation — assertion_points = tests_total +
# self-test assertions parsed from CI step names.
# ---------------------------------------------------------------------------


_ASSERT_SUFFIX_RE = re.compile(r"\((\d+)\s+assertions?\)")


def derive_self_test_assertions(workflow_path: Path) -> int:
    """Sum the ``(N assertions)`` suffix on every CI step whose name
    contains ``self-test`` (case-insensitive).

    Used by ``derive_assertion_points`` to add the embedded-selftest
    contribution (currently ``tl_parser`` 75 + ``screen`` 51 = 126)
    to the AST-derived ``tests_total``.

    The convention pins the count to the step name itself, so adding
    a new assertion to the underlying module requires bumping the
    step name as well — that becomes the drift signal in CI."""
    with open(workflow_path, encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    steps = doc["jobs"]["test"]["steps"]
    total = 0
    for step in steps:
        name = step.get("name", "")
        if "self-test" in name.lower():
            m = _ASSERT_SUFFIX_RE.search(name)
            if m:
                total += int(m.group(1))
    return total


def derive_assertion_points(tests_dir: Path, workflow_path: Path) -> int:
    """``tests_total + derive_self_test_assertions``."""
    return derive_tests_total(tests_dir) + derive_self_test_assertions(workflow_path)


# ---------------------------------------------------------------------------
# Full-mode runtime sanity check — execute every CI test step and
# fail if any returns non-zero.  Does NOT contribute to the count
# (counts are static); this is purely a "do the suites still pass?"
# gate, run in CI / pre-push.
# ---------------------------------------------------------------------------


def execute_all_ci_test_steps(workflow_path: Path, repo_root: Path) -> None:
    """Run every CI step whose ``name`` starts with ``Run `` (the
    project convention for test steps) and whose ``run`` is non-empty.

    Raises ``RuntimeError`` on the first failing step with the
    command and stderr tail attached.  No return value — the count
    of tests is derived statically by ``derive_tests_total``."""
    with open(workflow_path, encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    steps = doc["jobs"]["test"]["steps"]

    for step in steps:
        name = step.get("name", "")
        run = step.get("run", "")
        if not run or not name.startswith("Run "):
            continue
        proc = subprocess.run(
            run,
            shell=True,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"step failed (returncode={proc.returncode}):\n"
                f"  name: {name}\n"
                f"  cmd:  {run.strip()[:120]}\n"
                f"  stderr tail: {proc.stderr[-400:]}"
            )


# ---------------------------------------------------------------------------
# Reporter — formats a drift table for stdout.
# ---------------------------------------------------------------------------


def _format_row(key: str, real: int | None, claim: int | None) -> str:
    if real is None:
        real_s = "-"
        ok = "  N/A"
    elif claim is None:
        real_s = str(real)
        ok = "  MISS"
    elif real == claim:
        real_s = str(real)
        ok = "  OK"
    else:
        real_s = str(real)
        ok = "  DRIFT"
    claim_s = "-" if claim is None else str(claim)
    return f"  {key:<22} real={real_s:<8} claim={claim_s:<8} {ok}"


# ---------------------------------------------------------------------------
# CLI entry
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="verify_docs_claims",
        description="Cross-doc claim drift checker (round 49).",
    )
    mode = p.add_mutually_exclusive_group()
    mode.add_argument(
        "--fast",
        action="store_true",
        help="Fast checks only (file-size + test-files + ci-steps). Default.",
    )
    mode.add_argument(
        "--full",
        action="store_true",
        help="Fast checks + execute every CI 'Run *' step as a passing-suite sanity gate.",
    )
    p.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Override repo root (defaults to the parent of this script).",
    )
    p.add_argument(
        "--max-lines",
        type=int,
        default=DEFAULT_MAX_LINES,
        help=f"Soft limit per .py (default {DEFAULT_MAX_LINES}).",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    full = args.full
    # ``--fast`` is the default when neither flag is given.
    repo_root = (args.repo_root or REPO_ROOT_DEFAULT).resolve()
    handoff_path = repo_root / "HANDOFF.md"
    workflow_path = repo_root / ".github" / "workflows" / "test.yml"
    tests_dir = repo_root / "tests"

    print("=" * 60)
    print(f"verify_docs_claims  ({'full' if full else 'fast'} mode)")
    print(f"  repo_root: {repo_root}")
    print("=" * 60)

    issues: list[str] = []

    # 1. claim block
    try:
        claims = parse_claims(handoff_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"\n[setup error] {e}", file=sys.stderr)
        return 1

    # 2. file-size
    oversized = find_oversized_py_files(repo_root, max_lines=args.max_lines)
    if oversized:
        issues.append(f"{len(oversized)} .py file(s) over {args.max_lines} lines:")
        for p, n in oversized:
            try:
                rel = p.relative_to(repo_root)
            except ValueError:
                rel = p
            issues.append(f"    {rel}  {n} lines")

    # 3-6. Derive all four canonical numbers statically.  Workflow yaml
    # is required for ci_steps + assertion_points; surface yaml parse
    # errors as setup failure rather than soft drift.
    real: dict[str, int] = {}
    try:
        real["test_files"] = count_test_files(tests_dir)
        real["ci_steps"] = count_ci_steps(workflow_path)
        real["tests_total"] = derive_tests_total(tests_dir)
        real["assertion_points"] = derive_assertion_points(tests_dir, workflow_path)
    except (FileNotFoundError, KeyError) as e:
        print(f"\n[setup error] workflow parse failed: {e}", file=sys.stderr)
        return 1

    # 7. (--full only) execute every CI test step as a runtime sanity
    # gate.  Does NOT contribute to the count — counts are static.
    if full:
        try:
            execute_all_ci_test_steps(workflow_path, repo_root)
        except RuntimeError as e:
            print(f"\n[full mode] suite execution failed: {e}", file=sys.stderr)
            return 1

    # Drift comparison — print one row per claim key, then build the
    # issue list from any disagreement.
    print()
    for key in ALL_CLAIM_KEYS:
        print(_format_row(key, real.get(key), claims.get(key)))

    for key in ALL_CLAIM_KEYS:
        claim = claims.get(key)
        if claim is None:
            issues.append(f"claim missing: {key}")
        elif claim != real.get(key):
            issues.append(f"{key} drift: claim={claim} real={real.get(key)}")

    print()
    print("=" * 60)
    if issues:
        print("ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
        print()
        print(
            "Fix HANDOFF.md VERIFIED-CLAIMS block to match reality, OR "
            "fix the underlying drift (e.g. split oversized files), then "
            "re-run.  Bypass at your own risk with `git commit --no-verify`."
        )
        return 1

    print("All claims match reality.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
