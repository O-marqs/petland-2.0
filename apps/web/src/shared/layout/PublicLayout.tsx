import { useEffect } from 'react';
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom';
import { PawPrint, ArrowUpRight } from 'lucide-react';

export function PublicLayout() {
  const { pathname } = useLocation();
  useEffect(() => {
    document.title =
      pathname === '/design-system' ? 'Componentes · PetLand' : 'PetLand · Cuidado que conecta';
    document.getElementById('main')?.focus();
    window.scrollTo(0, 0);
  }, [pathname]);
  return (
    <>
      <a className="skip-link" href="#main">
        Pular para o conteúdo
      </a>
      <div className="preview-strip">
        Um novo capítulo de cuidado. <span>Prévia PetLand 3.0</span>
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
          <NavLink to="/design-system">
            Componentes <ArrowUpRight size={16} aria-hidden="true" />
          </NavLink>
        </nav>
      </header>
      <main id="main" tabIndex={-1}>
        <Outlet />
      </main>
      <footer className="public-footer container">
        <Link className="brand" to="/">
          PetLand<span className="brand-dot">.</span>
        </Link>
        <p>Cuidar também é organizar.</p>
        <span>Projeto de portfólio · Em desenvolvimento</span>
      </footer>
    </>
  );
}
