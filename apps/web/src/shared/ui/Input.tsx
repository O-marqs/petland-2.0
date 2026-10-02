import { useId, type ComponentProps } from 'react';

type Props = ComponentProps<'input'> & { label: string; hint?: string; error?: string };
export function Input({ id, label, hint, error, className = '', ...props }: Props) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  const describedBy =
    [hint && `${inputId}-hint`, error && `${inputId}-error`].filter(Boolean).join(' ') || undefined;
  return (
    <div className="field">
      <label htmlFor={inputId}>
        {label}
        {props.required && <span> (obrigatório)</span>}
      </label>
      {hint && (
        <p id={`${inputId}-hint`} className="field-hint">
          {hint}
        </p>
      )}
      <input
        {...props}
        id={inputId}
        className={`input ${className}`}
        aria-invalid={!!error}
        aria-describedby={describedBy}
      />
      {error && (
        <p id={`${inputId}-error`} className="field-error">
          {error}
        </p>
      )}
    </div>
  );
}
