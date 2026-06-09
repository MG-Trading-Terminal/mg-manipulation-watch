/* Post-build: write the public, VERSIONED API into dist/ so consumers can pin a
   stable path. Run after `vite build` via `npm run build`.

   /data.json            — latest (may change shape across versions)
   /v1/data.json         — stable v1 watchlist (additive-only; breaking -> /v2)
   /v1/token/<SYM>.json   — per-token record (full profile + signs + context)
   /CNAME                — custom domain
*/
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const dist = path.join(root, "dist");
const srcPath = path.join(root, "data", "candidates", "index.json");
fs.mkdirSync(dist, { recursive: true });

fs.writeFileSync(path.join(dist, "CNAME"), "mgterminal.com\n");

if (fs.existsSync(srcPath)) {
  const data = JSON.parse(fs.readFileSync(srcPath, "utf8"));
  delete data.tokens;             // ship the per-token view, not 3.8k market rows
  data.api_version = 1;

  // latest alias + stable v1
  fs.writeFileSync(path.join(dist, "data.json"), JSON.stringify(data));
  const v1 = path.join(dist, "v1");
  fs.mkdirSync(v1, { recursive: true });
  fs.writeFileSync(path.join(v1, "data.json"), JSON.stringify(data));

  // per-token endpoints
  const tdir = path.join(v1, "token");
  fs.mkdirSync(tdir, { recursive: true });
  let n = 0;
  for (const t of data.by_token ?? []) {
    const safe = String(t.symbol).toUpperCase().replace(/[^A-Z0-9._-]/g, "");
    if (!safe) continue;
    fs.writeFileSync(path.join(tdir, `${safe}.json`),
      JSON.stringify({ schema: data.schema, api_version: 1, generated_at: data.generated_at, token: t }));
    n++;
  }
  console.log(`api: /data.json + /v1/data.json + ${n} /v1/token/*.json`);
}
