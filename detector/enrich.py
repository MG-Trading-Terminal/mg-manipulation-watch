"""
enrich — bulk market-cap / TVL / fees maps for the WHOLE market.

The fundamental signals (MC/TVL, P/S, OI-as-fraction-of-float) need market cap and
TVL per token. Fetching those per-token would be thousands of calls; instead we
pull them in BULK and build symbol-keyed maps once (cached):

  CoinGecko /coins/markets   (paginated)  -> symbol -> market cap, volume
  DefiLlama /protocols       (1 call)     -> symbol -> TVL (+ mcap fallback)
  DefiLlama /overview/fees   (1 call)     -> symbol -> annualized fees (via slug)

So collect.py can score every one of the ~3.8k markets with the full signal set,
not just funding. Maps cache to data/enrich/maps.json; rebuild with --refresh.

Run:  python3 -m detector.enrich            # build/refresh the cache
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.request
from typing import Dict, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "data", "enrich", "maps.json")

_UA = {"User-Agent": "mgterminal-crime-scan/0.1 (+https://mgterminal.com)"}
_TIMEOUT = 20
# Binance/Bybit contract-size prefixes — strip so "1000PEPE" matches "PEPE".
_PREFIX = re.compile(r"^(1000000|100000|10000|1000|1M|1MB|1B|1K|K)(?=[A-Z])")


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


def norm_symbol(sym: str) -> str:
    """Normalize a perp base symbol for cross-source matching."""
    s = (sym or "").upper().strip()
    s = _PREFIX.sub("", s)
    return s


def _coingecko_markets(pages: int) -> Dict[str, dict]:
    out = {}
    for page in range(1, pages + 1):
        url = ("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd"
               f"&order=market_cap_desc&per_page=250&page={page}")
        data = _get(url)
        if not isinstance(data, list) or not data:
            break
        for c in data:
            s = (c.get("symbol") or "").upper()
            mc = _f(c.get("market_cap"))
            if not s or mc is None:
                continue
            if s not in out or mc > out[s]["mc"]:
                out[s] = {"mc": mc, "vol": _f(c.get("total_volume"))}
        time.sleep(2.5)  # free-tier pacing (python sleep, not the shell)
    return out


def _defillama() -> Dict[str, dict]:
    """symbol -> {tvl, mcap}, plus annualized fees via slug->symbol."""
    out = {}
    slug2sym = {}
    prot = _get("https://api.llama.fi/protocols")
    if isinstance(prot, list):
        for p in prot:
            s = (p.get("symbol") or "").upper()
            if not s or s == "-":
                continue
            slug2sym[p.get("slug")] = s
            tvl = _f(p.get("tvl"))
            mc = _f(p.get("mcap"))
            cat = p.get("category")
            rec = out.setdefault(s, {"tvl": None, "mcap": None, "fees": None, "category": None})
            if tvl is not None and (rec["tvl"] is None or tvl > rec["tvl"]):
                rec["tvl"] = tvl
                rec["category"] = cat  # category of the dominant (max-TVL) protocol
            if mc is not None and (rec["mcap"] is None or mc > rec["mcap"]):
                rec["mcap"] = mc
    fees = _get("https://api.llama.fi/overview/fees")
    if isinstance(fees, dict):
        for p in fees.get("protocols", []):
            sym = slug2sym.get(p.get("module"))
            f24 = _f(p.get("total24h"))
            if sym and f24:
                rec = out.setdefault(sym, {"tvl": None, "mcap": None, "fees": None, "category": None})
                ann = f24 * 365.0
                if rec["fees"] is None or ann > rec["fees"]:
                    rec["fees"] = ann
    return out


def build(pages: int = 16) -> dict:
    cg = _coingecko_markets(pages)
    dl = _defillama()
    maps = {"cg": cg, "dl": dl,
            "stats": {"cg_symbols": len(cg), "dl_symbols": len(dl)}}
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(maps, f)
    return maps


def load(rebuild_if_missing: bool = True) -> dict:
    if os.path.exists(CACHE):
        with open(CACHE, "r", encoding="utf-8") as f:
            return json.load(f)
    return build() if rebuild_if_missing else {"cg": {}, "dl": {}}


# Stablecoins are never crime-coin targets; their MC/TVL & P/S ratios are noise.
STABLES = {"USDT", "USDC", "USDE", "DAI", "USD1", "FDUSD", "TUSD", "USDD", "FRAX",
           "PYUSD", "BUSD", "USDP", "GUSD", "LUSD", "USDX", "SUSD", "CRVUSD", "GHO",
           "USDB", "USR", "USDF", "RLUSD", "USDS", "USDY", "USTC", "EURC", "USD0"}
# Categories where "TVL" is not a comparable fundamental (L1s, exchanges, bridges…).
TVL_EXCLUDE_CATEGORIES = {"CEX", "Chain", "Bridge", "Stablecoins", "Infrastructure",
                          "RWA", "Wallets", "Payments", "Staking Pool", "Privacy"}


def lookup(base_symbol: str, maps: dict):
    """Return (market_cap_usd, tvl_usd, fees_annualized_usd, volume_usd).

    MC is always returned (drives OI/MC). TVL & fees — the MC/TVL and P/S signals —
    are suppressed for stablecoins and non-protocol categories, where the ratio is
    meaningless and would false-positive on legit tokens (DOT, CRO, USDC…).
    """
    s = norm_symbol(base_symbol)
    cg = maps.get("cg", {}).get(s)
    dl = maps.get("dl", {}).get(s)
    mc = (cg or {}).get("mc")
    vol = (cg or {}).get("vol")
    tvl = fees = None
    if dl:
        cat = dl.get("category")
        dl_mc = dl.get("mcap")
        # Same-asset guard: a TVL match by ticker is only trustworthy if the
        # protocol's OWN market cap agrees with CoinGecko's for that symbol
        # (within 3x). This kills collisions (e.g. DOT/FLOW -> some tiny protocol
        # of the same ticker -> spurious 200x MC/TVL).
        consistent = bool(mc and dl_mc and (1 / 3.0) <= (dl_mc / mc) <= 3.0)
        if consistent and s not in STABLES and cat not in TVL_EXCLUDE_CATEGORIES:
            tvl = dl.get("tvl")
            fees = dl.get("fees")
        if mc is None:
            mc = dl_mc  # DefiLlama mcap fallback (no CoinGecko hit)
    return mc, tvl, fees, vol


def main(argv) -> int:
    maps = build()
    print(f"enrichment cache built: {maps['stats']['cg_symbols']} CoinGecko symbols, "
          f"{maps['stats']['dl_symbols']} DefiLlama symbols -> {CACHE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
