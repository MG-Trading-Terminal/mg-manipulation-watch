"""
Pipeline — the 4-hourly batch job.

universe.json -> fetch_signals (live, best-effort) -> score (pure) -> JSON dataset

Output (the JSON IS the source of truth; the site is generated from it):
  data/candidates/index.json   { generated_at, count, tokens: [record, ...] }
  data/candidates/<symbol>.json  one record per token (for granular diffing)

This job NEVER assigns a human verdict. Every record is `watchlist` or
`suspected` only. A human promotes `suspected` -> `confirmed` by hand under
data/confirmed/ (out of this job's scope).

Run:  python3 -m detector.pipeline
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import List

from .crime_score import score
from .sources import fetch_signals

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNIVERSE = os.path.join(ROOT, "data", "universe.json")
OUT_DIR = os.path.join(ROOT, "data", "candidates")


def _evidence_links(entry: dict) -> List[dict]:
    links = []
    sym = entry.get("symbol", "")
    if entry.get("binance_symbol"):
        links.append({"label": "Coinglass funding/OI",
                      "url": f"https://www.coinglass.com/currencies/{sym}"})
    if entry.get("cg_id"):
        links.append({"label": "CoinGecko",
                      "url": f"https://www.coingecko.com/en/coins/{entry['cg_id']}"})
    if entry.get("defillama_slug"):
        links.append({"label": "DefiLlama TVL",
                      "url": f"https://defillama.com/protocol/{entry['defillama_slug']}"})
    return links


def run(universe_path: str = UNIVERSE, out_dir: str = OUT_DIR) -> dict:
    with open(universe_path, "r", encoding="utf-8") as f:
        universe = json.load(f)
    entries = universe.get("tokens", [])

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    os.makedirs(out_dir, exist_ok=True)

    records = []
    for entry in entries:
        sym = entry["symbol"]
        signals = fetch_signals(entry)
        assessment = score(sym, signals)
        rec = assessment.to_record()
        rec["symbol"] = sym
        rec["last_checked"] = now
        rec["evidence"] = _evidence_links(entry)
        records.append(rec)
        # per-token file (stable path -> clean git diffs over time)
        with open(os.path.join(out_dir, f"{sym}.json"), "w", encoding="utf-8") as fp:
            json.dump(rec, fp, indent=2, sort_keys=True)
            fp.write("\n")

    records.sort(key=lambda r: r["score"], reverse=True)
    dataset = {
        "schema": "mgterminal.crime-coins/v0.1",
        "disclaimer": "Automated manipulation-risk heuristic. 'suspected' is an "
                      "unverified machine signal, not an accusation. See README.",
        "generated_at": now,
        "count": len(records),
        "suspected": sum(1 for r in records if r["status"] == "suspected"),
        "tokens": records,
    }
    with open(os.path.join(out_dir, "index.json"), "w", encoding="utf-8") as fp:
        json.dump(dataset, fp, indent=2)
        fp.write("\n")

    return dataset


def main() -> int:
    ds = run()
    print(f"scanned {ds['count']} tokens @ {ds['generated_at']}  "
          f"-> {ds['suspected']} suspected")
    print(f"{'SYM':<8}{'SCORE':>6}{'CONF':>7}  {'STATUS':<11}OAK")
    print("-" * 60)
    for r in ds["tokens"]:
        oak = ",".join(t.replace("OAK-", "") for t in r["oak_techniques"]) or "-"
        print(f"{r['symbol']:<8}{r['score']:>6}{r['confidence']:>7.2f}  "
              f"{r['status']:<11}{oak}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
