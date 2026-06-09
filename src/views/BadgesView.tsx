import { useMemo, useState } from "react";
import { data } from "../types";

const SITE = "https://mgterminal.com";

function pickExamples() {
  const by = data.by_token;
  const flagged = by.find((t) => t.status === "suspected" || t.flags.includes("honeypot"));
  const caution = by.find((t) => t.flags.length >= 1 && t.status !== "suspected" && !t.flags.includes("honeypot"));
  const ok = [...by].reverse().find((t) => t.flags.length === 0);
  return [ok?.symbol, caution?.symbol, flagged?.symbol].filter(Boolean) as string[];
}

export function BadgesView() {
  const [sym, setSym] = useState<string>("");
  const examples = useMemo(pickExamples, []);
  const upper = sym.trim().toUpperCase().replace(/[^A-Z0-9._-]/g, "");
  const badgeUrl = `${SITE}/badge/${upper || "_unknown"}.svg`;
  const localUrl = `badge/${upper || "_unknown"}.svg`;

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
        <div><img src="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='118' height='20'><rect width='118' height='20' rx='3' fill='%230a0a0a'/><rect x='84' width='34' height='20' rx='3' fill='%233ee07f'/><rect x='84' width='7' height='20' fill='%233ee07f'/><g font-family='Verdana,sans-serif' font-size='11'><text x='42' y='14' fill='%23f6f6f4' text-anchor='middle'>MG TERMINAL</text><text x='101' y='14' fill='%2306210f' text-anchor='middle' font-weight='bold'>OK</text></g></svg>" alt="OK" />
          <span>clean — no signs</span></div>
        <div><img src="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='150' height='20'><rect width='150' height='20' rx='3' fill='%230a0a0a'/><rect x='84' width='66' height='20' rx='3' fill='%23ffb547'/><rect x='84' width='7' height='20' fill='%23ffb547'/><g font-family='Verdana,sans-serif' font-size='11'><text x='42' y='14' fill='%23f6f6f4' text-anchor='middle'>MG TERMINAL</text><text x='117' y='14' fill='%232a1c00' text-anchor='middle' font-weight='bold'>2 SIGNS</text></g></svg>" alt="caution" />
          <span>caution — carries signs</span></div>
        <div><img src="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='150' height='20'><rect width='150' height='20' rx='3' fill='%230a0a0a'/><rect x='84' width='66' height='20' rx='3' fill='%23ff5b5b'/><rect x='84' width='7' height='20' fill='%23ff5b5b'/><g font-family='Verdana,sans-serif' font-size='11'><text x='42' y='14' fill='%23f6f6f4' text-anchor='middle'>MG TERMINAL</text><text x='117' y='14' fill='%232a0606' text-anchor='middle' font-weight='bold'>FLAGGED</text></g></svg>" alt="flagged" />
          <span>flagged — suspected / hostile contract</span></div>
      </div>

      {examples.length > 0 && (
        <>
          <h2>Live, right now</h2>
          <div className="badge-live">
            {examples.map((s) => (
              <a key={s} href={`#/`} title={s}><img src={`badge/${s}.svg`} alt={s} /></a>
            ))}
          </div>
        </>
      )}

      <h2>Embed yours</h2>
      <p>Swap in your ticker. Unscanned tickers return a neutral “NOT SCANNED” badge.</p>
      <div className="lookup">
        <input className="search" type="search" placeholder="TICKER (e.g. MYX)"
          value={sym} onChange={(e) => setSym(e.target.value)} aria-label="ticker" />
        <img src={localUrl} alt={upper || "preview"} style={{ marginLeft: 12, verticalAlign: "middle" }} />
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
