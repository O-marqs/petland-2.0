import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AuthPage from './AuthPage';
import { identityApi, type Account } from './api';
import { accountDestination } from './account';
import { ApiError } from '../../shared/lib/api';

vi.mock('./api', () => ({
  identityApi: {
    login: vi.fn(),
    register: vi.fn(),
    requestReset: vi.fn(),
    requestVerification: vi.fn(),
    verify: vi.fn(),
    reset: vi.fn(),
    acceptInvitation: vi.fn(),
    me: vi.fn(),
  },
}));

function setup(path: string) {
  return render(
    <QueryClientProvider
      client={
        new QueryClient({
          defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
        })
      }
    >
      <MemoryRouter initialEntries={[path]}>
        <AuthPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}
beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(identityApi.me).mockResolvedValue(null);
  window.history.replaceState(null, '', '/');
});

describe('identity forms', () => {
  it('guides registration without creating a session or claiming the account exists', async () => {
    const message = 'Se for possível cadastrar este endereço, enviaremos a confirmação.';
    vi.mocked(identityApi.register).mockResolvedValue({ message });
    setup('/criar-conta');
    await userEvent.type(screen.getByLabelText('Seu nome (obrigatório)'), 'Pessoa sintética');
    await userEvent.type(screen.getByLabelText('E-mail (obrigatório)'), 'pessoa@example.com');
    await userEvent.type(
      screen.getByLabelText('Senha (obrigatório)', { exact: true }),
      'Senha sintética para teste',
    );
    await userEvent.type(
      screen.getByLabelText('Confirmar senha (obrigatório)'),
      'Senha sintética para teste',
    );
    await userEvent.click(screen.getByRole('button', { name: 'Criar minha conta' }));
    const heading = await screen.findByRole('heading', {
      name: 'Confira seu e-mail para continuar.',
    });
    await waitFor(() => expect(heading).toHaveFocus());
    expect(screen.getByText(message)).toBeVisible();
    expect(screen.getByText('Adicione seu pet e escolha um serviço para agendar.')).toBeVisible();
    expect(identityApi.login).not.toHaveBeenCalled();
    expect(identityApi.me).not.toHaveBeenCalled();
  });

  it('validates and focuses the first invalid field before requesting registration', async () => {
    setup('/criar-conta');
    await userEvent.click(screen.getByRole('button', { name: 'Criar minha conta' }));
    await waitFor(() => expect(screen.getByLabelText('Seu nome (obrigatório)')).toHaveFocus());
    expect(identityApi.register).not.toHaveBeenCalled();
    expect(screen.getByText('Informe um e-mail válido.')).toBeVisible();
  });

  it('keeps password spaces and shows the safe server error without losing the email', async () => {
    vi.mocked(identityApi.login).mockRejectedValue(
      new ApiError(401, 'test', 'E-mail ou senha inválidos.', 'INVALID_CREDENTIALS'),
    );
    setup('/entrar');
    await userEvent.type(screen.getByLabelText('E-mail (obrigatório)'), 'pessoa@example.com');
    await userEvent.type(screen.getByLabelText('Senha (obrigatório)'), '  senha com espaços  ');
    await userEvent.click(screen.getByRole('button', { name: /^Entrar$/ }));
    expect(await screen.findByText('E-mail ou senha inválidos.')).toBeVisible();
    expect(identityApi.login).toHaveBeenCalledWith({
      email: 'pessoa@example.com',
      password: '  senha com espaços  ',
    });
    expect(screen.getByLabelText('E-mail (obrigatório)')).toHaveValue('pessoa@example.com');
  });

  it('reports the real recovery response and never confirms that an account exists', async () => {
    vi.mocked(identityApi.requestReset).mockResolvedValue({
      message: 'Se houver uma conta disponível, enviaremos as instruções.',
    });
    setup('/recuperar-acesso');
    await userEvent.type(screen.getByLabelText('E-mail (obrigatório)'), 'pessoa@example.com');
    await userEvent.click(screen.getByRole('button', { name: 'Enviar instruções' }));
    expect(
      await screen.findByText('Se houver uma conta disponível, enviaremos as instruções.'),
    ).toBeVisible();
  });

  it('removes the token from the address and waits for explicit confirmation before consuming it', async () => {
    window.history.replaceState(null, '', '/verificar-email#token=synthetic-token');
    vi.mocked(identityApi.verify).mockResolvedValue({ message: 'E-mail confirmado.' });
    setup('/verificar-email');
    expect(window.location.hash).toBe('');
    expect(identityApi.verify).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole('button', { name: 'Confirmar e-mail' }));
    await screen.findByText('E-mail confirmado.');
    expect(identityApi.verify).toHaveBeenCalledWith({ token: 'synthetic-token' });
  });

  it('does not offer password reset without a token', () => {
    setup('/redefinir-senha');
    expect(screen.getByText('Abra o link do seu e-mail')).toBeVisible();
    expect(screen.queryByRole('button', { name: 'Salvar nova senha' })).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Solicitar novo link' })).toHaveAttribute(
      'href',
      '/recuperar-acesso',
    );
  });
});

it('allows only exact destinations compatible with verified server-assigned roles', () => {
  const account: Account = {
    id: 'synthetic',
    display_name: 'Pessoa',
    email: 'pessoa@example.com',
    roles: ['CUSTOMER'],
    permissions: ['account:self'],
    email_verified: true,
    status: 'ACTIVE',
    version: 1,
  };
  for (const next of [
    'https://evil.example',
    '//evil.example',
    '/gestao',
    '/app/../gestao',
    '/app?next=https://evil.example',
  ])
    expect(accountDestination(account, next)).toBe('/app');
  expect(accountDestination(account, '/app/conta')).toBe('/app/conta');
  expect(accountDestination({ ...account, email_verified: false }, '/app')).toBe('/app/conta');
});
