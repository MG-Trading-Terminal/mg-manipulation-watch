# Data sources — where & how we evaluate

Each row of the watchlist is assembled from independent public feeds. The table
below is the catalog: what each source provides, which signal it feeds, whether it
needs a key, and its known limits. **All sources are free, no-key.**

## Perp venues — the market-wide sweep (`detector.collect`)
Crime coins are not mostly on Binance; the long tail lives on the smaller venues.
Each venue exposes ONE bulk endpoint with funding + OI + volume for every perp, so
the whole market (~3.8k markets) is one call per venue.

| venue | bulk endpoint | perps | OI quality |
|---|---|---|---|
| Binance USD-M | `fapi/v1/premiumIndex` + `ticker/24hr` | ~740 | no bulk OI (funding+vol only here) |
| Bybit | `v5/market/tickers?category=linear` | ~580 | exact USD (`openInterestValue`) |
| Bitget | `api/v2/mix/market/tickers` | ~620 | exact (`holdingAmount`×mark) |
| Gate | `api/v4/futures/usdt/tickers` | ~730 | exact (`total_size`×mult×mark) |
| MEXC | `api/v1/contract/ticker` | ~890 | **omitted** — `holdVol` is contracts, not USD |
| Hyperliquid | `info {metaAndAssetCtxs}` | ~230 | exact (`openInterest`×mark); funding is **hourly** |

**Breadth ranking is funding-driven.** Market-wide, only funding + OI are
available, and OI/volume floods (OI > 24h turnover is normal for alts), so OI is
collected but NOT scored without a real float (MC). Deeply negative funding (shorts
bleeding) is the squeeze tell and drives the ranking; everything stays `watchlist`
until enriched. Funding intervals differ (Binance/most = 8h, some Bybit = 4h,
Hyperliquid = 1h) — the scorer normalizes to a daily rate.

## Enrichment (free, no key) — the curated deep scan (`detector.pipeline`)
| source | endpoint | provides | feeds signal | notes |
|---|---|---|---|---|
| Binance USD-M | `fapi/v1/premiumIndex` | last funding rate, mark price | funding | per-interval rate |
| Binance USD-M | `fapi/v1/fundingInfo` | funding interval (h) | funding | defaults to 8h if absent |
| Binance USD-M | `fapi/v1/openInterest` | OI (base) × mark = OI USD | OI dominance | notional |
| Binance USD-M | `fapi/v1/ticker/24hr` | 24h quote volume | OI/vol fallback | |
| CoinGecko (free) | `coins/markets` | market cap, 24h volume | MC/TVL, P/S, OI dom. | **rate-limited** ~10–30 calls/min |
| DefiLlama (free) | `tvl/{slug}` | protocol TVL | MC/TVL | omit for non-protocol tokens |
| DefiLlama (free) | `summary/fees/{slug}` | 24h fees ×365 | P/S | annualized |

### The fundamental-disconnect signals
`MC/TVL` and `Price/Sales` are the strongest free discriminators: a token whose
market cap is 50–120× its locked value, or whose price is thousands of times its
revenue, is structurally a crime-coin candidate (MYX was ~120× and ~3500× resp.).
These require a `defillama_slug` in `universe.json`; tokens without a real protocol
(memecoins) legitimately skip them and lean on the perp-microstructure signals.

### The squeeze signals
`funding` (deeply negative on the short side = crowded shorts bleeding) and
`OI dominance` (perp OI large vs real float) come straight from Binance futures —
free, fast, no key. This is the engineered-liquidation core of the pattern
(OAK-T17.002).

## Manual today, keyed tomorrow
| signal | v0.1 source | v2 upgrade |
|---|---|---|
| supply concentration (`top_holders_pct`) | hand-entered in `universe.json` | Bubblemaps / Arkham / chain-explorer top-holders API (key) |
| wash volume (`wash_volume_flag`) | hand-entered | cross-venue volume-convergence detector (key) |
| unlock / OTC distribution | — | Tokenomist / CryptoRank unlock calendars → OAK-T5.006 |

## Known limits / honesty notes
- **CoinGecko rate limits** the free tier; the pipeline fires calls back-to-back, so
  on a large universe some `market_cap` reads return `None` and confidence dips
  (seen live: majors at 0.40 conf). Fix: add small pacing or a `COINGECKO_API_KEY`
  env (demo key header) for v0.2. The scorer degrades gracefully meanwhile.
- **DefiLlama slugs** must be exact; a wrong slug silently yields `None` TVL (the
  token then can't fire MC/TVL). Verify slugs at defillama.com/protocol/<slug>.
- **No backtest of the squeeze signals** — funding/OI/walls have no usable history
  (same lesson as the trading core). Validate forward via the committed JSON
  history, not a historical replay.

## Adding a token
Append to `data/universe.json`:
```json
{ "symbol": "XYZ", "binance_symbol": "XYZUSDT", "cg_id": "xyz-coin",
  "defillama_slug": "xyz-protocol", "top_holders_pct": 0.91 }
```
`binance_symbol` / `cg_id` / `defillama_slug` / `top_holders_pct` / `wash_volume_flag`
are all optional except `symbol`; provide what you have, the scorer uses the rest.
