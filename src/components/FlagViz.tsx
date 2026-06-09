import { FLAG_GROUPS, FLAG_LABEL } from "../lib";
import type { FlagCounts } from "../types";

/** Grouped horizontal bar chart of the per-token sign tally. */
export function FlagViz({ flagCounts }: { flagCounts: FlagCounts }) {
  const values = Object.values(flagCounts);
  if (!values.length) return null;
  const max = Math.max(1, ...values);

  return (
    <div className="viz">
      {FLAG_GROUPS.map(([gname, cls, keys]) => {
        const bars = keys.filter((k) => flagCounts[k]);
        if (!bars.length) return null;
        return (
          <div className="vgroup" key={gname}>
            <div className="vgname">{gname}</div>
            {bars.map((k) => {
              const n = flagCounts[k];
              return (
                <div className="vrow" key={k}>
                  <span className="vlabel">{FLAG_LABEL[k] ?? k}</span>
                  <span className="vbar">
                    <span className={`vfill ${cls}`} style={{ width: `${Math.round((n / max) * 100)}%` }} />
                  </span>
                  <span className="vn num">{n}</span>
                </div>
              );
            })}
          </div>
        );
      })}
    </div>
  );
}
