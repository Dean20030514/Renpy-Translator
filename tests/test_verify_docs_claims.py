#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round 49 prevention: unit tests for ``scripts/verify_docs_claims.py``
— the multi-dimensional drift checker that breaks the r45-r48
"docs claim vs reality" cycle.

The drift incidents in r45-r48 (CI step count / test file count /
test total / line counts in HANDOFF / CHANGELOG / CLAUDE) shared
one root cause: each round's docs sync used the *previous round's
claim* as a baseline and incremented blindly, instead of running
independent ``find/wc/grep`` to ground-truth.

``scripts/verify_docs_claims.py`` provides a single entry-point
that re-derives the four canonical numbers from source-of-truth
files and compares them against the fenced ``VERIFIED-CLAIMS``
block in ``HANDOFF.md``.  This test file pins the contract for
each helper plus the ``main(...)`` exit-code matrix.

Stdlib-only.  No pytest, no third-party deps.  Mirrors the
``def test_X / run_all -> int / ALL N PASSED`` idiom used by
the other 31 test_*.py files in this project.
"""

from __future__ import annotations

import io
import os
import sys
import tempfile
import textwrap
from pathlib import Path

# Repo-root sys.path injection so ``scripts.verify_docs_claims`` is
# importable in the same way ``tests/test_*.py`` import ``core/`` etc.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


# ---------------------------------------------------------------------------
# find_oversized_py_files
# ---------------------------------------------------------------------------


def test_find_oversized_py_files_returns_empty_when_all_under_limit():
    """When every .py is < max_lines, the helper returns ``[]``."""
    from scripts.verify_docs_claims import find_oversized_py_files

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "a.py").write_text("x = 1\n" * 50, encoding="utf-8")
        (root / "b.py").write_text("y = 2\n" * 100, encoding="utf-8")
        result = find_oversized_py_files(root, max_lines=800)
    assert result == [], f"expected [], got {result}"
    print("[OK] find_oversized_py_files_returns_empty_when_all_under_limit")


def test_find_oversized_py_files_detects_file_over_limit():
    """File exceeding the limit appears in the result with its line count."""
    from scripts.verify_docs_claims import find_oversized_py_files

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        small = root / "small.py"
        big = root / "big.py"
        small.write_text("a\n" * 100, encoding="utf-8")
        big.write_text("b\n" * 850, encoding="utf-8")
        result = find_oversized_py_files(root, max_lines=800)
    assert len(result) == 1, f"expected 1 oversized, got {len(result)}: {result}"
    found_path, found_lines = result[0]
    assert found_path.name == "big.py", f"expected big.py, got {found_path}"
    assert found_lines == 850, f"expected 850 lines, got {found_lines}"
    print("[OK] find_oversized_py_files_detects_file_over_limit")


def test_find_oversized_py_files_ignores_default_path_parts():
    """``.git`` / ``_archive`` / ``__pycache__`` / ``output`` are skipped
    by default — these directories are not part of the active source
    tree and may legitimately contain large files."""
    from scripts.verify_docs_claims import find_oversized_py_files

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        # Active source — should be reported.
        (root / "src.py").write_text("x\n" * 1000, encoding="utf-8")
        # Each of these should be ignored.
        for sub in ("_archive", "__pycache__", "output"):
            d = root / sub
            d.mkdir()
            (d / "huge.py").write_text("y\n" * 1500, encoding="utf-8")
        # .git uses a deeper layout; emulate by nesting.
        gitdir = root / ".git" / "hooks"
        gitdir.mkdir(parents=True)
        (gitdir / "buried.py").write_text("z\n" * 2000, encoding="utf-8")

        result = find_oversized_py_files(root, max_lines=800)
    assert len(result) == 1, f"expected 1 oversized (only src.py), got {result}"
    assert result[0][0].name == "src.py"
    print("[OK] find_oversized_py_files_ignores_default_path_parts")


def test_find_oversized_py_files_at_exact_boundary():
    """Files at exactly ``max_lines`` are NOT reported — the contract
    is ``> max_lines`` not ``>=`` (matches the user-supplied awk
    pattern ``$1>800``).  Pins the inclusive-vs-exclusive choice."""
    from scripts.verify_docs_claims import find_oversized_py_files

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        # Exactly 800 lines (no trailing newline → 800 lines of text +
        # 0 final blank).  ``wc -l`` counts newlines, so 800 ``\n``
        # produces 800.  We write 800 ``\n`` here to match.
        (root / "exact.py").write_text("a\n" * 800, encoding="utf-8")
        (root / "over.py").write_text("a\n" * 801, encoding="utf-8")
        result = find_oversized_py_files(root, max_lines=800)
    names = sorted(p.name for p, _ in result)
    assert names == ["over.py"], f"expected [over.py] only, got {names}"
    print("[OK] find_oversized_py_files_at_exact_boundary")


# ---------------------------------------------------------------------------
# count_test_files
# ---------------------------------------------------------------------------


def test_count_test_files_counts_test_prefix_and_smoke():
    """``count_test_files`` returns count of ``test_*.py`` plus
    ``smoke_test.py`` (legacy filename in this project that does not
    match ``test_*`` prefix but is part of the CI suite)."""
    from scripts.verify_docs_claims import count_test_files

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "test_foo.py").write_text("", encoding="utf-8")
        (root / "test_bar.py").write_text("", encoding="utf-8")
        (root / "smoke_test.py").write_text("", encoding="utf-8")
        # Should NOT be counted:
        (root / "helper.py").write_text("", encoding="utf-8")
        (root / "fixtures").mkdir()
        (root / "fixtures" / "test_data.py").write_text("", encoding="utf-8")
        n = count_test_files(root)
    assert n == 3, f"expected 3 (2 test_*.py + smoke_test.py), got {n}"
    print("[OK] count_test_files_counts_test_prefix_and_smoke")


def test_count_test_files_zero_when_dir_empty():
    """Empty tests dir returns 0 (not an error)."""
    from scripts.verify_docs_claims import count_test_files

    with tempfile.TemporaryDirectory() as td:
        n = count_test_files(Path(td))
    assert n == 0, f"expected 0, got {n}"
    print("[OK] count_test_files_zero_when_dir_empty")


# ---------------------------------------------------------------------------
# count_ci_steps
# ---------------------------------------------------------------------------


def test_count_ci_steps_parses_named_and_anonymous_steps():
    """``count_ci_steps`` returns ``len(jobs.test.steps)`` — every
    list entry counts, including anonymous ``- uses:`` checkout.
    Matches the user-visible "33 CI steps" count for this project."""
    from scripts.verify_docs_claims import count_ci_steps

    with tempfile.TemporaryDirectory() as td:
        wf = Path(td) / "test.yml"
        wf.write_text(
            textwrap.dedent(
                """\
                name: Tests
                on: [push]
                jobs:
                  test:
                    runs-on: ubuntu-latest
                    steps:
                      - uses: actions/checkout@v4
                      - name: Step A
                        run: echo a
                      - name: Step B
                        run: echo b
                """
            ),
            encoding="utf-8",
        )
        n = count_ci_steps(wf)
    assert n == 3, f"expected 3 (1 uses + 2 named), got {n}"
    print("[OK] count_ci_steps_parses_named_and_anonymous_steps")


def test_count_ci_steps_raises_on_missing_test_job():
    """If the ``test`` job is missing the helper raises ``KeyError`` —
    callers handle this as a structural error (not a soft drift)."""
    from scripts.verify_docs_claims import count_ci_steps

    with tempfile.TemporaryDirectory() as td:
        wf = Path(td) / "test.yml"
        wf.write_text("name: Tests\non: [push]\njobs:\n  build:\n    runs-on: x\n", encoding="utf-8")
        try:
            count_ci_steps(wf)
        except KeyError:
            print("[OK] count_ci_steps_raises_on_missing_test_job")
            return
    raise AssertionError("expected KeyError when test job is missing")


# ---------------------------------------------------------------------------
# parse_claims  —  fenced VERIFIED-CLAIMS block
# ---------------------------------------------------------------------------


def test_parse_claims_reads_fenced_block():
    """The fenced ``<!-- VERIFIED-CLAIMS-START -->...END -->`` block
    is the canonical declaration of declared numbers.  All other docs
    (CHANGELOG / CLAUDE / .cursorrules) reference it but do not
    declare independently — this is the r48 audit-2/3/4 fix.

    Block format: ``key: value`` per line, ints only, ``#`` comments
    after value tolerated."""
    from scripts.verify_docs_claims import parse_claims

    with tempfile.TemporaryDirectory() as td:
        h = Path(td) / "HANDOFF.md"
        h.write_text(
            textwrap.dedent(
                """\
                # HANDOFF

                some preamble.

                <!-- VERIFIED-CLAIMS-START -->
                tests_total: 439
                test_files: 32
                ci_steps: 33
                assertion_points: 565   # tl_parser 75 + screen 51 + tests 439
                <!-- VERIFIED-CLAIMS-END -->

                more text below.
                """
            ),
            encoding="utf-8",
        )
        claims = parse_claims(h)
    assert claims == {
        "tests_total": 439,
        "test_files": 32,
        "ci_steps": 33,
        "assertion_points": 565,
    }, f"unexpected claims: {claims}"
    print("[OK] parse_claims_reads_fenced_block")


def test_parse_claims_raises_when_block_missing():
    """Missing fenced block raises ``ValueError`` — without claims
    the verifier cannot do its job, callers must surface this as a
    setup error (not a drift)."""
    from scripts.verify_docs_claims import parse_claims

    with tempfile.TemporaryDirectory() as td:
        h = Path(td) / "HANDOFF.md"
        h.write_text("# HANDOFF\nno fenced block here.\n", encoding="utf-8")
        try:
            parse_claims(h)
        except ValueError as e:
            assert "VERIFIED-CLAIMS" in str(e), f"error must mention block name, got: {e}"
            print("[OK] parse_claims_raises_when_block_missing")
            return
    raise AssertionError("expected ValueError when fenced block is missing")


def test_parse_claims_ignores_inline_comments():
    """``key: 33   # comment`` parses to ``33`` — the right-hand-side
    is split on the first ``#`` and the int side is taken."""
    from scripts.verify_docs_claims import parse_claims

    with tempfile.TemporaryDirectory() as td:
        h = Path(td) / "HANDOFF.md"
        h.write_text(
            textwrap.dedent(
                """\
                <!-- VERIFIED-CLAIMS-START -->
                ci_steps: 33  # 1 checkout + 32 named
                <!-- VERIFIED-CLAIMS-END -->
                """
            ),
            encoding="utf-8",
        )
        claims = parse_claims(h)
    assert claims == {"ci_steps": 33}, f"expected {{ci_steps:33}}, got {claims}"
    print("[OK] parse_claims_ignores_inline_comments")


