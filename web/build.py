"""
Static site generator for mgterminal.com.

Reads the JSON dataset (the source of truth) and emits a self-contained,
auto-generated page in the MeatGrinder / MG Terminal design language:
  dist/index.html   (server-rendered rows + light JS filter; works without JS)
  dist/data.json    (the dataset, for programmatic access / cross-checking)

No build deps — pure Python string templating. The page pulls fonts from Google
Fonts and inlines the MG design tokens, so a single file deploys to Pages.

Run:  python3 -m site.build      (expects data/candidates/index.json present)
"""
from __future__ import annotations

import html
import json
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET = os.path.join(ROOT, "data", "candidates", "index.json")
DIST = os.path.join(ROOT, "dist")

# Short, human labels for the OAK technique ids the engine can fire.
OAK_LABELS = {
    "OAK-T17.001": "Price-discovery distortion",
    "OAK-T17.002": "Liquidation-cascade / squeeze",
    "OAK-T3.002": "Wash-trade volume",
    "OAK-T3.006": "Insider supply concentration",
}
OAK_URL = "https://onchainattack.com/technique/{}"

# Order + short labels for the signal mini-bars.
SIGNAL_ORDER = [
    ("mc_tvl", "MC/TVL"),
    ("funding", "FUND"),
    ("oi_dominance", "OI"),
    ("ps_ratio", "P/S"),
    ("supply_conc", "SUP"),
    ("wash_volume", "WASH"),
]


def _esc(s) -> str:
    return html.escape(str(s), quote=True)


def _score_class(score: int) -> str:
    if score >= 70:
        return "sc-hi"
    if score >= 50:
        return "sc-mid"
    return "sc-lo"


def _status_chip(status: str) -> str:
    cls = {
        "suspected": "chip-warn",
        "watchlist": "chip-mute",
        "likely": "chip-warn",
        "confirmed": "chip-red",
        "cleared": "chip-green",
    }.get(status, "chip-mute")
    return f'<span class="chip {cls}">{_esc(status)}</span>'


def _signal_bars(signals: dict) -> str:
    cells = []
    for key, lbl in SIGNAL_ORDER:
        v = signals.get(key)
        if v is None:
            cells.append(f'<div class="sig sig-na" title="{lbl}: no data">'
                         f'<span class="sig-fill" style="height:0"></span>'
                         f'<span class="sig-lbl">{lbl}</span></div>')
        else:
            pct = max(0, min(100, round(v * 100)))
            hot = " sig-hot" if v >= 0.5 else ""
            cells.append(f'<div class="sig{hot}" title="{lbl}: {v:.2f}">'
                         f'<span class="sig-fill" style="height:{pct}%"></span>'
                         f'<span class="sig-lbl">{lbl}</span></div>')
    return f'<div class="sigs">{"".join(cells)}</div>'


def _oak_chips(ids) -> str:
    if not ids:
        return '<span class="oak-none">—</span>'
    out = []
    for tid in ids:
        label = OAK_LABELS.get(tid, tid)
        slug = tid.replace("OAK-", "").lower()
        out.append(f'<a class="oak" href="{OAK_URL.format(slug)}" target="_blank" '
                   f'rel="noopener" title="{_esc(label)}">{_esc(tid.replace("OAK-",""))}</a>')
    return " ".join(out)


def _evidence(links) -> str:
    if not links:
        return '<span class="oak-none">—</span>'
    return " · ".join(
        f'<a href="{_esc(l["url"])}" target="_blank" rel="noopener">{_esc(l["label"])}</a>'
        for l in links
    )


