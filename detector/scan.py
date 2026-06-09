"""
scan — score a single token from the universe, live. A quick manual probe.

Usage:
  python3 -m detector.scan SOL
  python3 -m detector.scan MYX --offline   # score from the calibration fixture
"""
from __future__ import annotations

import json
import os
import sys

from .crime_score import score
from .sources import fetch_signals

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNIVERSE = os.path.join(ROOT, "data", "universe.json")


def _entry(symbol: str):
    with open(UNIVERSE, "r", encoding="utf-8") as f:
        for e in json.load(f).get("tokens", []):
            if e.get("symbol", "").upper() == symbol.upper():
                return e
    return None


def main(argv) -> int:
    if not argv:
        print("usage: python3 -m detector.scan <SYMBOL> [--offline]")
        return 2
    symbol = argv[0].upper()
    offline = "--offline" in argv

    if offline:
        from .fixtures import FIXTURES
        if symbol not in FIXTURES:
            print(f"no fixture for {symbol}; have: {', '.join(FIXTURES)}")
            return 2
        signals = FIXTURES[symbol]
    else:
        entry = _entry(symbol)
        if entry is None:
            print(f"{symbol} not in universe; add it to data/universe.json")
            return 2
        signals = fetch_signals(entry)

    a = score(symbol, signals)
    print(f"\n  {symbol}   score {a.score}   conf {a.confidence:.2f}   "
          f"[{a.status}]   attr={a.attribution}")
    print("  " + "-" * 48)
    for k in ["mc_tvl", "funding", "oi_dominance", "ps_ratio", "supply_conc", "wash_volume"]:
        sub = a.breakdown.get(k)
        raw = a.values.get(k)
        bar = "" if sub is None else ("█" * round(sub * 16)).ljust(16, "·")
        sub_s = " n/a" if sub is None else f"{sub:4.2f}"
        raw_s = "" if raw is None else f"  ({raw:.4g})"
        print(f"  {k:<13} {sub_s}  {bar}{raw_s}")
    print("  " + "-" * 48)
    if a.fired_techniques:
        print("  OAK: " + ", ".join(a.fired_techniques))
    print(json.dumps(a.to_record(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
