# Public API

The watchlist is **open data** — anyone can fetch it, no key, no auth.

## Endpoints

| endpoint | what | stability |
|---|---|---|
| `https://manipulation.mgterminal.com/v1/data.json` | full per-token watchlist | **stable — pin this** |
| `https://manipulation.mgterminal.com/v1/token/<SYMBOL>.json` | one token's record | stable |
| `https://manipulation.mgterminal.com/data.json` | latest (alias of current version) | may change shape |

**Pin `/v1/` for anything automated.** `v1` only ever changes additively (new
fields), so your integration won't break. A breaking change ships under a new path
(`/v2/`); the old version keeps serving. Every payload carries `api_version` and a
`schema` string you can assert on.

- **Open & free.** No API key, no rate limit, no auth.
- **Cadence.** Regenerated automatically every **4 hours** (GitHub Action). Check
  `generated_at` for the snapshot time.
- **Licence.** Data: CC-BY-4.0 (attribute "MG Terminal"). Code: MIT. See
  `LICENSE-data` / `LICENSE-code`.
- **Not financial advice.** Heuristic signals; `suspected` is an *unverified*
  machine signal, never a determination of wrongdoing. See the disclaimer in the
  payload and `README.md`.
- **CORS.** Served as a static file from GitHub Pages. Server-side fetch
  (curl / Python / Node) works everywhere; for cross-origin *browser* fetch, proxy
  it or copy the file if your host doesn't allow it.

## Top-level structure

```jsonc
{
  "schema": "mgterminal.crime-coins/v0.5-bytoken", // bump on breaking changes
  "disclaimer": "…",
  "generated_at": "2026-06-09T09:16:34+00:00",     // ISO-8601 UTC
  "venues":     { "binance": 741, "bybit": 582, … },// markets scanned per venue
  "count":         3802,   // total perp markets scanned
  "token_count":   1219,   // unique tokens (the list length)
  "enriched":      2695,   // tokens with a CoinGecko market-cap match
  "contract_checked": 235, // tokens with GoPlus contract data
  "dex_checked":   391,    // tokens with DexScreener market data
  "contract_scam":   0,    // honeypot/can't-sell contracts found
  "suspected_tokens": 1,   // tokens auto-flagged `suspected`
  "multi_sign":    175,    // tokens carrying >=2 signs
  "flag_counts":   { "thin-liquidity": 199, "holder-concentration": 135, … },
  "by_token":      [ Token, … ]   // one entry per token, ranked by sign count then score
}
```

## `Token` object

| field | type | meaning |
|---|---|---|
| `symbol` | string | base ticker (e.g. `MYX`) |
| `venues` | string[] | perp venues it trades on |
| `score` | int 0–100 | squeeze-mechanics score (funding + OI/MC) |
| `status` | string | `watchlist` \| `suspected` (machine) — `likely`/`confirmed`/`cleared` are human-only |
| `flags` | string[] | sign flags present (see vocabulary) |
| `oak_techniques` | string[] | OAK technique ids the signs map to |
| `context` | object | supporting numbers (below) |
| `evidence` | {label,url}[] | external links (Coinglass, …) |

### `context` fields (all optional)

`market_cap_usd`, `tvl_usd`, `fees_annualized_usd`, `fdv_usd`, `mc_tvl`, `ps`,
`float` (circulating/FDV), `liq_usd`, `liq_to_fdv`, `pair_age_days`,
`top_holder_control` (0–1), `holder_count`, `sell_tax`, `buy_tax`, `chain`,
`contract`.

## Sign flags → OAK technique

| flag | meaning | OAK |
|---|---|---|
| `squeeze` | deeply negative funding (shorts bleeding) | T17.002 |
| `oi-dominance` | perp OI large vs float | T17.002 |
| `thin-liquidity` | DEX pool ≪ FDV | T2 |
| `fresh-launch` | pair < 30d old at material FDV | T2 |
| `honeypot` | can't-sell / sell-tax ≥ 99% | T1.006 |
| `high-tax` | extractive sell tax ≥ 10% | T1.001/005 |
| `mintable` | supply can be minted | T1.003 |
| `owner-control` | pausable / hidden-owner / balance-rewrite | T1.004 |
| `holder-concentration` | top non-LP holders ≥ 70% (or < 50 holders) | T3.006 |
| `closed-source` | unverified contract | — |
| `mc/tvl-disconnect` | MC ≫ TVL (context only) | T17.001 |
| `ps-disconnect` | MC ≫ revenue (context only) | T17.001 |
| `low-float` | circulating < 30% of FDV | T3 |

`honeypot` forces `suspected`. `mc/tvl`/`ps`/`low-float` are *context* — they never
auto-condemn (they appear on plenty of legit L1s). See `SOURCES.md`.

## Status ladder

`watchlist` → `suspected` (machine) · `likely` / `confirmed` / `cleared` (human-gated, `data/confirmed/`).

## Examples

```bash
# All suspected tokens, with their signs (pin /v1/)
curl -s https://manipulation.mgterminal.com/v1/data.json \
  | jq '.by_token[] | select(.status=="suspected") | {symbol, score, flags}'

# Tokens carrying >=3 signs
curl -s https://manipulation.mgterminal.com/v1/data.json \
  | jq '.by_token[] | select((.flags|length) >= 3) | {symbol, flags}'

# One token (profile + signs + context)
curl -s https://manipulation.mgterminal.com/v1/token/MYX.json | jq '.token | {status, flags, profile}'
```

```python
import urllib.request, json
d = json.load(urllib.request.urlopen("https://manipulation.mgterminal.com/v1/data.json"))
assert d["api_version"] == 1                      # pin the contract
multi = [t for t in d["by_token"] if len(t["flags"]) >= 2]
print(d["generated_at"], "·", len(multi), "multi-sign tokens")
flags = {t["symbol"]: t["flags"] for t in d["by_token"]}  # cross-check your own read
print(flags.get("MYX"))
```

```js
const d = await (await fetch("https://manipulation.mgterminal.com/v1/data.json")).json();
const honeypots = d.by_token.filter((t) => t.flags.includes("honeypot"));
```

## Versioning policy

- **Path = major version.** `/v1/…` is stable. Only additive changes (new fields)
  land in v1 — existing fields and types never change or disappear, so a pinned
  integration keeps working. A breaking change ships at `/v2/…`; `/v1/` keeps
  serving from the last compatible build.
- **`api_version`** (integer) is in every payload — assert on it.
- **`schema`** (`mgterminal.crime-coins/<ver>`) tracks the internal shape for finer
  pinning. `/data.json` is an unversioned "latest" alias — convenient for humans,
  **don't** depend on it from code; use `/v1/`.
