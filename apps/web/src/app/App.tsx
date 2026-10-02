import { lazy, Suspense } from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PublicLayout } from '../shared/layout/PublicLayout';
import { Skeleton } from '../shared/ui/Feedback';
import { localEmailUrl } from '../shared/lib/local-email';
import { PublicAccountLinks } from '../features/identity/PublicAccountLinks';

const HomePage = lazy(() => import('../features/home/HomePage'));
const DesignSystemPage = lazy(() => import('../features/design-system/DesignSystemPage'));
const NotFoundPage = lazy(() => import('../features/system/NotFoundPage'));
const AuthPage = lazy(() => import('../features/identity/AuthPage'));
const AccountLayout = lazy(() => import('../features/identity/AccountLayout'));
const AccountPage = lazy(() => import('../features/identity/AccountPage'));
const OperationsPage = lazy(() => import('../features/booking/OperationsPage'));
const OperationsDashboard = lazy(() => import('../features/booking/OperationsDashboard'));
const RosterPage = lazy(() => import('../features/booking/RosterPage'));
const CapacityPage = lazy(() => import('../features/booking/CapacityPage'));
const AttendancePage = lazy(() => import('../features/booking/AttendancePage'));
const ManagementPage = lazy(() => import('../features/booking/ManagementPage'));
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
  const emailUrl = localEmailUrl();
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {import.meta.env.VITE_DEMO_MODE === 'true' && (
          <aside className="demo-notice" aria-label="Ambiente de demonstração">
            Demonstração de portfólio · Dados fictícios. Os agendamentos não representam
            atendimentos reais.{' '}
            {emailUrl && (
              <a href={emailUrl} target="_blank" rel="noopener noreferrer">
                E-mails de teste
              </a>
            )}
          </aside>
        )}
        <Suspense
          fallback={
            <div className="container loading-page">
              <Skeleton label="Carregando página" />
            </div>
          }
        >
          <Routes>
            <Route element={<PublicLayout accountLinks={<PublicAccountLinks />} />}>
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
              <Route path="operacao/agenda" element={<OperationsPage />} />
              <Route path="operacao/configuracoes" element={<CalendarPage />} />
              <Route path="operacao/atendimentos/:appointmentId" element={<AttendancePage />} />
              <Route path="operacao/clientes/:customerId/agendar" element={<BookingPage />} />
              <Route path="operacao/clientes" element={<CustomersPage />} />
              <Route path="operacao/clientes/:customerId" element={<CustomersPage />} />
              <Route path="operacao/clientes/:customerId/pets" element={<PetsPage />} />
              <Route path="operacao/servicos" element={<CatalogPage staff />} />
              <Route path="app/conta" element={<AccountPage />} />
              <Route path="operacao" element={<OperationsDashboard />} />
              <Route path="operacao/escala" element={<RosterPage />} />
              <Route path="operacao/capacidade" element={<CapacityPage />} />
              <Route path="gestao" element={<ManagementPage />} />
              <Route path="gestao/auditoria" element={<ManagementPage audit />} />
              <Route path="gestao/acessos" element={<AccessPage />} />
            </Route>
          </Routes>
        </Suspense>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
