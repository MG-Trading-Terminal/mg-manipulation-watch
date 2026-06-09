import { num } from "../lib";

export function Pager({ page, pageCount, total, pageSize, onPage }: {
  page: number;
  pageCount: number;
  total: number;
  pageSize: number;
  onPage: (p: number) => void;
}) {
  if (total === 0) return <div className="pager empty">no tokens match</div>;
  const from = page * pageSize + 1;
  const to = Math.min(total, (page + 1) * pageSize);
  return (
    <div className="pager">
      <button className="pbtn" disabled={page <= 0} onClick={() => onPage(page - 1)}>← prev</button>
      <span className="pinfo">
        page <span className="num">{page + 1}</span> / <span className="num">{pageCount}</span>
        <span className="psep"> · </span>
        <span className="num">{from}</span>–<span className="num">{to}</span> of <span className="num">{num(total)}</span>
      </span>
      <button className="pbtn" disabled={page >= pageCount - 1} onClick={() => onPage(page + 1)}>next →</button>
    </div>
  );
}
