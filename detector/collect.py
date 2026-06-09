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
from . import enrich, goplus, dexscreener

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "data", "candidates")
SNAP_DIR = os.path.join(ROOT, "data", "snapshots")
HIST = os.path.join(ROOT, "data", "history", "_scans.jsonl")
GP_CACHE = os.path.join(ROOT, "data", "enrich", "goplus.json")
DX_CACHE = os.path.join(ROOT, "data", "enrich", "dexscreener.json")


def _load_json(path) -> dict:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_json(path, obj) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f)


def _dexscreener_markets(contracts, max_fetch=600):
    """{symbol: market} for resolved contracts, cached across runs."""
    cache = _load_json(DX_CACHE)
    want = []
    for sym, ca in contracts.items():
        if ca and ca[1] not in cache:
            want.append(ca[1])
    for addr in want[:max_fetch]:
        cache[addr] = dexscreener.token_market(addr)
    if want:
        _save_json(DX_CACHE, cache)
    out = {}
    for sym, ca in contracts.items():
        if ca:
            m = cache.get(ca[1])
            if m and not m.get("_no_data"):
                out[sym] = m
    return out


def _load_goplus_cache() -> dict:
    if os.path.exists(GP_CACHE):
        try:
            with open(GP_CACHE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_goplus_cache(cache: dict) -> None:
    os.makedirs(os.path.dirname(GP_CACHE), exist_ok=True)
    with open(GP_CACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f)


def _resolve_contracts(tickers, maps):
    """base_symbol -> (chain_id, address) for tokens with a GoPlus-supported chain."""
    out = {}
    for tk in tickers:
        sym = tk["symbol"]
        if sym in out:
            continue
        pf = enrich.contract_platforms(sym, maps)
        out[sym] = None
        if not pf:
            continue
        for plat, addr in pf.items():
            cid = goplus.CG_PLATFORM_TO_CHAIN.get(plat)
            if cid and addr:
                out[sym] = (cid, addr.lower())
                break
    return out


def _goplus_security(contracts, max_fetch=500):
    """Resolve {symbol: (chain,addr)} -> {symbol: security}, cached across runs."""
    cache = _load_goplus_cache()
    want = {}                       # chain -> set(addr) we still need
    for sym, ca in contracts.items():
        if not ca:
            continue
        key = f"{ca[0]}:{ca[1]}"
        if key not in cache:
            want.setdefault(ca[0], set()).add(ca[1])
    fetched = 0
    for cid, addrs in want.items():
        addrs = list(addrs)
        if fetched >= max_fetch:
            break
        addrs = addrs[:max_fetch - fetched]
        res = goplus.token_security(cid, addrs)
        for a, v in res.items():
            cache[f"{cid}:{a}"] = v
        fetched += len(addrs)
    if fetched:
        _save_goplus_cache(cache)
    secmap = {}
    for sym, ca in contracts.items():
        if ca:
            sec = cache.get(f"{ca[0]}:{ca[1]}")
            if sec and not sec.get("_no_data"):   # skip negatively-cached (checked, no record)
                secmap[sym] = sec
    return secmap


def _signals(tk: dict, maps: dict):
    """Returns (Signals, context). Fuzzy MC/TVL & P/S are NOT auto-scored — by
    symbol they false-positive on legit L1s/exchange tokens (DOT, CRO, FLOW). They
    are computed as displayed CONTEXT for a human reviewer. The auto score runs on
    the manipulation-mechanics signals only: funding (squeeze) + OI/MC (perp
    dominance of real float). MC/TVL is auto-scored only in the curated pipeline
    where the DefiLlama slug is hand-verified."""
    mc, tvl, fees, cg_vol, fdv = enrich.lookup(tk["symbol"], maps)
    sig = Signals(
        market_cap_usd=mc,
        tvl_usd=None,
        fees_annualized_usd=None,
        funding_rate=tk.get("funding_rate"),
        funding_interval_hours=tk.get("funding_interval_hours"),
        open_interest_usd=tk.get("open_interest_usd"),
        volume_24h_usd=tk.get("volume_24h_usd") or cg_vol,
    )
    ctx = {"market_cap_usd": mc, "tvl_usd": tvl, "fees_annualized_usd": fees, "fdv_usd": fdv}
    if mc and tvl:
        ctx["mc_tvl"] = round(mc / tvl, 1)
    if mc and fees:
        ctx["ps"] = round(mc / fees, 0)
    if mc and fdv and fdv > 0:
        ctx["float"] = round(mc / fdv, 3)  # circulating share of fully-diluted
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
    fl = ctx.get("float")
    if fl is not None and fl < 0.30 and (ctx.get("fdv_usd") or 0) >= 20e6:
        flags.append("low-float")               # <30% circulating, FDV >=$20M (T3)
    return flags


def run(venues=None) -> dict:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(SNAP_DIR, exist_ok=True)

    now_ms = datetime.now(timezone.utc).timestamp() * 1000.0
    maps = enrich.load()  # bulk MC/TVL/fees maps (cached) -> full signal set
    tickers = all_tickers(venues)

    # Contract + market-structure pass: resolve EVM contracts, fetch GoPlus
    # (honeypot/tax/mint/authority/holders) and DexScreener (liquidity/pair-age).
    contracts = _resolve_contracts(tickers, maps)
    secmap = _goplus_security(contracts)
    dxmap = _dexscreener_markets(contracts)
    contract_scam = 0

    by_venue = {}
    enriched = 0
    records: List[dict] = []
    for tk in tickers:
        by_venue[tk["venue"]] = by_venue.get(tk["venue"], 0) + 1
        sym = tk["symbol"]
        sig, ctx = _signals(tk, maps)
        if sig.market_cap_usd is not None:
            enriched += 1
        a = score(sym, sig)
        rec = a.to_record()
        rec["symbol"] = sym
        rec["venue"] = tk["venue"]
        rec["market"] = tk["market"]
        rec["context"] = ctx
        rec["last_checked"] = now
        rec["evidence"] = [
            {"label": "Coinglass", "url": f"https://www.coinglass.com/currencies/{sym}"},
        ]
        rec["flags"] = _flags(rec, ctx)

        # Merge GoPlus contract-security signs (OAK T1/T3).
        sec = secmap.get(sym)
        if sec is not None:
            gp_flags, gp_oak, gp_fields = goplus.flags_from_security(sec)
            for fl in gp_flags:
                if fl not in rec["flags"]:
                    rec["flags"].append(fl)
            for t in gp_oak:
                if t not in rec["oak_techniques"]:
                    rec["oak_techniques"].append(t)
            rec["context"].update({k: v for k, v in gp_fields.items() if v is not None})
            ca = contracts.get(sym)
            if ca:
                rec["context"]["chain"] = ca[0]
                rec["context"]["contract"] = ca[1]
            # Honeypot / can't-sell is a definitive scam contract (T1.006) — force
            # suspected regardless of the market score. The human tier confirms.
            if "honeypot" in gp_flags:
                rec["status"] = "suspected"
                contract_scam += 1

        # Merge DexScreener market-structure signs (OAK T2).
        dx = dxmap.get(sym)
        if dx is not None:
            dx_flags, dx_oak, dx_fields = dexscreener.liquidity_signs(dx, now_ms)
            for fl in dx_flags:
                if fl not in rec["flags"]:
                    rec["flags"].append(fl)
            for t in dx_oak:
                if t not in rec["oak_techniques"]:
                    rec["oak_techniques"].append(t)
            rec["context"].update({k: v for k, v in dx_fields.items() if v is not None})

        records.append(rec)

    records.sort(key=lambda r: (len(r["flags"]), r["score"], r["confidence"]), reverse=True)
    suspected = sum(1 for r in records if r["status"] == "suspected")

    # --- Consolidate per TOKEN (one row per coin, signs unioned across venues) ---
    # "Привести в чувство": the list is by token, not by 3.8k markets.
    by_token = {}
    for r in records:
        sym = r["symbol"]
        t = by_token.get(sym)
        if t is None:
            t = by_token[sym] = {
                "symbol": sym, "venues": [], "score": 0, "status": "watchlist",
                "flags": [], "oak_techniques": [], "context": {},
                "evidence": r.get("evidence", []),
            }
        if r["venue"] not in t["venues"]:
            t["venues"].append(r["venue"])
        t["score"] = max(t["score"], r["score"])
        if r["status"] == "suspected":
            t["status"] = "suspected"
        for fl in r["flags"]:
            if fl not in t["flags"]:
                t["flags"].append(fl)
        for o in r["oak_techniques"]:
            if o not in t["oak_techniques"]:
                t["oak_techniques"].append(o)
        for k, v in (r.get("context") or {}).items():
            if v is not None and k not in t["context"]:
                t["context"][k] = v
    token_list = sorted(by_token.values(),
                        key=lambda t: (len(t["flags"]), t["score"], len(t["venues"])),
                        reverse=True)

    # Flag tally is per TOKEN (so a coin on 5 venues counts once).
    flag_counts = {}
    for t in token_list:
        for fl in t["flags"]:
            flag_counts[fl] = flag_counts.get(fl, 0) + 1
    multi_sign = sum(1 for t in token_list if len(t["flags"]) >= 2)
    suspected_tokens = sum(1 for t in token_list if t["status"] == "suspected")

    dataset = {
        "schema": "mgterminal.crime-coins/v0.5-bytoken",
        "disclaimer": "Automated manipulation-risk heuristic. 'suspected' is an "
                      "unverified machine signal, not an accusation. See README.",
        "generated_at": now,
        "venues": by_venue,
        "count": len(records),
        "token_count": len(token_list),
        "enriched": enriched,
        "contract_checked": len(secmap),
        "dex_checked": len(dxmap),
        "contract_scam": contract_scam,
        "suspected": suspected,
        "suspected_tokens": suspected_tokens,
        "multi_sign": multi_sign,
        "flag_counts": flag_counts,
        "by_token": token_list,
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
                            "token_count": len(token_list),
                            "suspected_tokens": suspected_tokens, "multi_sign": multi_sign,
                            "contract_scam": contract_scam, "flag_counts": flag_counts,
                            "venues": by_venue}) + "\n")

    return dataset


def main() -> int:
    ds = run()
    print(f"swept {ds['count']} markets -> {ds['token_count']} tokens across "
          f"{len(ds['venues'])} venues @ {ds['generated_at']}")
    print(f"  enriched {ds.get('enriched',0)} | GoPlus {ds.get('contract_checked',0)} | "
          f"DexScreener {ds.get('dex_checked',0)}")
    print(f"  suspected tokens: {ds['suspected_tokens']}   multi-sign (>=2): {ds['multi_sign']}   "
          f"honeypot: {ds.get('contract_scam', 0)}")
    print("  flags (per token):", ", ".join(f"{k}={v}" for k, v in sorted(ds["flag_counts"].items())) or "none")
    print()
    print(f"{'TOKEN':<13}{'VENUES':>7}{'SCORE':>6}  {'STATUS':<10}{'FLAGS'}")
    print("-" * 90)
    for t in ds["by_token"][:30]:
        flags = ",".join(t.get("flags", [])) or "-"
        print(f"{t['symbol']:<13}{len(t['venues']):>7}{t['score']:>6}  "
              f"{t['status']:<10}{flags}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
