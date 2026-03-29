import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { App } from "./App";
import * as api from "./api";
import type { FundDetail, FundScore, FundsListResponse, WatchlistScore } from "./types";

vi.mock("./api", () => ({
 fetchFunds: vi.fn(),
 fetchFundDetail: vi.fn(),
 fetchCompare: vi.fn(),
 fetchWatchlist: vi.fn(),
 addWatchlist: vi.fn(),
 removeWatchlist: vi.fn(),
}));

const mockedApi = vi.mocked(api);

function makeFund(code: string, score =88): FundScore {
 return {
 code,
 name: `基金${code}`,
 channel: code === "005827" ? "场外" : "场内",
 category: code === "005827" ? "混合" : "宽基",
 risk_level: code === "512480" ? "R5" : "R4",
 liquidity_label: code === "005827" ? "申赎为主" : "高流动性",
 final_score: score,
 base_score:80,
 policy_score:85,
 overlay_weight:0.15,
 explanation: {
 plus: ["政策支持"],
 minus: ["波动较高"],
 risk_tip: "注意回撤",
 applicable: "适合中长期持有",
 disclaimer: "仅供参考，不构成投资建议。",
 formula: "Final = Base*(1-overlay)+Policy*overlay",
 },
 };
}

function makeDetail(code: string): FundDetail {
 return {
 ...makeFund(code),
 risk_level: "中",
 channel: "场内",
 category: "宽基",
 years: 6,
 scale_billion: 120,
 one_year_return:12.3,
 max_drawdown:18.5,
 fee:0.5,
 tracking_error: 0.2,
 liquidity_label: "高流动性",
 updated_at: "2026-03-28",
 factors: {
 returns: 80,
 risk_control: 82,
 risk_adjusted: 79,
 stability: 78,
 cost_efficiency: 88,
 liquidity: 90,
 survival_quality: 85,
 },
 policy: {
 support: 84,
 execution: 82,
 regulation_safety: 80,
 },
 };
}

function makeFundsPage(codes: string[], page =1): FundsListResponse {
 return {
 items: codes.map((c, i) => makeFund(c,90 - i)),
 total:6,
 page,
 page_size:20,
 };
}

beforeEach(() => {
 vi.clearAllMocks();

 mockedApi.fetchFunds.mockResolvedValue(makeFundsPage(["510300", "005827", "512480"]));
 mockedApi.fetchFundDetail.mockImplementation(async (code) => makeDetail(code));
 mockedApi.fetchWatchlist.mockResolvedValue([] as WatchlistScore[]);
 mockedApi.fetchCompare.mockResolvedValue([makeFund("510300"), makeFund("005827")]);
 mockedApi.addWatchlist.mockResolvedValue();
 mockedApi.removeWatchlist.mockResolvedValue();
});

