import { type PropsWithChildren } from 'react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ManagementPage from './ManagementPage';
import { operationsApi } from './operations-api';

vi.mock('./operations-api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('./operations-api')>()),
  operationsApi: { establishment: vi.fn(), audit: vi.fn(), metrics: vi.fn() },
}));

function wrapper({ children }: PropsWithChildren) {
  return (
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

beforeEach(() => {
  vi.resetAllMocks();
  // 22:30 in São Paulo, already the next calendar day in UTC.
  vi.useFakeTimers({ toFake: ['Date'] });
  vi.setSystemTime(new Date('2026-10-02T01:30:00Z'));
  vi.mocked(operationsApi.establishment).mockResolvedValue({
    timezone: 'America/Sao_Paulo',
    shop_name: 'PetLand sintético',
    shop_address: '',
    shop_email: '',
    shop_phone: '',
  });
});

afterEach(() => vi.useRealTimers());

it('includes a recent action when the UTC audit date is ahead of the shop date', async () => {
  const occurredAt = '2026-10-02T01:15:00Z';
  vi.mocked(operationsApi.audit).mockImplementation(async ({ start, end }) => {
    const included = start <= occurredAt && occurredAt < end;
    return {
      total: included ? 1 : 0,
      items: included
        ? [
            {
              id: '11111111-1111-4111-8111-111111111111',
              action: 'appointment.complete',
              occurred_at: occurredAt,
              actor_user_id: null,
              target_id: null,
              result: 'success',
            },
          ]
        : [],
    };
  });
  render(<ManagementPage audit />, { wrapper });
  expect(screen.getByLabelText('Fim do período (obrigatório)')).toHaveValue('2026-10-02');
  expect(await screen.findByText('appointment.complete', { exact: true })).toBeVisible();
  expect(operationsApi.metrics).not.toHaveBeenCalled();
});

it('keeps business metrics on the shop date at the same instant', async () => {
  vi.mocked(operationsApi.metrics).mockResolvedValue({
    date_from: '2026-09-02',
    date_to: '2026-10-01',
    timezone: 'America/Sao_Paulo',
    total: 0,
    by_status: { COMPLETED: 0, CANCELLED: 0, NO_SHOW: 0 },
    by_service: {},
    occupied_minutes: 0,
    available_minutes: 0,
    occupancy_percent: null,
    calculated_at: '2026-10-02T01:30:00Z',
    staff: [],
    services: [],
    completed_pets: 0,
    completed_customers: 0,
  });
  render(<ManagementPage />, { wrapper });
  expect(screen.getByLabelText('Fim do período (obrigatório)')).toHaveValue('2026-10-01');
  await waitFor(() =>
    expect(operationsApi.metrics).toHaveBeenCalledWith(
      '2026-09-02',
      '2026-10-01',
      expect.any(AbortSignal),
    ),
  );
  expect(await screen.findByRole('heading', { name: 'Ocupação da agenda' })).toBeVisible();
  expect(operationsApi.audit).not.toHaveBeenCalled();
});
