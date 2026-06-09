import { FLAG_LABEL, FLAG_STYLE, OAK_LABELS, OAK_URL, STATUS_CHIP, flagTitle } from "../lib";
import type { Evidence, TokenContext } from "../types";

export function StatusChip({ status }: { status: string }) {
  return <span className={`chip ${STATUS_CHIP[status] ?? "chip-mute"}`}>{status}</span>;
}

export function FlagChips({ flags, ctx }: { flags: string[]; ctx: TokenContext }) {
  if (!flags.length) return <span className="oak-none">—</span>;
  return (
    <>
      {flags.map((fl) => (
        <span key={fl} className={`fl ${FLAG_STYLE[fl] ?? "fl-info"}`}
          title={flagTitle(fl, ctx as Record<string, number | string | null | undefined>)}>
          {FLAG_LABEL[fl] ?? fl}
        </span>
      ))}
    </>
  );
}

export function OakChips({ ids }: { ids: string[] }) {
  if (!ids.length) return <span className="oak-none">—</span>;
  return (
    <>
      {ids.map((id) => (
        <a key={id} className="oak" target="_blank" rel="noopener"
          href={`${OAK_URL}${id.replace("OAK-", "").toLowerCase()}`}
          title={OAK_LABELS[id] ?? id}>
          {id.replace("OAK-", "")}
        </a>
      ))}
    </>
  );
}

export function EvidenceLinks({ links }: { links: Evidence[] }) {
  if (!links?.length) return <span className="oak-none">—</span>;
  return (
    <>
      {links.map((l, i) => (
        <span key={l.url}>
          {i > 0 ? " · " : ""}
          <a href={l.url} target="_blank" rel="noopener">{l.label}</a>
        </span>
      ))}
    </>
  );
}
