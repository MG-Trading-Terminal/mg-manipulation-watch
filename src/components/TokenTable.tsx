import { changeClass, pctSigned, priceFmt, scoreClass } from "../lib";
import type { SortDir, SortKey } from "../lib";
import type { Token } from "../types";
import { FlagChips, StatusChip } from "./chips";
import { Sparkline } from "./Sparkline";

interface Col {
  key: SortKey | null;        // null = not sortable
  label: string;
  cls: string;
  align?: "right";
}
const COLS: Col[] = [
  { key: null, label: "#", cls: "c-rank" },
  { key: "symbol", label: "Token", cls: "c-sym" },
  { key: "score", label: "Score", cls: "c-score" },
  { key: null, label: "Status", cls: "c-status" },
  { key: "price", label: "Price", cls: "c-price", align: "right" },
  { key: "chg24", label: "24h", cls: "c-chg", align: "right" },
  { key: "drawdown", label: "ATH↓", cls: "c-dd", align: "right" },
  { key: null, label: "Trend", cls: "c-trend" },
  { key: "signs", label: "Signs", cls: "c-flags" },
  { key: "venues", label: "Venues", cls: "c-venue", align: "right" },
];

export function TokenTable({ tokens, startRank = 1, sort, onSort }: {
  tokens: Token[]; startRank?: number;
  sort: { key: SortKey; dir: SortDir };
  onSort: (k: SortKey) => void;
}) {
  return (
    <table className="ttable">
      <thead>
        <tr>
          {COLS.map((c) => {
            const active = c.key && sort.key === c.key;
            return (
              <th key={c.label} className={`${c.cls} ${c.align === "right" ? "ta-r" : ""}`}>
                {c.key ? (
                  <button className={`th-sort ${active ? "on" : ""}`} onClick={() => onSort(c.key!)}>
                    {c.label}
                    {active && <span className="sort-ind">{sort.dir === "asc" ? "▲" : "▼"}</span>}
                  </button>
                ) : c.label}
              </th>
            );
          })}
        </tr>
      </thead>
      <tbody>
        {tokens.map((t, i) => <TokenRow key={t.symbol} rank={startRank + i} t={t} />)}
      </tbody>
    </table>
  );
}

function ddClass(p?: number | null): string {
  if (p == null) return "";
  return p <= -90 ? "down-txt" : p <= -50 ? "dd-mid" : "dd-lo";
}

function TokenRow({ rank, t }: { rank: number; t: Token }) {
  const venues = t.venues ?? [];
  const sc = scoreClass(t.score);
  const m = t.market ?? {};
  return (
    <tr className="row">
      <td className="c-rank num">{String(rank).padStart(2, "0")}</td>
      <td className="c-sym">
        <a className="sym-link" href={`#/token/${encodeURIComponent(t.symbol)}`}>
          {t.profile?.image
            ? <img className="tlogo" src={t.profile.image} alt="" loading="lazy" width={20} height={20} />
            : <span className="tlogo tlogo-ph" />}
          <span className="sym-id">
            <span className="sym mono">{t.symbol}</span>
            {t.profile?.name && <span className="sym-name">{t.profile.name}</span>}
          </span>
        </a>
      </td>
      <td className="c-score">
        <div className="score-wrap">
          <span className={`score num ${sc}`}>{t.score}</span>
          <span className="gauge"><span className={`gauge-fill ${sc}`} style={{ width: `${Math.max(0, Math.min(100, t.score))}%` }} /></span>
        </div>
      </td>
      <td className="c-status"><StatusChip status={t.status} /></td>
      <td className="c-price num ta-r">{priceFmt(m.price)}</td>
      <td className={`c-chg num ta-r ${changeClass(m.chg24)}`}>{pctSigned(m.chg24)}</td>
      <td className={`c-dd num ta-r ${ddClass(m.ath_pct)}`}>{m.ath_pct != null ? `${m.ath_pct.toFixed(0)}%` : "—"}</td>
      <td className="c-trend"><Sparkline spark={t.dumps?.spark} /></td>
      <td className="c-flags"><FlagChips flags={t.flags} ctx={t.context} /></td>
      <td className="c-venue ta-r">
        <span className="venue" title={venues.join(", ")}>
          <span className="vcount num">{venues.length}</span>
          <span className="vsub">{venues.slice(0, 2).join(" · ")}{venues.length > 2 ? "…" : ""}</span>
        </span>
      </td>
    </tr>
  );
}
