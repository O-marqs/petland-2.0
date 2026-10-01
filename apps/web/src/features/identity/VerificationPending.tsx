import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { identityApi } from './api';
import { accountDestination } from './account';
import { VerificationResend } from './AuthPage';
import { LocalEmailNotice } from '../../shared/ui/LocalEmailNotice';
import { Alert } from '../../shared/ui/Feedback';
import { Button } from '../../shared/ui/Button';
import { errorMessage } from '../../shared/lib/api';

export function VerificationPending({ email }: { email: string }) {
  const cache = useQueryClient();
  const navigate = useNavigate();
  const refresh = useMutation({
    mutationFn: () => identityApi.me(),
    onSuccess: (account) => {
      cache.setQueryData(['identity', 'me'], account);
      if (!account) navigate('/entrar', { replace: true });
      else if (account.email_verified) navigate(accountDestination(account), { replace: true });
    },
  });
  return (
    <div className="care-stack">
      <Alert title="Falta confirmar seu e-mail">
        Abra a mensagem destinada a {email} e confirme seu endereço. Depois você poderá completar
        seu cadastro de contato, adicionar pets e reservar cuidados.
      </Alert>
      <LocalEmailNotice />
      <Button variant="secondary" busy={refresh.isPending} onClick={() => refresh.mutate()}>
        Já confirmei meu e-mail
      </Button>
      {refresh.isSuccess && refresh.data && !refresh.data.email_verified && (
        <Alert title="A confirmação ainda está pendente">
          Abra o link da mensagem e clique em “Confirmar e-mail”. Depois, tente novamente aqui.
        </Alert>
      )}
      {refresh.isError && (
        <Alert tone="error" title="Não foi possível conferir">
          {errorMessage(refresh.error)}
        </Alert>
      )}
      <VerificationResend email={email} />
    </div>
  );
}
