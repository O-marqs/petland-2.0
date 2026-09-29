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
const CustomersPage = lazy(() => import('../features/care/CustomersPage'));
const PetsPage = lazy(() => import('../features/care/PetsPage'));
const CatalogPage = lazy(() => import('../features/care/CatalogPage'));
const ClaimPage = lazy(() => import('../features/care/ClaimPage'));
const Dashboard = lazy(() => import('../features/care/Dashboard'));
const BookingPage = lazy(() => import('../features/booking/BookingPage'));
const AppointmentsPage = lazy(() => import('../features/booking/AppointmentsPage'));
const CalendarPage = lazy(() => import('../features/booking/CalendarPage'));
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
              <Route path="servicos" element={<CatalogPage />} />
              <Route path="servicos/:serviceId" element={<CatalogPage />} />
              <Route path="vincular-cadastro" element={<ClaimPage />} />
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
              <Route path="app" element={<Dashboard />} />
              <Route path="app/perfil" element={<CustomersPage profile />} />
              <Route path="app/pets" element={<PetsPage />} />
              <Route path="app/agendar" element={<BookingPage />} />
              <Route path="app/reservas" element={<AppointmentsPage />} />
              <Route path="app/reservas/:appointmentId" element={<AppointmentsPage />} />
              <Route path="operacao/reservas" element={<AppointmentsPage staff />} />
              <Route path="operacao/reservas/:appointmentId" element={<AppointmentsPage staff />} />
              <Route path="operacao/agenda" element={<CalendarPage />} />
              <Route path="operacao/clientes/:customerId/agendar" element={<BookingPage />} />
              <Route path="operacao/clientes" element={<CustomersPage />} />
              <Route path="operacao/clientes/:customerId" element={<CustomersPage />} />
              <Route path="operacao/clientes/:customerId/pets" element={<PetsPage />} />
              <Route path="operacao/servicos" element={<CatalogPage staff />} />
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
