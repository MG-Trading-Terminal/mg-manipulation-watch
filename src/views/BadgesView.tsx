import { useMemo, useState } from "react";
import { data } from "../types";
import { Badge, BadgeSvg } from "../components/Badge";

const SITE = "https://mgterminal.com";

function pickExamples() {
  const by = data.by_token;
  const flagged = by.find((t) => t.status === "suspected" || t.flags.includes("honeypot"));
  const caution = by.find((t) => t.flags.length >= 1 && t.status !== "suspected" && !t.flags.includes("honeypot"));
  const ok = [...by].reverse().find((t) => t.flags.length === 0);
  return [ok, caution, flagged].filter(Boolean) as typeof by;
}

export function BadgesView() {
  const [sym, setSym] = useState<string>("");
  const examples = useMemo(pickExamples, []);
  const upper = sym.trim().toUpperCase().replace(/[^A-Z0-9._-]/g, "");
  const found = useMemo(() => data.by_token.find((t) => t.symbol.toUpperCase() === upper), [upper]);
  const badgeUrl = `${SITE}/badge/${upper || "_unknown"}.svg`;

  return (
    <article className="prose">
      <div className="eyebrow">mgterminal.com · badges</div>
      <h1>Embeddable <em>status badges</em></h1>
      <p className="lede">
        Every scanned token gets a live SVG badge. A clean project can wear its
        <b> OK</b> proudly; a flagged one can't hide it. Refreshes every 4 hours.
      </p>

      <h2>The three states</h2>
      <div className="badge-states">
        <div><BadgeSvg value="OK" color="#3ee07f" text="#06210f" /><span>clean — no signs</span></div>
        <div><BadgeSvg value="2 SIGNS" color="#ffb547" text="#2a1c00" /><span>caution — carries signs</span></div>
        <div><BadgeSvg value="FLAGGED" color="#ff5b5b" text="#2a0606" /><span>flagged — suspected / hostile contract</span></div>
      </div>

      {examples.length > 0 && (
        <>
          <h2>Live, right now</h2>
          <div className="badge-live">
            {examples.map((t) => (
              <a key={t.symbol} href="#/" title={t.symbol} className="badge-ex">
                <Badge flags={t.flags} status={t.status} />
                <span className="badge-ex-sym">{t.symbol}</span>
              </a>
            ))}
          </div>
        </>
      )}

      <h2>Embed yours</h2>
      <p>Type a ticker to preview its live status. Unscanned tickers return a neutral badge.</p>
      <div className="lookup">
        <input className="search" type="search" placeholder="TICKER (e.g. MYX)"
          value={sym} onChange={(e) => setSym(e.target.value)} aria-label="ticker" />
        <span className="lookup-badge">
          {found
            ? <Badge flags={found.flags} status={found.status} />
            : <BadgeSvg value="NOT SCANNED" color="#5a5a55" text="#0a0a0a" />}
        </span>
      </div>
      <pre className="snippet">{`<!-- HTML -->
<a href="${SITE}"><img src="${badgeUrl}" alt="MG Terminal status"></a>

<!-- Markdown -->
[![MG Terminal](${badgeUrl})](${SITE})`}</pre>

      <p className="fineprint">
        Badges reflect an automated heuristic, not a verdict — see the
        <a href="#/methodology"> methodology</a>. A flagged project that believes it's a
        false positive can request a review (it would be <code>cleared</code>).
      </p>
    </article>
  );
}
