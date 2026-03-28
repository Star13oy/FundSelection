import {
 fetchCompare,
 fetchFundDetail,
 fetchFunds,
 fetchWatchlist,
 addWatchlist,
 removeWatchlist,
} from "./api";

type MockResponse = {
 ok: boolean;
 json: () => Promise<unknown>;
};

function makeResponse(ok: boolean, data: unknown): MockResponse {
 return {
 ok,
 json: async () => data,
 };
}

describe("api client", () => {
 beforeEach(() => {
 vi.stubGlobal("fetch", vi.fn());
 });

 afterEach(() => {
 vi.unstubAllGlobals();
 });

 test("fetchFunds 拼装查询参数并返回分页结果", async () => {
 const payload = { items: [], total:0, page:2, page_size:10 };
 vi.mocked(fetch).mockResolvedValue(makeResponse(true, payload) as unknown as Response);

 const result = await fetchFunds({
 risk_profile: "均衡",
 keyword: "510300",
 category: "",
 min_years: undefined,
 max_fee:0.6,
 page:2,
 page_size:10,
 sort_by: "final_score",
 sort_order: "desc",
 });

 expect(result).toEqual(payload);
 const calledUrl = vi.mocked(fetch).mock.calls[0][0] as string;
 const url = new URL(calledUrl);
 expect(url.pathname).toBe("/api/v1/funds");
 expect(url.searchParams.get("risk_profile")).toBe("均衡");
 expect(url.searchParams.get("keyword")).toBe("510300");
 expect(url.searchParams.get("max_fee")).toBe("0.6");
 expect(url.searchParams.get("page")).toBe("2");
 expect(url.searchParams.get("page_size")).toBe("10");
 expect(url.searchParams.has("category")).toBe(false);
 expect(url.searchParams.has("min_years")).toBe(false);
 });

 test("fetchFunds失败时抛出统一错误", async () => {
 vi.mocked(fetch).mockResolvedValue(makeResponse(false, {}) as unknown as Response);
 await expect(fetchFunds({ risk_profile: "均衡" })).rejects.toThrow("加载基金列表失败");
 });

 test("fetchFundDetail 成功返回详情", async () => {
 const payload = { code: "510300" };
 vi.mocked(fetch).mockResolvedValue(makeResponse(true, payload) as unknown as Response);

 await expect(fetchFundDetail("510300", "进取")).resolves.toEqual(payload);
 const calledUrl = vi.mocked(fetch).mock.calls[0][0] as string;
 expect(calledUrl).toContain("/api/v1/funds/510300?risk_profile=进取");
 });

 test("fetchFundDetail失败时抛出统一错误", async () => {
 vi.mocked(fetch).mockResolvedValue(makeResponse(false, {}) as unknown as Response);
 await expect(fetchFundDetail("510300", "均衡")).rejects.toThrow("加载基金详情失败");
 });

 test("fetchCompare 成功返回对比结果", async () => {
 const payload = [{ code: "510300" }, { code: "005827" }];
 vi.mocked(fetch).mockResolvedValue(makeResponse(true, payload) as unknown as Response);

 await expect(fetchCompare(["510300", "005827"], "保守")).resolves.toEqual(payload);
 const calledUrl = vi.mocked(fetch).mock.calls[0][0] as string;
 const url = new URL(calledUrl);
 expect(url.pathname).toBe("/api/v1/compare");
 expect(url.searchParams.getAll("codes")).toEqual(["510300", "005827"]);
 expect(url.searchParams.get("risk_profile")).toBe("保守");
 });

 test("fetchCompare失败时抛出统一错误", async () => {
 vi.mocked(fetch).mockResolvedValue(makeResponse(false, {}) as unknown as Response);
 await expect(fetchCompare(["510300", "005827"], "均衡")).rejects.toThrow("加载对比数据失败");
 });

 test("fetchWatchlist 成功返回观察池", async () => {
 const payload = [{ code: "512480" }];
 vi.mocked(fetch).mockResolvedValue(makeResponse(true, payload) as unknown as Response);

 await expect(fetchWatchlist("均衡")).resolves.toEqual(payload);
 const calledUrl = vi.mocked(fetch).mock.calls[0][0] as string;
 expect(calledUrl).toContain("/api/v1/watchlist?risk_profile=均衡");
 });

 test("fetchWatchlist失败时抛出统一错误", async () => {
 vi.mocked(fetch).mockResolvedValue(makeResponse(false, {}) as unknown as Response);
 await expect(fetchWatchlist("进取")).rejects.toThrow("加载观察池失败");
 });

 test("addWatchlist 成功时发送 POST JSON", async () => {
 vi.mocked(fetch).mockResolvedValue(makeResponse(true, {}) as unknown as Response);

 await expect(addWatchlist("510300")).resolves.toBeUndefined();
 expect(vi.mocked(fetch)).toHaveBeenCalledWith(
 "http://localhost:8000/api/v1/watchlist",
 expect.objectContaining({
 method: "POST",
 headers: { "Content-Type": "application/json" },
 body: JSON.stringify({ code: "510300" }),
 }),
 );
 });

 test("addWatchlist失败时抛出统一错误", async () => {
 vi.mocked(fetch).mockResolvedValue(makeResponse(false, {}) as unknown as Response);
 await expect(addWatchlist("510300")).rejects.toThrow("加入观察池失败");
 });

 test("removeWatchlist 成功时发送 DELETE", async () => {
 vi.mocked(fetch).mockResolvedValue(makeResponse(true, {}) as unknown as Response);

 await expect(removeWatchlist("510300")).resolves.toBeUndefined();
 expect(vi.mocked(fetch)).toHaveBeenCalledWith("http://localhost:8000/api/v1/watchlist/510300", {
 method: "DELETE",
 });
 });

 test("removeWatchlist失败时抛出统一错误", async () => {
 vi.mocked(fetch).mockResolvedValue(makeResponse(false, {}) as unknown as Response);
 await expect(removeWatchlist("510300")).rejects.toThrow("移除观察池失败");
 });
});
