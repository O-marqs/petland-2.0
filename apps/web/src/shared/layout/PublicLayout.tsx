import { Suspense } from 'react';
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom';
import { PawPrint } from 'lucide-react';
import { RouteFocus } from './RouteFocus';
import { Skeleton } from '../ui/Feedback';

export function PublicLayout() {
  const { pathname } = useLocation();
  return (
    <>
      <a className="skip-link" href="#main">
        Pular para o conteúdo
      </a>
      <div className="preview-strip">
        Um novo capítulo de cuidado. <span>PetLand 3.0 · Em desenvolvimento</span>
      </div>
      <header className="public-header container">
        <Link className="brand" to="/" aria-label="PetLand, página inicial">
          <PawPrint aria-hidden="true" size={30} strokeWidth={2} />
          PetLand<span className="brand-dot">.</span>
        </Link>
        <nav aria-label="Navegação principal">
          <NavLink to="/" end>
            Início
          </NavLink>
          <NavLink to="/servicos">Serviços</NavLink>
          <NavLink to="/entrar">Entrar</NavLink>
          <NavLink to="/criar-conta">Criar conta</NavLink>
        </nav>
      </header>
      <main id="main" tabIndex={-1} className="public-main">
        <RouteFocus />
        <Suspense
          key={pathname}
          fallback={
            <div className="container loading-page">
              <Skeleton label="Carregando página" />
            </div>
          }
        >
          <Outlet />
        </Suspense>
      </main>
      <footer className="public-footer container">
        <Link className="brand" to="/">
          PetLand<span className="brand-dot">.</span>
        </Link>
        <p>Cuidar também é organizar.</p>
        <span>Projeto de portfólio · Em desenvolvimento</span>
        <Link to="/design-system">Explorar componentes</Link>
      </footer>
    </>
  );
}
