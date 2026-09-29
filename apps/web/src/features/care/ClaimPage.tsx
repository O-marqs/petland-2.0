import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { careApi } from './api';
import { useAccount } from '../identity/account';
import { Button } from '../../shared/ui/Button';
import { Alert, Skeleton } from '../../shared/ui/Feedback';
import { errorMessage } from '../../shared/lib/api';

export default function ClaimPage() {
  const [token, setToken] = useState(
    () => new URLSearchParams(window.location.hash.slice(1)).get('token') || '',
  );
  const account = useAccount();
  const cache = useQueryClient();
  const mutation = useMutation({
    mutationFn: () => careApi.claim(token),
    onSuccess: async () => {
      setToken('');
      await cache.invalidateQueries({ queryKey: ['care'] });
    },
  });
  const reset = mutation.reset;
  useEffect(() => {
    const read = () => {
      const value = new URLSearchParams(window.location.hash.slice(1)).get('token') || '';
      setToken(value);
      reset();
      window.history.replaceState(null, '', window.location.pathname);
    };
    window.history.replaceState(null, '', window.location.pathname);
    window.addEventListener('hashchange', read);
    return () => window.removeEventListener('hashchange', read);
  }, [reset]);
  return (
    <div className="container care-public care-narrow">
      <span className="eyebrow">SEU CADASTRO PETLAND</span>
      <h1>Seu cuidado, conectado.</h1>
      <p>Vincule o cadastro feito pela equipe para acompanhar seus pets pela sua conta.</p>
      {account.isPending ? (
        <Skeleton label="Carregando sua conta" />
      ) : mutation.isSuccess ? (
        <>
          <Alert tone="success" title="Cadastro vinculado">
            Seus dados e pets já estão na sua área.
          </Alert>
          <Link className="button button--primary" to="/app/pets">
            Ver meus pets
          </Link>
        </>
      ) : !account.data ? (
        <section className="identity-card">
          <h2>Entre com o e-mail que recebeu o convite.</h2>
          <p>
            Depois de entrar ou criar e confirmar sua conta, abra novamente o link do e-mail para
            concluir o vínculo.
          </p>
          <div className="care-actions">
            <Link className="button button--primary" to="/entrar">
              Entrar
            </Link>
            <Link className="button button--secondary" to="/criar-conta">
              Criar conta
            </Link>
          </div>
        </section>
      ) : (
        <section className="identity-card">
          <h2>Confirmar vínculo</h2>
          <p>
            Você está usando {account.data.email}. Confirme para associar a esta conta o cadastro
            indicado no e-mail. Se você já tem outro cadastro, a equipe precisará revisar a
            situação.
          </p>
          {!account.data.email_verified ? (
            <Alert title="Confirme seu e-mail">
              Confirme o e-mail da conta antes de vincular o cadastro.
            </Alert>
          ) : !token ? (
            <Alert title="Abra o link recebido por e-mail">
              O link é necessário para confirmar o vínculo e tem validade de 24 horas.
            </Alert>
          ) : (
            <Button busy={mutation.isPending} onClick={() => mutation.mutate()}>
              Confirmar vínculo do cadastro
            </Button>
          )}
          {mutation.isError && (
            <Alert tone="error" title="Não foi possível vincular">
              {errorMessage(mutation.error)}
            </Alert>
          )}
        </section>
      )}
    </div>
  );
}
