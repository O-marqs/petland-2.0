import { useId, type ComponentProps } from 'react';

export function Select({
  label,
  error,
  hint,
  children,
  ...props
}: ComponentProps<'select'> & {
  label: string;
  error?: string;
  hint?: string;
}) {
  const id = useId();
  return (
    <div className="field">
      <label htmlFor={id}>
        {label}
        {props.required && ' (obrigatório)'}
      </label>
      <select
        {...props}
        id={id}
        aria-invalid={!!error}
        aria-describedby={error || hint ? id + '-help' : undefined}
      >
        {children}
      </select>
      {(error || hint) && (
        <p id={id + '-help'} className={error ? 'field-error' : 'field-hint'}>
          {error || hint}
        </p>
      )}
    </div>
  );
}

export function TextArea({
  label,
  error,
  hint,
  ...props
}: ComponentProps<'textarea'> & {
  label: string;
  error?: string;
  hint?: string;
}) {
  const id = useId();
  return (
    <div className="field">
      <label htmlFor={id}>
        {label}
        {props.required && ' (obrigatório)'}
      </label>
      <textarea
        {...props}
        id={id}
        aria-invalid={!!error}
        aria-describedby={error || hint ? id + '-help' : undefined}
      />
      {(error || hint) && (
        <p id={id + '-help'} className={error ? 'field-error' : 'field-hint'}>
          {error || hint}
        </p>
      )}
    </div>
  );
}
