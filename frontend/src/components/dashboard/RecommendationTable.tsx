import type { FundScore } from "../../types";

interface RecommendationTableProps {
  funds: FundScore[];
  loading?: boolean;
  onViewDetail?: (code: string) => void;
  onAddToWatchlist?: (code: string) => void;
}

export function RecommendationTable({
  funds,
  loading = false,
  onViewDetail,
  onAddToWatchlist,
}: RecommendationTableProps) {
  if (loading) {
    return (
      <div className="card" style={{ padding: '40px' }}>
        <div className="loading">加载中...</div>
      </div>
    );
  }

  if (funds.length === 0) {
    return (
      <div className="card">
        <div className="empty-state">
          <p>暂无推荐数据</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
      <table className="table">
        <thead>
          <tr>
            <th>基金代码/名称</th>
            <th>类型</th>
            <th>综合评分</th>
            <th>风险等级</th>
            <th>近1年收益</th>
            <th>最大回撤</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          {funds.map((fund) => (
            <tr key={fund.code}>
              <td>
                <div>
                  <strong style={{ display: 'block', fontSize: '12px' }}>{fund.code}</strong>
                  <span style={{ fontSize: '14px', fontWeight: 500 }}>{fund.name}</span>
                </div>
              </td>
              <td>
                <span className="chip chip-neutral">{fund.category}</span>
              </td>
              <td>
                <strong style={{ color: 'var(--color-primary)', fontSize: '32px', fontWeight: 800 }}>
                  {fund.final_score.toFixed(1)}
                </strong>
              </td>
              <td>
                <span className={`chip ${getRiskChipClass(fund.risk_level)}`}>{fund.risk_level}</span>
              </td>
              <td className="text-muted">
                -
              </td>
              <td className="text-error">
                -
              </td>
              <td>
                <div className="flex gap-sm">
                  <button
                    className="btn btn-ghost"
                    style={{ padding: '4px 8px' }}
                    onClick={() => onViewDetail?.(fund.code)}
                  >
                    详情
                  </button>
                  <button
                    className="btn btn-ghost"
                    style={{ padding: '4px 8px' }}
                    onClick={() => onAddToWatchlist?.(fund.code)}
                  >
                    +
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function getRiskChipClass(riskLevel: string | undefined): string {
  if (!riskLevel) return 'chip-neutral';
  const level = riskLevel.toUpperCase();
  if (level === 'R2') return 'chip-neutral';
  if (level === 'R3') return 'chip-gold';
  return 'chip-negative';
}
