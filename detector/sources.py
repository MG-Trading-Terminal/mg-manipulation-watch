"""
Data sources — best-effort, free, no-key fetchers (stdlib only).

Each fetch is wrapped so one dead source never kills a row: on any error the
corresponding `Signals` field stays None and the scorer degrades gracefully and
lowers confidence (see crime_score). This keeps the 4h pipeline robust.

Free sources wired here:
  * Binance USD-M futures  -> funding rate + interval, open interest, 24h volume
  * CoinGecko (free)       -> market cap, 24h volume
  * DefiLlama (free)       -> protocol TVL, annualized fees (for P/S)

Optional / keyed signals (supply concentration, wash-trade detection) are NOT
fetched here in v1 — they are supplied per-token in the universe file
(`top_holders_pct`, `wash_volume_flag`) until a keyed fetcher is added.
See SOURCES.md for the full catalog and upgrade path.
"""
from __future__ import annotations

import json
import urllib.request
from typing import Any, Optional

from .crime_score import Signals

_TIMEOUT = 10
_UA = {"User-Agent": "mgterminal-crime-scan/0.1 (+https://mgterminal.com)"}

BINANCE_FAPI = "https://fapi.binance.com"
COINGECKO = "https://api.coingecko.com/api/v3"
DEFILLAMA = "https://api.llama.fi"


def _get_json(url: str) -> Optional[Any]:
    try:
        req = urllib.request.Request(url, headers=_UA)
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def _f(x: Any) -> Optional[float]:
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------- #
# Binance USD-M futures                                                        #
# --------------------------------------------------------------------------- #
_FUNDING_INFO = None  # process-level cache: {symbol: interval_hours}


def _funding_interval(binance_symbol: str) -> float:
    global _FUNDING_INFO
    if _FUNDING_INFO is None:
        _FUNDING_INFO = {}
        info = _get_json(f"{BINANCE_FAPI}/fapi/v1/fundingInfo")
        if isinstance(info, list):
            for it in info:
                ih = _f(it.get("fundingIntervalHours"))
                if it.get("symbol") and ih:
                    _FUNDING_INFO[it["symbol"]] = ih
    return _FUNDING_INFO.get(binance_symbol, 8.0)


def binance_funding_oi(binance_symbol: str):
    """Returns (funding_rate, interval_hours, open_interest_usd, volume_24h_usd)."""
    funding_rate = interval_h = oi_usd = vol_usd = None
    mark = None

    prem = _get_json(f"{BINANCE_FAPI}/fapi/v1/premiumIndex?symbol={binance_symbol}")
    if isinstance(prem, dict):
        funding_rate = _f(prem.get("lastFundingRate"))
        mark = _f(prem.get("markPrice"))

    # Funding interval: default 8h; some symbols use 4h/1h (fundingInfo lists them).
    # fundingInfo returns the whole list; fetch it once per process (matters when
    # sweeping the full perp universe — otherwise it's one call per symbol).
    interval_h = _funding_interval(binance_symbol)

    oi = _get_json(f"{BINANCE_FAPI}/fapi/v1/openInterest?symbol={binance_symbol}")
    if isinstance(oi, dict) and mark:
        oi_base = _f(oi.get("openInterest"))
        if oi_base is not None:
            oi_usd = oi_base * mark

    tick = _get_json(f"{BINANCE_FAPI}/fapi/v1/ticker/24hr?symbol={binance_symbol}")
    if isinstance(tick, dict):
        vol_usd = _f(tick.get("quoteVolume"))

    return funding_rate, interval_h, oi_usd, vol_usd


# --------------------------------------------------------------------------- #
# CoinGecko (free)                                                            #
# --------------------------------------------------------------------------- #
def coingecko_market(cg_id: str):
    """Returns (market_cap_usd, volume_24h_usd)."""
    data = _get_json(f"{COINGECKO}/coins/markets?vs_currency=usd&ids={cg_id}")
    if isinstance(data, list) and data:
        d = data[0]
        return _f(d.get("market_cap")), _f(d.get("total_volume"))
    return None, None


# --------------------------------------------------------------------------- #
# DefiLlama (free)                                                            #
# --------------------------------------------------------------------------- #
def defillama_tvl(slug: str) -> Optional[float]:
    data = _get_json(f"{DEFILLAMA}/tvl/{slug}")
    return _f(data) if data is not None else None


def defillama_fees_annualized(slug: str) -> Optional[float]:
    data = _get_json(f"{DEFILLAMA}/summary/fees/{slug}")
    if isinstance(data, dict):
        d24 = _f(data.get("total24h"))
        if d24 is not None:
            return d24 * 365.0
    return None


# --------------------------------------------------------------------------- #
# Orchestrator                                                                #
# --------------------------------------------------------------------------- #
def fetch_signals(entry: dict) -> Signals:
    """
    Build a Signals snapshot for one universe entry. Expected keys (all optional
    except `symbol`):
      symbol, binance_symbol, cg_id, defillama_slug, top_holders_pct, wash_volume_flag
    """
    s = Signals()

    if entry.get("cg_id"):
        s.market_cap_usd, s.volume_24h_usd = coingecko_market(entry["cg_id"])

    if entry.get("binance_symbol"):
        fr, ih, oi, vol = binance_funding_oi(entry["binance_symbol"])
        s.funding_rate = fr
        s.funding_interval_hours = ih
        s.open_interest_usd = oi
        if s.volume_24h_usd is None:
            s.volume_24h_usd = vol

    if entry.get("defillama_slug"):
        s.tvl_usd = defillama_tvl(entry["defillama_slug"])
        s.fees_annualized_usd = defillama_fees_annualized(entry["defillama_slug"])

    # Manually-supplied (keyed) signals until a fetcher exists.
    if entry.get("top_holders_pct") is not None:
        s.top_holders_pct = float(entry["top_holders_pct"])
    if entry.get("wash_volume_flag") is not None:
        s.wash_volume_flag = bool(entry["wash_volume_flag"])

    return s
