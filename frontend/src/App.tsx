import { useEffect, useMemo, useState } from "react";
import {
 addWatchlist,
 fetchCompare,
 fetchFundDetail,
 fetchFunds,
 fetchWatchlist,
 removeWatchlist,
} from "./api";
import { scoreLabel } from "./lib/score";
import { nextRiskProfile, riskDescription } from "./state/risk";
import type { FundDetail, FundQuery, FundScore, RiskProfile, WatchlistScore } from "./types";

type Page = "首页" | "选基" | "详情" | "对比" | "观察池";

const DEFAULT_QUERY: Omit<FundQuery, "risk_profile"> = {
 channel: undefined,
 category: "",
 min_years: undefined,
 max_fee: undefined,
 keyword: "",
 sort_by: "final_score",
 sort_order: "desc",
 page:1,
 page_size:20,
};

export function App() {
 const [page, setPage] = useState<Page>("首页");
 const [risk, setRisk] = useState<RiskProfile>("均衡");
 const [query, setQuery] = useState(DEFAULT_QUERY);

 const [funds, setFunds] = useState<FundScore[]>([]);
 const [fundsTotal, setFundsTotal] = useState(0);
 const [fundsLoading, setFundsLoading] = useState(false);

 const [detail, setDetail] = useState<FundDetail | null>(null);
 const [selectedCode, setSelectedCode] = useState<string>("");

 const [manualCompareCodes, setManualCompareCodes] = useState<string[]>([]);
 const [compare, setCompare] = useState<FundScore[]>([]);

 const [watchlist, setWatchlist] = useState<WatchlistScore[]>([]);
 const [watchlistLoading, setWatchlistLoading] = useState(false);

 const [error, setError] = useState<string>("");

 const fundQuery: FundQuery = useMemo(() => ({ ...query, risk_profile: risk }), [query, risk]);

 useEffect(() => {
 setFundsLoading(true);
 setError("");
 fetchFunds(fundQuery)
 .then((data) => {
 setFunds(data.items);
 setFundsTotal(data.total);
 if (data.items.length ===0) {
 setDetail(null);
 return;
 }
 if (!selectedCode || !data.items.some((x) => x.code === selectedCode)) {
 setSelectedCode(data.items[0].code);
 }
 })
 .catch((e: Error) => setError(e.message))
 .finally(() => setFundsLoading(false));
 }, [fundQuery]);

 useEffect(() => {
 if (!selectedCode) {
 setDetail(null);
 return;
 }
 fetchFundDetail(selectedCode, risk)
 .then(setDetail)
 .catch((e: Error) => setError(e.message));
 }, [selectedCode, risk]);

 useEffect(() => {
 setWatchlistLoading(true);
 fetchWatchlist(risk)
 .then(setWatchlist)
 .catch((e: Error) => setError(e.message))
 .finally(() => setWatchlistLoading(false));
 }, [risk]);

 useEffect(() => {
 const fallbackCodes = watchlist.map((w) => w.code).slice(0,5);
 const codes = manualCompareCodes.length >0 ? manualCompareCodes : fallbackCodes;

 if (codes.length >=2) {
 fetchCompare(codes, risk).then(setCompare).catch((e: Error) => setError(e.message));
 } else {
 setCompare([]);
 }
 }, [manualCompareCodes, watchlist, risk]);

 const top10 = useMemo(() => funds.slice(0,10), [funds]);
 const pageSize = query.page_size ??20;
 const currentPage = query.page ??1;
 const totalPages = Math.max(1, Math.ceil(fundsTotal / pageSize));

 async function toggleWatch(code: string): Promise<void> {
 const exists = watchlist.some((w) => w.code === code);
 try {
 if (exists) await removeWatchlist(code);
 else await addWatchlist(code);
 const list = await fetchWatchlist(risk);
 setWatchlist(list);
 } catch (e) {
 setError((e as Error).message);
 }
 }

 function toggleManualCompare(code: string): void {
 setManualCompareCodes((prev) => {
 if (prev.includes(code)) return prev.filter((x) => x !== code);
 if (prev.length >=5) return prev;
 return [...prev, code];
 });
 }

 return (
 <div className="container">
 <header className="card">
 <div className="row">
 <h1>基金量化选基助手 ·评审会版本</h1>
 <p className="disclaimer">仅供参考，不构成投资建议</p>
 </div>
 <div className="nav">
 {(["首页", "选基", "详情", "对比", "观察池"] as Page[]).map((p) => (
 <button key={p} className={p === page ? "active" : ""} onClick={() => setPage(p)}>
 {p}
 </button>
 ))}
 <button onClick={() => setRisk(nextRiskProfile(risk))}>风险偏好：{risk}</button>
 </div>
 <p>{riskDescription(risk)}</p>
 </header>

 {error ? <div className="card">错误：{error}</div> : null}

 {page === "首页" ? <Dashboard top10={top10} risk={risk} loading={fundsLoading} /> : null}
 {page === "选基" ? (
 <Picker
 funds={funds}
 loading={fundsLoading}
 query={query}
 setQuery={setQuery}
 page={currentPage}
 totalPages={totalPages}
 total={fundsTotal}
 onPrevPage={() => setQuery((q) => ({ ...q, page: Math.max(1, (q.page ??1) -1) }))}
 onNextPage={() => setQuery((q) => ({ ...q, page: Math.min(totalPages, (q.page ??1) +1) }))}
 onOpenDetail={(code) => {
 setSelectedCode(code);
 setPage("详情");
 }}
 onToggleWatch={toggleWatch}
 watchCodes={new Set(watchlist.map((w) => w.code))}
 onToggleCompare={toggleManualCompare}
 compareCodes={new Set(manualCompareCodes)}
 />
 ) : null}
 {page === "详情" ? <Detail detail={detail} loading={fundsLoading} /> : null}
 {page === "对比" ? (
 <Compare data={compare} manualSelectedCount={manualCompareCodes.length} usingManual={manualCompareCodes.length >0} />
 ) : null}
 {page === "观察池" ? (
 <Watchlist
 items={watchlist}
 loading={watchlistLoading}
 onToggleWatch={toggleWatch}
 onCompare={() => setPage("对比")}
 />
 ) : null}
 </div>
 );
}

