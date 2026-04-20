#!/usr/bin/env bash
# Round 45 Commit 5: install the project's git hooks.
#
# Sets git config core.hooksPath to .git-hooks/ so the tracked hook
# scripts under .git-hooks/ take effect locally.  No symlinks needed —
# git will read directly from the tracked directory.
#
# Usage:
#     scripts/install_hooks.sh

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

if [ ! -d .git-hooks ]; then
    echo "[install-hooks] ERROR: .git-hooks/ directory not found at $REPO_ROOT" >&2
    exit 1
fi

git config core.hooksPath .git-hooks

echo "[install-hooks] core.hooksPath set to .git-hooks/"
echo "[install-hooks] active hooks:"
for hook in .git-hooks/*; do
    if [ -f "$hook" ] && [ ! "${hook##*.}" = "md" ]; then
        chmod +x "$hook" 2>/dev/null || true
        echo "  - $(basename "$hook")"
    fi
done
echo "[install-hooks] done.  Bypass a single commit with: git commit --no-verify"
