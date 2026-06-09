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
from . import enrich

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "data", "candidates")
SNAP_DIR = os.path.join(ROOT, "data", "snapshots")
HIST = os.path.join(ROOT, "data", "history", "_scans.jsonl")


def _signals(tk: dict, maps: dict):
    """Returns (Signals, context). Fuzzy MC/TVL & P/S are NOT auto-scored — by
    symbol they false-positive on legit L1s/exchange tokens (DOT, CRO, FLOW). They
    are computed as displayed CONTEXT for a human reviewer. The auto score runs on
    the manipulation-mechanics signals only: funding (squeeze) + OI/MC (perp
    dominance of real float). MC/TVL is auto-scored only in the curated pipeline
    where the DefiLlama slug is hand-verified."""
    mc, tvl, fees, cg_vol = enrich.lookup(tk["symbol"], maps)
    sig = Signals(
        market_cap_usd=mc,
        tvl_usd=None,
        fees_annualized_usd=None,
        funding_rate=tk.get("funding_rate"),
        funding_interval_hours=tk.get("funding_interval_hours"),
        open_interest_usd=tk.get("open_interest_usd"),
        volume_24h_usd=tk.get("volume_24h_usd") or cg_vol,
    )
    ctx = {"market_cap_usd": mc, "tvl_usd": tvl, "fees_annualized_usd": fees}
    if mc and tvl:
        ctx["mc_tvl"] = round(mc / tvl, 1)
    if mc and fees:
        ctx["ps"] = round(mc / fees, 0)
    return sig, ctx


# Sign thresholds for the human-readable flag list (separate from the auto score).
def _flags(rec: dict, ctx: dict) -> list:
    flags = []
    sig = rec.get("signals", {})
    if (sig.get("funding") or 0) >= 0.5:
        flags.append("squeeze")                 # deeply negative funding (mechanics)
    if (sig.get("oi_dominance") or 0) >= 0.5:
        flags.append("oi-dominance")            # perp OI large vs float (mechanics)
    mctvl = ctx.get("mc_tvl")
    if mctvl and mctvl >= 100:
        flags.append("mc/tvl-disconnect")       # fundamental disconnect (context)
    ps = ctx.get("ps")
    if ps and ps >= 1000:
        flags.append("ps-disconnect")           # price/sales blow-out (context)
    return flags


def run(venues=None) -> dict:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(SNAP_DIR, exist_ok=True)

    maps = enrich.load()  # bulk MC/TVL/fees maps (cached) -> full signal set
    tickers = all_tickers(venues)
    by_venue = {}
    enriched = 0
    records: List[dict] = []
    for tk in tickers:
        by_venue[tk["venue"]] = by_venue.get(tk["venue"], 0) + 1
        sig, ctx = _signals(tk, maps)
        if sig.market_cap_usd is not None:
            enriched += 1
        a = score(tk["symbol"], sig)
        rec = a.to_record()
        rec["symbol"] = tk["symbol"]
        rec["venue"] = tk["venue"]
        rec["market"] = tk["market"]
        rec["context"] = ctx
        rec["last_checked"] = now
        rec["evidence"] = [
            {"label": "Coinglass", "url": f"https://www.coinglass.com/currencies/{tk['symbol']}"},
        ]
        rec["flags"] = _flags(rec, ctx)
        records.append(rec)

    # Rank by number of distinct signs first, then score — multi-sign tokens
    # ("имеет признаки") rise to the top of the list.
    records.sort(key=lambda r: (len(r["flags"]), r["score"], r["confidence"]), reverse=True)
    suspected = sum(1 for r in records if r["status"] == "suspected")
    flag_counts = {}
    for r in records:
        for fl in r["flags"]:
            flag_counts[fl] = flag_counts.get(fl, 0) + 1
    multi_sign = sum(1 for r in records if len(r["flags"]) >= 2)

    dataset = {
        "schema": "mgterminal.crime-coins/v0.3-flags",
        "disclaimer": "Automated manipulation-risk heuristic. 'suspected' is an "
                      "unverified machine signal, not an accusation. See README.",
        "generated_at": now,
        "venues": by_venue,
        "count": len(records),
        "enriched": enriched,
        "suspected": suspected,
        "multi_sign": multi_sign,
        "flag_counts": flag_counts,
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
        f.write(json.dumps({"t": now, "count": len(records), "suspected": suspected,
                            "multi_sign": multi_sign, "flag_counts": flag_counts,
                            "venues": by_venue}) + "\n")

    return dataset


def main() -> int:
    ds = run()
    print(f"swept {ds['count']} markets across {len(ds['venues'])} venues "
          f"@ {ds['generated_at']}  ({ds.get('enriched', 0)} enriched)")
    print(f"  suspected (active squeeze): {ds['suspected']}   "
          f"multi-sign (>=2 flags): {ds['multi_sign']}")
    print("  flags:", ", ".join(f"{k}={v}" for k, v in sorted(ds["flag_counts"].items())) or "none")
    print()
    print(f"{'SYMBOL':<13}{'VENUE':<11}{'SCORE':>5}  {'STATUS':<10}{'FLAGS'}")
    print("-" * 78)
    for r in ds["tokens"][:30]:
        flags = ",".join(r.get("flags", [])) or "-"
        print(f"{r['symbol']:<13}{r['venue']:<11}{r['score']:>5}  "
              f"{r['status']:<10}{flags}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