function Dashboard({ top10, risk, loading }: { top10: FundScore[]; risk: RiskProfile; loading: boolean }) {
 if (loading) return <section className="card">首页加载中...</section>;
 return (
 <section className="card">
 <h2>首页 / 仪表盘</h2>
 <div className="grid grid-2">
 <article className="card">
 <h3>今日推荐数量</h3>
 <p className="score">{top10.length}</p>
 </article>
 <article className="card">
 <h3>当前风险偏好</h3>
 <p className="score">{risk}</p>
 </article>
 </div>
 <p>今日推荐 Top10（含解释标签）</p>
 {!top10.length ? (
 <p>暂无推荐结果</p>
 ) : (
 <table>
 <thead>
 <tr>
 <th>代码</th>
 <th>名称</th>
 <th>综合分</th>
 <th>政策权重</th>
 <th>标签</th>
 </tr>
 </thead>
 <tbody>
 {top10.map((f) => (
 <tr key={f.code}>
 <td>{f.code}</td>
 <td>{f.name}</td>
 <td className="score">{f.final_score}</td>
 <td>{Math.round(f.overlay_weight *100)}%</td>
 <td>{scoreLabel(f.final_score)}</td>
 </tr>
 ))}
 </tbody>
 </table>
 )}
 </section>
 );
}

