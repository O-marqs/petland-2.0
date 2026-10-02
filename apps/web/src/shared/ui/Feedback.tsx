import type { ReactNode } from 'react';
import { CircleAlert, CircleCheck, Info, Inbox } from 'lucide-react';

export function Alert({
  tone = 'info',
  title,
  children,
}: {
  tone?: 'info' | 'success' | 'error';
  title: string;
  children?: ReactNode;
}) {
  const Icon = tone === 'error' ? CircleAlert : tone === 'success' ? CircleCheck : Info;
  return (
    <div className={`alert alert--${tone}`} role={tone === 'error' ? 'alert' : 'status'}>
      <Icon size={22} aria-hidden="true" />
      <div>
        <strong>{title}</strong>
        {children && <div>{children}</div>}
      </div>
    </div>
  );
}
export function Badge({ children }: { children: ReactNode }) {
  return <span className="badge">{children}</span>;
}
export function Skeleton({ label = 'Carregando' }: { label?: string }) {
  return (
    <div className="skeleton-wrap" role="status">
      <span className="sr-only">{label}</span>
      <div className="skeleton" />
      <div className="skeleton skeleton--short" />
    </div>
  );
}
export function EmptyState({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="empty-state">
      <Inbox size={32} aria-hidden="true" />
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  );
}
