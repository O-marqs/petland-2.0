// Exercise new operational workflows against the owned local synthetic demo.
// Preserve existing identities/appointments; restore temporary scheduling rules in finally.
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { randomUUID } from 'node:crypto';
import { chromium, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const root = fileURLToPath(new URL('../../../', import.meta.url));
const local = resolve(root, '.local/staging');
const output = resolve(local, 'browser/operations-evolution');
const origin = 'https://localhost:8443';
const database = (await readFile(resolve(local, 'active-db.txt'), 'utf8')).trim();
if (!/^petland_demo$|^petland_(?:reset|recovery)_[a-f0-9]{32}_demo$/.test(database)) throw new Error('Owned local synthetic demo required');
const accounts = JSON.parse(await readFile(resolve(local, 'accounts.json'), 'utf8'));
await mkdir(output, { recursive: true });
const browser = await chromium.launch();
const contexts = [];
const checks = [], errors = [];
async function pageFor(profile) {
  const context = await browser.newContext({ baseURL: origin, ignoreHTTPSErrors: true, viewport: { width: 1440, height: 1000 } });
  contexts.push(context);
  const page = await context.newPage();
  page.on('pageerror', e => errors.push(e.name));
  await page.goto('/entrar');
  await page.getByLabel('E-mail (obrigatório)', { exact: true }).fill(accounts[profile].email);
  await page.getByLabel('Senha (obrigatório)', { exact: true }).fill(accounts[profile].password);
  await page.getByRole('button', { name: 'Entrar', exact: true }).click();
  await page.getByRole('button', { name: 'Sair', exact: true }).waitFor();
  return page;
}
async function get(page, path) {
  const r = await page.request.get('/api/v1' + path); expect(r.ok()).toBe(true); return r.json();
}
async function write(page, method, path, body) {
  const csrf = await get(page, '/auth/csrf');
  const r = await page.request.fetch('/api/v1' + path, { method, data: body,
    headers: { Origin: origin, 'X-CSRF-Token': csrf.csrf_token, 'Idempotency-Key': randomUUID() } });
  if (!r.ok()) {
    const failure = await r.json();
    throw new Error(`Operational request failed (${r.status()}/${failure.code || 'unknown'}) at ${path}`);
  }
  return r.json();
}
async function check(page, name) {
  await page.waitForLoadState('networkidle');
  const violations = (await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze()).violations.map(v => ({ id: v.id, nodes: v.nodes.map(n => n.target) }));
  expect(violations).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  expect(errors).toEqual([]);
  await page.screenshot({ path: resolve(output, name + '.png'), fullPage: true });
  checks.push({ name, violations, reflow: true }); console.log('Operational flow verified: ' + name);
}
async function mail(page, appointmentId, subject) {
  let found;
  await expect.poll(async () => {
    const list = await (await page.request.get('http://localhost:8026/api/v1/search', { params: { query: 'to:' + accounts.customer_a.email } })).json();
    for (const row of list.messages || []) {
      if (!row.Subject.includes(subject)) continue;
      const message = await (await page.request.get('http://localhost:8026/api/v1/message/' + row.ID)).json();
      if (message.Text.includes(appointmentId)) { found = message; return true; }
    }
    return false;
  }, { timeout: 20000 }).toBe(true);
  return found;
}
let staff, originalSettings, originalPools, originalRoster, rosterDay, appointment;
let following;
let service;
let rulesChanged = false, rosterChanged = false, poolsChanged = false;
try {
  staff = await pageFor('employee');
  const customer = await pageFor('customer_a');
  const admin = await pageFor('admin');
  originalSettings = await get(staff, '/operations/calendar');
  originalPools = await get(staff, '/operations/capacity');
  service = await write(staff, 'POST', '/operations/services', {
    name: 'Cuidado operacional sintético ' + Date.now(), description: 'Verificação de fluxo; dados fictícios.', active: true,
    species_ids: ['DOG'], options: [{ size: 'SMALL', price: '10.00', duration_minutes: 5 }],
  });
  const staffResources = originalSettings.resources.filter(r => r.active).slice(0, 2);
  expect(staffResources.length).toBe(2);
  rulesChanged = true;
  for (const r of staffResources) {
    const { id, ...body } = r;
    await write(staff, 'PUT', '/operations/resources/' + id, { ...body, service_ids: [...r.service_ids, service.id] });
  }
  rosterDay = new Date(Date.now() + 20 * 86400000).toISOString().slice(0, 10);
  originalRoster = await get(staff, '/operations/roster/' + rosterDay);
  await staff.goto('/operacao/escala?data=' + rosterDay);
  await staff.getByLabel('Motivo da escala (obrigatório)').fill('Equipe reduzida somente nesta data — teste sintético');
  const person = staff.locator('.roster-person').filter({ has: staff.getByText(staffResources[0].name, { exact: true }) });
  await person.getByRole('checkbox', { name: /Trabalha nesta data/ }).uncheck();
  await staff.getByRole('button', { name: 'Conferir impactos da escala', exact: true }).click();
  await expect(staff.getByText('Sem reservas incompatíveis nesta prévia', { exact: true })).toBeVisible();
  rosterChanged = true;
  await staff.getByRole('button', { name: 'Confirmar escala desta data', exact: true }).click();
  await expect(staff.getByText('Escala da data atualizada', { exact: true })).toBeVisible();
  const savedRoster = await get(staff, '/operations/roster/' + rosterDay);
  expect(savedRoster.rows.find(r => r.resource_id === staffResources[0].id).windows).toEqual([]);
  await check(staff, 'roster-desktop');
  await staff.setViewportSize({ width: 320, height: 900 }); await check(staff, 'roster-mobile');
  await staff.setViewportSize({ width: 1440, height: 1000 });
  await staff.goto('/operacao/capacidade');
  await staff.getByRole('button', { name: 'Adicionar recurso compartilhado', exact: true }).click();
  const index = originalPools.pools.length + 1;
  await staff.getByLabel('Nome do recurso ' + index + ' (obrigatório)', { exact: true }).fill('Banheira de teste sintético');
  await staff.getByLabel('Quantidade simultânea ' + index + ' (obrigatório)', { exact: true }).fill('1');
  await staff.getByRole('checkbox', { name: service.name + ' — recurso ' + index, exact: true }).check();
  await staff.getByRole('button', { name: 'Conferir impactos da capacidade', exact: true }).click();
  poolsChanged = true;
  await staff.getByRole('button', { name: 'Confirmar capacidade física', exact: true }).click();
  await expect(staff.getByText('Capacidade atualizada', { exact: true })).toBeVisible();
  await check(staff, 'capacity-desktop');
  await staff.setViewportSize({ width: 320, height: 900 }); await check(staff, 'capacity-mobile');
  await staff.setViewportSize({ width: 1440, height: 1000 });
  await customer.goto('/app/pets');
  await customer.getByRole('button', { name: 'Adicionar pet', exact: true }).click();
  const petName = 'Luna cuidado sintético ' + Date.now();
  await customer.getByLabel('Nome do pet (obrigatório)', { exact: true }).fill(petName);
  await customer.getByLabel('Espécie (obrigatório)', { exact: true }).selectOption('DOG');
  await customer.getByLabel('Porte (obrigatório)', { exact: true }).selectOption('SMALL');
  await customer.getByLabel('Alergias e restrições críticas', { exact: true }).fill('Alergia sintética: usar shampoo hipoalergênico.');
  await customer.getByLabel('Comportamento e preferências de cuidado', { exact: true }).fill('Secador baixo — preferência sintética.');
  await customer.getByRole('button', { name: 'Salvar pet', exact: true }).click();
  await expect(customer.getByRole('heading', { name: petName, exact: true })).toBeVisible();
  const pet = (await get(customer, '/me/pets')).items.find(p => p.name === petName);
  expect(pet.allergies).toContain('hipoalergênico');
  await check(customer, 'pet-critical-care');
  const settings = await get(staff, '/operations/calendar');
  const start = new Date(Math.ceil(Date.now() / 60000) * 60000 + 120000);
  const day = new Intl.DateTimeFormat('en-CA', { timeZone: settings.configuration.timezone }).format(start);
  const hour = new Intl.DateTimeFormat('pt-BR', { timeZone: settings.configuration.timezone, hour: '2-digit', minute: '2-digit' }).format(start);
  await write(staff, 'PUT', '/operations/calendar', { ...settings.configuration, step_minutes: 1, reminder_minutes: 1,
    calendar: { ...settings.configuration.calendar, exceptions: [...settings.configuration.calendar.exceptions.filter(d => d.date !== day), { date: day, windows: [{ start: 0, end: 1440 }] }] } });
  await customer.goto('/app/agendar');
  await customer.getByLabel('Pet (obrigatório)', { exact: true }).selectOption(pet.id);
  await customer.getByLabel('Serviço (obrigatório)', { exact: true }).selectOption(service.id);
  await customer.getByLabel('Dia do cuidado (obrigatório)').fill(day);
  await customer.getByRole('button', { name: hour, exact: true }).click();
  await customer.getByRole('button', { name: 'Sim, confirmar reserva', exact: true }).click();
  await expect(customer.getByRole('heading', { name: 'Reserva confirmada', exact: true })).toBeVisible();
  await customer.getByRole('button', { name: 'Ver minha reserva', exact: true }).click();
  appointment = (await get(customer, '/me/appointments/' + customer.url().split('/').at(-1))).appointment;
  const internal = await get(staff, '/operations/attendances/' + appointment.id);
  const alternate = staffResources.find(r => r.id !== internal.item.resource_id);
  await staff.goto('/operacao/atendimentos/' + appointment.id);
  await expect(staff.getByText('Alergia sintética: usar shampoo hipoalergênico.', { exact: true })).toBeVisible();
  await staff.getByRole('button', { name: 'Transferir responsável', exact: true }).click();
  await staff.getByLabel('Nova pessoa responsável (obrigatório)', { exact: true }).selectOption(alternate.id);
  await staff.getByLabel('Motivo (obrigatório)', { exact: true }).fill('Redistribuição interna sintética');
  await staff.getByRole('button', { name: 'Confirmar ação', exact: true }).click();
  await expect(staff.getByText('Responsável transferido', { exact: true })).toBeVisible();
  const moved = await get(staff, '/operations/attendances/' + appointment.id);
  expect(moved.item.appointment.starts_at).toBe(appointment.starts_at);
  expect(moved.item.resource_id).toBe(alternate.id);
  await check(staff, 'transfer-and-care-context');
  await staff.goto('/operacao?data=' + day + '&escopo=equipe');
  await expect(staff.getByRole('heading', { name: petName, exact: true })).toBeVisible();
  await check(staff, 'dashboard-desktop');
  await staff.setViewportSize({ width: 320, height: 900 }); await check(staff, 'dashboard-mobile');
  await staff.setViewportSize({ width: 1440, height: 1000 });
  await staff.goto('/operacao/atendimentos/' + appointment.id);
  // Wait for actual server time and the actual SMTP reminder; no simulated visit time.
  await expect.poll(async () => Date.now() >= start.getTime() - 60000, { timeout: 200000, intervals: [3000] }).toBe(true);
  await mail(customer, appointment.id, 'Lembrete');
  checks.push({ name: 'scheduled-reminder-smtp', actual_smtp: true }); console.log('Operational flow verified: scheduled-reminder-smtp');
  await staff.getByRole('button', { name: 'Registrar chegada', exact: true }).click();
  await staff.getByRole('button', { name: 'Confirmar ação', exact: true }).click();
  await expect.poll(async () => { await staff.getByRole('button', { name: 'Atualizar atendimento', exact: true }).click(); return staff.getByRole('button', { name: 'Iniciar atendimento', exact: true }).count(); }, { timeout: 130000, intervals: [3000] }).toBe(1);
  await staff.getByRole('button', { name: 'Iniciar atendimento', exact: true }).click();
  await staff.getByLabel('Li as alergias e restrições críticas atuais deste pet antes de iniciar.').check();
  await staff.getByRole('button', { name: 'Confirmar ação', exact: true }).click();
  await expect(staff.getByText('Em atendimento', { exact: true })).toBeVisible();
  await staff.getByRole('button', { name: 'Adicionar anotação', exact: true }).click();
  const secret = 'NOTA_PRIVADA_OPERACAO_SINTETICA';
  await staff.getByLabel('Anotação (obrigatório)', { exact: true }).fill(secret);
  await staff.getByRole('button', { name: 'Salvar anotação', exact: true }).click();
  await expect(staff.getByText(secret, { exact: true })).toBeVisible();
  await staff.getByRole('button', { name: 'Concluir atendimento', exact: true }).click();
  await staff.getByLabel('Resumo para o cliente', { exact: true }).fill('Pronto para buscar — cuidado sintético concluído.');
  await staff.getByRole('button', { name: 'Confirmar ação', exact: true }).click();
  await expect(staff.getByText('Concluída', { exact: true })).toBeVisible();
  const ready = await mail(customer, appointment.id, 'pet ficou pronto'); expect(ready.Text).not.toContain(secret);
  checks.push({ name: 'ready-notice-smtp', actual_smtp: true });
  await customer.reload();
  await expect(customer.getByText('Pronto para buscar — cuidado sintético concluído.', { exact: true })).toBeVisible();
  await expect(customer.getByText(secret)).toHaveCount(0);
  await check(customer, 'customer-completion');
  const nextAvailable = await get(customer, '/me/availability?pet_id=' + pet.id + '&service_id=' + service.id + '&date=' + day);
  const nextSlot = nextAvailable.slots.find(slot => new Date(slot.starts_at) >= new Date(appointment.ends_at));
  expect(nextSlot).toBeTruthy();
  following = await write(customer, 'POST', '/me/appointments', { pet_id: pet.id, service_id: service.id,
    starts_at: nextSlot.starts_at, offer_version: nextAvailable.offer.version, configuration_version: nextAvailable.configuration_version });
  await staff.goto('/operacao/atendimentos/' + following.id);
  await staff.locator('.previous-care summary').first().click();
  await expect(staff.getByText(secret, { exact: true })).toBeVisible();
  const followingPublic = await get(customer, '/me/appointments/' + following.id);
  expect(JSON.stringify(followingPublic)).not.toContain(secret);
  await check(staff, 'previous-care-private-context');
  await write(customer, 'POST', '/me/appointments/' + following.id + '/cancel', { version: following.version, reason: 'Encerrar segunda reserva sintética após verificar contexto' });
  await admin.goto('/gestao');
  await expect(admin.getByRole('heading', { name: 'Cuidados por pessoa', exact: true })).toBeVisible();
  const metrics = await get(admin, '/management/metrics?date_from=' + day + '&date_to=' + day);
  expect(metrics.staff.find(p => p.resource_id === alternate.id).completed).toBeGreaterThan(0);
  await check(admin, 'management-performance-desktop');
  await admin.setViewportSize({ width: 320, height: 900 }); await check(admin, 'management-performance-mobile');
  console.log('Operational journey completed with real server time and SMTP.');
} finally {
  // Restore only touched rules with current versions; never reset a volume or delete a reservation.
  const cleanup = [];
  if (staff && appointment) {
    const current = await get(staff, '/operations/attendances/' + appointment.id);
    if (current.item.appointment.status === 'BOOKED') {
      await write(staff, 'POST', '/operations/appointments/' + appointment.id + '/cancel', { version: current.item.appointment.version, reason: 'Encerrar verificação sintética incompleta' });
    }
  }
  if (staff && following) {
    const current = await get(staff, '/operations/attendances/' + following.id);
    if (current.item.appointment.status === 'BOOKED') await write(staff, 'POST', '/operations/appointments/' + following.id + '/cancel', { version: current.item.appointment.version, reason: 'Encerrar segunda reserva sintética incompleta' });
  }
  if (rosterChanged) {
    const current = await get(staff, '/operations/roster/' + rosterDay);
    await write(staff, 'PUT', '/operations/roster/' + rosterDay, { version: current.version, reason: 'Restaurar configuração anterior ao teste', shifts: originalRoster.custom ? originalRoster.rows.map(({ resource_id, windows }) => ({ resource_id, windows })) : null });
    cleanup.push('roster-restored');
  }
  if (poolsChanged) {
    const current = await get(staff, '/operations/capacity');
    await write(staff, 'PUT', '/operations/capacity', { version: current.version, pools: originalPools.pools }); cleanup.push('pools-restored');
  }
  if (rulesChanged) {
    let current = await get(staff, '/operations/calendar');
    await write(staff, 'PUT', '/operations/calendar', { ...originalSettings.configuration, version: current.configuration.version });
    for (const original of originalSettings.resources) {
      current = await get(staff, '/operations/calendar'); const live = current.resources.find(r => r.id === original.id);
      if (live && JSON.stringify(live.service_ids) !== JSON.stringify(original.service_ids)) {
        const { id, ...body } = original;
        await write(staff, 'PUT', '/operations/resources/' + id, { ...body, version: live.version });
      }
    }
    cleanup.push('calendar-and-skills-restored');
  }
  if (staff && service) {
    const current = await get(staff, '/operations/services/' + service.id);
    await write(staff, 'PUT', '/operations/services/' + current.id, { name: current.name, description: current.description,
      species_ids: current.species_ids, options: current.options, version: current.version, active: false });
    cleanup.push('synthetic-service-inactive');
  }
  await writeFile(resolve(output, 'report.json'), JSON.stringify({ database, checks, errors, cleanup, completed_at: new Date().toISOString() }, null, 2));
  await Promise.all(contexts.map(c => c.close())); await browser.close();
}
