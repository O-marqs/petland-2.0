// Current documentation snapshots. Writes only to the separate petlanddocs fixture.
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash, randomUUID } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { chromium, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const root = fileURLToPath(new URL('../../../', import.meta.url));
const local = resolve(root, '.local/docs-capture');
const output = resolve(local, 'screenshots');
const origin = 'https://localhost:8444';
const fixture = JSON.parse(await readFile(resolve(local, 'fixture.json'), 'utf8'));
const accounts = JSON.parse(await readFile(resolve(root, '.local/staging/accounts.json'), 'utf8'));
const image = execFileSync(
  'docker',
  ['inspect', '--format', '{{.Config.Image}}', 'petlanddocs-api-1'],
  { encoding: 'utf8' },
).trim();
const webImage = execFileSync(
  'docker',
  ['inspect', '--format', '{{.Config.Image}}', 'petlanddocs-web-1'],
  { encoding: 'utf8' },
).trim();
if (
  fixture.fixture !== 'petland-p07-synthetic-v1' ||
  image !== 'petland-stage-api:25495230b75e' ||
  webImage !== 'petland-stage-web:25495230b75e'
)
  throw new Error('Only the separate owned documentation fixture and reference image are allowed');
await mkdir(output, { recursive: true });
const browser = await chromium.launch();
const contexts = [];
const checks = [];
const errors = [];
async function pageFor(profile) {
  const context = await browser.newContext({
    baseURL: origin,
    ignoreHTTPSErrors: true,
    viewport: { width: 1440, height: 1000 },
  });
  contexts.push(context);
  const page = await context.newPage();
  page.on('pageerror', (error) => errors.push(error.name));
  if (profile) {
    await page.goto('/entrar');
    await page.getByLabel('E-mail (obrigatório)', { exact: true }).fill(accounts[profile].email);
    await page.getByLabel('Senha (obrigatório)', { exact: true }).fill(accounts[profile].password);
    await page.getByRole('button', { name: 'Entrar', exact: true }).click();
    await page.getByRole('button', { name: 'Sair', exact: true }).waitFor();
  }
  return page;
}
async function get(page, path) {
  const response = await page.request.get('/api/v1' + path);
  expect(response.ok()).toBe(true);
  return response.json();
}
async function mutate(page, method, path, data) {
  const csrf = await get(page, '/auth/csrf');
  const response = await page.request.fetch('/api/v1' + path, {
    method,
    data,
    headers: { Origin: origin, 'X-CSRF-Token': csrf.csrf_token, 'Idempotency-Key': randomUUID() },
  });
  if (!response.ok())
    throw new Error('Synthetic preparation failed: ' + response.status() + ' at ' + path);
  return response.json();
}
async function shot(page, name, capture = true) {
  await page.waitForLoadState('networkidle');
  await page.evaluate(() => document.fonts.ready);
  const violations = (
    await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze()
  ).violations.map((v) => v.id);
  expect(violations).toEqual([]);
  expect(errors).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  const checkpoint = {
    name,
    route: new URL(page.url()).pathname + new URL(page.url()).search,
    viewport: page.viewportSize(),
    violations,
    reflow: true,
    title: await page.title(),
  };
  if (capture) {
    const file = name + '-current.png';
    await page.screenshot({ path: resolve(output, file), fullPage: name !== 'home' });
    checkpoint.png = file;
    checkpoint.sha256 = createHash('sha256')
      .update(await readFile(resolve(output, file)))
      .digest('hex');
  }
  checks.push(checkpoint);
  console.log('Documentation checkpoint passed: ' + name);
}
try {
  const publicPage = await pageFor();
  await publicPage.goto('/');
  await shot(publicPage, 'home');
  const customer = await pageFor('customer_a');
  await customer.goto('/app');
  await shot(customer, 'tutor');
  const staff = await pageFor('employee');
  const admin = await pageFor('admin');
  const users = await get(admin, '/management/users?limit=50');
  expect(users.items.length).toBe(4);
  expect(users.has_more).toBe(false);
  expect(
    users.items.every((u) => u.email.startsWith('demo-') && u.email.endsWith('@example.com')),
  ).toBe(true);
  const reference = fixture.reference_date;
  const nextDay = new Date(reference + 'T12:00:00Z');
  nextDay.setUTCDate(nextDay.getUTCDate() + 1);
  const day = nextDay.toISOString().slice(0, 10);
  const emptyDay = new Date(reference + 'T12:00:00Z');
  emptyDay.setUTCDate(emptyDay.getUTCDate() + 3);
  const rosterDay = emptyDay.toISOString().slice(0, 10);
  const calendar = await get(staff, '/operations/calendar');
  const roster = await get(staff, '/operations/roster/' + rosterDay);
  await mutate(staff, 'PUT', '/operations/roster/' + rosterDay, {
    version: roster.version,
    reason: 'Equipe reduzida somente nesta data — demonstração documental fictícia',
    shifts: [
      {
        resource_id: calendar.resources[0].id,
        windows: [
          { start: 540, end: 720 },
          { start: 780, end: 1020 },
        ],
      },
    ],
  });
  const capacity = await get(staff, '/operations/capacity');
  await mutate(staff, 'PUT', '/operations/capacity', {
    version: capacity.version,
    pools: [
      {
        id: randomUUID(),
        name: 'Estações de banho demo',
        capacity: 2,
        service_ids: [fixture.services.bath, fixture.services.groom],
        active: true,
      },
    ],
  });
  const pet = await get(customer, '/me/pets/' + fixture.pets['Luna demo']);
  const id = pet.id;
  const petBody = Object.fromEntries(
    [
      'name',
      'species_id',
      'breed_id',
      'size',
      'sex',
      'birth_date',
      'birth_estimated',
      'care_notes',
      'version',
    ].map((key) => [key, pet[key]]),
  );
  await mutate(customer, 'PUT', '/me/pets/' + id, {
    ...petBody,
    allergies: 'Alerta fictício: usar shampoo hipoalergênico.',
    handling_notes: 'Manejo fictício: sensível ao secador; aproximar com calma.',
  });
  await customer.goto('/app/agendar');
  await customer
    .getByLabel('Pet (obrigatório)', { exact: true })
    .selectOption(fixture.pets['Luna demo']);
  await customer
    .getByLabel('Serviço (obrigatório)', { exact: true })
    .selectOption(fixture.services.bath);
  await customer.getByLabel('Dia do cuidado (obrigatório)', { exact: true }).fill(rosterDay);
  await customer.locator('.booking-slots button').first().click();
  await customer.getByRole('heading', { name: 'Confira antes de confirmar' }).waitFor();
  await shot(customer, 'booking');
  await customer.setViewportSize({ width: 320, height: 900 });
  await shot(customer, 'booking-mobile', false);
  await customer.setViewportSize({ width: 1440, height: 1000 });
  await staff.goto('/operacao?data=' + day + '&escopo=equipe');
  await shot(staff, 'dashboard');
  await staff.goto('/operacao/escala?data=' + rosterDay);
  await shot(staff, 'roster');
  await staff.goto('/operacao/capacidade');
  await shot(staff, 'capacity');
  await staff.goto('/operacao/atendimentos/' + fixture.appointments.last_slot_a);
  await shot(staff, 'attendance');
  await admin.goto('/gestao');
  await shot(admin, 'management');
  for (const [page, name, path] of [
    [publicPage, 'home-mobile', '/'],
    [customer, 'tutor-mobile', '/app'],
    [staff, 'dashboard-mobile', '/operacao?data=' + day + '&escopo=equipe'],
    [staff, 'roster-mobile', '/operacao/escala?data=' + rosterDay],
    [staff, 'capacity-mobile', '/operacao/capacidade'],
    [staff, 'attendance-mobile', '/operacao/atendimentos/' + fixture.appointments.last_slot_a],
    [admin, 'management-mobile', '/gestao'],
  ]) {
    await page.setViewportSize({ width: 320, height: 900 });
    await page.goto(path);
    await shot(page, name, false);
  }
  await writeFile(
    resolve(local, 'capture-raw.json'),
    JSON.stringify(
      {
        captured_at: new Date().toISOString(),
        functional_reference: '25495230b75e06ef61b52b8751c76ef9b280dfd1',
        schema_revision: '0007_product_operations',
        origin,
        project: 'petlanddocs',
        synthetic: true,
        fixture: fixture.fixture,
        reference_date: reference,
        fake_clock: false,
        image,
        web_image: webImage,
        source_hashes: Object.fromEntries(
          await Promise.all(
            [
              'apps/web/src/features/home/HomePage.tsx',
              'apps/web/src/features/identity/AccountLayout.tsx',
              'apps/web/src/shared/styles/tokens.css',
              'apps/web/src/features/booking/OperationsDashboard.tsx',
              'apps/api/src/petland/shared/database.py',
              'packages/api-contract/openapi.json',
            ].map(async (file) => [
              file,
              createHash('sha256')
                .update(await readFile(resolve(root, file)))
                .digest('hex'),
            ]),
          ),
        ),
        preparation: [
          'Fresh database seeded only with the existing synthetic fixture',
          'One-day roster on reference +3',
          'Capacity pool of two units',
          'Critical care text on synthetic Luna',
          'Booking review only; no new reservation confirmation',
        ],
        checks,
        javascript_errors: errors,
        passed: true,
      },
      null,
      2,
    ) + '\n',
  );
} finally {
  await Promise.all(contexts.map((context) => context.close()));
  await browser.close();
}
