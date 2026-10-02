import createClient from 'openapi-fetch';
import type { paths } from './schema.js';

export type { paths } from './schema.js';
export type { components } from './schema.js';

export function createApiClient(options: { baseUrl?: string; fetch?: typeof fetch } = {}) {
  const transport = options.fetch ?? fetch;
  const client = createClient<paths>({
    baseUrl: options.baseUrl ?? '',
    credentials: 'include',
    fetch: (request) =>
      transport(
        new Request(request, {
          signal: AbortSignal.any([request.signal, AbortSignal.timeout(15000)]),
        }),
      ),
  });
  client.use({
    async onRequest({ request }) {
      if (!['GET', 'HEAD', 'OPTIONS'].includes(request.method)) {
        const response = await transport(`${options.baseUrl ?? ''}/api/v1/auth/csrf`, {
          credentials: 'include',
          signal: AbortSignal.any([request.signal, AbortSignal.timeout(15000)]),
        });
        if (!response.ok)
          throw new Error('Não foi possível preparar uma conexão segura. Tente novamente.');
        const csrf: unknown = await response.json();
        if (
          !csrf ||
          typeof csrf !== 'object' ||
          !('csrf_token' in csrf) ||
          typeof csrf.csrf_token !== 'string'
        )
          throw new Error('Resposta de segurança inválida.');
        request.headers.set('X-CSRF-Token', csrf.csrf_token);
      }
      return request;
    },
  });
  return client;
}
