import { Alert } from '../../shared/ui/Feedback';
import { Button } from '../../shared/ui/Button';
import { errorMessage } from '../../shared/lib/api';

export function Failure({ error, retry }: { error: unknown; retry?: () => void }) {
  return (
    <>
      <Alert tone="error" title="Não foi possível concluir">
        {errorMessage(error)}
      </Alert>
      {retry && (
        <Button variant="secondary" onClick={retry}>
          Tentar novamente
        </Button>
      )}
    </>
  );
}
export function Pages({
  offset,
  total,
  change,
  size = 20,
}: {
  offset: number;
  total: number;
  change: (value: number) => void;
  size?: number;
}) {
  if (total <= size) return null;
  return (
    <nav className="care-actions" aria-label="Paginação">
      <Button variant="secondary" disabled={!offset} onClick={() => change(offset - size)}>
        Anterior
      </Button>
      <span>
        {offset + 1}–{Math.min(offset + size, total)} de {total}
      </span>
      <Button
        variant="secondary"
        disabled={offset + size >= total}
        onClick={() => change(offset + size)}
      >
        Próxima
      </Button>
    </nav>
  );
}
