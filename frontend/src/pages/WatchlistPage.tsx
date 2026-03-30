import { useState } from 'react';

interface WatchlistPageProps {
  items: any[];
  loading?: boolean;
  onRemove: (code: string) => void;
  onViewDetail: (code: string) => void;
}

export function WatchlistPage({ items, loading, onRemove, onViewDetail }: WatchlistPageProps) {
  const [compareCodes, setCompareCodes] = useState<string[]>([]);

  if (loading) {
    return (
      <div className="container">
        <div className="loading">观察池加载中...</div>
      </div>
    );
  }

  const avgScore = items.length > 0
    ? (items.reduce((sum, item) => sum + item.final_score, 0) / items.length).toFixed(1)
    : '0.0';

  const alertCount = items.reduce((sum, item) => sum + (item.alerts?.length || 0), 0);

  function toggleCompare(code: string) {
    setCompareCodes((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]
    );
  }

  return (
    <div className="container">
      {/* Header */}
      <div className="flex items-center justify-between mb-lg">
        <div>
          <h1>我的观察池</h1>
          <p className="body-md">基于最新量化模型生成的实时异动监控。</p>
        </div>
        <div className="flex gap-sm">
          <button className="btn btn-ghost">筛选</button>
          <button className="btn btn-primary">添加基金</button>
        </div>
      </div>

      {/* Hero Metrics */}
      <div className="grid grid-cols-3 gap-md mb-lg">
        <div className="card p-md">
          <span className="label-sm">待处理风险预警</span>
          <strong style={{ fontSize: '52px', lineHeight: 1, display: 'block', margin: '8px 0' }}>
            {String(alertCount).padStart(2, '0')}
          </strong>
          <small>高危波动点位</small>
        </div>
        <div className="card p-md">
          <span className="label-sm">已收藏基金总数</span>
          <strong style={{ fontSize: '52px', lineHeight: 1, display: 'block', margin: '8px 0' }}>
            {items.length}
          </strong>
          <small>支成分基金</small>
        </div>
        <div
          className="card p-md"
          style={{
            background: 'linear-gradient(135deg, var(--color-primary), var(--color-primary-light))',
            color: '#fff',
          }}
        >
          <span className="label-sm" style={{ color: 'rgba(255,255,255,0.7)' }}>全池平均量化评分</span>
          <strong style={{ fontSize: '64px', lineHeight: 1, display: 'block', margin: '8px 0' }}>
            {avgScore}
          </strong>
          <small>较昨日 +1.2%</small>
        </div>
      </div>

      {/* Watchlist Grid */}
      {items.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <p>暂无收藏基金</p>
            <button className="btn btn-primary mt-md">添加第一只基金</button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-lg mb-lg">
          {items.map((item) => (
            <div key={item.code} className="card p-md" style={{ position: 'relative' }}>
              {/* Top Section */}
              <div className="flex items-start justify-between mb-md">
                <div style={{ flex: 1 }}>
                  <div className="flex items-center gap-sm mb-sm">
                    <h3 style={{ fontSize: '18px', margin: 0 }}>{item.name}</h3>
                    <span
                      className="chip"
                      style={{
                        padding: '2px 6px',
                        borderRadius: '6px',
                        backgroundColor: '#E3E2E9',
                        color: '#46464C',
                        fontSize: '10px',
                      }}
                    >
                      {item.code}
                    </span>
                  </div>
                  <div className="flex gap-sm">
                    {item.alerts?.[0] ? (
                      <span className="chip chip-negative">{item.alerts[0]}</span>
                    ) : (
                      <span className="chip chip-neutral">提醒</span>
                    )}
                    <span className="chip chip-neutral">{item.category}</span>
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <strong style={{ fontSize: '32px', color: 'var(--color-primary)' }}>
                    {item.final_score}
                  </strong>
                  <span className="label-sm" style={{ display: 'block' }}>实时量化分</span>
                </div>
              </div>

              {/* Trend */}
              <div
                className="flex items-center justify-between p-sm mb-md"
                style={{
                  borderTop: '1px solid var(--color-border)',
                  borderBottom: '1px solid var(--color-border)',
                  padding: '14px 0',
                }}
              >
                <div
                  className="flex items-center gap-sm"
                  style={{ height: '54px', flex: 1 }}
                >
                  {/* Simple sparkline placeholder */}
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'flex-end',
                      gap: '4px',
                      height: '100%',
                      flex: 1,
                    }}
                  >
                    {Array.from({ length: 7 }).map((_, i) => (
                      <div
                        key={i}
                        style={{
                          width: '16px',
                          height: `${30 + Math.random() * 60}%`,
                          borderRadius: '2px 2px 0 0',
                          background: 'linear-gradient(180deg, #E9E8E7, var(--color-primary))',
                        }}
                      />
                    ))}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <strong
                    className={item.market?.price_change_pct > 0 ? 'text-success' : 'text-error'}
                  >
                    {item.market?.price_change_pct ? `${item.market.price_change_pct > 0 ? '+' : ''}${item.market.price_change_pct}%` : '暂无'}
                  </strong>
                  <span className="label-sm" style={{ display: 'block' }}>
                    {item.market?.current_price || '暂无'}
                  </span>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-sm justify-end">
                <button
                  className="btn btn-ghost"
                  style={{ padding: '4px 8px' }}
                  onClick={() => onViewDetail(item.code)}
                >
                  研报详情
                </button>
                <button
                  className={`btn ${compareCodes.includes(item.code) ? 'btn-primary' : 'btn-ghost'}`}
                  style={{ padding: '4px 8px' }}
                  onClick={() => toggleCompare(item.code)}
                >
                  {compareCodes.includes(item.code) ? '取消对比' : '跳转对比'}
                </button>
                <button
                  className="btn btn-ghost"
                  style={{ padding: '4px 8px', color: 'var(--color-text-muted)' }}
                  onClick={() => onRemove(item.code)}
                >
                  删除
                </button>
              </div>
            </div>
          ))}

          {/* Add Card */}
          <div
            className="card"
            style={{
              display: 'grid',
              placeItems: 'center',
              minHeight: '220px',
              border: '1px dashed var(--color-border)',
              backgroundColor: '#FBFBFB',
              cursor: 'pointer',
            }}
          >
            <div style={{ textAlign: 'center' }}>
              <button className="btn btn-primary" style={{ marginBottom: '8px' }}>
                + 导入更多关注基金
              </button>
              <p className="body-md" style={{ fontSize: '12px' }}>
                支持代码搜索或一键同步券商持仓
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Bottom Section */}
      <div className="grid gap-lg" style={{ gridTemplateColumns: '1.2fr 0.9fr' }}>
        {/* Recent */}
        <div className="card p-lg">
          <h4 style={{ marginBottom: '16px' }}>最近浏览</h4>
          <div className="grid grid-cols-4 gap-md">
            {['001051 天弘创业板ETF', '510300 华泰柏瑞沪深300', '000001 景顺长城', '110011 易方达中小盘'].map(
              (item) => (
                <div
                  key={item}
                  className="card p-md"
                  style={{ backgroundColor: 'var(--color-surface-elevated)', padding: '14px' }}
                >
                  <strong style={{ display: 'block', marginBottom: '4px' }}>{item}</strong>
                  <span className="text-error">-0.82%</span>
                </div>
              )
            )}
          </div>
        </div>

        {/* Tips */}
        <div className="card p-lg">
          <h4 style={{ marginBottom: '16px' }}>量化观察</h4>
          <ul style={{ paddingLeft: '20px', color: 'var(--color-text-secondary)' }}>
            <li style={{ marginBottom: '10px' }}>
              关注高换手基金，建议观察政策执行与风格漂移风险。
            </li>
            <li style={{ marginBottom: '10px' }}>
              若出现连续回撤预警，可进入对比页和详情页复核。
            </li>
          </ul>
          <button
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '16px' }}
            disabled={compareCodes.length < 2}
          >
            进入对比页
          </button>
        </div>
      </div>
    </div>
  );
}
