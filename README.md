# MG Terminal — Manipulation Watch

> Auto-updated manipulation-risk watchlist for perp tokens. JSON-first.
> Live at **[manipulation.mgterminal.com](https://manipulation.mgterminal.com)**. A MeatGrinder system.

## What this is
An automated scan that flags the **"crime-coin" pattern** in perpetual-futures
tokens — a price driven by perps rather than fundamentals, engineered short
squeezes that bleed traders via funding, supply concentrated in a few wallets,
and wash-traded volume. Each signal is mapped to an
[OnChain Attack Knowledge (OAK)](https://onchainattack.org) technique so a flag
is always explainable, never a black box.

The **JSON dataset is the source of truth** ([`/data.json`](https://manipulation.mgterminal.com/data.json));
the website is generated from it. The data is designed to be cross-checked
against other systems.

## ⚠️ Disclaimer — read this
This is a **heuristic, not an accusation.** A `suspected` status is an
**unverified, automated** signal — a starting point for your own research, **not a
determination of wrongdoing.** Statuses describe *evidence strength*
(`watchlist → suspected`); human-reviewed states (`likely / confirmed / cleared`)
are gated separately and never assigned by the bot. Nothing here is financial
advice. To request a correction or takedown, open an issue.

## Status ladder
| status | meaning | who sets it |
|---|---|---|
| `watchlist` | on the radar, not enough to suspect | automated |
| `suspected` | score over threshold, **unverified** | automated |
| `likely` | several independent signals + a human glance | human |
| `confirmed` | fully reviewed, evidence bundled | human |
| `cleared` | reviewed, suspicion withdrawn (false positive) | human |

## How the score works
Every token gets a **0–100 evidence score** built from the manipulation signs that
actually fired, in two tiers:

- **Hard evidence** — a *realized* rug (pump→dump, ≥90% collapse, death) or a
  definitive contract scam (honeypot). Low false-positive; drives the full scale.
- **Soft evidence** — heuristic contract / structure / market signs. These also
  fire on legit tokens (a multisig reads as `owner-control`, staked supply as
  `holder-concentration`), so on their own they **cap at 45** — "elevated", never high.

**Status derives from the score**: `suspected` ⟺ honeypot or score ≥ 50. Because
soft-only evidence caps below 50, a `suspected` call always rests on hard evidence —
a blue-chip that merely trips heuristic flags stays `watchlist`. See
[`ARCHITECTURE.md`](./ARCHITECTURE.md) and [`SOURCES.md`](./SOURCES.md).

| sign | tier | OAK |
|---|---|---|
| pump-and-dump (ran ≥3×, crashed ≥80%, no recovery) | hard | T3.003 |
| collapsed ≥90% from ATH · dead (no volume) | hard | T3.003 |
| honeypot / can't-sell | hard | T1.006 |
| owner-control · mintable · high-tax · holder-concentration | soft | T1 · T3.006 |
| thin liquidity · fresh launch · low float | soft | T2 |
| negative-funding squeeze · OI dominance · MC/TVL · P/S | soft | T17 |

## Run locally
```bash
python3 -m tests.test_calibration   # offline calibration (rugs high, blue-chips capped)
python3 -m detector.collect         # live multi-venue scan -> data/candidates/index.json
npm install && npm run build        # build the site (bakes JSON -> dist/)
```
The scan is Python 3.9+ stdlib-only; the site needs Node 20+. A free CoinGecko
Demo key in `.env` (`COINGECKO_API_KEY=…`) lifts the rate limit for richer profiles.

### Run it locally (no repo / no cloud)
The system accumulates an append-only base under `data/history/` so you can watch
a token's score climb into a squeeze over time. Pick one:
```bash
bash scripts/scan-once.sh     # one cycle (scan + history + rebuild site)
bash scripts/run-loop.sh      # foreground loop, every 4h
bash scripts/install-agent.sh # unattended macOS agent, every 4h (uninstall-agent.sh to stop)
bash scripts/serve.sh         # view at http://localhost:8787
```

## Repo map
```
detector/   scoring engine + data adapters (collect, venues, enrich, goplus, dexscreener)
data/       universe.json (inputs) · candidates/ (auto) · confirmed/ (human)
src/        Vite + React + TS frontend (App, components, generated data)
scripts/    build-site-data.mjs (JSON→generated.ts), copy-static.mjs, local runners
dist/       built site (generated) — deployed to manipulation.mgterminal.com
tests/      calibration regression
```

## Deploy (one-time setup)
Updates **and** production are fully automated by
[`.github/workflows/crime-scan.yml`](./.github/workflows/crime-scan.yml): every 4
hours it scans, gates on the calibration test, commits the history summary, builds
the site, and deploys to GitHub Pages. The enrichment cache persists across runs
(via `actions/cache`) so coverage accumulates. To go live, once:

1. **Push** — `git remote add origin git@github.com:MG-Trading-Terminal/mg-manipulation-watch.git && git push -u origin main`
2. **Add the API key secret** — `gh secret set COINGECKO_API_KEY` (or repo *Settings → Secrets → Actions*) — free [CoinGecko Demo](https://www.coingecko.com/en/api) key; the scan still runs without it, just rate-limited.
3. **Enable Pages** — repo *Settings → Pages → Source = **GitHub Actions***.
4. **Custom domain** — it's a subdomain, so add **one CNAME DNS record**: `manipulation` → `mg-trading-terminal.github.io`. The build already ships `dist/CNAME` (`manipulation.mgterminal.com`).
5. **Kick it** — *Actions → crime-scan → Run workflow* (or wait for the cron).

After that there is nothing manual: the job is the update system, Pages is production.

## Public API
The watchlist is **open data** — one JSON document, no key, no auth, refreshed every
4 hours: **[manipulation.mgterminal.com/data.json](https://manipulation.mgterminal.com/data.json)**. Structure,
fields, sign→OAK mapping and fetch examples (curl/Python/JS) are in **[API.md](./API.md)**.

```bash
curl -s https://manipulation.mgterminal.com/data.json \
  | jq '.by_token[] | select((.flags|length) >= 2) | {symbol, flags}'
```

## License
- Code: **MIT** — [`LICENSE-code`](./LICENSE-code)
- Data: **CC-BY-4.0** (attribute "MG Terminal") — [`LICENSE-data`](./LICENSE-data)

Heuristic outputs only; not financial advice. Sources: 6 perp venues + CoinGecko +
DefiLlama + GoPlus + DexScreener; taxonomy by [OAK](https://onchainattack.org). See `SOURCES.md`.
