import { siteData } from "./data/generated";

export interface TokenContext {
  market_cap_usd?: number | null;
  tvl_usd?: number | null;
  fees_annualized_usd?: number | null;
  fdv_usd?: number | null;
  mc_tvl?: number;
  ps?: number;
  float?: number;
  liq_usd?: number;
  liq_to_fdv?: number;
  pair_age_days?: number;
  top_holder_control?: number;
  holder_count?: number;
  sell_tax?: number;
  buy_tax?: number;
  chain?: string;
  contract?: string;
}

export interface Evidence {
  label: string;
  url: string;
}

export interface TokenMarket {
  price?: number | null;
  ath?: number | null;
  ath_pct?: number | null;     // % from all-time high (the dump; negative)
  ath_date?: string | null;
  chg24?: number | null;
  chg7d?: number | null;
  chg30d?: number | null;
  vol_24h?: number | null;
  market_cap?: number | null;
}

export interface TokenDumps {
  max_drawdown?: number;
  ath_date?: string;
  biggest_drop?: number;
  biggest_drop_date?: string;
  n_major?: number;
  run_up?: number;
  pump_dump?: boolean;
  recovered?: boolean;
  history_days?: number;
  spark?: number[];
  peak_at?: number | null;
  dump_at?: number | null;
}

export interface TokenProfile {
  name?: string;
  description?: string;
  homepage?: string;
  twitter?: string;
  telegram?: string;
  chat?: string;
  categories?: string[];
  platforms?: Record<string, string>;
  rank?: number;
  image?: string;
}

export interface Token {
  symbol: string;
  venues: string[];
  score: number;
  status: string;
  flags: string[];
  oak_techniques: string[];
  context: TokenContext;
  evidence: Evidence[];
  profile?: TokenProfile;
  market?: TokenMarket;
  dumps?: TokenDumps;
  liveness?: string;
  human_reviewed?: boolean;
  reviewer?: string;
  reviewed_at?: string;
  summary?: string;
}

export interface SiteData {
  schema: string;
  generated_at: string;
  venues: Record<string, number>;
  count: number;
  token_count: number;
  enriched: number;
  contract_checked: number;
  dex_checked: number;
  contract_scam: number;
  suspected: number;
  suspected_tokens: number;
  confirmed_count?: number;
  likely_count?: number;
  cleared_count?: number;
  multi_sign: number;
  flag_counts: Record<string, number>;
  by_token: Token[];
}

export type FlagCounts = Record<string, number>;

export const data: SiteData = siteData as unknown as SiteData;

export const tokenBySymbol = (sym: string): Token | undefined =>
  data.by_token.find((t) => t.symbol.toUpperCase() === sym.toUpperCase());
