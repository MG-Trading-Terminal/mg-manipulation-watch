/* Shared constants + helpers. Sign flags map to OAK techniques (see SOURCES.md). */

export const OAK_BASE = "https://onchainattack.org";
export const DISPLAY_LIMIT = 300;

/** Technique ids (OAK-Tn.nnn) resolve to /technique/<id>; tactic-level ids
 *  (e.g. OAK-T2) have no technique page, so link to the OAK site root. */
export function oakUrl(id: string): string {
  return /^OAK-T\d+\.\d{3}$/.test(id) ? `${OAK_BASE}/technique/${id}` : OAK_BASE;
}

export const FLAG_STYLE: Record<string, string> = {
  squeeze: "fl-red", "oi-dominance": "fl-amber", "mc/tvl-disconnect": "fl-info",
  "ps-disconnect": "fl-info", "low-float": "fl-amber", honeypot: "fl-red",
  "high-tax": "fl-red", mintable: "fl-amber", "owner-control": "fl-amber",
  "closed-source": "fl-info", "holder-concentration": "fl-amber",
  "thin-liquidity": "fl-amber", "fresh-launch": "fl-info",
};

export const FLAG_LABEL: Record<string, string> = {
  squeeze: "SQUEEZE", "oi-dominance": "OI", "mc/tvl-disconnect": "MC/TVL",
  "ps-disconnect": "P/S", "low-float": "LOW-FLOAT", honeypot: "HONEYPOT",
  "high-tax": "HIGH-TAX", mintable: "MINTABLE", "owner-control": "OWNER-CTRL",
  "closed-source": "CLOSED-SRC", "holder-concentration": "HOLDERS",
  "thin-liquidity": "THIN-LIQ", "fresh-launch": "FRESH",
};

// Visualization groups: contract / market / fundamental.
export const FLAG_GROUPS: ReadonlyArray<readonly [string, string, readonly string[]]> = [
  ["contract", "fl-red", ["honeypot", "high-tax", "mintable", "owner-control", "holder-concentration", "closed-source"]],
  ["market", "fl-amber", ["squeeze", "oi-dominance", "thin-liquidity", "fresh-launch"]],
  ["fundamental", "fl-info", ["mc/tvl-disconnect", "ps-disconnect", "low-float"]],
];

export const OAK_LABELS: Record<string, string> = {
  "OAK-T17.001": "Price-discovery distortion", "OAK-T17.002": "Liquidation-cascade / squeeze",
  "OAK-T3.002": "Wash-trade volume", "OAK-T3.006": "Insider supply concentration",
  "OAK-T1.006": "Honeypot", "OAK-T1.001": "Modifiable tax", "OAK-T1.003": "Hidden mint",
  "OAK-T1.004": "Weaponizable authority", "OAK-T2": "Liquidity establishment",
};

export const STATUS_CHIP: Record<string, string> = {
  suspected: "chip-warn", watchlist: "chip-mute", likely: "chip-warn",
  confirmed: "chip-red", cleared: "chip-green",
};

export const num = (n: number): string => Number(n).toLocaleString("en-US");

/** Badge tier from a token's signs — mirrors scripts/build-badges.mjs. */
export function badgeTier(flags: string[], status: string): { value: string; color: string; text: string } {
  const flagged = status === "suspected" || flags.includes("honeypot") || flags.includes("high-tax");
  if (flagged) return { value: "FLAGGED", color: "#ff5b5b", text: "#2a0606" };
  if (flags.length >= 1) return { value: `${flags.length} SIGN${flags.length > 1 ? "S" : ""}`, color: "#ffb547", text: "#2a1c00" };
  return { value: "OK", color: "#3ee07f", text: "#06210f" };
}

export function scoreClass(s: number): string {
  return s >= 70 ? "sc-hi" : s >= 50 ? "sc-mid" : "sc-lo";
}

type Ctx = Record<string, number | string | null | undefined>;

export function flagTitle(fl: string, ctx: Ctx): string {
  const n = (k: string) => ctx[k] as number | undefined;
  if (fl === "mc/tvl-disconnect" && n("mc_tvl")) return `MC/TVL ${n("mc_tvl")}x`;
  if (fl === "ps-disconnect" && n("ps")) return `P/S ${n("ps")}x`;
  if (fl === "low-float" && n("float") != null) return `${Math.round((n("float") as number) * 100)}% circulating of FDV`;
  if (fl === "thin-liquidity" && n("liq_usd") != null) return `pool $${num(n("liq_usd") as number)} liquidity`;
  if (fl === "fresh-launch" && n("pair_age_days") != null) return `pair ${n("pair_age_days")}d old`;
  if (fl === "holder-concentration" && n("top_holder_control") != null) return `top holders ${Math.round((n("top_holder_control") as number) * 100)}%`;
  return "";
}
