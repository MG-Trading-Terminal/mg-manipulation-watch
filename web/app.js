/* MG Terminal — Manipulation Watch. Renders data.json (the source of truth). */
'use strict';

const DISPLAY_LIMIT = 300;
const OAK_URL = 'https://onchainattack.com/technique/';

const FLAG_STYLE = {
  squeeze: 'fl-red', 'oi-dominance': 'fl-amber', 'mc/tvl-disconnect': 'fl-info',
  'ps-disconnect': 'fl-info', 'low-float': 'fl-amber', honeypot: 'fl-red',
  'high-tax': 'fl-red', mintable: 'fl-amber', 'owner-control': 'fl-amber',
  'closed-source': 'fl-info', 'holder-concentration': 'fl-amber',
  'thin-liquidity': 'fl-amber', 'fresh-launch': 'fl-info',
};
const FLAG_LABEL = {
  squeeze: 'SQUEEZE', 'oi-dominance': 'OI', 'mc/tvl-disconnect': 'MC/TVL',
  'ps-disconnect': 'P/S', 'low-float': 'LOW-FLOAT', honeypot: 'HONEYPOT',
  'high-tax': 'HIGH-TAX', mintable: 'MINTABLE', 'owner-control': 'OWNER-CTRL',
  'closed-source': 'CLOSED-SRC', 'holder-concentration': 'HOLDERS',
  'thin-liquidity': 'THIN-LIQ', 'fresh-launch': 'FRESH',
};
// Visualization groups: contract / market / fundamental.
const FLAG_GROUPS = [
  ['contract', 'fl-red', ['honeypot', 'high-tax', 'mintable', 'owner-control', 'holder-concentration', 'closed-source']],
  ['market', 'fl-amber', ['squeeze', 'oi-dominance', 'thin-liquidity', 'fresh-launch']],
  ['fundamental', 'fl-info', ['mc/tvl-disconnect', 'ps-disconnect', 'low-float']],
];
const OAK_LABELS = {
  'OAK-T17.001': 'Price-discovery distortion', 'OAK-T17.002': 'Liquidation-cascade / squeeze',
  'OAK-T3.002': 'Wash-trade volume', 'OAK-T3.006': 'Insider supply concentration',
  'OAK-T1.006': 'Honeypot', 'OAK-T1.001': 'Modifiable tax', 'OAK-T1.003': 'Hidden mint',
  'OAK-T1.004': 'Weaponizable authority', 'OAK-T2': 'Liquidity establishment',
};

const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const num = (n) => Number(n).toLocaleString('en-US');

function scoreClass(s) { return s >= 70 ? 'sc-hi' : s >= 50 ? 'sc-mid' : 'sc-lo'; }

function statusChip(st) {
  const cls = { suspected: 'chip-warn', watchlist: 'chip-mute', likely: 'chip-warn',
    confirmed: 'chip-red', cleared: 'chip-green' }[st] || 'chip-mute';
  return `<span class="chip ${cls}">${esc(st)}</span>`;
}

function flagTitle(fl, ctx) {
  if (fl === 'mc/tvl-disconnect' && ctx.mc_tvl) return `MC/TVL ${ctx.mc_tvl}x`;
  if (fl === 'ps-disconnect' && ctx.ps) return `P/S ${ctx.ps}x`;
  if (fl === 'low-float' && ctx.float != null) return `${Math.round(ctx.float * 100)}% circulating of FDV`;
  if (fl === 'thin-liquidity' && ctx.liq_usd != null) return `pool $${num(ctx.liq_usd)} liquidity`;
  if (fl === 'fresh-launch' && ctx.pair_age_days != null) return `pair ${ctx.pair_age_days}d old`;
  if (fl === 'holder-concentration' && ctx.top_holder_control != null) return `top holders ${Math.round(ctx.top_holder_control * 100)}%`;
  return '';
}

function flagChips(flags, ctx) {
  if (!flags || !flags.length) return '<span class="oak-none">—</span>';
  return flags.map((fl) =>
    `<span class="fl ${FLAG_STYLE[fl] || 'fl-info'}" title="${esc(flagTitle(fl, ctx || {}))}">${esc(FLAG_LABEL[fl] || fl)}</span>`
  ).join(' ');
}

function oakChips(ids) {
  if (!ids || !ids.length) return '<span class="oak-none">—</span>';
  return ids.map((id) => {
    const slug = id.replace('OAK-', '').toLowerCase();
    return `<a class="oak" href="${OAK_URL}${slug}" target="_blank" rel="noopener" title="${esc(OAK_LABELS[id] || id)}">${esc(id.replace('OAK-', ''))}</a>`;
  }).join(' ');
}

