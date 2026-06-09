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
                  data/candidates/index.json  (+ per-token json)   ← JSON is canonical
                              ▼
                        web/build.py  ─▶  dist/index.html + dist/data.json  (MG design)
                              ▼
                  GitHub Action (every 4h) ─▶ commit data, deploy Pages → mgterminal.com
```

## Layout
- `detector/crime_score.py` — pure scorer. **All scoring logic goes here**, nowhere else.
- `detector/sources.py` — best-effort free fetchers; one dead source must never kill a row.
- `detector/pipeline.py` — the 4h batch: universe → fetch → score → JSON.
- `detector/fixtures.py` — offline calibration snapshots (MYX/RAVE high, majors low).
- `web/build.py` — static site generator (MeatGrinder design language).
- `data/universe.json` — tokens to scan (add entries here).
- `data/candidates/` — machine output (auto). `data/confirmed/` — human-gated (manual).
- `tests/test_calibration.py` — regression test for the scorer.

## Commands
```bash
python3 -m tests.test_calibration   # MUST pass before any scorer change
python3 -m detector.collect         # PRIMARY: market-wide multi-venue sweep -> index.json + snapshot
python3 -m detector.build_universe  # rebuild data/universe.json from Binance perps
python3 -m detector.pipeline        # curated deep scan (Binance + cg/defillama enrichment)
python3 web/build.py                # regenerate dist/ from the JSON
python3 -m detector.scan SOL        # score one token from the universe, live
```

## Two scanners (same engine)
- **`detector.collect` (primary, broad):** one bulk call per venue
  (Binance/Bybit/Bitget/Gate/MEXC/Hyperliquid) → ~3.8k perp markets, fast. Only
  funding + OI available market-wide, and OI floods without a real float, so the
  **breadth ranking is funding-driven** (deeply negative funding = the squeeze
  tell). Everything stays `watchlist` — earning `suspected` needs enrichment.
  Writes `data/candidates/index.json` + immutable `data/snapshots/<ts>.json` (base).
- **`detector.pipeline` (curated, deep):** Binance + CoinGecko/DefiLlama enrichment
  (MC/TVL, P/S) for the handful in `universe.json` that have `cg_id`/`defillama_slug`
  → 2+ signals → can reach `suspected`. Per-symbol history in `data/history/`.
- MEXC OI is omitted (its `holdVol` is in contracts, not USD — it inflated
  BTC/stocks to max). OI is still collected for later OI/MC scoring.

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
