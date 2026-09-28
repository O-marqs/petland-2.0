import { createApiClient } from '@petland/api-contract';
export const client = createApiClient();

export class ApiError extends Error {
  constructor(
    public status: number,
    public requestId: string | null,
    message = 'Não foi possível verificar a conexão agora.',
    public code = '',
  ) {
    super(message);
  }
}

export function result<T>({
  data,
  error,
  response,
}: {
  data?: T;
  error?: unknown;
  response: Response;
}): T {
  if (!response.ok) {
    const problem = error && typeof error === 'object' ? (error as Record<string, unknown>) : {};
    throw new ApiError(
      response.status,
      response.headers.get('X-Request-ID'),
      typeof problem.detail === 'string'
        ? problem.detail
        : 'Não foi possível concluir. Tente novamente.',
      typeof problem.code === 'string' ? problem.code : '',
    );
  }
  return data as T;
}

export function errorMessage(error: unknown): string {
  return error instanceof ApiError
    ? error.message
    : 'Não foi possível conectar agora. Confira sua conexão e tente novamente.';
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
