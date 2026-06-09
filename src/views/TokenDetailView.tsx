import {
  FLAG_DESCRIPTION, FLAG_LABEL, FLAG_STYLE, OAK_LABELS, dexscreenerUrl,
  explorerUrl, fmtUsd, goplusUrl, num, oakUrl, pct, scoreClass,
} from "../lib";
import { tokenBySymbol } from "../types";
import { StatusChip } from "../components/chips";

function Row({ k, v, warn }: { k: string; v: React.ReactNode; warn?: boolean }) {
  return (
    <div className="dl-row">
      <span className="dl-k">{k}</span>
      <span className={`dl-v num ${warn ? "warn" : ""}`}>{v}</span>
    </div>
  );
}

export function TokenDetailView({ symbol }: { symbol: string }) {
  const t = tokenBySymbol(symbol);
  if (!t) {
    return (
      <article className="prose">
        <p><a href="#/">← back to watch</a></p>
        <h1>{symbol.toUpperCase()} <em>not scanned</em></h1>
        <p className="lede">This ticker isn't in the current scan. It may not trade on a
          covered perp venue, or hasn't been picked up yet.</p>
      </article>
    );
  }

  const c = t.context ?? {};
  const ex = explorerUrl(c.chain, c.contract);
  const sc = scoreClass(t.score);
  const links = [
    ...(t.evidence ?? []),
    ...(ex ? [{ label: "Explorer", url: ex }] : []),
    ...(dexscreenerUrl(c.contract) ? [{ label: "DexScreener", url: dexscreenerUrl(c.contract)! }] : []),
    ...(goplusUrl(c.chain, c.contract) ? [{ label: "GoPlus", url: goplusUrl(c.chain, c.contract)! }] : []),
  ];
  // de-dupe by url
  const seen = new Set<string>();
  const evidence = links.filter((l) => (seen.has(l.url) ? false : seen.add(l.url)));

  const groups: Array<[string, string, string[]]> = [
    ["contract", "fl-red", ["honeypot", "high-tax", "mintable", "owner-control", "holder-concentration", "closed-source"]],
    ["market", "fl-amber", ["squeeze", "oi-dominance", "thin-liquidity", "fresh-launch"]],
    ["fundamental", "fl-info", ["mc/tvl-disconnect", "ps-disconnect", "low-float"]],
  ];

  return (
    <article className="detail">
      <p className="back"><a href="#/">← back to watch</a></p>

      <div className="detail-head">
        <h1 className="dh-sym mono">{t.symbol}</h1>
        <StatusChip status={t.status} />
        <span className={`dh-score num ${sc}`}>{t.score}</span>
        <span className="gauge dh-gauge"><span className={`gauge-fill ${sc}`} style={{ width: `${Math.max(0, Math.min(100, t.score))}%` }} /></span>
      </div>
      <div className="eyebrow dh-meta">
        {c.chain ? `chain ${c.chain}` : "no contract"}
        {c.contract ? <> · <code className="mono">{c.contract.slice(0, 8)}…{c.contract.slice(-6)}</code></> : null}
        {" · "}venues: {t.venues.join(", ")}
      </div>
      {t.human_reviewed && (
        <div className="disc" style={{ marginTop: 14 }}>
          <b>Human-reviewed ({t.status}).</b> {t.summary} {t.reviewer ? `— ${t.reviewer}, ${t.reviewed_at}` : ""}
        </div>
      )}

      <h2 className="d-h2">Signs</h2>
      <div className="group-cards">
        {groups.map(([gname, cls, keys]) => {
          const present = keys.filter((k) => t.flags.includes(k));
          if (!present.length) return null;
          return (
            <div className="gcard" key={gname}>
              <div className={`gtitle ${cls}`}>{gname}</div>
              {present.map((k) => (
                <div className="sign-line" key={k}>
                  <span className={`fl ${FLAG_STYLE[k] ?? "fl-info"}`}>{FLAG_LABEL[k] ?? k}</span>
                  <span className="sign-desc">{FLAG_DESCRIPTION[k] ?? ""}</span>
                </div>
              ))}
            </div>
          );
        })}
        {t.flags.length === 0 && <div className="gcard"><div className="gtitle fl-info">clean</div><p>No signs raised in this scan.</p></div>}
      </div>

      <h2 className="d-h2">Fundamentals</h2>
      <div className="datalist">
        <Row k="Market cap" v={fmtUsd(c.market_cap_usd)} />
        <Row k="FDV" v={fmtUsd(c.fdv_usd)} />
        <Row k="Float (circ/FDV)" v={pct(c.float)} warn={c.float != null && c.float < 0.3} />
        <Row k="DEX liquidity" v={fmtUsd(c.liq_usd)} />
        <Row k="Liq / FDV" v={c.liq_to_fdv != null ? pct(c.liq_to_fdv, 3) : "—"} warn={c.liq_to_fdv != null && c.liq_to_fdv < 0.001} />
        <Row k="Pair age" v={c.pair_age_days != null ? `${c.pair_age_days}d` : "—"} />
        <Row k="Top holders" v={pct(c.top_holder_control)} warn={c.top_holder_control != null && c.top_holder_control >= 0.7} />
        <Row k="Holder count" v={c.holder_count != null ? num(c.holder_count) : "—"} warn={c.holder_count != null && c.holder_count < 50} />
        <Row k="Sell tax" v={c.sell_tax != null ? pct(c.sell_tax, 0) : "—"} warn={c.sell_tax != null && c.sell_tax >= 0.1} />
        <Row k="TVL" v={fmtUsd(c.tvl_usd)} />
        <Row k="MC / TVL" v={c.mc_tvl != null ? `${c.mc_tvl}×` : "—"} />
        <Row k="Price / sales" v={c.ps != null ? `${c.ps}×` : "—"} />
      </div>

      {t.oak_techniques.length > 0 && (
        <>
          <h2 className="d-h2">OAK techniques</h2>
          <div className="oak-list">
            {t.oak_techniques.map((id) => (
              <a key={id} className="oak-line" href={oakUrl(id)} target="_blank" rel="noopener">
                <span className="oak">{id.replace("OAK-", "")}</span>
                <span className="oak-desc">{OAK_LABELS[id] ?? id}</span>
              </a>
            ))}
          </div>
        </>
      )}

      <h2 className="d-h2">Evidence</h2>
      <div className="ev-links">
        {evidence.length
          ? evidence.map((l) => <a key={l.url} className="ev-link" href={l.url} target="_blank" rel="noopener">{l.label} ↗</a>)
          : <span className="oak-none">—</span>}
      </div>

      <p className="fineprint">
        Automated heuristic, not a verdict. <a href="#/methodology">How this works →</a>
      </p>
    </article>
  );
}
