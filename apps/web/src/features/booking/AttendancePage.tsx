import { Fragment, useEffect, useRef, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { bookingApi, dateTime, money } from './api';
import {
  operationsApi,
  actionLabels,
  eventLabels,
  statusLabels,
  type Attendance,
  type Transition,
} from './operations-api';
import { Failure } from './Feedback';
import { Input } from '../../shared/ui/Input';
import { Select, TextArea } from '../../shared/ui/Select';
import { Button } from '../../shared/ui/Button';
import { Alert, Badge, Skeleton } from '../../shared/ui/Feedback';
import { ApiError } from '../../shared/lib/api';
import { CommunicationHistory } from './CommunicationHistory';

type Attempt = {
  key: string;
  version: number;
  reason: string;
  body: string;
  visibility: 'INTERNAL' | 'PUBLIC';
  until: string;
  resource: string;
  care_version?: number;
};

function ActionForm({
  action,
  detail,
  close,
  done,
}: {
  action: string;
  detail: Attendance;
  close: () => void;
  done: () => void;
}) {
  const a = detail.item.appointment;
  const [attempt, setAttempt] = useState<Attempt>();
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    heading.current?.focus();
  }, []);
  const settings = useQuery({
    queryKey: ['schedule', 'settings'],
    queryFn: ({ signal }) => bookingApi.settings(signal),
    enabled: action === 'extend' || action === 'transfer',
  });
  const mutation = useMutation({
    mutationFn: (v: Attempt) =>
      action === 'note'
        ? operationsApi.note(
            a.id,
            { version: v.version, body: v.body, visibility: v.visibility },
            v.key,
          )
        : action === 'extend'
          ? operationsApi.extend(
              a.id,
              {
                version: v.version,
                reason: v.reason,
                until: v.until,
                resource_id: v.resource || undefined,
              },
              v.key,
            )
          : action === 'transfer'
            ? operationsApi.transfer(
                a.id,
                { version: v.version, reason: v.reason, resource_id: v.resource },
                v.key,
              )
            : operationsApi.transition(
                a.id,
                {
                  version: v.version,
                  operation: action as Transition['operation'],
                  reason: v.reason,
                  summary: action === 'complete' ? v.body : '',
                  care_version: v.care_version,
                },
                v.key,
              ),
    onSuccess: done,
  });
  const conflict = mutation.error instanceof ApiError && mutation.error.status < 500;
  return (
    <section className="identity-card operation-action" aria-labelledby="action-title">
      <h2 id="action-title" ref={heading} tabIndex={-1}>
        {actionLabels[action]}
      </h2>
      <p>
        {action === 'note'
          ? 'Notas ficam registradas com autoria e data. Uma correção deve ser uma nova anotação.'
          : `Confirme esta ação para ${a.offer.pet_name}. O histórico será preservado.`}
      </p>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (attempt) {
            mutation.mutate(attempt);
            return;
          }
          const data = new FormData(e.currentTarget);
          const extra = Number(data.get('minutes'));
          const value: Attempt = {
            key: crypto.randomUUID(),
            version: a.version,
            reason: String(data.get('reason') || ''),
            body: String(data.get('body') || ''),
            visibility: data.get('visibility') === 'PUBLIC' ? 'PUBLIC' : 'INTERNAL',
            until:
              action === 'extend'
                ? new Date(
                    new Date(a.reserved_until || a.ends_at).getTime() + extra * 60000,
                  ).toISOString()
                : '',
            resource: String(data.get('resource') || ''),
            care_version: data.get('care_ack') ? detail.context.pet_version : undefined,
          };
          setAttempt(value);
          mutation.mutate(value);
        }}
      >
        <fieldset className="form-lock" disabled={!!attempt}>
          {action === 'note' && (
            <Select label="Quem pode ler" name="visibility" defaultValue="INTERNAL">
              <option value="INTERNAL">Somente a equipe — nota interna</option>
              <option value="PUBLIC">Cliente e equipe — publicar resumo</option>
            </Select>
          )}
          {(action === 'note' || action === 'complete') && (
            <TextArea
              label={action === 'complete' ? 'Resumo para o cliente' : 'Anotação'}
              name="body"
              maxLength={2000}
              required={action === 'note'}
              hint={
                action === 'complete'
                  ? 'Opcional. Este texto será publicado para o cliente. Não copie notas internas.'
                  : 'Até 2.000 caracteres. A visibilidade selecionada será aplicada ao salvar.'
              }
            />
          )}
          {['no_show', 'cancel_exception', 'extend', 'transfer'].includes(action) && (
            <TextArea
              label="Motivo"
              name="reason"
              required
              maxLength={500}
              hint={
                action === 'transfer'
                  ? 'O motivo e a troca de responsável ficam no histórico interno da equipe.'
                  : 'O motivo faz parte do histórico visível ao cliente.'
              }
            />
          )}
          {action === 'start' && detail.context.allergies && (
            <label className="care-check critical-ack">
              <input type="checkbox" name="care_ack" required />
              Li as alergias e restrições críticas atuais deste pet antes de iniciar.
            </label>
          )}
          {action === 'transfer' && (
            <>
              <p>
                Responsável atual: <strong>{detail.item.resource_name}</strong>. Horário, duração e
                preço permanecem iguais. A nova pessoa precisa ter o período livre e estar apta ao
                serviço.
              </p>
              <Select label="Nova pessoa responsável" name="resource" required defaultValue="">
                <option value="">Selecione quem assumirá</option>
                {settings.data?.resources
                  .filter(
                    (r) =>
                      r.active &&
                      r.id !== detail.item.resource_id &&
                      r.service_ids.includes(a.service_id),
                  )
                  .map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.name}
                    </option>
                  ))}
              </Select>
              {settings.isError && <Failure error={settings.error} />}
            </>
          )}
          {action === 'extend' && (
            <>
              <p>
                Reservado até {dateTime(a.reserved_until || a.ends_at, a.timezone)}. O horário
                original e o preço são mantidos. Outras reservas não serão alteradas.
              </p>
              <Input
                type="number"
                label="Minutos adicionais"
                name="minutes"
                required
                min={1}
                max={480}
                step={1}
                defaultValue={15}
              />
              <Select
                label="Pessoa responsável"
                name="resource"
                defaultValue={detail.item.resource_id}
              >
                {settings.data?.resources
                  .filter((r) => r.active && r.service_ids.includes(a.service_id))
                  .map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.name}
                    </option>
                  ))}
              </Select>
              {settings.isError && <Failure error={settings.error} />}
              <p>
                A nova ocupação precisa caber no expediente e estar livre para o pet e para a pessoa
                escolhida.
              </p>
            </>
          )}
        </fieldset>
        {mutation.isError && <Failure error={mutation.error} />}
        {attempt && !conflict && mutation.isError && (
          <Alert title="Confira o resultado antes de outra ação">
            Tente novamente para recuperar esta mesma operação. Ao sair, atualize o atendimento
            antes de repetir.
          </Alert>
        )}
        <div className="care-actions">
          <Button
            type="submit"
            busy={mutation.isPending}
            disabled={conflict || (['extend', 'transfer'].includes(action) && !settings.data)}
            variant={action === 'cancel_exception' ? 'danger' : 'primary'}
          >
            {attempt
              ? 'Tentar a mesma ação novamente'
              : action === 'note'
                ? 'Salvar anotação'
                : 'Confirmar ação'}
          </Button>
          <Button variant="secondary" disabled={mutation.isPending} onClick={close}>
            {attempt ? 'Atualizar e voltar ao atendimento' : 'Voltar sem salvar'}
          </Button>
        </div>
      </form>
    </section>
  );
}

