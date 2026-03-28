export type RiskProfile = "保守" | "均衡" | "进取";

export type FundScore = {
 code: string;
 name: string;
 final_score: number;
 base_score: number;
 policy_score: number;
 overlay_weight: number;
 explanation: {
 plus: string[];
 minus: string[];
 risk_tip: string;
 formula: string;
 };
};

export type FundDetail = FundScore & {
 risk_level: string;
 channel: string;
 category: string;
 one_year_return: number;
 max_drawdown: number;
 fee: number;
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
 channel?: "场内" | "场外";
 category?: string;
 min_years?: number;
 max_fee?: number;
 keyword?: string;
 risk_profile: RiskProfile;
 sort_by?: "final_score" | "base_score" | "policy_score" | "one_year_return" | "max_drawdown" | "fee";
 sort_order?: "asc" | "desc";
 page?: number;
 page_size?: number;
};
