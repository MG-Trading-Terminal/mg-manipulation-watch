import { LIVENESS, TONE_COLOR, riskLevel } from "../lib";
import type { Token } from "../types";
import { ScoreRing } from "./ScoreRing";
import { StatusChip } from "./chips";

export function RiskHero({ token }: { token: Token }) {
  const rl = riskLevel(token.flags, token.status);
  const color = TONE_COLOR[rl.tone];
  const img = token.profile?.image;
  return (
    <div className={`risk-hero tone-${rl.tone}`} style={{ ["--tone" as string]: color }}>
      <ScoreRing score={token.score} color={color} />
      <div className="rh-main">
        <div className="rh-top">
          {img && <img className="rh-logo" src={img} alt="" width={26} height={26} />}
          <span className="rh-sym mono">{token.symbol}</span>
          {token.profile?.name && <span className="rh-name">{token.profile.name}</span>}
          <StatusChip status={token.status} />
          {!token.human_reviewed && (
            <span className="fl fl-info" title="Automated heuristic — not a human verdict, not an accusation">
              AUTO · UNVERIFIED
            </span>
          )}
          {token.liveness && LIVENESS[token.liveness] && (
            <span className={`fl ${LIVENESS[token.liveness].cls}`}>{LIVENESS[token.liveness].label}</span>
          )}
        </div>
        <div className="rh-label" style={{ color }}>{rl.label}</div>
        <div className="rh-blurb">{rl.blurb}</div>
      </div>
    </div>
  );
}
