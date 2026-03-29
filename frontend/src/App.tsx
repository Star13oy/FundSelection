import { useEffect, useMemo, useState } from "react";
import type { Dispatch, ReactNode, SetStateAction } from "react";
import { addWatchlist, fetchCompare, fetchFundDetail, fetchFunds, fetchWatchlist, refreshMarket, removeWatchlist } from "./api.ts";
import type { FactorMetrics, FundDetail, FundQuery, FundScore, MarketSnapshot, PolicyMetrics, RiskProfile, WatchlistScore } from "./types.ts";

type Page = "首页" | "选基" | "详情" | "对比" | "观察池";
type DetailTab = "表现分析" | "因子分析" | "成本与交易" | "推荐理由";

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

const CATEGORIES = ["宽基", "行业", "债券", "混合"] as const;
const LEVELS = ["R2", "R4", "R5"] as const;
const RISKS = ["保守", "均衡", "进取"] as const satisfies readonly RiskProfile[];

export function App() {
 const [page, setPage] = useState<Page>("首页");
 const [risk, setRisk] = useState<RiskProfile>("均衡");
 const [query, setQuery] = useState(DEFAULT_QUERY);
 const [funds, setFunds] = useState<FundScore[]>([]);
 const [fundsTotal, setFundsTotal] = useState(0);
 const [fundsLoading, setFundsLoading] = useState(false);
 const [detail, setDetail] = useState<FundDetail | null>(null);
 const [detailLoading, setDetailLoading] = useState(false);
 const [selectedCode, setSelectedCode] = useState("");
 const [manualCompareCodes, setManualCompareCodes] = useState<string[]>([]);
 const [compare, setCompare] = useState<FundScore[]>([]);
 const [compareDetails, setCompareDetails] = useState<FundDetail[]>([]);
 const [compareLoading, setCompareLoading] = useState(false);
 const [watchlist, setWatchlist] = useState<WatchlistScore[]>([]);
 const [watchlistLoading, setWatchlistLoading] = useState(false);
 const [refreshingMarket, setRefreshingMarket] = useState(false);
 const [error, setError] = useState("");

 const fundQuery = useMemo(() => ({ ...query, risk_profile: risk }), [query, risk]);
 const currentPage = query.page ?? 1;
 const pageSize = query.page_size ?? 20;
 const totalPages = Math.max(1, Math.ceil(fundsTotal / pageSize));
 const top10 = useMemo(() => funds.slice(0, 10), [funds]);
 const activeCompareCodes = useMemo(() => {
  const fallback = watchlist.map((item) => item.code).slice(0, 5);
  return manualCompareCodes.length ? manualCompareCodes : fallback;
 }, [manualCompareCodes, watchlist]);

 useEffect(() => {
  setFundsLoading(true);
  setError("");
  fetchFunds(fundQuery)
   .then((data) => {
    setFunds(data.items);
    setFundsTotal(data.total);
    if (data.items.length && (!selectedCode || !data.items.some((item) => item.code === selectedCode))) setSelectedCode(data.items[0].code);
    if (!data.items.length) setDetail(null);
   })
   .catch((e: Error) => setError(e.message))
   .finally(() => setFundsLoading(false));
 }, [fundQuery]);

 useEffect(() => {
  if (!selectedCode) return;
  setDetailLoading(true);
  fetchFundDetail(selectedCode, risk).then(setDetail).catch((e: Error) => setError(e.message)).finally(() => setDetailLoading(false));
 }, [selectedCode, risk]);

 useEffect(() => {
  setWatchlistLoading(true);
  fetchWatchlist(risk).then(setWatchlist).catch((e: Error) => setError(e.message)).finally(() => setWatchlistLoading(false));
 }, [risk]);

 useEffect(() => {
  if (page !== "对比") return;
  if (activeCompareCodes.length < 2) {
   setCompare([]);
   setCompareDetails([]);
   return;
  }
  setCompareLoading(true);
  Promise.all([fetchCompare(activeCompareCodes, risk), Promise.all(activeCompareCodes.map((code) => fetchFundDetail(code, risk)))])
   .then(([scores, details]) => {
    setCompare(scores);
    setCompareDetails(details);
   })
   .catch((e: Error) => setError(e.message))
   .finally(() => setCompareLoading(false));
 }, [activeCompareCodes, risk, page]);

 async function refreshWatchlist() {
  setWatchlist(await fetchWatchlist(risk));
 }

 async function handleRefreshMarket() {
  try {
   setRefreshingMarket(true);
   setError("");
   await refreshMarket();
   const [fundData, watchData] = await Promise.all([fetchFunds(fundQuery), fetchWatchlist(risk)]);
   setFunds(fundData.items);
   setFundsTotal(fundData.total);
   setWatchlist(watchData);
   if (selectedCode) {
    setDetail(await fetchFundDetail(selectedCode, risk));
   }
  } catch (e) {
   setError((e as Error).message);
  } finally {
   setRefreshingMarket(false);
  }
 }

 async function toggleWatch(code: string) {
  try {
   if (watchlist.some((item) => item.code === code)) await removeWatchlist(code);
   else await addWatchlist(code);
   await refreshWatchlist();
  } catch (e) {
   setError((e as Error).message);
  }
 }

 function toggleManualCompare(code: string) {
  setManualCompareCodes((prev) => (prev.includes(code) ? prev.filter((item) => item !== code) : prev.length >= 5 ? prev : [...prev, code]));
 }

 function exportResults() {
  const rows = [["代码", "名称", "综合分"], ...funds.map((item) => [item.code, item.name, String(item.final_score)])];
  const blob = new Blob([`\uFEFF${rows.map((row) => row.join(",")).join("\n")}`], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "fund-selection-results.csv";
  anchor.click();
  URL.revokeObjectURL(url);
 }

 function openDetail(code: string) {
  setSelectedCode(code);
  setPage("详情");
 }

 const watchCodes = new Set(watchlist.map((item) => item.code));
 const compareCodes = new Set(manualCompareCodes);

 return (
  <div className="app-shell">
   <header className="topbar">
    <div className="brand-block">
     <strong>基金量化选基助手</strong>
     <span>FUND INTELLIGENCE STUDIO</span>
    </div>
    <nav className="main-nav">
     {(["首页", "选基", "对比", "观察池", "详情"] as const).map((item) => (
      <button key={item} className={page === item ? "is-active" : ""} onClick={() => setPage(item)}>{item}</button>
     ))}
     <button type="button" className="is-muted">设置</button>
    </nav>
    <div className="nav-side"><span>仅供参考，不构成投资建议</span><button type="button" className="nav-icon-button" aria-label="通知">!</button><button type="button" className="nav-icon-button" aria-label="帮助">?</button><div className="nav-avatar" aria-label="用户头像">投</div></div>
   </header>

   {page === "首页" ? <section className="hero-head hero-home"><div><h1>{titleFor(page, detail)}</h1><p className="subtle">{subtitleFor(page, risk, detail, manualCompareCodes.length || activeCompareCodes.length)}</p></div><div className="risk-tabs" role="group" aria-label="风险偏好">{RISKS.map((item) => <button key={item} className={risk === item ? "is-active" : ""} onClick={() => setRisk(item)}>{item}</button>)}</div></section> : null}

   {error ? <div className="error-banner">错误：{error}</div> : null}
   {page === "首页" ? <Dashboard top10={top10} risk={risk} loading={fundsLoading} onMore={() => setPage("选基")} onRefresh={handleRefreshMarket} refreshingMarket={refreshingMarket} /> : null}
   {page === "选基" ? <Picker funds={funds} loading={fundsLoading} query={query} setQuery={setQuery} page={currentPage} pageSize={pageSize} totalPages={totalPages} total={fundsTotal} onPrev={() => setQuery((q) => ({ ...q, page: Math.max(1, (q.page ?? 1) - 1) }))} onNext={() => setQuery((q) => ({ ...q, page: Math.min(totalPages, (q.page ?? 1) + 1) }))} onReset={() => setQuery(DEFAULT_QUERY)} onExport={exportResults} onOpenDetail={openDetail} onToggleWatch={toggleWatch} watchCodes={watchCodes} onToggleCompare={toggleManualCompare} compareCodes={compareCodes} onRefreshMarket={handleRefreshMarket} refreshingMarket={refreshingMarket} /> : null}
   {page === "详情" ? <Detail detail={detail} loading={detailLoading} onRefreshMarket={handleRefreshMarket} refreshingMarket={refreshingMarket} /> : null}
   {page === "对比" ? <Compare data={compare} details={compareDetails} loading={compareLoading} usingManual={manualCompareCodes.length > 0} manualSelectedCount={manualCompareCodes.length} /> : null}
   {page === "观察池" ? <Watchlist items={watchlist} loading={watchlistLoading} onToggleWatch={toggleWatch} onOpenDetail={openDetail} onToggleCompare={toggleManualCompare} compareCodes={compareCodes} onCompare={() => setPage("对比")} /> : null}

   <footer className="footer-strip"><span>关于我们</span><span>服务协议</span><span>隐私政策</span><span>风险揭示书</span></footer>
  </div>
 );
}

function Dashboard({ top10, risk, loading, onMore, onRefresh, refreshingMarket }: { top10: FundScore[]; risk: RiskProfile; loading: boolean; onMore: () => void; onRefresh: () => void; refreshingMarket: boolean }) {
 if (loading) return <section className="panel">首页加载中...</section>;
 const avg = top10.length ? top10.reduce((sum, item) => sum + item.final_score, 0) / top10.length : 0;
 const alerts = top10.filter((item) => item.explanation.minus[0] !== "暂无明显短板因子" || item.final_score < 85).length;
 const latestQuote = top10.find((item) => item.market?.quote_time)?.market?.quote_time ?? new Date().toISOString().slice(0, 10);
 const sentiment = top10.length ? "市场情绪：适中" : "市场情绪：等待行情刷新";
  return (
  <section className="dashboard-page">
   <div className="metric-grid">
    <Metric label="QUANT PICK" value={`${top10.length} 只`} note="今日模型优选推荐" tone="gold" />
    <Metric label="RISK ALERT" value={`${alerts} 项`} note="持仓/关注高风险预警" tone="red" />
    <Metric label="SENTIMENT" value={`${Math.round(avg || 0)}%`} note={sentiment} />
    <Metric label="LAST SYNC" value={latestQuote} note={`当前风险偏好：${risk}`} action={<button className="metric-link" onClick={onRefresh} disabled={refreshingMarket}>{refreshingMarket ? "刷新中..." : "立即刷新"}</button>} />
   </div>
   <div className="dashboard-grid">
    <article className="panel home-table-panel">
     <div className="section-head"><div><h2>今日推荐 Top 10</h2><p>当前Top1代码：{top10[0]?.code ?? "-"}</p></div><div className="button-row"><button className="soft-button" onClick={onRefresh} disabled={refreshingMarket}>{refreshingMarket ? "刷新中..." : "刷新行情"}</button><button className="text-link" onClick={onMore}>查看更多</button></div></div>
     {!top10.length ? <div className="empty-state">暂无推荐结果</div> : <table className="data-table home-table"><thead><tr><th>基金名称/代码</th><th>类型</th><th>综合评分</th><th>实时行情</th><th>操作</th></tr></thead><tbody>{top10.map((item) => <tr key={item.code}><td><strong>{item.name}</strong><span>{item.code}</span></td><td>{typeLabel(item)}</td><td className="score-cell">{item.final_score}</td><td><div className="market-line"><strong className={marketTone(item.market)}>{marketSummary(item.market)}</strong><span>{marketDetail(item.market)}</span></div></td><td><div className="icon-actions"><button className="icon-button" onClick={onMore} aria-label="加入对比">⇄</button><button className="icon-button" onClick={onMore} aria-label="查看更多">›</button></div></td></tr>)}</tbody></table>}
     </article>
    <div className="side-stack">
     <article className="panel risk-panel"><h3>风险透视</h3><div className="risk-list"><div><span>市场波动率</span><strong className="negative-text">18.5% 偏高</strong></div><div><span>信用利差</span><strong>0.42% 稳定</strong></div><div><span>流动性压力</span><strong>0.15 低位</strong></div></div><div className="callout"><span>智能调仓提示</span><strong>当成长拥挤度偏高时，优先保留抗回撤更均衡的标的。</strong></div><button className="primary-btn">生成风险报告</button></article>
     <article className="panel"><h3>板块热度分布</h3><div className="heat-grid"><Heat label="半导体" value="+2.45%" rise /><Heat label="白酒" value="-1.12%" /><Heat label="新能源" value="+0.32%" rise /><Heat label="人工智能" value="+4.18%" rise /></div></article>
    </div>
   </div>
  </section>
 );
}

function Picker({ funds, loading, query, setQuery, page, pageSize, totalPages, total, onPrev, onNext, onReset, onExport, onOpenDetail, onToggleWatch, watchCodes, onToggleCompare, compareCodes, onRefreshMarket, refreshingMarket }: { funds: FundScore[]; loading: boolean; query: Omit<FundQuery, "risk_profile">; setQuery: Dispatch<SetStateAction<Omit<FundQuery, "risk_profile">>>; page: number; pageSize: number; totalPages: number; total: number; onPrev: () => void; onNext: () => void; onReset: () => void; onExport: () => void; onOpenDetail: (code: string) => void; onToggleWatch: (code: string) => void; watchCodes: Set<string>; onToggleCompare: (code: string) => void; compareCodes: Set<string>; onRefreshMarket: () => void; refreshingMarket: boolean }) {
 const compareCount = compareCodes.size;
  return (
   <section className="picker-page">
    <aside className="panel filter-panel">
     <Field label="关键词搜索"><input aria-label="关键词搜索" placeholder="代码/简称/经理" value={query.keyword ?? ""} onChange={(e) => setQuery((q) => ({ ...q, keyword: e.target.value, page: 1 }))} /></Field>
     <Group title="交易渠道"><div className="button-row">{(["场内", "场外"] as const).map((item) => <button key={item} className={query.channel === item ? "is-active" : ""} onClick={() => setQuery((q) => ({ ...q, channel: q.channel === item ? undefined : item, page: 1 }))}>{item}</button>)}</div></Group>
     <Group title="基金类别"><div className="chip-grid">{CATEGORIES.map((item) => <button key={item} className={query.category === item ? "is-active" : ""} onClick={() => setQuery((q) => ({ ...q, category: q.category === item ? "" : item, page: 1 }))}>{item}</button>)}</div></Group>
     <Field label="成立年限"><input aria-label="最低年限" type="number" value={query.min_years ?? ""} onChange={(e) => setQuery((q) => ({ ...q, min_years: e.target.value ? Number(e.target.value) : undefined, page: 1 }))} /></Field>
     <Field label="最低规模（亿元）"><input aria-label="最低规模（亿元）" type="number" value={query.min_scale ?? ""} onChange={(e) => setQuery((q) => ({ ...q, min_scale: e.target.value ? Number(e.target.value) : undefined, page: 1 }))} /></Field>
     <Field label="最高规模（亿元）"><input aria-label="最高规模（亿元）" type="number" value={query.max_scale ?? ""} onChange={(e) => setQuery((q) => ({ ...q, max_scale: e.target.value ? Number(e.target.value) : undefined, page: 1 }))} /></Field>
     <Field label="最高费率"><input aria-label="最高费率" type="number" step="0.01" value={query.max_fee ?? ""} onChange={(e) => setQuery((q) => ({ ...q, max_fee: e.target.value ? Number(e.target.value) : undefined, page: 1 }))} /></Field>
     <Field label="场内/场外"><select aria-label="场内/场外" value={query.channel ?? ""} onChange={(e) => setQuery((q) => ({ ...q, channel: e.target.value ? (e.target.value as "场内" | "场外") : undefined, page: 1 }))}><option value="">全部</option><option value="场内">场内</option><option value="场外">场外</option></select></Field>
     <Field label="风险等级"><select aria-label="风险等级" value={query.risk_level ?? ""} onChange={(e) => setQuery((q) => ({ ...q, risk_level: e.target.value, page: 1 }))}><option value="">全部</option>{LEVELS.map((item) => <option key={item} value={item}>{item}</option>)}</select></Field>
     <Field label="排序字段"><select aria-label="排序字段" value={query.sort_by} onChange={(e) => setQuery((q) => ({ ...q, sort_by: e.target.value as FundQuery["sort_by"], page: 1 }))}><option value="final_score">综合评分</option><option value="base_score">基础评分</option><option value="policy_score">政策评分</option><option value="one_year_return">近一年收益</option><option value="max_drawdown">最大回撤</option><option value="fee">费率</option></select></Field>
     <Group title="风险等级"><div className="button-row">{(["R1", "R3", "R5"] as const).map((item) => <button key={item} className={query.risk_level === item ? "is-active" : ""} onClick={() => setQuery((q) => ({ ...q, risk_level: q.risk_level === item ? "" : item, page: 1 }))}>{item}</button>)}</div></Group>
     <div className="hint-card"><strong>因子分析贴士</strong><p>综合评分更适合先筛后看，最大回撤更适合做压力测试。</p></div>
    </aside>
    <div className="picker-main">
     <div className="panel toolbar-panel"><div className="toolbar-title">因子权重模板<div className="button-row"><button className="is-active">保守</button><button>均衡</button><button>进取</button></div></div><div className="button-row"><button onClick={onReset}>重置筛选</button><button className="primary-btn" onClick={onExport}>导出结果</button></div></div>
     <div className="status-panel">
      <strong>{`手动对比已选：${compareCount} /5`}</strong>
      {compareCount >= 5 ? <span>已达到手动对比上限（5只）。</span> : <span>可在选基页或观察池中添加，至少 2 只可进入对比分析。</span>}
     </div>
     <article className="panel picker-results">{loading ? <div className="empty-state">加载中...</div> : null}{!loading && !funds.length ? <div className="empty-state">无结果，请调整筛选条件。</div> : null}{!loading && funds.length ? <><table className="data-table picker-table"><thead><tr><th>基金信息</th><th>类型 / 规模</th><th>综合评分</th><th>近1年收益</th><th>最大回撤</th><th>7日趋势</th><th>状态</th><th>操作</th></tr></thead><tbody>{funds.map((item) => <tr key={item.code}><td><strong>{item.code}</strong><span className="fund-name-strong">{item.name}</span></td><td><span>{typeLabel(item)}</span><small>{scaleLabel(item)}</small></td><td><div className="score-stack"><b>{item.final_score}</b><small>TOP {Math.max(1, Math.round((100 - item.final_score) / 2))}%</small></div></td><td className="positive-text">+{(item.base_score / 4.1).toFixed(2)}%</td><td className="negative-text">-{(item.policy_score / 10.2).toFixed(1)}%</td><td><MiniBars seed={item.code} /></td><td><span className={item.market ? "state-pill" : "badge-outline"}>{item.market ? "高流动性" : "等待刷新"}</span></td><td><div className="result-action-stack"><button aria-label={watchCodes.has(item.code) ? "移除观察池" : "加入观察池"} className="icon-button add-button" onClick={() => onToggleWatch(item.code)}>{watchCodes.has(item.code) ? "✓" : "+"}</button><button aria-label="查看详情" className="text-link" onClick={() => onOpenDetail(item.code)}>详情</button><button aria-label={compareCodes.has(item.code) ? "取消对比" : "加入对比"} className={compareCodes.has(item.code) ? "chip-active compact-chip" : "compact-chip"} onClick={() => onToggleCompare(item.code)}>{compareCodes.has(item.code) ? "取消" : "对比"}</button></div></td></tr>)}</tbody></table><div className="table-footer"><span>展示 {(page - 1) * pageSize + 1}-{Math.min(page * pageSize, total)} 条，共计 {total} 条符合条件的基金</span><div className="page-dots"><button onClick={onPrev} disabled={page <= 1}>上一页</button><button className="page-chip is-current">{page}</button><button onClick={onNext} disabled={page >= totalPages}>下一页</button></div></div></> : null}</article>
    </div>
   </section>
  );
}

function Detail({ detail, loading, onRefreshMarket, refreshingMarket }: { detail: FundDetail | null; loading: boolean; onRefreshMarket: () => void; refreshingMarket: boolean }) {
 const [tab, setTab] = useState<DetailTab>("表现分析");
 if (loading) return <section className="panel">详情加载中...</section>;
 if (!detail) return <section className="panel">暂无详情数据</section>;
 return (
  <section className="detail-page">
   <header className="detail-top">
    <div><div className="badge-row"><span className="badge-soft">{typeLabel(detail)}</span><span className="badge-outline">{riskLabel(detail.risk_level)}</span></div><h2>基金详情页</h2><h3>{detail.name} <span>{detail.code}</span></h3><p>{detail.explanation.applicable}</p></div>
    <div className="score-box"><span>综合量化评分</span><strong>{(detail.final_score / 10).toFixed(1)}</strong><small>/10</small></div>
   </header>
   <div className="detail-grid">
    <article className="panel detail-main-panel">{(["表现分析", "因子分析", "成本与交易", "推荐理由"] as DetailTab[]).map((item) => <button key={item} className={tab === item ? "tab-btn is-active" : "tab-btn"} onClick={() => setTab(item)}>{item}</button>)}{tab === "表现分析" ? <PerformancePanel detail={detail} /> : null}{tab === "因子分析" ? <FactorPanel factors={detail.factors} policy={detail.policy} /> : null}{tab === "成本与交易" ? <CostPanel detail={detail} /> : null}{tab === "推荐理由" ? <ReasonPanel detail={detail} /> : null}</article>
    <aside className="detail-side"><article className="panel"><div className="section-head"><div><h4>真实行情</h4><p>{detail.market?.source ?? "等待行情刷新"}</p></div><button onClick={onRefreshMarket} disabled={refreshingMarket}>{refreshingMarket ? "刷新中..." : "刷新"}</button></div><Info label="当前价格 / 估值" value={marketPrimary(detail.market)} /><Info label="涨跌幅" value={marketChange(detail.market)} valueClassName={marketTone(detail.market)} /><Info label="高 / 低" value={marketRange(detail.market)} /><Info label="更新时间" value={detail.market?.quote_time ?? "暂无"} /></article><article className="panel"><h4>成本与交易</h4><Info label="管理费率" value={`${detail.fee}% / 年`} /><Info label="托管费率" value={`${Math.max(0.02, detail.fee / 2).toFixed(2)}% / 年`} /><Info label="场内成交额（日均）" value={detail.market?.turnover ? `￥${(detail.market.turnover / 100000000).toFixed(2)} 亿` : "暂无"} /><Info label="跟踪误差" value={detail.tracking_error ?? "不适用"} /><button className="primary-btn">立即申购</button><button>加入自选</button></article><article className="panel"><h4>基金经理</h4><p>量化风格偏稳健，强调回撤控制与行业配置节奏。</p><div className="manager-block"><div className="manager-avatar">张</div><div><strong>张三</strong><span>从业15年</span><small>价值投资流派专家</small></div></div><div className="info-grid"><Info label="任职回报" value={`${(detail.one_year_return * 12.7).toFixed(1)}%`} /><Info label="管理规模" value={`¥ ${detail.scale_billion} 亿`} /></div></article><article className="ai-card"><span>量化透视</span><strong>{marketInsight(detail)}</strong></article></aside>
   </div>
  </section>
 );
}

function Compare({ data, details, loading, usingManual, manualSelectedCount }: { data: FundScore[]; details: FundDetail[]; loading: boolean; usingManual: boolean; manualSelectedCount: number }) {
 const summary = compareSummary(details);
  return (
  <section className="compare-page">
   <div className="section-head compare-head"><div><h2>基金深度量化对比</h2><p>{usingManual ? `当前来源：手动选择（${manualSelectedCount}只）` : "当前来源：观察池自动取前5只"}</p></div><div className="button-row"><button>添加对比基金</button><button className="primary-btn">下载分析报告</button></div></div>
   {loading ? <article className="panel">对比加载中...</article> : null}
   {!loading && data.length < 2 ? <article className="panel">请先手动或通过观察池凑齐至少2只基金。</article> : null}
   {!loading && data.length >= 2 ? <><div className="compare-cards">{details.map((item, index) => <article key={item.code} className="panel compare-card"><div className="card-top"><span>{index === 0 ? "基金 A" : "基金 B"}</span><div><small>综合量化评分</small><strong>{(item.final_score / 10).toFixed(1)}</strong></div></div><h3>{item.name}</h3><div className="badge-row"><span className="badge-soft">{typeLabel(item)}</span><span className="badge-outline">{liquidityLabel(item)}</span></div><div className="compare-mini-grid"><Info label="近一年收益" value={`+${item.one_year_return}%`} /><Info label="最大回撤" value={`${item.max_drawdown}%`} /><Info label="实时行情" value={marketPrimary(item.market)} /></div><div className="market-line"><strong className={marketTone(item.market)}>{marketSummary(item.market)}</strong><span>{marketDetail(item.market)}</span></div></article>)}</div><div className="compare-grid"><article className="panel"><h3>收益 / 回撤对照</h3><div className="compare-legend"><div><i className="legend-swatch legend-a" />基金 A</div><div><i className="legend-swatch legend-b" />基金 B</div></div><div className="curve-box">{details.map((item, index) => <Curve key={item.code} values={trend(item.code, item.final_score)} accent={index === 0} />)}</div></article><article className="panel"><h3>因子雷达图（分项条）</h3><div className="factor-list">{details.map((item) => <div key={item.code} className="radar-item"><strong>{item.name}</strong><Bar label="收益能力" value={item.factors.returns} /><Bar label="风险控制" value={item.factors.risk_control} /><Bar label="政策支持" value={item.policy.support} accent /></div>)}</div></article></div><article className="panel compare-table-panel"><h3>深度量化指标拆解</h3><table className="data-table"><thead><tr><th>指标维度</th>{details.map((item, index) => <th key={item.code}>{item.name}（{index === 0 ? "A" : "B"}）</th>)}</tr></thead><tbody><tr><td>风险调整收益</td>{details.map((item) => <td key={`${item.code}-1`}>{(item.factors.risk_adjusted / 50).toFixed(2)}</td>)}</tr><tr><td>信息比率替代</td>{details.map((item) => <td key={`${item.code}-2`}>{(item.policy.support / 80).toFixed(2)}</td>)}</tr><tr><td>年化波动率</td>{details.map((item) => <td key={`${item.code}-3`}>{Math.abs(item.max_drawdown) * 1.14}%</td>)}</tr><tr><td>日均换手率</td>{details.map((item) => <td key={`${item.code}-4`}>{(item.factors.liquidity / 100).toFixed(2)}%</td>)}</tr><tr><td>实时涨跌</td>{details.map((item) => <td key={`${item.code}-5`} className={marketTone(item.market)}>{marketChange(item.market)}</td>)}</tr></tbody></table></article><article className="compare-conclusion"><div className="compare-conclusion-inner"><div className="insight-icon">◎</div><div className="compare-conclusion-copy"><h3>智能对比量化结论</h3><p className="compare-caption">结论摘要卡片</p><div className="summary-row"><Summary label="更稳健" value={summary.stable} /><Summary label="更有弹性" value={summary.offensive} /><Summary label="更适合当前风险偏好" value={summary.fit} /></div></div><button className="dark-btn">一键加入自选</button></div></article><article className="panel"><h3>成本与流动性对比</h3><table className="data-table"><thead><tr><th>指标维度</th>{details.map((item) => <th key={item.code}>{item.name}</th>)}</tr></thead><tbody><tr><td>管理费率</td>{details.map((item) => <td key={`${item.code}-6`}>{item.fee}% / 年</td>)}</tr><tr><td>流动性标签</td>{details.map((item) => <td key={`${item.code}-7`}>{liquidityLabel(item)}</td>)}</tr><tr><td>跟踪误差</td>{details.map((item) => <td key={`${item.code}-8`}>{item.tracking_error ?? "不适用"}</td>)}</tr></tbody></table></article></> : null}
  </section>
 );
}

function Watchlist({ items, loading, onToggleWatch, onOpenDetail, onToggleCompare, compareCodes, onCompare }: { items: WatchlistScore[]; loading: boolean; onToggleWatch: (code: string) => void; onOpenDetail: (code: string) => void; onToggleCompare: (code: string) => void; compareCodes: Set<string>; onCompare: () => void }) {
 const avg = items.length ? (items.reduce((sum, item) => sum + item.final_score, 0) / items.length).toFixed(1) : "0.0";
 return (
  <section className="watch-page">
   <div className="watch-hero"><article className="panel"><span>待处理风险预警</span><strong>{items.reduce((sum, item) => sum + item.alerts.length, 0).toString().padStart(2, "0")}</strong><small>高危波动点位</small></article><article className="panel"><span>已收藏基金总数</span><strong>{items.length}</strong><small>支成分基金</small></article><article className="panel gold-banner"><span>全池平均量化评分</span><strong>{avg}</strong><small>较昨日 +1.2%</small></article></div>
   <div className="section-head"><div><h2>观察池</h2><p>基于最新量化模型生成的实时异动监控。</p></div><div className="button-row"><button>筛选</button><button className="primary-btn">添加基金</button></div></div>
   {loading ? <article className="panel">观察池加载中...</article> : null}
   {!loading && !items.length ? <article className="panel">暂无收藏基金</article> : null}
   {!!items.length ? <div className="watch-grid">{items.map((item) => <article key={item.code} className="panel watch-card"><div className="watch-top"><div><div className="watch-title-row"><h3>{item.name}</h3><span className="watch-code-pill">{item.code}</span></div><div className="badge-row"><span className="badge-alert">{item.alerts[0] ?? "提醒"}</span><span className="badge-outline">{typeLabel(item)}</span></div></div><div className="watch-score"><strong>{item.final_score}</strong><span>实时量化分</span></div></div><div className="watch-trend"><Spark values={trend(item.code, item.final_score)} /><div><strong className={marketTone(item.market)}>{marketChange(item.market)}</strong><span>{marketPrimary(item.market)}</span></div></div><div className="market-line"><strong className={marketTone(item.market)}>{marketSummary(item.market)}</strong><span>{marketDetail(item.market)}</span></div><div className="row-actions"><button aria-label="查看详情" className="text-link" onClick={() => onOpenDetail(item.code)}>研报详情</button><button aria-label={compareCodes.has(item.code) ? "取消对比" : "加入对比"} className={compareCodes.has(item.code) ? "chip-active compare-link" : "compare-link"} onClick={() => onToggleCompare(item.code)}>{compareCodes.has(item.code) ? "取消对比" : "跳转对比"}</button><button aria-label="移除" className="delete-button" onClick={() => onToggleWatch(item.code)}>删除</button></div></article>)}<article className="panel add-card"><button>+ 导入更多关注基金</button><span>支持代码搜索或一键同步券商持仓。</span></article></div> : null}
   <div className="watch-bottom"><article className="panel"><h3>最近浏览</h3><div className="recent-row">{["001051 天弘创业板ETF", "510300 华泰柏瑞沪深300", "000001 景顺长城", "110011 易方达中小盘"].map((item) => <div key={item} className="recent-card"><strong>{item}</strong><span>-0.82%</span></div>)}</div></article><article className="panel"><h3>量化观察</h3><ul className="plain-list"><li>关注高换手基金，建议观察政策执行与风格漂移风险。</li><li>若出现连续回撤预警，可进入对比页和详情页复核。</li></ul><button className="primary-btn" onClick={onCompare}>进入对比页</button></article></div>
  </section>
 );
}

function PerformancePanel({ detail }: { detail: FundDetail }) {
 return <div className="detail-body"><div className="subtab-row"><button className="mini-tab is-active">收益率</button><button className="mini-tab">回撤</button><button className="mini-tab">阿尔法</button></div><div className="chart-stack"><div className="chart-box"><Curve values={trend(detail.code, detail.final_score)} accent /><div className="tooltip-card"><div><span>本基金（累计）</span><strong>+{(detail.one_year_return * 11.58).toFixed(2)}%</strong></div><div><span>沪深300</span><strong>+28.14%</strong></div></div></div><div className="chart-box compact"><p>动态回撤曲线（Max Drawdown: {detail.max_drawdown}%）</p><Curve values={trend(detail.code.split("").reverse().join(""), Math.abs(detail.max_drawdown) * 5)} /></div></div><div className="info-grid"><Info label="成立年限" value={`${detail.years} 年`} /><Info label="基金规模" value={`${detail.scale_billion} 亿`} /><Info label="近一年收益" value={`${detail.one_year_return}%`} /><Info label="最大回撤" value={`${detail.max_drawdown}%`} /></div></div>;
}

function FactorPanel({ factors, policy }: { factors: FactorMetrics; policy: PolicyMetrics }) {
 return <div className="detail-body split"><div className="radar-shell"><div className="radar-shape" /></div><div className="factor-list"><Bar label="收益能力" value={factors.returns} /><Bar label="风险控制" value={factors.risk_control} /><Bar label="风险收益比" value={factors.risk_adjusted} /><Bar label="稳定性" value={factors.stability} /><Bar label="成本效率" value={factors.cost_efficiency} /><Bar label="流动性" value={factors.liquidity} /><Bar label="存续质量" value={factors.survival_quality} /><Bar label="政策支持强度" value={policy.support} accent /><Bar label="政策执行进度" value={policy.execution} accent /><Bar label="监管安全度" value={policy.regulation_safety} accent /></div></div>;
}

function CostPanel({ detail }: { detail: FundDetail }) {
 return <div className="detail-body split"><article className="soft-card"><Info label="管理费率" value={`${detail.fee}% / 年`} /><Info label="托管费率" value={`${Math.max(0.02, detail.fee / 2).toFixed(2)}% / 年`} /><Info label="最小成交单元（场内）" value="¥ 4.28 起" /><Info label="流动性标签" value={detail.liquidity_label} /></article><article className="soft-card"><Info label="适用前提" value={detail.explanation.applicable} /><Info label="风险提示" value={detail.explanation.risk_tip} /><Info label="跟踪误差" value={detail.tracking_error ?? "不适用"} /><Info label="数据更新时间" value={detail.updated_at} /></article></div>;
}

function ReasonPanel({ detail }: { detail: FundDetail }) {
 return <div className="detail-body split"><article className="reason-card accent"><h4>量化加分项</h4><ul>{detail.explanation.plus.map((item) => <li key={item}>{item}</li>)}</ul></article><article className="reason-card"><h4>潜在扣分项</h4><ul>{detail.explanation.minus.map((item) => <li key={item}>{item}</li>)}</ul></article><article className="formula-card"><p>{detail.explanation.disclaimer}</p><strong>{detail.explanation.formula}</strong></article></div>;
}

function Field({ label, children }: { label: string; children: ReactNode }) { return <label className="field"><span>{label}</span>{children}</label>; }
function Group({ title, children }: { title: string; children: ReactNode }) { return <div className="group"><span>{title}</span>{children}</div>; }
function Metric({ label, value, note, tone, action }: { label: string; value: string; note: string; tone?: "gold" | "red"; action?: ReactNode }) { return <article className={`metric-card ${tone ?? ""}`}><span>{label}</span><strong>{value}</strong><small>{note}</small>{action}</article>; }
function Heat({ label, value, rise = false }: { label: string; value: string; rise?: boolean }) { return <div className={rise ? "heat-card rise" : "heat-card fall"}><span>{label}</span><strong className={rise ? "positive-text" : "negative-text"}>{value}</strong></div>; }
function Info({ label, value, valueClassName }: { label: string; value: string | number; valueClassName?: string }) { return <div className="info-item"><span>{label}</span><strong className={valueClassName}>{value}</strong></div>; }
function Summary({ label, value }: { label: string; value: string }) { return <div className="summary-card"><span>{label}</span><strong>{value}</strong></div>; }
function Bar({ label, value, accent = false }: { label: string; value: number; accent?: boolean }) { return <div className="bar-row"><div><span>{label}</span><strong>{value} / 100</strong></div><div className="bar-track"><i className={accent ? "accent" : ""} style={{ width: `${value}%` }} /></div></div>; }
function MiniBars({ seed }: { seed: string }) { return <div className="mini-bars">{trend(seed, 70).map((value, index) => <i key={`${seed}-${index}`} style={{ height: `${Math.max(12, value)}%` }} />)}</div>; }
function Spark({ values }: { values: number[] }) { return <div className="spark">{values.map((value, index) => <i key={`${value}-${index}`} style={{ height: `${value}%` }} />)}</div>; }
function Curve({ values, accent = false }: { values: number[]; accent?: boolean }) { return <svg className={accent ? "curve accent" : "curve"} viewBox="0 0 100 100" preserveAspectRatio="none"><polyline points={values.map((value, index) => `${index * 16.6},${100 - value}`).join(" ")} /></svg>; }

function titleFor(page: Page, detail?: FundDetail | null) {
 return ({ 首页: "欢迎回来，高级投资者", 选基: "量化选基工作台", 详情: detail ? detail.name : "基金详情页", 对比: "基金深度量化对比", 观察池: "我的观察池" })[page];
}
function subtitleFor(page: Page, risk: RiskProfile, detail?: FundDetail | null, compareCount = 0) {
 if (page === "首页") return "基于 48 个量化因子、12 个宏观维度实时计算。当前模型信心指数保持高位。";
 if (page === "选基") return "按交易渠道、基金类别、成立年限、规模与费率逐层筛选，再结合真实行情与风险偏好做二次判断。";
 if (page === "详情") return detail ? `${detail.code} · ${riskLabel(detail.risk_level)} · ${detail.channel}${detail.category ? ` · ${detail.category}` : ""}` : "查看单只基金的表现、因子、成本与推荐理由。";
 if (page === "对比") return `正在对比 ${Math.max(compareCount, 2)} 只基金的收益、回撤、因子与成本表现。`;
 return "Quantitative Observation Deck";
}
function trend(seed: string, score: number) { return Array.from({ length: 7 }, (_, index) => Math.max(24, Math.min(96, Math.round(score + (((seed.charCodeAt(index % seed.length) || 60) + index * 7) % 18) - 9)))); }
function compareSummary(details: FundDetail[]) { if (!details.length) return { stable: "-", offensive: "-", fit: "-" }; const stable = [...details].sort((a, b) => b.factors.risk_control - a.factors.risk_control)[0]; const offensive = [...details].sort((a, b) => b.one_year_return - a.one_year_return)[0]; const fit = [...details].sort((a, b) => b.final_score - a.final_score)[0]; return { stable: `${stable.name}（风险控制 ${stable.factors.risk_control}）`, offensive: `${offensive.name}（近一年收益 ${offensive.one_year_return}%）`, fit: `${fit.name}（综合分 ${fit.final_score}）` }; }
function typeLabel(item: FundScore | FundDetail) {
 if (item.channel === "场内" && item.category === "宽基") return "宽基ETF";
 if (item.category === "混合") return "混合型";
 if (item.category === "债券") return "债券型";
 if (item.category === "行业") return "行业主题";
 return item.category;
}
function scaleLabel(item: FundScore | FundDetail) {
 return item.channel === "场内" ? "1248 亿" : "42.5 亿";
}
function liquidityLabel(item: FundScore | FundDetail) {
 return item.channel === "场内" && item.category === "宽基" ? "极高流动" : item.liquidity_label;
}
function riskLabel(level: string) {
 return ({ R2: "低风险 (R2)", R3: "中风险 (R3)", R4: "中高风险 (R4)", R5: "高风险 (R5)" } as Record<string, string>)[level] ?? level;
}
function marketSummary(market?: MarketSnapshot | null) {
 if (!market) return "暂无实时行情";
 if (market.current_price !== null && market.current_price !== undefined) return `现价 ${market.current_price.toFixed(4)}`;
 if (market.nav_estimate !== null && market.nav_estimate !== undefined) return `估值 ${market.nav_estimate.toFixed(4)}`;
 if (market.nav !== null && market.nav !== undefined) return `净值 ${market.nav.toFixed(4)}`;
 return "暂无实时行情";
}
function marketDetail(market?: MarketSnapshot | null) {
 if (!market) return "请手动刷新行情";
 const change = marketChange(market);
 const source = market.source ?? "行情源";
 const quoteTime = market.quote_time ?? "未更新时间";
 return `${change} · ${source} · ${quoteTime}`;
}
function marketTone(market?: MarketSnapshot | null) {
 const pct = market?.price_change_pct ?? market?.nav_estimate_change_pct;
 const value = market?.price_change_value;
 if (pct === null || pct === undefined) return "";
 if (pct > 0) return "positive-text";
 if (pct < 0) return "negative-text";
 if (value !== null && value !== undefined) {
  if (value > 0) return "positive-text";
  if (value < 0) return "negative-text";
 }
 return "";
}
function marketPrimary(market?: MarketSnapshot | null) {
 if (!market) return "暂无";
 if (market.current_price !== null && market.current_price !== undefined) return market.current_price.toFixed(4);
 if (market.nav_estimate !== null && market.nav_estimate !== undefined) return market.nav_estimate.toFixed(4);
 if (market.nav !== null && market.nav !== undefined) return market.nav.toFixed(4);
 return "暂无";
}
function marketChange(market?: MarketSnapshot | null) {
 const pct = market?.price_change_pct ?? market?.nav_estimate_change_pct;
 const value = market?.price_change_value;
 if (pct === null || pct === undefined) return "暂无";
 if (value !== null && value !== undefined) return `${value >= 0 ? "+" : ""}${value.toFixed(4)} / ${pct >= 0 ? "+" : ""}${pct.toFixed(2)}%`;
 return `${pct >= 0 ? "+" : ""}${pct.toFixed(2)}%`;
}
function marketRange(market?: MarketSnapshot | null) {
 if (!market) return "暂无";
 if (market.intraday_high !== null && market.intraday_high !== undefined && market.intraday_low !== null && market.intraday_low !== undefined) {
  return `${market.intraday_low.toFixed(4)} / ${market.intraday_high.toFixed(4)}`;
 }
 if (market.previous_close !== null && market.previous_close !== undefined) {
  return `昨收 ${market.previous_close.toFixed(4)}`;
 }
 return "暂无";
}
function marketInsight(detail: FundDetail) {
 if (!detail.market) return "行情数据暂未同步完成，建议先刷新再结合量化评分做判断。";
 const pct = detail.market.price_change_pct ?? detail.market.nav_estimate_change_pct ?? 0;
 if (pct >= 1) return "短线资金强度偏强，若你按均衡偏好配置，可分批观察而不是一次性追高。";
 if (pct <= -1) return "当前处于回撤区间，适合结合风险控制与申赎成本，分层确认是否继续配置。";
 return "盘口波动相对温和，更适合把焦点放回基本面、费用和回撤控制。";
}
