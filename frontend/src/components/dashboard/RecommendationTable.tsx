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
            <th className="table-header-cell">基金代码 / 名称</th>
            <th className="table-header-cell">类型标识</th>
            <th className="table-header-cell">综合评分</th>
            <th className="table-header-cell">风险等级</th>
            <th className="table-header-cell">近1年收益</th>
            <th className="table-header-cell">最大回撤</th>
            <th className="table-header-cell">操作</th>
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
                <div style={{ display: 'grid', gap: '6px' }}>
                  <span
                    className="chip chip-neutral"
                    style={{ justifyContent: 'center', minWidth: '78px', padding: '9px 14px', fontSize: '13px' }}
                    title={`${formatFundType(fund.fund_type)} / ${fund.channel}`}
                  >
                    {formatCategoryLabel(fund.category)}
                  </span>
                  <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)', fontWeight: 600 }}>
                    {formatFundType(fund.fund_type)} / {fund.channel}
                  </span>
                </div>
              </td>
              <td>
                <strong style={{ color: 'var(--color-primary)', fontSize: '32px', fontWeight: 800 }}>
                  {fund.final_score.toFixed(1)}
                </strong>
              </td>
              <td>
                <span className={`chip ${getRiskChipClass(fund.risk_level)}`}>{fund.risk_level}</span>
              </td>
              <td>
                <span className={fund.one_year_return >= 0 ? 'text-success' : 'text-error'} style={{ fontWeight: 700 }}>
                  {formatSignedPercent(fund.one_year_return)}
                </span>
              </td>
              <td>
                <span className={fund.max_drawdown >= 0 ? 'text-success' : 'text-error'} style={{ fontWeight: 700 }}>
                  {formatPercent(fund.max_drawdown)}
                </span>
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

function formatCategoryLabel(category: string): string {
  const normalized = category.replace("型", "");
  if (normalized.length <= 3) return normalized;
  if (normalized.includes("债")) return "债券";
  if (normalized.includes("宽")) return "宽基";
  if (normalized.includes("行")) return "行业";
  if (normalized.includes("混")) return "混合";
  return normalized.slice(0, 4);
}

function formatFundType(fundType: string): string {
  if (fundType === "etf_theme") return "ETF";
  if (fundType === "bond") return "债基";
  if (fundType === "equity") return "主动";
  return fundType;
}

function formatSignedPercent(value: number): string {
  return `${value > 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function formatPercent(value: number): string {
  return `${value.toFixed(2)}%`;
}
