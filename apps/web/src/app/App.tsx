import { lazy, Suspense } from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PublicLayout } from '../shared/layout/PublicLayout';
import { Skeleton } from '../shared/ui/Feedback';

const HomePage = lazy(() => import('../features/home/HomePage'));
const DesignSystemPage = lazy(() => import('../features/design-system/DesignSystemPage'));
const NotFoundPage = lazy(() => import('../features/system/NotFoundPage'));
const AuthPage = lazy(() => import('../features/identity/AuthPage'));
const AccountLayout = lazy(() => import('../features/identity/AccountLayout'));
const AccountPage = lazy(() => import('../features/identity/AccountPage'));
const AreaPage = lazy(() => import('../features/identity/AreaPage'));
const AccessPage = lazy(() => import('../features/identity/AccessPage'));
const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30000 } },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Suspense
          fallback={
            <div className="container loading-page">
              <Skeleton label="Carregando página" />
            </div>
          }
        >
          <Routes>
            <Route element={<PublicLayout />}>
              <Route index element={<HomePage />} />
              <Route path="design-system" element={<DesignSystemPage />} />
              {[
                'entrar',
                'criar-conta',
                'recuperar-acesso',
                'verificar-email',
                'redefinir-senha',
                'aceitar-convite',
              ].map((path) => (
                <Route key={path} path={path} element={<AuthPage />} />
              ))}
              <Route path="*" element={<NotFoundPage />} />
            </Route>
            <Route element={<AccountLayout />}>
              <Route path="app" element={<AreaPage />} />
              <Route path="app/conta" element={<AccountPage />} />
              <Route path="operacao" element={<AreaPage />} />
              <Route path="gestao" element={<AreaPage />} />
              <Route path="gestao/acessos" element={<AccessPage />} />
            </Route>
          </Routes>
        </Suspense>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
