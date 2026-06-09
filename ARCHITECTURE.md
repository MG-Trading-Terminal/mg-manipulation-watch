# Architecture

## Principle
**JSON is the source of truth. Everything else is derived.** The scorer is a pure
function; fetching is best-effort and isolated; the site is generated; the schedule
is dumb (re-run, re-emit, re-deploy). This makes every layer independently testable
and the whole thing safe to run unattended every 4 hours.

## Data flow
```
   6 perp venues  +  data/{blacklist,mappings}.json  +  data/confirmed/
   (Binance/Bybit/Bitget/Gate/MEXC/Hyperliquid)
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │              detector/collect.py              │   (primary market-wide sweep, 4h)
        │                                               │   blacklist drops tradfi up front
        │   venues.py    ──▶ funding / OI / volume       │   ← bulk, one call per venue
        │   enrich.py    ──▶ MC / TVL / price / dumps     │   ← CoinGecko + DefiLlama (cached)
        │   goplus.py    ──▶ contract security (EVM)      │   ← honeypot / mint / owner / holders
        │   dexscreener  ──▶ DEX liquidity / pair age     │     one dead source ≠ dead row
        │                       │                        │
        │   crime_score.py ◀────┘  risk_score(flags)      │   ← PURE. no I/O. testable.
        │      evidence score 0-100 → status             │     hard (realized rug / honeypot)
        │      soft heuristic signs cap at 45            │     drives scale; suspected ⟺ ≥50
        └──────────────────────────────────────────────┘
                               │
                               ▼
            data/candidates/index.json   (+ /v1/token/<SYMBOL>.json)
                               │   ◀── canonical machine-readable output
              ┌────────────────┴─────────────────┐
              ▼                                   ▼
        npm run build                       (consumers: bot-trader сверка,
          build-site-data.mjs → generated.ts   other tooling, API clients)
          vite build + copy-static.mjs
            → dist/ (+ CNAME, /data.json, /v1/…)
                               │
                               ▼
        GitHub Action (cron 0 */4 * * *) — .github/workflows/crime-scan.yml
          1. restore enrich cache → coverage accumulates across runs
          2. calibration gate     → fail the run if the scorer regressed
          3. run collect          → refresh JSON
          4. build                → bake JSON + render dist/
          5. commit data/history  → versioned summary for diffing / сверка
          6. deploy-pages         → GitHub Pages → manipulation.mgterminal.com
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
