# MG Terminal — Crime-Coin Manipulation Watch

## What
An auto-updated, JSON-first **manipulation-risk watchlist** for perpetual-futures
tokens. A scoring engine flags the "crime-coin" pattern (fundamental disconnect,
perp-driven short-squeeze, concentrated supply, wash volume), every flag maps to
an [OAK](https://onchainattack.com) technique, and a static site is generated
from the data. Ships at **mgterminal.com** under the **MeatGrinder** brand.

This is a sibling data source to the `bot-trader-2-0` system — the JSON is meant
for cross-checking ("сверка") against the trading core's own reads.

## The one rule that overrides everything: NO accusations
The engine emits **only** `watchlist` or `suspected`. `suspected` is an
*unverified automated heuristic*, never a determination of wrongdoing.
- Stronger states (`likely`, `confirmed`, `cleared`) are **human-gated** and live
  under `data/confirmed/` — the pipeline must never write them.
- Public copy uses evidence-strength language + a disclaimer, never "scam/criminal".
- Attribution caps at `inferred-weak` for anything automated (OAK vocabulary).
If you touch the scorer or the site, preserve this. It is legal protection, and
it is honest (the score is noisy).

## Architecture (see ARCHITECTURE.md)
```
data/universe.json ─▶ detector/pipeline.py
                        ├─ sources.py   (live fetch: Binance, CoinGecko, DefiLlama)
                        └─ crime_score.py (PURE scoring — no I/O, the source of truth)
                              ▼
                  data/candidates/index.json   ← JSON is the canonical output
                              ▼
   scripts/build-site-data.mjs ─▶ src/data/generated.ts (baked, like OAK)
                              ▼
   Vite + React + TS  ─(npm run build)─▶  dist/ (index.html + hashed assets + data.json)
                              ▼
                  GitHub Action (every 4h) ─▶ commit data, deploy Pages → mgterminal.com
```

## Frontend = Vite + React + TypeScript (same stack as OAK — NOT Python-generated HTML)
Python emits ONLY JSON. The site is a real Vite/React/TS app:
- `index.html` + `src/main.tsx` + `src/App.tsx` + `src/components/` + `src/styles.css`.
- `src/types.ts` — typed `data` (from generated.ts). `src/lib.ts` — flag/OAK constants + helpers.
- `scripts/build-site-data.mjs` — bakes `data/candidates/index.json` → `src/data/generated.ts`
  (`export const siteData`), imported at build time (OAK's embed pattern; generated.ts gitignored).
- `scripts/copy-static.mjs` — CNAME + a per-token `data.json` (public API) into dist/.
- Build: `npm run build` = `site:data && tsc --noEmit && vite build && copy-static`.
- **Do not reintroduce Python-side HTML templating.** UI lives in src/ (tsx + css).

## Layout
- `detector/crime_score.py` — pure scorer. **All scoring logic goes here**, nowhere else.
- `detector/collect.py` — PRIMARY 4h sweep: venues → enrich → GoPlus/DexScreener → per-token JSON.
- `detector/{venues,enrich,goplus,dexscreener,sources}.py` — data adapters (best-effort).
- `detector/fixtures.py` + `tests/test_calibration.py` — offline calibration (MYX/RAVE high, majors low).
- `src/` — the React app. `data/universe.json` — scan universe. `data/confirmed/` — human-gated tier.

## Commands
```bash
python3 -m tests.test_calibration   # MUST pass before any scorer change
python3 -m detector.collect         # PRIMARY: market-wide multi-venue sweep -> index.json + snapshot
python3 -m detector.build_universe  # rebuild data/universe.json from Binance perps
npm run build                       # site:data -> tsc -> vite build -> dist/  (the site)
npm run dev                         # local Vite dev server
python3 -m detector.scan SOL        # score one token from the universe, live
```

## How a token is classified — OAK-grounded sign flags
`detector.collect` sweeps ~3.8k perp markets (6 venues), enriches each, and tags it
with **sign flags**, every flag mapped to an OAK technique (see SOURCES.md table):
- **mechanics** (auto-scored): `squeeze` (neg funding, T17.002), `oi-dominance`.
- **contract** (GoPlus, OAK T1/T3): `honeypot`, `high-tax`, `mintable`,
  `owner-control`, `holder-concentration`, `closed-source`.
- **fundamental** (CONTEXT only — fuzzy ratios FP on legit L1s, so NOT auto-scored):
  `mc/tvl-disconnect`, `ps-disconnect`, `low-float`.

Status: `honeypot` → `suspected` (definitive scam contract). Else `suspected` =
squeeze mechanics score ≥ 50. `multi_sign` = ≥2 flags ("имеет признаки"). The
human-gated `confirmed/` tier is the only place "scam"/"likely"/"cleared" is asserted.

**Hard FP-discipline (learned over 4 iterations):** MC/TVL & P/S describe half the
market (every L1/governance token) — they must NEVER auto-condemn. They are shown
as context flags only. Reliable auto signals = squeeze (funding) + GoPlus contract
facts (honeypot/mint/tax/holders). MEXC OI is omitted (holdVol = contracts, not USD).

## Enrichment + contract pass
- `detector.enrich` — bulk MC/TVL/fees/FDV maps + CoinGecko `coins/list` contract
  platforms (cached `data/enrich/maps.json`). Run after universe changes.
- `detector.goplus` — per-address contract security, cached `data/enrich/goplus.json`
  (GoPlus batch is unreliable; per-address + cache is the path). 4h runs only fetch
  NEW contracts (budget `max_fetch`). EVM only in v1; Solana tail = v2.
- `detector.pipeline` — curated deep scan where `mc/tvl`/`ps` ARE auto-scored
  (hand-verified `defillama_slug` only). Per-symbol history in `data/history/`.

## Local operation (no repo / no cloud — the current mode)
The system runs fully locally and accumulates an append-only base under
`data/history/<SYMBOL>.jsonl` (one line per token per scan). Three ways to run:
```bash
bash scripts/scan-once.sh           # one cycle: scan + history + rebuild dist
bash scripts/run-loop.sh            # foreground 4h loop (leave in a terminal/tmux)
bash scripts/install-agent.sh       # unattended launchd agent, every 4h (macOS)
bash scripts/serve.sh               # view dist/ at http://localhost:8787
```
`install-agent.sh` installs a persistent LaunchAgent — run it yourself when ready
(`bash scripts/uninstall-agent.sh` to stop; the base is left intact). Deploy/repo
are deferred until the base is built. Logs: `data/logs/scan.log` (gitignored);
`data/history/` is the base and IS tracked.

## Design system (MeatGrinder / MG Terminal)
Dark only. `--bg-0:#050505`, accent **MG green `#3ee07f`** (the ONLY accent;
red/amber = state). Type: *Instrument Serif* display, *Geist* sans UI, *Geist Mono*
numerics/tickers. Tokens mirror the iOS app. Reference bundle: `_design-ref/`
(do not ship it; it's the Claude Design handoff). Numbers are always mono+tabular.

## Working principles (inherited from bot-trader)
- **Single source of truth**: scoring lives only in `crime_score.py`. No "simplified"
  copies. One bug fixed in one place.
- **Calibrate, don't guess**: change a threshold → re-run the calibration test and
  prove MYX/RAVE stay high and majors stay low. Add a fixture before trusting a tweak.
- **Graceful degradation over false confidence**: missing data lowers `confidence`,
  it never invents suspicion.
- `dist/` is generated — never hand-edit it.

## Status / TODO
v0.1 shipped: engine + free sources + pipeline + JSON + generated site + 4h Action.
Open: keyed supply-concentration + wash-trade fetchers (currently manual in
universe); CoinGecko pacing/key (rapid calls rate-limit → confidence dips);
unlock/OTC signal (OAK-T5.006) for the distribution stage; human `confirmed/` flow.
