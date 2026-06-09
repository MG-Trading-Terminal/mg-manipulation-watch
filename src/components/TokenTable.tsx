import { scoreClass } from "../lib";
import type { Token } from "../types";
import { EvidenceLinks, FlagChips, OakChips, StatusChip } from "./chips";

export function TokenTable({ tokens, startRank = 1 }: { tokens: Token[]; startRank?: number }) {
  return (
    <table>
      <thead>
        <tr>
          <th>#</th><th>Token</th><th>Venues</th><th>Status</th><th>Score</th>
          <th>Signs</th><th>OAK</th><th>Evidence</th>
        </tr>
      </thead>
      <tbody>
        {tokens.map((t, i) => <TokenRow key={t.symbol} rank={startRank + i} t={t} />)}
      </tbody>
    </table>
  );
}

function TokenRow({ rank, t }: { rank: number; t: Token }) {
  const venues = t.venues ?? [];
  const vlabel = venues.slice(0, 4).join(", ") + (venues.length > 4 ? "…" : "");
  const sc = scoreClass(t.score);
  return (
    <tr className="row">
      <td className="c-rank num">{String(rank).padStart(2, "0")}</td>
      <td className="c-sym">
        <a className="sym-link" href={`#/token/${encodeURIComponent(t.symbol)}`}>
          {t.profile?.image
            ? <img className="tlogo" src={t.profile.image} alt="" loading="lazy" width={18} height={18} />
            : <span className="tlogo tlogo-ph" />}
          <span className="sym mono">{t.symbol}</span>
        </a>
      </td>
      <td className="c-venue">
        <span className="venue" title={venues.join(", ")}>{venues.length}× <span className="vsub">{vlabel}</span></span>
      </td>
      <td className="c-status"><StatusChip status={t.status} /></td>
      <td className="c-score">
        <div className="score-wrap">
          <span className={`score num ${sc}`}>{t.score}</span>
          <span className="gauge">
            <span className={`gauge-fill ${sc}`} style={{ width: `${Math.max(0, Math.min(100, t.score))}%` }} />
          </span>
        </div>
      </td>
      <td className="c-flags"><FlagChips flags={t.flags} ctx={t.context} /></td>
      <td className="c-oak"><OakChips ids={t.oak_techniques} /></td>
      <td className="c-ev"><EvidenceLinks links={t.evidence} /></td>
    </tr>
  );
}
