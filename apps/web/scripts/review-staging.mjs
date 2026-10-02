import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
const require = createRequire(new URL('../package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;
const root = fileURLToPath(new URL('../../../', import.meta.url));
const phase = 'after';
if (!['before', 'after'].includes(phase)) throw new Error('Invalid phase');
const output = resolve(root, `.local/product-review/${phase}`);
await mkdir(output, { recursive: true });
const accounts = JSON.parse(await readFile(resolve(root, '.local/staging/accounts.json'), 'utf8'));
const browser = await chromium.launch();
const checks = [];
try {
  for (const profile of ['public', 'customer_a', 'employee', 'admin']) {
    const context = await browser.newContext({ ignoreHTTPSErrors: true });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.name));
    if (profile !== 'public') {
      await page.goto('https://localhost:8443/entrar');
      await page.getByLabel('E-mail (obrigatório)', { exact: true }).fill(accounts[profile].email);
      await page
        .getByLabel('Senha (obrigatório)', { exact: true })
        .fill(accounts[profile].password);
      await page.getByRole('button', { name: 'Entrar', exact: true }).click();
      await page.getByRole('button', { name: 'Sair', exact: true }).waitFor();
    }
    const route = {
      public: '/',
      customer_a: '/app',
      employee: '/operacao/agenda',
      admin: '/gestao',
    }[profile];
    for (const width of [1440, 768, 320]) {
      await page.setViewportSize({ width, height: 900 });
      await page.goto('https://localhost:8443' + route);
      await page.getByRole('heading', { level: 1 }).waitFor();
      await page.waitForLoadState('networkidle');
      const violations = (
        await new AxeBuilder({ page })
          .withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'])
          .analyze()
      ).violations.map((v) => ({ id: v.id, nodes: v.nodes.map((n) => n.target) }));
      const fits = await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth);
      await page.screenshot({ path: resolve(output, `${profile}-${width}.png`), fullPage: true });
      checks.push({ profile, route, width, fits, violations, errors: [...errors] });
      if (phase === 'after') {
        expect(fits).toBe(true);
        expect(violations).toEqual([]);
        expect(errors).toEqual([]);
      }
    }
    if (profile !== 'public') {
      const menu = page.getByRole('button', { name: 'Menu da conta', exact: true });
      const navigation = page.getByRole('navigation', { name: 'Áreas da conta', exact: true });
      await expect(menu).toHaveAttribute('aria-expanded', 'false');
      await expect(navigation).toBeHidden();
      await menu.focus();
      await page.keyboard.press('Enter');
      await expect(menu).toHaveAttribute('aria-expanded', 'true');
      await expect(navigation).toBeVisible();
      await page.keyboard.press('Escape');
      await expect(menu).toBeFocused();
      await expect(navigation).toBeHidden();
      await menu.click();
      const destination = {
        customer_a: ['Meus pets', '/app/pets'],
        employee: ['Equipe e horários', '/operacao/configuracoes'],
        admin: ['Auditoria', '/gestao/auditoria'],
      }[profile];
      await navigation.getByRole('link', { name: destination[0], exact: true }).click();
      await expect(page).toHaveURL('https://localhost:8443' + destination[1]);
      await expect(page.getByRole('heading', { level: 1 })).toBeFocused();
      await expect(menu).toHaveAttribute('aria-expanded', 'false');
      await expect(navigation).toBeHidden();
      if (profile !== 'admin')
        await expect(page.locator('a[href="/gestao/acessos"]')).toHaveCount(0);
      await page.reload();
      await page.getByRole('heading', { level: 1 }).waitFor();
      await expect(page.getByRole('link', { name: 'Minha conta', exact: true })).toBeVisible();
      await expect(page.getByRole('navigation', { name: 'Atalhos principais' })).toBeVisible();
      checks.push({
        profile,
        menu_keyboard_escape: true,
        route_closes_menu: true,
        route_focus: true,
        reload: true,
      });
      if (profile === 'employee') {
        const settings = await (
          await page.request.get('https://localhost:8443/api/v1/operations/calendar')
        ).json();
        const mutations = [];
        page.on('request', (request) => {
          if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(request.method()))
            mutations.push(request.method());
        });
        await page.getByRole('button', { name: 'Adicionar pessoa', exact: true }).click();
        await page.getByLabel('Seguir o expediente da loja', { exact: true }).uncheck();
        const weekdays = [
          'Segunda-feira',
          'Terça-feira',
          'Quarta-feira',
          'Quinta-feira',
          'Sexta-feira',
          'Sábado',
          'Domingo',
        ];
        const time = (value) =>
          String(Math.floor(value / 60)).padStart(2, '0') +
          ':' +
          String(value % 60).padStart(2, '0');
        const confirmWeek = async () => {
          for (const day of settings.configuration.calendar.weekly) {
            for (const [index, window] of day.windows.entries()) {
              await expect(
                page.getByLabel(`Início — ${weekdays[day.weekday]} ${index + 1} (obrigatório)`, {
                  exact: true,
                }),
              ).toHaveValue(time(window.start));
            }
          }
        };
        await confirmWeek();
        await page.getByRole('button', { name: 'Adicionar data especial', exact: true }).click();
        await page
          .getByLabel('Data especial 1 (obrigatório)', { exact: true })
          .fill(new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 10));
        await expect(
          page
            .getByRole('group', { name: 'Data especial 1', exact: true })
            .getByText('Fechado', { exact: true }),
        ).toBeVisible();
        await confirmWeek();
        await page.getByRole('button', { name: 'Voltar', exact: true }).click();
        await expect(
          page.getByRole('button', { name: 'Adicionar pessoa', exact: true }),
        ).toBeVisible();
        expect(mutations).toEqual([]);
        checks.push({
          profile,
          single_day_editor_keeps_week: true,
          unsaved_form_no_mutations: true,
        });
      }
    }
    await context.close();
  }
} finally {
  await browser.close();
}
await writeFile(resolve(output, 'report.json'), JSON.stringify(checks, null, 2));
console.log(
  JSON.stringify({
    phase,
    checkpoints: checks.length,
    passed: checks.every(
      (c) =>
        c.single_day_editor_keeps_week ||
        c.menu_keyboard_escape ||
        (c.fits && !c.violations.length && !c.errors.length),
    ),
  }),
);