describe("App interactions", () => {
 test("页面切换正常", async () => {
 render(<App />);

 fireEvent.click(screen.getByRole("button", { name: "选基" }));
 expect(screen.getByText(/手动对比已选：0\s*\/5/)).toBeInTheDocument();

 fireEvent.click(screen.getByRole("button", { name: "观察池" }));
 expect(screen.getByRole("heading", { level:2, name: "观察池" })).toBeInTheDocument();

 fireEvent.click(screen.getByRole("button", { name: "对比" }));
 expect(screen.getByRole("heading", { level:2, name: "基金深度量化对比" })).toBeInTheDocument();

 await waitFor(() => expect(mockedApi.fetchFunds).toHaveBeenCalled());
 });

 test("风险偏好切换会触发重新请求", async () => {
 render(<App />);

 await waitFor(() => expect(mockedApi.fetchFunds).toHaveBeenCalledTimes(1));
 fireEvent.click(screen.getByRole("button", { name: "进取" }));
 await waitFor(() => expect(mockedApi.fetchFunds).toHaveBeenCalledTimes(2));
 });

 test("手动对比2只后对比页展示手动来源", async () => {
 render(<App />);
 fireEvent.click(screen.getByRole("button", { name: "选基" }));

 const compareButtons = await screen.findAllByRole("button", { name: "加入对比" });
 fireEvent.click(compareButtons[0]);
  fireEvent.click(compareButtons[1]);

  fireEvent.click(screen.getByRole("button", { name: "对比" }));

  await waitFor(() => expect(mockedApi.fetchCompare).toHaveBeenCalled());
 expect(screen.getByText(/当前来源：手动选择/)).toBeInTheDocument();
 });

 test("观察池按钮调用新增接口", async () => {
 render(<App />);
 fireEvent.click(screen.getByRole("button", { name: "选基" }));

 const watchButtons = await screen.findAllByRole("button", { name: "加入观察池" });
 fireEvent.click(watchButtons[0]);

 await waitFor(() => expect(mockedApi.addWatchlist).toHaveBeenCalled());
 });

 test("查看详情会进入详情页并展示字段", async () => {
 render(<App />);
 fireEvent.click(screen.getByRole("button", { name: "选基" }));

 const detailButtons = await screen.findAllByRole("button", { name: "查看详情" });
  fireEvent.click(detailButtons[0]);

  await waitFor(() => {
 expect(screen.getByRole("heading", { level:2, name: "基金详情页" })).toBeInTheDocument();
  });
 expect(screen.getAllByText(/12.3%/).length).toBeGreaterThan(0);
 });

 test("单页结果时分页按钮禁用", async () => {
 render(<App />);
 fireEvent.click(screen.getByRole("button", { name: "选基" }));

 await waitFor(() => expect(mockedApi.fetchFunds).toHaveBeenCalledTimes(1));
 expect(screen.getByRole("button", { name: "上一页" })).toBeDisabled();
 expect(screen.getByRole("button", { name: "下一页" })).toBeDisabled();
 });

 test("观察池页面可触发移除", async () => {
 mockedApi.fetchWatchlist.mockResolvedValue([
 { ...makeFund("512480"), alerts: ["回撤超阈值"] },
 ] as WatchlistScore[]);

 render(<App />);
 fireEvent.click(screen.getByRole("button", { name: "观察池" }));

 const removeBtn = await screen.findByRole("button", { name: "移除" });
 fireEvent.click(removeBtn);
 await waitFor(() => expect(mockedApi.removeWatchlist).toHaveBeenCalled());
 });

 test("仅1只手动对比时显示不足提示", async () => {
 mockedApi.fetchCompare.mockResolvedValue([]);
 render(<App />);

 fireEvent.click(screen.getByRole("button", { name: "选基" }));
 const compareButtons = await screen.findAllByRole("button", { name: "加入对比" });
 fireEvent.click(compareButtons[0]);

 fireEvent.click(screen.getByRole("button", { name: "对比" }));
 expect(screen.getByText("请先手动或通过观察池凑齐至少2只基金。")).toBeInTheDocument();
 });

 test("基金列表请求失败时展示错误提示", async () => {
 mockedApi.fetchFunds.mockRejectedValueOnce(new Error("加载基金列表失败"));
 render(<App />);

 await waitFor(() => {
 expect(screen.getByText("错误：加载基金列表失败")).toBeInTheDocument();
 });
 });

 test("手动对比最多仅允许选择5只", async () => {
 mockedApi.fetchFunds.mockResolvedValueOnce(
 makeFundsPage(["510300", "005827", "512480", "159915", "513100", "159949"]),
 );
 render(<App />);
 fireEvent.click(screen.getByRole("button", { name: "选基" }));

 let addButtons = await screen.findAllByRole("button", { name: "加入对比" });
 for (let i =0; i < addButtons.length; i +=1) {
 fireEvent.click(addButtons[i]);
 }

 expect(screen.getByText(/手动对比已选：5\s*\/5/)).toBeInTheDocument();
 expect(screen.getByText("已达到手动对比上限（5只）。")).toBeInTheDocument();
 expect(screen.getAllByRole("button", { name: "取消对比" })).toHaveLength(5);
 });

 test("筛选表单变更会触发重新请求", async () => {
 render(<App />);
 fireEvent.click(screen.getByRole("button", { name: "选基" }));

 await waitFor(() => expect(mockedApi.fetchFunds).toHaveBeenCalledTimes(1));

 fireEvent.change(screen.getByLabelText("最低年限"), { target: { value: "3" } });
 fireEvent.change(screen.getByLabelText("最高费率"), { target: { value: "0.6" } });
 fireEvent.change(screen.getByLabelText("排序字段"), { target: { value: "fee" } });

 await waitFor(() => expect(mockedApi.fetchFunds).toHaveBeenCalledTimes(4));
 });


 test("分页可翻页并触发上一页/下一页请求", async () => {
 mockedApi.fetchFunds.mockResolvedValue({
 items: [makeFund("510300"), makeFund("005827")],
 total:60,
 page:1,
 page_size:20,
 });
 render(<App />);
 fireEvent.click(screen.getByRole("button", { name: "选基" }));

 await waitFor(() => expect(mockedApi.fetchFunds).toHaveBeenCalledTimes(1));
const nextButton = screen.getByRole("button", { name: "下一页" });
expect(nextButton).toBeEnabled();

fireEvent.click(nextButton);
await waitFor(() => expect(mockedApi.fetchFunds).toHaveBeenCalledTimes(2));

 fireEvent.click(screen.getByRole("button", { name: "上一页" }));
await waitFor(() => expect(mockedApi.fetchFunds).toHaveBeenCalledTimes(3));
 });

 test("空结果时展示无结果提示", async () => {
 mockedApi.fetchFunds.mockResolvedValue({ items: [], total:0, page:1, page_size:20 });
 render(<App />);
 fireEvent.click(screen.getByRole("button", { name: "选基" }));

 await waitFor(() => expect(mockedApi.fetchFunds).toHaveBeenCalled());
 expect(screen.getByText("无结果，请调整筛选条件。")).toBeInTheDocument();
 });

 test("观察池可进入对比页", async () => {
 mockedApi.fetchWatchlist.mockResolvedValue([
 { ...makeFund("510300"), alerts: ["提醒"] },
 { ...makeFund("005827"), alerts: ["提醒"] },
 ] as WatchlistScore[]);
 render(<App />);

  fireEvent.click(screen.getByRole("button", { name: "观察池" }));
  const toCompare = await screen.findByRole("button", { name: "进入对比页" });
  fireEvent.click(toCompare);

 expect(screen.getByRole("heading", { level:2, name: "基金深度量化对比" })).toBeInTheDocument();
 });

 test("详情页支持切换表现、因子、成本与解释标签", async () => {
 render(<App />);
 fireEvent.click(screen.getByRole("button", { name: "选基" }));

  const detailButtons = await screen.findAllByRole("button", { name: "查看详情" });
  fireEvent.click(detailButtons[0]);

  await screen.findByRole("heading", { level:2, name: "基金详情页" });
 fireEvent.click(screen.getByRole("button", { name: "因子分析" }));
 expect(screen.getByText("政策支持强度")).toBeInTheDocument();

fireEvent.click(screen.getByRole("button", { name: "成本与交易" }));
expect(screen.getAllByText("流动性标签").length).toBeGreaterThan(0);
expect(screen.getAllByText("高流动性").length).toBeGreaterThan(0);

 fireEvent.click(screen.getByRole("button", { name: "推荐理由" }));
 expect(screen.getAllByText("仅供参考，不构成投资建议。").length).toBeGreaterThan(0);
 });

 test("筛选扩展项与重置按钮会更新请求参数", async () => {
 render(<App />);
 fireEvent.click(screen.getByRole("button", { name: "选基" }));

 await waitFor(() => expect(mockedApi.fetchFunds).toHaveBeenCalledTimes(1));

 fireEvent.change(screen.getByLabelText("场内/场外"), { target: { value: "场内" } });
 fireEvent.change(screen.getByLabelText("风险等级"), { target: { value: "R4" } });
 fireEvent.change(screen.getByLabelText("最低规模（亿元）"), { target: { value: "50" } });
 fireEvent.change(screen.getByLabelText("最高规模（亿元）"), { target: { value: "300" } });

 await waitFor(() => expect(mockedApi.fetchFunds).toHaveBeenCalledTimes(5));
 expect(mockedApi.fetchFunds).toHaveBeenLastCalledWith(
  expect.objectContaining({
   channel: "场内",
   risk_level: "R4",
   min_scale: 50,
   max_scale: 300,
  }),
 );

 fireEvent.click(screen.getByRole("button", { name: "重置筛选" }));
 await waitFor(() => expect(mockedApi.fetchFunds).toHaveBeenCalledTimes(6));
 expect(mockedApi.fetchFunds).toHaveBeenLastCalledWith(
  expect.objectContaining({
   channel: undefined,
   risk_level: "",
   min_scale: undefined,
   max_scale: undefined,
  }),
 );
 });

 test("导出结果会创建下载链接", async () => {
 Object.defineProperty(URL, "createObjectURL", {
  writable: true,
  value: vi.fn(() => "blob:test"),
 });
 Object.defineProperty(URL, "revokeObjectURL", {
  writable: true,
  value: vi.fn(),
 });
 const click = vi.fn();
 const originalCreateElement = document.createElement.bind(document);
 vi.spyOn(document, "createElement").mockImplementation(((tagName: string) => {
  if (tagName === "a") {
   return { click, href: "", download: "" } as unknown as HTMLAnchorElement;
  }
  return originalCreateElement(tagName);
 }) as typeof document.createElement);

 render(<App />);
 fireEvent.click(screen.getByRole("button", { name: "选基" }));
 await screen.findByRole("button", { name: "导出结果" });
 fireEvent.click(screen.getByRole("button", { name: "导出结果" }));

 expect(URL.createObjectURL).toHaveBeenCalled();
 expect(click).toHaveBeenCalled();
 expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:test");
 });

 test("观察池条目可查看详情和加入对比", async () => {
 mockedApi.fetchWatchlist.mockResolvedValue([
  { ...makeFund("510300"), alerts: ["提醒"] },
 ] as WatchlistScore[]);

 render(<App />);
 fireEvent.click(screen.getByRole("button", { name: "观察池" }));

 const detailButton = await screen.findByRole("button", { name: "查看详情" });
 fireEvent.click(detailButton);
 await screen.findByRole("heading", { level:2, name: "基金详情页" });

 fireEvent.click(screen.getByRole("button", { name: "观察池" }));
 const compareButton = await screen.findByRole("button", { name: "加入对比" });
 fireEvent.click(compareButton);
 expect(await screen.findByRole("button", { name: "取消对比" })).toBeInTheDocument();
 });

 test("观察池自动对比会展示结论摘要卡片", async () => {
 mockedApi.fetchWatchlist.mockResolvedValue([
  { ...makeFund("510300", 91), alerts: ["提醒"] },
  { ...makeFund("005827", 87), alerts: ["提醒"] },
 ] as WatchlistScore[]);

 render(<App />);
 fireEvent.click(screen.getByRole("button", { name: "对比" }));

 await waitFor(() => expect(mockedApi.fetchCompare).toHaveBeenCalled());
 expect(screen.getByText("结论摘要卡片")).toBeInTheDocument();
 expect(screen.getByText("更稳健")).toBeInTheDocument();
 expect(screen.getByText(/成本与流动性对比/)).toBeInTheDocument();
 });

 test("首页空结果时也会展示空态", async () => {
 mockedApi.fetchFunds.mockResolvedValueOnce({ items: [], total:0, page:1, page_size:20 });
 render(<App />);

 await waitFor(() => expect(mockedApi.fetchFunds).toHaveBeenCalled());
 expect(screen.getByText("暂无推荐结果")).toBeInTheDocument();
 });

 test("首页和选基页展示风险等级与类型信息", async () => {
 render(<App />);

 await waitFor(() => expect(mockedApi.fetchFunds).toHaveBeenCalled());
 expect(screen.getByText("当前Top1代码：510300")).toBeInTheDocument();

 fireEvent.click(screen.getByRole("button", { name: "选基" }));
 expect(await screen.findByText("510300")).toBeInTheDocument();
 expect(screen.getAllByText("宽基ETF").length).toBeGreaterThan(0);
 expect(screen.getByText("状态")).toBeInTheDocument();
 });

 test("对比页展示风险等级和图形化对照模块", async () => {
 mockedApi.fetchWatchlist.mockResolvedValue([
  { ...makeFund("510300", 91), alerts: ["提醒"] },
  { ...makeFund("005827", 87), alerts: ["提醒"] },
 ] as WatchlistScore[]);

 render(<App />);
 fireEvent.click(screen.getByRole("button", { name: "对比" }));

 await waitFor(() => expect(mockedApi.fetchCompare).toHaveBeenCalled());
 expect(screen.getByText("收益 / 回撤对照")).toBeInTheDocument();
 expect(screen.getByText("因子雷达图（分项条）")).toBeInTheDocument();
 expect(screen.getAllByText(/极高流动|高流动性/).length).toBeGreaterThan(0);
 });

 test("加入观察池失败时展示错误提示", async () => {
 mockedApi.addWatchlist.mockRejectedValueOnce(new Error("加入观察池失败"));
 render(<App />);
 fireEvent.click(screen.getByRole("button", { name: "选基" }));

 const watchButtons = await screen.findAllByRole("button", { name: "加入观察池" });
 fireEvent.click(watchButtons[0]);

 await waitFor(() => {
  expect(screen.getByText("错误：加入观察池失败")).toBeInTheDocument();
 });
 });
});
