import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { expect, test, type APIRequestContext, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { staffCare } from './care-helpers';
import { keyboardAndSemantics } from './hardening-helpers';

// Synthetic, local-only demonstration identities. Never a production seed/default credential.
const password = 'Passeio sintético no parque 2026!';
const newPassword = 'Um novo passeio sintético 2026!';
const mailbox = process.env.MAILPIT_URL ?? 'http://127.0.0.1:8025';
const root = fileURLToPath(new URL('../../../../', import.meta.url));
const adminEmail = process.env.E2E_ADMIN_EMAIL ?? 'p02-admin-sintetico@example.com';
const adminPassword = process.env.E2E_ADMIN_PASSWORD ?? password;

test.beforeEach(async ({ baseURL }) => {
  for (const url of [baseURL!, mailbox]) expect(['localhost', '127.0.0.1']).toContain(new URL(url).hostname);
});

async function emailLink(request: APIRequestContext, email: string, subject: string) {
  let id = '';
  await expect.poll(async () => {
    const response = await request.get(`${mailbox}/api/v1/search`, { params: { query: `to:${email}` } });
    const data = await response.json();
    id = data.messages?.find((message: { Subject: string; ID: string }) => message.Subject.includes(subject))?.ID ?? '';
    return id;
  }, { timeout: 15000 }).not.toBe('');
  const message = await (await request.get(`${mailbox}/api/v1/message/${id}`)).json();
  const url = message.Text.match(/http:\/\/localhost:5173\/[^\s]+/)?.[0];
  expect(url).toBeTruthy();
  const parsed = new URL(url);
  return parsed.pathname + parsed.hash;
}

async function login(page: Page, email: string, secret = password) {
  await page.goto('/entrar');
  await page.getByLabel('E-mail (obrigatório)', { exact: true }).fill(email);
  await page.getByLabel('Senha (obrigatório)', { exact: true }).fill(secret);
  await page.getByRole('button', { name: 'Entrar', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Sair', exact: true })).toBeVisible();
}

async function accessibility(page: Page) {
  expect((await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze()).violations).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
}

test('customer signs up, verifies actual SMTP message, logs in, recovers and revokes access', async ({ page, request }, testInfo) => {
  test.setTimeout(90000);
  const email = `p02-cliente-${testInfo.project.name}-${Date.now()}@example.com`;
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/criar-conta');
  await accessibility(page);
  await page.getByLabel('Seu nome (obrigatório)').fill('Cliente Sintético P02');
  await page.getByLabel('E-mail (obrigatório)', { exact: true }).fill(email);
  await page.getByLabel('Senha (obrigatório)', { exact: true }).fill(password);
  await page.getByLabel('Confirmar senha (obrigatório)').fill(password);
  await page.getByRole('button', { name: 'Criar minha conta' }).click();
  await expect(page.getByText('Pronto para o próximo passo')).toBeVisible();
  await expect(
    page.getByRole('heading', { name: 'Confira seu e-mail para continuar.' }),
  ).toBeFocused();
  await expect(page.getByRole('link', { name: 'Abrir e-mails de teste' })).toHaveAttribute(
    'href',
    'http://127.0.0.1:8025',
  );
  const verification = await emailLink(request, email, 'Confirme');
  await login(page, email);
  await expect(page).toHaveURL(/\/app\/conta$/);
  expect((await page.request.get('/api/v1/me/pets')).status()).toBe(403);
  await page.getByRole('button', { name: 'Já confirmei meu e-mail' }).click();
  await expect(page.getByText('A confirmação ainda está pendente')).toBeVisible();
  // Confirmation in a second tab must unlock the original tab only after a real server refresh.
  const confirmation = await page.context().newPage();
  await confirmation.goto(verification);
  await expect(confirmation).toHaveURL(/verificar-email$/);
  await confirmation.getByRole('button', { name: 'Confirmar e-mail' }).click();
  await expect(confirmation.getByRole('link', { name: 'Continuar para minha área' })).toBeVisible();
  await confirmation.close();
  await page.getByRole('button', { name: 'Já confirmei meu e-mail' }).click();
  await expect(page).toHaveURL(/\/app$/);
  await page.goto('/app/agendar');
  await expect(
    page.getByRole('heading', { name: 'Complete seu cadastro para agendar' }),
  ).toBeVisible();
  await page.getByRole('link', { name: 'Completar meu cadastro', exact: true }).click();
  await page.getByRole('button', { name: 'Salvar cadastro' }).click();
  await page.getByRole('link', { name: 'Ver pets', exact: true }).click();
  await page.getByRole('button', { name: 'Adicionar pet' }).click();
  await page.getByLabel('Nome do pet (obrigatório)').fill('Pet sintético da nova conta');
  await page.getByLabel('Espécie (obrigatório)').selectOption('DOG');
  await page.getByRole('button', { name: 'Salvar pet', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Pet sintético da nova conta', exact: true }),
  ).toBeVisible();
  await page.goto('/servicos');
  await page.getByRole('link', { name: 'Minha área', exact: true }).click();
  await expect(page).toHaveURL(/\/app$/);
  await page.getByRole('link', { name: 'Minha conta', exact: true }).first().click();
  await expect(page.getByText(email, { exact: true })).toBeVisible();
  await keyboardAndSemantics(page, 'customer');
  await expect(page.getByText('Esta sessão', { exact: true })).toBeVisible();
  await accessibility(page);
  expect(await page.evaluate(() => [localStorage.length, sessionStorage.length])).toEqual([0, 0]);
  const cookie = (await page.context().cookies()).find(item => item.name === 'petland_dev_session');
  expect(cookie?.httpOnly).toBe(true);
  expect(cookie?.sameSite).toBe('Lax');
  await page.goto('/gestao/acessos');
  await expect(page.getByRole('heading', { name: 'Acesso indisponível' })).toBeVisible();
  expect((await page.request.get('/api/v1/management/users')).status()).toBe(403);
  await page.getByRole('button', { name: 'Sair', exact: true }).click();
  await page.getByRole('link', { name: 'Esqueci minha senha' }).click();
  // The login form also has an email field; wait for the new route's form to mount.
  await expect(page.getByRole('heading', { name: 'Vamos recuperar seu acesso.', exact: true })).toBeVisible();
  await page.getByLabel('E-mail (obrigatório)').fill(email);
  await expect(page.getByLabel('E-mail (obrigatório)')).toHaveValue(email);
  // Verify the accepted request as well as the account-enumeration-safe UI feedback.
  const recoveryResponse = page.waitForResponse(response => response.url().endsWith('/api/v1/auth/password-reset-requests') && response.request().method() === 'POST', { timeout: 15000 });
  await page.getByRole('button', { name: 'Enviar instruções' }).click();
  expect((await recoveryResponse).status()).toBe(202);
  await expect(page.getByText('Pronto para o próximo passo')).toBeVisible();
  const resetLink = await emailLink(request, email, 'Redefina');
  await page.goto(resetLink);
  await page.getByLabel('Nova senha (obrigatório)').fill(newPassword);
  await page.getByLabel('Confirmar senha (obrigatório)').fill(newPassword);
  await page.getByRole('button', { name: 'Salvar nova senha' }).click();
  await expect(page.getByText('Senha redefinida e sessões encerradas. Entre com a nova senha.')).toBeVisible();
  expect((await page.request.get('/api/v1/auth/me')).status()).toBe(401);
  await page.goto(resetLink);
  await page.getByLabel('Nova senha (obrigatório)', { exact: true }).fill(password);
  await page.getByLabel('Confirmar senha (obrigatório)').fill(password);
  await page.getByRole('button', { name: 'Salvar nova senha' }).click();
  await expect(page.getByText('Este link é inválido, já foi usado ou expirou. Solicite um novo link.')).toBeVisible();
  await login(page, email, newPassword);
  await page.goto('/app/conta');
  await page.getByLabel('Senha atual (obrigatório)').fill(newPassword);
  await page.getByLabel('Nova senha (obrigatório)', { exact: true }).fill(password);
  await page.getByLabel('Confirmar nova senha (obrigatório)').fill(password);
  await page.getByRole('button', { name: 'Alterar senha e sair' }).click();
  await expect(page).toHaveURL(/entrar\?senha=alterada$/);
  await login(page, email);
  await page.goto('/app/conta');
  await page.getByRole('button', { name: 'Encerrar esta sessão' }).click();
  await expect(page).toHaveURL(/entrar$/);
  expect(errors).toEqual([]);
});

test('administrator provisions through email, invites employee, changes roles and disables access', async ({ page, request, browser }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop', 'Provisioning is a singleton; the customer journey runs on both sizes.');
  test.setTimeout(420000); // Includes real-time appointment arrival/start/completion in P05.
  const csrf = await (await request.get('/api/v1/auth/csrf')).json();
  const check = await request.post('/api/v1/auth/login', { headers: { Origin: 'http://localhost:5173', 'X-CSRF-Token': csrf.csrf_token }, data: { email: adminEmail, password: adminPassword } });
  if (check.status() !== 200) {
    execFileSync(process.env.PYTHON ?? 'python', ['scripts/dev.py', 'bootstrap-admin', '--email', adminEmail], { cwd: root, stdio: 'pipe', windowsHide: true });
    await page.goto(await emailLink(request, adminEmail, 'Primeiro acesso'));
    await page.getByLabel('Seu nome (obrigatório)').fill('Admin Sintético P02');
    await page.getByLabel('Senha (obrigatório)', { exact: true }).fill(adminPassword);
    await page.getByRole('button', { name: 'Aceitar convite' }).click();
    await expect(page.getByText('Convite aceito. Entre para acessar sua área.')).toBeVisible();
  }
  await login(page, adminEmail, adminPassword);
  await page.goto('/gestao/acessos');
  await accessibility(page);
  await keyboardAndSemantics(page, 'admin');
  const staffEmail = `p02-equipe-${Date.now()}@example.com`;
  await page.getByLabel('E-mail da pessoa convidada (obrigatório)').fill(staffEmail);
  await page.getByLabel('Sua senha atual (obrigatório)').fill(adminPassword);
  await page.getByRole('button', { name: 'Enviar convite' }).click();
  await expect(page.getByText('Solicitação registrada')).toBeVisible();
  const invitation = await emailLink(request, staffEmail, 'convite');
  const context = await browser.newContext({ baseURL: testInfo.project.use.baseURL ?? 'http://127.0.0.1:5173' });
  const staff = await context.newPage();
  try {
    await staff.goto(invitation);
    await staff.getByLabel('Seu nome (obrigatório)').fill(`Equipe Sintética ${Date.now()}`);
    const staffName = await staff.getByLabel('Seu nome (obrigatório)').inputValue();
    await staff.getByLabel('Senha (obrigatório)', { exact: true }).fill(password);
    await staff.getByRole('button', { name: 'Aceitar convite' }).click();
    await expect(staff.getByText('Convite aceito. Entre para acessar sua área.')).toBeVisible();
    await login(staff, staffEmail);
    await expect(staff).toHaveURL(/operacao$/);
    await keyboardAndSemantics(staff, 'employee');
    expect((await staff.request.get('/api/v1/management/users')).status()).toBe(403);
    await staff.setViewportSize({ width: 390, height: 844 });
    await accessibility(staff);
    await staffCare(staff, request, browser);
    await page.goto('/gestao');
    await expect(page.getByRole('heading', { name: 'Ocupação da agenda', exact: true })).toBeVisible();
    await accessibility(page);
    await page.screenshot({ path: 'test-results/p05-management-desktop.png', fullPage: true });
    await page.goto('/gestao/auditoria');
    await expect(page.getByText('appointment.complete', { exact: true }).first()).toBeVisible();
    await accessibility(page);
    await page.goto('/gestao/acessos');
    await expect(page.getByRole('button', { name: /^Gerenciar / }).first()).toBeVisible();
    await page.getByRole('button', { name: 'Atualizar lista' }).click();
    const target = page.getByRole('button', { name: `Gerenciar ${staffName}`, exact: true });
    // Follow the rendered pagination, including on a local database reused across runs.
    for (let i = 0; i < 50 && !(await target.count()); i++) {
      await page.getByRole('button', { name: 'Próxima', exact: true }).click();
      await expect(page.getByText(`Página ${i + 2}`, { exact: true })).toBeVisible();
    }
    await expect(page.getByRole('button', { name: `Gerenciar ${staffName}` })).toBeVisible();
    await page.getByRole('button', { name: `Gerenciar ${staffName}` }).click();
    await page.getByLabel('Cliente', { exact: true }).check();
    await page.getByLabel('Confirme sua senha de administrador (obrigatório)').fill(adminPassword);
    await page.getByRole('button', { name: 'Salvar perfis' }).click();
    await expect(page.getByRole('heading', { name: `Acesso de ${staffName}` })).toHaveCount(0);
    expect((await staff.request.get('/api/v1/auth/me')).status()).toBe(401);
    await login(staff, staffEmail);
    await expect(staff.getByRole('link', { name: 'Área do cliente' })).toBeVisible();
    await page.getByRole('button', { name: `Gerenciar ${staffName}` }).click();
    await page.getByLabel('Confirme sua senha de administrador (obrigatório)').fill(adminPassword);
    await page.getByRole('button', { name: 'Desativar conta' }).click();
    await expect(page.getByRole('heading', { name: `Acesso de ${staffName}` })).toHaveCount(0);
    expect((await staff.request.get('/api/v1/auth/me')).status()).toBe(401);
  } finally { await context.close(); }
});

test('login, token recovery and account layout reflow at 320px', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 800 });
  for (const path of ['/entrar', '/criar-conta', '/recuperar-acesso', '/verificar-email', '/redefinir-senha', '/aceitar-convite']) {
    await page.goto(path);
    await accessibility(page);
  }
});
