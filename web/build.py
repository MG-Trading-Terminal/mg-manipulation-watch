"""
build — assemble the deployable site into dist/.

The Python side produces ONLY JSON (detector.collect -> data/candidates/index.json).
The frontend is plain html + css + js (web/index.html, web/styles.css, web/app.js)
that fetches data.json and renders client-side — same stack philosophy as OAK.

This script just copies the static assets + the dataset into dist/:
  dist/index.html  dist/styles.css  dist/app.js  dist/data.json  dist/CNAME

Run:  python3 web/build.py   (after a scan)
Serve locally:  bash scripts/serve.sh
"""
import json
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
DIST = os.path.join(ROOT, "dist")
DATASET = os.path.join(ROOT, "data", "candidates", "index.json")
ASSETS = ("index.html", "styles.css", "app.js")


def build() -> str:
    os.makedirs(DIST, exist_ok=True)
    for name in ASSETS:
        shutil.copyfile(os.path.join(WEB, name), os.path.join(DIST, name))
    if os.path.exists(DATASET):
        # Publish the per-token view (what the page needs). The full per-market
        # detail stays in data/snapshots/ + data/candidates/index.json for сверка.
        with open(DATASET, "r", encoding="utf-8") as f:
            ds = json.load(f)
        ds.pop("tokens", None)
        with open(os.path.join(DIST, "data.json"), "w", encoding="utf-8") as f:
            json.dump(ds, f)
    with open(os.path.join(DIST, "CNAME"), "w", encoding="utf-8") as f:
        f.write("mgterminal.com\n")
    return DIST


def main() -> int:
    out = build()
    print("assembled site -> " + out)
    print("  " + " ".join(ASSETS) + " + data.json + CNAME")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
