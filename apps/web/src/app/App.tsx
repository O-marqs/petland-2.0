import { lazy, Suspense } from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PublicLayout } from '../shared/layout/PublicLayout';
import { Skeleton } from '../shared/ui/Feedback';

const HomePage = lazy(() => import('../features/home/HomePage'));
const DesignSystemPage = lazy(() => import('../features/design-system/DesignSystemPage'));
const NotFoundPage = lazy(() => import('../features/system/NotFoundPage'));
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
              <Route path="*" element={<NotFoundPage />} />
            </Route>
          </Routes>
        </Suspense>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
