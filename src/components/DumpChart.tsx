import type { TokenDumps } from "../types";

const fmtP = (v: number): string => {
  if (v >= 1000) return v.toLocaleString("en-US", { maximumFractionDigits: 0 });
  if (v >= 1) return v.toFixed(2);
  if (v >= 0.01) return v.toFixed(4);
  return v.toPrecision(2);
};

/** Log-scaled price-history chart with a price axis, ATH + biggest-dump markers,
 *  and the current (latest) point. Pure SVG, scales uniformly (no text stretch). */
export function DumpChart({ dumps }: { dumps: TokenDumps }) {
  const s = dumps.spark;
  if (!s || s.length < 4) return null;

  const W = 760, H = 188, padL = 0, padR = 48, padY = 16;
  const innerW = W - padL - padR;
  const lo = Math.min(...s), hi = Math.max(...s);
  const logs = s.map((v) => Math.log10(Math.max(v, 1e-12)));
  const lLo = Math.min(...logs), lHi = Math.max(...logs);
  const span = lHi - lLo || 1;
  const x = (i: number) => padL + (i / (s.length - 1)) * innerW;
  const y = (lg: number) => padY + (1 - (lg - lLo) / span) * (H - 2 * padY);

  const path = logs.map((lg, i) => `${i ? "L" : "M"}${x(i).toFixed(1)} ${y(lg).toFixed(1)}`).join(" ");
  const area = `${path} L${x(s.length - 1).toFixed(1)} ${H - padY} L${x(0).toFixed(1)} ${H - padY} Z`;

  const markerX = (frac?: number | null) => (frac == null ? null : padL + frac * innerW);
  const peakX = markerX(dumps.peak_at);
  const dumpX = markerX(dumps.dump_at);

  // right-axis price ticks (log-spaced: hi / geometric-mid / lo)
  const ticks = [lHi, (lHi + lLo) / 2, lLo].map((lg) => ({ lg, v: Math.pow(10, lg) }));
  const lastI = s.length - 1;

  return (
    <svg className="dumpchart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="price history">
      <defs>
        <linearGradient id="dcfill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="var(--mg)" stopOpacity="0.16" />
          <stop offset="100%" stopColor="var(--mg)" stopOpacity="0" />
        </linearGradient>
        <filter id="dcglow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="1.6" result="b" />
          <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>

      {/* price grid + right-axis labels */}
      {ticks.map((t, i) => (
        <g key={i}>
          <line x1={padL} x2={padL + innerW} y1={y(t.lg)} y2={y(t.lg)}
            stroke="rgba(255,255,255,0.05)" strokeDasharray={i === 0 || i === 2 ? "0" : "2 5"} />
          <text x={padL + innerW + 6} y={y(t.lg) + 3} fill="var(--fg-4)" fontSize="9.5"
            fontFamily="'Geist Mono',monospace">{fmtP(t.v)}</text>
        </g>
      ))}

      <path d={area} fill="url(#dcfill)" />
      <path d={path} fill="none" stroke="var(--mg)" strokeWidth="1.6" filter="url(#dcglow)" />

      {peakX != null && (
        <g>
          <line x1={peakX} y1={padY} x2={peakX} y2={H - padY} stroke="var(--mg)" strokeWidth="1" strokeDasharray="3 3" opacity="0.55" />
          <text x={peakX} y={padY - 3} fill="var(--mg)" fontSize="9.5" fontFamily="'Geist Mono',monospace" textAnchor="middle">ATH {fmtP(hi)}</text>
        </g>
      )}
      {dumpX != null && (
        <g>
          <line x1={dumpX} y1={padY} x2={dumpX} y2={H - padY} stroke="var(--down)" strokeWidth="1" strokeDasharray="3 3" opacity="0.65" />
          <text x={dumpX} y={padY - 3} fill="var(--down)" fontSize="9.5" fontFamily="'Geist Mono',monospace" textAnchor="middle">DUMP</text>
        </g>
      )}

      {/* current point */}
      <circle cx={x(lastI)} cy={y(logs[lastI])} r="2.6" fill="var(--mg)" />
      <circle cx={x(lastI)} cy={y(logs[lastI])} r="5" fill="none" stroke="var(--mg)" strokeOpacity="0.4" />
    </svg>
  );
}
