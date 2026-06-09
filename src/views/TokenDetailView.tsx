import {
  FLAG_DESCRIPTION, FLAG_LABEL, FLAG_STYLE, OAK_LABELS, dexscreenerUrl,
  explorerUrl, fmtUsd, goplusUrl, num, oakUrl, pct, platformLink,
} from "../lib";
import { tokenBySymbol } from "../types";
import type { Evidence } from "../types";
import { RiskHero } from "../components/RiskHero";

function Field({ k, v, warn }: { k: string; v: React.ReactNode; warn?: boolean }) {
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
      <article className="detail">
        <p className="back"><a href="#/">← back to watch</a></p>
        <h1 className="d-h2">{symbol.toUpperCase()} — not scanned</h1>
        <p className="muted">This ticker isn't in the current scan. It may not trade on a
          covered perp venue, or hasn't been picked up yet.</p>
      </article>
    );
  }

  const c = t.context ?? {};
  const p = t.profile ?? {};

  // Contracts: prefer the full per-chain set from the profile; fall back to the
  // single resolved contract used for GoPlus.
  const contracts = Object.keys(p.platforms ?? {}).length
    ? Object.entries(p.platforms!).map(([plat, addr]) => ({ ...platformLink(plat, addr), addr }))
    : (c.contract ? [{ ...(explorerUrl(c.chain, c.contract)
        ? { label: String(c.chain), url: explorerUrl(c.chain, c.contract)! }
        : { label: "contract", url: dexscreenerUrl(c.contract)! }), addr: c.contract }] : []);

  const socials: Array<[string, string | undefined]> = [
    ["Website", p.homepage], ["X / Twitter", p.twitter], ["Telegram", p.telegram], ["Discord / chat", p.chat],
  ];
  const hasLinks = socials.some(([, u]) => u) || contracts.length;

  const evidence: Evidence[] = (() => {
    const out = [...(t.evidence ?? [])];
    if (dexscreenerUrl(c.contract)) out.push({ label: "DexScreener", url: dexscreenerUrl(c.contract)! });
    if (goplusUrl(c.chain, c.contract)) out.push({ label: "GoPlus", url: goplusUrl(c.chain, c.contract)! });
    const seen = new Set<string>();
    return out.filter((l) => (seen.has(l.url) ? false : seen.add(l.url)));
  })();

  const groups: Array<[string, string, string[]]> = [
    ["contract", "fl-red", ["honeypot", "high-tax", "mintable", "owner-control", "holder-concentration", "closed-source"]],
    ["market", "fl-amber", ["squeeze", "oi-dominance", "thin-liquidity", "fresh-launch"]],
    ["fundamental", "fl-info", ["mc/tvl-disconnect", "ps-disconnect", "low-float"]],
  ];

  return (
    <article className="detail">
      <p className="back"><a href="#/">← back to watch</a></p>

      <RiskHero token={t} />

      {t.human_reviewed && (
        <div className="disc" style={{ marginTop: 14 }}>
          <b>Human-reviewed ({t.status}).</b> {t.summary}
          {t.reviewer ? ` — ${t.reviewer}, ${t.reviewed_at}` : ""}
        </div>
      )}

      {(p.description || (p.categories && p.categories.length) || p.rank) && (
        <section className="d-sec">
          <h2 className="d-h2">About</h2>
          {p.rank && <div className="eyebrow" style={{ marginBottom: 8 }}>market-cap rank #{p.rank}</div>}
          {p.description && <p className="d-desc">{p.description}</p>}
          {p.categories && p.categories.length > 0 && (
            <div className="cats">{p.categories.map((cat) => <span className="cat" key={cat}>{cat}</span>)}</div>
          )}
        </section>
      )}

      <section className="d-sec">
        <h2 className="d-h2">Links &amp; contracts</h2>
        {hasLinks ? (
          <div className="linkrow">
            {socials.filter(([, u]) => u).map(([label, u]) => (
              <a key={label} className="ev-link" href={u} target="_blank" rel="noopener">{label} ↗</a>
            ))}
            {contracts.map((ct) => (
              <a key={ct.addr} className="ev-link contract" href={ct.url} target="_blank" rel="noopener"
                title={ct.addr}>{ct.label}: {ct.addr.slice(0, 6)}…{ct.addr.slice(-4)} ↗</a>
            ))}
          </div>
        ) : <p className="muted">No links resolved (token not matched to a CoinGecko profile).</p>}
      </section>

      <section className="d-sec">
        <h2 className="d-h2">Trades on</h2>
        <div className="cats">{t.venues.map((v) => <span className="cat venue-cat" key={v}>{v}</span>)}</div>
      </section>

      <section className="d-sec">
        <h2 className="d-h2">Signs <span className="hcount">{t.flags.length}</span></h2>
        <div className="group-cards">
          {groups.map(([gname, cls, keys]) => {
            const present = keys.filter((k) => t.flags.includes(k));
            if (!present.length) return null;
            return (
              <div className={`gcard accent-${cls}`} key={gname}>
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
          {t.flags.length === 0 && (
            <div className="gcard"><div className="gtitle fl-info">clean</div>
              <p className="muted">No signs raised in this scan.</p></div>
          )}
        </div>
      </section>

      <section className="d-sec">
        <h2 className="d-h2">Fundamentals</h2>
        <div className="datalist">
          <Field k="Market cap" v={fmtUsd(c.market_cap_usd)} />
          <Field k="FDV" v={fmtUsd(c.fdv_usd)} />
          <Field k="Float (circ/FDV)" v={pct(c.float)} warn={c.float != null && c.float < 0.3} />
          <Field k="DEX liquidity" v={fmtUsd(c.liq_usd)} />
          <Field k="Liq / FDV" v={c.liq_to_fdv != null ? pct(c.liq_to_fdv, 3) : "—"} warn={c.liq_to_fdv != null && c.liq_to_fdv < 0.001} />
          <Field k="Pair age" v={c.pair_age_days != null ? `${c.pair_age_days}d` : "—"} />
          <Field k="Top holders" v={pct(c.top_holder_control)} warn={c.top_holder_control != null && c.top_holder_control >= 0.7} />
          <Field k="Holder count" v={c.holder_count != null ? num(c.holder_count) : "—"} warn={c.holder_count != null && c.holder_count < 50} />
          <Field k="Sell tax" v={c.sell_tax != null ? pct(c.sell_tax, 0) : "—"} warn={c.sell_tax != null && c.sell_tax >= 0.1} />
          <Field k="TVL" v={fmtUsd(c.tvl_usd)} />
          <Field k="MC / TVL" v={c.mc_tvl != null ? `${c.mc_tvl}×` : "—"} />
          <Field k="Price / sales" v={c.ps != null ? `${c.ps}×` : "—"} />
        </div>
      </section>

      {t.oak_techniques.length > 0 && (
        <section className="d-sec">
          <h2 className="d-h2">OAK techniques</h2>
          <div className="oak-list">
            {t.oak_techniques.map((id) => (
              <a key={id} className="oak-line" href={oakUrl(id)} target="_blank" rel="noopener">
                <span className="oak">{id.replace("OAK-", "")}</span>
                <span className="oak-desc">{OAK_LABELS[id] ?? id}</span>
              </a>
            ))}
          </div>
        </section>
      )}

      <section className="d-sec">
        <h2 className="d-h2">Evidence</h2>
        <div className="linkrow">
          {evidence.length
            ? evidence.map((l) => <a key={l.url} className="ev-link" href={l.url} target="_blank" rel="noopener">{l.label} ↗</a>)
            : <span className="muted">—</span>}
        </div>
      </section>

      <p className="fineprint">Automated heuristic, not a verdict. <a href="#/methodology">How this works →</a></p>
    </article>
  );
}
