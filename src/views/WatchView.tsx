import { useEffect, useMemo, useState } from "react";
import { num } from "../lib";
import { data } from "../types";
import { FlagViz } from "../components/FlagViz";
import { TokenTable } from "../components/TokenTable";
import { Pager } from "../components/Pager";

const FILTERS = [
  ["all", "All"], ["suspected", "Suspected"], ["multi", "Multi-sign"], ["watchlist", "Watchlist"],
] as const;
const PAGE_SIZE = 50;

function Stat({ k, v, cls }: { k: string; v: React.ReactNode; cls?: string }) {
  return (
    <div className="stat">
      <div className="k">{k}</div>
      <div className={`v ${cls ?? ""}`}>{v}</div>
    </div>
  );
}

export function WatchView() {
  const d = data;
  const [filter, setFilter] = useState<string>("all");
  const [query, setQuery] = useState<string>("");
  const [page, setPage] = useState<number>(0);

  const q = query.trim().toLowerCase();
  const filtered = useMemo(() => d.by_token.filter((t) => {
    const passFilter = filter === "all" ? true
      : filter === "multi" ? t.flags.length >= 2
        : t.status === filter;
    if (!passFilter) return false;
    if (!q) return true;
    return t.symbol.toLowerCase().includes(q)
      || t.flags.some((f) => f.includes(q))
      || t.venues.some((v) => v.toLowerCase().includes(q));
  }), [d.by_token, filter, q]);

  useEffect(() => { setPage(0); }, [filter, q]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const clampedPage = Math.min(page, pageCount - 1);
  const shown = filtered.slice(clampedPage * PAGE_SIZE, clampedPage * PAGE_SIZE + PAGE_SIZE);

  const venueLine = Object.keys(d.venues).sort().map((k) => `${k} ${d.venues[k]}`).join(" · ");

  return (
    <>
      <section className="hero">
        <div className="eyebrow">mgterminal.com · suspected manipulation</div>
        <h1>Manipulation <em>Watch</em></h1>
        <p className="lede">
          Automated risk scan of perpetual-futures tokens for the crime-coin pattern —
          engineered squeeze, thin liquidity, concentrated supply, hostile contracts,
          fundamental disconnect. Every sign maps to an{" "}
          <a href="https://onchainattack.org" target="_blank" rel="noopener">OAK</a> technique.
          <a href="#/methodology"> How this works →</a>
        </p>
      </section>

      <div className="disc">
        <b>Not an accusation.</b> A <b>suspected</b> status is an unverified, automated
        heuristic — a starting point for research, never a determination of wrongdoing.
        Human-reviewed states (<i>likely / confirmed / cleared</i>) are gated separately.
        Nothing here is financial advice.
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
        <input
          className="search" type="search" placeholder="search token / sign / venue…"
          value={query} onChange={(e) => setQuery(e.target.value)} aria-label="search"
        />
        <span className="right">{num(filtered.length)} match</span>
      </div>

      <TokenTable tokens={shown} startRank={clampedPage * PAGE_SIZE + 1} />
      <Pager page={clampedPage} pageCount={pageCount} total={filtered.length} pageSize={PAGE_SIZE} onPage={setPage} />
    </>
  );
}
