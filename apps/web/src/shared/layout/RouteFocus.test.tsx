import { StrictMode } from 'react';
import { expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Link } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import { RouteFocus } from './RouteFocus';

function Page({ ready = false }: { ready?: boolean }) {
  return (
    <StrictMode>
      <MemoryRouter>
        <main id="main" tabIndex={-1}>
          <RouteFocus />
          {ready ? <h1>Minhas reservas</h1> : <p role="status">Carregando</p>}
          <input aria-label="Buscar" />
          <Link to="?status=COMPLETED">Filtrar</Link>
        </main>
      </MemoryRouter>
    </StrictMode>
  );
}

it('announces delayed content and keeps filter changes from resetting focus', async () => {
  vi.spyOn(window, 'scrollTo').mockImplementation(() => {});
  const view = render(<Page />);
  expect(screen.getByRole('main')).toHaveFocus();
  view.rerender(<Page ready />);
  await waitFor(() => expect(screen.getByRole('heading')).toHaveFocus());
  expect(document.title).toBe('Minhas reservas · PetLand');
  await userEvent.click(screen.getByRole('link', { name: 'Filtrar' }));
  expect(screen.getByRole('link')).toHaveFocus();
});

it('updates the delayed title without stealing focus from a person typing', async () => {
  vi.spyOn(window, 'scrollTo').mockImplementation(() => {});
  const view = render(<Page />);
  await userEvent.type(screen.getByRole('textbox'), 'Luna');
  view.rerender(<Page ready />);
  await waitFor(() => expect(document.title).toBe('Minhas reservas · PetLand'));
  expect(screen.getByRole('textbox')).toHaveFocus();
  expect(screen.getByRole('textbox')).toHaveValue('Luna');
});
