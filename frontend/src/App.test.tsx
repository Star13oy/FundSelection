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
 final_score: score,
 base_score:80,
 policy_score:85,
 overlay_weight:0.15,
 explanation: {
 plus: ["政策支持"],
 minus: ["波动较高"],
 risk_tip: "注意回撤",
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
 one_year_return:12.3,
 max_drawdown:18.5,
 fee:0.5,
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
 expect(screen.getByRole("heading", { level:2, name: "选基页（筛选 + 排序）" })).toBeInTheDocument();

 fireEvent.click(screen.getByRole("button", { name: "观察池" }));
 expect(screen.getByRole("heading", { level:2, name: "观察池" })).toBeInTheDocument();

 fireEvent.click(screen.getByRole("button", { name: "对比" }));
 expect(screen.getByRole("heading", { level:2, name: "基金对比页（2-5只）" })).toBeInTheDocument();

 await waitFor(() => expect(mockedApi.fetchFunds).toHaveBeenCalled());
 });

 test("风险偏好切换会触发重新请求", async () => {
 render(<App />);

 await waitFor(() => expect(mockedApi.fetchFunds).toHaveBeenCalledTimes(1));
 fireEvent.click(screen.getByRole("button", { name: /风险偏好：均衡/ }));
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
 expect(screen.getByText(/近一年收益：12.3%/)).toBeInTheDocument();
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

 expect(screen.getByText("手动对比已选：5 /5（至少2只可触发手动对比）")).toBeInTheDocument();
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
 const prevButton = screen.getByRole("button", { name: "上一页" });
 expect(nextButton).toBeEnabled();

 fireEvent.click(nextButton);
 await waitFor(() => expect(mockedApi.fetchFunds).toHaveBeenCalledTimes(2));

 fireEvent.click(prevButton);
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

 expect(screen.getByRole("heading", { level:2, name: "基金对比页（2-5只）" })).toBeInTheDocument();
 });
});
