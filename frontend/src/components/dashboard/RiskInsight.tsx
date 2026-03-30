import { ReactNode } from "react";

interface InsightItem {
  label: string;
  value: string;
  tone?: 'neutral' | 'positive' | 'negative';
}

interface Callout {
  label: string;
  value: string;
}

interface RiskInsightProps {
  metrics?: InsightItem[];
  callout?: Callout;
  extraContent?: ReactNode;
}

export function RiskInsight({ metrics = [], callout, extraContent }: RiskInsightProps) {
  return (
    <div className="card" style={{ padding: '24px' }}>
      <h4 style={{ marginBottom: '16px' }}>风险透视</h4>

      {metrics.length > 0 && (
        <div style={{ display: 'grid', gap: '14px', marginBottom: '16px' }}>
          {metrics.map((metric, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-sm"
              style={{ backgroundColor: 'var(--color-surface-elevated)', borderRadius: 'var(--radius-md)', padding: '12px' }}
            >
              <span style={{ fontSize: '14px', color: 'var(--color-text-secondary)' }}>{metric.label}</span>
              <strong
                style={{
                  color: metric.tone === 'positive' ? 'var(--color-success)' :
                         metric.tone === 'negative' ? 'var(--color-error)' :
                         'var(--color-text-primary)'
                }}
              >
                {metric.value}
              </strong>
            </div>
          ))}
        </div>
      )}

      {callout && (
        <div
          style={{
            margin: '12px 0',
            padding: '14px',
            borderRadius: 'var(--radius-md)',
            backgroundColor: '#F6EFCF',
            display: 'grid',
            gap: '8px',
          }}
        >
          <span className="label-sm">{callout.label}</span>
          <strong style={{ color: '#483800' }}>{callout.value}</strong>
        </div>
      )}

      {extraContent}
    </div>
  );
}

interface SectorHeatProps {
  label: string;
  value: string;
  rise?: boolean;
}

export function SectorHeat({ label, value, rise }: SectorHeatProps) {
  return (
    <div
      className="card p-md"
      style={{
        backgroundColor: rise ? '#FFEFED' : '#EEF8F2',
        borderRadius: 'var(--radius-md)',
        padding: '12px',
      }}
    >
      <span className="label-sm" style={{ display: 'block', marginBottom: '6px' }}>{label}</span>
      <strong
        className={rise ? 'text-success' : 'text-error'}
        style={{ display: 'block', marginTop: '6px', fontSize: '16px' }}
      >
        {value}
      </strong>
    </div>
  );
}
