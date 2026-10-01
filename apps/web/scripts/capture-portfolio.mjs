// P08: real UI writes in a fresh, explicitly owned local synthetic demo only.
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { chromium, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const root = fileURLToPath(new URL('../../../', import.meta.url));
const output = resolve(root, '.local/p08/capture');
const origin = 'https://localhost:8443';
if (process.env.APP_ENV === 'production') throw new Error('Production refused');
const fixture = JSON.parse(await readFile(resolve(root, '.local/p08/fixture.json'), 'utf8'));
const active = (await readFile(resolve(root, '.local/staging/active-db.txt'), 'utf8')).trim();
if (
  !/^petland_reset_[a-f0-9]{32}_demo$/.test(active) ||
  fixture.database !== active ||
  fixture.manifest.fixture !== 'petland-p07-synthetic-v1'
)
  throw new Error('Fresh isolated demo required');
const accounts = JSON.parse(await readFile(resolve(root, '.local/staging/accounts.json'), 'utf8'));
await mkdir(output, { recursive: true });
const browser = await chromium.launch();
const context = await browser.newContext({
  baseURL: origin,
  ignoreHTTPSErrors: true,
  viewport: { width: 1280, height: 900 },
  recordVideo: { dir: resolve(output, 'raw'), size: { width: 1280, height: 900 } },
});
const chapters = [],
  checks = [],
  errors = [];
let page, video, started;
const elapsed = () => Math.round((performance.now() - started) / 10) / 100;
const hold = (ms = 5500) => page.waitForTimeout(ms);
async function api(path, method = 'GET', data) {
  const headers = { Origin: origin };
  if (method !== 'GET') {
    const csrf = await (await context.request.get('/api/v1/auth/csrf')).json();
    headers['X-CSRF-Token'] = csrf.csrf_token;
    headers['Idempotency-Key'] = crypto.randomUUID();
  }
  const response = await context.request.fetch('/api/v1' + path, { method, data, headers });
  if (!response.ok()) throw new Error(`Local demo API ${method} ${path}: ${response.status()}`);
  return response.json();
}
async function auth(profile) {
  await context.clearCookies();
  await api('/auth/login', 'POST', accounts[profile]);
  const identity = await api('/auth/me');
  if (identity.email !== accounts[profile].email) throw new Error('Unexpected demo actor');
}
async function shot(name, caption) {
  await page.waitForLoadState('networkidle');
  const violations = (
    await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze()
  ).violations;
  if (violations.length)
    throw new Error('Accessibility violations: ' + violations.map((v) => v.id).join(','));
  if (!(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)))
    throw new Error('Horizontal overflow');
  await page.screenshot({ path: resolve(output, name + '.png') });
  chapters.push({ at_seconds: elapsed(), caption, screenshot: name + '.png' });
  checks.push({ name, axe_violations: 0, horizontal_overflow: false });
  console.log('Portfolio chapter verified: ' + name);
}