function Picker({
 funds,
 loading,
 query,
 setQuery,
 page,
 totalPages,
 total,
 onPrevPage,
 onNextPage,
 onOpenDetail,
 onToggleWatch,
 watchCodes,
 onToggleCompare,
 compareCodes,
}: {
 funds: FundScore[];
 loading: boolean;
 query: Omit<FundQuery, "risk_profile">;
 setQuery: React.Dispatch<React.SetStateAction<Omit<FundQuery, "risk_profile">>>;
 page: number;
 totalPages: number;
 total: number;
 onPrevPage: () => void;
 onNextPage: () => void;
 onOpenDetail: (code: string) => void;
 onToggleWatch: (code: string) => void;
 watchCodes: Set<string>;
 onToggleCompare: (code: string) => void;
 compareCodes: Set<string>;
}) {
 const selectedCompareCount = compareCodes.size;

 return (
 <section className="card">
 <h2>选基页（筛选 + 排序）</h2>
 <div className="grid grid-2">
 <label>
关键词
 <input
 value={query.keyword ?? ""}
 onChange={(e) => setQuery((q) => ({ ...q, keyword: e.target.value, page:1 }))}
 />
 </label>
 <label>
 类别
 <input
 value={query.category ?? ""}
 onChange={(e) => setQuery((q) => ({ ...q, category: e.target.value, page:1 }))}
 />
 </label>
 <label>
 最低年限
 <input
 type="number"
 value={query.min_years ?? ""}
 onChange={(e) =>
 setQuery((q) => ({ ...q, min_years: e.target.value ? Number(e.target.value) : undefined, page:1 }))
 }
 />
 </label>
 <label>
最高费率
 <input
 type="number"
 step="0.01"
 value={query.max_fee ?? ""}
 onChange={(e) =>
 setQuery((q) => ({ ...q, max_fee: e.target.value ? Number(e.target.value) : undefined, page:1 }))
 }
 />
 </label>
 <label>
 排序字段
 <select
 value={query.sort_by}
 onChange={(e) =>
 setQuery((q) => ({ ...q, sort_by: e.target.value as FundQuery["sort_by"], page:1 }))
 }
 >
 <option value="final_score">综合分</option>
 <option value="base_score">Base分</option>
 <option value="policy_score">Policy分</option>
 <option value="one_year_return">近1年收益</option>
 <option value="max_drawdown">最大回撤</option>
 <option value="fee">费率</option>
 </select>
 </label>
 <label>
 排序方向
 <select
 value={query.sort_order}
 onChange={(e) => setQuery((q) => ({ ...q, sort_order: e.target.value as "asc" | "desc", page:1 }))}
 >
 <option value="desc">降序</option>
 <option value="asc">升序</option>
 </select>
 </label>
 </div>

 <div className="row">
 <p>手动对比已选：{selectedCompareCount} /5（至少2只可触发手动对比）</p>
 </div>
 {selectedCompareCount >=5 ? <p className="disclaimer">已达到手动对比上限（5只）。</p> : null}

 {loading ? <p>加载中...</p> : null}
 {!loading && !funds.length ? <p>无结果，请调整筛选条件。</p> : null}

 <div className="row">
 <p>
 分页：第 {page} / {totalPages} 页，合计 {total} 条
 </p>
 <div className="nav">
 <button onClick={onPrevPage} disabled={page <=1 || loading}>
 上一页
 </button>
 <button onClick={onNextPage} disabled={page >= totalPages || loading}>
 下一页
 </button>
 </div>
 </div>

 <div className="grid grid-2">
 {funds.map((f) => {
 const watched = watchCodes.has(f.code);
 const selected = compareCodes.has(f.code);
 return (
 <article key={f.code} className="card">
 <div className="row">
 <strong>{f.name}</strong>
 <span className="tag">{f.code}</span>
 </div>
 <p>
 综合分：<span className="score">{f.final_score}</span>
 </p>
 <p>
 Base / Policy：{f.base_score} / {f.policy_score}
 </p>
 <p>政策权重：{Math.round(f.overlay_weight *100)}%</p>
 <p>主要加分项：{f.explanation.plus[0]}</p>
 <p>主要扣分项：{f.explanation.minus[0]}</p>
 <div className="nav">
 <button onClick={() => onOpenDetail(f.code)}>查看详情</button>
 <button className={watched ? "active" : ""} onClick={() => onToggleWatch(f.code)}>
 {watched ? "移除观察池" : "加入观察池"}
 </button>
 <button className={selected ? "active" : ""} onClick={() => onToggleCompare(f.code)}>
 {selected ? "取消对比" : "加入对比"}
 </button>
 </div>
 </article>
 );
 })}
 </div>
 </section>
 );
}

