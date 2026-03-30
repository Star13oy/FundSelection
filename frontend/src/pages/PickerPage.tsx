import { useState } from 'react';

interface PickerPageProps {
  funds: any[];
  loading?: boolean;
  onFilterChange: (filters: any) => void;
  onViewDetail: (code: string) => void;
  onAddToWatchlist: (code: string) => void;
}

export function PickerPage({ funds, loading, onFilterChange, onViewDetail, onAddToWatchlist }: PickerPageProps) {
  const [filters, setFilters] = useState({
    channel: '',
    category: '',
    min_years: '',
    max_fee: '',
    keyword: '',
  });

  return (
    <div className="container">
      <div className="flex items-center justify-between mb-lg">
        <div>
          <h1>量化选基工作台</h1>
          <p className="body-md">
            按交易渠道、基金类别、成立年限、规模与费率逐层筛选，再结合真实行情与风险偏好做二次判断。
          </p>
        </div>
      </div>

      <div className="grid gap-lg" style={{ gridTemplateColumns: '292px 1fr' }}>
        {/* Left: Filter Panel */}
        <aside className="card" style={{ padding: '14px', position: 'sticky', top: '12px', alignSelf: 'start' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {/* Keyword Search */}
            <div>
              <label className="label-sm" style={{ display: 'block', marginBottom: '8px' }}>
                关键词搜索
              </label>
              <input
                type="text"
                className="input"
                placeholder="代码/简称/经理"
                value={filters.keyword}
                onChange={(e) => setFilters({ ...filters, keyword: e.target.value })}
              />
            </div>

            {/* Channel */}
            <div>
              <span className="label-sm" style={{ display: 'block', marginBottom: '8px' }}>
                交易渠道
              </span>
              <div className="flex gap-sm">
                {['场内', '场外'].map((channel) => (
                  <button
                    key={channel}
                    className={`chip ${filters.channel === channel ? 'chip-gold' : 'chip-neutral'}`}
                    style={{ border: 'none', cursor: 'pointer' }}
                    onClick={() => setFilters({ ...filters, channel: filters.channel === channel ? '' : channel })}
                  >
                    {channel}
                  </button>
                ))}
              </div>
            </div>

            {/* Category */}
            <div>
              <span className="label-sm" style={{ display: 'block', marginBottom: '8px' }}>
                基金类别
              </span>
              <div className="grid grid-cols-2 gap-sm">
                {['宽基', '行业', '债券', '混合'].map((category) => (
                  <button
                    key={category}
                    className={`chip ${filters.category === category ? 'chip-gold' : 'chip-neutral'}`}
                    style={{ border: 'none', cursor: 'pointer' }}
                    onClick={() => setFilters({ ...filters, category: filters.category === category ? '' : category })}
                  >
                    {category}
                  </button>
                ))}
              </div>
            </div>

            {/* Min Years */}
            <div>
              <label className="label-sm" style={{ display: 'block', marginBottom: '8px' }}>
                成立年限
              </label>
              <input
                type="number"
                className="input"
                placeholder="最低年限"
                value={filters.min_years}
                onChange={(e) => setFilters({ ...filters, min_years: e.target.value })}
              />
            </div>

            {/* Max Fee */}
            <div>
              <label className="label-sm" style={{ display: 'block', marginBottom: '8px' }}>
                最高费率
              </label>
              <input
                type="number"
                className="input"
                placeholder="最高费率"
                step="0.01"
                value={filters.max_fee}
                onChange={(e) => setFilters({ ...filters, max_fee: e.target.value })}
              />
            </div>

            {/* Hint Card */}
            <div
              className="card p-sm"
              style={{
                padding: '12px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: '#F6EFCF',
                color: '#483800',
              }}
            >
              <strong className="label-sm">因子分析贴士</strong>
              <p style={{ fontSize: '12px', margin: '4px 0 0' }}>
                综合评分更适合先筛后看，最大回撤更适合做压力测试。
              </p>
            </div>
          </div>
        </aside>

        {/* Right: Results */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Toolbar */}
          <div className="card flex items-center justify-between p-md">
            <div className="flex items-center gap-md">
              <span className="label-sm">因子权重模板</span>
              <div className="flex gap-sm">
                {['保守', '均衡', '进取'].map((template) => (
                  <button
                    key={template}
                    className="btn btn-secondary"
                    style={{ padding: '6px 12px', fontSize: '12px' }}
                  >
                    {template}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex gap-sm">
              <button className="btn btn-ghost">重置筛选</button>
              <button className="btn btn-primary">导出结果</button>
            </div>
          </div>

          {/* Results Table */}
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            {loading ? (
              <div className="loading">加载中...</div>
            ) : funds.length === 0 ? (
              <div className="empty-state">无结果，请调整筛选条件。</div>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>基金信息</th>
                    <th>类型/规模</th>
                    <th>综合评分</th>
                    <th>近1年收益</th>
                    <th>最大回撤</th>
                    <th>状态</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {funds.map((fund) => (
                    <tr key={fund.code}>
                      <td>
                        <strong style={{ display: 'block', fontSize: '14px' }}>{fund.code}</strong>
                        <span style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-primary)' }}>
                          {fund.name}
                        </span>
                      </td>
                      <td>
                        <span className="chip chip-neutral">{fund.category}</span>
                        <small style={{ display: 'block', marginTop: '4px', color: 'var(--color-text-secondary)' }}>
                          {fund.scale_billion} 亿
                        </small>
                      </td>
                      <td>
                        <strong style={{ color: 'var(--color-primary)', fontSize: '24px' }}>
                          {fund.final_score}
                        </strong>
                      </td>
                      <td className={fund.one_year_return > 0 ? 'text-success' : 'text-error'}>
                        {fund.one_year_return > 0 ? '+' : ''}{fund.one_year_return}%
                      </td>
                      <td className="text-error">{fund.max_drawdown}%</td>
                      <td>
                        <span className="chip chip-gold">高流动性</span>
                      </td>
                      <td>
                        <div className="flex gap-sm">
                          <button className="btn btn-ghost" style={{ padding: '4px 8px' }} onClick={() => onViewDetail(fund.code)}>
                            详情
                          </button>
                          <button className="btn btn-ghost" style={{ padding: '4px 8px' }} onClick={() => onAddToWatchlist(fund.code)}>
                            +
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
