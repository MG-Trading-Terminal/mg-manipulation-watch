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

# Optional free CoinGecko Demo API key (env) — the clean way past the rate limit.
CG_KEY = os.environ.get("COINGECKO_API_KEY")


def _cg(url: str) -> str:
    """Append the CoinGecko demo key to a CoinGecko URL if one is configured."""
    if CG_KEY:
        return url + ("&" if "?" in url else "?") + "x_cg_demo_api_key=" + CG_KEY
    return url


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
               "&order=market_cap_desc&per_page=250&price_change_percentage=24h,7d,30d"
               f"&page={page}")
        # Retry a rate-limited page rather than breaking the whole pagination
        # (a single 429 must not truncate the universe to a few hundred coins).
        data = None
        for attempt in range(3):
            data = _get(_cg(url))
            if isinstance(data, list):
                break
            time.sleep(5)
        if not isinstance(data, list):
            continue          # skip this page, keep going
        if not data:
            break             # genuinely past the last page
        for c in data:
            s = (c.get("symbol") or "").upper()
            mc = _f(c.get("market_cap"))
            if not s or mc is None:
                continue
            if s not in out or mc > out[s]["mc"]:
                out[s] = {
                    "mc": mc,
                    "vol": _f(c.get("total_volume")),
                    "fdv": _f(c.get("fully_diluted_valuation")),
                    "id": c.get("id"),
                    # live market metrics (refreshed each scan via refresh_markets)
                    "price": _f(c.get("current_price")),
                    "ath": _f(c.get("ath")),
                    "ath_pct": _f(c.get("ath_change_percentage")),     # % from all-time high (the dump)
                    "ath_date": c.get("ath_date"),
                    "chg24": _f(c.get("price_change_percentage_24h_in_currency")),
                    "chg7d": _f(c.get("price_change_percentage_7d_in_currency")),
                    "chg30d": _f(c.get("price_change_percentage_30d_in_currency")),
                }
        time.sleep(2.5)  # free-tier pacing (python sleep, not the shell)
    return out


def refresh_markets(maps: dict, pages: int = 0) -> int:
    """Re-fetch the bulk markets pages and merge fresh price / ATH-drawdown /
    24h-7d-30d change / volume into the cached cg map (so the risk profile updates
    every scan) AND extend the symbol->id coverage deeper into the long tail.
    Static fields (platforms, detail) are left untouched. Depth = env CG_PAGES."""
    pages = pages or int(os.environ.get("CG_PAGES", "40"))
    fresh = _coingecko_markets(pages)
    cg = maps.setdefault("cg", {})
    n = 0
    for sym, m in fresh.items():
        e = cg.setdefault(sym, {})
        e.update(m)            # mc/vol/fdv/price/ath/ath_pct/chg* refresh; id preserved/set
        n += 1
    if n:
        with open(CACHE, "w", encoding="utf-8") as f:
            json.dump(maps, f)
    return n


# Live market metrics for a perp base symbol (price, dump, changes, volume).
def market_for(base_symbol: str, maps: dict):
    cg = maps.get("cg", {}).get(norm_symbol(base_symbol))
    if not cg:
        return None
    m = {k: cg.get(k) for k in ("price", "ath", "ath_pct", "ath_date", "chg24", "chg7d", "chg30d")}
    m["vol_24h"] = cg.get("vol")
    m["market_cap"] = cg.get("mc")
    return m if any(v is not None for v in m.values()) else None


def _coingecko_platforms() -> Dict[str, dict]:
    """id -> {platform: contract_address} for the whole market (one big call).

    ~10MB payload — needs a long timeout, and must run BEFORE the paginated
    markets calls or it gets rate-limited. Retries a few times.
    """
    url = "https://api.coingecko.com/api/v3/coins/list?include_platform=true"
    out = {}
    for attempt in range(4):
        try:
            req = urllib.request.Request(_cg(url), headers=_UA)
            with urllib.request.urlopen(req, timeout=90) as r:
                data = json.loads(r.read().decode("utf-8"))
            if isinstance(data, list):
                for c in data:
                    pf = {k: v for k, v in (c.get("platforms") or {}).items() if v}
                    if pf and c.get("id"):
                        out[c["id"]] = pf
                if out:
                    return out
        except Exception:
            pass
        time.sleep(6)
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


