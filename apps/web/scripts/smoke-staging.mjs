// Local synthetic staging only. Never accepts an external origin or account input.
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { chromium } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const root = fileURLToPath(new URL('../../../', import.meta.url));
const local = resolve(root, '.local/staging');
const phase = process.argv[2] ?? 'source';
if (!['source', 'recovery', 'return'].includes(phase)) throw new Error('Invalid rehearsal phase');
const output = resolve(local, 'browser', phase);
await mkdir(output, { recursive: true });
const accounts = JSON.parse(await readFile(resolve(local, 'accounts.json'), 'utf8'));
const browser = await chromium.launch();
const checks = [];
try {
  for (const [profile, route, content] of [
    ['customer_a', '/app/pets', 'Luna demo'],
    ['employee', '/operacao/agenda', 'Agenda da equipe'],
    ['admin', '/gestao/acessos', 'Pessoas e acessos'],
  ]) {
    // Only the locally generated CA is absent from Chromium's trust store.
    // Python smoke verifies that certificate strictly before this UI check.
    const context = await browser.newContext({
      ignoreHTTPSErrors: true,
      viewport: { width: 320, height: 800 },
    });
    const page = await context.newPage();
    const errors = [],
      violations = [];
    page.on('pageerror', (error) => errors.push(error.name));
    await page.addInitScript(() => {
      window.__p07Csp = [];
      document.addEventListener('securitypolicyviolation', (event) =>
        window.__p07Csp.push(event.violatedDirective),
      );
    });
    await page.goto('https://localhost:8443/entrar');
    await page.getByLabel('E-mail (obrigatório)', { exact: true }).fill(accounts[profile].email);
    await page.getByLabel('Senha (obrigatório)', { exact: true }).fill(accounts[profile].password);
    await page.getByRole('button', { name: 'Entrar', exact: true }).click();
    await page.getByRole('button', { name: 'Sair', exact: true }).waitFor();
    await page.goto(`https://localhost:8443${route}`);
    await page.getByRole('heading', { level: 1 }).waitFor();
    // Assert page content rather than a duplicate label in the closed mobile menu.
    await page.getByRole('heading', { name: content, exact: true }).waitFor();
    await page.getByRole('complementary', { name: 'Ambiente de demonstração' }).waitFor();
    await page.waitForLoadState('networkidle');
    violations.push(
      ...(
        await new AxeBuilder({ page })
          .withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'])
          .analyze()
      ).violations.map((v) => v.id),
    );
    const fits = await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth);
    const csp = await page.evaluate(() => window.__p07Csp);
    const cookies = await context.cookies();
    const secure =
      cookies.length > 0 && cookies.every((cookie) => cookie.secure && cookie.httpOnly);
    await page.screenshot({ path: resolve(output, `${profile}.png`) });
    if (!fits || !secure || errors.length || violations.length || csp.length) {
      throw new Error(
        `Staging ${profile}: reflow=${fits}, cookies=${secure}, JS=${errors.length}, axe=${violations.join(',')}, CSP=${csp.join(',')}`,
      );
    }
    checks.push({
      profile,
      route,
      reflow_320: fits,
      secure_httponly_cookies: secure,
      errors,
      violations,
      csp,
    });
    await context.close();
  }
} finally {
  await browser.close();
}
await writeFile(
  resolve(output, 'report.json'),
  JSON.stringify({ phase, browser: 'Chromium', checks, passed: true }, null, 2),
);
console.log(`Static staging browser verified: ${phase}, three profiles, 320px, axe and CSP.`);
