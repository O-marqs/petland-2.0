import { expect, type APIRequestContext, type Browser, type Page } from '@playwright/test';
import { accessible, signIn } from './care-helpers';

async function mutation(page: Page, path: string, data: unknown) {
  const csrf = await (await page.request.get('/api/v1/auth/csrf')).json();
  return page.request.post('/api/v1' + path, { headers: { Origin: 'http://localhost:5173', 'X-CSRF-Token': csrf.csrf_token, 'Idempotency-Key': crypto.randomUUID() }, data });
}
async function notice(request: APIRequestContext, email: string, subject: string) {
  const mailbox = process.env.MAILPIT_URL ?? 'http://127.0.0.1:8025';
  expect(['localhost', '127.0.0.1']).toContain(new URL(mailbox).hostname);
  await expect.poll(async () => {
    const messages = await (await request.get(mailbox + '/api/v1/search', { params: { query: 'to:' + email } })).json();
    return messages.messages?.some((m: { Subject: string }) => m.Subject.includes(subject));
  }, { timeout: 20000 }).toBe(true);
}

export async function staffScheduling(staff: Page, request: APIRequestContext, browser: Browser, service: { id: string; name: string; version: number }, customerId: string, email: string) {
  const petResponse = await mutation(staff, '/operations/customers/' + customerId + '/pets', { name: 'Luna Agenda Sintética', species_id: 'DOG', size: 'SMALL' });
  expect(petResponse.status()).toBe(201);
  const pet = await petResponse.json();
  const otherPet = await (await mutation(staff, '/operations/customers/' + customerId + '/pets', { name: 'Sol Agenda Sintético', species_id: 'DOG', size: 'SMALL' })).json();
  const worker = await (await staff.request.get('/api/v1/auth/me')).json();
  const date = new Date(Date.now() + 14 * 86400000).toISOString().slice(0, 10);
  const resourceName = 'Equipe Agenda Sintética ' + Date.now();
  await staff.goto('/operacao/configuracoes');
  await staff.getByRole('button', { name: 'Adicionar pessoa', exact: true }).click();
  await staff.getByLabel('Pessoa da equipe (obrigatório)').selectOption(worker.id);
  await staff.getByLabel('Nome na agenda da equipe (obrigatório)').fill(resourceName);
  await staff.getByLabel(service.name, { exact: true }).check();
  await staff.getByRole('button', { name: 'Salvar pessoa na agenda' }).click();
  await expect(staff.getByText('Agenda atualizada', { exact: true })).toBeVisible();
  await staff.getByRole('button', { name: 'Configurar expediente e regras' }).click();
  await staff.getByLabel('Antecedência mínima para reservar (minutos) (obrigatório)').fill('0');
  await staff.getByLabel('Até quantos dias no futuro aceitar reservas (obrigatório)').fill('30');
  await staff.getByLabel('Intervalo entre opções de horário (minutos) (obrigatório)').fill('15');
  await staff.getByLabel('Prazo para o cliente alterar (minutos antes) (obrigatório)').fill('0');
  const existing = await (await staff.request.get('/api/v1/operations/calendar')).json();
  let index = existing.configuration.calendar.exceptions.findIndex((e: { date: string }) => e.date === date);
  if (index < 0) { index = existing.configuration.calendar.exceptions.length; await staff.getByRole('button', { name: 'Adicionar data especial', exact: true }).click(); }
  await staff.getByLabel('Data especial ' + (index + 1) + ' (obrigatório)', { exact: true }).fill(date);
  const section = staff.getByRole('group', { name: 'Data especial ' + (index + 1), exact: true });
  if (await section.getByLabel('Início — data especial ' + (index + 1) + ' 1 (obrigatório)', { exact: true }).count() === 0) {
    await section.getByRole('button', { name: 'Adicionar período', exact: false }).click();
  }
  await section.getByLabel('Início — data especial ' + (index + 1) + ' 1 (obrigatório)', { exact: true }).fill('09:00');
  await section.getByLabel('Fim — data especial ' + (index + 1) + ' 1 (obrigatório)', { exact: true }).fill('18:00');
  await staff.getByLabel('Abrir a agenda para novas reservas').check();
  await staff.getByRole('button', { name: 'Conferir impacto' }).click();
  await expect(staff.getByText('Nenhuma reserva afetada', { exact: true })).toBeVisible();
  await accessible(staff);
  await staff.getByRole('button', { name: 'Salvar agenda', exact: true }).click();
  await expect(staff.getByText('Agenda atualizada', { exact: true })).toBeVisible();
  const customerContext = await browser.newContext({ baseURL: 'http://127.0.0.1:5173', viewport: { width: 390, height: 844 } });
  const ids: string[] = [];
  try {
    const customer = await customerContext.newPage();
    await signIn(customer, email);
    await customer.goto('/app/agendar');
    await customer.getByLabel('Pet (obrigatório)', { exact: true }).selectOption(pet.id);
    await customer.getByLabel('Serviço (obrigatório)', { exact: true }).selectOption(service.id);
    await customer.getByLabel('Dia do cuidado (obrigatório)').fill(date);
    await customer.getByRole('button', { name: '09:00', exact: true }).click();
    await expect(customer.getByRole('heading', { name: 'Confira antes de confirmar' })).toBeVisible();
    const before = await (await customer.request.get('/api/v1/me/appointments')).json();
    expect(before.total).toBe(0); // review is not a hold or a booking
    // Another pet takes the last slot after the customer's review.
    const config = await (await staff.request.get('/api/v1/operations/calendar')).json();
    const competitor = await mutation(staff, '/operations/appointments', { customer_id: customerId, pet_id: otherPet.id, service_id: service.id, starts_at: date + 'T12:00:00Z', offer_version: service.version, configuration_version: config.configuration.version });
    expect(competitor.status()).toBe(201);
    const competing = await competitor.json();
    ids.push(competing.id);
    await customer.getByRole('button', { name: 'Sim, confirmar reserva' }).click();
    await expect(customer.getByText('Esse horário não está mais disponível. Escolha outra opção.')).toBeVisible();
    await customer.getByRole('button', { name: 'Voltar aos horários' }).click();
    await expect(customer.getByLabel('Pet (obrigatório)', { exact: true })).toHaveValue(pet.id);
    await expect(customer.getByLabel('Dia do cuidado (obrigatório)')).toHaveValue(date);
    await customer.getByRole('button', { name: '10:00', exact: true }).click();
    await accessible(customer);
    await customer.screenshot({ path: 'test-results/p04-booking-review-mobile.png', fullPage: true });
    // Server commits but the first response is lost. UI must replay the same key and payload.
    let lost = false;
    await customer.route('**/api/v1/me/appointments', async route => {
      if (route.request().method() === 'POST' && !lost) {
        lost = true;
        const response = await route.fetch();
        expect(response.status()).toBe(201);
        await route.abort('failed');
      } else await route.continue();
    });
    await customer.getByRole('button', { name: 'Sim, confirmar reserva' }).click();
    await expect(customer.getByRole('button', { name: 'Tentar confirmar novamente' })).toBeVisible();
    await customer.getByRole('button', { name: 'Tentar confirmar novamente' }).click();
    await expect(customer.getByRole('heading', { name: 'Reserva confirmada', exact: true })).toBeVisible();
    const after = await (await customer.request.get('/api/v1/me/appointments')).json();
    expect(after.total).toBe(2); // only one customer attempt + competitor
    const appointment = after.items.find((a: { pet_id: string }) => a.pet_id === pet.id);
    ids.push(appointment.id);
    await notice(request, email, 'Reserva confirmada');
    await customer.getByRole('button', { name: 'Ver minha reserva' }).click();
    await accessible(customer);
    // Employee can assist; the customer gets a durable notification and sees the new time.
    await staff.goto('/operacao/reservas/' + appointment.id);
    await staff.getByRole('button', { name: 'Reagendar', exact: true }).click();
    await staff.getByLabel('Dia do cuidado (obrigatório)').fill(date);
    await staff.getByLabel('Motivo do reagendamento (obrigatório)').fill('Alteração sintética solicitada pelo cliente');
    await staff.getByRole('button', { name: '11:00', exact: true }).click();
    await staff.getByRole('button', { name: 'Confirmar novo horário' }).click();
    await expect(staff.getByRole('heading', { name: 'Novo horário confirmado' })).toBeVisible();
    await notice(request, email, 'Reserva reagendada');
    await customer.reload();
    await expect(customer.getByText('Alteração sintética solicitada pelo cliente', { exact: true })).toBeVisible();
    await customer.getByRole('button', { name: 'Cancelar reserva', exact: true }).click();
    await customer.getByLabel('Motivo do cancelamento (obrigatório)').fill('Cancelamento sintético para encerrar o teste');
    await customer.getByRole('button', { name: 'Sim, cancelar reserva' }).click();
    await expect(customer.getByText('Cancelada', { exact: true })).toBeVisible();
    await notice(request, email, 'Reserva cancelada');
    await customer.setViewportSize({ width: 320, height: 800 });
    await accessible(customer);
    await customer.locator('#main').focus();
    await customer.screenshot({ path: 'test-results/p04-history-320.png', fullPage: true });
  } finally {
    // Keep the local calendar clean, including when a browser assertion fails.
    for (const id of ids) {
      const response = await staff.request.get('/api/v1/operations/appointments/' + id);
      if (response.ok()) {
        const { appointment } = await response.json();
        if (appointment.status === 'BOOKED') await mutation(staff, '/operations/appointments/' + id + '/cancel', { version: appointment.version, reason: 'Limpeza do cenário sintético P04' });
      }
    }
    await customerContext.close();
  }
}

