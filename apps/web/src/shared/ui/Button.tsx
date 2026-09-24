import type { ComponentProps } from 'react';

type Props = ComponentProps<'button'> & {
  variant?: 'primary' | 'secondary' | 'danger';
  busy?: boolean;
};
export function Button({
  variant = 'primary',
  busy = false,
  disabled,
  children,
  className = '',
  ...props
}: Props) {
  return (
    <button
      type="button"
      {...props}
      className={`button button--${variant} ${className}`}
      disabled={disabled || busy}
      aria-busy={busy || undefined}
    >
      {busy && <span className="spinner" aria-hidden="true" />}
      {children}
    </button>
  );
}
