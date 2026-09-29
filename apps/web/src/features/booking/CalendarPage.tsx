import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import {
  bookingApi,
  type Calendar,
  type Config,
  type Resource,
  type ResourceInput,
  type Settings,
} from './api';
import { CalendarEditor } from './CalendarEditor';
import { Failure, Pages } from './Feedback';
import { Input } from '../../shared/ui/Input';
import { Select } from '../../shared/ui/Select';
import { Button } from '../../shared/ui/Button';
import { Alert, Badge, Skeleton } from '../../shared/ui/Feedback';

function ConfigurationForm({ initial, done }: { initial: Config; done: () => void }) {
  const form = useForm<Config>({ defaultValues: initial });
  const [calendar, setCalendar] = useState(initial.calendar);
  const [impact, setImpact] = useState<string[]>();
  const [checkedBody, setCheckedBody] = useState<Config>();
  const preview = useMutation({
    mutationFn: bookingApi.preview,
    onSuccess: (value, body) => {
      setImpact(value.appointment_ids);
      setCheckedBody(body);
    },
  });
  const save = useMutation({ mutationFn: bookingApi.configure, onSuccess: done });
  const resetPreview = () => {
    setImpact(undefined);
    setCheckedBody(undefined);
    preview.reset();
    save.reset();
  };
  return (
    <section className="identity-card">
      <h2>Regras e expediente da loja</h2>
      {!initial.enabled && (
        <Alert title="Agenda fechada para novas reservas">
          Preencha e confira as regras antes de abrir os agendamentos. Nenhum horário de atendimento
          foi preenchido automaticamente.
        </Alert>
      )}
      <form
        onChange={resetPreview}
        onSubmit={form.handleSubmit((data) => preview.mutate({ ...data, calendar }))}
      >
        <fieldset className="form-lock" disabled={preview.isPending || save.isPending}>
          <Input
            label="Fuso horário da loja"
            required
            hint="Nome IANA, por exemplo: America/Sao_Paulo."
            {...form.register('timezone', { required: true })}
          />
          <div className="care-form-grid">
            <Input
              label="Antecedência mínima para reservar (minutos)"
              type="number"
              min={0}
              max={525600}
              required
              {...form.register('lead_minutes', { valueAsNumber: true, required: true })}
            />
            <Input
              label="Até quantos dias no futuro aceitar reservas"
              type="number"
              min={1}
              max={366}
              required
              {...form.register('horizon_days', { valueAsNumber: true, required: true })}
            />
            <Input
              label="Intervalo entre opções de horário (minutos)"
              type="number"
              min={1}
              max={120}
              required
              hint="A duração do serviço é definida no catálogo."
              {...form.register('step_minutes', { valueAsNumber: true, required: true })}
            />
            <Input
              label="Prazo para o cliente alterar (minutos antes)"
              type="number"
              min={0}
              max={525600}
              required
              hint="Zero permite alterar até o início. A equipe pode ajudar fora desse prazo."
              {...form.register('change_cutoff_minutes', { valueAsNumber: true, required: true })}
            />
          </div>
          <CalendarEditor
            value={calendar}
            change={(next) => {
              setCalendar(next);
              resetPreview();
            }}
          />
          <label className="care-check">
            <input type="checkbox" {...form.register('enabled')} />
            Abrir a agenda para novas reservas
          </label>
          {preview.isError && <Failure error={preview.error} />}
          {save.isError && <Failure error={save.error} />}
          {impact && (
            <Alert
              tone={impact.length ? 'error' : 'success'}
              title={
                impact.length
                  ? impact.length + ' reserva(s) seriam afetadas'
                  : 'Nenhuma reserva afetada'
              }
            >
              {impact.length
                ? 'A mudança será bloqueada. Ajuste as reservas abaixo antes de salvar.'
                : 'Você pode salvar. As reservas serão conferidas novamente na confirmação.'}
            </Alert>
          )}
          {!!impact?.length && (
            <ul>
              {impact.map((id) => (
                <li key={id}>
                  <Link to={'/operacao/reservas/' + id}>Revisar reserva {id.slice(0, 8)}</Link>
                </li>
              ))}
            </ul>
          )}
          <div className="care-actions">
            <Button type="submit" busy={preview.isPending}>
              Conferir impacto
            </Button>
            <Button
              disabled={!checkedBody || !impact || impact.length > 0 || preview.isPending}
              busy={save.isPending}
              onClick={() => checkedBody && save.mutate(checkedBody)}
            >
              Salvar agenda
            </Button>
          </div>
        </fieldset>
      </form>
    </section>
  );
}

