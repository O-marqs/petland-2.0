import { useState } from 'react';
import { useNavigate, useOutletContext } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from '../../shared/lib/validation';
import { Alert, Badge, EmptyState, Skeleton } from '../../shared/ui/Feedback';
import { Button } from '../../shared/ui/Button';
import { Input } from '../../shared/ui/Input';
import { errorMessage } from '../../shared/lib/api';
import { identityApi, type Account, type Role } from './api';
import { roleLabels } from './account';

export default function AccessPage() {
  const actor = useOutletContext<Account>();
  const navigate = useNavigate();
  const cache = useQueryClient();
  const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState<Account | null>(null);
  const users = useQuery({
    queryKey: ['identity', 'users', offset],
    queryFn: ({ signal }) => identityApi.users(offset, signal),
    retry: false,
  });
  async function saved(id: string) {
    if (id === actor.id) {
      cache.clear();
      navigate('/entrar', { replace: true });
    } else await cache.invalidateQueries({ queryKey: ['identity', 'users'] });
    setSelected(null);
  }
  return (
    <>
      <header className="area-heading">
        <span className="eyebrow">ADMINISTRAÇÃO</span>
        <h1>Pessoas e acessos</h1>
        <p>Convide a equipe e mantenha cada acesso adequado à sua função.</p>
      </header>
      <InviteForm />
      <section className="identity-card">
        <div className="section-heading">
          <div>
            <h2>Contas cadastradas</h2>
            <p>Alterações exigem sua senha e encerram as sessões da conta alterada.</p>
          </div>
          <Button variant="secondary" onClick={() => void users.refetch()}>
            Atualizar lista
          </Button>
        </div>
        {users.isPending && <Skeleton label="Carregando contas" />}
        {users.isError && (
          <Alert tone="error" title="Não foi possível carregar as contas">
            {errorMessage(users.error)}
          </Alert>
        )}
        {users.data?.items.length === 0 && (
          <EmptyState title="Nenhuma conta nesta página">
            Volte à página anterior para consultar os acessos.
          </EmptyState>
        )}
        {users.data && (
          <>
            <ul className="people-list">
              {users.data.items.map((user) => (
                <li key={user.id}>
                  <div>
                    <h3>{user.display_name}</h3>
                    <p>{user.email}</p>
                    <small>{user.roles.map((role) => roleLabels[role]).join(' · ')}</small>
                  </div>
                  <Badge>{user.status === 'ACTIVE' ? 'Ativa' : 'Desativada'}</Badge>
                  <Button
                    variant="secondary"
                    onClick={() => setSelected(user)}
                    aria-label={`Gerenciar ${user.display_name}`}
                  >
                    Gerenciar
                  </Button>
                </li>
              ))}
            </ul>
            <div className="pagination">
              <Button
                variant="secondary"
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - 20))}
              >
                Anterior
              </Button>
              <span>Página {offset / 20 + 1}</span>
              <Button
                variant="secondary"
                disabled={!users.data.has_more}
                onClick={() => setOffset(offset + 20)}
              >
                Próxima
              </Button>
            </div>
          </>
        )}
      </section>
      {selected && (
        <AccessEditor
          key={`${selected.id}-${selected.version}`}
          user={selected}
          onClose={() => setSelected(null)}
          onSaved={() => saved(selected.id)}
        />
      )}
    </>
  );
}

