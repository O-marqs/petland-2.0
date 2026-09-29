import { Alert } from '../../shared/ui/Feedback';
import { Button } from '../../shared/ui/Button';
import { errorMessage } from '../../shared/lib/api';

export function LoadError({ error, retry }: { error: unknown; retry: () => void }) {
  return (
    <div className="care-stack">
      <Alert tone="error" title="Não foi possível carregar">
        {errorMessage(error)}
      </Alert>
      <Button variant="secondary" onClick={retry}>
        Tentar novamente
      </Button>
    </div>
  );
}
export function SaveError({ error, reload }: { error: unknown; reload?: () => void }) {
  return (
    <Alert tone="error" title="Não foi possível salvar">
      {errorMessage(error)} Suas informações continuam no formulário.
      {reload && (
        <Button variant="secondary" onClick={reload}>
          Recarregar dados salvos
        </Button>
      )}
    </Alert>
  );
}
export function Pagination({
  offset,
  total,
  change,
}: {
  offset: number;
  total: number;
  change: (offset: number) => void;
}) {
  if (total <= 20) return null;
  return (
    <nav className="care-actions" aria-label="Paginação">
      <Button variant="secondary" disabled={offset === 0} onClick={() => change(offset - 20)}>
        Anterior
      </Button>
      <span>
        {offset + 1}–{Math.min(offset + 20, total)} de {total}
      </span>
      <Button
        variant="secondary"
        disabled={offset + 20 >= total}
        onClick={() => change(offset + 20)}
      >
        Próxima
      </Button>
    </nav>
  );
}
