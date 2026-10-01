// Read-only verification of the public local case, media and chapter controls.
import { spawn } from 'node:child_process';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { chromium, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const root = fileURLToPath(new URL('../../../', import.meta.url));
const publicRoot = resolve(root, 'docs/case');
const capture = JSON.parse(await readFile(resolve(publicRoot, 'media/capture.json'), 'utf8'));
const server = spawn('python', [resolve(root, 'scripts/portfolio_preview.py'), '--port', '0'], {
  cwd: root,
  stdio: ['ignore', 'pipe', 'ignore'],
});
server.stdout.setEncoding('utf8');
const origin = await new Promise((done, reject) => {
  const timeout = setTimeout(() => {
    server.kill();
    reject(new Error('Local case preview did not start'));
  }, 10000);
  let content = '';
  server.on('error', reject);
  server.stdout.on('data', (chunk) => {
    content += chunk;
    const match = content.match(/http:\/\/127\.0\.0\.1:\d+/);
    if (match) {
      clearTimeout(timeout);
      done(match[0]);
    }
  });
});
const browser = await chromium.launch();
const results = [];
try {
  for (const width of [1280, 320]) {
    const context = await browser.newContext({ viewport: { width, height: 900 } });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.name));
    await page.goto(origin);
    await page.getByRole('heading', { level: 1 }).waitFor();
    await expect(page.locator('.chapter')).toHaveCount(capture.chapters.length);
    const links = await page
      .locator('a[href], source[src], track[src], img[src]')
      .evaluateAll((elements) =>
        elements.map((el) => el.getAttribute('href') ?? el.getAttribute('src')),
      );
    for (const link of new Set(links)) {
      if (link.startsWith('#')) {
        await expect(page.locator(link)).toHaveCount(1);
      } else if (!link.startsWith('https://')) {
        expect((await page.request.head(new URL(link, origin).href)).status()).toBe(200);
      }
    }
    const video = page.locator('video');
    await expect
      .poll(() => video.evaluate((element) => Number.isFinite(element.duration)))
      .toBe(true);
    const media = await video.evaluate((element) => ({
      duration: element.duration,
      captions: element.textTracks[0]?.mode,
    }));
    expect(Math.abs(media.duration - capture.duration_seconds)).toBeLessThan(1);
    expect(media.captions).toBe('showing');
    for (const chapter of [capture.chapters[0], capture.chapters[7], capture.chapters[12]]) {
      await page
        .getByRole('button', {
          name: new RegExp(chapter.caption.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')),
        })
        .click();
      await expect
        .poll(() => video.evaluate((element) => element.currentTime))
        .toBeCloseTo(chapter.at_seconds, 0);
      await expect
        .poll(() => page.locator('track').evaluate((element) => element.track.cues?.length))
        .toBe(capture.chapters.length);
    }
    const violations = (
      await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'])
        .analyze()
    ).violations.map((v) => v.id);
    const reflow = await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth);
    expect(violations).toEqual([]);
    expect(errors).toEqual([]);
    expect(reflow).toBe(true);
    results.push({
      width,
      local_links: true,
      video_duration: media.duration,
      captions: media.captions,
      chapter_seek: true,
      axe_violations: violations,
      errors,
      reflow,
    });
    await context.close();
  }
} finally {
  await browser.close();
  await new Promise((done) => {
    server.once('exit', done);
    server.kill();
  });
}
await mkdir(resolve(root, '.local/p08'), { recursive: true });
await writeFile(
  resolve(root, '.local/p08/player-verification.json'),
  JSON.stringify({ passed: true, results }, null, 2),
);
console.log(
  'Portfolio player: 1280/320px, local links, duration, captions, chapters and axe passed.',
);
