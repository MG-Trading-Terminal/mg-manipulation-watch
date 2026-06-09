#!/usr/bin/env bash
# View the generated site locally at http://localhost:8787
set -uo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${1:-8787}"
if [ ! -f "$DIR/dist/index.html" ]; then
  echo "dist/ not built yet — running npm run build..."
  ( cd "$DIR" && npm run build )
fi
echo "serving $DIR/dist at http://localhost:${PORT}  (Ctrl-C to stop)"
cd "$DIR/dist" && python3 -m http.server "$PORT"
