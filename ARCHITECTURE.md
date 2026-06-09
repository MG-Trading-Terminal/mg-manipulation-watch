# Architecture

## Principle
**JSON is the source of truth. Everything else is derived.** The scorer is a pure
function; fetching is best-effort and isolated; the site is generated; the schedule
is dumb (re-run, re-emit, re-deploy). This makes every layer independently testable
and the whole thing safe to run unattended every 4 hours.

## Data flow
```
                        data/universe.json            (inputs: what to scan)
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │             detector/pipeline.py              │   (orchestration, 4h batch)
        │                                               │
        │   sources.py ──fetch──▶ Signals snapshot      │   ← live, best-effort, no-key
        │      Binance USD-M  (funding, OI, vol)         │     one dead source ≠ dead row
        │      CoinGecko      (market cap)               │
        │      DefiLlama      (TVL, fees)                │
        │                       │                        │
        │   crime_score.py ◀────┘  score(Signals)        │   ← PURE. no I/O. testable.
        │      6 signals → weighted 0-100 → status       │     emits watchlist|suspected only
        └──────────────────────────────────────────────┘
                               │
                               ▼
            data/candidates/index.json   (+ <SYMBOL>.json per token)
                               │   ◀── canonical machine-readable output
              ┌────────────────┴─────────────────┐
              ▼                                   ▼
        web/build.py                       (consumers: bot-trader сверка,
        dist/index.html + data.json          other tooling, API clients)
        (MeatGrinder design)
                               │
                               ▼
        GitHub Action (cron 0 */4 * * *)
          1. run pipeline      → refresh JSON
          2. run calibration   → fail the run if the scorer regressed
          3. commit data/      → versioned history for diffing / сверка
          4. build + deploy    → GitHub Pages → mgterminal.com
```

## The two-tier data model (machine vs human)
| tier | dir | written by | statuses |
|---|---|---|---|
| candidates | `data/candidates/` | the pipeline (auto, every 4h) | `watchlist`, `suspected` |
| confirmed | `data/confirmed/` | a human, by hand (PR) | `likely`, `confirmed`, `cleared` |

The automated job is **incapable** of asserting a verdict — it can only raise
`suspected`. Promotion to a human-reviewed state is a manual edit under
`data/confirmed/` (out of the pipeline's scope). This is the "verify locally, then
publish" gate, enforced structurally.

## Scoring (detector/crime_score.py)
- Each signal maps a raw value → `[0,1]` via a documented ramp (log for ratios,
  linear for rates/fractions).
- Final score = weight-normalized mean over **available** signals × 100.
  `confidence` = sum of available weights (weights sum to 1.0).
- A signal "fires" at sub-score ≥ 0.5 and attaches its OAK technique id.
- `suspected` requires score ≥ 50 **and** ≥ 2 available signals **and**
  confidence ≥ 0.30. Otherwise `watchlist`. Never higher.
- Weights: MC/TVL .24 · funding .22 · OI .18 · P/S .16 · supply .12 · wash .08.

## Why the pipeline is robust unattended
- **No exceptions escape a fetch** — every source returns `None` on failure; the
  scorer treats `None` as "no info" and lowers confidence.
- **Calibration gates the deploy** — if a change makes MYX/RAVE stop scoring high
  or majors start scoring high, the Action fails before publishing.
- **Deterministic + idempotent** — same inputs → same JSON → clean git diffs.
- **No build deps** — stdlib-only Python; nothing to break on a dependency bump.

## Extension points (v2)
- Keyed fetchers for supply concentration (Bubblemaps/Arkham/explorer) and
  wash-trade detection (replace manual `universe.json` fields).
- Unlock/OTC-distribution signal → OAK-T5.006 (vesting-cliff-dump) for the
  distribution stage of the pattern.
- Per-token history series (the per-`SYMBOL`.json files already give git history).
- A small REST/edge function in front of `data.json` if pull volume grows.
