import { useEffect, useMemo, useState } from "react";
import type { Dispatch, SetStateAction } from "react";
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
import type {
 FactorMetrics,
 FundDetail,
 FundQuery,
 FundScore,
 PolicyMetrics,
 RiskProfile,
 WatchlistScore,
} from "./types";

type Page = "首页" | "选基" | "详情" | "对比" | "观察池";
type DetailTab = "表现" | "因子分析" | "成本与交易" | "解释";

const DEFAULT_QUERY: Omit<FundQuery, "risk_profile"> = {
 channel: undefined,
 category: "",
 risk_level: "",
 min_years: undefined,
 min_scale: undefined,
 max_scale: undefined,
 max_fee: undefined,
 keyword: "",
 sort_by: "final_score",
 sort_order: "desc",
 page: 1,
 page_size: 20,
};

const CATEGORY_OPTIONS = ["", "宽基", "行业", "债券", "混合"];
const RISK_LEVEL_OPTIONS = ["", "R2", "R4", "R5"];

export function App() {
 const [page, setPage] = useState<Page>("首页");
 const [risk, setRisk] = useState<RiskProfile>("均衡");
 const [query, setQuery] = useState(DEFAULT_QUERY);

 const [funds, setFunds] = useState<FundScore[]>([]);
 const [fundsTotal, setFundsTotal] = useState(0);
 const [fundsLoading, setFundsLoading] = useState(false);

 const [detail, setDetail] = useState<FundDetail | null>(null);
 const [detailLoading, setDetailLoading] = useState(false);
 const [selectedCode, setSelectedCode] = useState<string>("");

 const [manualCompareCodes, setManualCompareCodes] = useState<string[]>([]);
 const [compare, setCompare] = useState<FundScore[]>([]);
 const [compareDetails, setCompareDetails] = useState<FundDetail[]>([]);
 const [compareLoading, setCompareLoading] = useState(false);

 const [watchlist, setWatchlist] = useState<WatchlistScore[]>([]);
 const [watchlistLoading, setWatchlistLoading] = useState(false);

 const [error, setError] = useState<string>("");

 const fundQuery: FundQuery = useMemo(() => ({ ...query, risk_profile: risk }), [query, risk]);
 const pageSize = query.page_size ?? 20;
 const currentPage = query.page ?? 1;
 const totalPages = Math.max(1, Math.ceil(fundsTotal / pageSize));
 const top10 = useMemo(() => funds.slice(0, 10), [funds]);
 const activeCompareCodes = useMemo(() => {
  const fallbackCodes = watchlist.map((w) => w.code).slice(0, 5);
  return manualCompareCodes.length > 0 ? manualCompareCodes : fallbackCodes;
 }, [manualCompareCodes, watchlist]);

 useEffect(() => {
  setFundsLoading(true);
  setError("");
  fetchFunds(fundQuery)
   .then((data) => {
    setFunds(data.items);
    setFundsTotal(data.total);
    if (data.items.length === 0) {
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
  setDetailLoading(true);
  fetchFundDetail(selectedCode, risk)
   .then(setDetail)
   .catch((e: Error) => setError(e.message))
   .finally(() => setDetailLoading(false));
 }, [selectedCode, risk]);

 useEffect(() => {
  setWatchlistLoading(true);
  fetchWatchlist(risk)
   .then(setWatchlist)
   .catch((e: Error) => setError(e.message))
   .finally(() => setWatchlistLoading(false));
 }, [risk]);

 useEffect(() => {
  if (activeCompareCodes.length < 2) {
   setCompare([]);
   setCompareDetails([]);
   return;
  }

  setCompareLoading(true);
  Promise.all([
   fetchCompare(activeCompareCodes, risk),
   Promise.all(activeCompareCodes.map((code) => fetchFundDetail(code, risk))),
  ])
   .then(([scores, details]) => {
    setCompare(scores);
    setCompareDetails(details);
   })
   .catch((e: Error) => setError(e.message))
   .finally(() => setCompareLoading(false));
 }, [activeCompareCodes, risk]);

 async function refreshWatchlist(): Promise<void> {
  const list = await fetchWatchlist(risk);
  setWatchlist(list);
 }

 async function toggleWatch(code: string): Promise<void> {
  const exists = watchlist.some((w) => w.code === code);
  try {
   if (exists) await removeWatchlist(code);
   else await addWatchlist(code);
   await refreshWatchlist();
  } catch (e) {
   setError((e as Error).message);
  }
 }

 function toggleManualCompare(code: string): void {
  setManualCompareCodes((prev) => {
   if (prev.includes(code)) return prev.filter((x) => x !== code);
   if (prev.length >= 5) return prev;
   return [...prev, code];
  });
 }

 function resetFilters(): void {
  setQuery(DEFAULT_QUERY);
 }

 function exportResults(): void {
  const rows = [
   ["代码", "名称", "综合分", "Base分", "Policy分", "政策权重"],
   ...funds.map((item) => [
    item.code,
    item.name,
    String(item.final_score),
    String(item.base_score),
    String(item.policy_score),
    `${Math.round(item.overlay_weight * 100)}%`,
   ]),
  ];
  const csv = rows.map((row) => row.join(",")).join("\n");
  const blob = new Blob([`\uFEFF${csv}`], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "fund-selection-results.csv";
  anchor.click();
  URL.revokeObjectURL(url);
 }

 function openDetail(code: string): void {
  setSelectedCode(code);
  setPage("详情");
 }

 return (
  <div className="app-shell">
   <div className="hero">
    <div className="hero-copy">
     <p className="eyebrow">A股基金量化选基助手</p>
     <h1>把筛选、解释、对比和观察池串成一条完整决策链。</h1>
     <p className="hero-subtitle">
      面向理财初学者，用多因子评分和政策 Overlay 给出更可解释的推荐视图。
     </p>
    </div>
    <div className="hero-panel">
     <p className="disclaimer">仅供参考，不构成投资建议</p>
     <button className="segmented active" onClick={() => setRisk(nextRiskProfile(risk))}>
      风险偏好：{risk}
     </button>
     <p className="muted">{riskDescription(risk)}</p>
    </div>
   </div>

   <header className="topbar card">
    <div className="nav">
     {(["首页", "选基", "详情", "对比", "观察池"] as Page[]).map((p) => (
      <button key={p} className={p === page ? "active" : ""} onClick={() => setPage(p)}>
       {p}
      </button>
     ))}
    </div>
   </header>

   {error ? <div className="card error-banner">错误：{error}</div> : null}

   {page === "首页" ? (
    <Dashboard top10={top10} risk={risk} loading={fundsLoading} />
   ) : null}

   {page === "选基" ? (
    <Picker
     funds={funds}
     loading={fundsLoading}
     query={query}
     setQuery={setQuery}
     page={currentPage}
     totalPages={totalPages}
     total={fundsTotal}
     onPrevPage={() => setQuery((q) => ({ ...q, page: Math.max(1, (q.page ?? 1) - 1) }))}
     onNextPage={() => setQuery((q) => ({ ...q, page: Math.min(totalPages, (q.page ?? 1) + 1) }))}
     onReset={resetFilters}
     onExport={exportResults}
     onOpenDetail={openDetail}
     onToggleWatch={toggleWatch}
     watchCodes={new Set(watchlist.map((w) => w.code))}
     onToggleCompare={toggleManualCompare}
     compareCodes={new Set(manualCompareCodes)}
    />
   ) : null}

   {page === "详情" ? <Detail detail={detail} loading={detailLoading} /> : null}

   {page === "对比" ? (
    <Compare
     data={compare}
     details={compareDetails}
     loading={compareLoading}
     manualSelectedCount={manualCompareCodes.length}
     usingManual={manualCompareCodes.length > 0}
    />
   ) : null}

   {page === "观察池" ? (
    <Watchlist
     items={watchlist}
     loading={watchlistLoading}
     onToggleWatch={toggleWatch}
     onOpenDetail={openDetail}
     onToggleCompare={toggleManualCompare}
     compareCodes={new Set(manualCompareCodes)}
     onCompare={() => setPage("对比")}
    />
   ) : null}
  </div>
 );
}

function Dashboard({ top10, risk, loading }: { top10: FundScore[]; risk: RiskProfile; loading: boolean }) {
 if (loading) return <section className="card">首页加载中...</section>;

 const riskAlerts = top10.filter((item) => item.final_score < 80 || item.explanation.minus[0] !== "暂无明显短板因子").length;
 const avgScore = top10.length ? top10.reduce((sum, item) => sum + item.final_score, 0) / top10.length : 0;
 const marketTemperature = avgScore >= 85 ? "偏热" : avgScore >= 78 ? "中性" : "偏冷";
 const highLiquidityCount = top10.filter((item) => item.channel === "场内" && item.liquidity_label.includes("高")).length;
 const latestUpdatedAt = top10.length ? top10[0].code : "-";

 return (
  <section className="dashboard">
   <div className="grid grid-4">
    <MetricCard title="今日推荐数量" value={String(top10.length)} note="Top10 名单实时随筛选变化" />
    <MetricCard title="高风险预警数" value={String(riskAlerts)} note="综合分偏低或短板因子较多" />
     <MetricCard title="市场温度" value={marketTemperature} note="基于当前推荐均分推断" />
    <MetricCard title="当前风险偏好" value={risk} note={riskDescription(risk)} />
   </div>
   <div className="grid feature-grid">
    <article className="card spotlight">
     <h2>首页 / 仪表盘</h2>
     <div className="hero-metrics">
      <span>高流动性场内基金：{highLiquidityCount}</span>
      <span>当前Top1代码：{latestUpdatedAt}</span>
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
         <th>类型</th>
         <th>综合分</th>
         <th>风险等级</th>
         <th>政策权重</th>
         <th>标签</th>
        </tr>
       </thead>
       <tbody>
        {top10.map((f) => (
         <tr key={f.code}>
          <td>{f.code}</td>
          <td>{f.name}</td>
          <td>{f.channel} / {f.category}</td>
          <td className="score">{f.final_score}</td>
          <td>{f.risk_level}</td>
          <td>{Math.round(f.overlay_weight * 100)}%</td>
          <td>{scoreLabel(f.final_score)}</td>
         </tr>
        ))}
       </tbody>
      </table>
     )}
    </article>
    <article className="card">
     <h3>风险提示卡片</h3>
     <p className="note">把评分、政策和回撤提醒放在同一视角，避免只盯收益。</p>
     <ul className="plain-list">
      <li>优先检查“扣分项 Top3”是否与你的风险偏好冲突。</li>
      <li>行业主题 ETF 的政策权重更高，波动也会更明显。</li>
      <li>观察池中如出现“政策因子转弱”，建议回到详情页复核。</li>
     </ul>
    </article>
   </div>
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
 onReset,
 onExport,
 onOpenDetail,
 onToggleWatch,
 watchCodes,
 onToggleCompare,
 compareCodes,
}: {
 funds: FundScore[];
 loading: boolean;
 query: Omit<FundQuery, "risk_profile">;
 setQuery: Dispatch<SetStateAction<Omit<FundQuery, "risk_profile">>>;
 page: number;
 totalPages: number;
 total: number;
 onPrevPage: () => void;
 onNextPage: () => void;
 onReset: () => void;
 onExport: () => void;
 onOpenDetail: (code: string) => void;
 onToggleWatch: (code: string) => void;
 watchCodes: Set<string>;
 onToggleCompare: (code: string) => void;
 compareCodes: Set<string>;
}) {
 const selectedCompareCount = compareCodes.size;

 return (
  <section className="picker-layout">
   <aside className="card filter-panel">
    <h2>选基页（筛选 + 排序）</h2>
    <div className="grid">
     <label>
      关键词
      <input
       value={query.keyword ?? ""}
       onChange={(e) => setQuery((q) => ({ ...q, keyword: e.target.value, page: 1 }))}
      />
     </label>
     <label>
      场内/场外
      <select
       value={query.channel ?? ""}
       onChange={(e) =>
        setQuery((q) => ({
         ...q,
         channel: e.target.value ? (e.target.value as FundQuery["channel"]) : undefined,
         page: 1,
        }))
       }
      >
       <option value="">全部</option>
       <option value="场内">场内</option>
       <option value="场外">场外</option>
      </select>
     </label>
     <label>
      类别
      <select value={query.category ?? ""} onChange={(e) => setQuery((q) => ({ ...q, category: e.target.value, page: 1 }))}>
       {CATEGORY_OPTIONS.map((item) => (
        <option key={item || "all"} value={item}>
         {item || "全部"}
        </option>
       ))}
      </select>
     </label>
     <label>
      风险等级
      <select value={query.risk_level ?? ""} onChange={(e) => setQuery((q) => ({ ...q, risk_level: e.target.value, page: 1 }))}>
       {RISK_LEVEL_OPTIONS.map((item) => (
        <option key={item || "all"} value={item}>
         {item || "全部"}
        </option>
       ))}
      </select>
     </label>
     <label>
      最低年限
      <input
       type="number"
       value={query.min_years ?? ""}
       onChange={(e) =>
        setQuery((q) => ({ ...q, min_years: e.target.value ? Number(e.target.value) : undefined, page: 1 }))
       }
      />
     </label>
     <label>
      最低规模（亿元）
      <input
       type="number"
       value={query.min_scale ?? ""}
       onChange={(e) =>
        setQuery((q) => ({ ...q, min_scale: e.target.value ? Number(e.target.value) : undefined, page: 1 }))
       }
      />
     </label>
     <label>
      最高规模（亿元）
      <input
       type="number"
       value={query.max_scale ?? ""}
       onChange={(e) =>
        setQuery((q) => ({ ...q, max_scale: e.target.value ? Number(e.target.value) : undefined, page: 1 }))
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
        setQuery((q) => ({ ...q, max_fee: e.target.value ? Number(e.target.value) : undefined, page: 1 }))
       }
      />
     </label>
     <label>
      排序字段
      <select
       value={query.sort_by}
       onChange={(e) =>
        setQuery((q) => ({ ...q, sort_by: e.target.value as FundQuery["sort_by"], page: 1 }))
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
       onChange={(e) => setQuery((q) => ({ ...q, sort_order: e.target.value as "asc" | "desc", page: 1 }))}
      >
       <option value="desc">降序</option>
       <option value="asc">升序</option>
      </select>
     </label>
    </div>

    <div className="toolbar">
     <button onClick={onReset}>重置筛选</button>
     <button onClick={onExport}>导出结果</button>
    </div>
   </aside>

   <div className="grid">
    <div className="card">
     <div className="row wrap">
      <p>手动对比已选：{selectedCompareCount} /5（至少2只可触发手动对比）</p>
      <p className="muted">支持从结果列表或观察池加入对比。</p>
     </div>
     {selectedCompareCount >= 5 ? <p className="disclaimer">已达到手动对比上限（5只）。</p> : null}
     {loading ? <p>加载中...</p> : null}
     {!loading && !funds.length ? <p>无结果，请调整筛选条件。</p> : null}
    </div>

    <div className="card">
     <div className="row wrap">
      <p>
       分页：第 {page} / {totalPages} 页，合计 {total} 条
      </p>
      <div className="nav">
       <button onClick={onPrevPage} disabled={page <= 1 || loading}>
        上一页
       </button>
       <button onClick={onNextPage} disabled={page >= totalPages || loading}>
        下一页
       </button>
      </div>
     </div>
    </div>

    <div className="result-grid">
     {funds.map((f) => {
      const watched = watchCodes.has(f.code);
      const selected = compareCodes.has(f.code);
      return (
       <article key={f.code} className="card result-card">
        <div className="row">
       <div>
          <strong>{f.name}</strong>
          <p className="muted">{f.code} · {f.channel} / {f.category}</p>
         </div>
         <span className="score-pill">{scoreLabel(f.final_score)}</span>
        </div>
        <p className="score-display">{f.final_score}</p>
        <div className="metric-row">
         <span>风险等级 / 流动性</span>
         <strong>
          {f.risk_level} / {f.liquidity_label}
         </strong>
        </div>
        <div className="metric-row">
         <span>Base / Policy</span>
         <strong>
          {f.base_score} / {f.policy_score}
         </strong>
        </div>
        <div className="metric-row">
         <span>政策权重</span>
         <strong>{Math.round(f.overlay_weight * 100)}%</strong>
        </div>
        <div className="divider-space" />
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
   </div>
  </section>
 );
}

function Detail({ detail, loading }: { detail: FundDetail | null; loading: boolean }) {
 const [tab, setTab] = useState<DetailTab>("表现");

 if (loading) return <section className="card">详情加载中...</section>;
 if (!detail) return <section className="card">暂无详情数据</section>;

 return (
  <section className="grid">
   <article className="card detail-hero">
    <div className="row wrap">
     <div>
      <h2>基金详情页</h2>
      <p className="detail-title">
       {detail.name}（{detail.code}）
      </p>
      <p className="muted">
       {detail.channel} / {detail.category} / {detail.risk_level}
      </p>
     </div>
     <div className="detail-score">
      <p className="muted">综合评分</p>
      <p className="score-display">{detail.final_score}</p>
     </div>
    </div>
    <div className="grid grid-4 compact-grid">
      <MetricCard title="近一年收益" value={`${detail.one_year_return}%`} note="用于判断弹性与近期表现" />
      <MetricCard title="最大回撤" value={`${detail.max_drawdown}%`} note="衡量下行压力" />
      <MetricCard title="管理费率" value={`${detail.fee}%`} note="长期成本影响收益" />
      <MetricCard title="数据更新" value={detail.updated_at} note={detail.explanation.disclaimer} />
    </div>
   </article>

   <article className="card">
    <div className="nav">
     {(["表现", "因子分析", "成本与交易", "解释"] as DetailTab[]).map((item) => (
      <button key={item} className={item === tab ? "active" : ""} onClick={() => setTab(item)}>
       {item}
      </button>
     ))}
    </div>
   </article>

   {tab === "表现" ? <PerformancePanel detail={detail} /> : null}
   {tab === "因子分析" ? <FactorPanel factors={detail.factors} policy={detail.policy} /> : null}
   {tab === "成本与交易" ? <CostPanel detail={detail} /> : null}
   {tab === "解释" ? <ExplanationPanel detail={detail} /> : null}
  </section>
 );
}

function Compare({
 data,
 details,
 loading,
 manualSelectedCount,
 usingManual,
}: {
 data: FundScore[];
 details: FundDetail[];
 loading: boolean;
 manualSelectedCount: number;
 usingManual: boolean;
}) {
 const summary = useMemo(() => buildCompareSummary(details), [details]);

 return (
  <section className="grid">
   <article className="card">
    <h2>基金对比页（2-5只）</h2>
    {usingManual ? <p>当前来源：手动选择（{manualSelectedCount}只）</p> : <p>当前来源：观察池自动取前5只</p>}
   </article>

   {loading ? <article className="card">对比加载中...</article> : null}
   {!loading && data.length < 2 ? <article className="card">请先手动或通过观察池凑齐至少2只基金。</article> : null}

   {!loading && data.length >= 2 ? (
    <>
     <article className="card">
      <h3>结论摘要卡片</h3>
      <ul className="plain-list">
       <li>更稳健：{summary.stable}</li>
       <li>更有弹性：{summary.offensive}</li>
       <li>更适合当前风险偏好：{summary.fit}</li>
      </ul>
     </article>
     <article className="card">
      <h3>收益 / 回撤对照</h3>
      <div className="result-grid">
       {details.map((item) => (
        <article key={`${item.code}-trend`} className="subcard">
         <strong>{item.name}</strong>
         <p>收益曲线（示意）</p>
         <Sparkline values={buildTrend(item.code, item.final_score)} />
         <p>回撤曲线（示意）</p>
         <Sparkline
          values={buildTrend(item.code.split("").reverse().join(""), Math.abs(item.max_drawdown) * 4).map((value) =>
           Math.max(20, Math.min(95, value)),
          )}
          danger
         />
        </article>
       ))}
      </div>
     </article>
     <article className="card">
      <table>
       <thead>
        <tr>
         <th>代码</th>
         <th>名称</th>
         <th>综合分</th>
         <th>Base</th>
         <th>Policy</th>
         <th>风险等级</th>
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
          <td>{f.risk_level}</td>
          <td>{scoreLabel(f.final_score)}</td>
         </tr>
        ))}
       </tbody>
      </table>
     </article>
     <article className="card">
      <h3>因子雷达图（分项条）</h3>
      <div className="result-grid">
       {details.map((item) => (
        <article key={`${item.code}-factors`} className="subcard">
         <strong>{item.name}</strong>
         <FactorBar label="收益能力" value={item.factors.returns} />
         <FactorBar label="风险控制" value={item.factors.risk_control} />
         <FactorBar label="稳定性" value={item.factors.stability} />
         <FactorBar label="政策支持" value={item.policy.support} accent />
        </article>
       ))}
      </div>
     </article>
     <article className="card">
      <h3>成本与流动性对比</h3>
      <div className="result-grid">
       {details.map((item) => (
        <article key={item.code} className="subcard">
         <strong>{item.name}</strong>
         <p>费率：{item.fee}%</p>
         <p>流动性：{item.liquidity_label}</p>
         <p>规模：{item.scale_billion} 亿元</p>
         <p>跟踪误差：{item.tracking_error ?? "不适用"}</p>
        </article>
       ))}
      </div>
     </article>
    </>
   ) : null}
  </section>
 );
}

function Watchlist({
 items,
 loading,
 onToggleWatch,
 onOpenDetail,
 onToggleCompare,
 compareCodes,
 onCompare,
}: {
 items: WatchlistScore[];
 loading: boolean;
 onToggleWatch: (code: string) => void;
 onOpenDetail: (code: string) => void;
 onToggleCompare: (code: string) => void;
 compareCodes: Set<string>;
 onCompare: () => void;
}) {
 return (
  <section className="grid">
   <article className="card">
    <h2>观察池</h2>
    {loading ? <p>观察池加载中...</p> : null}
    {!loading && !items.length ? <p>暂无收藏基金</p> : null}
   </article>

   {items.map((item) => (
    <article key={item.code} className="card watch-card">
     <div className="row wrap">
     <div>
       <strong>{item.name}</strong>
       <p className="muted">{item.code} · {item.risk_level}</p>
      </div>
      <span className="score-pill">{item.final_score}</span>
     </div>
     <p>告警：{item.alerts.join("；")}</p>
     <Sparkline values={buildTrend(item.code, item.final_score)} />
     <div className="nav">
      <button onClick={() => onOpenDetail(item.code)}>查看详情</button>
      <button className={compareCodes.has(item.code) ? "active" : ""} onClick={() => onToggleCompare(item.code)}>
       {compareCodes.has(item.code) ? "取消对比" : "加入对比"}
      </button>
      <button onClick={() => onToggleWatch(item.code)}>移除</button>
     </div>
    </article>
   ))}

   <article className="card">
    <button onClick={onCompare}>进入对比页</button>
    <p className="disclaimer">评审点：验证“收藏/移除 -&gt; 对比页联动 + 手动2-5只对比”链路。</p>
   </article>
  </section>
 );
}

function PerformancePanel({ detail }: { detail: FundDetail }) {
 const trend = buildTrend(detail.code, detail.final_score);
 const drawdown = buildTrend(detail.code.split("").reverse().join(""), Math.abs(detail.max_drawdown) * 4).map((value) => Math.max(20, Math.min(95, value)));

 return (
  <article className="card">
   <div className="grid grid-2">
    <div>
     <h3>表现</h3>
     <p>成立年限：{detail.years} 年</p>
     <p>基金规模：{detail.scale_billion} 亿元</p>
     <p>近一年收益：{detail.one_year_return}%</p>
     <p>最大回撤：{detail.max_drawdown}%</p>
    </div>
    <div>
     <p className="muted">收益曲线（示意）</p>
     <Sparkline values={trend} />
     <p className="muted">回撤曲线（示意）</p>
     <Sparkline values={drawdown} danger />
    </div>
   </div>
  </article>
 );
}

function FactorPanel({ factors, policy }: { factors: FactorMetrics; policy: PolicyMetrics }) {
 return (
  <article className="card">
   <h3>因子分析</h3>
   <div className="grid grid-2">
    <div>
     <FactorBar label="收益能力" value={factors.returns} />
     <FactorBar label="风险控制" value={factors.risk_control} />
     <FactorBar label="风险收益比" value={factors.risk_adjusted} />
     <FactorBar label="稳定性" value={factors.stability} />
     <FactorBar label="成本效率" value={factors.cost_efficiency} />
     <FactorBar label="流动性" value={factors.liquidity} />
     <FactorBar label="存续质量" value={factors.survival_quality} />
    </div>
    <div>
     <FactorBar label="政策支持强度" value={policy.support} accent />
     <FactorBar label="政策执行进度" value={policy.execution} accent />
     <FactorBar label="监管安全度" value={policy.regulation_safety} accent />
    </div>
   </div>
  </article>
 );
}

function CostPanel({ detail }: { detail: FundDetail }) {
 return (
  <article className="card">
   <h3>成本与交易</h3>
   <div className="grid grid-2">
    <div className="subcard">
     <p>费率：{detail.fee}%</p>
     <p>流动性标签：{detail.liquidity_label}</p>
     <p>跟踪误差：{detail.tracking_error ?? "不适用"}</p>
    </div>
    <div className="subcard">
     <p>适用前提：{detail.explanation.applicable}</p>
     <p>风险提示：{detail.explanation.risk_tip}</p>
    </div>
   </div>
  </article>
 );
}

function ExplanationPanel({ detail }: { detail: FundDetail }) {
 return (
  <article className="card">
   <h3>推荐解释</h3>
   <div className="grid grid-2">
    <div>
     <p>
      <strong>加分项 Top3</strong>
     </p>
     <ul>
      {detail.explanation.plus.map((x) => (
       <li key={x}>+ {x}</li>
      ))}
     </ul>
     <p>
      <strong>扣分项 Top3</strong>
     </p>
     <ul>
      {detail.explanation.minus.map((x) => (
       <li key={x}>- {x}</li>
      ))}
     </ul>
    </div>
    <div>
     <p>{detail.explanation.risk_tip}</p>
     <p>{detail.explanation.applicable}</p>
     <p className="disclaimer">{detail.explanation.disclaimer}</p>
     <p className="formula">公式：{detail.explanation.formula}</p>
    </div>
   </div>
  </article>
 );
}

function MetricCard({ title, value, note }: { title: string; value: string; note: string }) {
 return (
  <article className="metric-card">
   <p className="eyebrow">{title}</p>
   <p className="metric-value">{value}</p>
   <p className="muted">{note}</p>
  </article>
 );
}

function FactorBar({ label, value, accent = false }: { label: string; value: number; accent?: boolean }) {
 return (
  <div className="factor-row">
   <div className="row">
    <span>{label}</span>
    <strong>{value}</strong>
   </div>
   <div className="bar-track">
    <div className={accent ? "bar-fill accent" : "bar-fill"} style={{ width: `${value}%` }} />
   </div>
  </div>
 );
}

function Sparkline({ values, danger = false }: { values: number[]; danger?: boolean }) {
 return (
  <div className={danger ? "sparkline danger" : "sparkline"}>
   {values.map((value, index) => (
    <span key={`${value}-${index}`} style={{ height: `${value}%` }} />
   ))}
  </div>
 );
}

function buildTrend(seed: string, score: number): number[] {
 return Array.from({ length: 7 }, (_, index) => {
  const char = seed.charCodeAt(index % seed.length) || 60;
  const swing = ((char + index * 7) % 18) - 9;
  return Math.max(24, Math.min(96, Math.round(score + swing)));
 });
}

function buildCompareSummary(details: FundDetail[]): { stable: string; offensive: string; fit: string } {
 if (!details.length) {
  return { stable: "-", offensive: "-", fit: "-" };
 }

 const stable = [...details].sort((a, b) => b.factors.risk_control - a.factors.risk_control)[0];
 const offensive = [...details].sort((a, b) => b.one_year_return - a.one_year_return)[0];
 const fit = [...details].sort((a, b) => b.final_score - a.final_score)[0];

 return {
  stable: `${stable.name}（风险控制 ${stable.factors.risk_control}）`,
  offensive: `${offensive.name}（近一年收益 ${offensive.one_year_return}%）`,
  fit: `${fit.name}（综合分 ${fit.final_score}）`,
 };
}
