"""
Offline calibration snapshots.

These are hand-entered, source-cited approximate snapshots used to calibrate and
regression-test the pure scorer WITHOUT the network. They are deliberately
honest: where a value is genuinely unknown for a token, it is left as None so the
graceful-degradation path is exercised (e.g. RAVE has no protocol TVL).

Known crime-coin examples (should score HIGH):
  - MYX  : Sep-2025, MC ~$3.35B vs TVL ~$28M (~120x), P/S ~3500x, funding
           ~-2%/4h, >90% operator supply, documented wash trades.
  - RAVE : thin-book perp squeeze, OI ~ float, ~-1.5%/4h funding, concentrated.

Controls (should score LOW):
  - BTC/ETH/SOL : majors, normal funding, low OI/MC, distributed supply.
  - AAVE        : healthy DeFi protocol with real TVL (low MC/TVL) — proves the
                  MC/TVL signal does not false-positive on legit protocols.
"""
from .crime_score import Signals

FIXTURES = {
    # ---- known crime-coin patterns (HIGH) ----
    "MYX": Signals(
        market_cap_usd=3.35e9,
        tvl_usd=28e6,
        fees_annualized_usd=9.57e5,      # -> P/S ~3500x
        funding_rate=-0.02,
        funding_interval_hours=4.0,      # -> ~-12%/day drain
        open_interest_usd=None,          # unknown — left out honestly
        top_holders_pct=0.92,
        wash_volume_flag=True,
    ),
    "RAVE": Signals(
        market_cap_usd=1.2e8,
        tvl_usd=None,                    # no real protocol -> MC/TVL n/a
        fees_annualized_usd=None,        # -> P/S n/a
        funding_rate=-0.015,
        funding_interval_hours=4.0,      # -> ~-9%/day
        open_interest_usd=9.0e7,         # OI ~ float
        top_holders_pct=0.88,
        wash_volume_flag=None,
    ),

    # ---- majors (LOW) ----
    "BTC": Signals(
        market_cap_usd=1.25e12,
        tvl_usd=None,
        funding_rate=0.00001448,
        funding_interval_hours=8.0,
        open_interest_usd=3.0e10,
        top_holders_pct=0.11,
        wash_volume_flag=False,
    ),
    "ETH": Signals(
        market_cap_usd=4.0e11,
        tvl_usd=None,
        funding_rate=0.00005,
        funding_interval_hours=8.0,
        open_interest_usd=1.2e10,
        top_holders_pct=0.09,
        wash_volume_flag=False,
    ),
    "SOL": Signals(
        market_cap_usd=9.0e10,
        tvl_usd=None,
        funding_rate=0.00003,
        funding_interval_hours=8.0,
        open_interest_usd=4.0e9,
        top_holders_pct=0.15,
        wash_volume_flag=False,
    ),

    # ---- healthy DeFi protocol with real TVL (LOW; MC/TVL sanity) ----
    "AAVE": Signals(
        market_cap_usd=1.5e9,
        tvl_usd=2.0e10,                  # ~$20B TVL -> MC/TVL ~0.075
        fees_annualized_usd=1.0e8,       # -> P/S ~15x
        funding_rate=0.00002,
        funding_interval_hours=8.0,
        open_interest_usd=2.0e8,
        top_holders_pct=0.30,
        wash_volume_flag=False,
    ),
}
