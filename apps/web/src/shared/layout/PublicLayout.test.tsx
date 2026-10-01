import { lazy, type ComponentType } from 'react';
import { expect, it, vi } from 'vitest';
import { act, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import { PublicLayout } from './PublicLayout';

it('keeps navigation available and announces loading before a delayed page arrives', async () => {
  vi.spyOn(window, 'scrollTo').mockImplementation(() => {});
  let reveal!: (value: { default: ComponentType }) => void;
  const Login = lazy(
    () =>
      new Promise<{ default: ComponentType }>((resolve) => {
        reveal = resolve;
      }),
  );
  render(
    <MemoryRouter>
      <Routes>
        <Route element={<PublicLayout />}>
          <Route index element={<h1>Início</h1>} />
          <Route path="entrar" element={<Login />} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
  await userEvent.click(screen.getByRole('link', { name: 'Entrar' }));
  expect(await screen.findByText('Carregando página')).toBeInTheDocument();
  expect(screen.getByRole('navigation', { name: 'Navegação principal' })).toBeVisible();
  expect(screen.getByRole('main')).toHaveFocus();
  expect(screen.queryByRole('heading', { name: 'Início' })).not.toBeInTheDocument();
  await act(async () => reveal({ default: () => <h1>Entrar na sua conta</h1> }));
  await waitFor(() => expect(screen.getByRole('heading')).toHaveFocus());
  expect(document.title).toBe('Entrar na sua conta · PetLand');
});
