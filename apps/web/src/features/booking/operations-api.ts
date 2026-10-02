import type { components } from '@petland/api-contract';
import { client, result } from '../../shared/lib/api';
type S = components['schemas'];
export type Attendance = S['OperationDetailResponse'];
export type Transition = S['AttendanceInput'];
export type Status = S['AppointmentResponse']['status'];
export const statusLabels: Record<Status, string> = {
  BOOKED: 'Confirmada',
  ARRIVED: 'Chegou',
  IN_PROGRESS: 'Em atendimento',
  COMPLETED: 'Concluída',
  CANCELLED: 'Cancelada',
  NO_SHOW: 'Não compareceu',
};
export const actionLabels: Record<string, string> = {
  arrive: 'Registrar chegada',
  start: 'Iniciar atendimento',
  complete: 'Concluir atendimento',
  no_show: 'Registrar falta',
  cancel_exception: 'Cancelar por exceção',
  extend: 'Estender atendimento',
  transfer: 'Transferir responsável',
  note: 'Salvar anotação',
};
export const eventLabels: Record<string, string> = {
  book: 'Reserva confirmada',
  reschedule: 'Reserva reagendada',
  cancel: 'Reserva cancelada',
  arrive: 'Chegada registrada',
  start: 'Atendimento iniciado',
  complete: 'Atendimento concluído',
  no_show: 'Falta registrada',
  cancel_exception: 'Cancelamento excepcional',
  extend: 'Tempo reservado ampliado',
  transfer: 'Responsável transferido',
  note_internal: 'Nota interna adicionada',
  note_public: 'Resumo publicado para o cliente',
};
export const addDays = (day: string, count: number) => {
  const date = new Date(day + 'T12:00:00Z');
  if (Number.isNaN(date.getTime())) return day;
  date.setUTCDate(date.getUTCDate() + count);
  return date.toISOString().slice(0, 10);
};
export const localDay = (timezone: string) =>
  new Intl.DateTimeFormat('en-CA', { timeZone: timezone }).format(new Date());
export const operationsApi = {
  async agenda(
    query: {
      date_from?: string;
      date_to?: string;
      status?: Status;
      search?: string;
      resource_id?: string;
      offset?: number;
      mine?: boolean;
    },
    signal?: AbortSignal,
  ) {
    return result(
      await client.GET('/api/v1/operations/agenda', {
        params: { query: { ...query, limit: 20 } },
        signal,
      }),
    );
  },
  async detail(id: string, signal?: AbortSignal) {
    return result(
      await client.GET('/api/v1/operations/attendances/{appointment_id}', {
        params: { path: { appointment_id: id } },
        signal,
      }),
    );
  },
  async dashboard(date?: string, mine = true, signal?: AbortSignal) {
    return result(
      await client.GET('/api/v1/operations/dashboard', {
        params: { query: { date, mine } },
        signal,
      }),
    );
  },
  async roster(day: string, signal?: AbortSignal) {
    return result(
      await client.GET('/api/v1/operations/roster/{day}', { params: { path: { day } }, signal }),
    );
  },
  async previewRoster(day: string, body: S['RosterInput']) {
    return result(
      await client.POST('/api/v1/operations/roster/{day}/impact-preview', {
        params: { path: { day } },
        body,
      }),
    );
  },
  async saveRoster(day: string, body: S['RosterInput']) {
    return result(
      await client.PUT('/api/v1/operations/roster/{day}', { params: { path: { day } }, body }),
    );
  },
  async pools(signal?: AbortSignal) {
    return result(await client.GET('/api/v1/operations/capacity', { signal }));
  },
  async previewPools(body: S['PoolsInput']) {
    return result(await client.POST('/api/v1/operations/capacity/impact-preview', { body }));
  },
  async savePools(body: S['PoolsInput']) {
    return result(await client.PUT('/api/v1/operations/capacity', { body }));
  },
  async transfer(id: string, body: S['TransferInput'], key: string) {
    return result(
      await client.POST('/api/v1/operations/attendances/{appointment_id}/transfer', {
        params: { path: { appointment_id: id }, header: { 'Idempotency-Key': key } },
        body,
      }),
    );
  },
  async transition(id: string, body: Transition, key: string) {
    return result(
      await client.POST('/api/v1/operations/attendances/{appointment_id}/transitions', {
        params: { path: { appointment_id: id }, header: { 'Idempotency-Key': key } },
        body,
      }),
    );
  },
  async note(id: string, body: S['NoteInput'], key: string) {
    return result(
      await client.POST('/api/v1/operations/attendances/{appointment_id}/notes', {
        params: { path: { appointment_id: id }, header: { 'Idempotency-Key': key } },
        body,
      }),
    );
  },
  async extend(id: string, body: S['ExtensionInput'], key: string) {
    return result(
      await client.POST('/api/v1/operations/attendances/{appointment_id}/extensions', {
        params: { path: { appointment_id: id }, header: { 'Idempotency-Key': key } },
        body,
      }),
    );
  },
  async metrics(date_from: string, date_to: string, signal?: AbortSignal) {
    return result(
      await client.GET('/api/v1/management/metrics', {
        params: { query: { date_from, date_to } },
        signal,
      }),
    );
  },
  async audit(
    query: {
      start: string;
      end: string;
      action?: string;
      actor_id?: string;
      target_id?: string;
      offset: number;
    },
    signal?: AbortSignal,
  ) {
    return result(
      await client.GET('/api/v1/management/audit', {
        params: { query: { ...query, limit: 20 } },
        signal,
      }),
    );
  },
  async establishment(signal?: AbortSignal) {
    return result(await client.GET('/api/v1/establishment', { signal }));
  },
};
