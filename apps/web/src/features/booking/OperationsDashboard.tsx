import { Link, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { operationsApi, statusLabels } from './operations-api';
import { dateTime, timeOnly } from './api';
import { Failure } from './Feedback';
import { Input } from '../../shared/ui/Input';
import { Button } from '../../shared/ui/Button';
import { Alert, Badge, Skeleton } from '../../shared/ui/Feedback';

export default function OperationsDashboard() {
  const [params, setParams] = useSearchParams();
  const day = params.get('data') || undefined;
  const mine = params.get('escopo') !== 'equipe';
  const dashboard = useQuery({
    queryKey: ['schedule', 'dashboard', day, mine],
    queryFn: ({ signal }) => operationsApi.dashboard(day, mine, signal),
    refetchInterval: 30000,
  });
  const data = dashboard.data;
  return (
    <section className="operations-page daily-dashboard">
      <header className="daily-heading">
        <div>
          <span className="eyebrow">O CUIDADO COMEÇA NA ORGANIZAÇÃO</span>
          <h1>
            O dia na <em>PetLand.</em>
          </h1>
          <p>Uma visão do dia para cuidar de cada chegada e de quem atende.</p>
        </div>
        <div className="daily-controls">
          <Input
            label="Dia da operação"
            type="date"
            required
            value={day || data?.date || ''}
            onChange={(e) =>
              e.target.value && setParams({ ...Object.fromEntries(params), data: e.target.value })
            }
          />
          <Button
            variant="secondary"
            busy={dashboard.isFetching}
            onClick={() => void dashboard.refetch()}
          >
            Atualizar o dia
          </Button>
        </div>
      </header>
      <nav className="care-actions" aria-label="Organizar o dia">
        <Link className="button button--primary" to="/operacao/clientes">
          Novo cuidado para um cliente
        </Link>
        <Link to="/operacao/escala">Organizar equipe nesta data</Link>
        <Link to="/operacao/agenda?escopo=equipe">Abrir agenda completa</Link>
      </nav>
      {dashboard.isPending ? (
        <Skeleton label="Carregando o dia da equipe" />
      ) : dashboard.isError ? (
        <Failure error={dashboard.error} retry={() => void dashboard.refetch()} />
      ) : (
        data && (
          <>
            <section className="daily-numbers" aria-label="Reservas da loja na data selecionada">
              {[
                [data.total, 'Reservas do dia'],
                [data.by_status.ARRIVED || 0, 'Chegaram'],
                [data.by_status.IN_PROGRESS || 0, 'Em atendimento'],
                [data.by_status.COMPLETED || 0, 'Concluídos'],
              ].map(([value, label]) => (
                <div key={label}>
                  <strong>{value}</strong>
                  <span>{label}</span>
                </div>
              ))}
            </section>
            <div className="daily-columns">
              <section className="daily-queue">
                <div className="care-toolbar">
                  <h2>{mine ? 'Seus próximos cuidados' : 'Próximos cuidados da equipe'}</h2>
                  <div className="care-actions">
                    <Button
                      variant="secondary"
                      aria-pressed={mine}
                      onClick={() => setParams({ ...Object.fromEntries(params), escopo: 'minha' })}
                    >
                      Minha agenda
                    </Button>
                    <Button
                      variant="secondary"
                      aria-pressed={!mine}
                      onClick={() => setParams({ ...Object.fromEntries(params), escopo: 'equipe' })}
                    >
                      Toda a equipe
                    </Button>
                  </div>
                </div>
                {mine && !data.my_resource_id ? (
                  <Alert title="Você ainda não está na capacidade da agenda">
                    Acompanhe toda a equipe ou{' '}
                    <Link to="/operacao/configuracoes">
                      configure sua disponibilidade e serviços
                    </Link>
                    .
                  </Alert>
                ) : !data.appointments.length ? (
                  <p>
                    Nenhum cuidado aberto neste recorte. As reservas confirmadas aparecerão aqui.
                  </p>
                ) : (
                  <ol className="daily-care-list">
                    {data.appointments.map((item) => (
                      <li key={item.appointment.id}>
                        <span className="daily-care-time">
                          {timeOnly(item.appointment.starts_at, data.timezone)}
                        </span>
                        <div>
                          <Badge>{statusLabels[item.appointment.status]}</Badge>
                          <h3>{item.appointment.offer.pet_name}</h3>
                          <p>
                            {item.appointment.offer.service_name} · {item.resource_name}
                          </p>
                          <span>{item.customer_name}</span>
                        </div>
                        <Link to={'/operacao/atendimentos/' + item.appointment.id}>
                          Abrir cuidado
                          <span className="sr-only"> de {item.appointment.offer.pet_name}</span>
                        </Link>
                      </li>
                    ))}
                  </ol>
                )}
                <Link to={'/operacao/agenda?data=' + data.date + (mine ? '' : '&escopo=equipe')}>
                  Ver a agenda deste dia →
                </Link>
              </section>
              <section className="daily-attention">
                <span className="eyebrow">PARA RESOLVER AGORA</span>
                <h2>Atenção ao cuidado</h2>
                <p>
                  Pendências atuais da operação; atendimentos abertos de dias anteriores também
                  aparecem.
                </p>
                {!data.attention.length ? (
                  <p className="daily-clear">Nenhum alerta operacional neste momento.</p>
                ) : (
                  <ol>
                    {data.attention.map((item) => (
                      <li key={item.appointment.id}>
                        <strong>{item.appointment.offer.pet_name}</strong>
                        <span>
                          {item.overdue
                            ? 'Ocupação prevista encerrada'
                            : item.appointment.status === 'BOOKED'
                              ? 'Horário passou; chegada não registrada'
                              : 'Chegou e aguarda início'}
                        </span>
                        <small>
                          {dateTime(item.appointment.starts_at, data.timezone)} ·{' '}
                          {item.resource_name}
                        </small>
                        <Link to={'/operacao/atendimentos/' + item.appointment.id}>
                          Conferir atendimento →
                        </Link>
                      </li>
                    ))}
                  </ol>
                )}
                <p>
                  Canceladas: {data.by_status.CANCELLED || 0} · Não compareceram:{' '}
                  {data.by_status.NO_SHOW || 0}
                </p>
              </section>
            </div>
            <section className="daily-load">
              <div className="care-toolbar">
                <div>
                  <span className="eyebrow">PESSOAS QUE FAZEM O DIA</span>
                  <h2>Distribuição da equipe</h2>
                </div>
                <Link to={'/operacao/escala?data=' + data.date}>Revisar escala →</Link>
              </div>
              <p>
                Minutos reservados e capacidade atual de cada pessoa. As novas reservas priorizam a
                pessoa apta com menor carga planejada no dia. Limites físicos também entram na
                disponibilidade.
              </p>
              {!data.staff.length ? (
                <Alert title="Configure a equipe para abrir horários">
                  <Link to="/operacao/configuracoes">Adicionar pessoas e serviços atendidos</Link>
                </Alert>
              ) : (
                <ul className="workload-list">
                  {data.staff.map((person) => (
                    <li key={person.resource_id}>
                      <div>
                        <h3>{person.name}</h3>
                        <p>
                          {person.planned} reserva(s) · {person.completed} concluído(s)
                        </p>
                      </div>
                      <div>
                        {person.available_minutes > 0 ? (
                          <>
                            <meter
                              aria-label={'Ocupação planejada de ' + person.name}
                              min={0}
                              max={person.available_minutes}
                              value={person.occupied_minutes}
                            />
                            <span>
                              {Math.round(
                                (100 * person.occupied_minutes) / person.available_minutes,
                              )}
                              % · {Math.round(person.occupied_minutes)} /{' '}
                              {Math.round(person.available_minutes)} min
                            </span>
                          </>
                        ) : (
                          <span>Sem capacidade configurada nesta data</span>
                        )}
                      </div>
                      <Link
                        to={'/operacao/agenda?data=' + data.date + '&pessoa=' + person.resource_id}
                      >
                        Ver agenda<span className="sr-only"> de {person.name}</span>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </section>
            <small>
              Atualizado em {dateTime(data.calculated_at, data.timezone)}. Contagens usam a data
              agendada e o estado atual; ocupação considera os horários atuais, sem medir tempo
              efetivamente trabalhado.
            </small>
          </>
        )
      )}
    </section>
  );
}