# ---------------------------------------------------------------------------
# main()  —  fast path exit-code matrix
# ---------------------------------------------------------------------------


def _make_fixture_repo(td: Path, *,
                      ci_steps: int,
                      test_files: int,
                      claim_ci: int,
                      claim_test_files: int,
                      claim_tests_total: int = 100,
                      claim_assertion_points: int = 100,
                      oversized_count: int = 0) -> None:
    """Build a synthetic repo tree under ``td`` so ``main()`` can run
    against it via ``--repo-root``.  The four levers correspond to
    the four drift dimensions verify_docs_claims checks."""
    (td / ".github" / "workflows").mkdir(parents=True)
    (td / "tests").mkdir()
    (td / "scripts").mkdir()

    # tests/ — n placeholder test files
    for i in range(test_files):
        (td / "tests" / f"test_synthetic_{i}.py").write_text("", encoding="utf-8")

    # .github/workflows/test.yml — n synthetic steps.  Build the yaml
    # by hand (no textwrap.dedent) because yaml is column-sensitive and
    # dedent's common-prefix logic mangles interpolated indented blocks.
    yaml_lines = [
        "name: Tests",
        "on: [push]",
        "jobs:",
        "  test:",
        "    runs-on: ubuntu-latest",
        "    steps:",
    ]
    for i in range(ci_steps):
        yaml_lines.append(f"      - name: Step {i}")
        yaml_lines.append(f"        run: echo {i}")
    (td / ".github" / "workflows" / "test.yml").write_text(
        "\n".join(yaml_lines) + "\n",
        encoding="utf-8",
    )

    # HANDOFF.md — fenced block with the *claimed* numbers (which may
    # disagree with reality on purpose, depending on the test).
    (td / "HANDOFF.md").write_text(
        textwrap.dedent(
            f"""\
            # HANDOFF

            <!-- VERIFIED-CLAIMS-START -->
            tests_total: {claim_tests_total}
            test_files: {claim_test_files}
            ci_steps: {claim_ci}
            assertion_points: {claim_assertion_points}
            <!-- VERIFIED-CLAIMS-END -->
            """
        ),
        encoding="utf-8",
    )

    # Synthetic oversized .py files at root (not under tests/ to keep
    # test_files count clean — find_oversized_py_files walks the
    # entire root, count_test_files only walks tests/).
    for i in range(oversized_count):
        (td / f"big_{i}.py").write_text("x\n" * 1000, encoding="utf-8")


