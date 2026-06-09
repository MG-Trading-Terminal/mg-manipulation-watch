"""
dumps — systematic historical dump analysis from the full price chart.

For every token we pull CoinGecko market_chart (max history, daily) and measure
the dump record over ALL time, not a single ATH snapshot:
  * max_drawdown  — worst peak→trough fall ever (e.g. -0.98)
  * biggest_drop  — sharpest 30-day crash + when
  * n_major       — how many distinct ≥50% collapses it has had
  * recovered     — is it back above half its all-time peak?
  * pump_dump     — ran up >=3x then fell >=80% (the rug shape)
This is the data scanners have; we take it, cross-reference it, and score it.

`dump_metrics` is pure (list of [ts_ms, price]) so it's testable offline; the
fetch is cached/budgeted by the caller (CoinGecko key + pacing).
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from typing import Optional

_UA = {"User-Agent": "mgterminal-crime-scan/0.1 (+https://mgterminal.com)"}
_TIMEOUT = 25
_CG_KEY = os.environ.get("COINGECKO_API_KEY")


def _cg(url: str) -> str:
    return url + ("&" if "?" in url else "?") + "x_cg_demo_api_key=" + _CG_KEY if _CG_KEY else url


def _get(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=_UA), timeout=_TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def _date(ts_ms) -> Optional[str]:
    # ts is ms; format without datetime.now (avoid clock deps) — simple UTC date.
    try:
        import datetime
        return datetime.datetime.utcfromtimestamp(ts_ms / 1000.0).strftime("%Y-%m-%d")
    except Exception:
        return None


def dump_metrics(prices) -> Optional[dict]:
    pts = [(p[0], float(p[1])) for p in (prices or []) if p and p[1] and float(p[1]) > 0]
    if len(pts) < 20:
        return None

    ath = max(pts, key=lambda x: x[1])
    first = pts[0][1]
    cur = pts[-1][1]

    # worst peak->trough drawdown over the whole series
    run_peak, max_dd, max_dd_ts = pts[0][1], 0.0, pts[0][0]
    # distinct >=50% collapses (reset running peak after each counted crash)
    n_major, crash_peak, counted = 0, pts[0][1], False
    for ts, px in pts:
        if px > run_peak:
            run_peak = px
        dd = px / run_peak - 1.0
        if dd < max_dd:
            max_dd, max_dd_ts = dd, ts
        # major-crash counter
        if px > crash_peak:
            crash_peak, counted = px, False
        elif not counted and px <= 0.5 * crash_peak:
            n_major += 1
            counted = True
            crash_peak = px

    # sharpest ~30-sample window crash + date
    biggest, biggest_ts = 0.0, None
    w = 30 if len(pts) > 45 else max(2, len(pts) // 3)
    for i in range(w, len(pts)):
        chg = pts[i][1] / pts[i - w][1] - 1.0
        if chg < biggest:
            biggest, biggest_ts = chg, pts[i][0]

    run_up = ath[1] / first if first > 0 else 0.0
    pump_dump = run_up >= 3.0 and max_dd <= -0.80
    recovered = cur >= 0.5 * ath[1]

    # Downsample for a sparkline (~60 evenly-spaced points) + marker positions.
    n_pts = 60
    step = max(1, len(pts) // n_pts)
    samp = pts[::step]
    if samp[-1] != pts[-1]:
        samp.append(pts[-1])
    t0, t1 = samp[0][0], samp[-1][0]
    span = (t1 - t0) or 1
    spark = [round(p, 10) for _, p in samp]

    def _frac(ts):
        return round((ts - t0) / span, 4) if ts else None

    return {
        "max_drawdown": round(max_dd, 4),
        "ath_date": _date(ath[0]),
        "biggest_drop": round(biggest, 4),
        "biggest_drop_date": _date(biggest_ts),
        "n_major": n_major,
        "run_up": round(run_up, 1),
        "pump_dump": pump_dump,
        "recovered": recovered,
        "history_days": len(pts),
        "spark": spark,
        "peak_at": _frac(ath[0]),
        "dump_at": _frac(biggest_ts),
    }


def dump_history(cg_id: str):
    """Returns dump_metrics dict, {"_no_data": True}, or None (transient -> retry)."""
    # days=max / interval=daily are Pro-only (401 on Demo); 365d daily is allowed
    # and is enough to catch recent dumps/collapses.
    url = (f"https://api.coingecko.com/api/v3/coins/{cg_id}/market_chart"
           "?vs_currency=usd&days=365")
    d = None
    for attempt in range(3):
        d = _get(_cg(url))
        if isinstance(d, dict):
            break
        time.sleep(4 * (attempt + 1))   # backoff on transient / rate-limit
    if not isinstance(d, dict):
        return None                      # transient — caller must NOT cache; retry next run
    m = dump_metrics(d.get("prices"))
    return m if m else {"_no_data": True}
