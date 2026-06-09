/* Shared constants + helpers. Sign flags map to OAK techniques (see SOURCES.md). */
import type { Token } from "./types";

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
  collapsed: "fl-red", dead: "fl-red", "pump-dump": "fl-red",
};

export const FLAG_LABEL: Record<string, string> = {
  squeeze: "SQUEEZE", "oi-dominance": "OI", "mc/tvl-disconnect": "MC/TVL",
  "ps-disconnect": "P/S", "low-float": "LOW-FLOAT", honeypot: "HONEYPOT",
  "high-tax": "HIGH-TAX", mintable: "MINTABLE", "owner-control": "OWNER-CTRL",
  "closed-source": "CLOSED-SRC", "holder-concentration": "HOLDERS",
  "thin-liquidity": "THIN-LIQ", "fresh-launch": "FRESH",
  collapsed: "COLLAPSED", dead: "DEAD", "pump-dump": "PUMP-DUMP",
};

// Visualization groups: contract / market / fundamental.
export const FLAG_GROUPS: ReadonlyArray<readonly [string, string, readonly string[]]> = [
  ["contract", "fl-red", ["honeypot", "high-tax", "mintable", "owner-control", "holder-concentration", "closed-source"]],
  ["market", "fl-amber", ["pump-dump", "squeeze", "oi-dominance", "thin-liquidity", "fresh-launch", "collapsed", "dead"]],
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

/** Plain-English, beginner-readable description per sign (paired with the chip). */
export const FLAG_DESCRIPTION: Record<string, string> = {
  squeeze: "Deeply negative funding — shorts are bleeding fees. A classic engineered short-squeeze.",
  "oi-dominance": "Open interest is large versus the real float — price is driven by perps, not spot.",
  "thin-liquidity": "The DEX pool is tiny versus the token's valuation — its price is easy to move.",
  "fresh-launch": "A brand-new trading pair already sitting at a large valuation.",
  honeypot: "The contract may block selling (or taxes selling ~100%). You could buy but not get out.",
  "high-tax": "An extractive sell tax (≥10%) skims your exit.",
  mintable: "The team can mint more supply — your share can be diluted.",
  "owner-control": "Owner can pause transfers, hide ownership, or rewrite balances.",
  "holder-concentration": "A few wallets hold most of the supply — they can dump on you.",
  "closed-source": "The contract isn't verified — you can't see what it does.",
  "mc/tvl-disconnect": "Market cap dwarfs the value locked in the protocol (shown as context only).",
  "ps-disconnect": "Market cap dwarfs the revenue it earns (shown as context only).",
  "low-float": "Most supply isn't circulating yet — unlocks can flood the market.",
  collapsed: "Ever fell ≥90% peak-to-trough — a realized dump.",
  dead: "Effectively no trading volume — abandoned.",
  "pump-dump": "Ran up 3x+ then crashed 80%+ and never recovered — the classic rug shape.",
};

export function fmtUsd(n?: number | null): string {
  if (n == null) return "—";
  const a = Math.abs(n);
  if (a >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (a >= 1e6) return `$${(n / 1e6).toFixed(1)}M`;
  if (a >= 1e3) return `$${(n / 1e3).toFixed(1)}K`;
  return `$${n.toFixed(0)}`;
}

export const pct = (x?: number | null, dp = 1): string =>
  x == null ? "—" : `${(x * 100).toFixed(dp)}%`;

export const pctSigned = (x?: number | null): string =>
  x == null ? "—" : `${x >= 0 ? "+" : ""}${x.toFixed(1)}%`;

export const changeClass = (x?: number | null): string =>
  x == null ? "" : x > 0 ? "up" : x < 0 ? "down-txt" : "";

export function priceFmt(p?: number | null): string {
  if (p == null) return "—";
  if (p >= 1) return `$${p.toLocaleString("en-US", { maximumFractionDigits: 2 })}`;
  if (p >= 0.01) return `$${p.toFixed(4)}`;
  return `$${p.toPrecision(2)}`;
}

export const LIVENESS: Record<string, { label: string; cls: string }> = {
  active: { label: "ACTIVE", cls: "fl-info" },
  low: { label: "LOW ACTIVITY", cls: "fl-amber" },
  collapsed: { label: "COLLAPSED", cls: "fl-red" },
  dead: { label: "DEAD · NO VOLUME", cls: "fl-red" },
};
export const dateShort = (s?: string | null): string =>
  s ? s.slice(0, 10) : "—";

const EXPLORERS: Record<string, string> = {
  "1": "https://etherscan.io/token/", "56": "https://bscscan.com/token/",
  "137": "https://polygonscan.com/token/", "42161": "https://arbiscan.io/token/",
  "8453": "https://basescan.org/token/", "10": "https://optimistic.etherscan.io/token/",
  "43114": "https://snowtrace.io/token/", "250": "https://ftmscan.com/token/",
  solana: "https://solscan.io/token/",
};
export function explorerUrl(chain?: string, contract?: string): string | null {
  if (!contract) return null;
  const base = EXPLORERS[String(chain ?? "")];
  return base ? base + contract : null;
}
export function goplusUrl(chain?: string, contract?: string): string | null {
  return contract ? `https://gopluslabs.io/token-security/${chain ?? "1"}/${contract}` : null;
}
export function dexscreenerUrl(contract?: string): string | null {
  return contract ? `https://dexscreener.com/search?q=${contract}` : null;
}

// CoinGecko platform id -> [display name, explorer token base]
const CG_PLATFORM_EXPLORER: Record<string, [string, string]> = {
  ethereum: ["Ethereum", "https://etherscan.io/token/"],
  "binance-smart-chain": ["BSC", "https://bscscan.com/token/"],
  "polygon-pos": ["Polygon", "https://polygonscan.com/token/"],
  "arbitrum-one": ["Arbitrum", "https://arbiscan.io/token/"],
  base: ["Base", "https://basescan.org/token/"],
  "optimistic-ethereum": ["Optimism", "https://optimistic.etherscan.io/token/"],
  avalanche: ["Avalanche", "https://snowtrace.io/token/"],
  fantom: ["Fantom", "https://ftmscan.com/token/"],
  solana: ["Solana", "https://solscan.io/token/"],
  "hyperliquid": ["Hyperliquid", "https://app.hyperliquid.xyz/explorer/address/"],
};
export function platformLink(platform: string, address: string): { label: string; url: string } {
  const m = CG_PLATFORM_EXPLORER[platform];
  return m
    ? { label: m[0], url: m[1] + address }
    : { label: platform, url: `https://dexscreener.com/search?q=${address}` };
}

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

/** A loud, beginner-readable verdict for the detail hero. */
export function riskLevel(flags: string[], status: string): { label: string; tone: "red" | "amber" | "green"; blurb: string } {
  if (status === "confirmed") return { label: "CONFIRMED SCAM", tone: "red", blurb: "Human-reviewed — stays flagged." };
  if (status === "cleared") return { label: "CLEARED", tone: "green", blurb: "Reviewed — false positive." };
  if (flags.includes("honeypot")) return { label: "HOSTILE CONTRACT", tone: "red", blurb: "Selling may be blocked — do not enter." };
  if (status === "suspected") return { label: "HIGH RISK", tone: "red", blurb: "Suspected active manipulation." };
  if (flags.length >= 3) return { label: "ELEVATED RISK", tone: "amber", blurb: `${flags.length} risk signs present.` };
  if (flags.length >= 1) return { label: "CAUTION", tone: "amber", blurb: `${flags.length} risk sign${flags.length > 1 ? "s" : ""} present.` };
  return { label: "NO SIGNS", tone: "green", blurb: "Clean in this scan — still DYOR." };
}

export const TONE_COLOR: Record<string, string> = { red: "#ff5b5b", amber: "#ffb547", green: "#3ee07f" };

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

/* ---- Sorting (column headers on desktop, segmented control on mobile) ---- */
export type SortKey = "score" | "symbol" | "price" | "chg24" | "drawdown" | "signs" | "venues";
export type SortDir = "asc" | "desc";

const sortValue = (t: Token, key: SortKey): number | string | null => {
  switch (key) {
    case "score": return t.score;
    case "symbol": return t.symbol;
    case "price": return t.market?.price ?? null;
    case "chg24": return t.market?.chg24 ?? null;
    case "drawdown": return t.market?.ath_pct ?? null;        // negative; more negative = bigger dump
    case "signs": return t.flags.length;
    case "venues": return t.venues.length;
  }
};

/** Stable sort with null/undefined values always pushed to the bottom, so a
 *  "—" row never tops the list regardless of direction. */
export function sortTokens(tokens: Token[], key: SortKey, dir: SortDir): Token[] {
  const sign = dir === "asc" ? 1 : -1;
  return tokens
    .map((t, i) => [t, i] as const)
    .sort(([a, ai], [b, bi]) => {
      const va = sortValue(a, key), vb = sortValue(b, key);
      if (va == null && vb == null) return ai - bi;
      if (va == null) return 1;
      if (vb == null) return -1;
      if (typeof va === "string" && typeof vb === "string") {
        const c = va.localeCompare(vb);
        return c !== 0 ? sign * c : ai - bi;
      }
      const c = (va as number) - (vb as number);
      return c !== 0 ? sign * c : ai - bi;
    })
    .map(([t]) => t);
}

/** Net direction of a price-history sparkline: end vs start. */
export function sparkTrend(spark?: number[] | null): "up" | "down" | "flat" {
  if (!spark || spark.length < 2) return "flat";
  const a = spark[0], b = spark[spark.length - 1];
  if (b > a * 1.02) return "up";
  if (b < a * 0.98) return "down";
  return "flat";
}
