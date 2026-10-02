import { expect, type APIRequestContext, type Browser, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { staffScheduling } from './booking-helpers';
import { staffAttendance } from './attendance-helpers';

export const syntheticPassword = 'Passeio sintético no parque 2026!';
const mailbox = process.env.MAILPIT_URL ?? 'http://127.0.0.1:8025';

export async function mailLink(request: APIRequestContext, email: string, subject: string) {
  expect(['localhost', '127.0.0.1']).toContain(new URL(mailbox).hostname);
  let id = '';
  await expect
    .poll(
      async () => {
        const data = await (
          await request.get(mailbox + '/api/v1/search', { params: { query: 'to:' + email } })
        ).json();
        id =
          data.messages?.find((m: { Subject: string; ID: string }) => m.Subject.includes(subject))
            ?.ID || '';
        return id;
      },
      { timeout: 15000 },
    )
    .not.toBe('');
  const message = await (await request.get(mailbox + '/api/v1/message/' + id)).json();
  const url = new URL(message.Text.match(/http:\/\/localhost:5173\/[^\s]+/)[0]);
  return url.pathname + url.hash;
}

export async function registerCustomer(request: APIRequestContext, email: string) {
  const csrf = await (await request.get('/api/v1/auth/csrf')).json();
  const headers = { Origin: 'http://localhost:5173', 'X-CSRF-Token': csrf.csrf_token };
  expect(
    (
      await request.post('/api/v1/auth/register', {
        headers,
        data: {
          email,
          display_name: 'Cliente Sintético P03',
          password: syntheticPassword,
        },
      })
    ).status(),
  ).toBe(202);
  const link = await mailLink(request, email, 'Confirme');
  const token = new URLSearchParams(link.split('#')[1]).get('token');
  expect(
    (await request.post('/api/v1/auth/email-verifications', { headers, data: { token } })).status(),
  ).toBe(200);
}

export async function signIn(page: Page, email: string) {
  await page.goto('/entrar');
  await page.getByLabel('E-mail (obrigatório)', { exact: true }).fill(email);
  await page.getByLabel('Senha (obrigatório)', { exact: true }).fill(syntheticPassword);
  await page.getByRole('button', { name: 'Entrar', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Sair', exact: true })).toBeVisible();
}

export async function accessible(page: Page) {
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'])
        .analyze()
    ).violations,
  ).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  );
}

export async function staffCare(staff: Page, request: APIRequestContext, browser: Browser) {
  const email = 'p03-assistido-' + Date.now() + '@example.com';
  await registerCustomer(request, email);
  await staff.goto('/operacao/clientes/novo');
  await expect(staff.getByRole('heading', { name: 'Novo cliente', exact: true })).toBeVisible();
  await staff.getByLabel('Nome completo (obrigatório)').fill('Cliente Assistido Sintético P03');
  await staff.getByLabel('E-mail (obrigatório)', { exact: true }).fill(email);
  await staff.getByLabel('Telefone com DDD').fill('11999991234');
  await staff.getByRole('button', { name: 'Salvar cadastro', exact: true }).click();
  await expect(staff.getByRole('button', { name: 'Enviar link de vínculo' })).toBeVisible();
  const customerUrl = new URL(staff.url()).pathname;
  await staff.getByRole('link', { name: 'Ver pets', exact: true }).click();
  await staff.getByRole('button', { name: 'Adicionar pet' }).click();
  await staff.getByLabel('Nome do pet (obrigatório)').fill('Nino Assistido Sintético');
  await staff.getByLabel('Espécie (obrigatório)').selectOption('CAT');
  await staff.getByRole('button', { name: 'Salvar pet', exact: true }).click();
  await expect(
    staff.getByRole('heading', { name: 'Nino Assistido Sintético', exact: true }),
  ).toBeVisible();
  await staff.goto(customerUrl);
  await staff.getByRole('button', { name: 'Enviar link de vínculo' }).click();
  await expect(staff.getByText('Link solicitado', { exact: true })).toBeVisible();
  const link = await mailLink(request, email, 'Vincule');
  const customerContext = await browser.newContext({
    baseURL: 'http://127.0.0.1:5173',
    viewport: { width: 390, height: 844 },
  });
  try {
    const customer = await customerContext.newPage();
    await signIn(customer, email);
    await customer.goto(link);
    await expect(customer).toHaveURL(/vincular-cadastro$/);
    await customer.getByRole('button', { name: 'Confirmar vínculo do cadastro' }).click();
    await expect(customer.getByText('Cadastro vinculado', { exact: true })).toBeVisible();
    await customer.getByRole('link', { name: 'Ver meus pets' }).click();
    await expect(
      customer.getByRole('heading', { name: 'Nino Assistido Sintético', exact: true }),
    ).toBeVisible();
    await accessible(customer);
    await customer.reload();
    await expect(
      customer.getByRole('heading', { name: 'Nino Assistido Sintético', exact: true }),
    ).toBeVisible();
  } finally {
    await customerContext.close();
  }
  await staff.goto('/operacao/servicos');
  await staff.getByRole('button', { name: 'Novo serviço' }).click();
  const name = 'Banho sintético P03 ' + Date.now();
  await staff.getByLabel('Nome do serviço (obrigatório)').fill(name);
  await staff
    .getByLabel('Descrição', { exact: true })
    .fill('Oferta sintética criada pelo teste automatizado.');
  await staff.getByLabel('Cachorro', { exact: true }).check();
  for (const [size, price, duration] of [
    ['Pequeno', '80,25', '40'],
    ['Médio', '100,50', '60'],
    ['Grande', '120,75', '90'],
  ]) {
    await staff.getByLabel('Oferecer porte ' + size.toLowerCase()).check();
    await staff.getByLabel('Preço — ' + size + ' (R$) (obrigatório)', { exact: true }).fill(price);
    await staff
      .getByLabel('Duração — ' + size + ' (minutos) (obrigatório)', { exact: true })
      .fill(duration);
  }
  await staff.getByLabel('Serviço ativo no catálogo público').check();
  await accessible(staff);
  const saving = staff.waitForResponse(
    (r) => r.url().endsWith('/api/v1/operations/services') && r.request().method() === 'POST',
  );
  await staff.getByRole('button', { name: 'Salvar serviço', exact: true }).click();
  const response = await saving;
  expect(response.status()).toBe(201);
  const service = await response.json();
  await expect(staff.getByText('Serviço salvo', { exact: true })).toBeVisible();
  await staff.goto('/servicos/' + service.id);
  await expect(staff.getByRole('heading', { name, exact: true })).toBeVisible();
  await expect(staff.getByText('R$ 80,25', { exact: true })).toBeVisible();
  await expect(staff.getByText('90 min', { exact: true })).toBeVisible();
  await accessible(staff);
  await staffScheduling(staff, request, browser, service, customerUrl.split('/').at(-1)!, email);
  await staffAttendance(staff, browser, customerUrl.split('/').at(-1)!, email);
  await staff.goto('/operacao/servicos');
  await staff.getByRole('button', { name: 'Editar ' + name, exact: true }).click();
  await staff.getByLabel('Serviço ativo no catálogo público').uncheck();
  await staff.getByRole('button', { name: 'Salvar serviço', exact: true }).click();
  await expect(staff.getByText('Serviço salvo', { exact: true })).toBeVisible();
  expect((await staff.request.get('/api/v1/catalog/services/' + service.id)).status()).toBe(404);
}
