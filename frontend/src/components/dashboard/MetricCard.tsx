import { ReactNode } from "react";

interface MetricCardProps {
  label: string;
  value: string | number;
  note?: string;
  icon?: ReactNode;
  action?: ReactNode;
  variant?: 'default' | 'gold' | 'red';
}

export function MetricCard({ label, value, note, icon, action, variant = 'default' }: MetricCardProps) {
  const variantStyles = {
    default: {
      background: 'var(--color-surface)',
    },
    gold: {
      background: 'var(--color-surface)',
      boxShadow: 'inset 0 -4px 0 var(--color-primary-light)',
    },
    red: {
      background: 'var(--color-surface)',
      boxShadow: 'inset 0 -4px 0 var(--color-error)',
    },
  };

  return (
    <div
      className="card"
      style={{
        ...variantStyles[variant],
        padding: '24px',
        minHeight: '150px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
      }}
    >
      <div className="flex items-center gap-sm" style={{ marginBottom: '16px' }}>
        {icon}
        <span className="label-sm">{label}</span>
      </div>
      <strong style={{ fontSize: '58px', lineHeight: 1, fontWeight: 800 }}>
        {value}
      </strong>
      <div className="flex items-center justify-between gap-md">
        <small style={{ color: 'var(--color-text-secondary)' }}>{note}</small>
        {action}
      </div>
    </div>
  );
}
