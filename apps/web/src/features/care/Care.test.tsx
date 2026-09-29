import { StrictMode, type PropsWithChildren } from 'react';
import { beforeEach, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ClaimPage from './ClaimPage';
import { CustomerForm } from './CustomersPage';
import { careApi, type Customer } from './api';
import { ApiError } from '../../shared/lib/api';

vi.mock('./api', () => ({ careApi: { claim: vi.fn(), saveCustomer: vi.fn() } }));
vi.mock('../identity/account', () => ({
  useAccount: () => ({
    isPending: false,
    data: { email: 'sintetico@example.com', email_verified: true },
  }),
}));
vi.mock('react-router-dom', async (importOriginal) => ({
  ...(await importOriginal<typeof import('react-router-dom')>()),
  useOutletContext: () => ({ email: 'sintetico@example.com', display_name: 'Pessoa Sintética' }),
}));
const customer: Customer = {
  id: '11111111-1111-4111-8111-111111111111',
  name: 'Pessoa Sintética',
  email: 'sintetico@example.com',
  phone: '',
  address: '',
  version: 1,
  linked: true,
};

function wrapper({ children }: PropsWithChildren) {
  return (
    <StrictMode>
      <QueryClientProvider
        client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
      >
        <MemoryRouter>{children}</MemoryRouter>
      </QueryClientProvider>
    </StrictMode>
  );
}
beforeEach(() => {
  vi.resetAllMocks();
  window.history.replaceState(null, '', '/');
});

it('keeps the email claim in memory through StrictMode and removes the URL fragment', async () => {
  window.history.replaceState(null, '', '/vincular-cadastro#token=synthetic-claim-for-test');
  vi.mocked(careApi.claim).mockResolvedValue(customer);
  render(<ClaimPage />, { wrapper });
  expect(window.location.hash).toBe('');
  await userEvent.click(screen.getByRole('button', { name: 'Confirmar vínculo do cadastro' }));
  expect(careApi.claim).toHaveBeenCalledExactlyOnceWith('synthetic-claim-for-test');
  expect(await screen.findByText('Cadastro vinculado')).toBeVisible();
  expect(localStorage.length + sessionStorage.length).toBe(0);
  window.location.hash = '#token=another-synthetic-claim';
  await waitFor(() =>
    expect(screen.getByRole('button', { name: 'Confirmar vínculo do cadastro' })).toBeVisible(),
  );
  await userEvent.click(screen.getByRole('button', { name: 'Confirmar vínculo do cadastro' }));
  expect(careApi.claim).toHaveBeenLastCalledWith('another-synthetic-claim');
});

it('does not adopt a background version while an older customer form is being edited', async () => {
  vi.mocked(careApi.saveCustomer).mockRejectedValue(
    new ApiError(409, 'test', 'Este registro foi alterado.', 'STALE_VERSION'),
  );
  const view = render(<CustomerForm staff={false} existing={customer} reload={vi.fn()} />, {
    wrapper,
  });
  await userEvent.clear(screen.getByLabelText('Nome completo (obrigatório)'));
  await userEvent.type(screen.getByLabelText('Nome completo (obrigatório)'), 'Minha edição');
  view.rerender(
    <CustomerForm
      staff={false}
      existing={{ ...customer, version: 2, name: 'Edição de outra pessoa' }}
      reload={vi.fn()}
    />,
  );
  await userEvent.click(screen.getByRole('button', { name: 'Salvar cadastro' }));
  await waitFor(() => expect(careApi.saveCustomer).toHaveBeenCalled());
  expect(vi.mocked(careApi.saveCustomer).mock.calls[0][2]?.version).toBe(1);
  expect(screen.getByLabelText('Nome completo (obrigatório)')).toHaveValue('Minha edição');
  expect(await screen.findByText(/Este registro foi alterado/)).toBeVisible();
});
