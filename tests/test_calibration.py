"""
Calibration / regression test for the pure scorer — runs offline on fixtures.

Run:  python3 -m tests.test_calibration   (from repo root)
Exits non-zero on any failure. Also prints a readable table.

Calibration contract:
  * Known crime-coin patterns (MYX, RAVE) -> HIGH score, status `suspected`.
  * Majors + healthy DeFi (BTC, ETH, SOL, AAVE) -> LOW score, status `watchlist`.
"""
import sys

from detector.crime_score import score, STATUS_SUSPECTED, STATUS_WATCHLIST
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
