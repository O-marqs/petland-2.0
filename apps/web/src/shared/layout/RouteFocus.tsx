import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

/** Announce a new page, including content that arrives after the layout. */
export function RouteFocus() {
  const { pathname } = useLocation();
  useEffect(() => {
    const main = document.getElementById('main');
    if (!main) return;
    document.title = 'PetLand · Carregando página';
    main.focus();
    window.scrollTo(0, 0);
    const announce = () => {
      const heading = main.querySelector('h1');
      if (!heading?.textContent?.trim()) return false;
      document.title = `${heading.textContent.trim()} · PetLand`;
      // Never interrupt someone who already started using the loading page.
      if (document.activeElement === main) {
        heading.tabIndex = -1;
        heading.focus({ preventScroll: true });
      }
      return true;
    };
    if (announce()) return;
    const observer = new MutationObserver(() => {
      if (announce()) observer.disconnect();
    });
    observer.observe(main, { childList: true, subtree: true, characterData: true });
    return () => observer.disconnect();
  }, [pathname]);
  return null;
}
