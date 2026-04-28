# Git Hooks

This directory contains the project's pre-commit hook.  It runs four
fast sanity checks before letting a commit proceed.  Round 49
extended the original two-check hook (round 45 commit 5) with the
file-size guard and docs-claim drift checker that the r45-r48
audit-tail incidents motivated.

## What it checks

1. **`py_compile` smoke** — every staged `.py` file is byte-compiled
   to catch syntax errors before they land.

2. **File-size guard** *(round 49 prevention (a))* — any `.py` outside
   `.git` / `_archive` / `__pycache__` / `output` exceeding **800
   lines** blocks the commit.  Direct port of the user-supplied awk
   pattern.  Motivated by r48 audit-tail when `tests/test_engines.py`
   (1090) and `tests/test_custom_engine.py` (1020) silently grew over
   the soft limit across r45-r48 while HANDOFF/CHANGELOG repeatedly
   claimed "all tests < 800 maintained".

3. **Meta-runner tests** (`tests/test_all.py`, ~150 tests, ~5s) —
   catches regressions in the core 6 focused suites (api / file_processor
   / translators / glossary-prompts-config / translation-state /
   runtime-hook).

4. **`scripts/verify_docs_claims.py --fast`** *(round 49 prevention
   (b)+(d))* — re-derives `test_files` and `ci_steps` from the source
   tree and compares them against the fenced `VERIFIED-CLAIMS` block in
   `HANDOFF.md`.  Any drift fails the commit.  Motivated by r48
   audit-2/3/4 chain — four consecutive rounds of drift between
   docs claim and reality (440 vs 439 tests / 29 vs 31 files / 32
   vs 33 CI steps / etc.).

The expensive `tests_total` / `assertion_points` re-derivation is
gated behind `--full` and runs in CI only — a full sweep takes
~30-60s and isn't appropriate for every local commit.

The full 23-file independent-suite sweep (`python tests/test_engines.py`
/ `test_ui_whitelist.py` / etc.) is also reserved for CI.  Local
commit wall-time stays around 7-12 seconds.

## Round 49 prevention contract (c)

**Never claim numbers** — test count, file count, CI step count, line
count, assertion count — in `HANDOFF.md` / `CHANGELOG_RECENT.md` /
`CLAUDE.md` / `.cursorrules` without first running
`grep` / `wc` / `find` / `python scripts/verify_docs_claims.py` to
ground-truth.

`HANDOFF.md`'s fenced `<!-- VERIFIED-CLAIMS-START -->...<!-- END -->`
block is the **single declaration site**.  Every other doc may
reference those numbers in prose but MUST NOT re-declare them.  When
end-of-round docs sync runs, only the fenced block changes; the
surrounding prose stays generic ("see VERIFIED-CLAIMS").  This
collapses the n-way docs-sync drift surface to a single comparison
the pre-commit hook enforces.

## Install

Run `scripts/install_hooks.sh`, or equivalently set the git config
directly: `git config core.hooksPath .git-hooks`.

## Bypass

For emergencies (e.g., a hotfix where tests need to land in a separate
commit), pass `--no-verify` to `git commit`.  Document the reason in
the commit body.

## Uninstall

`git config --unset core.hooksPath`.
