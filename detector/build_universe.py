"""
build_universe — populate data/universe.json with the FULL Binance USD-M perp list.

Pulls every TRADING, USDT-quoted PERPETUAL contract from Binance exchangeInfo and
merges it into the universe, preserving any hand-curated enrichment
(cg_id / defillama_slug / top_holders_pct / wash_volume_flag) already present for a
symbol. This is how we go from a 7-token demo set to a full-market sweep.

Run:  python3 -m detector.build_universe
"""
from __future__ import annotations

import json
import os

from .sources import _get_json, BINANCE_FAPI

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNIVERSE = os.path.join(ROOT, "data", "universe.json")

# Curated keys to carry over when a symbol already exists.
_KEEP = ("cg_id", "defillama_slug", "top_holders_pct", "wash_volume_flag")


def binance_perps():
    """All TRADING USDT-quoted perpetuals -> [(base_symbol, binance_symbol), ...]."""
    info = _get_json(f"{BINANCE_FAPI}/fapi/v1/exchangeInfo")
    out = []
    if isinstance(info, dict):
        for s in info.get("symbols", []):
            if (s.get("contractType") == "PERPETUAL"
                    and s.get("quoteAsset") == "USDT"
                    and s.get("status") == "TRADING"):
                out.append((s.get("baseAsset"), s.get("symbol")))
    return out


def build(universe_path: str = UNIVERSE) -> dict:
    # Load existing curated entries (keyed by binance_symbol) to preserve enrichment.
    curated = {}
    if os.path.exists(universe_path):
        with open(universe_path, "r", encoding="utf-8") as f:
            old = json.load(f)
        for e in old.get("tokens", []):
            key = e.get("binance_symbol") or e.get("symbol")
            curated[key] = e

    tokens = []
    seen = set()
    for base, bsym in binance_perps():
        if not base or not bsym or bsym in seen:
            continue
        seen.add(bsym)
        entry = {"symbol": base, "binance_symbol": bsym}
        prev = curated.get(bsym)
        if prev:
            for k in _KEEP:
                if prev.get(k) is not None:
                    entry[k] = prev[k]
        tokens.append(entry)

    tokens.sort(key=lambda e: e["symbol"])
    universe = {
        "_comment": "Full Binance USD-M perp universe (auto-built by "
                    "detector.build_universe). Hand-curated enrichment "
                    "(cg_id/defillama_slug/top_holders_pct) is preserved on rebuild.",
        "tokens": tokens,
    }
    with open(universe_path, "w", encoding="utf-8") as f:
        json.dump(universe, f, indent=2)
        f.write("\n")
    return universe


def main() -> int:
    u = build()
    enriched = sum(1 for t in u["tokens"] if any(t.get(k) for k in _KEEP))
    print(f"universe rebuilt: {len(u['tokens'])} perps ({enriched} with curated enrichment)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