def test_main_fast_path_returns_zero_when_everything_matches():
    """When file-size / test-file count / CI step count all match
    the fenced claims, ``main(['--fast', '--repo-root', td])`` exits
    0 and prints a success summary."""
    from scripts.verify_docs_claims import main

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        _make_fixture_repo(td,
                           ci_steps=5, test_files=3,
                           claim_ci=5, claim_test_files=3)
        rc = main(["--fast", "--repo-root", str(td)])
    assert rc == 0, f"expected exit 0, got {rc}"
    print("[OK] main_fast_path_returns_zero_when_everything_matches")


def test_main_fast_path_fails_on_oversized_py_file():
    """Any ``.py`` over the 800-line limit makes ``--fast`` exit 1
    even if all other dimensions agree."""
    from scripts.verify_docs_claims import main

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        _make_fixture_repo(td,
                           ci_steps=5, test_files=3,
                           claim_ci=5, claim_test_files=3,
                           oversized_count=1)
        rc = main(["--fast", "--repo-root", str(td)])
    assert rc == 1, f"expected exit 1 on oversized .py, got {rc}"
    print("[OK] main_fast_path_fails_on_oversized_py_file")


def test_main_fast_path_fails_on_test_file_count_drift():
    """Real test_files (3) > claim (2) → drift → exit 1."""
    from scripts.verify_docs_claims import main

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        _make_fixture_repo(td,
                           ci_steps=5, test_files=3,
                           claim_ci=5, claim_test_files=2)
        rc = main(["--fast", "--repo-root", str(td)])
    assert rc == 1, f"expected exit 1 on test-files drift, got {rc}"
    print("[OK] main_fast_path_fails_on_test_file_count_drift")


