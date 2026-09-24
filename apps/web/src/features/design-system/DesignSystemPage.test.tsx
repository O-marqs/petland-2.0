import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, test } from 'vitest';
import DesignSystemPage from './DesignSystemPage';

test('invalid input focuses field, explains error and preserves the value', async () => {
  const user = userEvent.setup();
  render(<DesignSystemPage />);
  const input = screen.getByLabelText(/Nome de exemplo/);
  await user.click(screen.getByRole('button', { name: 'Validar exemplo' }));
  expect(await screen.findByText('Informe um nome para testar o campo.')).toBeVisible();
  expect(input).toHaveFocus();
  expect(input).toHaveAttribute('aria-invalid', 'true');
  await user.type(input, 'Luna de demonstração');
  await user.click(screen.getByRole('button', { name: 'Validar exemplo' }));
  expect(await screen.findByText('Nenhum dado foi salvo.')).toBeVisible();
  expect(input).toHaveValue('Luna de demonstração');
  await user.click(screen.getByRole('button', { name: 'Limpar exemplo' }));
  expect(input).toHaveValue('');
  expect(screen.queryByText('Nenhum dado foi salvo.')).not.toBeInTheDocument();
});

test('feedback state selector supports keyboard and does not claim a reservation', async () => {
  const user = userEvent.setup();
  render(<DesignSystemPage />);
  const success = screen.getByRole('button', { name: 'Sucesso' });
  success.focus();
  await user.keyboard('{Enter}');
  expect(success).toHaveAttribute('aria-pressed', 'true');
  expect(screen.getByText('Demonstração visual. Nenhuma reserva foi criada.')).toBeVisible();
  expect(screen.getByRole('button', { name: 'Indisponível' })).toBeDisabled();
});
