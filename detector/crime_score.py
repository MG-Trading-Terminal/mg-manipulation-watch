"""
crime_score — pure, deterministic scoring of "crime-coin" manipulation risk.

This module is the single source of truth for HOW a token is evaluated. It is
intentionally free of any I/O: it takes a `Signals` snapshot (already fetched)
and returns an `Assessment`. That makes the scoring logic unit-testable on
offline fixtures (calibrate on MYX/RAVE vs BTC/ETH/SOL) without touching the
network — the same discipline as the trading core (pure logic, no I/O).

Design rules baked in:
  * The engine NEVER asserts wrongdoing. It can only output `watchlist` or
    `suspected`. The stronger states `likely` / `confirmed` / `cleared` are
    human-gated and live in the data layer, not here.
  * Every signal degrades gracefully: a missing input contributes nothing and
    lowers `confidence` instead of silently defaulting to zero suspicion.
  * Each signal is mapped to a real OAK technique id (onchainattack taxonomy)
    so a flag is always explainable in a shared vocabulary, never a black box.

Reference: thetokendispatch.com/p/crime-coins-cryptos-most-profitable
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# --------------------------------------------------------------------------- #
# Status ladder (mirrors data-layer/site)                                      #
# --------------------------------------------------------------------------- #
# Machine-emittable:
STATUS_WATCHLIST = "watchlist"   # on the radar, not enough to suspect
STATUS_SUSPECTED = "suspected"   # score over threshold, NOT human-verified
# Human-gated only (never returned by this engine), documented for reference:
HUMAN_ONLY_STATUSES = ("likely", "confirmed", "cleared")

# Attribution strength — reuses OAK's vocabulary. The engine is automated and
# unverified, so it can never claim more than a weak inference.
ATTR_AUTO_WEAK = "inferred-weak"
ATTR_NONE = "unattributed"

# A signal must reach this sub-score to be counted as "fired" (and to attach its
# OAK technique to the assessment).
FIRE_THRESHOLD = 0.50
# Final score (0-100) at/above which an auto assessment becomes `suspected`.
SUSPECT_SCORE = 50.0
# Guards against flagging on too little data.
MIN_SIGNALS_FOR_SUSPECT = 2
MIN_CONFIDENCE_FOR_SUSPECT = 0.30


@dataclass
class Signals:
    """Raw, already-fetched inputs for one token. Any field may be None."""

    # valuation / fundamentals
    market_cap_usd: Optional[float] = None
    tvl_usd: Optional[float] = None              # protocol TVL (None for memecoins / L1s)
    fees_annualized_usd: Optional[float] = None  # for price/sales

    # perp microstructure
    funding_rate: Optional[float] = None         # fraction per interval, e.g. -0.02
    funding_interval_hours: Optional[float] = None
    open_interest_usd: Optional[float] = None
    volume_24h_usd: Optional[float] = None

    # supply / on-chain (optional — keyed sources)
    top_holders_pct: Optional[float] = None      # 0..1, fraction held by operator cluster
    wash_volume_flag: Optional[bool] = None       # True if wash-trading detected


# --------------------------------------------------------------------------- #
# Ramps — turn a raw value into a [0,1] sub-score                              #
# --------------------------------------------------------------------------- #
def _clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


def _lin_ramp(x: float, lo: float, hi: float) -> float:
    """Linear ramp: x<=lo -> 0, x>=hi -> 1."""
    if hi <= lo:
        return 0.0
    return _clamp01((x - lo) / (hi - lo))


def _log_ramp(x: float, lo: float, hi: float) -> float:
    """Log ramp for ratios that span orders of magnitude (MC/TVL, P/S)."""
    if x <= 0 or lo <= 0 or hi <= lo:
        return 0.0
    return _clamp01((math.log10(x) - math.log10(lo)) / (math.log10(hi) - math.log10(lo)))


# --------------------------------------------------------------------------- #
# Signal definitions                                                          #
# --------------------------------------------------------------------------- #
@dataclass
class Signal:
    key: str
    weight: float
    oak: List[str]                  # real OAK technique ids this signal evidences
    label: str

    # set at runtime
    sub: Optional[float] = None     # [0,1] or None if input unavailable
    value: Optional[float] = None   # the raw value, for the evidence record


def _mc_tvl(s: Signals) -> Optional[tuple]:
    if s.market_cap_usd is None or s.tvl_usd is None or s.tvl_usd <= 0:
        return None
    ratio = s.market_cap_usd / s.tvl_usd
    # Only EXTREME disconnect counts — L1s/established tokens routinely run 5-20x
    # without being crime. Ramp 10x..200x so only a real blow-out fires (MYX ~120x).
    return _log_ramp(ratio, 10.0, 200.0), ratio


def _ps(s: Signals) -> Optional[tuple]:
    if s.market_cap_usd is None or s.fees_annualized_usd is None or s.fees_annualized_usd <= 0:
        return None
    ps = s.market_cap_usd / s.fees_annualized_usd
    # Many legit tokens have high P/S; only the absurd counts. Ramp 200x..5000x
    # so only a real blow-out fires (MYX ~3500x).
    return _log_ramp(ps, 200.0, 5000.0), ps


def _funding(s: Signals) -> Optional[tuple]:
    if s.funding_rate is None or s.funding_interval_hours is None or s.funding_interval_hours <= 0:
        return None
    daily = s.funding_rate * (24.0 / s.funding_interval_hours)
    # Squeeze mode = crowded shorts BLEEDING via deeply negative funding.
    # Ramp from -0.5%/day to -12%/day (the canonical crime-coin drain).
    neg = -daily
    return _lin_ramp(neg, 0.005, 0.12), daily


def _oi_dominance(s: Signals) -> Optional[tuple]:
    # Perp-driven price: huge OI relative to real float (MC proxy), or to volume.
    # OI/MC is the real measure — ramp 0.10..0.60. The OI/24h-volume FALLBACK
    # (when MC is unknown, e.g. a market-wide sweep) is weak: OI > 24h turnover is
    # normal for most alts, so it must be desensitized (3x..20x) or it floods —
    # in a no-MC sweep, negative FUNDING is the real squeeze discriminator.
    if s.open_interest_usd is not None and s.market_cap_usd and s.market_cap_usd > 0:
        r = s.open_interest_usd / s.market_cap_usd
        return _lin_ramp(r, 0.10, 0.60), r
    # No OI/volume fallback: OI > 24h turnover is normal for alts, so without a
    # real float (MC) it floods. OI is still collected into the base for later
    # OI/MC scoring once MC enrichment is wired. In a no-MC sweep, funding rules.
    return None


def _supply(s: Signals) -> Optional[tuple]:
    if s.top_holders_pct is None:
        return None
    return _lin_ramp(s.top_holders_pct, 0.50, 0.95), s.top_holders_pct


def _wash(s: Signals) -> Optional[tuple]:
    if s.wash_volume_flag is None:
        return None
    return (1.0 if s.wash_volume_flag else 0.0), (1.0 if s.wash_volume_flag else 0.0)


# (key, weight, oak ids, label, extractor). Weights sum to 1.0.
_DEFS = [
    ("mc_tvl", 0.24, ["OAK-T17.001"], "MC / TVL disconnect", _mc_tvl),
    ("funding", 0.22, ["OAK-T17.002"], "Negative-funding short squeeze", _funding),
    ("oi_dominance", 0.18, ["OAK-T17.002"], "Perp OI dominance", _oi_dominance),
    ("ps_ratio", 0.16, ["OAK-T17.001"], "Price / sales blow-out", _ps),
    ("supply_conc", 0.12, ["OAK-T3.006"], "Supply concentration", _supply),
    ("wash_volume", 0.08, ["OAK-T3.002"], "Wash-trade volume", _wash),
]


# --------------------------------------------------------------------------- #
# Evidence-based risk score                                                    #
# --------------------------------------------------------------------------- #
# The live-signal score above only measures an ACTIVE squeeze (funding / OI /
# MC). A coin that has ALREADY rugged — RAVE: pump->dump, -98%, dead liquidity —
# shows nothing on those live signals yet is the highest-risk case of all, so it
# would read score 0 while flagged `suspected`. That is the bug this fixes.
#
# The DISPLAYED score is therefore an EVIDENCE score, built in TWO tiers:
#
#   HARD evidence — a realized manipulation outcome (pump→dump, collapse, death)
#   or a definitive contract scam (honeypot). Low false-positive; this is what
#   justifies a HIGH score and drives the full 0-100 scale.
#
#   SOFT evidence — heuristic contract / structure / mechanics signs. These ALSO
#   fire on perfectly legit tokens (a multisig reads as `owner-control`, staked
#   supply as `holder-concentration`, a thin perp-DEX pool as `thin-liquidity`),
#   so on their OWN they cap at SOFT_CAP — "elevated, watch", never a top score.
#
# Net effect: a coin that already rugged (RAVE) scores high; a blue-chip that
# merely trips heuristic flags (GMX) stays mid. Score and status are consistent:
# a `suspected` coin (gated on hard evidence / honeypot) can never read 0.
_HARD_POINTS = {
    "honeypot": 100,                # can't sell — definitive contract scam
    "pump-dump": 50,                # ran >=3x then crashed >=80%, no recovery — the crime shape (suspects alone)
    "collapsed": 28,                # >=90% peak->trough (needs corroboration to suspect)
    "dead": 18,                     # abandoned, no volume
}
_SOFT_POINTS = {
    # contract red-flags (GoPlus / OAK T1,T3) — heuristic, fire on legit tokens too
    "high-tax": 18,                 # extractive tax — least FP-prone of the contract signs
    "owner-control": 12,
    "holder-concentration": 12,
    "mintable": 10,
    "closed-source": 6,
    # market structure (OAK T2)
    "thin-liquidity": 12,
    "fresh-launch": 10,
    "low-float": 8,
    # live perp mechanics (the original squeeze scorer's signs)
    "squeeze": 14,
    "oi-dominance": 8,
    "mc/tvl-disconnect": 8,
    "ps-disconnect": 6,
}
SOFT_CAP = 45  # heuristic-only evidence tops out here — "elevated", not "confirmed-rug high"
# Evidence score at/above which an automated assessment becomes `suspected`. It
# sits ABOVE SOFT_CAP by design: only HARD evidence (realized rug / honeypot) can
# clear it, so a `suspected` call never rests on heuristic-only flags that also
# fire on legit tokens (a blue-chip with a multisig stays watchlist, capped <50).
SUSPECT_RISK = 50

# Each sign belongs to one evidence group; corroboration across groups raises
# confidence (a lone sign is weak; signs from 3+ groups are strong).
_FLAG_GROUPS = {
    "realized": {"pump-dump", "collapsed", "dead"},
    "contract": {"honeypot", "high-tax", "mintable", "owner-control",
                 "closed-source", "holder-concentration"},
    "structure": {"thin-liquidity", "low-float", "fresh-launch"},
    "mechanics": {"squeeze", "oi-dominance", "mc/tvl-disconnect", "ps-disconnect"},
}


def risk_score(flags) -> int:
    """Evidence-based 0-100 risk score. Hard evidence (realized rug / honeypot)
    drives the full scale; soft heuristic signs alone cap at SOFT_CAP."""
    fl = set(flags or [])
    if "honeypot" in fl:
        return 100
    hard = sum(_HARD_POINTS.get(f, 0) for f in fl)
    soft = sum(_SOFT_POINTS.get(f, 0) for f in fl)
    if hard == 0:
        return min(SOFT_CAP, soft)        # heuristic-only -> elevated at most
    return min(100, hard + soft)          # realized harm present -> full scale


def evidence_confidence(flags) -> float:
    """Corroboration across the independent evidence groups (0-1): signs from 3+
    different groups => full confidence; a single lone sign is weak."""
    fl = set(flags or [])
    groups = sum(1 for g in _FLAG_GROUPS.values() if fl & g)
    return min(1.0, groups / 3.0)


@dataclass
class Assessment:
    token: str
    score: int                       # 0-100
    confidence: float                # 0-1 (weight of available signals)
    status: str                      # watchlist | suspected
    attribution: str                 # inferred-weak | unattributed
    fired_techniques: List[str]      # OAK ids of signals that fired
    breakdown: Dict[str, Optional[float]] = field(default_factory=dict)  # sub-scores
    values: Dict[str, Optional[float]] = field(default_factory=dict)     # raw values
    available: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)

    def to_record(self) -> dict:
        """Machine-readable record for the JSON dataset / site."""
        return {
            "token": self.token,
            "status": self.status,
            "score": self.score,
            "confidence": round(self.confidence, 3),
            "attribution": self.attribution,
            "oak_techniques": self.fired_techniques,
            "signals": {k: (round(v, 3) if v is not None else None)
                        for k, v in self.breakdown.items()},
            "values": {k: v for k, v in self.values.items()},
            "available_signals": self.available,
            "missing_signals": self.missing,
            "reviewer": None,  # null = automated; set by a human on promotion
            "note": "Alleged market-manipulation pattern; automated heuristic, "
                    "not a determination of wrongdoing.",
        }


def score(token: str, s: Signals) -> Assessment:
    """Score one token's manipulation-risk from a fetched signal snapshot."""
    signals: List[Signal] = []
    for key, weight, oak, label, fn in _DEFS:
        sig = Signal(key=key, weight=weight, oak=oak, label=label)
        res = fn(s)
        if res is not None:
            sig.sub, sig.value = res
        signals.append(sig)

    available = [sg for sg in signals if sg.sub is not None]
    avail_weight = sum(sg.weight for sg in available)

    if avail_weight > 0:
        weighted = sum(sg.weight * sg.sub for sg in available) / avail_weight
        final = round(weighted * 100)
    else:
        final = 0

    fired = []
    for sg in available:
        if sg.sub is not None and sg.sub >= FIRE_THRESHOLD:
            for t in sg.oak:
                if t not in fired:
                    fired.append(t)

    confidence = avail_weight  # weights sum to 1.0, so this is already a fraction

    if (len(available) >= MIN_SIGNALS_FOR_SUSPECT
            and confidence >= MIN_CONFIDENCE_FOR_SUSPECT
            and final >= SUSPECT_SCORE):
        status = STATUS_SUSPECTED
        attribution = ATTR_AUTO_WEAK
    else:
        status = STATUS_WATCHLIST
        attribution = ATTR_NONE

    return Assessment(
        token=token,
        score=final,
        confidence=confidence,
        status=status,
        attribution=attribution,
        fired_techniques=fired,
        breakdown={sg.key: sg.sub for sg in signals},
        values={sg.key: sg.value for sg in signals},
        available=[sg.key for sg in available],
        missing=[sg.key for sg in signals if sg.sub is None],
    )
