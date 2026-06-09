/* Post-build: drop CNAME + a programmatic data.json (per-token, for сверка/API)
   into dist/. Run after `vite build` via `npm run build`. */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const dist = path.join(root, "dist");
fs.mkdirSync(dist, { recursive: true });

fs.writeFileSync(path.join(dist, "CNAME"), "mgterminal.com\n");

const srcPath = path.join(root, "data", "candidates", "index.json");
if (fs.existsSync(srcPath)) {
  const data = JSON.parse(fs.readFileSync(srcPath, "utf8"));
  delete data.tokens; // per-token view for the public API
  fs.writeFileSync(path.join(dist, "data.json"), JSON.stringify(data));
}
console.log("copied CNAME + data.json -> dist/");
