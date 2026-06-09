import { data } from "../types";

// Real donation addresses go here before public launch. Until then we show NO
// address — never ship a placeholder that could silently receive (and lose) funds.
const WALLETS: ReadonlyArray<readonly [string, string]> = [
  // ["EVM", "0x…"], ["SOL", "…"], ["BTC", "bc1…"],
];

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
        {WALLETS.length > 0 ? (
          <div className="wallets">
            {WALLETS.map(([chain, addr]) => (
              <div className="wallet" key={chain}>
                <span className="wchain">{chain}</span>
                <code className="waddr" title="click to select">{addr}</code>
              </div>
            ))}
          </div>
        ) : (
          <p className="donate-soon">Donation addresses go live at launch.</p>
        )}
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
