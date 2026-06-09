import { data } from "../types";

// Placeholder addresses — replace with real ones before launch.
const WALLETS = [
  ["EVM", "0x0000000000000000000000000000000000000000"],
  ["SOL", "So11111111111111111111111111111111111111112"],
  ["BTC", "bc1qxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"],
] as const;

export function DonateFooter() {
  const d = data;
  return (
    <>
      <section className="donate">
        <div className="eyebrow">support the watch</div>
        <h2 className="donate-h">Scanning the whole perp market every 4 hours isn't free.</h2>
        <p className="donate-p">
          No ads, no token, no paywall — the data stays open. If MG Terminal kept you
          out of a rug, chip in and keep the lights on. <b>Without you, we don't scan.</b>
        </p>
        <div className="wallets">
          {WALLETS.map(([chain, addr]) => (
            <div className="wallet" key={chain}>
              <span className="wchain">{chain}</span>
              <code className="waddr" title="click to select">{addr}</code>
            </div>
          ))}
        </div>
      </section>

      <footer>
        Sources: 6 perp venues (Binance · Bybit · Bitget · Gate · MEXC · Hyperliquid) +
        CoinGecko + DefiLlama + GoPlus + DexScreener. One row per token; signs unioned
        across venues. Each sign maps to an{" "}
        <a href="https://onchainattack.org" target="_blank" rel="noopener">OAK</a> technique.<br />
        Open API: <a className="json-link" href="data.json">data.json</a> ·{" "}
        <a href="https://github.com/onchainattack/crime-coins/blob/main/API.md" target="_blank" rel="noopener">docs</a> ·{" "}
        badges <a href="#/badges">/badges</a> · schema <span className="mono">{d.schema}</span>.<br />
        Code MIT · data CC-BY-4.0. © MeatGrinder · MG Terminal. Manipulation-risk
        heuristic, not financial advice.
      </footer>
    </>
  );
}
