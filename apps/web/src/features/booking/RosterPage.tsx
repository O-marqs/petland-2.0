import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { components } from '@petland/api-contract';
import { operationsApi, localDay } from './operations-api';
import { Windows } from './CalendarEditor';
import { Failure } from './Feedback';
import { Input } from '../../shared/ui/Input';
import { TextArea } from '../../shared/ui/Select';
import { Button } from '../../shared/ui/Button';
import { Alert, Skeleton } from '../../shared/ui/Feedback';

type S = components['schemas'];
function RosterEditor({ initial, done }: { initial: S['RosterResponse']; done: () => void }) {
  const [rows, setRows] = useState(initial.rows);
  const [reason, setReason] = useState(initial.reason);
  const [prepared, setPrepared] = useState<{ body: S['RosterInput']; ids: string[] }>();
  const preview = useMutation({
    mutationFn: (body: S['RosterInput']) => operationsApi.previewRoster(initial.date, body),
    onSuccess: (response, body) => setPrepared({ body, ids: response.appointment_ids }),
  });
  const save = useMutation({
    mutationFn: (body: S['RosterInput']) => operationsApi.saveRoster(initial.date, body),
    onSuccess: done,
  });
  const reset = () => {
    setPrepared(undefined);
    preview.reset();
    save.reset();
  };
  const busy = preview.isPending || save.isPending;
  const present = rows.filter((r) => r.windows.length).length;
  return (
    <form
      className="roster-editor"
      onChange={reset}
      onSubmit={(e) => {
        e.preventDefault();
        preview.mutate({
          version: initial.version,
          reason,
          shifts: rows.map(({ resource_id, windows }) => ({ resource_id, windows })),
        });
      }}
    >
      <p className="roster-count" aria-live="polite">
        <strong>{present}</strong> de {rows.length} pessoas com horário nesta data
      </p>
      <p>
        Esta escala substitui os horários individuais somente nesta data. O expediente da loja
        continua limitando o atendimento. Nos demais dias, as semanas e folgas individuais
        permanecem.
      </p>
      <fieldset className="form-lock" disabled={busy}>
        {rows.map((row, index) => (
          <fieldset className="care-fieldset roster-person" key={row.resource_id}>
            <legend>{row.name}</legend>
            <label className="care-check">
              <input
                type="checkbox"
                checked={!!row.windows.length}
                onChange={(e) =>
                  setRows(
                    rows.map((r, i) =>
                      i === index
                        ? { ...r, windows: e.target.checked ? [{ start: -1, end: -1 }] : [] }
                        : r,
                    ),
                  )
                }
              />{' '}
              Trabalha nesta data<span className="sr-only"> — {row.name}</span>
            </label>
            {!!row.windows.length && (
              <Windows
                label={row.name}
                values={row.windows}
                change={(windows) => {
                  reset();
                  setRows(rows.map((r, i) => (i === index ? { ...r, windows } : r)));
                }}
              />
            )}
            {!row.windows.length && <p>Indisponível apenas nesta data.</p>}
          </fieldset>
        ))}
        <TextArea
          label="Motivo da escala"
          required
          maxLength={500}
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          hint="Exemplo: equipe reduzida, saída antecipada ou reforço pontual. O motivo fica no registro operacional."
        />
        <div className="care-actions">
          <Button type="submit" busy={preview.isPending} disabled={!reason.trim()}>
            Conferir impactos da escala
          </Button>
          {initial.custom && (
            <Button
              variant="secondary"
              disabled={busy || !reason.trim()}
              onClick={() => preview.mutate({ version: initial.version, reason, shifts: null })}
            >
              Voltar aos horários habituais nesta data
            </Button>
          )}
        </div>
      </fieldset>
      {preview.isError && <Failure error={preview.error} />}
      {save.isError && <Failure error={save.error} />}
      {prepared && (
        <section className="roster-impact" aria-label="Impacto da escala">
          {prepared.ids.length ? (
            <>
              <Alert
                tone="error"
                title={`${prepared.ids.length} reserva(s) precisam ser resolvidas`}
              >
                Reagende, transfira para uma pessoa que continuará presente ou cancele cada reserva
                antes de salvar. Nada será alterado automaticamente.
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
                Confira a escala. A disponibilidade será validada novamente ao salvar.
              </Alert>
              <Button busy={save.isPending} onClick={() => save.mutate(prepared.body)}>
                Confirmar escala desta data
              </Button>
            </>
          )}
        </section>
      )}
    </form>
  );
}

export default function RosterPage() {
  const cache = useQueryClient();
  const [params, setParams] = useSearchParams();
  const [saved, setSaved] = useState(false);
  const shop = useQuery({
    queryKey: ['schedule', 'establishment'],
    queryFn: ({ signal }) => operationsApi.establishment(signal),
  });
  const day = params.get('data') || localDay(shop.data?.timezone || 'America/Sao_Paulo');
  const roster = useQuery({
    queryKey: ['schedule', 'roster', day],
    queryFn: ({ signal }) => operationsApi.roster(day, signal),
    refetchOnWindowFocus: false,
  });
  return (
    <section className="operations-page">
      <header>
        <span className="eyebrow">PESSOAS, TEMPO E CUIDADO</span>
        <h1>Equipe por data</h1>
        <p>Organize um dia diferente sem refazer a semana inteira.</p>
      </header>
      <Link to="/operacao/configuracoes">← Equipe e horários habituais</Link>
      <Input
        label="Data da escala"
        type="date"
        required
        value={day}
        onChange={(e) => {
          if (e.target.value) {
            setSaved(false);
            setParams({ data: e.target.value });
          }
        }}
      />
      {saved && <Alert tone="success" title="Escala da data atualizada" />}
      {roster.isPending ? (
        <Skeleton label="Carregando escala" />
      ) : roster.isError ? (
        <Failure error={roster.error} retry={() => void roster.refetch()} />
      ) : !roster.data.rows.length ? (
        <Alert title="Adicione pessoas à agenda primeiro">
          <Link to="/operacao/configuracoes">Organizar equipe e serviços</Link>
        </Alert>
      ) : (
        <RosterEditor
          key={day + ':' + roster.data.version}
          initial={roster.data}
          done={() => {
            setSaved(true);
            void cache.invalidateQueries({ queryKey: ['schedule'] });
          }}
        />
      )}
    </section>
  );
}