function Detail({ detail, loading }: { detail: FundDetail | null; loading: boolean }) {
 if (loading) return <section className="card">详情加载中...</section>;
 if (!detail) return <section className="card">暂无详情数据</section>;
 return (
 <section className="card">
 <h2>基金详情页</h2>
 <div className="grid grid-2">
 <div>
 <p>
 <strong>{detail.name}</strong>（{detail.code}）
 </p>
 <p>
 类型：{detail.channel} / {detail.category}
 </p>
 <p>风险等级：{detail.risk_level}</p>
 <p>近一年收益：{detail.one_year_return}%</p>
 <p>最大回撤：{detail.max_drawdown}%</p>
 <p>费率：{detail.fee}%</p>
 <p>
 综合评分：<span className="score">{detail.final_score}</span>
 </p>
 </div>
 <div>
 <p>
 <strong>推荐解释</strong>
 </p>
 <ul>
 {detail.explanation.plus.map((x) => (
 <li key={x}>+ {x}</li>
 ))}
 {detail.explanation.minus.map((x) => (
 <li key={x}>- {x}</li>
 ))}
 </ul>
 <p>{detail.explanation.risk_tip}</p>
 <p className="disclaimer">公式：{detail.explanation.formula}</p>
 </div>
 </div>
 </section>
 );
}

function Compare({
 data,
 manualSelectedCount,
 usingManual,
}: {
 data: FundScore[];
 manualSelectedCount: number;
 usingManual: boolean;
}) {
 return (
 <section className="card">
 <h2>基金对比页（2-5只）</h2>
 {usingManual ? <p>当前来源：手动选择（{manualSelectedCount}只）</p> : <p>当前来源：观察池自动取前5只</p>}
 {data.length <2 ? (
 <p>请先手动或通过观察池凑齐至少2只基金。</p>
 ) : (
 <table>
 <thead>
 <tr>
 <th>代码</th>
 <th>名称</th>
 <th>综合分</th>
 <th>Base</th>
 <th>Policy</th>
 <th>结论</th>
 </tr>
 </thead>
 <tbody>
 {data.map((f) => (
 <tr key={f.code}>
 <td>{f.code}</td>
 <td>{f.name}</td>
 <td className="score">{f.final_score}</td>
 <td>{f.base_score}</td>
 <td>{f.policy_score}</td>
 <td>{scoreLabel(f.final_score)}</td>
 </tr>
 ))}
 </tbody>
 </table>
 )}
 </section>
 );
}

function Watchlist({
 items,
 loading,
 onToggleWatch,
 onCompare,
}: {
 items: WatchlistScore[];
 loading: boolean;
 onToggleWatch: (code: string) => void;
 onCompare: () => void;
}) {
 return (
 <section className="card">
 <h2>观察池</h2>
 {loading ? <p>观察池加载中...</p> : null}
 {!loading && !items.length ? <p>暂无收藏基金</p> : null}
 {items.map((item) => (
 <article key={item.code} className="card">
 <div className="row">
 <strong>{item.name}</strong>
 <span className="tag">{item.code}</span>
 </div>
 <p>
 综合分：<span className="score">{item.final_score}</span>
 </p>
 <p>告警：{item.alerts.join("；")}</p>
 <button onClick={() => onToggleWatch(item.code)}>移除</button>
 </article>
 ))}
 <button onClick={onCompare}>进入对比页</button>
 <p className="disclaimer">评审点：验证“收藏/移除 -&gt; 对比页联动 + 手动2-5只对比”链路。</p>
 </section>
 );
}
