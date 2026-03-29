export type RiskProfile = "保守" | "均衡" | "进取";
export type Channel = "场内" | "场外";

export type Explanation = {
 plus: string[];
 minus: string[];
 risk_tip: string;
 applicable: string;
 disclaimer: string;
 formula: string;
};

export type FactorMetrics = {
 returns: number;
 risk_control: number;
 risk_adjusted: number;
 stability: number;
 cost_efficiency: number;
 liquidity: number;
 survival_quality: number;
};

export type PolicyMetrics = {
 support: number;
 execution: number;
 regulation_safety: number;
};

export type FundScore = {
 code: string;
 name: string;
 channel: Channel;
 category: string;
 risk_level: string;
 liquidity_label: string;
 final_score: number;
 base_score: number;
 policy_score: number;
 overlay_weight: number;
 explanation: Explanation;
};

export type FundDetail = FundScore & {
 risk_level: string;
 channel: Channel;
 category: string;
 years: number;
 scale_billion: number;
 one_year_return: number;
 max_drawdown: number;
 fee: number;
 tracking_error: number | null;
 liquidity_label: string;
 updated_at: string;
 factors: FactorMetrics;
 policy: PolicyMetrics;
};

export type WatchlistScore = FundScore & {
 alerts: string[];
};

export type FundsListResponse = {
 items: FundScore[];
 total: number;
 page: number;
 page_size: number;
};

export type FundQuery = {
 channel?: Channel;
 category?: string;
 risk_level?: string;
 min_years?: number;
 min_scale?: number;
 max_scale?: number;
 max_fee?: number;
 keyword?: string;
 risk_profile: RiskProfile;
 sort_by?: "final_score" | "base_score" | "policy_score" | "one_year_return" | "max_drawdown" | "fee";
 sort_order?: "asc" | "desc";
 page?: number;
 page_size?: number;
};
