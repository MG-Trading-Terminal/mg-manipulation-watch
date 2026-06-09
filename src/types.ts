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

export interface Token {
  symbol: string;
  venues: string[];
  score: number;
  status: string;
  flags: string[];
  oak_techniques: string[];
  context: TokenContext;
  evidence: Evidence[];
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
  multi_sign: number;
  flag_counts: Record<string, number>;
  by_token: Token[];
}

export type FlagCounts = Record<string, number>;

export const data: SiteData = siteData as unknown as SiteData;
