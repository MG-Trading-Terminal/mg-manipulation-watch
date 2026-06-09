/* Generate an embeddable status badge SVG per token -> dist/badge/<SYMBOL>.svg.
   Projects can <img>-embed their own: green OK (clean) / amber caution (signs) /
   red flagged (suspected or hostile contract). Run after vite build. */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const srcPath = path.join(root, "data", "candidates", "index.json");
const outDir = path.join(root, "dist", "badge");

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function tier(t) {
  const flagged = t.status === "suspected" || t.flags.includes("honeypot") || t.flags.includes("high-tax");
  if (flagged) return { value: "FLAGGED", color: "#ff5b5b", text: "#2a0606" };
  if (t.flags.length >= 1) return { value: `${t.flags.length} SIGN${t.flags.length > 1 ? "S" : ""}`, color: "#ffb547", text: "#2a1c00" };
  return { value: "OK", color: "#3ee07f", text: "#06210f" };
}

function badge(label, value, color, text) {
  const lw = Math.round(10 + label.length * 6.3);
  const vw = Math.round(16 + value.length * 6.6);
  const w = lw + vw;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="20" role="img" aria-label="${esc(label)}: ${esc(value)}">
  <rect width="${w}" height="20" rx="3" fill="#0a0a0a"/>
  <rect x="${lw}" width="${vw}" height="20" rx="3" fill="${color}"/>
  <rect x="${lw}" width="7" height="20" fill="${color}"/>
  <g font-family="Verdana,DejaVu Sans,Geist,sans-serif" font-size="11">
    <text x="${Math.round(lw / 2)}" y="14" fill="#f6f6f4" text-anchor="middle">${esc(label)}</text>
    <text x="${lw + Math.round(vw / 2)}" y="14" fill="${text}" text-anchor="middle" font-weight="bold">${esc(value)}</text>
  </g>
</svg>`;
}

if (!fs.existsSync(srcPath)) {
  console.error("missing index.json — run detector.collect first");
  process.exit(1);
}
const data = JSON.parse(fs.readFileSync(srcPath, "utf8"));
fs.mkdirSync(outDir, { recursive: true });

let n = 0;
for (const t of data.by_token) {
  const safe = String(t.symbol).toUpperCase().replace(/[^A-Z0-9._-]/g, "");
  if (!safe) continue;
  const { value, color, text } = tier(t);
  fs.writeFileSync(path.join(outDir, `${safe}.svg`), badge("MG TERMINAL", value, color, text));
  n++;
}
// Fallback for an un-scanned ticker.
fs.writeFileSync(path.join(outDir, "_unknown.svg"), badge("MG TERMINAL", "NOT SCANNED", "#5a5a55", "#0a0a0a"));
console.log(`wrote ${n} badge SVGs -> dist/badge/`);