function ResourceForm({
  initial,
  settings,
  done,
  cancel,
}: {
  initial?: Resource;
  settings: Settings;
  done: () => void;
  cancel: () => void;
}) {
  const form = useForm<ResourceInput>({
    defaultValues: initial || { user_id: '', name: '', active: true, service_ids: [], version: 1 },
  });
  const [calendar, setCalendar] = useState<Calendar | null>(initial?.calendar || null);
  const [selectedServices, setSelectedServices] = useState(initial?.service_ids || []);
  const [offset, setOffset] = useState(0);
  const services = useQuery({
    queryKey: ['schedule', 'staffServices', offset],
    queryFn: ({ signal }) => bookingApi.staffServices(offset, signal),
  });
  const save = useMutation({
    mutationFn: (data: ResourceInput) =>
      bookingApi.resource({ ...data, calendar, service_ids: selectedServices }, initial?.id),
    onSuccess: done,
  });
  const workers = settings.workers;
  return (
    <section className="identity-card">
      <h2>{initial ? 'Editar disponibilidade da pessoa' : 'Adicionar pessoa à agenda'}</h2>
      <p>
        Cada pessoa atende um pet por vez. Marque os serviços que ela pode realizar. Uma pessoa só
        pode aparecer uma vez na capacidade.
      </p>
      <form onSubmit={form.handleSubmit((data) => save.mutate(data))}>
        <Select
          label="Pessoa da equipe"
          required
          {...form.register('user_id', { required: true })}
          disabled={!!initial}
        >
          <option value="">Selecione uma pessoa</option>
          {workers.map((w) => (
            <option value={w.id} key={w.id}>
              {w.name}
            </option>
          ))}
          {initial && !workers.some((w) => w.id === initial.user_id) && (
            <option value={initial.user_id}>{initial.name} (conta inativa)</option>
          )}
        </Select>
        {!workers.length && (
          <Alert title="Nenhuma conta de equipe disponível">
            Um administrador precisa convidar a pessoa em “Pessoas e acessos”. Depois que o convite
            for aceito, ela poderá ser adicionada à agenda.
          </Alert>
        )}
        <Input
          label="Nome na agenda da equipe"
          required
          maxLength={100}
          {...form.register('name', { required: true })}
        />
        <fieldset className="care-fieldset">
          <legend>Serviços atendidos</legend>
          {services.isPending ? (
            <Skeleton label="Carregando serviços" />
          ) : services.isError ? (
            <Failure error={services.error} retry={() => void services.refetch()} />
          ) : (
            <>
              {!services.data.items.length && (
                <p>Cadastre serviços antes de disponibilizar esta pessoa.</p>
              )}
              {services.data.items.map((service) => (
                <label className="care-check" key={service.id}>
                  <input
                    type="checkbox"
                    checked={selectedServices.includes(service.id)}
                    onChange={(e) =>
                      setSelectedServices(
                        e.target.checked
                          ? [...selectedServices, service.id]
                          : selectedServices.filter((id) => id !== service.id),
                      )
                    }
                  />
                  {service.name}
                  {!service.active && ' (inativo)'}
                </label>
              ))}
              <Pages offset={offset} total={services.data.total} change={setOffset} size={100} />
            </>
          )}
        </fieldset>
        <label className="care-check">
          <input
            type="checkbox"
            checked={calendar === null}
            onChange={(e) => setCalendar(e.target.checked ? null : { weekly: [], exceptions: [] })}
          />
          Seguir o expediente da loja
        </label>
        {calendar !== null && (
          <>
            <p>Os períodos desta pessoa serão limitados também pelo expediente da loja.</p>
            <CalendarEditor value={calendar} change={setCalendar} />
          </>
        )}
        <label className="care-check">
          <input type="checkbox" {...form.register('active')} />
          Disponível para novos agendamentos
        </label>
        {save.isError && <Failure error={save.error} />}
        <div className="care-actions">
          <Button type="submit" busy={save.isPending}>
            Salvar pessoa na agenda
          </Button>
          <Button variant="secondary" onClick={cancel} disabled={save.isPending}>
            Voltar
          </Button>
        </div>
      </form>
    </section>
  );
}

