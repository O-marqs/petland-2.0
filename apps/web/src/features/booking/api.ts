import type { components } from '@petland/api-contract';
import { client, result } from '../../shared/lib/api';
type S = components['schemas'];
export type Appointment = S['AppointmentResponse'];
export type Availability = S['AvailabilityResponse'];
export type Config = S['ConfigurationInput'];
export type Calendar = S['CalendarInput'];
export type Resource = S['ResourceResponse'];
export type ResourceInput = S['ResourceInput'];
export type Settings = S['SettingsResponse'];
export type Booking = S['BookingInput'];
export type Pet = S['PetResponse'];
export const money = (value: string | number) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(value));
export const dateTime = (value: string, timezone: string) =>
  new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'medium',
    timeStyle: 'short',
    timeZone: timezone,
  }).format(new Date(value));
export const timeOnly = (value: string, timezone: string) =>
  new Intl.DateTimeFormat('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
    timeZone: timezone,
  }).format(new Date(value));
export const bookingApi = {
  async settings(signal?: AbortSignal) {
    return result(await client.GET('/api/v1/operations/calendar', { signal }));
  },
  async configure(body: Config) {
    return result(await client.PUT('/api/v1/operations/calendar', { body }));
  },
  async preview(body: Config) {
    return result(await client.POST('/api/v1/operations/calendar/impact-preview', { body }));
  },
  async resource(body: ResourceInput, id?: string) {
    return id
      ? result(
          await client.PUT('/api/v1/operations/resources/{resource_id}', {
            params: { path: { resource_id: id } },
            body,
          }),
        )
      : result(await client.POST('/api/v1/operations/resources', { body }));
  },
  async pets(customerId?: string, offset = 0, signal?: AbortSignal) {
    return customerId
      ? result(
          await client.GET('/api/v1/operations/customers/{customer_id}/pets', {
            params: { path: { customer_id: customerId }, query: { limit: 20, offset } },
            signal,
          }),
        )
      : result(
          await client.GET('/api/v1/me/pets', { params: { query: { limit: 20, offset } }, signal }),
        );
  },
  async services(species_id?: string, size?: Pet['size'], offset = 0, signal?: AbortSignal) {
    return result(
      await client.GET('/api/v1/catalog/services', {
        params: { query: { species_id, size, offset, limit: 20 } },
        signal,
      }),
    );
  },
  async staffServices(offset = 0, signal?: AbortSignal) {
    return result(
      await client.GET('/api/v1/operations/services', {
        params: { query: { offset, limit: 100 } },
        signal,
      }),
    );
  },
  async availability(
    pet_id: string,
    service_id: string,
    date: string,
    customerId?: string,
    appointment_id?: string,
    signal?: AbortSignal,
  ) {
    const query = { pet_id, service_id, date, appointment_id };
    return customerId
      ? result(
          await client.GET('/api/v1/operations/availability', {
            params: { query: { ...query, customer_id: customerId } },
            signal,
          }),
        )
      : result(await client.GET('/api/v1/me/availability', { params: { query }, signal }));
  },
  async book(body: Booking, key: string, customerId?: string) {
    const params = { header: { 'Idempotency-Key': key } };
    return customerId
      ? result(
          await client.POST('/api/v1/operations/appointments', {
            params,
            body: { ...body, customer_id: customerId },
          }),
        )
      : result(await client.POST('/api/v1/me/appointments', { params, body }));
  },
  async list(
    staff: boolean,
    offset: number,
    signal?: AbortSignal,
    filters: {
      customer_id?: string;
      pet_id?: string;
      status?: Appointment['status'];
      period?: 'all' | 'upcoming' | 'history';
    } = {},
  ) {
    const params = { query: { offset, limit: 20, ...filters } };
    return staff
      ? result(await client.GET('/api/v1/operations/appointments', { params, signal }))
      : result(await client.GET('/api/v1/me/appointments', { params, signal }));
  },
  async detail(staff: boolean, id: string, signal?: AbortSignal) {
    const params = { path: { appointment_id: id } };
    return staff
      ? result(
          await client.GET('/api/v1/operations/appointments/{appointment_id}', { params, signal }),
        )
      : result(await client.GET('/api/v1/me/appointments/{appointment_id}', { params, signal }));
  },
  async cancel(staff: boolean, id: string, body: S['ChangeInput'], key: string) {
    const params = { path: { appointment_id: id }, header: { 'Idempotency-Key': key } };
    return staff
      ? result(
          await client.POST('/api/v1/operations/appointments/{appointment_id}/cancel', {
            params,
            body,
          }),
        )
      : result(
          await client.POST('/api/v1/me/appointments/{appointment_id}/cancel', { params, body }),
        );
  },
  async reschedule(staff: boolean, id: string, body: S['RescheduleInput'], key: string) {
    const params = { path: { appointment_id: id }, header: { 'Idempotency-Key': key } };
    return staff
      ? result(
          await client.POST('/api/v1/operations/appointments/{appointment_id}/reschedule', {
            params,
            body,
          }),
        )
      : result(
          await client.POST('/api/v1/me/appointments/{appointment_id}/reschedule', {
            params,
            body,
          }),
        );
  },
};
