#!/usr/bin/env bash
# One scan cycle: refresh JSON + history, rebuild the local site. Never aborts the
# scheduler on a transient failure — it logs and moves on. This is the unit of work
# the launchd agent (and run-loop.sh) call.
set -uo pipefail

# launchd runs with a minimal PATH — make python3 findable.
export PATH="/usr/bin:/usr/local/bin:/opt/homebrew/bin:$PATH"

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR" || exit 1
mkdir -p data/logs
LOG="data/logs/scan.log"
ts() { date -u +%FT%TZ; }

echo "[$(ts)] scan start" >> "$LOG"
if python3 -m detector.pipeline >> "$LOG" 2>&1; then
  echo "[$(ts)] pipeline ok" >> "$LOG"
else
  echo "[$(ts)] pipeline FAILED (rc=$?)" >> "$LOG"
fi
if python3 web/build.py >> "$LOG" 2>&1; then
  echo "[$(ts)] build ok" >> "$LOG"
else
  echo "[$(ts)] build FAILED (rc=$?)" >> "$LOG"
fi
echo "[$(ts)] scan done" >> "$LOG"
