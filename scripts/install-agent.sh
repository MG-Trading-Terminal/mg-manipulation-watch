#!/usr/bin/env bash
# Install + load the local 4-hourly scan agent (macOS launchd). Reversible via
# uninstall-agent.sh. No repo / no cloud — runs entirely on this machine to build
# the initial base.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LABEL="com.meatgrinder.crimescan"
DEST="$HOME/Library/LaunchAgents/${LABEL}.plist"

mkdir -p "$HOME/Library/LaunchAgents" "$DIR/data/logs"

# Render the template with this project's absolute path.
sed "s|__PROJECT_DIR__|${DIR}|g" "$DIR/scripts/${LABEL}.plist" > "$DEST"
echo "wrote $DEST"

# Reload cleanly if already present.
launchctl unload "$DEST" 2>/dev/null || true
launchctl load -w "$DEST"
echo "loaded ${LABEL} — scans every 4h (and once now)."
echo "logs:   $DIR/data/logs/scan.log"
echo "status: launchctl list | grep ${LABEL}"
echo "stop:   bash scripts/uninstall-agent.sh"
