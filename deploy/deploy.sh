#!/usr/bin/env bash
#
# deploy.sh — pull-based updater for the inky Pi.
#
# Polls origin/$BRANCH; when it moves, hard-resets the working tree to it,
# syncs deps only if the lockfile changed, and restarts the display service.
# Run on a timer (see inky-deploy.timer). Logs go to journald.
#
set -euo pipefail

# pipenv lives in /usr/local/bin on the Pi; ensure it resolves under systemd.
PATH=/usr/local/bin:/usr/bin:/bin:$PATH

# --- config -----------------------------------------------------------------
BRANCH="main"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE="inky.service"
LOCKFILE="/tmp/inky-deploy.lock"
# ----------------------------------------------------------------------------

# Serialize runs: if a deploy is already in flight, exit immediately.
exec 9>"$LOCKFILE"
if ! flock -n 9; then
    echo "deploy: another run holds the lock, skipping"
    exit 0
fi

cd "$REPO_DIR"

git fetch --quiet origin "$BRANCH"

local_sha="$(git rev-parse HEAD)"
remote_sha="$(git rev-parse "origin/$BRANCH")"

if [ "$local_sha" = "$remote_sha" ]; then
    # Up to date — nothing to do. Stay quiet so the journal isn't spammed.
    exit 0
fi

echo "deploy: $BRANCH ${local_sha:0:7} -> ${remote_sha:0:7}, updating"

# Capture the lockfile hash before the reset so we can tell if deps changed.
lock_before="$(git rev-parse "HEAD:Pipfile.lock" 2>/dev/null || echo none)"

# This is a deploy target, not an edit box: take origin verbatim. Untracked
# files (.env, logs) are preserved by reset.
git reset --hard "origin/$BRANCH"

lock_after="$(git rev-parse "HEAD:Pipfile.lock" 2>/dev/null || echo none)"

if [ "$lock_before" != "$lock_after" ]; then
    echo "deploy: Pipfile.lock changed, running pipenv sync"
    pipenv sync
else
    echo "deploy: lockfile unchanged, skipping dep sync"
fi

echo "deploy: restarting $SERVICE"
systemctl --user restart "$SERVICE"

echo "deploy: done at ${remote_sha:0:7}"
