import { MetricCard } from '../components/dashboard/MetricCard';
import { RecommendationTable } from '../components/dashboard/RecommendationTable';
import { RiskInsight, SectorHeat } from '../components/dashboard/RiskInsight';
import type { SectorHeatItem } from '../types';

interface HomePageProps {
  riskProfile: '保守' | '均衡' | '进取';
  onRiskProfileChange: (profile: '保守' | '均衡' | '进取') => void;
  funds: any[];
  loading?: boolean;
  onRefreshMarket?: () => void;
  refreshingMarket?: boolean;
  onViewDetail?: (code: string) => void;
  onAddToWatchlist?: (code: string) => void;
  sectorHeat?: SectorHeatItem[];
}

export function HomePage({
  riskProfile,
  onRiskProfileChange,
  funds,
  loading = false,
  onRefreshMarket,
  refreshingMarket = false,
  onViewDetail,
  onAddToWatchlist,
  sectorHeat = [],
}: HomePageProps) {
  const top10 = funds.slice(0, 10);
  const avgScore = top10.length > 0
    ? (top10.reduce((sum, fund) => sum + fund.final_score, 0) / top10.length).toFixed(0)
    : '0';
  const alertCount = top10.filter(
    (fund) => fund.final_score < 85 || fund.explanation?.minus?.[0] !== '暂无明显短板因子'
  ).length;

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '0 32px' }}>
      {/* Welcome Section */}
      <div className="flex items-center justify-between mb-lg">
        <div>
          <h1 style={{ margin: '6px 0 10px', fontSize: 'clamp(2.3rem, 4.2vw, 4.2rem)', lineHeight: 1.02, letterSpacing: '-0.04em' }}>
            欢迎回来，高级投资者
          </h1>
          <p className="body-md" style={{ maxWidth: '70ch', fontSize: '18px', color: 'var(--color-text-secondary)' }}>
            基于 48 个量化因子、12 个宏观维度实时计算。当前模型信心指数保持高位。
          </p>
        </div>

        {/* Risk Profile Tabs */}
        <div
          className="flex items-center gap-sm"
          style={{ backgroundColor: 'var(--color-surface-elevated)', padding: '4px', borderRadius: '10px' }}
        >
          {(['保守', '均衡', '进取'] as const).map((profile) => (
            <button
              key={profile}
              className={riskProfile === profile ? 'btn-primary' : 'btn btn-ghost'}
              style={{
                borderRadius: '10px',
                padding: '8px 16px',
                fontSize: '14px',
                fontWeight: 600,
              }}
              onClick={() => onRiskProfileChange(profile)}
            >
              {profile}
            </button>
          ))}
        </div>
      </div>

      {/* Overview Bento Grid */}
      <div className="grid grid-cols-4 gap-md" style={{ marginBottom: '24px' }}>
        <MetricCard
          label="QUANT PICK"
          value={`${top10.length} 只`}
          note="今日模型优选推荐"
          variant="gold"
        />
        <MetricCard
          label="RISK ALERT"
          value={`${alertCount} 项`}
          note="持仓/关注高风险预警"
          variant="red"
        />
        <MetricCard
          label="SENTIMENT"
          value={`${avgScore}%`}
          note="市场情绪：适中"
        />
        <MetricCard
          label="LAST SYNC"
          value={new Date().toLocaleDateString('zh-CN')}
          note={`当前风险偏好：${riskProfile}`}
          action={
            <button
              className="btn btn-ghost"
              style={{ padding: 0, color: 'var(--color-primary)', fontSize: '12px', fontWeight: 700 }}
              onClick={onRefreshMarket}
              disabled={refreshingMarket}
            >
              {refreshingMarket ? '刷新中...' : '立即刷新'}
            </button>
          }
        />
      </div>

      {/* Main Content Area */}
      <div className="grid" style={{ gridTemplateColumns: '1.75fr 0.9fr', gap: '24px' }}>
        {/* Left: Top 10 Recommendations */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div className="card" style={{ padding: '28px 28px 0' }}>
            <div className="flex items-center justify-between mb-md">
              <div>
                <h2 style={{ margin: 0 }}>今日推荐 Top 10</h2>
                <p className="body-md" style={{ margin: '4px 0 0', fontSize: '14px' }}>
                  当前Top1代码：{top10[0]?.code || '-'}
                </p>
              </div>
              <div className="flex gap-sm">
                <button
                  className="btn btn-secondary"
                  onClick={onRefreshMarket}
                  disabled={refreshingMarket}
                >
                  {refreshingMarket ? '刷新中...' : '刷新行情'}
                </button>
              </div>
            </div>
          </div>

          <RecommendationTable
            funds={top10}
            loading={loading}
            onViewDetail={onViewDetail}
            onAddToWatchlist={onAddToWatchlist}
          />
        </div>

        {/* Right: Risk Insight Sidebar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <RiskInsight
            metrics={[
              { label: '市场波动率', value: '18.5% 偏高', tone: 'negative' },
              { label: '信用利差', value: '0.42% 稳定', tone: 'neutral' },
              { label: '流动性压力', value: '0.15 低位', tone: 'positive' },
            ]}
            callout={{
              label: '智能调仓提示',
              value: '当成长拥挤度偏高时，优先保留抗回撤更均衡的标的。',
            }}
            extraContent={
              <button className="btn btn-primary" style={{ width: '100%', marginTop: '16px' }}>
                生成风险报告
              </button>
            }
          />

          {/* Sector Heat */}
          <div className="card" style={{ padding: '24px' }}>
            <h4 style={{ marginBottom: '16px' }}>板块热度分布</h4>
            <div className="grid grid-cols-2 gap-md">
              {sectorHeat.map((item) => (
                <SectorHeat
                  key={item.code}
                  label={item.label}
                  value={formatSectorValue(item.change_pct)}
                  tone={getSectorTone(item.change_pct)}
                  meta={item.current_price ? `ETF ${item.code} · ${item.current_price.toFixed(3)}` : `ETF ${item.code}`}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function formatSectorValue(changePct: number | null): string {
  if (changePct === null || Number.isNaN(changePct)) return '暂无行情';
  return `${changePct > 0 ? '+' : ''}${changePct.toFixed(2)}%`;
}

function getSectorTone(changePct: number | null): 'rise' | 'fall' | 'flat' {
  if (changePct === null || Number.isNaN(changePct) || changePct === 0) return 'flat';
  return changePct > 0 ? 'rise' : 'fall';
}
