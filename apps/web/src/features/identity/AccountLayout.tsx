import { useEffect } from 'react';
import { Link, Navigate, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { PawPrint, LogOut, UserRound, LayoutGrid, CalendarDays, ShieldCheck } from 'lucide-react';
import { useAccount, roleLabels } from './account';
import { identityApi } from './api';
import { Alert, Skeleton } from '../../shared/ui/Feedback';
import { Button } from '../../shared/ui/Button';
import { errorMessage } from '../../shared/lib/api';

export default function AccountLayout() {
  const account = useAccount();
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const logout = useMutation({
    mutationFn: identityApi.logout,
    onSuccess: () => {
      queryClient.clear();
      navigate('/entrar', { replace: true });
    },
  });
  useEffect(() => {
    document.title = 'Sua área · PetLand';
    document.getElementById('main')?.focus();
    window.scrollTo(0, 0);
  }, [pathname]);
  if (account.isPending)
    return (
      <main className="container loading-page">
        <Skeleton label="Carregando sua conta" />
      </main>
    );
  if (account.isError)
    return (
      <main className="container loading-page">
        <Alert tone="error" title="Não foi possível carregar sua conta">
          {errorMessage(account.error)}
        </Alert>
        <Button onClick={() => void account.refetch()}>Tentar novamente</Button>
      </main>
    );
  if (!account.data)
    return <Navigate to={`/entrar?next=${encodeURIComponent(pathname)}`} replace />;
  const user = account.data;
  const customer = user.email_verified && user.roles.includes('CUSTOMER');
  const employee =
    user.email_verified && user.roles.some((role) => role === 'EMPLOYEE' || role === 'ADMIN');
  const admin = user.email_verified && user.roles.includes('ADMIN');
  const allowed =
    pathname === '/app/conta' ||
    (pathname.startsWith('/gestao')
      ? admin
      : pathname.startsWith('/operacao')
        ? employee
        : customer);
  return (
    <>
      <a className="skip-link" href="#main">
        Pular para o conteúdo
      </a>
      <header className="account-header">
        <div className="container account-header-inner">
          <Link className="brand" to="/" aria-label="PetLand, página inicial">
            <PawPrint aria-hidden="true" />
            PetLand<span className="brand-dot">.</span>
          </Link>
          <div className="account-identity">
            <span>{user.display_name}</span>
            <small>{user.roles.map((role) => roleLabels[role]).join(' · ')}</small>
          </div>
          <Button variant="secondary" onClick={() => logout.mutate()} busy={logout.isPending}>
            <LogOut size={17} aria-hidden="true" />
            Sair
          </Button>
        </div>
      </header>
      <div className="container application-layout">
        <aside className="area-navigation">
          <span className="eyebrow">SEU ESPAÇO</span>
          <nav aria-label="Áreas da conta">
            {customer && (
              <NavLink to="/app" end>
                <LayoutGrid size={20} aria-hidden="true" />
                Área do cliente
              </NavLink>
            )}
            {customer && <NavLink to="/app/pets">Meus pets</NavLink>}
            {customer && <NavLink to="/app/perfil">Meu cadastro</NavLink>}
            {employee && <NavLink to="/operacao/clientes">Clientes e pets</NavLink>}
            {employee && <NavLink to="/operacao/servicos">Serviços</NavLink>}
            {employee && (
              <NavLink to="/operacao" end>
                <CalendarDays size={20} aria-hidden="true" />
                Área da equipe
              </NavLink>
            )}
            {admin && (
              <NavLink to="/gestao" end>
                <LayoutGrid size={20} aria-hidden="true" />
                Administração
              </NavLink>
            )}
            {admin && (
              <NavLink to="/gestao/acessos">
                <ShieldCheck size={20} aria-hidden="true" />
                Pessoas e acessos
              </NavLink>
            )}
            <NavLink to="/app/conta">
              <UserRound size={20} aria-hidden="true" />
              Minha conta
            </NavLink>
          </nav>
          <p>Um cuidado mais próximo, a cada etapa.</p>
        </aside>
        <main id="main" tabIndex={-1} className="area-content">
          {logout.isError && (
            <Alert tone="error" title="Não foi possível sair">
              {errorMessage(logout.error)}
            </Alert>
          )}
          {allowed ? (
            <Outlet context={user} />
          ) : (
            <>
              <h1>Acesso indisponível</h1>
              <Alert title="Esta área não está disponível para sua conta">
                {user.email_verified
                  ? 'Seu perfil não permite acessar esta área.'
                  : 'Confirme seu e-mail para continuar.'}
              </Alert>
              <Link className="button button--primary" to="/app/conta">
                Ir para minha conta
              </Link>
            </>
          )}
        </main>
      </div>
    </>
  );
}