def test_main_fast_path_fails_on_ci_steps_drift():
    """Real ci_steps (5) > claim (4) → drift → exit 1."""
    from scripts.verify_docs_claims import main

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        _make_fixture_repo(td,
                           ci_steps=5, test_files=3,
                           claim_ci=4, claim_test_files=3)
        rc = main(["--fast", "--repo-root", str(td)])
    assert rc == 1, f"expected exit 1 on ci-steps drift, got {rc}"
    print("[OK] main_fast_path_fails_on_ci_steps_drift")


def test_main_fast_path_fails_on_missing_handoff():
    """If HANDOFF.md is missing the claim block, exit 1 (setup
    error surfaces as failure — silent pass would defeat the
    drift detector)."""
    from scripts.verify_docs_claims import main

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        _make_fixture_repo(td,
                           ci_steps=5, test_files=3,
                           claim_ci=5, claim_test_files=3)
        # Overwrite HANDOFF without claim block.
        (td / "HANDOFF.md").write_text("# HANDOFF\nno block.\n", encoding="utf-8")
        rc = main(["--fast", "--repo-root", str(td)])
    assert rc == 1, f"expected exit 1 on missing claim block, got {rc}"
    print("[OK] main_fast_path_fails_on_missing_handoff")


def test_main_fast_path_skips_test_total_and_assertion_points():
    """``--fast`` mode does NOT verify ``tests_total`` /
    ``assertion_points`` (those require running the suites,
    deferred to ``--full``).  So a mismatch on those two keys
    must NOT fail fast mode."""
    from scripts.verify_docs_claims import main

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        _make_fixture_repo(td,
                           ci_steps=5, test_files=3,
                           claim_ci=5, claim_test_files=3,
                           claim_tests_total=99999,        # absurdly wrong
                           claim_assertion_points=99999)    # absurdly wrong
        rc = main(["--fast", "--repo-root", str(td)])
    assert rc == 0, (
        f"--fast must NOT cross-check tests_total / assertion_points "
        f"(those need runtime), but got exit {rc}"
    )
    print("[OK] main_fast_path_skips_test_total_and_assertion_points")


