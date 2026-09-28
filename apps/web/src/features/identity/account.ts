import { useQuery } from '@tanstack/react-query';
import { identityApi, type Account } from './api';

export function useAccount() {
  return useQuery({
    queryKey: ['identity', 'me'],
    queryFn: ({ signal }) => identityApi.me(signal),
    retry: false,
    staleTime: 0,
  });
}

export function accountDestination(account: Account, requested?: string | null): string {
  const allowed = ['/app/conta'];
  if (account.email_verified) {
    if (account.roles.includes('CUSTOMER')) allowed.push('/app');
    if (account.roles.some((role) => role === 'EMPLOYEE' || role === 'ADMIN'))
      allowed.push('/operacao');
    if (account.roles.includes('ADMIN')) allowed.push('/gestao', '/gestao/acessos');
  }
  if (requested && allowed.includes(requested)) return requested;
  if (!account.email_verified) return '/app/conta';
  return account.roles.includes('ADMIN')
    ? '/gestao'
    : account.roles.includes('EMPLOYEE')
      ? '/operacao'
      : '/app';
}

export const roleLabels = { CUSTOMER: 'Cliente', EMPLOYEE: 'Funcionário', ADMIN: 'Administrador' };
