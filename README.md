# MG Terminal — Manipulation Watch

> Auto-updated manipulation-risk watchlist for perp tokens. JSON-first.
> Live at **[mgterminal.com](https://mgterminal.com)**. A MeatGrinder system.

## What this is
An automated scan that flags the **"crime-coin" pattern** in perpetual-futures
tokens — a price driven by perps rather than fundamentals, engineered short
squeezes that bleed traders via funding, supply concentrated in a few wallets,
and wash-traded volume. Each signal is mapped to an
[OnChain Attack Knowledge (OAK)](https://onchainattack.com) technique so a flag
is always explainable, never a black box.

The **JSON dataset is the source of truth** ([`/data.json`](https://mgterminal.com/data.json));
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
Six signals → weighted 0–100 → status. Missing data lowers *confidence* instead
of faking certainty. See [`SOURCES.md`](./SOURCES.md) and
[`ARCHITECTURE.md`](./ARCHITECTURE.md).

| signal | normal | crime-coin | OAK |
|---|---|---|---|
| MC / TVL | 1–4× | 50–120× | T17.001 |
| Funding (short side) | ~0 | −1.5…−2% / 4h | T17.002 |
| Perp OI / float | low | dominant | T17.002 |
| Price / sales | tens | thousands | T17.001 |
| Supply concentration | distributed | >90% one cluster | T3.006 |
| Wash volume | no | yes | T3.002 |

## Run locally
```bash
python3 -m tests.test_calibration   # offline calibration (MYX/RAVE high, majors low)
python3 -m detector.pipeline        # live scan -> data/candidates/index.json
python3 web/build.py                # generate dist/index.html + dist/data.json
```
No dependencies — Python 3.9+ stdlib only.

## Repo map
```
detector/   scoring engine, data sources, pipeline, fixtures
data/       universe.json (inputs) · candidates/ (auto) · confirmed/ (human)
web/        static site generator (MeatGrinder design)
dist/       generated site (do not edit) — deployed to mgterminal.com
tests/      calibration regression
```

## License / data
Heuristic outputs only. Sources: Binance, CoinGecko, DefiLlama (free tiers),
taxonomy by OAK. See `SOURCES.md`.
