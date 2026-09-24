import { createApiClient } from '@petland/api-contract';
const client = createApiClient();

export class ApiError extends Error {
  constructor(
    public status: number,
    public requestId: string | null,
  ) {
    super('Não foi possível verificar a conexão agora.');
  }
}

export async function getReadiness(signal?: AbortSignal) {
  const timeout = AbortSignal.timeout(6000);
  const { data, response } = await client.GET('/api/v1/health/ready', {
    signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
  });
  if (!response.ok || !data)
    throw new ApiError(response.status, response.headers.get('X-Request-ID'));
  return data;
}
