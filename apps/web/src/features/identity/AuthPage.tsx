import { useEffect, useRef, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from '../../shared/lib/validation';
import { ArrowRight, ShieldCheck } from 'lucide-react';
import { Button } from '../../shared/ui/Button';
import { Input } from '../../shared/ui/Input';
import { Alert } from '../../shared/ui/Feedback';
import { errorMessage } from '../../shared/lib/api';
import { PetIllustration } from '../home/PetIllustration';
import { identityApi } from './api';
import { accountDestination } from './account';
import { LocalEmailNotice } from '../../shared/ui/LocalEmailNotice';

type Mode = 'login' | 'register' | 'forgot' | 'verify' | 'reset' | 'invite';
const modes: Record<string, Mode> = {
  '/entrar': 'login',
  '/criar-conta': 'register',
  '/recuperar-acesso': 'forgot',
  '/verificar-email': 'verify',
  '/redefinir-senha': 'reset',
  '/aceitar-convite': 'invite',
};
const copy = {
  login: [
    'Bom ter você por aqui.',
    'Entre com seu e-mail e senha para continuar de onde parou.',
    'Entrar',
  ],
  register: [
    'O cuidado começa aqui.',
    'Crie sua conta de cliente. Você receberá um link para confirmar seu e-mail.',
    'Criar minha conta',
  ],
  forgot: [
    'Vamos recuperar seu acesso.',
    'Informe o e-mail da sua conta para receber as instruções.',
    'Enviar instruções',
  ],
  verify: [
    'Confirme seu e-mail.',
    'Confirme que este endereço é seu para acessar os recursos da sua conta.',
    'Confirmar e-mail',
  ],
  reset: [
    'Um novo começo.',
    'Escolha uma nova senha. Suas sessões anteriores serão encerradas.',
    'Salvar nova senha',
  ],
  invite: [
    'Você faz parte do cuidado.',
    'Aceite o convite enviado para seu e-mail. Se já tem conta, informe sua senha atual.',
    'Aceitar convite',
  ],
};

export default function AuthPage() {
  const { pathname } = useLocation();
  const mode = modes[pathname] ?? 'login';
  return <AuthForm key={mode} mode={mode} />;
}

function AuthForm({ mode }: { mode: Mode }) {
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const [token, setToken] = useState(
    () => new URLSearchParams(window.location.hash.slice(1)).get('token') ?? '',
  );
  const [message, setMessage] = useState('');
  const heading = useRef<HTMLHeadingElement>(null);
  const confirmedAccount = useQuery({
    queryKey: ['identity', 'me'],
    queryFn: ({ signal }) => identityApi.me(signal),
    enabled: mode === 'verify' && !!message,
    retry: false,
    staleTime: 0,
  });
  useEffect(() => {
    if (message) heading.current?.focus();
  }, [message]);
  const emailRequired = ['login', 'register', 'forgot'].includes(mode);
  const passwordRequired = ['login', 'register', 'reset', 'invite'].includes(mode);
  const newPassword = ['register', 'reset'].includes(mode);
  const nameRequired = ['register', 'invite'].includes(mode);
  const schema = z
    .object({
      email: z.string(),
      password: z.string(),
      confirm_password: z.string(),
      display_name: z.string(),
    })
    .superRefine((values, ctx) => {
      if (emailRequired && !z.email().safeParse(values.email.trim()).success)
        ctx.addIssue({ code: 'custom', path: ['email'], message: 'Informe um e-mail válido.' });
      if (
        passwordRequired &&
        (values.password.length < (mode === 'login' ? 1 : 15) || values.password.length > 128)
      )
        ctx.addIssue({
          code: 'custom',
          path: ['password'],
          message: mode === 'login' ? 'Informe sua senha.' : 'Use de 15 a 128 caracteres.',
        });
      if (newPassword && values.password !== values.confirm_password)
        ctx.addIssue({
          code: 'custom',
          path: ['confirm_password'],
          message: 'As senhas precisam ser iguais.',
        });
      if (
        nameRequired &&
        (values.display_name.trim().length < 2 || values.display_name.trim().length > 100)
      )
        ctx.addIssue({
          code: 'custom',
          path: ['display_name'],
          message: 'Informe seu nome, de 2 a 100 caracteres.',
        });
    });
  type Values = z.infer<typeof schema>;
  const {
    register,
    handleSubmit,
    resetField,
    formState: { errors },
  } = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { email: '', password: '', confirm_password: '', display_name: '' },
  });
  const mutation = useMutation({
    mutationFn: async (values: Values) => {
      const email = values.email.trim();
      if (mode === 'login') {
        const account = await identityApi.login({ email, password: values.password });
        queryClient.clear();
        queryClient.setQueryData(['identity', 'me'], account);
        navigate(accountDestination(account, new URLSearchParams(location.search).get('next')), {
          replace: true,
        });
        return;
      }
      const response =
        mode === 'register'
          ? await identityApi.register({
              email,
              display_name: values.display_name.trim(),
              password: values.password,
            })
          : mode === 'forgot'
            ? await identityApi.requestReset({ email })
            : mode === 'verify'
              ? await identityApi.verify({ token })
              : mode === 'reset'
                ? await identityApi.reset({ token, password: values.password })
                : await identityApi.acceptInvitation({
                    token,
                    password: values.password,
                    display_name: values.display_name.trim(),
                  });
      setMessage(response.message);
      setToken('');
      resetField('password');
      resetField('confirm_password');
      await queryClient.invalidateQueries({ queryKey: ['identity'] });
    },
  });
  const resetMutation = mutation.reset;
  useEffect(() => {
    function receiveLink() {
      const incoming = new URLSearchParams(window.location.hash.slice(1)).get('token');
      if (!incoming) return;
      setToken(incoming);
      setMessage('');
      resetMutation();
      window.history.replaceState(
        window.history.state,
        '',
        window.location.pathname + window.location.search,
      );
    }
    receiveLink();
    window.addEventListener('hashchange', receiveLink);
    return () => window.removeEventListener('hashchange', receiveLink);
  }, [resetMutation]);
  const needsToken = ['verify', 'reset', 'invite'].includes(mode);
  const [title, description, action] = copy[mode];
  return (
    <div className="container auth-layout">
      <aside className="auth-story" aria-label="Bem-vindo ao PetLand">
        <span className="eyebrow">CUIDADO QUE CONECTA</span>
        <h2>Mais perto de quem faz parte da família.</h2>
        <PetIllustration />
        <p>Seu espaço para organizar o cuidado, com clareza em cada etapa.</p>
      </aside>
      <section className="auth-panel" aria-labelledby="auth-title">
        <span className="eyebrow">
          <ShieldCheck size={18} aria-hidden="true" /> SEU ESPAÇO PETLAND
        </span>
        <h1 id="auth-title" tabIndex={-1} ref={heading}>
          {message && mode === 'register' ? 'Confira seu e-mail para continuar.' : title}
        </h1>
        <p>
          {message && mode === 'register'
            ? 'Confirme seu e-mail e entre na sua área para cadastrar pets e reservar cuidados.'
            : description}
        </p>
        {message ? (
          <>
            <Alert tone="success" title="Pronto para o próximo passo">
              {message}
            </Alert>
            {['register', 'forgot'].includes(mode) && <LocalEmailNotice />}
            {mode === 'register' && (
              <ol className="onboarding-steps">
                <li>Abra o e-mail e confirme seu endereço.</li>
                <li>Entre na sua área e complete seu cadastro de contato.</li>
                <li>Adicione seu pet e escolha um serviço para agendar.</li>
              </ol>
            )}
            <Link
              className="button button--primary"
              to={
                mode === 'verify' && confirmedAccount.data?.email_verified
                  ? accountDestination(confirmedAccount.data)
                  : '/entrar'
              }
            >
              {mode === 'verify' && confirmedAccount.data?.email_verified
                ? 'Continuar para minha área'
                : 'Ir para o login'}
            </Link>
          </>
        ) : (
          <>
            {mutation.isError && (
              <Alert tone="error" title="Não foi possível continuar">
                {errorMessage(mutation.error)}
              </Alert>
            )}
            {needsToken && !token ? (
              <Alert title="Abra o link do seu e-mail">
                O link tem prazo limitado. Se ele expirou, solicite outro. Para convites, peça ao
                administrador que envie um novo.
              </Alert>
            ) : (
              <form onSubmit={handleSubmit((values) => mutation.mutate(values))} noValidate>
                {nameRequired && (
                  <Input
                    label="Seu nome"
                    autoComplete="name"
                    required
                    maxLength={100}
                    {...register('display_name')}
                    error={errors.display_name?.message}
                  />
                )}
                {emailRequired && (
                  <Input
                    label="E-mail"
                    type="email"
                    autoComplete="email"
                    required
                    maxLength={254}
                    {...register('email')}
                    error={errors.email?.message}
                  />
                )}
                {passwordRequired && (
                  <Input
                    label={mode === 'reset' ? 'Nova senha' : 'Senha'}
                    type="password"
                    autoComplete={
                      mode === 'login' || mode === 'invite' ? 'current-password' : 'new-password'
                    }
                    required
                    maxLength={128}
                    hint={
                      mode === 'login'
                        ? undefined
                        : 'De 15 a 128 caracteres. Você pode usar espaços e colar sua senha.'
                    }
                    {...register('password')}
                    error={errors.password?.message}
                  />
                )}
                {newPassword && (
                  <Input
                    label="Confirmar senha"
                    type="password"
                    autoComplete="new-password"
                    required
                    maxLength={128}
                    {...register('confirm_password')}
                    error={errors.confirm_password?.message}
                  />
                )}
                {mode === 'login' && (
                  <Link className="text-link" to="/recuperar-acesso">
                    Esqueci minha senha
                  </Link>
                )}
                <Button type="submit" busy={mutation.isPending}>
                  {action}
                  <ArrowRight size={18} aria-hidden="true" />
                </Button>
              </form>
            )}
          </>
        )}
        {mode === 'verify' && <VerificationResend />}
        {mode === 'verify' && !message && <LocalEmailNotice />}
        {mode === 'reset' && !message && (
          <Link className="text-link" to="/recuperar-acesso">
            Solicitar novo link
          </Link>
        )}
        <p className="auth-alternative">
          {mode === 'login' ? (
            <>
              Ainda não tem conta? <Link to="/criar-conta">Criar uma conta</Link>
            </>
          ) : (
            <>
              Já tem uma conta? <Link to="/entrar">Entrar no PetLand</Link>
            </>
          )}
        </p>
      </section>
    </div>
  );
}

export function VerificationResend({ email: initialEmail = '' }: { email?: string }) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(z.object({ email: z.email('Informe um e-mail válido.') })),
    defaultValues: { email: initialEmail },
  });
  const mutation = useMutation({ mutationFn: identityApi.requestVerification });
  return (
    <details className="resend-panel">
      <summary>Reenviar confirmação de e-mail</summary>
      <form onSubmit={handleSubmit((values) => mutation.mutate(values))} noValidate>
        <Input
          label="E-mail para confirmação"
          type="email"
          autoComplete="email"
          required
          {...register('email')}
          error={errors.email?.message}
        />
        <Button type="submit" variant="secondary" busy={mutation.isPending}>
          Reenviar confirmação
        </Button>
        {mutation.isSuccess && <Alert title="Solicitação recebida">{mutation.data.message}</Alert>}
        {mutation.isError && (
          <Alert tone="error" title="Não foi possível reenviar">
            {errorMessage(mutation.error)}
          </Alert>
        )}
      </form>
    </details>
  );
}
