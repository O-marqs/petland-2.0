import { expect, type Browser, type Page } from '@playwright/test';
import { accessible, signIn } from './care-helpers';

async function write(page: Page, method: 'POST' | 'PUT', path: string, data: unknown) {
  const csrf = await (await page.request.get('/api/v1/auth/csrf')).json();
  const response = await page.request.fetch('/api/v1' + path, {
    method,
    headers: {
      Origin: 'http://localhost:5173',
      'X-CSRF-Token': csrf.csrf_token,
      'Idempotency-Key': crypto.randomUUID(),
    },
    data,
  });
  expect(response.ok(), await response.text()).toBe(true);
  return response.json();
}

export async function staffAttendance(
  staff: Page,
  browser: Browser,
  customerId: string,
  email: string,
) {
  const service = await write(staff, 'POST', '/operations/services', {
    name: 'Cuidado P05 Sintético ' + Date.now(),
    description: 'Somente teste de atendimento',
    species_ids: ['DOG'],
    active: true,
    options: [{ size: 'SMALL', price: '10.00', duration_minutes: 5 }],
  });
  const pet = await write(staff, 'POST', '/operations/customers/' + customerId + '/pets', {
    name: 'Luna Operação Sintética',
    species_id: 'DOG',
    size: 'SMALL',
    care_notes: 'Sensibilidade ao secador — dado sintético.',
  });
  const actor = await (await staff.request.get('/api/v1/auth/me')).json();
  let settings = await (await staff.request.get('/api/v1/operations/calendar')).json();
  const resource = settings.resources.find((r: { user_id: string }) => r.user_id === actor.id);
  const { id: resourceId, ...resourceBody } = resource;
  await write(staff, 'PUT', '/operations/resources/' + resourceId, {
    ...resourceBody,
    service_ids: [...resource.service_ids, service.id],
  });
  settings = await (await staff.request.get('/api/v1/operations/calendar')).json();
  const start = new Date(Math.ceil(Date.now() / 60000) * 60000 + 60000);
  const day = new Intl.DateTimeFormat('en-CA', {
    timeZone: settings.configuration.timezone,
  }).format(start);
  const hour = new Intl.DateTimeFormat('pt-BR', {
    timeZone: settings.configuration.timezone,
    hour: '2-digit',
    minute: '2-digit',
  }).format(start);
  await write(staff, 'PUT', '/operations/calendar', {
    ...settings.configuration,
    step_minutes: 1,
    no_show_grace_minutes: 10,
    calendar: {
      ...settings.configuration.calendar,
      exceptions: [
        ...settings.configuration.calendar.exceptions.filter(
          (e: { date: string }) => e.date !== day,
        ),
        { date: day, windows: [{ start: 0, end: 1440 }] },
      ],
    },
  });
  const customerContext = await browser.newContext({
    baseURL: 'http://127.0.0.1:5173',
    viewport: { width: 390, height: 844 },
  });
  let appointmentId: string | undefined;
  try {
    const customer = await customerContext.newPage();
    await signIn(customer, email);
    await customer.goto('/app/agendar');
    await customer.getByLabel('Pet (obrigatório)', { exact: true }).selectOption(pet.id);
    await customer.getByLabel('Serviço (obrigatório)', { exact: true }).selectOption(service.id);
    await customer.getByLabel('Dia do cuidado (obrigatório)').fill(day);
    await customer.getByRole('button', { name: hour, exact: true }).click();
    await customer.getByRole('button', { name: 'Sim, confirmar reserva' }).click();
    await expect(
      customer.getByRole('heading', { name: 'Reserva confirmada', exact: true }),
    ).toBeVisible();
    await customer.getByRole('button', { name: 'Ver minha reserva' }).click();
    appointmentId = customer.url().split('/').at(-1)!;
    await staff.goto('/operacao/agenda?data=' + day + '&busca=Luna%20Operação&pessoa=' + resourceId);
    await expect(staff.getByRole('heading', { name: pet.name, exact: true })).toBeVisible();
    await accessible(staff);
    await staff.getByRole('link', { name: /Abrir atendimento de Luna Operação/ }).click();
    await staff.getByRole('button', { name: 'Registrar chegada', exact: true }).click();
    await staff.getByRole('button', { name: 'Confirmar ação', exact: true }).click();
    await expect(staff.getByText('Chegou', { exact: true })).toBeVisible();
    await staff.getByRole('button', { name: 'Adicionar anotação', exact: true }).click();
    const secret = 'Nota privada P05 — nunca publicar automaticamente.';
    await staff.getByLabel('Anotação (obrigatório)', { exact: true }).fill(secret);
    await staff.getByRole('button', { name: 'Salvar anotação', exact: true }).click();
    await expect(staff.getByText(secret, { exact: true })).toBeVisible();
    const publicDetail = await customer.request.get('/api/v1/me/appointments/' + appointmentId);
    expect(await publicDetail.text()).not.toContain(secret);
    expect(
      (await customer.request.get('/api/v1/operations/attendances/' + appointmentId)).status(),
    ).toBe(403);
    await accessible(staff);
    await staff.locator('#main').focus();
    await staff.screenshot({ path: 'test-results/p05-attendance-mobile.png', fullPage: true });
    // Real server time, no test-only endpoint or browser clock pretending the visit started.
    await expect
      .poll(
        async () => {
          await staff.getByRole('button', { name: 'Atualizar atendimento', exact: true }).click();
          return await staff
            .getByRole('button', { name: 'Iniciar atendimento', exact: true })
            .count();
        },
        { timeout: 130000, intervals: [2000, 5000] },
      )
      .toBe(1);
    await staff.getByRole('button', { name: 'Iniciar atendimento', exact: true }).click();
    await staff.getByRole('button', { name: 'Confirmar ação', exact: true }).click();
    await expect(staff.getByText('Em atendimento', { exact: true })).toBeVisible();
    await staff.getByRole('button', { name: 'Concluir atendimento', exact: true }).click();
    await staff
      .getByLabel('Resumo para o cliente', { exact: true })
      .fill('Cuidado concluído com tranquilidade — resumo sintético P05.');
    await staff.getByRole('button', { name: 'Confirmar ação', exact: true }).click();
    await expect(staff.getByText('Concluída', { exact: true })).toBeVisible();
    await customer.reload();
    await expect(customer.getByRole('heading', { name: 'Resumo do cuidado' })).toBeVisible();
    await expect(
      customer.getByText('Cuidado concluído com tranquilidade — resumo sintético P05.', {
        exact: true,
      }),
    ).toBeVisible();
    await expect(customer.getByText(secret)).toHaveCount(0);
    await customer.setViewportSize({ width: 320, height: 800 });
    await accessible(customer);
    await customer.screenshot({
      path: 'test-results/p05-customer-history-mobile.png',
      fullPage: true,
    });
    await staff.setViewportSize({ width: 1440, height: 1000 });
    await staff.goto('/operacao/agenda?data=' + day);
    await staff.getByRole('button', { name: 'Semana', exact: true }).click();
    await expect(staff).toHaveURL(/visao=semana/);
    await accessible(staff);
    await staff.screenshot({ path: 'test-results/p05-agenda-desktop.png', fullPage: true });
    // A full-day calendar (1440) must remain editable in the native time inputs.
    await staff.goto('/operacao/configuracoes');
    await staff.getByRole('button', { name: 'Configurar expediente e regras' }).click();
    await staff.getByRole('button', { name: 'Conferir impacto' }).click();
    await expect(staff.getByText('Nenhuma reserva afetada', { exact: true })).toBeVisible();
  } finally {
    await customerContext.close();
  }
}
