// Read-only proof that the filmed single-date roster leaves adjacent dates available.
import { chromium, expect } from '@playwright/test';
import { readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
const root = fileURLToPath(new URL('../../../', import.meta.url));
const fixture = JSON.parse(await readFile(resolve(root, '.local/final-case/fixture.json'), 'utf8'));
expect(fixture.project).toBe('petlandfinalcase');
expect(fixture.origin).toBe('https://localhost:8445');
const capture = JSON.parse(
  await readFile(resolve(root, 'docs/case/media/final/capture.json'), 'utf8'),
);
expect(fixture.database).toBe(capture.database);
const accounts = JSON.parse(
  await readFile(resolve(root, '.local/final-case/staging/accounts.json'), 'utf8'),
);
const browser = await chromium.launch();
try {
  const context = await browser.newContext({ baseURL: fixture.origin, ignoreHTTPSErrors: true });
  const token = (await (await context.request.get('/api/v1/auth/csrf')).json()).csrf_token;
  const response = await context.request.post('/api/v1/auth/login', {
    data: accounts.admin,
    headers: { Origin: fixture.origin, 'X-CSRF-Token': token },
  });
  expect(response.ok()).toBe(true);
  const day = capture.actions.find((a) => a.kind === 'single_date_roster_saved_via_ui').date;
  const days = [-1, 0, 1].map((delta) =>
    new Date(Date.parse(day + 'T12:00:00Z') + delta * 86400000).toISOString().slice(0, 10),
  );
  const rows = [];
  for (const date of days) {
    const response = await context.request.get('/api/v1/operations/roster/' + date);
    expect(response.ok()).toBe(true);
    const roster = await response.json();
    rows.push({
      date,
      working_people: roster.rows.filter((r) => r.windows.length > 0).length,
      resources: roster.rows.map((r) => ({ id: r.resource_id, working: r.windows.length > 0 })),
    });
  }
  expect(rows.map((r) => r.working_people)).toEqual([2, 1, 2]);
  const result = {
    application_commit: capture.application_commit,
    project: fixture.project,
    synthetic: true,
    checked_at: new Date().toISOString(),
    mode: 'read-only verification after capture, own demo only',
    counts: rows,
    passed: true,
  };
  await writeFile(
    resolve(root, '.local/final-case/roster-adjacent.json'),
    JSON.stringify(result, null, 2) + '\n',
  );
  console.log(
    'Actual adjacent-date roster: 2 → 1 → 2; isolated demo, read-only API checks passed.',
  );
} finally {
  await browser.close();
}
