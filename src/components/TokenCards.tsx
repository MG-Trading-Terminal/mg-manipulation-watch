import { changeClass, pctSigned, priceFmt, scoreClass } from "../lib";
import type { Token } from "../types";
import { FlagChips, StatusChip } from "./chips";
import { Sparkline } from "./Sparkline";

/** Mobile / narrow-screen layout — one tappable card per token instead of a
 *  horizontally-scrolling table. */
export function TokenCards({ tokens }: { tokens: Token[] }) {
  return (
    <div className="tcards">
      {tokens.map((t) => <TokenCard key={t.symbol} t={t} />)}
    </div>
  );
}

function ddClass(p?: number | null): string {
  if (p == null) return "";
  return p <= -90 ? "down-txt" : p <= -50 ? "dd-mid" : "dd-lo";
}

function TokenCard({ t }: { t: Token }) {
  const sc = scoreClass(t.score);
  const m = t.market ?? {};
  return (
    <a className="tcard" href={`#/token/${encodeURIComponent(t.symbol)}`}>
      <div className="tcard-head">
        <div className="tcard-id">
          {t.profile?.image
            ? <img className="tlogo" src={t.profile.image} alt="" loading="lazy" width={26} height={26} />
            : <span className="tlogo tlogo-ph" />}
          <div className="sym-id">
            <span className="sym mono">{t.symbol}</span>
            {t.profile?.name && <span className="sym-name">{t.profile.name}</span>}
          </div>
        </div>
        <div className="tcard-score">
          <span className={`score num ${sc}`}>{t.score}</span>
          <StatusChip status={t.status} />
        </div>
      </div>

      <span className="gauge gauge-card"><span className={`gauge-fill ${sc}`} style={{ width: `${Math.max(0, Math.min(100, t.score))}%` }} /></span>

      <div className="tcard-metrics">
        <div className="tm"><span className="tm-k">Price</span><span className="tm-v num">{priceFmt(m.price)}</span></div>
        <div className="tm"><span className="tm-k">24h</span><span className={`tm-v num ${changeClass(m.chg24)}`}>{pctSigned(m.chg24)}</span></div>
        <div className="tm"><span className="tm-k">From ATH</span><span className={`tm-v num ${ddClass(m.ath_pct)}`}>{m.ath_pct != null ? `${m.ath_pct.toFixed(0)}%` : "—"}</span></div>
        <div className="tm tm-spark"><Sparkline spark={t.dumps?.spark} width={300} height={30} /></div>
      </div>

      {t.flags.length > 0 && (
        <div className="tcard-flags"><FlagChips flags={t.flags} ctx={t.context} /></div>
      )}
    </a>
  );
}
