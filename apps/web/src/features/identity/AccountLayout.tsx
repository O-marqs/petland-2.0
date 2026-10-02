import { Suspense, useId, useRef, useState } from 'react';
import { Link, Navigate, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { PawPrint, LogOut, Menu, X } from 'lucide-react';
import { useAccount, roleLabels } from './account';
import { identityApi } from './api';
import { Alert, Skeleton } from '../../shared/ui/Feedback';
import { Button } from '../../shared/ui/Button';
import { errorMessage } from '../../shared/lib/api';
import { RouteFocus } from '../../shared/layout/RouteFocus';

export default function AccountLayout() {
  const account = useAccount();
  const { pathname, search } = useLocation();
  const [expandedPath, setExpandedPath] = useState<string | null>(null);
  const navigationId = useId();
  const menuButton = useRef<HTMLButtonElement>(null);
  const menuOpen = expandedPath === pathname;
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const logout = useMutation({
    mutationFn: identityApi.logout,
    onSuccess: () => {
      queryClient.clear();
      navigate('/entrar', { replace: true });
    },
  });
  if (account.isPending)
    return (
      <main id="main" tabIndex={-1} className="container loading-page">
        <Skeleton label="Carregando sua conta" />
      </main>
    );
  if (account.isError)
    return (
      <main id="main" tabIndex={-1} className="container loading-page">
        <RouteFocus />
        <h1>Sua conta</h1>
        <Alert tone="error" title="Não foi possível carregar sua conta">
          {errorMessage(account.error)}
        </Alert>
        <Button onClick={() => void account.refetch()}>Tentar novamente</Button>
      </main>
    );
  if (!account.data)
    return <Navigate to={`/entrar?next=${encodeURIComponent(pathname + search)}`} replace />;
  const user = account.data;
  const customer = user.email_verified && user.roles.includes('CUSTOMER');
  const employee =
    user.email_verified && user.roles.some((role) => role === 'EMPLOYEE' || role === 'ADMIN');
  const admin = user.email_verified && user.roles.includes('ADMIN');
  const management = admin && pathname.startsWith('/gestao');
  const groups = [
    {
      label: 'Seu cuidado',
      show: customer,
      items: [
        ['/app', 'Área do cliente'],
        ['/app/pets', 'Meus pets'],
        ['/app/agendar', 'Agendar um cuidado'],
        ['/app/reservas', 'Minhas reservas'],
        ['/app/perfil', 'Meu cadastro'],
      ],
    },
    {
      label: 'Operação',
      show: employee,
      items: [
        ['/operacao', 'Hoje na PetLand'],
        ['/operacao/agenda', 'Agenda'],
        ['/operacao/reservas', 'Reservas'],
        ['/operacao/clientes', 'Clientes e pets'],
        ['/operacao/servicos', 'Serviços'],
        ['/operacao/configuracoes', 'Equipe e horários'],
        ['/operacao/escala', 'Equipe por data'],
        ['/operacao/capacidade', 'Capacidade física'],
      ],
    },
    {
      label: 'Gestão',
      show: admin,
      items: [
        ['/gestao', 'Visão geral'],
        ['/gestao/auditoria', 'Auditoria'],
        ['/gestao/acessos', 'Pessoas e acessos'],
      ],
    },
  ].filter((group) => group.show);
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
          <Link className="account-utility" to="/app/conta">
            Minha conta
          </Link>
          <Button variant="secondary" onClick={() => logout.mutate()} busy={logout.isPending}>
            <LogOut size={17} aria-hidden="true" />
            Sair
          </Button>
        </div>
      </header>
      <div
        className={`container application-layout ${employee ? 'workspace-team' : 'workspace-customer'}`}
      >
        <aside
          className="area-navigation"
          onKeyDown={(event) => {
            if (event.key === 'Escape' && menuOpen) {
              setExpandedPath(null);
              menuButton.current?.focus();
            }
          }}
        >
          <div className="mobile-navigation-tools">
            <span className="eyebrow">{employee ? 'EQUIPE PETLAND' : 'SEU ESPAÇO'}</span>
            <button
              ref={menuButton}
              className="button button--secondary"
              aria-label="Menu da conta"
              aria-expanded={menuOpen}
              aria-controls={navigationId}
              onClick={() => setExpandedPath(menuOpen ? null : pathname)}
            >
              {menuOpen ? (
                <X size={18} aria-hidden="true" />
              ) : (
                <Menu size={18} aria-hidden="true" />
              )}
              {menuOpen ? 'Fechar' : 'Menu'}
            </button>
          </div>
          <nav className="mobile-primary-navigation" aria-label="Atalhos principais">
            <NavLink
              to={management ? '/gestao' : employee ? '/operacao/agenda' : '/app'}
              end
              aria-label={management ? 'Visão geral' : employee ? 'Agenda' : 'Área do cliente'}
              className={({ isActive }) => (isActive ? 'active' : undefined)}
            >
              {management ? 'Visão geral' : employee ? 'Agenda' : 'Início'}
            </NavLink>
            {(employee || customer) && (
              <NavLink
                to={
                  employee
                    ? management
                      ? '/operacao/agenda'
                      : '/operacao/reservas'
                    : '/app/agendar'
                }
                aria-label={employee ? (management ? 'Agenda' : 'Reservas') : 'Agendar um cuidado'}
              >
                {employee ? (management ? 'Agenda' : 'Reservas') : 'Agendar'}
              </NavLink>
            )}
          </nav>
          <nav
            id={navigationId}
            className="workspace-navigation"
            aria-label="Áreas da conta"
            data-open={menuOpen}
            onClick={(event) => {
              const link = (event.target as HTMLElement).closest('a');
              if (link) {
                setExpandedPath(null);
                if (link.getAttribute('href') === pathname) menuButton.current?.focus();
              }
            }}
          >
            {groups.map((group) => (
              <div className="navigation-group" key={group.label}>
                <span className="navigation-group-label">{group.label}</span>
                {group.items.map(([to, label]) => (
                  <NavLink
                    key={to}
                    to={to}
                    end={to === '/app' || to === '/gestao' || to === '/operacao'}
                    className={({ isActive }) => (isActive ? 'active' : undefined)}
                  >
                    {label}
                  </NavLink>
                ))}
              </div>
            ))}
          </nav>
          {employee && (
            <p className="navigation-signature">
              Do horário marcado
              <br />
              ao cuidado feito<span aria-hidden="true">.</span>
            </p>
          )}
        </aside>
        <main id="main" tabIndex={-1} className="area-content">
          <RouteFocus />
          {logout.isError && (
            <Alert tone="error" title="Não foi possível sair">
              {errorMessage(logout.error)}
            </Alert>
          )}
          {allowed ? (
            <Suspense key={pathname} fallback={<Skeleton label="Carregando página" />}>
              <Outlet context={user} />
            </Suspense>
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