def _row(rank: int, r: dict) -> str:
    score = r.get("score", 0)
    conf = r.get("confidence", 0.0)
    return f"""
    <tr class="row" data-status="{_esc(r.get('status',''))}" data-score="{score}">
      <td class="c-rank num">{rank:02d}</td>
      <td class="c-sym"><span class="sym mono">{_esc(r.get('symbol',''))}</span></td>
      <td class="c-venue"><span class="venue">{_esc(r.get('venue',''))}</span></td>
      <td class="c-status">{_status_chip(r.get('status',''))}</td>
      <td class="c-score">
        <div class="score-wrap">
          <span class="score num {_score_class(score)}">{score}</span>
          <span class="gauge"><span class="gauge-fill {_score_class(score)}" style="width:{max(0,min(100,score))}%"></span></span>
        </div>
      </td>
      <td class="c-conf num">{conf:.2f}</td>
      <td class="c-sigs">{_signal_bars(r.get('signals', {}))}</td>
      <td class="c-oak">{_oak_chips(r.get('oak_techniques', []))}</td>
      <td class="c-ev">{_evidence(r.get('evidence', []))}</td>
    </tr>"""


DISPLAY_LIMIT = 250  # render the top N rows; full set lives in data.json


def render(dataset: dict) -> str:
    tokens = dataset.get("tokens", [])
    shown = tokens[:DISPLAY_LIMIT]
    rows = "\n".join(_row(i + 1, r) for i, r in enumerate(shown))
    gen = dataset.get("generated_at", "")
    count = dataset.get("count", len(tokens))
    suspected = dataset.get("suspected", 0)
    venues = dataset.get("venues", {})
    venue_line = " · ".join(f"{k} {v}" for k, v in sorted(venues.items())) or "—"
    shown_note = (f"top {len(shown)} of {count:,} markets — full set in "
                  f"<a class='json-link' href='data.json'>data.json</a>")

    return TEMPLATE.format(
        rows=rows, gen=_esc(gen), count=f"{count:,}", suspected=suspected,
        watch=f"{count - suspected:,}", venue_line=_esc(venue_line),
        shown_note=shown_note,
    )