export default function CalendarPage() {
  const cache = useQueryClient();
  const settings = useQuery({
    queryKey: ['schedule', 'settings'],
    queryFn: ({ signal }) => bookingApi.settings(signal),
  });
  const [resource, setResource] = useState<Resource | 'new'>();
  const [editing, setEditing] = useState(false);
  const [baseline, setBaseline] = useState<Config>();
  const [saved, setSaved] = useState(false);
  const done = () => {
    setResource(undefined);
    setEditing(false);
    setSaved(true);
    void cache.invalidateQueries({ queryKey: ['schedule'] });
  };
  if (settings.isPending) return <Skeleton label="Carregando agenda" />;
  if (settings.isError)
    return <Failure error={settings.error} retry={() => void settings.refetch()} />;
  const data = settings.data;
  return (
    <section className="calendar-page">
      <span className="eyebrow">CAPACIDADE DE ATENDIMENTO</span>
      <h1>Equipe e horários</h1>
      <p>Defina quem atende, quais serviços realiza e quando a loja pode receber cada pet.</p>
      {saved && (
        <Alert tone="success" title="Agenda atualizada">
          As próximas consultas de horário usarão essa configuração.
        </Alert>
      )}
      {resource ? (
        <ResourceForm
          initial={resource === 'new' ? undefined : resource}
          settings={data}
          done={done}
          cancel={() => setResource(undefined)}
        />
      ) : editing && baseline ? (
        <>
          <ConfigurationForm initial={baseline} done={done} />
          <Button variant="secondary" onClick={() => setEditing(false)}>
            Voltar sem salvar
          </Button>
        </>
      ) : (
        <>
          <section className="identity-card">
            <Badge>{data.configuration.enabled ? 'Agenda aberta' : 'Agenda fechada'}</Badge>
            <h2>Expediente da loja</h2>
            <p>Fuso: {data.configuration.timezone}</p>
            <p>
              Antecedência: {data.configuration.lead_minutes} min · Horizonte:{' '}
              {data.configuration.horizon_days} dias · Intervalo entre opções:{' '}
              {data.configuration.step_minutes} min
            </p>
            <Button
              onClick={() => {
                setBaseline(data.configuration);
                setEditing(true);
                setSaved(false);
              }}
            >
              Configurar expediente e regras
            </Button>
          </section>
          <div className="care-toolbar">
            <h2>Pessoas na agenda</h2>
            <Button
              onClick={() => {
                setResource('new');
                setSaved(false);
              }}
            >
              Adicionar pessoa
            </Button>
          </div>
          <p>
            Convites e permissões de acesso são administrados em “Pessoas e acessos”. Aqui, a equipe
            organiza a capacidade de atendimento.
          </p>
          {!data.resources.length && (
            <Alert title="Adicione a equipe para liberar vagas">
              Cadastre cada pessoa e os serviços que ela realiza.
            </Alert>
          )}
          <div className="care-grid">
            {data.resources.map((r) => (
              <article className="identity-card" key={r.id}>
                <Badge>
                  {!data.workers.some((w) => w.id === r.user_id)
                    ? 'Conta indisponível'
                    : r.active
                      ? 'Disponível'
                      : 'Indisponível'}
                </Badge>
                <h3>{r.name}</h3>
                <p>
                  {r.service_ids.length} serviço(s) ·{' '}
                  {r.calendar ? 'Expediente próprio' : 'Segue o expediente da loja'}
                </p>
                <Button
                  variant="secondary"
                  onClick={() => {
                    setResource(r);
                    setSaved(false);
                  }}
                >
                  Editar {r.name}
                </Button>
              </article>
            ))}
          </div>
          <Button
            variant="secondary"
            busy={settings.isFetching}
            onClick={() => void settings.refetch()}
          >
            Atualizar configuração
          </Button>
        </>
      )}
    </section>
  );
}
