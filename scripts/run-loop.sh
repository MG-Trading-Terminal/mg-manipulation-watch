#!/usr/bin/env bash
# Foreground 4-hourly loop — the no-launchd alternative. Leave it running in a
# terminal (or tmux) to accumulate the base. Ctrl-C to stop.
set -uo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INTERVAL="${1:-14400}"   # seconds; default 4h
echo "crime-scan loop every ${INTERVAL}s — Ctrl-C to stop"
while true; do
  bash "$DIR/scan-once.sh"
  tail -n 1 "$DIR/../data/logs/scan.log" 2>/dev/null
  sleep "$INTERVAL"
done
