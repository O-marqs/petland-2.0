import type { components } from '@petland/api-contract';
import { client, result } from '../../shared/lib/api';
type S = components['schemas'];
export type Customer = S['CustomerResponse'];
export type CustomerInput = S['CustomerInput'];
export type Pet = S['PetResponse'];
export type PetInput = S['PetInput'];
export type Service = S['ServiceResponse'];
export type ServiceInput = S['ServiceInput'];
export type Size = S['Size'];
export const sizeLabels: Record<Size, string> = {
  SMALL: 'Pequeno',
  MEDIUM: 'Médio',
  LARGE: 'Grande',
};
export const sizes = Object.keys(sizeLabels) as Size[];
export const money = (amount: string | number) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(amount));

export const careApi = {
  async profile(signal?: AbortSignal) {
    return result(await client.GET('/api/v1/me/customer', { signal }));
  },
  async customers(q: string, offset: number, signal?: AbortSignal) {
    return result(
      await client.GET('/api/v1/operations/customers', {
        params: { query: { q, offset, limit: 20 } },
        signal,
      }),
    );
  },
  async customer(id: string, signal?: AbortSignal) {
    return result(
      await client.GET('/api/v1/operations/customers/{customer_id}', {
        params: { path: { customer_id: id } },
        signal,
      }),
    );
  },
  async saveCustomer(body: CustomerInput, staff: boolean, existing?: Customer | null) {
    if (staff)
      return existing
        ? result(
            await client.PUT('/api/v1/operations/customers/{customer_id}', {
              params: { path: { customer_id: existing.id } },
              body: { ...body, version: existing.version },
            }),
          )
        : result(await client.POST('/api/v1/operations/customers', { body }));
    return existing
      ? result(
          await client.PUT('/api/v1/me/customer', { body: { ...body, version: existing.version } }),
        )
      : result(await client.POST('/api/v1/me/customer', { body }));
  },
  async invite(id: string) {
    return result(
      await client.POST('/api/v1/operations/customers/{customer_id}/claim-invitations', {
        params: { path: { customer_id: id } },
      }),
    );
  },
  async claim(token: string) {
    return result(await client.POST('/api/v1/me/customer-claims', { body: { token } }));
  },
  async species(signal?: AbortSignal) {
    return result(await client.GET('/api/v1/catalog/species', { signal }));
  },
  async breeds(species_id: string, signal?: AbortSignal) {
    return result(
      await client.GET('/api/v1/catalog/breeds', { params: { query: { species_id } }, signal }),
    );
  },
  async pets(
    customerId: string | undefined,
    archived: boolean,
    offset: number,
    signal?: AbortSignal,
  ) {
    return customerId
      ? result(
          await client.GET('/api/v1/operations/customers/{customer_id}/pets', {
            params: { path: { customer_id: customerId }, query: { archived, offset, limit: 20 } },
            signal,
          }),
        )
      : result(
          await client.GET('/api/v1/me/pets', {
            params: { query: { archived, offset, limit: 20 } },
            signal,
          }),
        );
  },
  async savePet(body: PetInput, customerId?: string, existing?: Pet) {
    if (customerId)
      return existing
        ? result(
            await client.PUT('/api/v1/operations/customers/{customer_id}/pets/{pet_id}', {
              params: { path: { customer_id: customerId, pet_id: existing.id } },
              body: { ...body, version: existing.version },
            }),
          )
        : result(
            await client.POST('/api/v1/operations/customers/{customer_id}/pets', {
              params: { path: { customer_id: customerId } },
              body,
            }),
          );
    return existing
      ? result(
          await client.PUT('/api/v1/me/pets/{pet_id}', {
            params: { path: { pet_id: existing.id } },
            body: { ...body, version: existing.version },
          }),
        )
      : result(await client.POST('/api/v1/me/pets', { body }));
  },
  async archive(pet: Pet, archived: boolean, customerId?: string) {
    const body = { version: pet.version, archived };
    return customerId
      ? result(
          await client.PATCH('/api/v1/operations/customers/{customer_id}/pets/{pet_id}/archive', {
            params: { path: { customer_id: customerId, pet_id: pet.id } },
            body,
          }),
        )
      : result(
          await client.PATCH('/api/v1/me/pets/{pet_id}/archive', {
            params: { path: { pet_id: pet.id } },
            body,
          }),
        );
  },
  async services(
    staff: boolean,
    offset: number,
    species_id?: string,
    size?: Size,
    signal?: AbortSignal,
  ) {
    return staff
      ? result(
          await client.GET('/api/v1/operations/services', {
            params: { query: { offset, limit: 20 } },
            signal,
          }),
        )
      : result(
          await client.GET('/api/v1/catalog/services', {
            params: { query: { offset, limit: 20, species_id, size } },
            signal,
          }),
        );
  },
  async service(id: string, signal?: AbortSignal) {
    return result(
      await client.GET('/api/v1/catalog/services/{service_id}', {
        params: { path: { service_id: id } },
        signal,
      }),
    );
  },
  async saveService(body: ServiceInput, existing?: Service) {
    return existing
      ? result(
          await client.PUT('/api/v1/operations/services/{service_id}', {
            params: { path: { service_id: existing.id } },
            body: { ...body, version: existing.version },
          }),
        )
      : result(await client.POST('/api/v1/operations/services', { body }));
  },
};
