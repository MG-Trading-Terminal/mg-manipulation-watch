import { useId } from "react";
import { sparkTrend } from "../lib";

const TREND_COLOR = { up: "#3ee07f", down: "#ff5b5b", flat: "#8a8a85" } as const;

/** Compact log-scaled price-history sparkline for the watchlist row / card.
 *  Colored by net direction; the dump marker (deepest point) gets a tick. */
export function Sparkline({
  spark, width = 88, height = 26, strokeWidth = 1.25,
}: { spark?: number[] | null; width?: number; height?: number; strokeWidth?: number }) {
  if (!spark || spark.length < 4) {
    return <span className="spark-empty" aria-hidden="true">—</span>;
  }
  const trend = sparkTrend(spark);
  const color = TREND_COLOR[trend];

  // Log scale so a -99% history is still readable (linear flattens the tail).
  const logs = spark.map((v) => Math.log10(Math.max(v, 1e-12)));
  const lo = Math.min(...logs), hi = Math.max(...logs);
  const span = hi - lo || 1;
  const pad = 2;
  const x = (i: number) => pad + (i / (logs.length - 1)) * (width - 2 * pad);
  const y = (lg: number) => pad + (1 - (lg - lo) / span) * (height - 2 * pad);

  const d = logs.map((lg, i) => `${i ? "L" : "M"}${x(i).toFixed(1)} ${y(lg).toFixed(1)}`).join(" ");
  const area = `${d} L${x(logs.length - 1).toFixed(1)} ${height - pad} L${x(0).toFixed(1)} ${height - pad} Z`;

  // deepest point (the realized dump bottom)
  const lowIdx = logs.indexOf(lo);
  const gid = "sg" + useId().replace(/:/g, "");   // unique per instance (no id collisions)

  return (
    <svg className="spark" width="100%" height={height} viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none" role="img" aria-label={`price trend ${trend}`}>
      <defs>
        <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.22" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#${gid})`} />
      <path d={d} fill="none" stroke={color} strokeWidth={strokeWidth} strokeLinejoin="round" strokeLinecap="round" />
      {lowIdx > 0 && lowIdx < logs.length - 1 && (
        <circle cx={x(lowIdx)} cy={y(lo)} r="1.6" fill="#ff5b5b" />
      )}
    </svg>
  );
}
