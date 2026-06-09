"""
goplus — contract-security adapter (GoPlus Labs, free).

GoPlus is named as a reference implementation in OAK's detection specs
(T1.006 honeypot, T1.001/005 tax, T3.006 holder concentration). This adapter
batch-fetches token security and maps the fields onto OAK-grounded sign flags so
the watchlist can tell *scam contracts* from merely *suspicious markets*.

Thresholds come from the OAK specs:
  * T1.006 honeypot — is_honeypot / cannot_sell_all → structurally null legit
    overlap (a contract you can buy but not sell has no legitimate use).
  * T1.006 PATH C — sell_tax ≥ 0.99 ≈ a revert (honeypot-equivalent).
  * T1.001/005 — extractive sell tax.
  * T3.006 — team/holder supply control (top holders, excl. LP & locked).
"""
from __future__ import annotations

import json
import time
import urllib.request
from typing import Dict, List, Optional

_UA = {"User-Agent": "mgterminal-crime-scan/0.1 (+https://mgterminal.com)"}
_TIMEOUT = 20

# CoinGecko platform id -> GoPlus chain id (EVM chains GoPlus supports).
CG_PLATFORM_TO_CHAIN = {
    "ethereum": "1", "binance-smart-chain": "56", "polygon-pos": "137",
    "arbitrum-one": "42161", "base": "8453", "optimistic-ethereum": "10",
    "avalanche": "43114", "fantom": "250", "cronos": "25", "zksync": "324",
    "linea": "59144", "mantle": "5000", "opbnb": "204", "scroll": "534352",
}

# OAK-spec thresholds.
SELL_TAX_HONEYPOT = 0.99   # T1.006 PATH C: sell-tax >= 99% ~ revert
SELL_TAX_HIGH = 0.10       # T1.001/005: >10% sell tax is extractive
HOLDER_CONC_HIGH = 0.70    # T3.006: top non-LP/locked holders control majority
HOLDER_COUNT_LOW = 50      # near-zero distribution


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


def token_security(chain_id: str, addresses: List[str], pacing: float = 1.4) -> Dict[str, dict]:
    """GoPlus token_security for one chain, keyed by lowercased address.

    Queried ONE address at a time: GoPlus's multi-address batch only returns the
    tokens it has already analyzed (≈1 of 20 for a cold set), so per-address is
    the only reliable path. Results are cached by the caller, so this cost is paid
    once and 4h runs only fetch new contracts.
    """
    out = {}
    for a in sorted({a.lower() for a in addresses if a}):
        url = (f"https://api.gopluslabs.io/api/v1/token_security/{chain_id}"
               f"?contract_addresses={a}")
        d = _get(url)
        if isinstance(d, dict) and isinstance(d.get("result"), dict):
            for k, v in d["result"].items():
                out[k.lower()] = v
        time.sleep(pacing)  # free-tier pacing
    return out


def _top_holder_control(sec: dict) -> Optional[float]:
    """Sum of top holders that are NOT LP and NOT locked (the controllable float)."""
    holders = sec.get("holders")
    if not isinstance(holders, list) or not holders:
        return None
    total = 0.0
    for h in holders:
        if str(h.get("is_locked")) == "1":
            continue
        tag = (h.get("tag") or "").lower()
        if "lp" in tag or "pair" in tag or "dead" in tag or "burn" in tag:
            continue
        pct = _f(h.get("percent"))
        if pct:
            total += pct
    return total


def flags_from_security(sec: dict):
    """Return (flags, oak_techniques, fields) grounded in OAK specs."""
    flags, oak = [], []
    f = {}

    honeypot = str(sec.get("is_honeypot")) == "1" or str(sec.get("cannot_sell_all")) == "1"
    sell_tax = _f(sec.get("sell_tax"))
    buy_tax = _f(sec.get("buy_tax"))
    f["sell_tax"] = sell_tax
    f["buy_tax"] = buy_tax

    if honeypot or (sell_tax is not None and sell_tax >= SELL_TAX_HONEYPOT):
        flags.append("honeypot")            # T1.006 — can't sell
        oak.append("OAK-T1.006")
    elif sell_tax is not None and sell_tax >= SELL_TAX_HIGH:
        flags.append("high-tax")            # T1.001/005 — extractive tax
        oak.append("OAK-T1.001")

    if str(sec.get("is_mintable")) == "1":
        flags.append("mintable")            # hidden-mint dilution risk (T5.003 / T1)
        oak.append("OAK-T1.003")
    if (str(sec.get("transfer_pausable")) == "1" or str(sec.get("hidden_owner")) == "1"
            or str(sec.get("owner_change_balance")) == "1"):
        flags.append("owner-control")       # weaponizable authority (T1.004)
        oak.append("OAK-T1.004")
    if str(sec.get("is_open_source")) == "0":
        flags.append("closed-source")       # opacity

    conc = _top_holder_control(sec)
    f["top_holder_control"] = round(conc, 3) if conc is not None else None
    hc = _f(sec.get("holder_count"))
    f["holder_count"] = int(hc) if hc is not None else None
    if conc is not None and conc >= HOLDER_CONC_HIGH:
        flags.append("holder-concentration")   # T3.006 — supply control
        if "OAK-T3.006" not in oak:
            oak.append("OAK-T3.006")
    elif hc is not None and hc < HOLDER_COUNT_LOW:
        flags.append("holder-concentration")
        if "OAK-T3.006" not in oak:
            oak.append("OAK-T3.006")

    return flags, oak, f
