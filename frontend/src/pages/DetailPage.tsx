import { useState } from 'react';

interface DetailPageProps {
  code: string;
  data?: any;
  loading?: boolean;
  onBack: () => void;
}

export function DetailPage({ code, data, loading, onBack }: DetailPageProps) {
  const [activeTab, setActiveTab] = useState<'表现' | '因子' | '成本' | '解释'>('表现');

  if (loading) {
    return (
      <div className="container">
        <div className="loading">详情加载中...</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="container">
        <div className="empty-state">暂无详情数据</div>
      </div>
    );
  }

  return (
    <div className="container">
      {/* Header */}
      <div className="flex items-center justify-between mb-lg">
        <button className="btn btn-ghost" onClick={onBack}>
          ← 返回
        </button>
      </div>

      {/* Fund Header */}
      <div className="card p-xl mb-lg">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex gap-sm mb-md">
              <span className="chip chip-neutral">{data.category}</span>
              <span className={`chip ${getRiskChipClass(data.risk_level)}`}>{data.risk_level}</span>
            </div>
            <h1 style={{ marginBottom: '8px' }}>{data.name}</h1>
            <p className="body-md">{data.code} · {data.channel}</p>
          </div>
          <div
            className="card p-md"
            style={{
              minWidth: '180px',
              textAlign: 'center',
              border: '2px solid var(--color-primary-light)',
            }}
          >
            <span className="label-sm" style={{ display: 'block' }}>综合量化评分</span>
            <strong style={{ fontSize: '64px', lineHeight: 0.95, color: 'var(--color-primary)' }}>
              {(data.final_score / 10).toFixed(1)}
            </strong>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="grid gap-lg" style={{ gridTemplateColumns: '1.6fr 0.9fr' }}>
        {/* Main Content */}
        <div className="card p-lg">
          <div className="flex gap-sm mb-md">
            {(['表现', '因子', '成本', '解释'] as const).map((tab) => (
              <button
                key={tab}
                className={`btn ${activeTab === tab ? 'btn-primary' : 'btn-ghost'}`}
                style={{ marginRight: '8px', marginBottom: '12px' }}
                onClick={() => setActiveTab(tab)}
              >
                {tab}分析
              </button>
            ))}
          </div>

          {activeTab === '表现' && <PerformancePanel data={data} />}
          {activeTab === '因子' && <FactorPanel factors={data.factors} policy={data.policy} />}
          {activeTab === '成本' && <CostPanel data={data} />}
          {activeTab === '解释' && <ExplanationPanel explanation={data.explanation} />}
        </div>

        {/* Sidebar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Market Data */}
          <div className="card p-lg">
            <h4 style={{ marginBottom: '16px' }}>真实行情</h4>
            <div className="flex flex-col gap-md">
              <div>
                <span className="label-sm" style={{ display: 'block' }}>当前价格/估值</span>
                <strong style={{ fontSize: '18px' }}>
                  {data.market?.current_price || data.market?.nav_estimate || '暂无'}
                </strong>
              </div>
              <div>
                <span className="label-sm" style={{ display: 'block' }}>涨跌幅</span>
                <strong className={data.market?.price_change_pct > 0 ? 'text-success' : 'text-error'}>
                  {data.market?.price_change_pct ? `${data.market.price_change_pct > 0 ? '+' : ''}${data.market.price_change_pct}%` : '暂无'}
                </strong>
              </div>
              <div>
                <span className="label-sm" style={{ display: 'block' }}>更新时间</span>
                <span style={{ fontSize: '14px', color: 'var(--color-text-secondary)' }}>
                  {data.market?.quote_time || '暂无'}
                </span>
              </div>
            </div>
          </div>

          {/* Cost Info */}
          <div className="card p-lg">
            <h4 style={{ marginBottom: '16px' }}>成本与交易</h4>
            <div className="flex flex-col gap-md">
              <div>
                <span className="label-sm" style={{ display: 'block' }}>管理费率</span>
                <span>{data.fee}% / 年</span>
              </div>
              <div>
                <span className="label-sm" style={{ display: 'block' }}>流动性标签</span>
                <span className="chip chip-gold">{data.liquidity_label}</span>
              </div>
              {data.tracking_error && (
                <div>
                  <span className="label-sm" style={{ display: 'block' }}>跟踪误差</span>
                  <span>{data.tracking_error}</span>
                </div>
              )}
            </div>
            <button className="btn btn-primary" style={{ width: '100%', marginTop: '16px' }}>
              立即申购
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function PerformancePanel({ data }: { data: any }) {
  return (
    <div>
      <h3 style={{ marginBottom: '16px' }}>表现分析</h3>
      <div className="grid grid-cols-2 gap-md mb-lg">
        <div className="card p-md" style={{ backgroundColor: 'var(--color-surface-elevated)' }}>
          <span className="label-sm" style={{ display: 'block' }}>近一年收益</span>
          <strong className={data.one_year_return > 0 ? 'text-success' : 'text-error'} style={{ fontSize: '24px' }}>
            {data.one_year_return > 0 ? '+' : ''}{data.one_year_return}%
          </strong>
        </div>
        <div className="card p-md" style={{ backgroundColor: 'var(--color-surface-elevated)' }}>
          <span className="label-sm" style={{ display: 'block' }}>最大回撤</span>
          <strong className="text-error" style={{ fontSize: '24px' }}>
            {data.max_drawdown}%
          </strong>
        </div>
        <div className="card p-md" style={{ backgroundColor: 'var(--color-surface-elevated)' }}>
          <span className="label-sm" style={{ display: 'block' }}>成立年限</span>
          <strong style={{ fontSize: '24px' }}>{data.years} 年</strong>
        </div>
        <div className="card p-md" style={{ backgroundColor: 'var(--color-surface-elevated)' }}>
          <span className="label-sm" style={{ display: 'block' }}>基金规模</span>
          <strong style={{ fontSize: '24px' }}>{data.scale_billion} 亿</strong>
        </div>
      </div>

      {/* Chart Placeholder */}
      <div
        className="card p-md"
        style={{
          minHeight: '280px',
          backgroundColor: 'var(--color-surface-elevated)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--color-text-muted)',
        }}
      >
        收益曲线图表（待实现）
      </div>
    </div>
  );
}

function FactorPanel({ factors, policy }: { factors: any; policy: any }) {
  const factorList = [
    { label: '收益能力', value: factors?.returns },
    { label: '风险控制', value: factors?.risk_control },
    { label: '风险收益比', value: factors?.risk_adjusted },
    { label: '稳定性', value: factors?.stability },
    { label: '成本效率', value: factors?.cost_efficiency },
    { label: '流动性', value: factors?.liquidity },
    { label: '存续质量', value: factors?.survival_quality },
    { label: '政策支持强度', value: policy?.support, accent: true },
    { label: '政策执行进度', value: policy?.execution, accent: true },
    { label: '监管安全度', value: policy?.regulation_safety, accent: true },
  ];

  return (
    <div>
      <h3 style={{ marginBottom: '16px' }}>因子分析</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {factorList.map((factor) => (
          <div key={factor.label}>
            <div className="flex items-center justify-between mb-sm">
              <span style={{ fontSize: '14px', color: 'var(--color-text-secondary)' }}>{factor.label}</span>
              <strong style={{ fontSize: '14px' }}>{factor.value} / 100</strong>
            </div>
            <div
              style={{
                height: '10px',
                borderRadius: '999px',
                backgroundColor: '#E9E8E7',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  height: '100%',
                  width: `${factor.value}%`,
                  background: factor.accent
                    ? 'linear-gradient(90deg, #7F7663, #111827)'
                    : 'linear-gradient(90deg, #745B00, #C5A021)',
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function CostPanel({ data }: { data: any }) {
  return (
    <div>
      <h3 style={{ marginBottom: '16px' }}>成本与交易</h3>
      <div className="grid grid-cols-2 gap-md">
        <div className="card p-md" style={{ backgroundColor: 'var(--color-surface-elevated)' }}>
          <span className="label-sm" style={{ display: 'block' }}>管理费率</span>
          <strong>{data.fee}% / 年</strong>
        </div>
        <div className="card p-md" style={{ backgroundColor: 'var(--color-surface-elevated)' }}>
          <span className="label-sm" style={{ display: 'block' }}>托管费率</span>
          <strong>{(data.fee / 2).toFixed(2)}% / 年</strong>
        </div>
        <div className="card p-md" style={{ backgroundColor: 'var(--color-surface-elevated)' }}>
          <span className="label-sm" style={{ display: 'block' }}>流动性标签</span>
          <span className="chip chip-gold">{data.liquidity_label}</span>
        </div>
        {data.tracking_error && (
          <div className="card p-md" style={{ backgroundColor: 'var(--color-surface-elevated)' }}>
            <span className="label-sm" style={{ display: 'block' }}>跟踪误差</span>
            <strong>{data.tracking_error}</strong>
          </div>
        )}
      </div>
    </div>
  );
}

function ExplanationPanel({ explanation }: { explanation: any }) {
  return (
    <div>
      <h3 style={{ marginBottom: '16px' }}>推荐理由</h3>

      <div
        className="card p-md mb-md"
        style={{
          borderLeft: '4px solid var(--color-success)',
          backgroundColor: 'var(--color-surface-elevated)',
        }}
      >
        <h4 style={{ marginBottom: '12px', color: 'var(--color-success)' }}>量化加分项</h4>
        <ul style={{ paddingLeft: '20px', margin: 0 }}>
          {explanation?.plus?.map((item: string, index: number) => (
            <li key={index} style={{ marginBottom: '8px' }}>
              {item}
            </li>
          )) || <li>暂无明显优势因子</li>}
        </ul>
      </div>

      <div
        className="card p-md mb-md"
        style={{
          borderLeft: '4px solid var(--color-error)',
          backgroundColor: 'var(--color-surface-elevated)',
        }}
      >
        <h4 style={{ marginBottom: '12px', color: 'var(--color-error)' }}>潜在扣分项</h4>
        <ul style={{ paddingLeft: '20px', margin: 0 }}>
          {explanation?.minus?.map((item: string, index: number) => (
            <li key={index} style={{ marginBottom: '8px' }}>
              {item}
            </li>
          )) || <li>暂无明显短板因子</li>}
        </ul>
      </div>

      <div className="card p-md" style={{ backgroundColor: 'var(--color-surface-elevated)' }}>
        <p className="body-md" style={{ marginBottom: '12px' }}>{explanation?.disclaimer}</p>
        <strong style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
          {explanation?.formula}
        </strong>
      </div>
    </div>
  );
}

function getRiskChipClass(riskLevel: string): string {
  const level = riskLevel.toUpperCase();
  if (level === 'R2') return 'chip-neutral';
  if (level === 'R3') return 'chip-gold';
  return 'chip-negative';
}
