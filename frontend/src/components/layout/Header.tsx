import { ReactNode } from "react";

interface HeaderProps {
  children?: ReactNode;
}

export function TopNavigation({ children }: HeaderProps) {
  return (
    <header className="flex items-center justify-between" style={{ padding: '0 32px', height: '64px' }}>
      {children}
    </header>
  );
}

export function Brand() {
  return (
    <div className="flex items-center gap-md">
      <div>
        <strong className="display-lg" style={{ fontSize: '34px', fontWeight: 800, letterSpacing: '-0.02em' }}>
          基金量化选基助手
        </strong>
        <span className="label-sm" style={{ display: 'block', marginTop: '-2px' }}>
          FUND INTELLIGENCE STUDIO
        </span>
      </div>
    </div>
  );
}

interface NavItem {
  label: string;
  active?: boolean;
  onClick?: () => void;
}

export function Navigation({ items }: { items: NavItem[] }) {
  return (
    <nav className="flex items-center gap-xl">
      {items.map((item) => (
        <button
          key={item.label}
          className={item.active ? 'text-primary' : ''}
          style={{
            background: 'transparent',
            border: 'none',
            borderBottom: item.active ? '2px solid var(--color-primary)' : '2px solid transparent',
            borderRadius: 0,
            padding: '7px 0',
            color: item.active ? 'var(--color-primary)' : 'var(--color-text-muted)',
            fontWeight: 600,
            fontSize: '15px',
            cursor: 'pointer',
          }}
          onClick={item.onClick}
        >
          {item.label}
        </button>
      ))}
    </nav>
  );
}
