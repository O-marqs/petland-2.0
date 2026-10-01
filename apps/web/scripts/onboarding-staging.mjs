// A new synthetic customer uses the real local staging UI and SMTP inbox.
// Existing accounts, services and calendar are preserved; only the new test booking is cancelled.
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { randomUUID, randomBytes } from 'node:crypto';
import { chromium, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const root = fileURLToPath(new URL('../../../', import.meta.url));
const local = resolve(root, '.local/staging');
const output = resolve(local, 'browser/onboarding');
const origin = 'https://localhost:8443';
const mailbox = 'http://localhost:8026';
const database = (await readFile(resolve(local, 'active-db.txt'), 'utf8')).trim();
if (!/^petland_demo$|^petland_(?:reset|recovery)_[a-f0-9]{32}_demo$/.test(database))
  throw new Error('Only an isolated synthetic demo database is allowed');
const accounts = JSON.parse(await readFile(resolve(local, 'accounts.json'), 'utf8'));
const email = `onboarding-${randomUUID()}@example.com`;
const password = randomBytes(24).toString('hex');
await mkdir(output, { recursive: true });
const browser = await chromium.launch();
const context = await browser.newContext({
  baseURL: origin,
  ignoreHTTPSErrors: true,
  viewport: { width: 1280, height: 900 },
});
const page = await context.newPage();
const errors = [];
page.on('pageerror', (error) => errors.push(error.name));
const checks = [];

async function checkpoint(name) {
  await page.waitForLoadState('networkidle');
  const violations = (
    await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze()
  ).violations.map((v) => v.id);
  expect(violations).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: resolve(output, name + '.png') });
  checks.push({ name, axe_violations: violations, reflow: true });
  console.log('New-account step verified: ' + name);
}
async function mail(subject) {
  let id;
  await expect
    .poll(
      async () => {
        const messages = await (
          await context.request.get(mailbox + '/api/v1/search', {
            params: { query: 'to:' + email },
          })
        ).json();
        id = messages.messages?.find((m) => m.Subject.includes(subject))?.ID;
        return !!id;
      },
      { timeout: 20000 },
    )
    .toBe(true);
  return (await context.request.get(mailbox + '/api/v1/message/' + id)).json();
}
async function signIn(target, identity) {
  await target.goto('/entrar');
  await target.getByLabel('E-mail (obrigatório)', { exact: true }).fill(identity.email);
  await target.getByLabel('Senha (obrigatório)', { exact: true }).fill(identity.password);
  await target.getByRole('button', { name: 'Entrar', exact: true }).click();
  await target.getByRole('button', { name: 'Sair', exact: true }).waitFor();
}
async function availableDay(target, firstDay = 1) {
  for (let offset = firstDay; offset <= 14; offset++) {
    const date = new Date(Date.now() + offset * 86400000).toISOString().slice(0, 10);
    const response = target.waitForResponse(
      (r) => r.url().includes('/availability?') && r.request().method() === 'GET',
    );
    await target.getByLabel('Dia do cuidado (obrigatório)').fill(date);
    const available = await response;
    expect(available.status()).toBe(200);
    const slot = target.getByRole('button', { name: /^\d{2}:\d{2}$/, exact: true }).first();
    if ((await available.json()).slots.length) {
      await slot.click();
      return date;
    }
  }
  throw new Error('Demo has no availability in the next 14 days; calendar was preserved');
}
let appointmentId;
try {
  await page.goto('/criar-conta');
  await page.getByLabel('Seu nome (obrigatório)').fill('Pessoa sintética de jornada');
  await page.getByLabel('E-mail (obrigatório)', { exact: true }).fill(email);
  await page.getByLabel('Senha (obrigatório)', { exact: true }).fill(password);
  await page.getByLabel('Confirmar senha (obrigatório)').fill(password);
  await page.getByRole('button', { name: 'Criar minha conta' }).click();
  await expect(
    page.getByRole('heading', { name: 'Confira seu e-mail para continuar.' }),
  ).toBeFocused();
  await expect(page.getByRole('link', { name: 'Abrir e-mails de teste' })).toHaveAttribute(
    'href',
    mailbox,
  );
  await checkpoint('registration');
  const message = await mail('Confirme');
  const link = message.Text.match(/https:\/\/localhost:8443\/verificar-email#token=[^\s]+/)?.[0];
  if (!link) throw new Error('Expected local confirmation link missing');
  await signIn(page, { email, password });
  await expect(page).toHaveURL(origin + '/app/conta');
  expect((await page.request.get('/api/v1/me/pets')).status()).toBe(403);
  await page.getByRole('button', { name: 'Já confirmei meu e-mail' }).click();
  await expect(page.getByText('A confirmação ainda está pendente')).toBeVisible();
  await page.setViewportSize({ width: 320, height: 800 });
  await checkpoint('pending-mobile');
  const confirmation = await context.newPage();
  await confirmation.goto(link);
  await confirmation.getByRole('button', { name: 'Confirmar e-mail' }).click();
  await expect(confirmation.getByRole('link', { name: 'Continuar para minha área' })).toBeVisible();
  await confirmation.close();
  await page.getByRole('button', { name: 'Já confirmei meu e-mail' }).click();
  await expect(page).toHaveURL(origin + '/app');
  await checkpoint('dashboard-mobile');
  await page.goto('/app/agendar');
  await expect(
    page.getByRole('heading', { name: 'Complete seu cadastro para agendar' }),
  ).toBeVisible();
  await checkpoint('contact-required');
  await page.getByRole('link', { name: 'Completar meu cadastro', exact: true }).click();
  await page.getByRole('button', { name: 'Salvar cadastro' }).click();
  await page.getByRole('link', { name: 'Ver pets', exact: true }).click();
  await page.getByRole('button', { name: 'Adicionar pet' }).click();
  await page.getByLabel('Nome do pet (obrigatório)').fill('Pet sintético de jornada');
  await page.getByLabel('Espécie (obrigatório)').selectOption('DOG');
  await page.getByLabel('Porte (obrigatório)').selectOption('SMALL');
  await page.getByRole('button', { name: 'Salvar pet', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Pet sintético de jornada', exact: true }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole('heading', { name: 'Pet sintético de jornada', exact: true }),
  ).toBeVisible();
  await checkpoint('persisted-pet-mobile');
  await page.goto('/servicos');
  await page.getByRole('link', { name: 'Minha área', exact: true }).click();
  await expect(page).toHaveURL(origin + '/app');
  const pets = await (await page.request.get('/api/v1/me/pets')).json();
  expect(pets.total).toBe(1);
  await page.goto('/app/agendar');
  await page.getByLabel('Pet (obrigatório)', { exact: true }).selectOption(pets.items[0].id);
  const services = page.getByLabel('Serviço (obrigatório)', { exact: true });
  await expect(services.locator('option')).not.toHaveCount(1);
  const serviceId = await services.locator('option').nth(1).getAttribute('value');
  await services.selectOption(serviceId);
  await availableDay(page);
  await expect(page.getByRole('heading', { name: 'Confira antes de confirmar' })).toBeVisible();
  expect((await (await page.request.get('/api/v1/me/appointments')).json()).total).toBe(0);
  await checkpoint('booking-review-mobile');
  const reserved = page.waitForResponse(
    (r) => r.url().endsWith('/api/v1/me/appointments') && r.request().method() === 'POST',
  );
  await page.getByRole('button', { name: 'Sim, confirmar reserva' }).click();
  const response = await reserved;
  expect(response.status()).toBe(201);
  appointmentId = (await response.json()).id;
  await writeFile(
    resolve(output, 'attempt.json'),
    JSON.stringify({ appointment_id: appointmentId, synthetic: true }),
  );
  await expect(
    page.getByRole('heading', { name: 'Reserva confirmada', exact: true }),
  ).toBeVisible();
  await checkpoint('confirmed-mobile');
  await mail('Reserva confirmada');
  await page.getByRole('button', { name: 'Ver minha reserva' }).click();
  await page.reload();
  const persisted = (
    await (await page.request.get('/api/v1/me/appointments/' + appointmentId)).json()
  ).appointment;
  expect(persisted.status).toBe('BOOKED');
  const staffContext = await browser.newContext({ baseURL: origin, ignoreHTTPSErrors: true });
  try {
    const staff = await staffContext.newPage();
    await signIn(staff, accounts.employee);
    await staff.goto('/operacao/reservas/' + appointmentId);
    await expect(
      staff.getByRole('heading', { name: 'Pet sintético de jornada', exact: true }),
    ).toBeVisible();
    await staff.getByRole('button', { name: 'Reagendar', exact: true }).click();
    await staff
      .getByLabel('Motivo do reagendamento (obrigatório)')
      .fill('Reagendamento sintético para verificar a comunicação');
    await availableDay(staff, 8);
    await staff.getByRole('button', { name: 'Confirmar novo horário', exact: true }).click();
    await expect(
      staff.getByRole('heading', { name: 'Novo horário confirmado', exact: true }),
    ).toBeVisible();
    await mail('Reserva reagendada');
    expect(
      (await (await page.request.get('/api/v1/me/appointments/' + appointmentId)).json())
        .appointment.starts_at,
    ).not.toBe(persisted.starts_at);
    await page.reload();
    await checkpoint('customer-after-reschedule');
    await staff.goto('/operacao/reservas/' + appointmentId);
    await staff.getByRole('button', { name: 'Cancelar reserva', exact: true }).click();
    await staff
      .getByLabel('Motivo do cancelamento (obrigatório)')
      .fill('Encerramento da reserva sintética de verificação');
    await staff.getByRole('button', { name: 'Sim, cancelar reserva', exact: true }).click();
    await mail('Reserva cancelada');
  } finally {
    await staffContext.close();
  }
  await page.reload();
  expect(
    (await (await page.request.get('/api/v1/me/appointments/' + appointmentId)).json()).appointment
      .status,
  ).toBe('CANCELLED');
  await checkpoint('cancelled-mobile');
  expect(errors).toEqual([]);
  const cookies = await context.cookies(origin);
  expect(cookies.every((cookie) => cookie.secure && cookie.httpOnly)).toBe(true);
  await writeFile(
    resolve(output, 'report.json'),
    JSON.stringify(
      {
        passed: true,
        synthetic: true,
        external_email_delivery: false,
        appointment_id: appointmentId,
        checks,
        errors,
      },
      null,
      2,
    ),
  );
  console.log(
    'New customer, verified email, contact, pet, booking, staff reschedule/cancel and four SMTP messages verified.',
  );
} catch (error) {
  await writeFile(
    resolve(output, 'report.json'),
    JSON.stringify(
      { passed: false, synthetic: true, appointment_id: appointmentId, checks, errors },
      null,
      2,
    ),
  );
  throw error;
} finally {
  await browser.close();
}