export default function AttendancePage() {
  const { appointmentId = '' } = useParams();
  const [params] = useSearchParams();
  const back = params.get('voltar')?.startsWith('/operacao/agenda?')
    ? params.get('voltar')!
    : '/operacao/agenda';
  const cache = useQueryClient();
  const [selected, setSelected] = useState<{ action: string; detail: Attendance }>();
  const [saved, setSaved] = useState('');
  const detail = useQuery({
    queryKey: ['schedule', 'attendance', appointmentId],
    queryFn: ({ signal }) => operationsApi.detail(appointmentId, signal),
    refetchInterval: selected ? false : 30000,
  });
  const finish = () => {
    setSaved('Alteração registrada.');
    setSelected(undefined);
    void cache.invalidateQueries({ queryKey: ['schedule'] });
    void cache.invalidateQueries({ queryKey: ['management'] });
  };
  if (detail.isPending) return <Skeleton label="Carregando atendimento" />;
  if (detail.isError) return <Failure error={detail.error} retry={() => void detail.refetch()} />;
  const d = detail.data,
    a = d.item.appointment;
  return (
    <article className="operations-page">
      <Link to={back}>← Voltar à agenda</Link>
      <header className="operations-heading">
        <div>
          <span className="eyebrow">UM CUIDADO, PASSO A PASSO</span>
          <h1>Atendimento de {a.offer.pet_name}</h1>
          <p>
            {a.offer.service_name} · {dateTime(a.starts_at, a.timezone)}
          </p>
        </div>
        <Badge>{statusLabels[a.status]}</Badge>
      </header>
      {saved && <Alert tone="success" title={saved} />}
      {d.context.allergies && (
        <Alert tone="error" title="Atenção: alergias e restrições críticas">
          <p className="preserve-lines">{d.context.allergies}</p>
          <p>Informação do cadastro do pet. Confira antes de iniciar o cuidado.</p>
        </Alert>
      )}
      {d.item.overdue && (
        <Alert title="O tempo reservado terminou">
          O atendimento continua aberto. Confira a agenda e estenda a ocupação se houver
          disponibilidade; o sistema não altera outras reservas automaticamente.
        </Alert>
      )}
      {!selected && (
        <div className="care-actions">
          {d.item.allowed_actions.map((action, i) => (
            <Button
              key={action}
              variant={i === 0 ? 'primary' : 'secondary'}
              onClick={() => {
                setSaved('');
                setSelected({ action, detail: d });
              }}
            >
              {actionLabels[action]}
            </Button>
          ))}
          <Button
            variant="secondary"
            onClick={() => {
              setSaved('');
              setSelected({ action: 'note', detail: d });
            }}
          >
            Adicionar anotação
          </Button>
          <Button
            variant="secondary"
            busy={detail.isFetching}
            onClick={() => void detail.refetch()}
          >
            Atualizar atendimento
          </Button>
        </div>
      )}
      {selected && (
        <ActionForm
          key={selected.action + selected.detail.item.appointment.version}
          action={selected.action}
          detail={selected.detail}
          done={finish}
          close={() => {
            setSelected(undefined);
            void detail.refetch();
          }}
        />
      )}
      <div className="attendance-layout">
        <div className="care-stack">
          <section className="identity-card care-context">
            <h2>Informações para atender</h2>
            <p>
              <strong>Tutor:</strong> {d.context.customer_name}
            </p>
            <p>
              {d.context.phone || 'Telefone não informado'} · {d.context.email}
            </p>
            <p>
              {d.context.species === 'DOG' ? 'Cachorro' : 'Gato'} · {d.item.resource_name}
            </p>
            {d.context.care_notes ? (
              <Alert title="Cuidados informados pelo tutor">{d.context.care_notes}</Alert>
            ) : (
              <p>Sem observações de cuidado informadas.</p>
            )}
            {d.context.handling_notes && (
              <p className="preserve-lines">
                <strong>Comportamento e preferências:</strong> {d.context.handling_notes}
              </p>
            )}
            <Link to={'/operacao/clientes/' + a.customer_id}>
              Abrir cadastro e histórico do cliente
            </Link>
          </section>
          <section className="identity-card">
            <h2>Nos cuidados anteriores</h2>
            <p>
              Últimos três atendimentos concluídos deste pet; até cinco anotações recentes de cada
              cuidado, com visibilidade preservada.
            </p>
            {!d.previous_care.length ? (
              <p>Este pet ainda não tem um atendimento anterior concluído.</p>
            ) : (
              d.previous_care.map((p) => (
                <details className="previous-care" key={p.appointment_id}>
                  <summary>
                    {p.service_name} · {dateTime(p.completed_at, a.timezone)}
                  </summary>
                  <p>
                    {p.resource_name} ·{' '}
                    {p.actual_minutes === null
                      ? 'Tempo real não registrado'
                      : `${p.actual_minutes.toLocaleString('pt-BR')} min reais`}
                  </p>
                  {p.notes.map((n) => (
                    <div key={n.id}>
                      <Badge>
                        {n.visibility === 'INTERNAL' ? 'Nota interna' : 'Resumo público'}
                      </Badge>
                      <p className="preserve-lines">{n.body}</p>
                    </div>
                  ))}
                  <Link to={'/operacao/atendimentos/' + p.appointment_id}>
                    Abrir histórico completo
                  </Link>
                </details>
              ))
            )}
          </section>
          <section className="identity-card">
            <h2>Horários e condições</h2>
            <dl className="operation-facts">
              <dt>Previsão original</dt>
              <dd>
                {dateTime(a.starts_at, a.timezone)} até {dateTime(a.ends_at, a.timezone)}
              </dd>
              <dt>Serviço contratado</dt>
              <dd>
                {a.offer.duration_minutes} min · {money(a.offer.price)}
              </dd>
              <dt>Pessoa responsável</dt>
              <dd>{d.item.resource_name}</dd>
              {a.reserved_until && (
                <>
                  <dt>Ocupação estendida até</dt>
                  <dd>{dateTime(a.reserved_until, a.timezone)}</dd>
                </>
              )}
              {[
                ['Chegada', a.arrived_at],
                ['Início real', a.started_at],
                ['Conclusão real', a.completed_at],
              ].map(([label, value]) => (
                <Fragment key={label}>
                  <dt>{label}</dt>
                  <dd>{value ? dateTime(value, a.timezone) : 'Ainda não registrado'}</dd>
                </Fragment>
              ))}
            </dl>
            <p>
              Falta pode ser registrada após {a.no_show_grace_minutes} minuto(s) do horário
              previsto, se o pet ainda não chegou.
            </p>
            <Link to={'/operacao/reservas/' + a.id}>Ver reserva e opções de reagendamento</Link>
          </section>
          <section className="identity-card">
            <h2>Anotações do atendimento</h2>
            <p>
              Textos internos ficam disponíveis somente à equipe. Resumos publicados também aparecem
              no histórico do cliente.
            </p>
            {d.notes.length === 0 ? (
              <p>Nenhuma anotação registrada.</p>
            ) : (
              <ol className="operation-notes">
                {d.notes.map((n) => (
                  <li key={n.id}>
                    <Badge>
                      {n.visibility === 'INTERNAL'
                        ? 'Nota interna · equipe'
                        : 'Resumo publicado · cliente'}
                    </Badge>
                    <p className="preserve-lines">{n.body}</p>
                    <small>
                      {dateTime(n.occurred_at, a.timezone)} · Autor:{' '}
                      {d.authors[n.actor_id] || 'Equipe'}
                    </small>
                  </li>
                ))}
              </ol>
            )}
          </section>
        </div>
        <section className="identity-card operation-timeline">
          <h2>Linha do tempo</h2>
          <ol className="booking-history">
            {d.events.map((e) => (
              <li key={e.id}>
                <strong>{eventLabels[e.kind] || e.kind}</strong>
                <span>{dateTime(e.occurred_at, a.timezone)}</span>
                {e.reason && <p>{e.reason}</p>}
                {e.kind === 'extend' && <p>Ocupação até {dateTime(e.ends_at, a.timezone)}.</p>}
                {e.previous_resource_id && e.resource_id && (
                  <p>
                    {d.resources[e.previous_resource_id] || 'Responsável anterior'} →{' '}
                    {d.resources[e.resource_id] || 'Novo responsável'}
                  </p>
                )}
                <small>Autor: {d.authors[e.actor_id] || 'Equipe'}</small>
              </li>
            ))}
          </ol>
          <CommunicationHistory messages={d.communications} timezone={a.timezone} />
        </section>
      </div>
    </article>
  );
}
