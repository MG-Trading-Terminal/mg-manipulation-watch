"""
Calibration / regression test for the pure scorer — runs offline on fixtures.

Run:  python3 -m tests.test_calibration   (from repo root)
Exits non-zero on any failure. Also prints a readable table.

Calibration contract:
  * Known crime-coin patterns (MYX, RAVE) -> HIGH score, status `suspected`.
  * Majors + healthy DeFi (BTC, ETH, SOL, AAVE) -> LOW score, status `watchlist`.
"""
import sys

from detector.crime_score import (
    score, risk_score, SUSPECT_RISK, SOFT_CAP,
    STATUS_SUSPECTED, STATUS_WATCHLIST,
)
from detector.fixtures import FIXTURES

# (token, min_score, max_score, expected_status)
EXPECT = [
    ("MYX", 70, 100, STATUS_SUSPECTED),
    ("RAVE", 60, 100, STATUS_SUSPECTED),
    ("BTC", 0, 35, STATUS_WATCHLIST),
    ("ETH", 0, 35, STATUS_WATCHLIST),
    ("SOL", 0, 35, STATUS_WATCHLIST),
    ("AAVE", 0, 35, STATUS_WATCHLIST),
]

# Evidence-score contract (the DISPLAYED score, driven by the signs that fired).
# (case, flags, min_score, max_score, expected_status)
#   * Realized rugs -> HIGH, suspected (and NEVER 0 — the bug this guards).
#   * A pure collapse / dead coin -> below SUSPECT_RISK (a bear market, not a rug).
#   * Legit tokens that merely trip heuristic contract flags (a multisig reads as
#     owner-control, staked supply as holder-concentration) -> capped at SOFT_CAP,
#     watchlist — never condemned by soft evidence alone.
EVIDENCE = [
    ("realized rug (RAVE-shape)", ["pump-dump", "collapsed", "thin-liquidity", "low-float"], 80, 100, STATUS_SUSPECTED),
    ("honeypot (definitive)",     ["honeypot", "low-float"],                                100, 100, STATUS_SUSPECTED),
    ("pump-dump alone",           ["pump-dump"],                                             50,  55, STATUS_SUSPECTED),
    ("plain collapse (bear)",     ["collapsed"],                                              0,  49, STATUS_WATCHLIST),
    ("collapsed + dead husk",     ["collapsed", "dead"],                                      0,  49, STATUS_WATCHLIST),
    ("blue-chip heuristic FPs",   ["mintable", "owner-control", "holder-concentration"],      0, SOFT_CAP, STATUS_WATCHLIST),
    ("soft-flag pile (capped)",   ["mintable", "owner-control", "holder-concentration",
                                   "thin-liquidity", "low-float", "oi-dominance"],            0, SOFT_CAP, STATUS_WATCHLIST),
    ("clean (no signs)",          [],                                                         0,   0, STATUS_WATCHLIST),
]


def _evidence_status(flags) -> str:
    sc = risk_score(flags)
    return STATUS_SUSPECTED if ("honeypot" in flags or sc >= SUSPECT_RISK) else STATUS_WATCHLIST


def main() -> int:
    failures = []
    print(f"{'TOKEN':<6}{'SCORE':>6}{'CONF':>7}  {'STATUS':<11}{'OAK':<28}{'VERDICT'}")
    print("-" * 78)
    for token, lo, hi, want_status in EXPECT:
        a = score(token, FIXTURES[token])
        ok = (lo <= a.score <= hi) and (a.status == want_status)
        verdict = "PASS" if ok else "FAIL"
        if not ok:
            failures.append(
                f"{token}: score={a.score} (want {lo}-{hi}), "
                f"status={a.status} (want {want_status})"
            )
        oak = ",".join(t.replace("OAK-", "") for t in a.fired_techniques) or "-"
        print(f"{token:<6}{a.score:>6}{a.confidence:>7.2f}  "
              f"{a.status:<11}{oak:<28}{verdict}")

    print("\nEVIDENCE SCORE (displayed score from signs)")
    print(f"{'CASE':<28}{'SCORE':>6}  {'STATUS':<11}{'VERDICT'}")
    print("-" * 78)
    for case, flags, lo, hi, want_status in EVIDENCE:
        sc = risk_score(flags)
        st = _evidence_status(flags)
        ok = (lo <= sc <= hi) and (st == want_status)
        verdict = "PASS" if ok else "FAIL"
        if not ok:
            failures.append(
                f"{case}: score={sc} (want {lo}-{hi}), status={st} (want {want_status})"
            )
        print(f"{case:<28}{sc:>6}  {st:<11}{verdict}")

    print("-" * 78)
    if failures:
        print("\nFAILURES:")
        for f in failures:
            print("  " + f)
        return 1
    print("All calibration checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
