// Final presentation: ordinary UI/API, owned demo on 8445 only, actual server clock.
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { createHash, randomUUID } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { chromium, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const root = fileURLToPath(new URL('../../../', import.meta.url));
const local = resolve(root, '.local/final-case');
const output = resolve(local, 'capture');
const origin = 'https://localhost:8445';
const reference = 'f3d70a2cce07d587351eadaa66864b7c1ae4444a';
const fixture = JSON.parse(await readFile(resolve(local, 'fixture.json'), 'utf8'));
const active = (await readFile(resolve(local, 'staging/active-db.txt'), 'utf8')).trim();
if (
  process.env.APP_ENV === 'production' ||
  fixture.project !== 'petlandfinalcase' ||
  fixture.origin !== origin ||
  fixture.application_commit !== reference ||
  !fixture.tls_verified ||
  active !== fixture.database ||
  !/^petland_reset_[a-f0-9]{32}_demo$/.test(active) ||
  fixture.manifest.fixture !== 'petland-p07-synthetic-v1'
)
  throw new Error('Own fresh presentation demo required');
const images = Object.fromEntries(
  ['api', 'web'].map((name) => {
    const value = JSON.parse(
      execFileSync('docker', ['inspect', `petlandfinalcase-${name}-1`], { encoding: 'utf8' }),
    )[0];
    if (value.Config.Labels['org.opencontainers.image.revision'] !== reference.slice(0, 12))
      throw new Error('Source image mismatch');
    return [
      name,
      {
        tag: value.Config.Image,
        id: value.Image,
        revision: value.Config.Labels['org.opencontainers.image.revision'],
      },
    ];
  }),
);
const accounts = JSON.parse(await readFile(resolve(local, 'staging/accounts.json'), 'utf8'));
await mkdir(output, { recursive: true });
const browser = await chromium.launch();
const context = await browser.newContext({
  baseURL: origin,
  ignoreHTTPSErrors: true,
  viewport: { width: 1280, height: 900 },
  recordVideo: { dir: resolve(output, 'raw'), size: { width: 1280, height: 900 } },
});
const checks = [],
  chapters = [],
  actions = [],
  errors = [];
let page, video, started;
const elapsed = () => Math.round((performance.now() - started) / 10) / 100;
async function api(path, method = 'GET', data) {
  const headers = { Origin: origin };
  if (method !== 'GET') {
    const response = await context.request.get('/api/v1/auth/csrf');
    expect(response.ok()).toBe(true);
    headers['X-CSRF-Token'] = (await response.json()).csrf_token;
    headers['Idempotency-Key'] = randomUUID();
  }
  const response = await context.request.fetch('/api/v1' + path, { method, data, headers });
  if (!response.ok()) throw new Error(`Owned API ${method} ${path}: ${response.status()}`);
  return response.json();
}
async function auth(profile) {
  await context.clearCookies();
  await api('/auth/login', 'POST', accounts[profile]);
  expect((await api('/auth/me')).email).toBe(accounts[profile].email);
}
async function shot(name, title, caption, hold = 6500) {
  await page.waitForLoadState('networkidle');
  await page.evaluate(() => document.fonts.ready);
  const violations = (
    await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze()
  ).violations.map((v) => v.id);
  expect(violations).toEqual([]);
  expect(errors).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: resolve(output, name + '.png'), fullPage: name !== 'final-home' });
  chapters.push({ at_seconds: elapsed(), title, caption, screenshot: name + '.png' });
  checks.push({
    name,
    route: new URL(page.url()).pathname + new URL(page.url()).search,
    viewport: page.viewportSize(),
    violations,
    reflow: true,
    screenshot: name + '.png',
  });
  console.log('Final chapter captured: ' + name);
  await page.waitForTimeout(hold);
}
const dayFor = (value) =>
  new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Sao_Paulo' }).format(value);
const hourFor = (value) =>
  new Intl.DateTimeFormat('pt-BR', {
    timeZone: 'America/Sao_Paulo',
    hour: '2-digit',
    minute: '2-digit',
  }).format(value);
