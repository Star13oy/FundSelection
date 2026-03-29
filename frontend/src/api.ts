import type { FundDetail, FundQuery, FundsListResponse, FundScore, MarketRefreshResponse, RiskProfile, WatchlistScore } from "./types.ts";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api/v1";

function resolveErrorMessage(resp: Response, fallback: string): string {
 if (resp.status >= 500) return `${fallback}（后端服务异常）`;
 if (resp.status === 404) return `${fallback}（接口不存在）`;
 if (resp.status === 400) return `${fallback}（请求参数错误）`;
 return fallback;
}

async function requestJson<T>(url: string, init: RequestInit | undefined, fallback: string): Promise<T> {
 try {
  const resp = await fetch(url, init);
  if (!resp.ok) throw new Error(resolveErrorMessage(resp, fallback));
  return resp.json() as Promise<T>;
 } catch (error) {
  if (error instanceof TypeError) {
   throw new Error(`${fallback}（无法连接后端，请确认 8000 端口服务已启动）`);
  }
  throw error;
 }
}

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
 return requestJson<FundsListResponse>(`${API_BASE}/funds?${qs}`, undefined, "加载基金列表失败");
}

export async function fetchFundDetail(code: string, riskProfile: RiskProfile): Promise<FundDetail> {
 return requestJson<FundDetail>(`${API_BASE}/funds/${code}?risk_profile=${riskProfile}`, undefined, "加载基金详情失败");
}

export async function fetchCompare(codes: string[], riskProfile: RiskProfile): Promise<FundScore[]> {
 const qs = new URLSearchParams();
 codes.forEach((c) => qs.append("codes", c));
 qs.set("risk_profile", riskProfile);
 return requestJson<FundScore[]>(`${API_BASE}/compare?${qs.toString()}`, undefined, "加载对比数据失败");
}

export async function fetchWatchlist(riskProfile: RiskProfile): Promise<WatchlistScore[]> {
 return requestJson<WatchlistScore[]>(`${API_BASE}/watchlist?risk_profile=${riskProfile}`, undefined, "加载观察池失败");
}

export async function addWatchlist(code: string): Promise<void> {
 const resp = await fetch(`${API_BASE}/watchlist`, {
 method: "POST",
 headers: { "Content-Type": "application/json" },
 body: JSON.stringify({ code }),
 });
 if (!resp.ok) throw new Error(resolveErrorMessage(resp, "加入观察池失败"));
}

export async function removeWatchlist(code: string): Promise<void> {
 const resp = await fetch(`${API_BASE}/watchlist/${code}`, { method: "DELETE" });
 if (!resp.ok) throw new Error(resolveErrorMessage(resp, "移除观察池失败"));
}

export async function refreshMarket(): Promise<MarketRefreshResponse> {
 return requestJson<MarketRefreshResponse>(`${API_BASE}/market/refresh`, { method: "POST" }, "刷新行情失败");
}
