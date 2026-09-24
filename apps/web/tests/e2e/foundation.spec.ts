import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('real API connection, navigation, validation, accessibility and responsive layout', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto('/');
  await expect(page.getByRole('heading', { level: 1 })).toContainText('Mais cuidado.');
  await expect(page.getByText('Ambiente conectado')).toBeVisible();
  const health = await page.request.get('/api/v1/health/ready');
  expect(health.status()).toBe(200);
  expect(await health.json()).toEqual({ status: 'ready' });
  expect((await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze()).violations).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.getByRole('link', { name: 'Explorar componentes' }).click();
  await expect(page).toHaveURL(/design-system$/);
  const input = page.getByLabel('Nome de exemplo');
  await page.getByRole('button', { name: 'Validar exemplo' }).click();
  await expect(input).toBeFocused();
  await expect(input).toHaveAttribute('aria-invalid', 'true');
  await input.fill('Luna de demonstração');
  await page.getByRole('button', { name: 'Validar exemplo' }).click();
  await expect(page.getByText('Nenhum dado foi salvo.')).toBeVisible();
  expect((await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze()).violations).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.reload();
  await expect(page.getByRole('heading', { level: 1 })).toContainText('Cuidar também');
  await page.goto('/endereco-inexistente');
  await page.getByRole('link', { name: 'Voltar ao início' }).click();
  await expect(page.getByText('Ambiente conectado')).toBeVisible();
  expect(errors).toEqual([]);
});

test('API failure is visible and a retry calls the real backend', async ({ page }) => {
  await page.route('**/api/v1/health/ready', (route) => route.abort());
  await page.goto('/');
  await expect(page.getByText('Conexão indisponível no momento')).toBeVisible();
  await expect(page.getByText('Ambiente conectado')).toHaveCount(0);
  await page.unroute('**/api/v1/health/ready');
  await page.getByRole('button', { name: 'Tentar novamente' }).click();
  await expect(page.getByText('Ambiente conectado')).toBeVisible();
});

test('keyboard skip link and 320px reflow', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 800 });
  await page.goto('/');
  await page.getByRole('link', { name: 'Pular para o conteúdo' }).focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('#main')).toBeFocused();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.goto('/design-system');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});
