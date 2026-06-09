"""
collect — market-wide multi-venue sweep. The primary broad scanner.

One bulk call per venue (Binance/Bybit/Bitget/Gate/MEXC/Hyperliquid) -> thousands
of perp markets -> the same pure scorer -> a single snapshot. Fast (a handful of
calls, not thousands). Each row is tagged with its venue, because a crime-coin
squeeze is usually run on one specific venue.

Signals available market-wide: funding + OI-dominance (2 of 6) -> confidence ~0.40.
That is enough to surface squeeze candidates; deep enrichment (MC/TVL, supply) is
the curated detector.pipeline's job for known protocol tokens.

Output:
  data/candidates/index.json     current snapshot (ALL markets, sorted) — site source
  data/snapshots/<ts>.json       immutable per-scan snapshot — THE accumulating base
  data/history/_scans.jsonl      per-scan summary (append)

Run:  python3 -m detector.collect
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import List

from .crime_score import score, Signals
from .venues import all_tickers, ADAPTERS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "data", "candidates")
SNAP_DIR = os.path.join(ROOT, "data", "snapshots")
HIST = os.path.join(ROOT, "data", "history", "_scans.jsonl")


def _signals(tk: dict) -> Signals:
    return Signals(
        funding_rate=tk.get("funding_rate"),
        funding_interval_hours=tk.get("funding_interval_hours"),
        open_interest_usd=tk.get("open_interest_usd"),
        volume_24h_usd=tk.get("volume_24h_usd"),
    )


def run(venues=None) -> dict:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(SNAP_DIR, exist_ok=True)

    tickers = all_tickers(venues)
    by_venue = {}
    records: List[dict] = []
    for tk in tickers:
        by_venue[tk["venue"]] = by_venue.get(tk["venue"], 0) + 1
        a = score(tk["symbol"], _signals(tk))
        rec = a.to_record()
        rec["symbol"] = tk["symbol"]
        rec["venue"] = tk["venue"]
        rec["market"] = tk["market"]
        rec["last_checked"] = now
        rec["evidence"] = [
            {"label": "Coinglass", "url": f"https://www.coinglass.com/currencies/{tk['symbol']}"},
        ]
        records.append(rec)

    records.sort(key=lambda r: (r["score"], r["confidence"]), reverse=True)
    suspected = sum(1 for r in records if r["status"] == "suspected")

    dataset = {
        "schema": "mgterminal.crime-coins/v0.2-multivenue",
        "disclaimer": "Automated manipulation-risk heuristic. 'suspected' is an "
                      "unverified machine signal, not an accusation. See README.",
        "generated_at": now,
        "venues": by_venue,
        "count": len(records),
        "suspected": suspected,
        "tokens": records,
    }

    with open(os.path.join(OUT_DIR, "index.json"), "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)
        f.write("\n")

    # Immutable base snapshot (filesystem-safe timestamp).
    snap = os.path.join(SNAP_DIR, now.replace(":", "-") + ".json")
    with open(snap, "w", encoding="utf-8") as f:
        json.dump(dataset, f)
        f.write("\n")

    os.makedirs(os.path.dirname(HIST), exist_ok=True)
    with open(HIST, "a", encoding="utf-8") as f:
        f.write(json.dumps({"t": now, "count": len(records),
                            "suspected": suspected, "venues": by_venue}) + "\n")

    return dataset


def main() -> int:
    ds = run()
    print(f"swept {ds['count']} markets across {len(ds['venues'])} venues "
          f"@ {ds['generated_at']}  -> {ds['suspected']} suspected")
    print("per venue:", ", ".join(f"{k}={v}" for k, v in sorted(ds["venues"].items())))
    print()
    print(f"{'SYMBOL':<14}{'VENUE':<12}{'SCORE':>6}{'CONF':>6}  {'STATUS':<10}OAK")
    print("-" * 70)
    for r in ds["tokens"][:30]:
        oak = ",".join(t.replace("OAK-", "") for t in r["oak_techniques"]) or "-"
        print(f"{r['symbol']:<14}{r['venue']:<12}{r['score']:>6}{r['confidence']:>6.2f}  "
              f"{r['status']:<10}{oak}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
