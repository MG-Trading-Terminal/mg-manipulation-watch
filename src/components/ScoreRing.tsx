export function ScoreRing({ score, color }: { score: number; color: string }) {
  const r = 34;
  const circ = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, score)) / 100;
  return (
    <svg width="86" height="86" viewBox="0 0 86 86" role="img" aria-label={`score ${score}`}>
      <circle cx="43" cy="43" r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="7" />
      <circle cx="43" cy="43" r={r} fill="none" stroke={color} strokeWidth="7" strokeLinecap="round"
        strokeDasharray={circ} strokeDashoffset={circ * (1 - pct)} transform="rotate(-90 43 43)" />
      <text x="43" y="49" textAnchor="middle" fontFamily="'Geist Mono',ui-monospace,monospace"
        fontSize="25" fontWeight="600" fill={color}>{score}</text>
    </svg>
  );
}