function InviteForm() {
  const schema = z.object({
    email: z.email('Informe um e-mail válido.'),
    current_password: z.string().min(1, 'Confirme sua senha atual.'),
  });
  const {
    register,
    handleSubmit,
    resetField,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { email: '', current_password: '' },
  });
  const mutation = useMutation({
    mutationFn: identityApi.invite,
    onSuccess: () => resetField('current_password'),
  });
  return (
    <section className="identity-card">
      <h2>Convidar para a equipe</h2>
      <p>
        O convite concede o perfil Funcionário após confirmação do e-mail. Nenhuma senha é enviada
        por mensagem.
      </p>
      <form
        className="invite-form"
        onSubmit={handleSubmit((values) => mutation.mutate(values))}
        noValidate
      >
        <Input
          label="E-mail da pessoa convidada"
          type="email"
          required
          autoComplete="off"
          {...register('email')}
          error={errors.email?.message}
        />
        <Input
          label="Sua senha atual"
          type="password"
          required
          autoComplete="current-password"
          maxLength={128}
          {...register('current_password')}
          error={errors.current_password?.message}
        />
        <Button type="submit" busy={mutation.isPending}>
          Enviar convite
        </Button>
        {mutation.isError && (
          <Alert tone="error" title="Não foi possível convidar">
            {errorMessage(mutation.error)}
          </Alert>
        )}
        {mutation.isSuccess && (
          <Alert tone="success" title="Solicitação registrada">
            {mutation.data.message}
          </Alert>
        )}
      </form>
    </section>
  );
}

function AccessEditor({
  user,
  onClose,
  onSaved,
}: {
  user: Account;
  onClose: () => void;
  onSaved: () => Promise<void>;
}) {
  const schema = z.object({
    roles: z
      .array(z.enum(['CUSTOMER', 'EMPLOYEE', 'ADMIN']))
      .min(1, 'Selecione pelo menos um perfil.'),
    current_password: z.string().min(1, 'Confirme sua senha atual.'),
  });
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { roles: user.roles, current_password: '' },
  });
  const mutation = useMutation({
    mutationFn: async ({
      roles,
      current_password,
      command,
    }: {
      roles: Role[];
      current_password: string;
      command: 'roles' | 'status';
    }) => {
      if (command === 'roles')
        await identityApi.roles(user.id, {
          roles,
          current_password,
          expected_version: user.version,
        });
      else
        await identityApi.status(user.id, {
          status: user.status === 'ACTIVE' ? 'DISABLED' : 'ACTIVE',
          current_password,
          expected_version: user.version,
        });
    },
    onSuccess: onSaved,
  });
  return (
    <section className="identity-card access-editor" aria-label={`Acesso de ${user.display_name}`}>
      <h2>Acesso de {user.display_name}</h2>
      <p>{user.email}</p>
      <form
        onSubmit={handleSubmit((values) => mutation.mutate({ ...values, command: 'roles' }))}
        noValidate
      >
        <fieldset>
          <legend>Perfis da conta</legend>
          {(['CUSTOMER', 'EMPLOYEE', 'ADMIN'] as Role[]).map((role) => (
            <label className="check-label" key={role}>
              <input type="checkbox" value={role} {...register('roles')} />
              {roleLabels[role]}
            </label>
          ))}
          {errors.roles && (
            <p className="field-error" role="alert">
              {errors.roles.message}
            </p>
          )}
        </fieldset>
        <Input
          label="Confirme sua senha de administrador"
          type="password"
          autoComplete="current-password"
          required
          maxLength={128}
          {...register('current_password')}
          error={errors.current_password?.message}
        />
        {mutation.isError && (
          <Alert tone="error" title="A alteração não foi realizada">
            {errorMessage(mutation.error)}
          </Alert>
        )}
        <p className="field-hint">
          Deve permanecer pelo menos um administrador ativo. Alterar seu próprio acesso exigirá novo
          login.
        </p>
        <div className="form-actions">
          <Button type="submit" busy={mutation.isPending}>
            Salvar perfis
          </Button>
          <Button
            type="button"
            variant={user.status === 'ACTIVE' ? 'danger' : 'secondary'}
            disabled={mutation.isPending}
            onClick={() =>
              void handleSubmit((values) => mutation.mutate({ ...values, command: 'status' }))()
            }
          >
            {user.status === 'ACTIVE' ? 'Desativar conta' : 'Reativar conta'}
          </Button>
          <Button type="button" variant="secondary" onClick={onClose}>
            Fechar
          </Button>
        </div>
      </form>
    </section>
  );
}
