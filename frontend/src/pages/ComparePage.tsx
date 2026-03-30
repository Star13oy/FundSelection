interface ComparePageProps {
  funds: any[];
  loading?: boolean;
}

export function ComparePage({ funds, loading }: ComparePageProps) {
  if (loading) {
    return (
      <div className="container">
        <div className="loading">对比加载中...</div>
      </div>
    );
  }

  if (funds.length < 2) {
    return (
      <div className="container">
        <div className="empty-state">
          <p>请先选择至少 2 只基金进行对比</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      {/* Header */}
      <div className="flex items-center justify-between mb-lg">
        <div>
          <h1>基金深度量化对比</h1>
          <p className="body-md">正在对比 {funds.length} 只基金的收益、回撤、因子与成本表现。</p>
        </div>
        <div className="flex gap-sm">
          <button className="btn btn-ghost">添加对比基金</button>
          <button className="btn btn-primary">下载分析报告</button>
        </div>
      </div>

      {/* Comparison Cards */}
      <div className="grid grid-cols-2 gap-lg mb-lg">
        {funds.map((fund, index) => (
          <div key={fund.code} className="card p-lg">
            <div className="flex items-start justify-between mb-md">
              <span className="chip chip-neutral">{index === 0 ? '基金 A' : '基金 B'}</span>
              <div>
                <small className="label-sm">综合量化评分</small>
                <strong style={{ fontSize: '32px', color: 'var(--color-primary)' }}>
                  {(fund.final_score / 10).toFixed(1)}
                </strong>
              </div>
            </div>
            <h3 style={{ marginBottom: '12px' }}>{fund.name}</h3>
            <div className="flex gap-sm mb-md">
              <span className="chip chip-neutral">{fund.category}</span>
              <span className="chip chip-gold">{fund.liquidity_label}</span>
            </div>
            <div className="grid grid-cols-3 gap-md">
              <div>
                <span className="label-sm" style={{ display: 'block' }}>近一年收益</span>
                <strong className={fund.one_year_return > 0 ? 'text-success' : 'text-error'}>
                  {fund.one_year_return > 0 ? '+' : ''}{fund.one_year_return}%
                </strong>
              </div>
              <div>
                <span className="label-sm" style={{ display: 'block' }}>最大回撤</span>
                <strong className="text-error">{fund.max_drawdown}%</strong>
              </div>
              <div>
                <span className="label-sm" style={{ display: 'block' }}>实时行情</span>
                <strong>{fund.market?.current_price || '暂无'}</strong>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Comparison Tables */}
      <div className="grid gap-lg" style={{ gridTemplateColumns: '1.25fr 0.95fr' }}>
        {/* Factor Comparison */}
        <div className="card p-lg">
          <h3 style={{ marginBottom: '16px' }}>因子对比</h3>
          <table className="table">
            <thead>
              <tr>
                <th>指标维度</th>
                {funds.map((fund) => (
                  <th key={fund.code}>{fund.name}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>收益能力</td>
                {funds.map((fund) => (
                  <td key={fund.code}>{fund.factors?.returns || '-'}</td>
                ))}
              </tr>
              <tr>
                <td>风险控制</td>
                {funds.map((fund) => (
                  <td key={fund.code}>{fund.factors?.risk_control || '-'}</td>
                ))}
              </tr>
              <tr>
                <td>风险收益比</td>
                {funds.map((fund) => (
                  <td key={fund.code}>{fund.factors?.risk_adjusted || '-'}</td>
                ))}
              </tr>
              <tr>
                <td>政策支持</td>
                {funds.map((fund) => (
                  <td key={fund.code}>{fund.policy?.support || '-'}</td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>

        {/* Cost Comparison */}
        <div className="card p-lg">
          <h3 style={{ marginBottom: '16px' }}>成本与流动性对比</h3>
          <table className="table">
            <thead>
              <tr>
                <th>指标维度</th>
                {funds.map((fund) => (
                  <th key={fund.code}>{fund.name}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>管理费率</td>
                {funds.map((fund) => (
                  <td key={fund.code}>{fund.fee}%</td>
                ))}
              </tr>
              <tr>
                <td>流动性标签</td>
                {funds.map((fund) => (
                  <td key={fund.code}>
                    <span className="chip chip-gold">{fund.liquidity_label}</span>
                  </td>
                ))}
              </tr>
              <tr>
                <td>跟踪误差</td>
                {funds.map((fund) => (
                  <td key={fund.code}>{fund.tracking_error || '不适用'}</td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Conclusion */}
      <div
        className="card p-lg mt-lg"
        style={{
          padding: '1px',
          borderRadius: '12px',
          background: 'linear-gradient(135deg, var(--color-primary), var(--color-primary-light))',
        }}
      >
        <div
          style={{
            padding: '18px',
            borderRadius: '11px',
            backgroundColor: 'rgba(255, 255, 255, 0.96)',
            display: 'flex',
            alignItems: 'center',
            gap: '20px',
          }}
        >
          <div
            style={{
              width: '72px',
              height: '72px',
              borderRadius: '999px',
              backgroundColor: 'rgba(116, 91, 0, 0.08)',
              color: 'var(--color-primary)',
              display: 'grid',
              placeItems: 'center',
              fontSize: '32px',
              fontWeight: 800,
            }}
          >
            ◎
          </div>
          <div style={{ flex: 1 }}>
            <h3 style={{ margin: '0 0 8px' }}>智能对比量化结论</h3>
            <p className="body-md" style={{ margin: 0 }}>
              基于当前风险偏好，{funds[0]?.name} 在综合评分上表现更优，
              特别是在{funds[0]?.factors?.returns > funds[1]?.factors?.returns ? '收益能力' : '风险控制'}方面。
            </p>
          </div>
          <button className="btn btn-primary">一键加入自选</button>
        </div>
      </div>
    </div>
  );
}
