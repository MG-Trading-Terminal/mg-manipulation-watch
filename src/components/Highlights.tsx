import { scoreClass } from "../lib";
import type { Token } from "../types";
import { Sparkline } from "./Sparkline";

/** A horizontal rail of the highest-risk realized rugs — score + the dump curve.
 *  Visual entry point above the table; scrolls horizontally on mobile. */
export function Highlights({ tokens }: { tokens: Token[] }) {
  const picks = tokens
    .filter((t) => t.dumps?.spark && t.dumps.spark.length > 4 && (t.flags.includes("pump-dump") || t.score >= 70))
    .sort((a, b) => b.score - a.score)
    .slice(0, 6);

  if (picks.length < 3) return null;

  return (
    <section className="hl">
      <div className="eyebrow hl-eye">Worst offenders · realized rugs</div>
      <div className="hl-rail">
        {picks.map((t) => {
          const dd = t.market?.ath_pct ?? (t.dumps?.max_drawdown != null ? t.dumps.max_drawdown * 100 : null);
          return (
            <a className="hl-card" key={t.symbol} href={`#/token/${encodeURIComponent(t.symbol)}`}>
              <div className="hl-top">
                {t.profile?.image
                  ? <img className="tlogo" src={t.profile.image} alt="" loading="lazy" width={20} height={20} />
                  : <span className="tlogo tlogo-ph" />}
                <span className="sym mono">{t.symbol}</span>
                <span className={`hl-score num ${scoreClass(t.score)}`}>{t.score}</span>
              </div>
              <Sparkline spark={t.dumps!.spark} width={200} height={46} strokeWidth={1.5} />
              <div className="hl-meta">
                <span className="hl-dd num">{dd != null ? `${dd.toFixed(0)}%` : "—"} from ATH</span>
                {t.flags.includes("pump-dump") && <span className="fl fl-red">PUMP-DUMP</span>}
              </div>
            </a>
          );
        })}
      </div>
    </section>
  );
}
