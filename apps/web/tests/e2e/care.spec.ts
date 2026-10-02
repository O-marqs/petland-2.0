import { expect, test } from '@playwright/test';
import { accessible, registerCustomer, signIn } from './care-helpers';

test('customer profile and pets persist, recover from failure, edit, archive and restore', async ({
  page,
  request,
  baseURL,
}, info) => {
  test.setTimeout(90000);
  expect(['localhost', '127.0.0.1']).toContain(new URL(baseURL!).hostname);
  const email = 'p03-own-' + info.project.name + '-' + Date.now() + '@example.com';
  await registerCustomer(request, email);
  await signIn(page, email);
  await page.getByRole('link', { name: 'Completar meu cadastro' }).click();
  await expect(page.getByRole('heading', { name: 'Meu cadastro', exact: true })).toBeVisible();
  await page.getByLabel('Telefone com DDD').fill('(11) 99999-5678');
  await page.getByLabel('Endereço', { exact: true }).fill('Endereço sintético de teste');
  await page.getByRole('button', { name: 'Salvar cadastro' }).click();
  await expect(page.getByRole('link', { name: 'Ver pets', exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByLabel('Telefone com DDD')).toHaveValue('11999995678');
  await page.getByRole('link', { name: 'Ver pets', exact: true }).click();
  await page.getByRole('button', { name: 'Adicionar pet' }).click();
  await page.getByRole('button', { name: 'Salvar pet', exact: true }).click();
  await expect(page.getByLabel('Nome do pet (obrigatório)')).toBeFocused();
  await page.getByLabel('Nome do pet (obrigatório)').fill('Luna Sintética P03');
  await page.getByLabel('Espécie (obrigatório)').selectOption('DOG');
  await page.getByLabel('Porte (obrigatório)').selectOption('MEDIUM');
  await page.getByLabel('Cuidados importantes').fill('Cuidados sintéticos informados pelo tutor.');
  await accessible(page);
  await page.route('**/api/v1/me/pets', (route) =>
    route.request().method() === 'POST' ? route.abort() : route.continue(),
  );
  await page.getByRole('button', { name: 'Salvar pet', exact: true }).click();
  await expect(page.getByText('Não foi possível salvar', { exact: true })).toBeVisible();
  await expect(page.getByLabel('Nome do pet (obrigatório)')).toHaveValue('Luna Sintética P03');
  await page.unroute('**/api/v1/me/pets');
  await page.getByRole('button', { name: 'Salvar pet', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Luna Sintética P03', exact: true }),
  ).toBeVisible();
  await page.reload();
  await page.getByRole('button', { name: 'Editar Luna Sintética P03' }).click();
  await page.getByLabel('Nome do pet (obrigatório)').fill('Luna Atualizada P03');
  await page.getByRole('button', { name: 'Salvar pet', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Luna Atualizada P03', exact: true }),
  ).toBeVisible();
  await page.getByRole('button', { name: 'Arquivar Luna Atualizada P03' }).click();
  await page.getByRole('button', { name: 'Confirmar arquivamento' }).click();
  await expect(page.getByText('Pet arquivado. Suas informações foram preservadas.')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Luna Atualizada P03', exact: true })).toHaveCount(
    0,
  );
  await page.getByRole('button', { name: 'Arquivados', exact: true }).click();
  await page.getByRole('button', { name: 'Restaurar Luna Atualizada P03' }).click();
  await page.getByRole('button', { name: 'Confirmar restauração' }).click();
  await expect(page.getByText('Pet restaurado.', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Ativos', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Luna Atualizada P03', exact: true }),
  ).toBeVisible();
  await page.setViewportSize({ width: 320, height: 800 });
  await accessible(page);
  await page.goto('/app');
  await expect(
    page.getByRole('heading', { name: 'Luna Atualizada P03', exact: true }),
  ).toBeVisible();
  await accessible(page);
  expect(await page.evaluate(() => [localStorage.length, sessionStorage.length])).toEqual([0, 0]);
});

test('public catalog filters, direct routes and retry at 320px', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 800 });
  await page.goto('/servicos');
  await expect(page.getByRole('heading', { name: 'Um cuidado para cada pet.' })).toBeVisible();
  await page.getByLabel('Espécie', { exact: true }).selectOption('CAT');
  await page.getByLabel('Porte', { exact: true }).selectOption('LARGE');
  await accessible(page);
  await page.route('**/api/v1/catalog/services?**', (route) => route.abort());
  await page.reload();
  await expect(page.getByText('Não foi possível carregar', { exact: true })).toBeVisible();
  await page.unroute('**/api/v1/catalog/services?**');
  await page.getByRole('button', { name: 'Tentar novamente' }).click();
  await expect(page.getByText('Não foi possível carregar', { exact: true })).toHaveCount(0);
  await page.goto('/vincular-cadastro');
  await accessible(page);
});
