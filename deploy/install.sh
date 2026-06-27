#!/usr/bin/env bash
#
# install.sh — one-time setup for pull-based auto-deploy on the inky Pi.
#
# Run once on the Pi:
#     cd ~/inky && git pull && bash deploy/install.sh
#
# Installs the systemd *user* units (no sudo), enables linger so they run at
# boot without a login, starts the app service and the deploy timer, and prints
# the old crontab line to remove.
#
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNIT_DIR="$HOME/.config/systemd/user"
SRC="$REPO_DIR/deploy"

echo "Installing inky auto-deploy from: $REPO_DIR"

mkdir -p "$UNIT_DIR"

# Template the real repo path into each unit and install it.
for unit in inky.service inky-deploy.service inky-deploy.timer; do
    sed "s|__REPO_DIR__|$REPO_DIR|g" "$SRC/$unit" > "$UNIT_DIR/$unit"
    echo "  installed $UNIT_DIR/$unit"
done

chmod +x "$SRC/deploy.sh" "$REPO_DIR/start.sh"

# Linger lets user services run at boot without an active login session.
echo "Enabling linger for $USER (needs sudo once)..."
sudo loginctl enable-linger "$USER"

systemctl --user daemon-reload

echo "Enabling and starting inky.service ..."
systemctl --user enable --now inky.service

echo "Enabling and starting inky-deploy.timer ..."
systemctl --user enable --now inky-deploy.timer

echo
echo "Done. Status:"
systemctl --user --no-pager status inky.service inky-deploy.timer || true

echo
echo "=============================================================="
echo "ACTION REQUIRED: remove the old cron launcher so it doesn't"
echo "fight the systemd service. Run 'crontab -e' and delete the line:"
echo
crontab -l 2>/dev/null | grep -F "start.sh" || echo "  (no start.sh crontab line found — nothing to remove)"
echo "=============================================================="
echo
echo "Watch deploys with:  journalctl --user -u inky-deploy -f"
