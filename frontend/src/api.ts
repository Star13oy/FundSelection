import { FundDetail, FundQuery, FundsListResponse, FundScore, RiskProfile, WatchlistScore } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api/v1";

function toQuery(params: Record<string, string | number | undefined>): string {
 const qs = new URLSearchParams();
 Object.entries(params).forEach(([k, v]) => {
 if (v !== undefined && v !== "") qs.set(k, String(v));
 });
 return qs.toString();
}

export async function fetchFunds(query: FundQuery): Promise<FundsListResponse> {
 const qs = toQuery({
 channel: query.channel,
 category: query.category,
 risk_level: query.risk_level,
 min_years: query.min_years,
 min_scale: query.min_scale,
 max_scale: query.max_scale,
 max_fee: query.max_fee,
 keyword: query.keyword,
 risk_profile: query.risk_profile,
 sort_by: query.sort_by,
 sort_order: query.sort_order,
 page: query.page,
 page_size: query.page_size,
 });
 const resp = await fetch(`${API_BASE}/funds?${qs}`);
 if (!resp.ok) throw new Error("加载基金列表失败");
 return resp.json();
}

export async function fetchFundDetail(code: string, riskProfile: RiskProfile): Promise<FundDetail> {
 const resp = await fetch(`${API_BASE}/funds/${code}?risk_profile=${riskProfile}`);
 if (!resp.ok) throw new Error("加载基金详情失败");
 return resp.json();
}

export async function fetchCompare(codes: string[], riskProfile: RiskProfile): Promise<FundScore[]> {
 const qs = new URLSearchParams();
 codes.forEach((c) => qs.append("codes", c));
 qs.set("risk_profile", riskProfile);
 const resp = await fetch(`${API_BASE}/compare?${qs.toString()}`);
 if (!resp.ok) throw new Error("加载对比数据失败");
 return resp.json();
}

export async function fetchWatchlist(riskProfile: RiskProfile): Promise<WatchlistScore[]> {
 const resp = await fetch(`${API_BASE}/watchlist?risk_profile=${riskProfile}`);
 if (!resp.ok) throw new Error("加载观察池失败");
 return resp.json();
}

export async function addWatchlist(code: string): Promise<void> {
 const resp = await fetch(`${API_BASE}/watchlist`, {
 method: "POST",
 headers: { "Content-Type": "application/json" },
 body: JSON.stringify({ code }),
 });
 if (!resp.ok) throw new Error("加入观察池失败");
}

export async function removeWatchlist(code: string): Promise<void> {
 const resp = await fetch(`${API_BASE}/watchlist/${code}`, { method: "DELETE" });
 if (!resp.ok) throw new Error("移除观察池失败");
}