# ---------------------------------------------------------------------------
# Real-repo smoke — pin the contract that ``--fast`` against the
# actual project tree currently exits 0.  This catches the case
# where someone lands a commit *without* updating HANDOFF claims.
# ---------------------------------------------------------------------------


def test_main_fast_path_zero_against_real_repo():
    """Cross-check: running ``--fast`` against the real repo (no
    --repo-root override) must exit 0 at HEAD.  This is the
    smoke that ``pre-commit`` will run on every commit."""
    from scripts.verify_docs_claims import main

    rc = main(["--fast"])
    assert rc == 0, (
        f"real-repo --fast must exit 0 at HEAD; got {rc}.  "
        "If this fails, HANDOFF.md VERIFIED-CLAIMS block disagrees "
        "with reality — fix the claims before committing."
    )
    print("[OK] main_fast_path_zero_against_real_repo")


# ---------------------------------------------------------------------------
# Test registry + entry point
# ---------------------------------------------------------------------------


TESTS = [
    test_find_oversized_py_files_returns_empty_when_all_under_limit,
    test_find_oversized_py_files_detects_file_over_limit,
    test_find_oversized_py_files_ignores_default_path_parts,
    test_find_oversized_py_files_at_exact_boundary,
    test_count_test_files_counts_test_prefix_and_smoke,
    test_count_test_files_zero_when_dir_empty,
    test_count_ci_steps_parses_named_and_anonymous_steps,
    test_count_ci_steps_raises_on_missing_test_job,
    test_parse_claims_reads_fenced_block,
    test_parse_claims_raises_when_block_missing,
    test_parse_claims_ignores_inline_comments,
    test_main_fast_path_returns_zero_when_everything_matches,
    test_main_fast_path_fails_on_oversized_py_file,
    test_main_fast_path_fails_on_test_file_count_drift,
    test_main_fast_path_fails_on_ci_steps_drift,
    test_main_fast_path_fails_on_missing_handoff,
    test_main_fast_path_skips_test_total_and_assertion_points,
    test_main_fast_path_zero_against_real_repo,
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
    print(f"ALL {n} VERIFY DOCS CLAIMS TESTS PASSED")
    print("=" * 40)
