# Git Hooks

Round 45 Commit 5 introduces an opt-in pre-commit hook stored in this
directory.  The hook runs two fast sanity checks before every commit:

1. **`py_compile` smoke** on every staged `.py` file — catches syntax
   errors before they land.
2. **Meta-runner tests** (`tests/test_all.py`, ~150 tests, ~5 s) —
   catches regressions in the core 6 focused suites.

The full 23-file test sweep (`python tests/test_engines.py` /
`test_ui_whitelist.py` / etc.) is NOT run here — that is reserved for
CI (`.github/workflows/test.yml`) to keep the local commit wall-time
under 10 seconds.

## Install

Run `scripts/install_hooks.sh`, or equivalently set the git config
directly: `git config core.hooksPath .git-hooks`.

## Bypass

For emergencies (e.g., a hotfix where tests need to land in a separate
commit), pass `--no-verify` to `git commit`.

## Uninstall

`git config --unset core.hooksPath`.
