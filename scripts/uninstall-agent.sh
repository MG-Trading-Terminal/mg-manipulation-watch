#!/usr/bin/env bash
# Stop + remove the local scan agent. Leaves the accumulated base (data/history) intact.
set -uo pipefail
LABEL="com.meatgrinder.crimescan"
DEST="$HOME/Library/LaunchAgents/${LABEL}.plist"
launchctl unload "$DEST" 2>/dev/null || true
rm -f "$DEST"
echo "removed ${LABEL}. data/history is untouched."