function evidence(links) {
  if (!links || !links.length) return '<span class="oak-none">—</span>';
  return links.map((l) => `<a href="${esc(l.url)}" target="_blank" rel="noopener">${esc(l.label)}</a>`).join(' · ');
}

function flagViz(flagCounts) {
  if (!flagCounts) return '';
  const mx = Math.max(1, ...Object.values(flagCounts));
  const blocks = FLAG_GROUPS.map(([gname, cls, keys]) => {
    const bars = keys.filter((k) => flagCounts[k]).map((k) => {
      const n = flagCounts[k], w = Math.round((n / mx) * 100);
      return `<div class="vrow"><span class="vlabel">${esc(FLAG_LABEL[k] || k)}</span>` +
        `<span class="vbar"><span class="vfill ${cls}" style="width:${w}%"></span></span>` +
        `<span class="vn num">${n}</span></div>`;
    }).join('');
    return bars ? `<div class="vgroup"><div class="vgname">${gname}</div>${bars}</div>` : '';
  }).join('');
  return blocks ? `<div class="viz">${blocks}</div>` : '';
}

function row(rank, t) {
  const score = t.score || 0, flags = t.flags || [], venues = t.venues || [];
  const vlabel = venues.slice(0, 4).join(', ') + (venues.length > 4 ? '…' : '');
  return `<tr class="row" data-status="${esc(t.status)}" data-flags="${flags.length}">
    <td class="c-rank num">${String(rank).padStart(2, '0')}</td>
    <td class="c-sym"><span class="sym mono">${esc(t.symbol)}</span></td>
    <td class="c-venue"><span class="venue" title="${esc(venues.join(', '))}">${venues.length}× <span class="vsub">${esc(vlabel)}</span></span></td>
    <td class="c-status">${statusChip(t.status)}</td>
    <td class="c-score"><div class="score-wrap">
      <span class="score num ${scoreClass(score)}">${score}</span>
      <span class="gauge"><span class="gauge-fill ${scoreClass(score)}" style="width:${Math.max(0, Math.min(100, score))}%"></span></span>
    </div></td>
    <td class="c-flags">${flagChips(flags, t.context)}</td>
    <td class="c-oak">${oakChips(t.oak_techniques)}</td>
    <td class="c-ev">${evidence(t.evidence)}</td>
  </tr>`;
}

function statCell(k, v, cls) {
  return `<div class="stat"><div class="k">${esc(k)}</div><div class="v ${cls || ''}">${v}</div></div>`;
}

function render(d) {
  const tokens = d.by_token || d.tokens || [];
  const count = d.token_count || tokens.length;
  const suspected = d.suspected_tokens != null ? d.suspected_tokens : (d.suspected || 0);
  document.getElementById('stats').innerHTML =
    statCell('Tokens', num(count)) +
    statCell('Suspected', suspected, 'warn') +
    statCell('Multi-sign · ≥2', d.multi_sign || 0) +
    statCell('Updated (UTC)', `<span style="font-size:14px">${esc(d.generated_at)}</span>`);

  const venues = d.venues || {};
  document.getElementById('venues').textContent =
    'venues: ' + (Object.keys(venues).sort().map((k) => `${k} ${venues[k]}`).join(' · ') || '—');
  document.getElementById('checks').textContent =
    `checked: GoPlus ${d.contract_checked || 0} · DexScreener ${d.dex_checked || 0} · ${num(d.count || 0)} markets`;

  document.getElementById('viz').innerHTML = flagViz(d.flag_counts);

  const shown = tokens.slice(0, DISPLAY_LIMIT);
  document.getElementById('rows').innerHTML = shown.map((t, i) => row(i + 1, t)).join('');
  document.getElementById('shown-note').innerHTML =
    `top ${shown.length} of ${num(count)} tokens — full set in <a class="json-link" href="data.json">data.json</a>`;
  document.getElementById('loading').style.display = 'none';
  document.getElementById('table').style.display = '';

  document.querySelectorAll('.filt').forEach((b) => {
    b.addEventListener('click', () => {
      document.querySelectorAll('.filt').forEach((x) => x.classList.remove('on'));
      b.classList.add('on');
      const f = b.getAttribute('data-f');
      document.querySelectorAll('#rows .row').forEach((r) => {
        const show = f === 'all'
          ? true
          : f === 'multi'
            ? parseInt(r.getAttribute('data-flags'), 10) >= 2
            : r.getAttribute('data-status') === f;
        r.style.display = show ? '' : 'none';
      });
    });
  });
}

fetch('data.json')
  .then((r) => r.json())
  .then(render)
  .catch((e) => {
    document.getElementById('loading').textContent = 'failed to load data.json: ' + e;
  });
