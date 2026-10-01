import { useNavigate, useOutletContext } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from '../../shared/lib/validation';
import { Alert, Badge, Skeleton } from '../../shared/ui/Feedback';
import { Button } from '../../shared/ui/Button';
import { Input } from '../../shared/ui/Input';
import { errorMessage } from '../../shared/lib/api';
import { identityApi, type Account, type Session } from './api';
import { roleLabels } from './account';
import { VerificationResend } from './AuthPage';

const passwordSchema = z
  .object({
    current_password: z.string().min(1, 'Informe sua senha atual.'),
    password: z.string().min(15, 'Use pelo menos 15 caracteres.').max(128),
    confirm: z.string(),
  })
  .refine((values) => values.password === values.confirm, {
    path: ['confirm'],
    message: 'As senhas precisam ser iguais.',
  });

export default function AccountPage() {
  const user = useOutletContext<Account>();
  return (
    <>
      <header className="area-heading">
        <span className="eyebrow">SEU PERFIL E SUA SEGURANÇA</span>
        <h1>Minha conta</h1>
        <p>Seus dados básicos, senha e sessões em um só lugar.</p>
      </header>
      <section className="identity-card">
        <h2>Dados da conta</h2>
        <dl className="account-details">
          <div>
            <dt>Nome</dt>
            <dd>{user.display_name}</dd>
          </div>
          <div>
            <dt>E-mail</dt>
            <dd>{user.email}</dd>
          </div>
          <div>
            <dt>Perfis</dt>
            <dd>{user.roles.map((role) => roleLabels[role]).join(' · ')}</dd>
          </div>
          <div>
            <dt>Confirmação</dt>
            <dd>
              <Badge>{user.email_verified ? 'E-mail confirmado' : 'Confirmação pendente'}</Badge>
            </dd>
          </div>
        </dl>
        {!user.email_verified && (
          <>
            <Alert title="Falta confirmar seu e-mail">
              Abra a mensagem enviada para seu endereço e confirme sua conta. Você pode solicitar um
              novo link abaixo.
            </Alert>
            <VerificationResend email={user.email} />
          </>
        )}
      </section>
      <div className="security-grid">
        <PasswordChange />
        <Sessions />
      </div>
    </>
  );
}

function PasswordChange() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(passwordSchema),
    defaultValues: { current_password: '', password: '', confirm: '' },
  });
  const mutation = useMutation({
    mutationFn: identityApi.changePassword,
    onSuccess: () => {
      queryClient.clear();
      navigate('/entrar?senha=alterada', { replace: true });
    },
  });
  return (
    <section className="identity-card">
      <h2>Alterar senha</h2>
      <p>Ao alterar, todas as suas sessões serão encerradas.</p>
      <form
        onSubmit={handleSubmit(({ current_password, password }) =>
          mutation.mutate({ current_password, password }),
        )}
        noValidate
      >
        <Input
          label="Senha atual"
          type="password"
          autoComplete="current-password"
          required
          maxLength={128}
          {...register('current_password')}
          error={errors.current_password?.message}
        />
        <Input
          label="Nova senha"
          type="password"
          autoComplete="new-password"
          hint="De 15 a 128 caracteres, incluindo espaços se preferir."
          required
          maxLength={128}
          {...register('password')}
          error={errors.password?.message}
        />
        <Input
          label="Confirmar nova senha"
          type="password"
          autoComplete="new-password"
          required
          maxLength={128}
          {...register('confirm')}
          error={errors.confirm?.message}
        />
        {mutation.isError && (
          <Alert tone="error" title="Não foi possível alterar">
            {errorMessage(mutation.error)}
          </Alert>
        )}
        <Button type="submit" busy={mutation.isPending}>
          Alterar senha e sair
        </Button>
      </form>
    </section>
  );
}

function Sessions() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ['identity', 'sessions'],
    queryFn: ({ signal }) => identityApi.sessions(signal),
    retry: false,
  });
  const mutation = useMutation({
    mutationFn: (session: Session) => identityApi.revokeSession(session.id),
    onSuccess: async (_, session) => {
      if (session.current) {
        queryClient.clear();
        navigate('/entrar', { replace: true });
      } else await queryClient.invalidateQueries({ queryKey: ['identity', 'sessions'] });
    },
  });
  return (
    <section className="identity-card">
      <h2>Sessões ativas</h2>
      <p>Encerre um acesso que você não reconhece.</p>
      {query.isPending && <Skeleton label="Carregando sessões" />}
      {query.isError && (
        <>
          <Alert tone="error" title="Não foi possível carregar">
            {errorMessage(query.error)}
          </Alert>
          <Button variant="secondary" onClick={() => void query.refetch()}>
            Tentar novamente
          </Button>
        </>
      )}
      {mutation.isError && (
        <Alert tone="error" title="Não foi possível encerrar">
          {errorMessage(mutation.error)}
        </Alert>
      )}
      {query.data && (
        <ul className="session-list">
          {query.data.map((session) => (
            <li key={session.id}>
              <strong>{session.current ? 'Esta sessão' : 'Outra sessão'}</strong>
              <span>Iniciada em {new Date(session.created_at).toLocaleString('pt-BR')}</span>
              <small>
                Última atividade: {new Date(session.last_seen_at).toLocaleString('pt-BR')}
              </small>
              <Button
                variant="secondary"
                busy={mutation.isPending && mutation.variables?.id === session.id}
                disabled={mutation.isPending}
                onClick={() => mutation.mutate(session)}
              >
                {session.current ? 'Encerrar esta sessão' : 'Encerrar sessão'}
              </Button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
