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

# Fast-path checks the keys that can be derived without running tests.
FAST_KEYS = ("test_files", "ci_steps")
# Full-path also checks these (require running suites).
FULL_KEYS = ("tests_total", "assertion_points")


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


def count_test_files(tests_dir: Path) -> int:
    """Count ``test_*.py`` plus ``smoke_test.py`` directly under
    ``tests_dir`` (non-recursive — fixtures / artifacts subdirs do
    not contribute to the suite count)."""
    if not tests_dir.is_dir():
        return 0
    n = 0
    for entry in tests_dir.iterdir():
        if not entry.is_file() or entry.suffix != ".py":
            continue
        name = entry.name
        if name.startswith("test_") or name == "smoke_test.py":
            n += 1
    return n


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
# Full-path runtime aggregation — runs each "Run *" step in the
# workflow, parses ``ALL N`` from stdout, sums.
# ---------------------------------------------------------------------------


_ALL_N_RE = re.compile(r"\bALL\s+(\d+)\b", re.IGNORECASE)
_ASSERT_SUFFIX_RE = re.compile(r"\((\d+)\s+assertions?\)")


def _run_step(step_run: str, repo_root: Path) -> int:
    """Run a step's ``run:`` command, parse ``ALL N`` from stdout,
    return N.  Returns 0 if no ``ALL N`` line found (which is the
    normal case for non-test steps like py_compile).
    """
    proc = subprocess.run(
        step_run,
        shell=True,
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        # Test failure surfaces as a hard stop — drift is meaningless
        # if the suites do not pass.
        raise RuntimeError(
            f"step failed (returncode={proc.returncode}):\n"
            f"  cmd: {step_run.strip()[:120]}\n"
            f"  stderr tail: {proc.stderr[-400:]}"
        )
    matches = _ALL_N_RE.findall(proc.stdout)
    if not matches:
        return 0
    # Take the *last* ALL N — some test files print intermediate
    # progress (e.g., ``ALL 5 FOO PASSED`` then ``ALL 10 BAR PASSED``)
    # but the final summary always wins.  Most files emit exactly one.
    return int(matches[-1])


def run_full_test_sum(workflow_path: Path, repo_root: Path) -> tuple[int, int]:
    """Run every ``- run: python tests/...`` and ``- run: python -c
    "from translators..."`` step in the workflow, sum ``ALL N``.

    Returns ``(tests_total, assertion_points)`` where
    ``assertion_points = tests_total + sum(self-test assertion counts
    parsed from step names like "(75 assertions)")``.
    """
    with open(workflow_path, encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    steps = doc["jobs"]["test"]["steps"]

    tests_total = 0
    self_test_assertions = 0
    for step in steps:
        run = step.get("run", "")
        name = step.get("name", "")
        if not run:
            continue
        # tl_parser / screen self-tests are the two ``python -c
        # "from ... import _run_self_tests; _run_self_tests()"``
        # steps.  They print self-test output but do not always
        # emit ``ALL N`` (the modules' selftest functions print
        # their own format).  We trust the step name's
        # "(75 assertions)" suffix as the canonical count.
        suffix_match = _ASSERT_SUFFIX_RE.search(name)
        if suffix_match and "self-test" in name.lower():
            self_test_assertions += int(suffix_match.group(1))
            # Still execute it to verify it actually passes.
            _run_step(run, repo_root)
            continue
        # Regular ``Run *`` test step — sum its ``ALL N``.
        if name.startswith("Run "):
            tests_total += _run_step(run, repo_root)

    assertion_points = tests_total + self_test_assertions
    return tests_total, assertion_points


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
        help="Fast checks + run all CI test steps to sum tests_total & assertion_points.",
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

    # 3. test files
    real_test_files = count_test_files(tests_dir)
    # 4. ci steps
    try:
        real_ci_steps = count_ci_steps(workflow_path)
    except (FileNotFoundError, KeyError) as e:
        print(f"\n[setup error] workflow parse failed: {e}", file=sys.stderr)
        return 1

    real_full: dict[str, int] = {}
    if full:
        try:
            tt, ap = run_full_test_sum(workflow_path, repo_root)
        except RuntimeError as e:
            print(f"\n[full mode] suite execution failed: {e}", file=sys.stderr)
            return 1
        real_full["tests_total"] = tt
        real_full["assertion_points"] = ap

    # Drift comparison
    print()
    print(_format_row("test_files", real_test_files, claims.get("test_files")))
    print(_format_row("ci_steps", real_ci_steps, claims.get("ci_steps")))
    if full:
        print(_format_row("tests_total", real_full.get("tests_total"), claims.get("tests_total")))
        print(_format_row("assertion_points", real_full.get("assertion_points"), claims.get("assertion_points")))
    else:
        print(_format_row("tests_total", None, claims.get("tests_total")) + "  [skipped — use --full]")
        print(_format_row("assertion_points", None, claims.get("assertion_points")) + "  [skipped — use --full]")

    # Build issue list from drift.
    fast_real = {"test_files": real_test_files, "ci_steps": real_ci_steps}
    for key, real in fast_real.items():
        claim = claims.get(key)
        if claim is None:
            issues.append(f"claim missing: {key}")
        elif claim != real:
            issues.append(f"{key} drift: claim={claim} real={real}")

    if full:
        for key in FULL_KEYS:
            real = real_full.get(key)
            claim = claims.get(key)
            if claim is None:
                issues.append(f"claim missing: {key}")
            elif real != claim:
                issues.append(f"{key} drift: claim={claim} real={real}")

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