try {
  const publicContext = await browser.newContext({
    baseURL: origin,
    ignoreHTTPSErrors: true,
    viewport: { width: 1280, height: 900 },
  });
  const publicPage = await publicContext.newPage();
  await publicPage.goto('/entrar');
  await publicPage.getByRole('button', { name: 'Entrar', exact: true }).waitFor();
  await publicPage.screenshot({ path: resolve(output, 'after-login.png') });
  await publicContext.close();
  // Preparations use the ordinary API. Short duration and minute steps are fictitious demo settings.
  await auth('employee');
  const existingServices = await api('/operations/services');
  if (existingServices.items.some((item) => item.name === 'Cuidado rápido demo P08')) {
    throw new Error(
      'Capture already started in this database; create a fresh reset before retrying',
    );
  }
  const service = await api('/operations/services', 'POST', {
    name: 'Cuidado rápido demo P08',
    description: 'Serviço sintético de cinco minutos para demonstrar o fluxo com relógio real.',
    species_ids: ['DOG'],
    active: true,
    options: [{ size: 'SMALL', price: '10.00', duration_minutes: 5 }],
  });
  let settings = await api('/operations/calendar');
  const actor = await api('/auth/me');
  const resource = settings.resources.find((r) => r.user_id === actor.id);
  const { id, ...resourceBody } = resource;
  await api('/operations/resources/' + id, 'PUT', {
    ...resourceBody,
    service_ids: [...resource.service_ids, service.id],
  });
  const today = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Sao_Paulo' }).format(
    new Date(),
  );
  settings = await api('/operations/calendar');
  await api('/operations/calendar', 'PUT', {
    ...settings.configuration,
    lead_minutes: 0,
    step_minutes: 1,
    calendar: {
      ...settings.configuration.calendar,
      exceptions: [
        ...settings.configuration.calendar.exceptions.filter((e) => e.date !== today),
        { date: today, windows: [{ start: 0, end: 1440 }] },
      ],
    },
  });
  await auth('customer_a');
  page = await context.newPage();
  video = page.video();
  started = performance.now();
  page.on('pageerror', (error) => errors.push(error.name));
  await page.goto('/');
  await shot('after-home', 'PetLand 3.0: demonstração local, dados fictícios e perfis reais.');
  await hold();
  await page.goto('/entrar'); // Authenticated identity; no password is filmed or logged.
  await shot(
    'after-session-entry',
    'Acesso com sessão do servidor; credenciais geradas ficam fora do vídeo.',
  );
  await hold();
  await page.goto('/app/pets');
  await page.getByRole('button', { name: 'Adicionar pet', exact: true }).click();
  await page.getByLabel('Nome do pet (obrigatório)', { exact: true }).fill('Nala demo P08');
  await page.getByLabel('Espécie (obrigatório)', { exact: true }).selectOption('DOG');
  await shot(
    'after-pet-form',
    'Cliente cadastra Nala. Espécie e porte orientam os serviços; raça e nascimento são opcionais.',
  );
  await hold();
  await page.getByRole('button', { name: 'Salvar pet', exact: true }).click();
  await expect(page.getByText('Pet salvo com sucesso.', { exact: true })).toBeVisible();
  const pets = await api('/me/pets');
  const pet = pets.items.find((p) => p.name === 'Nala demo P08');
  if (!pet) throw new Error('UI pet not persisted');
  await page.goto('/app/agendar');
  await page.getByLabel('Pet (obrigatório)', { exact: true }).selectOption(pet.id);
  await page.getByLabel('Serviço (obrigatório)', { exact: true }).selectOption(service.id);
  // Same real server clock used by production rules; no test endpoint or fake clock.
  const start = new Date(Math.ceil(Date.now() / 60000) * 60000 + 60000);
  const day = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Sao_Paulo' }).format(start);
  if (day !== today) throw new Error('Do not capture across local midnight; reset and retry');
  const hour = new Intl.DateTimeFormat('pt-BR', {
    timeZone: 'America/Sao_Paulo',
    hour: '2-digit',
    minute: '2-digit',
  }).format(start);
  await page.getByLabel('Dia do cuidado (obrigatório)').fill(day);
  await page.getByRole('button', { name: hour, exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Confira antes de confirmar' })).toBeVisible();
  await shot(
    'after-booking-review',
    'Resumo do servidor: serviço, preço e duração. O cliente confirma; a equipe é atribuída automaticamente.',
  );
  await hold(9000);
  await page.getByRole('button', { name: 'Sim, confirmar reserva', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Reserva confirmada', exact: true }),
  ).toBeVisible();
  await hold();
  await page.getByRole('button', { name: 'Ver minha reserva', exact: true }).click();
  const appointmentId = page.url().split('/').at(-1);
  await shot(
    'after-booking-confirmed',
    'Reserva persistida. Repetição e disputa de última vaga são verificadas na suíte concorrente.',
  );
  await hold();
  await auth('employee');
  await page.goto('/operacao/agenda?data=' + day + '&busca=Nala');
  await expect(page.getByRole('heading', { name: 'Nala demo P08', exact: true })).toBeVisible();
  await shot(
    'after-employee-agenda',
    'Equipe consulta a agenda e abre o atendimento da reserva feita pelo cliente.',
  );
  await hold();
  await page.getByRole('link', { name: /Abrir atendimento de Nala/ }).click();
  await page.getByRole('button', { name: 'Registrar chegada', exact: true }).click();
  await page.getByRole('button', { name: 'Confirmar ação', exact: true }).click();
  await expect(page.getByText('Chegou', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Adicionar anotação', exact: true }).click();
  const privateNote = 'Nota interna sintética P08: observar sensibilidade ao secador.';
  await page.getByLabel('Anotação (obrigatório)', { exact: true }).fill(privateNote);
  await page.getByRole('button', { name: 'Salvar anotação', exact: true }).click();
  await expect(page.getByText(privateNote, { exact: true })).toBeVisible();
  await shot(
    'after-employee-arrival',
    'Chegada e nota interna registradas. Iniciar depende do horário real da reserva.',
  );
  await hold();
  await expect
    .poll(
      async () => {
        await page.getByRole('button', { name: 'Atualizar atendimento', exact: true }).click();
        return page.getByRole('button', { name: 'Iniciar atendimento', exact: true }).count();
      },
      { timeout: 130000, intervals: [3000, 5000] },
    )
    .toBe(1);
  await page.getByRole('button', { name: 'Iniciar atendimento', exact: true }).click();
  await page.getByRole('button', { name: 'Confirmar ação', exact: true }).click();
  await expect(page.getByText('Em atendimento', { exact: true })).toBeVisible();
  await shot(
    'after-employee-started',
    'Transição válida: chegou para em atendimento. Os instantes são definidos pelo servidor.',
  );
  await hold();
  await page.getByRole('button', { name: 'Concluir atendimento', exact: true }).click();
  const summary =
    'Cuidado fictício concluído com tranquilidade. Nala está pronta para voltar para casa.';
  await page.getByLabel('Resumo para o cliente', { exact: true }).fill(summary);
  await page.getByRole('button', { name: 'Confirmar ação', exact: true }).click();
  await expect(page.getByText('Concluída', { exact: true })).toBeVisible();
  await shot(
    'after-employee-completed',
    'Atendimento concluído; apenas o resumo deliberadamente publicado será mostrado ao cliente.',
  );
  await hold();
  await auth('customer_a');
  await page.goto('/app/reservas/' + appointmentId);
  await expect(page.getByText(summary, { exact: true })).toBeVisible();
  await expect(page.getByText(privateNote, { exact: true })).toHaveCount(0);
  const detail = await api('/me/appointments/' + appointmentId);
  if (JSON.stringify(detail).includes(privateNote) || detail.appointment.status !== 'COMPLETED')
    throw new Error('Public history privacy/status failed');
  await shot(
    'after-customer-history',
    'O cliente vê o histórico concluído e o resumo público. A nota interna não está no payload.',
  );
  await hold();
  await page.setViewportSize({ width: 320, height: 800 });
  await shot(
    'after-customer-mobile',
    'A mesma reserva a 320 px: conteúdo legível, sem rolagem horizontal nos critérios exercitados.',
  );
  await hold();
  await page.setViewportSize({ width: 1280, height: 900 });
  // A second real booking provides a future impact target, using the ordinary customer API.
  const futureDate = new Date(Date.now() + 2 * 86400000).toISOString().slice(0, 10);
  const free = await api(
    '/me/availability?pet_id=' + pet.id + '&service_id=' + service.id + '&date=' + futureDate,
  );
  if (!free.slots.length) throw new Error('No future demo slot');
  const future = await api('/me/appointments', 'POST', {
    pet_id: pet.id,
    service_id: service.id,
    starts_at: free.slots[0].starts_at,
    offer_version: free.offer.version,
    configuration_version: free.configuration_version,
  });
  await auth('admin');
  await page.goto('/gestao');
  await page.getByRole('heading', { level: 1 }).waitFor();
  await shot(
    'after-admin-management',
    'Administrador consulta indicadores derivados dos dados. Métricas da demo não representam uma loja real.',
  );
  await hold();
  settings = await api('/operations/calendar');
  const originalVersion = settings.configuration.version;
  await page.goto('/operacao/configuracoes');
  await page.getByRole('button', { name: 'Configurar expediente e regras', exact: true }).click();
  await page.getByRole('button', { name: 'Adicionar data especial', exact: true }).click();
  const index = settings.configuration.calendar.exceptions.length + 1;
  await page
    .getByLabel('Data especial ' + index + ' (obrigatório)', { exact: true })
    .fill(futureDate);
  await page.getByRole('button', { name: 'Conferir impacto', exact: true }).click();
  await expect(page.getByText('1 reserva(s) seriam afetadas', { exact: true })).toBeVisible();
  await shot(
    'after-admin-impact',
    'Fechar o dia com reserva futura revela impacto e bloqueia salvar. A reserva existente continua válida.',
  );
  await hold(9000);
  const unchanged = await api('/operations/calendar');
  if (unchanged.configuration.version !== originalVersion)
    throw new Error('Impact preview mutated configuration');
  const preserved = await api('/operations/attendances/' + future.id);
  if (preserved.item.appointment.status !== 'BOOKED') throw new Error('Future appointment changed');
  await page.goto('/gestao/auditoria');
  await page.getByRole('heading', { level: 1 }).waitFor();
  await shot(
    'after-admin-audit',
    'Eventos rastreáveis. Backup restaurado em 23 tabelas na P07; publicação externa e aceite humano seguem pendentes.',
  );
  const remaining = Math.max(0, 185000 - (performance.now() - started));
  await hold(Math.min(remaining, 60000));
  if (errors.length) throw new Error('Browser execution errors: ' + errors.join(','));
  const duration = elapsed();
  await context.close();
  await video.saveAs(resolve(output, 'petland-3.0-demo.webm'));
  await writeFile(
    resolve(output, 'capture.json'),
    JSON.stringify(
      {
        captured_at: new Date().toISOString(),
        version: '3.0.0-rc.1',
        origin,
        database: active,
        synthetic: true,
        preparation:
          'Ordinary API: synthetic five-minute service, minute steps and full-day exception; passwords never filmed. Future impact target booked by customer API.',
        fake_clock: false,
        stories: [
          'customer: create pet, review and confirm',
          'employee: arrive, private note, start and complete',
          'customer: public history without private note',
          'admin: indicators, non-mutating blocked impact and audit',
        ],
        duration_seconds: duration,
        appointment_id: appointmentId,
        future_appointment_id: future.id,
        chapters,
        checks,
        errors,
        passed: true,
      },
      null,
      2,
    ),
  );
  const stamp = (value) => new Date(Math.round(value * 1000)).toISOString().slice(11, 23);
  const vtt =
    'WEBVTT\n\n' +
    chapters
      .map(
        (chapter, i) =>
          `${i + 1}\n${stamp(chapter.at_seconds)} --> ${stamp(chapters[i + 1]?.at_seconds ?? duration)}\n${chapter.caption}\n`,
      )
      .join('\n');
  await writeFile(resolve(output, 'petland-3.0-demo.vtt'), vtt);
  console.log('Three real journeys recorded and verified; duration ' + duration + ' seconds.');
} finally {
  await context.close();
  await browser.close();
}