async function mail(appointmentId, subject) {
  await expect
    .poll(
      async () => {
        const messages = await (
          await context.request.get('http://127.0.0.1:8028/api/v1/search', {
            params: { query: `to:${accounts.customer_a.email} subject:${subject}` },
          })
        ).json();
        for (const m of messages.messages ?? []) {
          const message = await (
            await context.request.get('http://127.0.0.1:8028/api/v1/message/' + m.ID)
          ).json();
          if (message.Text.includes(appointmentId)) return true;
        }
        return false;
      },
      { timeout: 20000 },
    )
    .toBe(true);
  checks.push({ name: 'smtp-' + subject, actual_mailpit: true, external_delivery: false });
}

try {
  // Preparation uses existing APIs; fixture settings are disclosed in the public provenance.
  await auth('employee');
  const services = await api('/operations/services');
  if (services.items.some((s) => s.name === 'Banho de demonstração final'))
    throw new Error('Capture already started; run final_case_demo.py fresh');
  const service = await api('/operations/services', 'POST', {
    name: 'Banho de demonstração final',
    description: 'Cuidado fictício de cinco minutos para captura com relógio real.',
    species_ids: ['DOG'],
    active: true,
    options: [{ size: 'SMALL', price: '40.00', duration_minutes: 5 }],
  });
  let settings = await api('/operations/calendar');
  const resources = settings.resources.filter((r) => r.active).slice(0, 2);
  expect(resources.length).toBe(2);
  for (const resource of resources) {
    const { id, ...body } = resource;
    await api('/operations/resources/' + id, 'PUT', {
      ...body,
      service_ids: [...resource.service_ids, service.id],
    });
  }
  const today = dayFor(new Date());
  settings = await api('/operations/calendar');
  await api('/operations/calendar', 'PUT', {
    ...settings.configuration,
    lead_minutes: 0,
    step_minutes: 1,
    reminder_minutes: 1,
    calendar: {
      ...settings.configuration.calendar,
      exceptions: [
        ...settings.configuration.calendar.exceptions.filter((e) => e.date !== today),
        { date: today, windows: [{ start: 0, end: 1440 }] },
      ],
    },
  });
  const capacity = await api('/operations/capacity');
  await api('/operations/capacity', 'PUT', {
    version: capacity.version,
    pools: [
      ...capacity.pools,
      {
        id: randomUUID(),
        name: 'Banheiras da demonstração',
        capacity: 2,
        active: true,
        service_ids: [service.id],
      },
    ],
  });
  await auth('customer_a');
  page = await context.newPage();
  video = page.video();
  started = performance.now();
  page.on('pageerror', (error) => errors.push(error.name));
  await page.goto('/');
  await shot(
    'final-home',
    'O cuidado começa aqui',
    'PetLand 3.0: uma jornada de tutor, equipe e gestão. Ambiente local, dados fictícios.',
    8000,
  );
  await page.goto('/app');
  await shot(
    'final-customer-dashboard',
    'Primeiros passos com contexto',
    'Conta demo verificada e contato preparado. A área do tutor orienta pet, reserva e acompanhamento.',
    8000,
  );
  await page.goto('/app/pets');
  await page.getByRole('button', { name: 'Adicionar pet', exact: true }).click();
  await page.getByLabel('Nome do pet (obrigatório)', { exact: true }).fill('Nala');
  await page.getByLabel('Espécie (obrigatório)', { exact: true }).selectOption('DOG');
  await page.getByLabel('Porte (obrigatório)', { exact: true }).selectOption('SMALL');
  const allergy = 'Alerta fictício: usar shampoo hipoalergênico.';
  await page.getByLabel('Alergias e restrições críticas', { exact: true }).fill(allergy);
  await page
    .getByLabel('Comportamento e preferências de cuidado', { exact: true })
    .fill('Preferência fictícia: secador baixo e aproximação tranquila.');
  await shot(
    'final-pet',
    'O pet vem com seu contexto',
    'Nala é cadastrada pela interface, com porte, alergia e preferência. São dados fictícios persistidos.',
    7000,
  );
  await page.getByRole('button', { name: 'Salvar pet', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Nala', exact: true })).toBeVisible();
  const pet = (await api('/me/pets')).items.find((p) => p.name === 'Nala');
  expect(pet.allergies).toBe(allergy);
  actions.push({ kind: 'pet_created_via_ui', pet_id: pet.id, persisted: true });
  await page.goto('/servicos');
  await shot(
    'final-services',
    'Um cuidado com preço claro',
    'O catálogo apresenta serviços e portes. O serviço da captura usa duração fictícia de cinco minutos.',
    6500,
  );
  await page.goto('/app/agendar');
  await page.getByLabel('Pet (obrigatório)', { exact: true }).selectOption(pet.id);
  await page.getByLabel('Serviço (obrigatório)', { exact: true }).selectOption(service.id);
  const start = new Date(Math.ceil(Date.now() / 60000) * 60000 + 60000);
  if (dayFor(start) !== today) throw new Error('Capture cannot cross local midnight');
  await page.getByLabel('Dia do cuidado (obrigatório)').fill(today);
  await expect(page.getByRole('button', { name: hourFor(start), exact: true })).toBeVisible();
  await shot(
    'final-availability',
    'Uma vaga real',
    'A disponibilidade considera loja, pessoas aptas, duração, bloqueios e recurso físico. O tutor escolhe o horário.',
    7000,
  );
  await page.getByRole('button', { name: hourFor(start), exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Confira antes de confirmar' })).toBeVisible();
  await shot(
    'final-booking',
    'Revisar antes de reservar',
    'Preço e duração aparecem no resumo. Abrir o resumo ainda não cria a reserva; o tutor precisa confirmar.',
    9000,
  );
  await page.getByRole('button', { name: 'Sim, confirmar reserva', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Reserva confirmada', exact: true }),
  ).toBeVisible();
  await shot(
    'final-confirmation',
    'Reserva confirmada',
    'A confirmação grava a reserva. Uma pessoa apta é atribuída pelo servidor, conforme a regra de produto.',
    7000,
  );
  await page.getByRole('button', { name: 'Ver minha reserva', exact: true }).click();
  const appointmentId = page.url().split('/').at(-1);
  const appointment = (await api('/me/appointments/' + appointmentId)).appointment;
  expect(appointment.pet_id).toBe(pet.id);
  actions.push({
    kind: 'booking_confirmed_via_ui',
    appointment_id: appointmentId,
    pet_id: pet.id,
    status: appointment.status,
  });
  await auth('employee');
  await page.goto('/operacao?data=' + today + '&escopo=equipe');
  await expect(page.getByRole('heading', { name: pet.name, exact: true })).toBeVisible();
  await shot(
    'final-operations-dashboard',
    'O que a equipe faz hoje',
    'O painel reúne próximos cuidados, agenda, pendências e carga. A mesma Nala aparece para a equipe.',
    8000,
  );
  await page.goto('/operacao/agenda?data=' + today + '&busca=Nala');
  await shot(
    'final-agenda',
    'Da agenda ao atendimento',
    'A reserva do tutor é a mesma na agenda da loja. O funcionário abre seu atendimento.',
    6500,
  );
  await page.getByRole('link', { name: /Abrir atendimento de Nala/ }).click();
  await expect(page.getByText(allergy, { exact: true })).toBeVisible();
  await shot(
    'final-attendance',
    'Contexto crítico antes de começar',
    'A alergia acompanha o pet. A equipe tem contexto de cuidado e registra as ações com autoria.',
    7500,
  );
  await page.getByRole('button', { name: 'Registrar chegada', exact: true }).click();
  await page.getByRole('button', { name: 'Confirmar ação', exact: true }).click();
  await expect(page.getByText('Chegou', { exact: true })).toBeVisible();
  const beforeTransfer = await api('/operations/attendances/' + appointmentId);
  const alternate = resources.find((r) => r.id !== beforeTransfer.item.resource_id);
  await page.getByRole('button', { name: 'Transferir responsável', exact: true }).click();
  await page
    .getByLabel('Nova pessoa responsável (obrigatório)', { exact: true })
    .selectOption(alternate.id);
  await page
    .getByLabel('Motivo (obrigatório)', { exact: true })
    .fill('Redistribuição da equipe — demonstração fictícia.');
  await page.getByRole('button', { name: 'Confirmar ação', exact: true }).click();
  await expect(page.getByText('Responsável transferido', { exact: true })).toBeVisible();
  const moved = await api('/operations/attendances/' + appointmentId);
  expect(moved.item.resource_id).toBe(alternate.id);
  expect(moved.item.appointment.starts_at).toBe(appointment.starts_at);
  actions.push({
    kind: 'arrival_and_transfer_via_ui',
    appointment_id: appointmentId,
    assigned_resource: alternate.id,
    time_preserved: true,
  });
  await shot(
    'final-transfer',
    'Trocar a pessoa, preservar o combinado',
    'A equipe transfere o cuidado com motivo. Horário, preço e duração contratados permanecem iguais.',
    6500,
  );
  const privateNote = 'Nota interna fictícia: sensível ao secador; observar aproximação.';
  await page.getByRole('button', { name: 'Adicionar anotação', exact: true }).click();
  await page.getByLabel('Anotação (obrigatório)', { exact: true }).fill(privateNote);
  await page.getByRole('button', { name: 'Salvar anotação', exact: true }).click();
  await expect
    .poll(
      async () => {
        await page.getByRole('button', { name: 'Atualizar atendimento', exact: true }).click();
        return page.getByRole('button', { name: 'Iniciar atendimento', exact: true }).count();
      },
      { timeout: 130000, intervals: [3000] },
    )
    .toBe(1);
  await page.getByRole('button', { name: 'Iniciar atendimento', exact: true }).click();
  await page
    .getByLabel('Li as alergias e restrições críticas atuais deste pet antes de iniciar.')
    .check();
  await page.getByRole('button', { name: 'Confirmar ação', exact: true }).click();
  await expect(page.getByText('Em atendimento', { exact: true })).toBeVisible();
  await shot(
    'final-attendance-started',
    'Leitura atual e início real',
    'Início liberado pelo relógio real do servidor. A equipe confirma que leu as restrições atuais.',
    8000,
  );
  const summary =
    'Cuidado fictício concluído com shampoo hipoalergênico. Nala está pronta para buscar.';
  await page.getByRole('button', { name: 'Concluir atendimento', exact: true }).click();
  await page.getByLabel('Resumo para o cliente', { exact: true }).fill(summary);
  await page.getByRole('button', { name: 'Confirmar ação', exact: true }).click();
  await expect(page.getByText('Concluída', { exact: true })).toBeVisible();
  await shot(
    'final-attendance-completed',
    'Concluir e comunicar',
    'Conclusão e resumo são registrados. O aviso de pronto é verificado no Mailpit local, sem envio externo.',
    7000,
  );
  await mail(appointmentId, 'pet ficou pronto');
  await auth('customer_a');
  await page.goto('/app/reservas/' + appointmentId);
  await expect(page.getByText(summary, { exact: true })).toBeVisible();
  expect(JSON.stringify(await api('/me/appointments/' + appointmentId))).not.toContain(privateNote);
  await expect(page.getByText(privateNote, { exact: true })).toHaveCount(0);
  actions.push({
    kind: 'completed_history_via_ui',
    appointment_id: appointmentId,
    status: 'COMPLETED',
    internal_note_hidden_in_public_payload: true,
  });
  await shot(
    'final-customer-history',
    'O tutor sabe o que aconteceu',
    'O histórico mostra o cuidado concluído e o resumo publicado. A nota interna permanece privada.',
    8000,
  );
  let futureDay, free;
  for (let delta = 7; delta <= 14; delta++) {
    futureDay = dayFor(new Date(Date.now() + delta * 86400000));
    free = await api(
      '/me/availability?pet_id=' + pet.id + '&service_id=' + service.id + '&date=' + futureDay,
    );
    if (free.slots.length) break;
  }
  expect(free.slots.length).toBeGreaterThan(0);
  const future = await api('/me/appointments', 'POST', {
    pet_id: pet.id,
    service_id: service.id,
    starts_at: free.slots[0].starts_at,
    offer_version: free.offer.version,
    configuration_version: free.configuration_version,
  });
  await auth('admin');
  await page.goto('/gestao');
  await page.getByRole('heading', { name: 'Cuidados por pessoa', exact: true }).waitFor();
  await shot(
    'final-management',
    'A operação vira informação',
    'Indicadores vêm dos atendimentos persistidos. Atribuição pelo responsável final; números da demo são fictícios.',
    8500,
  );
  const rosterDay = dayFor(new Date(Date.now() + 5 * 86400000));
  await page.goto('/operacao/escala?data=' + rosterDay);
  await page
    .getByLabel('Motivo da escala (obrigatório)')
    .fill('Equipe reduzida somente nesta data — demonstração.');
  const person = page
    .locator('.roster-person')
    .filter({ has: page.getByText(resources[0].name, { exact: true }) });
  await person.getByRole('checkbox', { name: /Trabalha nesta data/ }).uncheck();
  await page.getByRole('button', { name: 'Conferir impactos da escala', exact: true }).click();
  await page.getByRole('button', { name: 'Confirmar escala desta data', exact: true }).click();
  await expect(page.getByText('Escala da data atualizada', { exact: true })).toBeVisible();
  expect(
    (await api('/operations/roster/' + rosterDay)).rows.find(
      (r) => r.resource_id === resources[0].id,
    ).windows,
  ).toEqual([]);
  actions.push({
    kind: 'single_date_roster_saved_via_ui',
    date: rosterDay,
    outside_week_unchanged: true,
  });
  await shot(
    'final-roster',
    'Um dia diferente, sem refazer a semana',
    'Escala coletiva salva para uma única data: pessoas e períodos definidos, com prévia e confirmação.',
    7500,
  );
  await page.goto('/operacao/capacidade');
  const pools = await api('/operations/capacity');
  const poolIndex = pools.pools.findIndex((p) => p.name === 'Banheiras da demonstração') + 1;
  await page
    .getByLabel('Quantidade simultânea ' + poolIndex + ' (obrigatório)', { exact: true })
    .fill('1');
  await page.getByRole('button', { name: 'Conferir impactos da capacidade', exact: true }).click();
  await page.getByRole('button', { name: 'Confirmar capacidade física', exact: true }).click();
  await expect(page.getByText('Capacidade atualizada', { exact: true })).toBeVisible();
  actions.push({
    kind: 'physical_capacity_saved_via_ui',
    shared_pool: 'Banheiras da demonstração',
    quantity: 1,
  });
  await shot(
    'final-capacity',
    'Equipe livre não basta',
    'O recurso físico limita serviços simultâneos. Uma banheira pode ser o limite mesmo com duas pessoas livres.',
    7500,
  );
  const futureInternal = await api('/operations/attendances/' + future.id);
  const beforeRoster = await api('/operations/roster/' + futureDay);
  await page.goto('/operacao/escala?data=' + futureDay);
  await page
    .getByLabel('Motivo da escala (obrigatório)')
    .fill('Prévia: colaborador ausente com reserva existente — demonstração.');
  const affected = beforeRoster.rows.find((r) => r.resource_id === futureInternal.item.resource_id);
  await page
    .locator('.roster-person')
    .filter({ has: page.getByText(affected.name, { exact: true }) })
    .getByRole('checkbox', { name: /Trabalha nesta data/ })
    .uncheck();
  await page.getByRole('button', { name: 'Conferir impactos da escala', exact: true }).click();
  await expect(
    page.getByText('1 reserva(s) precisam ser resolvidas', { exact: true }),
  ).toBeVisible();
  expect((await api('/operations/roster/' + futureDay)).version).toBe(beforeRoster.version);
  expect((await api('/operations/attendances/' + future.id)).item.appointment.status).toBe(
    'BOOKED',
  );
  actions.push({
    kind: 'blocked_impact_preview_via_ui',
    future_appointment_id: future.id,
    mutation: false,
    reservation_preserved: true,
  });
  await shot(
    'final-impact',
    'Mudar com responsabilidade',
    'A prévia identifica a reserva afetada e bloqueia salvar. Ninguém perde seu horário silenciosamente.',
    8000,
  );
  await page.goto('/gestao/auditoria');
  await shot(
    'final-audit',
    'História e limites explícitos',
    'Ações mantêm autoria e histórico. Aceite humano, publicação e SMTP externo continuam pendentes.',
    6500,
  );
  if (elapsed() < 240) await page.waitForTimeout((240 - elapsed()) * 1000);
  const duration = elapsed();
  if (duration < 180 || duration > 300) throw new Error('Capture outside 3–5 minutes: ' + duration);
  await context.close();
  await video.saveAs(resolve(output, 'petland-final-demo.webm'));
  // Mobile checks after recording: actual pages at 320px, no credentials captured.
  const mobile = await browser.newContext({
    baseURL: origin,
    ignoreHTTPSErrors: true,
    viewport: { width: 320, height: 900 },
  });
  for (const [profile, route, name] of [
    ['customer_a', '/app/reservas/' + appointmentId, 'final-customer-mobile'],
    ['employee', '/operacao?data=' + today + '&escopo=equipe', 'final-operations-mobile'],
    ['admin', '/operacao/escala?data=' + rosterDay, 'final-roster-mobile'],
  ]) {
    const p = await mobile.newPage();
    p.on('pageerror', (error) => errors.push(error.name));
    const token = (await (await mobile.request.get('/api/v1/auth/csrf')).json()).csrf_token;
    const login = await mobile.request.post('/api/v1/auth/login', {
      data: accounts[profile],
      headers: { Origin: origin, 'X-CSRF-Token': token },
    });
    expect(login.ok()).toBe(true);
    await p.goto(route);
    await p.waitForLoadState('networkidle');
    const violations = (
      await new AxeBuilder({ page: p })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'])
        .analyze()
    ).violations.map((v) => v.id);
    expect(violations).toEqual([]);
    expect(errors).toEqual([]);
    expect(await p.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await p.screenshot({ path: resolve(output, name + '.png'), fullPage: true });
    checks.push({
      name,
      route,
      viewport: { width: 320, height: 900 },
      violations,
      reflow: true,
      screenshot: name + '.png',
    });
    await mobile.clearCookies();
    await p.close();
  }
  await mobile.close();
  await writeFile(
    resolve(output, 'capture-raw.json'),
    JSON.stringify(
      {
        status: 'FINAL_CURRENT_SNAPSHOT',
        application_commit: reference,
        schema_revision: '0007_product_operations',
        captured_at: new Date().toISOString(),
        origin,
        project: 'petlandfinalcase',
        database: active,
        synthetic: true,
        fixture: fixture.manifest.fixture,
        fake_clock: false,
        video_audio: 'none',
        source_equality_checked: true,
        images,
        viewport: { width: 1280, height: 900 },
        duration_seconds: duration,
        preparation: [
          'Own credentials/CA/volume; seed/reset through existing offline tools',
          'Verified demo customer/contact; authentication through normal API before filmed journeys; passwords not filmed',
          'Existing service API: fictional five-minute service at BRL 40; two skilled resources; minute slots; current-day opening; lead=0/reminder=1',
          'Shared pool initially two units; one future booking via ordinary customer API solely for impact preview',
        ],
        actions,
        chapters,
        checks,
        errors,
        passed: true,
        capture_script_sha256: createHash('sha256')
          .update(await readFile(fileURLToPath(import.meta.url)))
          .digest('hex'),
      },
      null,
      2,
    ) + '\n',
  );
  console.log(
    'Final continuous recording completed: ' +
      duration +
      ' seconds; actual UI/API/SMTP, no fake clock.',
  );
} finally {
  await context.close();
  await browser.close();
}