def build() -> str:
    with open(DATASET, "r", encoding="utf-8") as f:
        dataset = json.load(f)
    os.makedirs(DIST, exist_ok=True)
    page = render(dataset)
    with open(os.path.join(DIST, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)
    shutil.copyfile(DATASET, os.path.join(DIST, "data.json"))
    # Custom domain for GitHub Pages.
    with open(os.path.join(DIST, "CNAME"), "w", encoding="utf-8") as f:
        f.write("mgterminal.com\n")
    return os.path.join(DIST, "index.html")


# --------------------------------------------------------------------------- #
# Template — MG Terminal design language (dark, serif display, mono numerics)  #
# --------------------------------------------------------------------------- #
TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>MG Terminal — Manipulation Watch</title>
<meta name="description" content="Automated manipulation-risk watchlist for perp tokens. Heuristic signals, OAK-mapped. Not financial advice." />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Geist:wght@300;400;500;600;700&family=Geist+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
<style>
  :root {{
    --bg-0:#050505; --bg-1:#0a0a0a; --bg-2:#111; --bg-3:#161616;
    --line-1:rgba(255,255,255,.06); --line-2:rgba(255,255,255,.10); --line-3:rgba(255,255,255,.16);
    --fg-1:#f6f6f4; --fg-2:#c7c7c2; --fg-3:#8a8a85; --fg-4:#5a5a55;
    --mg:#3ee07f; --mg-bright:#5cff9c; --mg-dim:#1f7a44; --mg-soft:rgba(62,224,127,.10);
    --down:#ff5b5b; --warn:#ffb547;
    --font-display:'Instrument Serif','Times New Roman',serif;
    --font-sans:'Geist',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
    --font-mono:'Geist Mono',ui-monospace,'SF Mono',Menlo,monospace;
  }}
  * {{ box-sizing:border-box; }}
  html,body {{ margin:0; background:
    radial-gradient(circle at 1px 1px, rgba(255,255,255,.04) 1px, transparent 0) 0 0/28px 28px, var(--bg-0);
    color:var(--fg-1); font-family:var(--font-sans); letter-spacing:-.005em;
    -webkit-font-smoothing:antialiased; }}
  a {{ color:var(--fg-2); text-decoration:none; }} a:hover {{ color:var(--mg-bright); }}
  .num,.mono {{ font-family:var(--font-mono); font-feature-settings:"tnum" 1; }}
  .wrap {{ max-width:1180px; margin:0 auto; padding:0 24px 80px; }}

  /* header */
  header {{ display:flex; align-items:center; justify-content:space-between;
    padding:20px 24px; border-bottom:1px solid var(--line-1); max-width:1180px; margin:0 auto; }}
  .logo {{ font-family:var(--font-sans); font-weight:600; letter-spacing:-.04em; font-size:18px;
    display:inline-flex; align-items:center; }}
  .logo .pipe {{ width:2px; height:.95em; background:var(--mg); margin:0 2px; display:inline-block; }}
  .logo .sub {{ color:var(--fg-3); font-weight:400; margin-left:8px; }}
  .live {{ display:inline-flex; align-items:center; gap:8px; font-family:var(--font-mono);
    font-size:11px; text-transform:uppercase; letter-spacing:.14em; color:var(--fg-3); }}
  .dot {{ width:6px; height:6px; border-radius:50%; background:var(--mg);
    box-shadow:0 0 0 0 rgba(62,224,127,.6); animation:pulse 1.8s ease-out infinite; }}
  @keyframes pulse {{ 0%{{box-shadow:0 0 0 0 rgba(62,224,127,.6)}} 70%{{box-shadow:0 0 0 7px rgba(62,224,127,0)}} 100%{{box-shadow:0 0 0 0 rgba(62,224,127,0)}} }}

  /* hero */
  .hero {{ padding:54px 0 26px; }}
  .eyebrow {{ font-family:var(--font-mono); font-size:11px; text-transform:uppercase;
    letter-spacing:.18em; color:var(--fg-3); }}
  h1 {{ font-family:var(--font-display); font-weight:400; letter-spacing:-.02em; line-height:.98;
    font-size:64px; margin:14px 0 0; }}
  h1 em {{ font-style:italic; color:var(--mg-bright); }}
  .lede {{ color:var(--fg-2); max-width:640px; margin-top:16px; font-size:15px; line-height:1.55; }}

  /* disclaimer */
  .disc {{ margin:22px 0 30px; padding:14px 16px; border:1px solid var(--line-2);
    border-left:2px solid var(--warn); border-radius:8px; background:var(--bg-1);
    color:var(--fg-3); font-size:12.5px; line-height:1.5; }}
  .disc b {{ color:var(--fg-2); font-weight:500; }}

  /* stats */
  .stats {{ display:flex; gap:0; border:1px solid var(--line-1); border-radius:10px;
    overflow:hidden; margin-bottom:26px; background:var(--bg-1); }}
  .stat {{ flex:1; padding:16px 18px; border-right:1px solid var(--line-1); }}
  .stat:last-child {{ border-right:none; }}
  .stat .k {{ font-family:var(--font-mono); font-size:10.5px; text-transform:uppercase;
    letter-spacing:.14em; color:var(--fg-4); }}
  .stat .v {{ font-family:var(--font-mono); font-size:26px; margin-top:6px; }}
  .stat .v.warn {{ color:var(--warn); }}

  /* controls */
  .controls {{ display:flex; align-items:center; gap:8px; margin-bottom:14px; }}
  .filt {{ font-family:var(--font-mono); font-size:11px; text-transform:uppercase; letter-spacing:.08em;
    padding:6px 11px; border:1px solid var(--line-2); border-radius:999px; background:transparent;
    color:var(--fg-3); cursor:pointer; }}
  .filt.on {{ color:#002814; background:var(--mg); border-color:var(--mg-bright); }}
  .controls .right {{ margin-left:auto; font-family:var(--font-mono); font-size:11px; color:var(--fg-4); }}

  /* table */
  table {{ width:100%; border-collapse:collapse; }}
  thead th {{ font-family:var(--font-mono); font-size:10px; text-transform:uppercase; letter-spacing:.12em;
    color:var(--fg-4); text-align:left; padding:0 12px 10px; border-bottom:1px solid var(--line-2); font-weight:500; }}
  tbody td {{ padding:14px 12px; border-bottom:1px solid var(--line-1); vertical-align:middle; }}
  .row:hover {{ background:var(--bg-1); }}
  .c-rank {{ color:var(--fg-4); font-size:12px; width:38px; }}
  .sym {{ font-size:15px; font-weight:600; }}
  .c-venue {{ width:96px; }}
  .venue {{ font-family:var(--font-mono); font-size:11px; color:var(--fg-3);
    text-transform:uppercase; letter-spacing:.04em; }}
  .c-score {{ width:140px; }}
  .score-wrap {{ display:flex; align-items:center; gap:10px; }}
  .score {{ font-size:19px; width:30px; }}
  .sc-hi {{ color:var(--down); }} .sc-mid {{ color:var(--warn); }} .sc-lo {{ color:var(--fg-3); }}
  .gauge {{ flex:1; height:4px; background:var(--bg-3); border-radius:999px; overflow:hidden; }}
  .gauge-fill {{ display:block; height:100%; border-radius:999px; }}
  .gauge-fill.sc-hi {{ background:var(--down); }} .gauge-fill.sc-mid {{ background:var(--warn); }}
  .gauge-fill.sc-lo {{ background:var(--mg-dim); }}
  .c-conf {{ color:var(--fg-3); font-size:13px; width:54px; }}

  /* chips */
  .chip {{ display:inline-flex; align-items:center; padding:3px 9px; border-radius:4px;
    font-family:var(--font-mono); font-size:10.5px; text-transform:uppercase; letter-spacing:.05em;
    border:1px solid var(--line-2); }}
  .chip-warn {{ background:rgba(255,181,71,.08); border-color:rgba(255,181,71,.4); color:var(--warn); }}
  .chip-mute {{ background:var(--bg-3); color:var(--fg-3); }}
  .chip-red {{ background:rgba(255,91,91,.08); border-color:rgba(255,91,91,.4); color:var(--down); }}
  .chip-green {{ background:var(--mg-soft); border-color:var(--mg-dim); color:var(--mg-bright); }}

  /* signal mini-bars */
  .sigs {{ display:flex; gap:4px; }}
  .sig {{ display:flex; flex-direction:column; align-items:center; gap:4px; width:30px; }}
  .sig .sig-fill {{ width:18px; height:0; background:var(--fg-4); border-radius:2px;
    align-self:flex-end; min-height:2px; }}
  .sig {{ position:relative; }}
  .sig > .sig-fill {{ display:block; }}
  .sig-bar {{ height:26px; }}
  .sig .sig-fill {{ }}
  .sig-lbl {{ font-family:var(--font-mono); font-size:8px; color:var(--fg-4); letter-spacing:.02em; }}
  .sig.sig-hot .sig-fill {{ background:var(--warn); }}
  .sig.sig-na .sig-fill {{ background:var(--line-2); }}
  /* render fill inside a fixed-height track */
  .c-sigs .sig {{ height:42px; justify-content:flex-end; }}
  .c-sigs .sig .sig-fill {{ }}

  .oak {{ font-family:var(--font-mono); font-size:10px; color:var(--mg); padding:2px 6px;
    border:1px solid var(--mg-dim); border-radius:4px; background:var(--mg-soft); }}
  .oak:hover {{ color:var(--mg-bright); }}
  .oak-none {{ color:var(--fg-4); }}
  .c-ev {{ font-size:12px; color:var(--fg-3); }}
  .c-oak, .c-ev {{ max-width:220px; }}

  footer {{ margin-top:46px; padding-top:22px; border-top:1px solid var(--line-1);
    color:var(--fg-4); font-size:12px; line-height:1.7; }}
  footer a {{ color:var(--fg-3); }}
  .json-link {{ font-family:var(--font-mono); }}

  @media (max-width:760px) {{
    h1 {{ font-size:44px; }}
    .c-sigs, .c-oak {{ display:none; }}
  }}
</style>
</head>
<body>
<header>
  <span class="logo">MG<span class="pipe"></span>Terminal<span class="sub">/ manipulation watch</span></span>
  <span class="live"><span class="dot"></span> auto · every 4h</span>
</header>

<div class="wrap">
  <section class="hero">
    <div class="eyebrow">mgterminal.com · suspected manipulation</div>
    <h1>Manipulation <em>Watch</em></h1>
    <p class="lede">Automated risk scan of perp tokens for the crime-coin pattern —
      fundamental disconnect, perp-driven squeeze, concentrated supply, wash volume.
      Every signal is mapped to an <a href="https://onchainattack.com" target="_blank" rel="noopener">OAK</a>
      technique. The JSON below is the source of truth; this page is generated from it.</p>
  </section>

  <div class="disc">
    <b>Not an accusation.</b> A <b>suspected</b> status is an unverified, automated
    heuristic — a starting point for research, never a determination of wrongdoing.
    Statuses describe evidence strength (<i>watchlist → suspected</i>), and human-reviewed
    states (<i>likely / confirmed / cleared</i>) are gated separately. Nothing here is
    financial advice. Corrections / takedowns: see the repository.
  </div>

  <div class="stats">
    <div class="stat"><div class="k">Markets</div><div class="v">{count}</div></div>
    <div class="stat"><div class="k">Suspected</div><div class="v warn">{suspected}</div></div>
    <div class="stat"><div class="k">Watchlist</div><div class="v">{watch}</div></div>
    <div class="stat"><div class="k">Updated (UTC)</div><div class="v" style="font-size:14px">{gen}</div></div>
  </div>
  <div class="eyebrow" style="margin:10px 2px 0">venues: {venue_line}</div>

  <div class="controls">
    <button class="filt on" data-f="all">All</button>
    <button class="filt" data-f="suspected">Suspected</button>
    <button class="filt" data-f="watchlist">Watchlist</button>
    <span class="right">{shown_note}</span>
  </div>

  <table>
    <thead><tr>
      <th>#</th><th>Token</th><th>Venue</th><th>Status</th><th>Score</th><th>Conf</th>
      <th>Signals</th><th>OAK</th><th>Evidence</th>
    </tr></thead>
    <tbody id="rows">
      {rows}
    </tbody>
  </table>

  <footer>
    Sources: 6 perp venues — Binance · Bybit · Bitget · Gate · MEXC · Hyperliquid
    (funding · OI · volume). Market-wide ranking is funding-driven; OI/MC, P/S,
    supply &amp; wash enrich curated tokens (v0.2). Taxonomy:
    <a href="https://onchainattack.com" target="_blank" rel="noopener">OnChain Attack Knowledge (OAK)</a>.<br/>
    Dataset: <a class="json-link" href="data.json">data.json</a> · schema <span class="mono">mgterminal.crime-coins/v0.2-multivenue</span>.
    Generated automatically — do not hand-edit dist/.<br/>
    © MeatGrinder · MG Terminal. Manipulation-risk heuristic, not financial advice.
  </footer>
</div>

<script>
  // Light client-side filter (page is fully server-rendered without it).
  document.querySelectorAll('.filt').forEach(function(b) {{
    b.addEventListener('click', function() {{
      document.querySelectorAll('.filt').forEach(function(x){{x.classList.remove('on');}});
      b.classList.add('on');
      var f = b.getAttribute('data-f');
      document.querySelectorAll('#rows .row').forEach(function(r) {{
        r.style.display = (f === 'all' || r.getAttribute('data-status') === f) ? '' : 'none';
      }});
    }});
  }});
</script>
</body>
</html>
"""


def main() -> int:
    out = build()
    print("built " + out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
