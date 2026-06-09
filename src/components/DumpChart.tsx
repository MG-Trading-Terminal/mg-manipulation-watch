import type { TokenDumps } from "../types";

/** Price-history sparkline (log scale) with markers at the all-time-high and the
 *  biggest dump. Pure SVG, no deps. */
export function DumpChart({ dumps }: { dumps: TokenDumps }) {
  const s = dumps.spark;
  if (!s || s.length < 4) return null;

  const W = 760, H = 150, padX = 6, padY = 12;
  const logs = s.map((v) => Math.log10(Math.max(v, 1e-12)));
  const lo = Math.min(...logs), hi = Math.max(...logs);
  const span = hi - lo || 1;
  const x = (i: number) => padX + (i / (s.length - 1)) * (W - 2 * padX);
  const y = (lg: number) => padY + (1 - (lg - lo) / span) * (H - 2 * padY);

  const path = logs.map((lg, i) => `${i ? "L" : "M"}${x(i).toFixed(1)} ${y(lg).toFixed(1)}`).join(" ");
  const area = `${path} L${x(s.length - 1).toFixed(1)} ${H - padY} L${x(0).toFixed(1)} ${H - padY} Z`;

  const markerX = (frac?: number | null) =>
    frac == null ? null : padX + frac * (W - 2 * padX);
  const peakX = markerX(dumps.peak_at);
  const dumpX = markerX(dumps.dump_at);

  return (
    <svg className="dumpchart" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" role="img" aria-label="price history">
      <defs>
        <linearGradient id="dcfill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="rgba(62,224,127,0.14)" />
          <stop offset="100%" stopColor="rgba(62,224,127,0)" />
        </linearGradient>
      </defs>
      <path d={area} fill="url(#dcfill)" />
      <path d={path} fill="none" stroke="#3ee07f" strokeWidth="1.5" />
      {peakX != null && (
        <g>
          <line x1={peakX} y1={padY} x2={peakX} y2={H - padY} stroke="#3ee07f" strokeWidth="1" strokeDasharray="3 3" opacity="0.6" />
          <text x={peakX} y={padY - 2} fill="#3ee07f" fontSize="10" fontFamily="'Geist Mono',monospace" textAnchor="middle">ATH</text>
        </g>
      )}
      {dumpX != null && (
        <g>
          <line x1={dumpX} y1={padY} x2={dumpX} y2={H - padY} stroke="#ff5b5b" strokeWidth="1" strokeDasharray="3 3" opacity="0.7" />
          <text x={dumpX} y={padY - 2} fill="#ff5b5b" fontSize="10" fontFamily="'Geist Mono',monospace" textAnchor="middle">DUMP</text>
        </g>
      )}
    </svg>
  );
}
