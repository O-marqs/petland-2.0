import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, test, vi } from 'vitest';
import { ConnectionStatus } from './ConnectionStatus';
import { getReadiness, ApiError } from '../../shared/lib/api';

vi.mock('../../shared/lib/api', async (original) => ({
  ...(await original<typeof import('../../shared/lib/api')>()),
  getReadiness: vi.fn(),
}));

function renderStatus() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <ConnectionStatus />
    </QueryClientProvider>,
  );
}

test('shows unavailability then verifies a successful retry', async () => {
  vi.mocked(getReadiness)
    .mockRejectedValueOnce(new ApiError(503, 'reference-123'))
    .mockResolvedValueOnce({ status: 'ready' });
  renderStatus();
  expect(await screen.findByText('Conexão indisponível no momento')).toBeVisible();
  expect(screen.queryByText('Ambiente conectado')).not.toBeInTheDocument();
  await userEvent.click(screen.getByRole('button', { name: 'Tentar novamente' }));
  expect(await screen.findByText('Ambiente conectado')).toBeVisible();
});

test('never presents loading as a successful connection', () => {
  vi.mocked(getReadiness).mockReturnValue(new Promise(() => {}));
  renderStatus();
  expect(screen.getByText('Verificando conexão…')).toBeVisible();
  expect(screen.queryByText('Ambiente conectado')).not.toBeInTheDocument();
});
