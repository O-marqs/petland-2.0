import { useQuery } from '@tanstack/react-query';
import { CircleCheck, RefreshCw, CircleAlert } from 'lucide-react';
import { getReadiness, ApiError } from '../../shared/lib/api';
import { Button } from '../../shared/ui/Button';

export function ConnectionStatus() {
  const status = useQuery({
    queryKey: ['system', 'readiness'],
    queryFn: ({ signal }) => getReadiness(signal),
    retry: false,
    refetchInterval: 30000,
  });
  const ready = status.isSuccess && status.data.status === 'ready';
  return (
    <section className="connection-status" aria-label="Conexão do ambiente">
      <div aria-live="polite">
        {status.isFetching ? (
          <RefreshCw size={18} aria-hidden="true" />
        ) : ready ? (
          <CircleCheck size={18} aria-hidden="true" />
        ) : (
          <CircleAlert size={18} aria-hidden="true" />
        )}
        <span>
          {status.isFetching
            ? 'Verificando conexão…'
            : ready
              ? 'Ambiente conectado'
              : 'Conexão indisponível no momento'}
        </span>
      </div>
      {!ready && !status.isFetching && (
        <>
          <Button variant="secondary" onClick={() => void status.refetch()}>
            Tentar novamente
          </Button>
          {status.error instanceof ApiError && status.error.requestId && (
            <small>Referência: {status.error.requestId}</small>
          )}
        </>
      )}
      {ready && <small>Consulta em tempo real</small>}
    </section>
  );
}
