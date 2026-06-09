import { useState } from "react";
import { DISPLAY_LIMIT, num } from "./lib";
import { data } from "./types";
import { FlagViz } from "./components/FlagViz";
import { TokenTable } from "./components/TokenTable";

const FILTERS = [
  ["all", "All"], ["suspected", "Suspected"], ["multi", "Multi-sign"], ["watchlist", "Watchlist"],
] as const;

function Stat({ k, v, cls }: { k: string; v: React.ReactNode; cls?: string }) {
  return (
    <div className="stat">
      <div className="k">{k}</div>
      <div className={`v ${cls ?? ""}`}>{v}</div>
    </div>
  );
}

export default function App() {
  const [filter, setFilter] = useState<string>("all");
  const d = data;

  const filtered = d.by_token.filter((t) =>
    filter === "all" ? true
      : filter === "multi" ? t.flags.length >= 2
        : t.status === filter,
  );
  const shown = filtered.slice(0, DISPLAY_LIMIT);

  const venueLine = Object.keys(d.venues).sort().map((k) => `${k} ${d.venues[k]}`).join(" · ");

  return (
    <>
      <header>
        <span className="logo">MG<span className="pipe" />Terminal<span className="sub">/ manipulation watch</span></span>
        <span className="live"><span className="dot" /> auto · every 4h</span>
      </header>

      <div className="wrap">
        <section className="hero">
          <div className="eyebrow">mgterminal.com · suspected manipulation</div>
          <h1>Manipulation <em>Watch</em></h1>
          <p className="lede">
            Automated risk scan of perpetual-futures tokens for the crime-coin pattern —
            engineered squeeze, thin liquidity, concentrated supply, hostile contracts,
            fundamental disconnect. Every sign maps to an{" "}
            <a href="https://onchainattack.com" target="_blank" rel="noopener">OAK</a> technique.
          </p>
        </section>

        <div className="disc">
          <b>Not an accusation.</b> A <b>suspected</b> status is an unverified, automated
          heuristic — a starting point for research, never a determination of wrongdoing.
          Statuses describe evidence strength (<i>watchlist → suspected</i>); human-reviewed
          states (<i>likely / confirmed / cleared</i>) are gated separately. Nothing here is
          financial advice. Corrections / takedowns: open an issue on the repository.
        </div>

        <div className="stats">
          <Stat k="Tokens" v={num(d.token_count)} />
          <Stat k="Suspected" v={d.suspected_tokens} cls="warn" />
          <Stat k="Multi-sign · ≥2" v={d.multi_sign} />
          <Stat k="Updated (UTC)" v={<span style={{ fontSize: 14 }}>{d.generated_at}</span>} />
        </div>
        <div className="eyebrow" style={{ margin: "10px 2px 0" }}>venues: {venueLine}</div>
        <div className="eyebrow" style={{ margin: "5px 2px 2px" }}>
          checked: GoPlus {d.contract_checked} · DexScreener {d.dex_checked} · {num(d.count)} markets
        </div>

        <FlagViz flagCounts={d.flag_counts} />

        <div className="controls">
          {FILTERS.map(([f, label]) => (
            <button key={f} className={`filt ${filter === f ? "on" : ""}`} onClick={() => setFilter(f)}>
              {label}
            </button>
          ))}
          <span className="right">
            top {shown.length} of {num(filtered.length)} tokens — full set in{" "}
            <a className="json-link" href="data.json">data.json</a>
          </span>
        </div>

        <TokenTable tokens={shown} />

        <footer>
          Sources: 6 perp venues (Binance · Bybit · Bitget · Gate · MEXC · Hyperliquid —
          funding · OI · volume) + CoinGecko (MC · float) + DefiLlama (TVL · fees) +
          GoPlus (contract security) + DexScreener (DEX liquidity · pair age). One row per
          token; signs unioned across venues. Each sign maps to an{" "}
          <a href="https://onchainattack.com" target="_blank" rel="noopener">OnChain Attack Knowledge (OAK)</a> technique.<br />
          Dataset: <a className="json-link" href="data.json">data.json</a> · schema <span className="mono">{d.schema}</span>.<br />
          © MeatGrinder · MG Terminal. Manipulation-risk heuristic, not financial advice.
        </footer>
      </div>
    </>
  );
}
