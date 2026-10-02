// RNF03 lab measurement against `pnpm preview --port 4173` after a production build.
import { readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium, devices } from '@playwright/test';

const baseURL = process.env.PERF_WEB_URL ?? 'http://127.0.0.1:4173';
if (!['127.0.0.1', 'localhost'].includes(new URL(baseURL).hostname)) {
  throw new Error('Only a local build preview may be measured.');
}
const root = fileURLToPath(new URL('../../../', import.meta.url));
const library = await readFile(
  resolve(dirname(fileURLToPath(import.meta.resolve('web-vitals'))), 'web-vitals.iife.js'),
  'utf8',
);
const browser = await chromium.launch();
const samples = [];
try {
  for (const route of ['/', '/entrar', '/servicos']) {
    for (let run = 1; run <= 3; run++) {
      const context = await browser.newContext({ ...devices['Pixel 7'], baseURL });
      const page = await context.newPage();
      const errors = [];
      const consoleErrors = [];
      const guestAuthResponses = [];
      const guestURL = new URL('/api/v1/auth/me', baseURL).href;
      page.on('pageerror', (error) => errors.push(error.message));
      page.on('console', (message) => {
        if (message.type() === 'error')
          consoleErrors.push({ text: message.text(), url: message.location().url });
      });
      page.on('response', (response) => {
        if (
          response.url() === guestURL &&
          response.status() === 401 &&
          response.request().method() === 'GET'
        )
          guestAuthResponses.push(response.url());
      });
      await page.addInitScript({
        content:
          library +
          `
        window.__vitals = {};
        window.__policyViolations = [];
        window.__shifts = [];
        window.__interactions = [];
        new PerformanceObserver(list => {
          for (const entry of list.getEntries()) if (!entry.hadRecentInput) {
            window.__shifts.push({ value: entry.value, sources: entry.sources.map(s => ({node:s.node?.outerHTML?.slice(0,160), previous:s.previousRect.toJSON(), current:s.currentRect.toJSON()})) });
          }
        }).observe({type:'layout-shift', buffered:true});
        document.addEventListener('securitypolicyviolation', e => window.__policyViolations.push({directive: e.violatedDirective, blocked: e.blockedURI, source: e.sourceFile, line: e.lineNumber}));
        for (const name of ['LCP', 'INP', 'CLS']) {
          webVitals['on' + name](metric => {
            window.__vitals[name] = metric.value;
            if (name === 'INP') window.__interactions = metric.entries.map(e => ({name:e.name, target:e.target?.outerHTML?.slice(0,160), start:e.startTime, duration:e.duration, input_delay:e.processingStart-e.startTime, processing:e.processingEnd-e.processingStart, presentation:e.startTime+e.duration-e.processingEnd}));
          }, { reportAllChanges: true });
        }
      `,
      });
      const cdp = await context.newCDPSession(page);
      await cdp.send('Network.enable');
      await cdp.send('Network.setCacheDisabled', { cacheDisabled: true });
      await cdp.send('Network.emulateNetworkConditions', {
        offline: false,
        latency: 150,
        downloadThroughput: 1_600_000 / 8,
        uploadThroughput: 750_000 / 8,
      });
      await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
      const response = await page.goto(route, { waitUntil: 'networkidle' });
      if (
        !response.ok() ||
        response.headers()['content-security-policy'].includes("script-src 'self' 'unsafe-inline'")
      ) {
        throw new Error('Use the production preview with its strict script policy.');
      }
      await page.getByRole('heading', { level: 1 }).waitFor();
      if (route === '/servicos') {
        await page.getByLabel('Espécie', { exact: true }).focus();
        await page.keyboard.press('ArrowDown');
        await page.keyboard.press('Enter');
        await page.getByLabel('Porte', { exact: true }).focus();
        await page.keyboard.press('ArrowDown');
        await page.keyboard.press('Enter');
      } else {
        if (route === '/')
          await page.getByRole('link', { name: 'Já tenho uma conta', exact: true }).click();
        await page
          .getByLabel('E-mail (obrigatório)', { exact: true })
          .pressSequentially('synthetic@example.com');
        await page.getByRole('button', { name: 'Entrar', exact: true }).click();
        await page.getByText('Informe sua senha.').waitFor();
      }
      await page.waitForTimeout(1200); // Finish the observer's interaction reporting window.
      // Flush final values via the documented visibility lifecycle, without unloading the document.
      const foreground = await context.newPage();
      await foreground.bringToFront();
      const values = await page.evaluate(() => ({
        ...window.__vitals,
        violations: window.__policyViolations,
        shifts: window.__shifts,
        interactions: window.__interactions,
      }));
      let expectedGuestAuth401 = 0;
      for (const error of consoleErrors) {
        // The public account link probes a real session; unauthenticated visitors get 401.
        // Pair only this exact GET response with its browser console entry. All other
        // console errors, including a 401 from any other endpoint, still fail the sample.
        if (
          error.url === guestURL &&
          error.text ===
            'Failed to load resource: the server responded with a status of 401 (Unauthorized)' &&
          expectedGuestAuth401 < guestAuthResponses.length
        )
          expectedGuestAuth401++;
        else errors.push(error.text);
      }
      const result = {
        route,
        run,
        ...values,
        errors,
        expected_guest_auth_401: expectedGuestAuth401,
        passed:
          Number.isFinite(values.LCP) &&
          Number.isFinite(values.INP) &&
          Number.isFinite(values.CLS) &&
          values.LCP <= 2500 &&
          values.INP <= 200 &&
          values.CLS <= 0.1 &&
          errors.length === 0 &&
          values.violations.length === 0,
      };
      samples.push(result);
      console.log(JSON.stringify(result));
      await context.close();
    }
  }
} finally {
  await browser.close();
}
const report = {
  measured_at: new Date().toISOString(),
  browser: 'Playwright Chromium',
  browser_version: browser.version(),
  web_vitals: '6.2.2',
  method:
    'Production build, Pixel 7 viewport, cold cache per run, 4x CPU slowdown, 150ms latency, 1.6Mbps down/750kbps up. Three runs per entry page. Real keyboard/click interactions; INP is limited to these lab interactions, not field data. No authentication submissions or writes.',
  samples,
  passed: samples.every((sample) => sample.passed),
};
await writeFile(
  resolve(root, '.local-p06-web-benchmark.json'),
  JSON.stringify(report, null, 2) + '\n',
);
if (!report.passed) process.exitCode = 1;