def build(pages: int = 0) -> dict:
    pages = pages or int(os.environ.get("CG_PAGES", "40"))  # depth into the long tail
    platforms = _coingecko_platforms()   # big call first (before pagination throttles)
    cg = _coingecko_markets(pages)
    dl = _defillama()
    maps = {"cg": cg, "dl": dl, "platforms": platforms,
            "stats": {"cg_symbols": len(cg), "dl_symbols": len(dl),
                      "platform_ids": len(platforms)}}
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(maps, f)
    return maps


def contract_platforms(base_symbol: str, maps: dict):
    """{platform: address} for a perp base symbol, via its CoinGecko id."""
    cg = maps.get("cg", {}).get(norm_symbol(base_symbol))
    cid = (cg or {}).get("id")
    if not cid:
        return None
    return maps.get("platforms", {}).get(cid)


def cg_id_for(base_symbol: str, maps: dict):
    cg = maps.get("cg", {}).get(norm_symbol(base_symbol))
    return (cg or {}).get("id")


def coingecko_detail(cg_id: str) -> dict:
    """Compact project PROFILE from /coins/{id}: what it is, who's behind it,
    socials, categories, all-chain contracts, rank. {"_no_data": True} if absent."""
    url = (f"https://api.coingecko.com/api/v3/coins/{cg_id}"
           "?localization=false&tickers=false&market_data=false"
           "&community_data=false&developer_data=false&sparkline=false")
    d = None
    for attempt in range(3):
        d = _get(_cg(url))
        if isinstance(d, dict):
            break
        time.sleep(4 * (attempt + 1))  # backoff on transient / rate-limit
    if not isinstance(d, dict):
        return None                    # transient — caller must NOT cache; retry next run
    if not d.get("id"):
        return {"_no_data": True}      # genuine miss — safe to cache
    links = d.get("links") or {}
    homepage = next((u for u in (links.get("homepage") or []) if u), None)
    chat = next((u for u in (links.get("chat_url") or []) if u), None)
    tw = links.get("twitter_screen_name")
    tg = links.get("telegram_channel_identifier")
    desc = (d.get("description") or {}).get("en") or ""
    desc = " ".join(desc.split())  # collapse whitespace/newlines
    return {
        "name": d.get("name"),
        "description": desc[:600],
        "homepage": homepage,
        "twitter": f"https://x.com/{tw}" if tw else None,
        "telegram": f"https://t.me/{tg}" if tg else None,
        "chat": chat,
        "categories": [c for c in (d.get("categories") or []) if c][:6],
        "platforms": {k: v for k, v in (d.get("platforms") or {}).items() if v},
        "rank": d.get("market_cap_rank"),
        "image": ((d.get("image") or {}).get("small")) or None,
    }


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
    """Return (market_cap_usd, tvl_usd, fees_annualized_usd, volume_usd, fdv_usd).

    MC is always returned (drives OI/MC). TVL & fees — the MC/TVL and P/S signals —
    are suppressed for stablecoins and non-protocol categories, where the ratio is
    meaningless and would false-positive on legit tokens (DOT, CRO, USDC…).
    """
    s = norm_symbol(base_symbol)
    cg = maps.get("cg", {}).get(s)
    dl = maps.get("dl", {}).get(s)
    mc = (cg or {}).get("mc")
    vol = (cg or {}).get("vol")
    fdv = (cg or {}).get("fdv")
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
    return mc, tvl, fees, vol, fdv


def main(argv) -> int:
    maps = build()
    s = maps["stats"]
    print(f"enrichment cache built: {s['cg_symbols']} CoinGecko symbols, "
          f"{s['dl_symbols']} DefiLlama symbols, {s.get('platform_ids', 0)} contract-platform ids "
          f"-> {CACHE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
