#!/usr/bin/env bash
# View the generated site locally at http://localhost:8787
set -uo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${1:-8787}"
if [ ! -f "$DIR/dist/index.html" ]; then
  echo "dist/ not built yet — running build..."
  ( cd "$DIR" && python3 web/build.py )
fi
echo "serving $DIR/dist at http://localhost:${PORT}  (Ctrl-C to stop)"
cd "$DIR/dist" && python3 -m http.server "$PORT"
