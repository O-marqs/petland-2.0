import { Link, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { CalendarDays, ArrowRight } from 'lucide-react';
import { bookingApi, dateTime, timeOnly } from './api';
import { operationsApi, statusLabels, addDays, localDay, type Status } from './operations-api';
import { Failure, Pages } from './Feedback';
import { Input } from '../../shared/ui/Input';
import { Select } from '../../shared/ui/Select';
import { Button } from '../../shared/ui/Button';
import { Alert, Badge, Skeleton } from '../../shared/ui/Feedback';

export default function OperationsPage() {
  const [params, setParams] = useSearchParams();
  const settings = useQuery({
    queryKey: ['schedule', 'settings'],
    queryFn: ({ signal }) => bookingApi.settings(signal),
  });
  const date =
    params.get('data') ||
    (settings.data ? localDay(settings.data.configuration.timezone) : undefined);
  const week = params.get('visao') === 'semana';
  const offset = Math.max(0, Number(params.get('pagina')) || 0) * 20;
  const query = {
    date_from: date,
    date_to: date && week ? addDays(date, 6) : date,
    search: params.get('busca') || undefined,
    status: (params.get('status') || undefined) as Status | undefined,
    resource_id: params.get('pessoa') || undefined,
    offset,
    mine: !params.get('pessoa') && params.get('escopo') !== 'equipe',
  };
  const agenda = useQuery({
    queryKey: ['schedule', 'agenda', query],
    queryFn: ({ signal }) => operationsApi.agenda(query, signal),
    refetchInterval: 30000,
    enabled: !week || !!date,
  });
  const shownDate = date || agenda.data?.date_from || '';
  const change = (values: Record<string, string>) =>
    setParams({ ...Object.fromEntries(params), pagina: '0', ...values });
  return (
    <section className="operations-page">
      <header className="operations-heading">
        <div>
          <span className="eyebrow">O CUIDADO DE CADA DIA</span>
          <h1>Agenda da equipe</h1>
          <p>Quem está chegando, quem já está por aqui e o próximo cuidado.</p>
        </div>
        <CalendarDays aria-hidden="true" size={38} />
      </header>
      <div className="care-actions">
        <Link to="/operacao">Hoje na PetLand</Link>
        <Link className="button button--primary" to="/operacao/clientes">
          Agendar para um cliente
        </Link>
        <Link to="/operacao/configuracoes">Equipe e horários</Link>
        <Link to="/operacao/reservas">Consultar histórico</Link>
      </div>
      <section className="identity-card agenda-filters" aria-label="Filtros da agenda">
        <div className="care-actions">
          <Button
            variant="secondary"
            aria-pressed={query.mine}
            onClick={() => change({ escopo: 'minha', pessoa: '' })}
          >
            Minha agenda
          </Button>
          <Button
            variant="secondary"
            aria-pressed={!query.mine}
            onClick={() => change({ escopo: 'equipe', pessoa: '' })}
          >
            Toda a equipe
          </Button>
          <Button
            variant="secondary"
            onClick={() =>
              change({
                data: localDay(
                  agenda.data?.timezone ||
                    settings.data?.configuration.timezone ||
                    'America/Sao_Paulo',
                ),
              })
            }
          >
            Hoje
          </Button>
          <Button
            variant="secondary"
            aria-pressed={!week}
            disabled={!shownDate}
            onClick={() => change({ data: shownDate, visao: 'dia' })}
          >
            Dia
          </Button>
          <Button
            variant="secondary"
            aria-pressed={week}
            disabled={!shownDate}
            onClick={() => change({ data: shownDate, visao: 'semana' })}
          >
            Semana
          </Button>
        </div>
        <form
          key={params.toString() + shownDate}
          className="operations-filter-grid"
          onSubmit={(e) => {
            e.preventDefault();
            const values = new FormData(e.currentTarget);
            change({
              data: String(values.get('data')),
              busca: String(values.get('busca')),
              status: String(values.get('status')),
              pessoa: String(values.get('pessoa')),
              escopo: String(values.get('pessoa')) ? 'equipe' : params.get('escopo') || 'minha',
            });
          }}
        >
          <Input
            type="date"
            name="data"
            label={week ? 'Primeiro dia da semana' : 'Dia da agenda'}
            required
            defaultValue={shownDate}
          />
          <Input
            name="busca"
            label="Buscar pet ou tutor"
            maxLength={100}
            defaultValue={params.get('busca') || ''}
          />
          <Select label="Situação" name="status" defaultValue={query.status || ''}>
            <option value="">Todas</option>
            {Object.entries(statusLabels).map(([id, name]) => (
              <option key={id} value={id}>
                {name}
              </option>
            ))}
          </Select>
          <Select label="Pessoa da equipe" name="pessoa" defaultValue={query.resource_id || ''}>
            <option value="">{query.mine ? 'Somente minha agenda' : 'Todas'}</option>
            {settings.data?.resources.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </Select>
          <Button type="submit">Aplicar filtros</Button>
        </form>
        {settings.isError && (
          <Failure error={settings.error} retry={() => void settings.refetch()} />
        )}
      </section>
      <div className="care-toolbar">
        <p aria-live="polite">
          {agenda.data
            ? `${agenda.data.total} reserva(s) no período · ${agenda.data.timezone}`
            : 'Consultando agenda…'}
        </p>
        <Button variant="secondary" busy={agenda.isFetching} onClick={() => void agenda.refetch()}>
          Atualizar agenda
        </Button>
      </div>
      {agenda.isPending ? (
        <Skeleton label="Carregando agenda" />
      ) : agenda.isError ? (
        <Failure error={agenda.error} retry={() => void agenda.refetch()} />
      ) : (
        <>
          {agenda.data.total === 0 ? (
            <Alert title="Nenhum atendimento neste período">
              Confira outra data ou ajuste os filtros. Novas reservas aparecerão aqui após a
              confirmação.
            </Alert>
          ) : (
            <ol className="agenda-list">
              {agenda.data.items.map((item) => {
                const a = item.appointment;
                return (
                  <li className={'agenda-row agenda-row--' + a.status.toLowerCase()} key={a.id}>
                    <div className="agenda-time">
                      <strong>{timeOnly(a.starts_at, a.timezone)}</strong>
                      <span>
                        {new Intl.DateTimeFormat('pt-BR', {
                          day: '2-digit',
                          month: 'short',
                          timeZone: a.timezone,
                        }).format(new Date(a.starts_at))}
                      </span>
                    </div>
                    <div className="agenda-care">
                      <Badge>{statusLabels[a.status]}</Badge>
                      <h2>{a.offer.pet_name}</h2>
                      <p>
                        {a.offer.service_name} · {a.offer.duration_minutes} min
                      </p>
                      <span>
                        Tutor: {item.customer_name} · {item.resource_name}
                      </span>
                      {item.overdue && (
                        <p className="operation-warning">
                          Tempo reservado encerrado. Confira a ocupação antes de estender.
                        </p>
                      )}
                    </div>
                    <Link
                      className="button button--secondary"
                      to={
                        '/operacao/atendimentos/' +
                        a.id +
                        '?voltar=' +
                        encodeURIComponent('/operacao/agenda?' + params.toString())
                      }
                    >
                      Abrir atendimento <ArrowRight size={18} aria-hidden="true" />
                      <span className="sr-only">
                        {' '}
                        de {a.offer.pet_name}, {dateTime(a.starts_at, a.timezone)}
                      </span>
                    </Link>
                  </li>
                );
              })}
            </ol>
          )}
          <Pages
            offset={offset}
            total={agenda.data.total}
            change={(next) => change({ pagina: String(next / 20) })}
          />
        </>
      )}
    </section>
  );
}
