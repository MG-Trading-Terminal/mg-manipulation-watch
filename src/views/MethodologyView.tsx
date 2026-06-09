import { data } from "../types";

export function MethodologyView() {
  const d = data;
  return (
    <article className="prose">
      <div className="eyebrow">manipulation.mgterminal.com · methodology</div>
      <h1>How a token gets <em>on the list</em></h1>
      <p className="lede">
        We sweep the entire perpetual-futures market every four hours, enrich each
        token from independent public feeds, and tag it with <b>signs</b> — each one
        mapped to an <a href="https://onchainattack.org" target="_blank" rel="noopener">OAK</a>
        technique. Nothing here is a verdict. It is a transparent, reproducible read of
        the data so you can do your own research before you ape in.
      </p>

      <h2>The pipeline</h2>
      <ol className="steps">
        <li><b>Sweep — every venue.</b> One bulk call to each of 6 perp venues
          (Binance, Bybit, Bitget, Gate, MEXC, Hyperliquid) → ~{d.count.toLocaleString()} markets,
          consolidated into {d.token_count.toLocaleString()} unique tokens.</li>
        <li><b>Enrich.</b> CoinGecko (market cap, float), DefiLlama (TVL, fees),
          GoPlus (contract security), DexScreener (DEX pool liquidity &amp; pair age).</li>
        <li><b>Score &amp; sign.</b> A pure, open scorer reads the snapshot and raises
          signs in three groups (below). Missing data lowers confidence — it never
          invents suspicion.</li>
        <li><b>Classify.</b> Mechanics drive an auto <code>score</code>; a hostile
          contract (honeypot) forces <code>suspected</code>. Tokens carrying ≥2 signs
          are <b>multi-sign</b>.</li>
        <li><b>Human review.</b> The bot can only say <code>watchlist</code> /
          <code>suspected</code>. A person promotes the strong cases to
          <code>likely</code> / <code>confirmed</code> — or <code>cleared</code> if it
          was a false positive — with an evidence bundle. That is the only place
          "scam" is ever asserted.</li>
        <li><b>Publish.</b> The result is regenerated into open JSON and this page,
          automatically, every 4 hours.</li>
      </ol>

      <h2>The three sign groups</h2>
      <div className="group-cards">
        <div className="gcard">
          <div className="gtitle fl-red">contract</div>
          <p>What the token's smart contract can do to you. <b>honeypot</b> (can't
            sell), <b>high-tax</b>, <b>mintable</b>, <b>owner-control</b> (pausable /
            hidden owner / balance rewrite), <b>holder-concentration</b>,
            <b>closed-source</b>. From GoPlus, grounded in OAK T1 / T3.</p>
        </div>
        <div className="gcard">
          <div className="gtitle fl-amber">market</div>
          <p>How manipulable the market around it is. <b>squeeze</b> (deeply negative
            funding bleeding shorts), <b>oi-dominance</b>, <b>thin-liquidity</b>,
            <b>fresh-launch</b>. From venue funding/OI + DexScreener. OAK T17 / T2.</p>
        </div>
        <div className="gcard">
          <div className="gtitle fl-info">fundamental</div>
          <p>Valuation disconnect — <b>shown as context, never auto-condemning</b>,
            because plenty of legit L1s look the same. <b>mc/tvl-disconnect</b>,
            <b>ps-disconnect</b>, <b>low-float</b>. From CoinGecko / DefiLlama.</p>
        </div>
      </div>

      <h2>Status ladder</h2>
      <table className="ladder">
        <tbody>
          <tr><td><span className="chip chip-mute">watchlist</span></td><td>on the radar, not enough to suspect</td><td>automated</td></tr>
          <tr><td><span className="chip chip-warn">suspected</span></td><td>score over threshold / hostile contract — <b>unverified</b></td><td>automated</td></tr>
          <tr><td><span className="chip chip-warn">likely</span></td><td>several independent signs + a human glance</td><td>human</td></tr>
          <tr><td><span className="chip chip-red">confirmed</span></td><td>fully reviewed, evidence bundled</td><td>human</td></tr>
          <tr><td><span className="chip chip-green">cleared</span></td><td>reviewed, suspicion withdrawn (false positive)</td><td>human</td></tr>
        </tbody>
      </table>

      <h2>Why we don't just trust a ratio</h2>
      <p>"High market cap versus locked value" describes half the market — every L1,
        governance and infrastructure token. So the fundamental ratios are shown as
        context only and never flip a token to <code>suspected</code> on their own.
        The reliable automatic signals are the squeeze (funding) and hard contract
        facts (honeypot, mint, tax, holder concentration).</p>

      <h2>Open &amp; reproducible</h2>
      <p>Every number is fetched from free public feeds and the whole dataset is
        published as open JSON — see the <a href="https://github.com/onchainattack/crime-coins/blob/main/API.md" target="_blank" rel="noopener">API docs</a>.
        Found a false positive? It should be <code>cleared</code> — open an issue.</p>
    </article>
  );
}
