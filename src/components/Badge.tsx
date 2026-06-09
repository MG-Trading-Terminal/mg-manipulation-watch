import { badgeTier } from "../lib";

/** Inline SVG badge with the exact sizing of scripts/build-badges.mjs (so the
 *  on-page preview matches the embeddable file — no hand-coded data-URIs). */
export function BadgeSvg({ label = "MG TERMINAL", value, color, text }: {
  label?: string; value: string; color: string; text: string;
}) {
  const lw = Math.round(10 + label.length * 6.3);
  const vw = Math.round(16 + value.length * 6.6);
  const w = lw + vw;
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width={w} height={20} role="img"
      aria-label={`${label}: ${value}`} style={{ display: "block" }}>
      <rect width={w} height={20} rx={3} fill="#0a0a0a" />
      <rect x={lw} width={vw} height={20} rx={3} fill={color} />
      <rect x={lw} width={7} height={20} fill={color} />
      <g fontFamily="Verdana,DejaVu Sans,Geist,sans-serif" fontSize={11}>
        <text x={Math.round(lw / 2)} y={14} fill="#f6f6f4" textAnchor="middle">{label}</text>
        <text x={lw + Math.round(vw / 2)} y={14} fill={text} textAnchor="middle" fontWeight="bold">{value}</text>
      </g>
    </svg>
  );
}

export function Badge({ flags, status }: { flags: string[]; status: string }) {
  const { value, color, text } = badgeTier(flags, status);
  return <BadgeSvg value={value} color={color} text={text} />;
}
