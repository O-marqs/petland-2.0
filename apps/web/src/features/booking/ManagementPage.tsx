import { Link, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { operationsApi, addDays, localDay, statusLabels } from './operations-api';
import { dateTime } from './api';
import { Failure, Pages } from './Feedback';
import { Input } from '../../shared/ui/Input';
import { Button } from '../../shared/ui/Button';
import { Alert, Skeleton } from '../../shared/ui/Feedback';

export default function ManagementPage({ audit = false }: { audit?: boolean }) {
  const [params, setParams] = useSearchParams();
  const shop = useQuery({
    queryKey: ['schedule', 'establishment'],
    queryFn: ({ signal }) => operationsApi.establishment(signal),
  });
  const today = localDay(shop.data?.timezone || 'America/Sao_Paulo');
  const first = params.get('inicio') || addDays(today, -29),
    last = params.get('fim') || today;
  const offset = Math.max(0, Number(params.get('pagina')) || 0) * 20;
  const metrics = useQuery({
    queryKey: ['management', 'metrics', first, last],
    queryFn: ({ signal }) => operationsApi.metrics(first, last, signal),
    enabled: !audit && !!shop.data,
  });
  const log = useQuery({
    queryKey: ['management', 'audit', first, last, params.toString()],
    queryFn: ({ signal }) =>
      operationsApi.audit(
        {
          start: first + 'T00:00:00Z',
          end: addDays(last, 1) + 'T00:00:00Z',
          action: params.get('acao') || undefined,
          actor_id: params.get('autor') || undefined,
          target_id: params.get('objeto') || undefined,
          offset,
        },
        signal,
      ),
    enabled: audit,
  });
  return (
    <section className="operations-page">
      <header>
        <span className="eyebrow">GESTÃO PETLAND</span>
        <h1>{audit ? 'Auditoria' : 'Visão geral'}</h1>
        <p>
          {audit
            ? 'Ações registradas com autoria, data e objeto, sem textos de notas ou credenciais.'
            : 'Um retrato da agenda para apoiar as decisões da equipe.'}
        </p>
      </header>
      <nav className="care-actions" aria-label="Gestão">
        <Link to="/gestao">Visão geral</Link>
        <Link to="/operacao/agenda">Abrir agenda</Link>
        <Link to="/gestao/acessos">Pessoas e acessos</Link>
        <Link to="/operacao/configuracoes">Configurações</Link>
        <Link to="/gestao/auditoria">Ver auditoria</Link>
      </nav>
      <form
        key={params.toString() + first}
        className="identity-card operations-filter-grid"
        onSubmit={(e) => {
          e.preventDefault();
          const form = new FormData(e.currentTarget);
          setParams({
            inicio: String(form.get('inicio')),
            fim: String(form.get('fim')),
            acao: String(form.get('acao') || ''),
            autor: String(form.get('autor') || ''),
            objeto: String(form.get('objeto') || ''),
          });
        }}
      >
        <Input label="Início do período" type="date" name="inicio" defaultValue={first} required />
        <Input label="Fim do período" type="date" name="fim" defaultValue={last} required />
        {audit && (
          <>
            <Input
              label="Ação exata"
              name="acao"
              maxLength={64}
              defaultValue={params.get('acao') || ''}
              hint="Exemplo: appointment.complete"
            />
            <Input
              label="Identificador do autor"
              name="autor"
              defaultValue={params.get('autor') || ''}
            />
            <Input
              label="Identificador do objeto"
              name="objeto"
              defaultValue={params.get('objeto') || ''}
            />
          </>
        )}
        <Button type="submit">Consultar período</Button>
        <small>
          {audit ? 'Datas e horários da auditoria em UTC.' : 'Datas no fuso da loja.'} Intervalo
          máximo: 31 dias.
        </small>
      </form>
      {shop.isError && <Failure error={shop.error} retry={() => void shop.refetch()} />}
      {audit ? (
        log.isPending ? (
          <Skeleton label="Carregando auditoria" />
        ) : log.isError ? (
          <Failure error={log.error} retry={() => void log.refetch()} />
        ) : (
          <>
            <p>{log.data.total} registro(s) encontrados.</p>
            {!log.data.items.length && (
              <Alert title="Nenhum registro neste recorte">
                Ajuste os filtros para consultar outro período.
              </Alert>
            )}
            <ol className="operation-notes">
              {log.data.items.map((e) => (
                <li className="identity-card" key={e.id}>
                  <strong>{e.action}</strong>
                  <p>
                    {dateTime(e.occurred_at, 'UTC')} (UTC) ·{' '}
                    {e.result === 'success' ? 'Concluída' : e.result}
                  </p>
                  <small>
                    Autor: {e.actor_user_id || 'Sistema'}
                    <br />
                    Objeto: {e.target_id || 'Não se aplica'}
                  </small>
                  {e.action.startsWith('appointment.') && e.target_id && (
                    <p>
                      <Link to={'/operacao/atendimentos/' + e.target_id}>
                        Consultar atendimento
                      </Link>
                    </p>
                  )}
                </li>
              ))}
            </ol>
            <Pages
              offset={offset}
              total={log.data.total}
              change={(next) =>
                setParams({ ...Object.fromEntries(params), pagina: String(next / 20) })
              }
            />
          </>
        )
      ) : metrics.isPending ? (
        <Skeleton label="Calculando visão geral" />
      ) : metrics.isError ? (
        <Failure error={metrics.error} retry={() => void metrics.refetch()} />
      ) : (
        <>
          <div className="operation-metrics">
            {[
              ['Reservas no período', metrics.data.total],
              ['Concluídas', metrics.data.by_status.COMPLETED],
              ['Canceladas', metrics.data.by_status.CANCELLED],
              ['Não compareceu', metrics.data.by_status.NO_SHOW],
            ].map(([label, value]) => (
              <article className="metric-card" key={label}>
                <strong>{value}</strong>
                <span>{label}</span>
              </article>
            ))}
          </div>
          <div className="attendance-layout">
            <section className="identity-card">
              <h2>Ocupação da agenda</h2>
              <strong className="metric-value">
                {metrics.data.occupancy_percent === null
                  ? 'Sem capacidade configurada'
                  : metrics.data.occupancy_percent.toLocaleString('pt-BR') + '%'}
              </strong>
              <p>
                {metrics.data.occupied_minutes.toLocaleString('pt-BR')} minutos reservados /{' '}
                {metrics.data.available_minutes.toLocaleString('pt-BR')} minutos disponíveis.
              </p>
              <p>
                Referência: configuração atual de horários e pessoas. Inclui preparação, intervalos
                e extensões; exclui cancelamentos e faltas. Não mede tempo efetivamente trabalhado.
              </p>
              <small>
                Ao consultar o passado, mudanças posteriores de expediente ou equipe podem alterar a
                comparação. O percentual pode superar 100%.
              </small>
            </section>
            <section className="identity-card">
              <h2>Reservas por situação</h2>
              <dl className="operation-facts">
                {Object.entries(statusLabels).map(([id, label]) => (
                  <div className="operation-fact" key={id}>
                    <dt>{label}</dt>
                    <dd>{metrics.data.by_status[id]}</dd>
                  </div>
                ))}
              </dl>
            </section>
          </div>
          <section className="identity-card">
            <h2>Reservas por serviço</h2>
            <p>Contagem pelo horário agendado, incluindo todos os estados.</p>
            {!metrics.data.total ? (
              <p>Nenhuma reserva no período selecionado.</p>
            ) : (
              <ul className="service-counts">
                {Object.entries(metrics.data.by_service).map(([name, count]) => (
                  <li key={name}>
                    <span>{name}</span>
                    <meter
                      aria-label={'Reservas de ' + name}
                      value={count}
                      min={0}
                      max={metrics.data.total}
                    />
                    <strong>{count}</strong>
                  </li>
                ))}
              </ul>
            )}
            <p>Atualizado em {dateTime(metrics.data.calculated_at, metrics.data.timezone)}.</p>
          </section>
        </>
      )}
    </section>
  );
}
