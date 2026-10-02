import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { components } from '@petland/api-contract';
import { operationsApi } from './operations-api';
import { bookingApi } from './api';
import { Failure, Pages } from './Feedback';
import { Input } from '../../shared/ui/Input';
import { Button } from '../../shared/ui/Button';
import { Alert, Skeleton } from '../../shared/ui/Feedback';

type S = components['schemas'];
function PoolEditor({ initial, done }: { initial: S['PoolsInput']; done: () => void }) {
  const [pools, setPools] = useState(initial.pools);
  const [offset, setOffset] = useState(0);
  const [prepared, setPrepared] = useState<{ body: S['PoolsInput']; ids: string[] }>();
  const services = useQuery({
    queryKey: ['schedule', 'staffServices', offset],
    queryFn: ({ signal }) => bookingApi.staffServices(offset, signal),
  });
  const preview = useMutation({
    mutationFn: operationsApi.previewPools,
    onSuccess: (value, body) => setPrepared({ body, ids: value.appointment_ids }),
  });
  const save = useMutation({ mutationFn: operationsApi.savePools, onSuccess: done });
  const reset = () => {
    setPrepared(undefined);
    preview.reset();
    save.reset();
  };
  const patch = (id: string, values: Partial<S['PoolInput']>) => {
    reset();
    setPools(pools.map((p) => (p.id === id ? { ...p, ...values } : p)));
  };
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        preview.mutate({ version: initial.version, pools });
      }}
    >
      <fieldset className="form-lock" disabled={preview.isPending || save.isPending}>
        {!pools.length && (
          <Alert title="Nenhum limite físico configurado">
            A disponibilidade considera apenas pessoas, horários e duração até que você configure os
            recursos compartilhados.
          </Alert>
        )}
        {pools.map((pool, index) => (
          <fieldset className="care-fieldset" key={pool.id}>
            <legend>Recurso compartilhado {index + 1}</legend>
            <div className="care-form-grid">
              <Input
                label={`Nome do recurso ${index + 1}`}
                required
                maxLength={100}
                value={pool.name}
                onChange={(e) => patch(pool.id, { name: e.target.value })}
              />
              <Input
                label={`Quantidade simultânea ${index + 1}`}
                type="number"
                min={1}
                max={100}
                required
                value={pool.capacity}
                onChange={(e) => patch(pool.id, { capacity: Number(e.target.value) })}
              />
            </div>
            <label className="care-check">
              <input
                type="checkbox"
                checked={pool.active}
                onChange={(e) => patch(pool.id, { active: e.target.checked })}
              />
              Disponível<span className="sr-only"> — recurso {index + 1}</span>
            </label>
            <p>
              Os serviços marcados compartilham esta quantidade, incluindo preparação e intervalo
              final. Indisponível bloqueia os serviços vinculados; remover o limite volta a
              considerar apenas a equipe.
            </p>
            <fieldset className="care-fieldset">
              <legend>Serviços que usam este recurso</legend>
              {services.isPending ? (
                <Skeleton label="Carregando serviços" />
              ) : services.isError ? (
                <Failure error={services.error} />
              ) : (
                <>
                  {services.data.items.map((s) => (
                    <label className="care-check" key={s.id}>
                      <input
                        type="checkbox"
                        checked={pool.service_ids.includes(s.id)}
                        onChange={(e) =>
                          patch(pool.id, {
                            service_ids: e.target.checked
                              ? [...pool.service_ids, s.id]
                              : pool.service_ids.filter((id) => id !== s.id),
                          })
                        }
                      />
                      {s.name}
                      <span className="sr-only"> — recurso {index + 1}</span>
                    </label>
                  ))}
                  <Pages
                    offset={offset}
                    total={services.data.total}
                    size={100}
                    change={setOffset}
                  />
                </>
              )}
            </fieldset>
            <Button
              variant="secondary"
              onClick={() => {
                reset();
                setPools(pools.filter((p) => p.id !== pool.id));
              }}
            >
              Remover limite configurado<span className="sr-only"> {index + 1}</span>
            </Button>
          </fieldset>
        ))}
        <div className="care-actions">
          <Button
            variant="secondary"
            disabled={pools.length >= 32}
            onClick={() => {
              reset();
              setPools([
                ...pools,
                { id: crypto.randomUUID(), name: '', capacity: 1, active: true, service_ids: [] },
              ]);
            }}
          >
            Adicionar recurso compartilhado
          </Button>
          <Button
            type="submit"
            busy={preview.isPending}
            disabled={!services.data || pools.some((p) => !p.service_ids.length)}
          >
            Conferir impactos da capacidade
          </Button>
        </div>
      </fieldset>
      {preview.isError && <Failure error={preview.error} />}
      {save.isError && <Failure error={save.error} />}
      {prepared &&
        (prepared.ids.length ? (
          <>
            <Alert tone="error" title={`${prepared.ids.length} reserva(s) incompatíveis`}>
              Resolva os horários antes de reduzir ou fechar a capacidade. As reservas atuais
              permanecem intactas.
            </Alert>
            <ul>
              {prepared.ids.map((id) => (
                <li key={id}>
                  <Link to={'/operacao/atendimentos/' + id}>
                    Resolver atendimento {id.slice(0, 8)}
                  </Link>
                </li>
              ))}
            </ul>
          </>
        ) : (
          <>
            <Alert title="Sem reservas incompatíveis nesta prévia">
              A regra será validada novamente ao confirmar.
            </Alert>
            <Button busy={save.isPending} onClick={() => save.mutate(prepared.body)}>
              Confirmar capacidade física
            </Button>
          </>
        ))}
    </form>
  );
}

export default function CapacityPage() {
  const cache = useQueryClient();
  const [saved, setSaved] = useState(false);
  const query = useQuery({
    queryKey: ['schedule', 'pools'],
    queryFn: ({ signal }) => operationsApi.pools(signal),
    refetchOnWindowFocus: false,
  });
  return (
    <section className="operations-page">
      <header>
        <span className="eyebrow">O ESPAÇO TAMBÉM CONTA</span>
        <h1>Capacidade física</h1>
        <p>Banheiras, mesas e outros recursos limitam quantos cuidados podem acontecer juntos.</p>
      </header>
      <Link to="/operacao/configuracoes">← Equipe e horários</Link>
      {saved && <Alert tone="success" title="Capacidade atualizada" />}
      {query.isPending ? (
        <Skeleton label="Carregando capacidade" />
      ) : query.isError ? (
        <Failure error={query.error} retry={() => void query.refetch()} />
      ) : (
        <PoolEditor
          key={query.data.version}
          initial={query.data}
          done={() => {
            setSaved(true);
            void cache.invalidateQueries({ queryKey: ['schedule'] });
          }}
        />
      )}
    </section>
  );
}
