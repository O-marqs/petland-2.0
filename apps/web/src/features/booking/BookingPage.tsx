import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { CalendarDays, CheckCircle2, Clock3 } from 'lucide-react';
import {
  bookingApi,
  dateTime,
  money,
  timeOnly,
  type Appointment,
  type Availability,
  type Booking,
  type Pet,
} from './api';
import { Failure, Pages } from './Feedback';
import { Button } from '../../shared/ui/Button';
import { Input } from '../../shared/ui/Input';
import { Select, TextArea } from '../../shared/ui/Select';
import { Alert, Skeleton } from '../../shared/ui/Feedback';
import { ApiError } from '../../shared/lib/api';

type Review = { availability: Availability; body: Booking; key: string; reason: string };

export function BookingWizard({
  original,
  staff = false,
  customerId,
}: {
  original?: Appointment;
  staff?: boolean;
  customerId?: string;
}) {
  const navigate = useNavigate();
  const cache = useQueryClient();
  const [pet, setPet] = useState<Pet>();
  const [serviceId, setServiceId] = useState(original?.service_id || '');
  const [day, setDay] = useState('');
  const [reason, setReason] = useState('');
  const [review, setReview] = useState<Review>();
  const reviewHeading = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    if (review) reviewHeading.current?.focus();
  }, [review]);
  const [confirmed, setConfirmed] = useState<Appointment>();
  const [petOffset, setPetOffset] = useState(0);
  const [serviceOffset, setServiceOffset] = useState(0);
  const pets = useQuery({
    queryKey: ['schedule', 'pets', customerId, petOffset],
    queryFn: ({ signal }) => bookingApi.pets(customerId, petOffset, signal),
    enabled: !original,
  });
  const services = useQuery({
    queryKey: ['schedule', 'services', pet?.species_id, pet?.size, serviceOffset],
    queryFn: ({ signal }) => bookingApi.services(pet?.species_id, pet?.size, serviceOffset, signal),
    enabled: !!pet && !original,
  });
  const petId = original?.pet_id || pet?.id || '';
  const availability = useQuery({
    queryKey: ['schedule', 'availability', customerId, petId, serviceId, day, original?.id],
    queryFn: ({ signal }) =>
      bookingApi.availability(petId, serviceId, day, customerId, original?.id, signal),
    enabled: !!petId && !!serviceId && !!day && !review && !confirmed,
    staleTime: 0,
  });
  const mutation = useMutation({
    mutationFn: (value: Review) =>
      original
        ? bookingApi.reschedule(
            staff,
            original.id,
            {
              version: original.version,
              reason: value.reason,
              starts_at: value.body.starts_at,
              configuration_version: value.body.configuration_version,
            },
            value.key,
          )
        : bookingApi.book(value.body, value.key, customerId),
    onSuccess: (appointment) => {
      setConfirmed(appointment);
      void cache.invalidateQueries({ queryKey: ['schedule'] });
    },
  });
  const base = staff ? '/operacao/reservas' : '/app/reservas';
  const retryUnknown =
    mutation.isError && (!(mutation.error instanceof ApiError) || mutation.error.status >= 500);
  const goBack = () => {
    setReview(undefined);
    mutation.reset();
    void availability.refetch();
  };
  if (confirmed)
    return (
      <section className="booking-success identity-card">
        <CheckCircle2 size={42} aria-hidden="true" />
        <span className="eyebrow">TUDO CERTO</span>
        <h1>{original ? 'Novo horário confirmado' : 'Reserva confirmada'}</h1>
        <p>{confirmed.offer.pet_name} tem um cuidado marcado.</p>
        <h2>{dateTime(confirmed.starts_at, confirmed.timezone)}</h2>
        <p>
          {confirmed.offer.service_name} · {confirmed.offer.duration_minutes} minutos ·{' '}
          {money(confirmed.offer.price)}
        </p>
        <p>O aviso será enviado para o e-mail do cadastro.</p>
        <Button onClick={() => navigate(base + '/' + confirmed.id)}>Ver minha reserva</Button>
      </section>
    );
  return (
    <section className="booking-page">
      <span className="eyebrow">{original ? 'REAGENDAMENTO' : 'UM MOMENTO DE CUIDADO'}</span>
      <h1>{original ? 'Escolher outro horário' : 'Agendar um cuidado'}</h1>
      <ol className="booking-progress" aria-label="Etapas do agendamento">
        <li aria-current={!serviceId && !review ? 'step' : undefined}>1. Pet e serviço</li>
        <li aria-current={serviceId && !review ? 'step' : undefined}>2. Data e horário</li>
        <li aria-current={review ? 'step' : undefined}>3. Revisar e confirmar</li>
      </ol>
      {review ? (
        <section className="identity-card booking-review" aria-label="Resumo da reserva">
          <h2 ref={reviewHeading} tabIndex={-1}>
            Confira antes de confirmar
          </h2>
          <dl>
            <dt>Pet</dt>
            <dd>{review.availability.offer.pet_name}</dd>
            <dt>Serviço</dt>
            <dd>{review.availability.offer.service_name}</dd>
            <dt>Quando</dt>
            <dd>{dateTime(review.body.starts_at, review.availability.timezone)}</dd>
            <dt>Duração</dt>
            <dd>{review.availability.offer.duration_minutes} minutos</dd>
            <dt>Valor</dt>
            <dd>{money(review.availability.offer.price)}</dd>
          </dl>
          <p>O profissional será definido pela equipe. A vaga é garantida após a confirmação.</p>
          <p>
            Sem taxa para cancelar ou reagendar. Você pode alterar pela sua conta até{' '}
            {review.availability.change_cutoff_minutes === 0
              ? 'o início do atendimento'
              : review.availability.change_cutoff_minutes + ' minutos antes do atendimento'}
            . Depois desse prazo, procure a equipe.
          </p>
          <p>Tem certeza de que deseja {original ? 'reagendar' : 'reservar'} este horário?</p>
          {mutation.isError && <Failure error={mutation.error} />}
          {retryUnknown && (
            <Alert title="Confira esta tentativa">
              A resposta não chegou. Use “Tentar confirmar novamente” para consultar e concluir a
              mesma tentativa, sem duplicar sua reserva.
            </Alert>
          )}
          <div className="care-actions">
            <Button
              busy={mutation.isPending}
              disabled={mutation.isError && !retryUnknown}
              onClick={() => mutation.mutate(review)}
            >
              {retryUnknown
                ? 'Tentar confirmar novamente'
                : original
                  ? 'Confirmar novo horário'
                  : 'Sim, confirmar reserva'}
            </Button>
            <Button
              variant="secondary"
              disabled={mutation.isPending || retryUnknown}
              onClick={goBack}
            >
              Voltar aos horários
            </Button>
          </div>
        </section>
      ) : (
        <div className="booking-layout">
          <div className="identity-card">
            {original ? (
              <Alert title={original.offer.pet_name + ' · ' + original.offer.service_name}>
                Reserva atual: {dateTime(original.starts_at, original.timezone)}. Valor e duração
                serão mantidos. A reserva atual continua válida até a troca ser confirmada.
              </Alert>
            ) : (
              <>
                <h2>Para quem é o cuidado?</h2>
                {pets.isPending ? (
                  <Skeleton label="Carregando pets" />
                ) : pets.isError ? (
                  <Failure error={pets.error} retry={() => void pets.refetch()} />
                ) : pets.data.items.length ? (
                  <>
                    <Select
                      label="Pet"
                      value={pet?.id || ''}
                      onChange={(e) => {
                        setPet(pets.data.items.find((p) => p.id === e.target.value));
                        setServiceId('');
                        setServiceOffset(0);
                      }}
                      required
                    >
                      <option value="">Selecione um pet</option>
                      {pets.data.items.map((p) => (
                        <option value={p.id} key={p.id}>
                          {p.name}
                        </option>
                      ))}
                    </Select>
                    <Pages offset={petOffset} total={pets.data.total} change={setPetOffset} />
                  </>
                ) : (
                  <p>
                    Cadastre um pet para começar.{' '}
                    <Link
                      to={customerId ? '/operacao/clientes/' + customerId + '/pets' : '/app/pets'}
                    >
                      Ir para pets
                    </Link>
                  </p>
                )}
                {pet &&
                  (services.isPending ? (
                    <Skeleton label="Carregando serviços" />
                  ) : services.isError ? (
                    <Failure error={services.error} retry={() => void services.refetch()} />
                  ) : (
                    <>
                      <Select
                        label="Serviço"
                        required
                        value={serviceId}
                        onChange={(e) => setServiceId(e.target.value)}
                      >
                        <option value="">Selecione um serviço</option>
                        {services.data?.items.map((s) => (
                          <option value={s.id} key={s.id}>
                            {s.name} ·{' '}
                            {money(s.options.find((o) => o.size === pet.size)?.price || '0')}
                          </option>
                        ))}
                      </Select>
                      {!services.data?.items.length && (
                        <p>Nenhum serviço disponível para a espécie e o porte deste pet.</p>
                      )}
                      <Pages
                        offset={serviceOffset}
                        total={services.data?.total || 0}
                        change={setServiceOffset}
                      />
                    </>
                  ))}
              </>
            )}
            {serviceId && (
              <Input
                label="Dia do cuidado"
                type="date"
                required
                value={day}
                onChange={(e) => setDay(e.target.value)}
              />
            )}
            {original && (
              <TextArea
                label="Motivo do reagendamento"
                required
                maxLength={500}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
              />
            )}
          </div>
          <section className="identity-card booking-hours" aria-label="Horários disponíveis">
            <CalendarDays aria-hidden="true" size={28} />
            <h2>Encontre um bom horário</h2>
            {!day || !serviceId ? (
              <p>Escolha o pet, o serviço e o dia para consultar as vagas.</p>
            ) : availability.isPending ? (
              <Skeleton label="Consultando horários" />
            ) : availability.isError ? (
              <Failure error={availability.error} retry={() => void availability.refetch()} />
            ) : (
              availability.data && (
                <>
                  <p>
                    <Clock3 size={16} aria-hidden="true" />{' '}
                    {availability.data.offer.duration_minutes} minutos ·{' '}
                    {money(availability.data.offer.price)}
                  </p>
                  <small>
                    Horários em {availability.data.timezone}. A consulta não segura a vaga.
                  </small>
                  {!availability.data.enabled ? (
                    <Alert title="Agenda ainda não disponível">
                      A equipe está preparando o calendário.
                    </Alert>
                  ) : !availability.data.slots.length ? (
                    <Alert title="Sem vagas neste dia">
                      Tente outra data. Expediente, prazo para reservar e disponibilidade da equipe
                      podem limitar os horários.
                    </Alert>
                  ) : (
                    <div className="booking-slots">
                      {availability.data.slots.map((slot) => (
                        <Button
                          variant="secondary"
                          key={slot.starts_at}
                          disabled={!!original && !reason.trim()}
                          onClick={() => {
                            const current = availability.data;
                            setReview({
                              availability: current,
                              key: crypto.randomUUID(),
                              reason,
                              body: {
                                pet_id: petId,
                                service_id: serviceId,
                                starts_at: slot.starts_at,
                                offer_version: current.offer.version,
                                configuration_version: current.configuration_version,
                              },
                            });
                            window.scrollTo({ top: 0, behavior: 'smooth' });
                          }}
                        >
                          {timeOnly(slot.starts_at, availability.data.timezone)}
                        </Button>
                      ))}
                    </div>
                  )}
                  <Button
                    variant="secondary"
                    busy={availability.isFetching}
                    onClick={() => void availability.refetch()}
                  >
                    Atualizar horários
                  </Button>
                </>
              )
            )}
          </section>
        </div>
      )}
      <Link to={base}>Ver reservas</Link>
    </section>
  );
}

export default function BookingPage() {
  const { customerId } = useParams();
  return <BookingWizard customerId={customerId} staff={!!customerId} />;
}
