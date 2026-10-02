import { expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { VerificationPending } from './VerificationPending';
import { identityApi, type Account } from './api';

vi.mock('./api', () => ({ identityApi: { me: vi.fn(), requestVerification: vi.fn() } }));
const account: Account = {
  id: 'synthetic',
  email: 'pessoa@example.com',
  display_name: 'Pessoa',
  roles: ['CUSTOMER'],
  permissions: ['account:self'],
  email_verified: false,
  status: 'ACTIVE',
  version: 1,
};

it('keeps a pending account restricted, then continues only after the server confirms verification', async () => {
  vi.mocked(identityApi.me)
    .mockResolvedValueOnce(account)
    .mockResolvedValueOnce({ ...account, email_verified: true });
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={['/app/conta']}>
        <Routes>
          <Route path="/app/conta" element={<VerificationPending email={account.email} />} />
          <Route path="/app" element={<h1>Área do cliente</h1>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
  await userEvent.click(screen.getByRole('button', { name: 'Já confirmei meu e-mail' }));
  expect(await screen.findByText('A confirmação ainda está pendente')).toBeVisible();
  expect(screen.queryByRole('heading', { name: 'Área do cliente' })).not.toBeInTheDocument();
  await userEvent.click(screen.getByRole('button', { name: 'Já confirmei meu e-mail' }));
  expect(await screen.findByRole('heading', { name: 'Área do cliente' })).toBeVisible();
  expect(identityApi.me).toHaveBeenCalledTimes(2);
});
