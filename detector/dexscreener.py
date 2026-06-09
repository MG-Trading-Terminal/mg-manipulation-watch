"""
dexscreener — DEX liquidity / pair-age adapter (free, no key).

The "not only on-chain-contract" market layer: how thin is the spot pool and how
fresh is the pair. A perp-driven price sitting on a paper-thin spot pool, or a
brand-new pair already at a large FDV, is the manipulation-prone setup
(OAK-T2 — Liquidity Establishment).

GoPlus tells us WHAT the contract can do; DexScreener tells us how MANIPULABLE the
market around it is. Queried per-address (DexScreener's multi-address response caps
at 30 pairs total, so batching is unreliable); results cached by the caller.
"""
from __future__ import annotations

import json
import time
import urllib.request
from typing import Optional

_UA = {"User-Agent": "mgterminal-crime-scan/0.1 (+https://manipulation.mgterminal.com)"}
_TIMEOUT = 15

# OAK-T2 thresholds.
THIN_LIQ_FRAC = 0.01        # spot pool < 1% of FDV = paper-thin vs valuation
THIN_LIQ_ABS = 50_000.0     # ...or under $50k absolute while FDV is material
FRESH_DAYS = 30             # pair younger than 30d
MIN_FDV = 20_000_000.0      # only flag when the valuation is material


def _get(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=_UA), timeout=_TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def _f(x) -> Optional[float]:
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def token_market(address: str, pacing: float = 0.4) -> dict:
    """Best (max-liquidity) DEX pair for a token address -> compact market dict.

    Returns {"_no_data": True} when DexScreener has no pair, so the caller can
    cache it as checked.
    """
    d = _get(f"https://api.dexscreener.com/latest/dex/tokens/{address}")
    time.sleep(pacing)
    pairs = (d or {}).get("pairs") or []
    if not pairs:
        return {"_no_data": True}
    best = max(pairs, key=lambda p: (p.get("liquidity") or {}).get("usd") or 0)
    return {
        "liq_usd": _f((best.get("liquidity") or {}).get("usd")),
        "fdv": _f(best.get("fdv")),
        "vol24": _f((best.get("volume") or {}).get("h24")),
        "pair_created_ms": best.get("pairCreatedAt"),
        "chain": best.get("chainId"),
        "dex": best.get("dexId"),
    }


def search(symbol: str, pacing: float = 0.3) -> dict:
    """Find a token by ticker on any DEX. Returns the best (max-liquidity) pair whose
    base symbol matches — {chain, contract, liq_usd, fdv, pair_created_ms} — or
    {"_no_data": True} if NO on-chain pair exists (i.e. it's not a crypto token:
    a tokenized stock / index / commodity). None on transient error (retry later)."""
    d = _get(f"https://api.dexscreener.com/latest/dex/search?q={symbol}")
    time.sleep(pacing)
    if not isinstance(d, dict):
        return None
    up = symbol.upper()
    pairs = [p for p in (d.get("pairs") or [])
             if ((p.get("baseToken") or {}).get("symbol") or "").upper() == up]
    if not pairs:
        return {"_no_data": True}
    best = max(pairs, key=lambda p: (p.get("liquidity") or {}).get("usd") or 0)
    return {
        "chain": best.get("chainId"),
        "contract": (best.get("baseToken") or {}).get("address"),
        "liq_usd": _f((best.get("liquidity") or {}).get("usd")),
        "fdv": _f(best.get("fdv")),
        "pair_created_ms": best.get("pairCreatedAt"),
    }


def liquidity_signs(market: dict, now_ms: float):
    """Return (flags, oak_techniques, fields) from a token_market dict."""
    if not market or market.get("_no_data"):
        return [], [], {}
    flags, oak, f = [], [], {}
    liq = market.get("liq_usd")
    fdv = market.get("fdv")
    f["liq_usd"] = round(liq) if liq is not None else None
    if liq is not None and fdv and fdv >= MIN_FDV:
        frac = liq / fdv if fdv else None
        if frac is not None:
            f["liq_to_fdv"] = round(frac, 5)
        if (frac is not None and frac < THIN_LIQ_FRAC) or liq < THIN_LIQ_ABS:
            flags.append("thin-liquidity")          # OAK-T2
            oak.append("OAK-T2")
    created = market.get("pair_created_ms")
    if created:
        age_days = (now_ms - float(created)) / 86_400_000.0
        f["pair_age_days"] = round(age_days, 1)
        if age_days < FRESH_DAYS and (fdv or 0) >= MIN_FDV:
            flags.append("fresh-launch")            # OAK-T2 / T1
            if "OAK-T2" not in oak:
                oak.append("OAK-T2")
    return flags, oak, f
