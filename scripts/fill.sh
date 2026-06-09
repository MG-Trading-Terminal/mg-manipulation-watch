#!/usr/bin/env bash
# Init fill — pull as much enrichment as the current IP allows, then stop.
# Designed for VPN rotation: caches persist, so each run only fetches what's still
# missing. Workflow:  switch VPN location → run this → coverage grows → repeat.
#
# Run ONE fill at a time (don't run alongside scan-once/the agent — they share caches).
#
# Tune via env. With a free CoinGecko demo key you can drop the pacing and go big:
#   COINGECKO_API_KEY=CG-xxxx PROFILE_PACE=0.4 PROFILE_BUDGET=600 bash scripts/fill.sh
set -uo pipefail
export PATH="/usr/bin:/usr/local/bin:/opt/homebrew/bin:$PATH"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$DIR" || exit 1
[ -f "$DIR/.env" ] && { set -a; . "$DIR/.env"; set +a; }   # load key + tunables

# With a CoinGecko key (100/min) go fast; without, stay polite. Env overrides.
: "${PROFILE_BUDGET:=600}"; export PROFILE_BUDGET
if [ -z "${PROFILE_PACE:-}" ]; then
  [ -n "${COINGECKO_API_KEY:-}" ] && PROFILE_PACE=0.6 || PROFILE_PACE=2.5
fi
export PROFILE_PACE
echo "fill: budget=$PROFILE_BUDGET pace=${PROFILE_PACE}s  cg-key=$([ -n "${COINGECKO_API_KEY:-}" ] && echo set || echo none)"

python3 -m detector.collect | sed -n '1,3p'

python3 - <<'PY'
import json, os
d = json.load(open("data/candidates/index.json"))
cgf = "data/enrich/cg_detail.json"
real = 0
if os.path.exists(cgf):
    cg = json.load(open(cgf))
    real = sum(1 for v in cg.values() if not (isinstance(v, dict) and v.get("_no_data")))
print(f"profiled: {d.get('profiled')}  | cg profiles cached: {real}  | contracts(GoPlus): {d.get('contract_checked')}")
print("→ switch VPN location and re-run to fetch more — caches keep what's already done.")
PY
