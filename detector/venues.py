"""
venues — multi-exchange perp adapters.

Crime coins are NOT mostly on Binance — the long tail lives on MEXC / Gate /
Bitget / Bybit / Hyperliquid (where everything gets listed and wash-volume is run
before a coin "graduates"). Each adapter makes ONE bulk call and returns a list of
normalized tickers so the same scorer runs market-wide.

Normalized ticker dict:
  { venue, symbol, market, funding_rate, funding_interval_hours,
    open_interest_usd, volume_24h_usd }

All adapters are defensive: a venue that errors returns [] (never aborts a sweep).
USD open-interest is exact where the venue gives it (Bybit/Bitget/Gate/HL); MEXC's
is approximate (see note). Binance has no bulk OI endpoint, so its rows carry
funding only here — the curated detector.pipeline covers Binance OI per-symbol.
"""
from __future__ import annotations

import json
import urllib.request
from typing import List, Optional

_TIMEOUT = 15
_UA = {"User-Agent": "mgterminal-crime-scan/0.1 (+https://mgterminal.com)"}


def _get(url: str, data: Optional[bytes] = None, headers=None):
    try:
        h = dict(_UA)
        if headers:
            h.update(headers)
        req = urllib.request.Request(url, data=data, headers=h)
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def _f(x) -> Optional[float]:
    try:
        v = float(x)
        return v
    except (TypeError, ValueError):
        return None


def _t(venue, symbol, market, fr, ih, oi, vol):
    return {"venue": venue, "symbol": symbol, "market": market,
            "funding_rate": fr, "funding_interval_hours": ih,
            "open_interest_usd": oi, "volume_24h_usd": vol}


# --------------------------------------------------------------------------- #
def binance() -> List[dict]:
    """Funding + volume in 2 bulk calls. No bulk OI endpoint -> oi=None here."""
    prem = _get("https://fapi.binance.com/fapi/v1/premiumIndex")
    tick = _get("https://fapi.binance.com/fapi/v1/ticker/24hr")
    info = _get("https://fapi.binance.com/fapi/v1/fundingInfo")
    if not isinstance(prem, list):
        return []
    vol = {t["symbol"]: _f(t.get("quoteVolume")) for t in tick} if isinstance(tick, list) else {}
    interval = {}
    if isinstance(info, list):
        for it in info:
            ih = _f(it.get("fundingIntervalHours"))
            if it.get("symbol") and ih:
                interval[it["symbol"]] = ih
    out = []
    for p in prem:
        sym = p.get("symbol", "")
        if not sym.endswith("USDT"):
            continue
        out.append(_t("binance", sym[:-4], sym, _f(p.get("lastFundingRate")),
                      interval.get(sym, 8.0), None, vol.get(sym)))
    return out


def bybit() -> List[dict]:
    d = _get("https://api.bybit.com/v5/market/tickers?category=linear")
    if not isinstance(d, dict):
        return []
    out = []
    for t in d.get("result", {}).get("list", []):
        sym = t.get("symbol", "")
        if not sym.endswith("USDT"):
            continue
        out.append(_t("bybit", sym[:-4], sym, _f(t.get("fundingRate")),
                      _f(t.get("fundingIntervalHour")) or 8.0,
                      _f(t.get("openInterestValue")), _f(t.get("turnover24h"))))
    return out


def bitget() -> List[dict]:
    d = _get("https://api.bitget.com/api/v2/mix/market/tickers?productType=usdt-futures")
    if not isinstance(d, dict):
        return []
    out = []
    for t in d.get("data", []):
        sym = t.get("symbol", "")
        base = sym[:-4] if sym.endswith("USDT") else sym
        oi_base = _f(t.get("holdingAmount"))
        mark = _f(t.get("markPrice"))
        oi_usd = oi_base * mark if (oi_base is not None and mark) else None
        out.append(_t("bitget", base, sym, _f(t.get("fundingRate")), 8.0,
                      oi_usd, _f(t.get("usdtVolume"))))
    return out


def gate() -> List[dict]:
    d = _get("https://api.gateio.ws/api/v4/futures/usdt/tickers")
    if not isinstance(d, list):
        return []
    out = []
    for t in d:
        c = t.get("contract", "")
        base = c[:-5] if c.endswith("_USDT") else c
        # OI USD = total_size (contracts) * quanto_multiplier (size) * mark_price
        size = _f(t.get("total_size"))
        mult = _f(t.get("quanto_multiplier")) or 1.0
        mark = _f(t.get("mark_price"))
        oi_usd = size * mult * mark if (size is not None and mark) else None
        out.append(_t("gate", base, c, _f(t.get("funding_rate")), 8.0,
                      oi_usd, _f(t.get("volume_24h_settle"))))
    return out


def mexc() -> List[dict]:
    d = _get("https://contract.mexc.com/api/v1/contract/ticker")
    if not isinstance(d, dict):
        return []
    out = []
    for t in d.get("data", []):
        sym = t.get("symbol", "")
        base = sym.split("_")[0] if "_" in sym else sym
        # OI omitted: holdVol is in CONTRACTS and MEXC contract size varies wildly,
        # so holdVol*price is not a valid USD OI (it inflated BTC/stocks to max).
        # Funding + USD turnover (amount24) are reliable; OI awaits contractSize v2.
        out.append(_t("mexc", base, sym, _f(t.get("fundingRate")), 8.0,
                      None, _f(t.get("amount24"))))
    return out


def hyperliquid() -> List[dict]:
    d = _get("https://api.hyperliquid.xyz/info",
             data=json.dumps({"type": "metaAndAssetCtxs"}).encode(),
             headers={"Content-Type": "application/json"})
    if not isinstance(d, list) or len(d) < 2:
        return []
    meta = d[0].get("universe", [])
    ctxs = d[1]
    out = []
    for m, c in zip(meta, ctxs):
        name = m.get("name", "")
        oi_base = _f(c.get("openInterest"))
        mark = _f(c.get("markPx"))
        oi_usd = oi_base * mark if (oi_base is not None and mark) else None
        # HL funding is HOURLY (interval=1) — the scorer normalizes to daily.
        out.append(_t("hyperliquid", name, name, _f(c.get("funding")), 1.0,
                      oi_usd, _f(c.get("dayNtlVlm"))))
    return out


ADAPTERS = {
    "binance": binance,
    "bybit": bybit,
    "bitget": bitget,
    "gate": gate,
    "mexc": mexc,
    "hyperliquid": hyperliquid,
}


def all_tickers(venues=None) -> List[dict]:
    """Fan out across venues (sequential bulk calls). Returns one row per market."""
    names = venues or list(ADAPTERS)
    out = []
    for name in names:
        rows = ADAPTERS[name]()
        out.extend(rows)
    return out
