import createClient from 'openapi-fetch';
import type { paths } from './schema.js';

export type { paths } from './schema.js';

export function createApiClient(options: { baseUrl?: string; fetch?: typeof fetch } = {}) {
  return createClient<paths>({
    baseUrl: options.baseUrl ?? '',
    credentials: 'include',
    fetch: options.fetch,
  });
}
