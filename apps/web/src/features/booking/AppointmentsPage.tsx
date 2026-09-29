import { useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { bookingApi, dateTime, money, type Appointment } from './api';
import { BookingWizard } from './BookingPage';
import { Failure, Pages } from './Feedback';
import { Button } from '../../shared/ui/Button';
import { TextArea } from '../../shared/ui/Select';
import { Alert, Badge, Skeleton } from '../../shared/ui/Feedback';
import { statusLabels, eventLabels } from './operations-api';
import { Select } from '../../shared/ui/Select';

function Detail({ id, staff }: { id: string; staff: boolean }) {
  const cache = useQueryClient();
  const [reschedule, setReschedule] = useState<Appointment>();
  const [cancel, setCancel] = useState<{
    appointment: Appointment;
    reason: string;
    key: string;
    submitted: boolean;
  }>();
  const detail = useQuery({
    queryKey: ['schedule', 'detail', staff, id],
    queryFn: ({ signal }) => bookingApi.detail(staff, id, signal),
  });
  const mutation = useMutation({
    mutationFn: (value: NonNullable<typeof cancel>) =>
      bookingApi.cancel(
        staff,
        id,
        { version: value.appointment.version, reason: value.reason },
        value.key,
      ),
    onSuccess: () => {
      setCancel(undefined);
      void cache.invalidateQueries({ queryKey: ['schedule'] });
    },
  });
  const base = staff ? '/operacao/reservas' : '/app/reservas';
  if (reschedule)
    return (
      <BookingWizard
        original={reschedule}
        staff={staff}
        customerId={staff ? reschedule.customer_id : undefined}
      />
    );
  if (detail.isPending) return <Skeleton label="Carregando reserva" />;
  if (detail.isError) return <Failure error={detail.error} retry={() => void detail.refetch()} />;
  const a = detail.data.appointment;
  return (
    <section>
      <Link to={base}>← Todas as reservas</Link>
      <span className="eyebrow">CUIDADO AGENDADO</span>
      <h1>{a.offer.pet_name}</h1>
      <section className="identity-card">
        <Badge>{statusLabels[a.status]}</Badge>
        <h2>{a.offer.service_name}</h2>
        <p>{dateTime(a.starts_at, a.timezone)}</p>
        <p>
          {a.offer.duration_minutes} minutos · {money(a.offer.price)}
        </p>
        <p>
          Alterações pela conta do cliente: até{' '}
          {a.change_cutoff_minutes === 0
            ? 'o início do atendimento'
            : a.change_cutoff_minutes + ' minutos antes do atendimento'}
          . Sem taxa.
        </p>
        <p>Cancelamentos e reagendamentos geram um aviso para o e-mail do cadastro.</p>
        {staff && (
          <Link className="button button--primary" to={'/operacao/atendimentos/' + a.id}>
            Abrir atendimento
          </Link>
        )}
        {a.completed_at && <p>Concluído em {dateTime(a.completed_at, a.timezone)}.</p>}
        {a.status === 'BOOKED' && new Date(a.starts_at) > new Date() && !cancel && (
          <div className="care-actions">
            <Button onClick={() => setReschedule(a)}>Reagendar</Button>
            <Button
              variant="secondary"
              onClick={() => {
                mutation.reset();
                setCancel({
                  appointment: a,
                  reason: '',
                  key: crypto.randomUUID(),
                  submitted: false,
                });
              }}
            >
              Cancelar reserva
            </Button>
          </div>
        )}
        {cancel && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const value = { ...cancel, submitted: true };
              setCancel(value);
              mutation.mutate(value);
            }}
          >
            <h2>Confirmar cancelamento</h2>
            <p>A vaga será liberada e o histórico será mantido.</p>
            <TextArea
              required
              label="Motivo do cancelamento"
              maxLength={500}
              value={cancel.reason}
              disabled={cancel.submitted}
              onChange={(e) => setCancel({ ...cancel, reason: e.target.value })}
            />
            {mutation.isError && <Failure error={mutation.error} />}
            <div className="care-actions">
              <Button
                variant="danger"
                type="submit"
                busy={mutation.isPending}
                disabled={!cancel.reason.trim()}
              >
                {cancel.submitted ? 'Tentar cancelar novamente' : 'Sim, cancelar reserva'}
              </Button>
              <Button
                variant="secondary"
                disabled={mutation.isPending}
                onClick={() => {
                  setCancel(undefined);
                  mutation.reset();
                  void detail.refetch();
                }}
              >
                Voltar ao detalhe
              </Button>
            </div>
          </form>
        )}
      </section>
      {!!detail.data.summaries?.length && (
        <section className="identity-card">
          <h2>Resumo do cuidado</h2>
          {detail.data.summaries?.map((n) => (
            <article key={n.id}>
              <p className="preserve-lines">{n.body}</p>
              <small>{dateTime(n.occurred_at, a.timezone)}</small>
            </article>
          ))}
        </section>
      )}
      <section className="identity-card">
        <h2>Histórico desta reserva</h2>
        <ol className="booking-history">
          {detail.data.events.map((event) => (
            <li key={event.id}>
              <strong>{eventLabels[event.kind] || event.kind}</strong>
              <span>{dateTime(event.occurred_at, a.timezone)}</span>
              {event.reason && <p>{event.reason}</p>}
              <small>Horário registrado: {dateTime(event.starts_at, a.timezone)}</small>
            </li>
          ))}
        </ol>
      </section>
    </section>
  );
}
export default function AppointmentsPage({ staff = false }: { staff?: boolean }) {
  const { appointmentId } = useParams();
  const [params, setParams] = useSearchParams();
  const offset = Math.max(0, Number(params.get('pagina')) || 0) * 20;
  const setOffset = (value: number) =>
    setParams({ ...Object.fromEntries(params), pagina: String(value / 20) });
  const period = (params.get('periodo') || 'all') as 'all' | 'upcoming' | 'history';
  const filters = {
    period,
    customer_id: staff ? params.get('cliente') || undefined : undefined,
    pet_id: params.get('pet') || undefined,
    status: (params.get('status') || undefined) as Appointment['status'] | undefined,
  };
  const list = useQuery({
    queryKey: ['schedule', 'appointments', staff, offset, filters],
    queryFn: ({ signal }) => bookingApi.list(staff, offset, signal, filters),
    enabled: !appointmentId,
  });
  const base = staff ? '/operacao/reservas' : '/app/reservas';
  if (appointmentId) return <Detail key={appointmentId} id={appointmentId} staff={staff} />;
  return (
    <section>
      <span className="eyebrow">{staff ? 'CUIDADOS DA LOJA' : 'A PRÓXIMA VISITA'}</span>
      <h1>{staff ? 'Reservas da equipe' : 'Minhas reservas'}</h1>
      <p>Consulte os horários confirmados e acompanhe as alterações.</p>
      <div className="care-actions" aria-label="Período das reservas">
        {[
          ['all', 'Todas'],
          ['upcoming', 'Próximos cuidados'],
          ['history', 'Histórico'],
        ].map(([id, label]) => (
          <Button
            key={id}
            variant="secondary"
            aria-pressed={period === id}
            onClick={() => setParams({ ...Object.fromEntries(params), periodo: id, pagina: '0' })}
          >
            {label}
          </Button>
        ))}
      </div>
      <Select
        label="Filtrar situação"
        value={filters.status || ''}
        onChange={(e) =>
          setParams({ ...Object.fromEntries(params), status: e.target.value, pagina: '0' })
        }
      >
        <option value="">Todas as situações</option>
        {Object.entries(statusLabels).map(([id, label]) => (
          <option key={id} value={id}>
            {label}
          </option>
        ))}
      </Select>
      {(filters.customer_id || filters.pet_id) && (
        <p>
          Exibindo somente o cadastro selecionado.{' '}
          <Link to={base}>Ver todos os cadastros permitidos</Link>
        </p>
      )}
      <div className="care-actions">
        <Link className="button button--primary" to={staff ? '/operacao/clientes' : '/app/agendar'}>
          {staff ? 'Escolher cliente para agendar' : 'Agendar um cuidado'}
        </Link>
        <Button variant="secondary" busy={list.isFetching} onClick={() => void list.refetch()}>
          Atualizar reservas
        </Button>
      </div>
      {list.isPending ? (
        <Skeleton label="Carregando reservas" />
      ) : list.isError ? (
        <Failure error={list.error} retry={() => void list.refetch()} />
      ) : (
        <>
          {!list.data.items.length && (
            <Alert title="Nenhuma reserva por aqui">
              Os próximos cuidados aparecerão aqui após a confirmação.
            </Alert>
          )}
          <div className="care-grid">
            {list.data.items.map((a) => (
              <article className="identity-card" key={a.id}>
                <Badge>{statusLabels[a.status]}</Badge>
                <h2>{a.offer.pet_name}</h2>
                <p>{a.offer.service_name}</p>
                <strong>{dateTime(a.starts_at, a.timezone)}</strong>
                <p>
                  {money(a.offer.price)} · {a.offer.duration_minutes} minutos
                </p>
                <Link className="button button--secondary" to={base + '/' + a.id}>
                  Ver reserva<span className="sr-only"> de {a.offer.pet_name}</span>
                </Link>
              </article>
            ))}
          </div>
          <Pages offset={offset} total={list.data.total} change={setOffset} />
        </>
      )}
    </section>
  );
}
