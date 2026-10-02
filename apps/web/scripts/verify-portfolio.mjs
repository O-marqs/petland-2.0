// Actual public players: current final + preserved historical P08, with range-aware media.
import { spawn } from 'node:child_process';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { chromium, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
const root = fileURLToPath(new URL('../../../', import.meta.url));
const publicRoot = resolve(root, 'docs/case');
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
  for (const [route, metadata] of [
    ['/', 'media/final/capture.json'],
    ['/historical-p08.html', 'media/capture.json'],
  ]) {
    const capture = JSON.parse(await readFile(resolve(publicRoot, metadata), 'utf8'));
    for (const width of [1280, 320]) {
      const context = await browser.newContext({ viewport: { width, height: 900 } });
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', (error) => errors.push(error.name));
      await page.goto(origin + route);
      await page.getByRole('heading', { level: 1 }).waitFor();
      await page.evaluate(() => document.fonts.ready);
      await expect(page.locator('.chapter')).toHaveCount(capture.chapters.length);
      const links = await page
        .locator('a[href], source[src], track[src], img[src], link[rel="stylesheet"]')
        .evaluateAll((elements) =>
          elements.map((el) => el.getAttribute('href') ?? el.getAttribute('src')),
        );
      for (const link of new Set(links)) {
        if (link.startsWith('#')) await expect(page.locator(link)).toHaveCount(1);
        else if (!link.startsWith('https://'))
          expect((await page.request.head(new URL(link, origin + route).href)).status()).toBe(200);
      }
      const video = page.locator('video');
      await expect.poll(() => video.evaluate((el) => Number.isFinite(el.duration))).toBe(true);
      const media = await video.evaluate((el) => ({
        duration: el.duration,
        captions: el.textTracks[0]?.mode,
        src: el.currentSrc,
      }));
      expect(Math.abs(media.duration - capture.duration_seconds)).toBeLessThan(1);
      expect(media.captions).toBe('showing');
      const range = await page.request.get(media.src, { headers: { Range: 'bytes=0-99' } });
      expect(range.status()).toBe(206);
      expect(range.headers()['content-range']).toMatch(/^bytes 0-99\//);
      expect((await range.body()).length).toBe(100);
      for (const [index, chapter] of capture.chapters.entries()) {
        const button = page.locator('.chapter').nth(index);
        await expect(button).toHaveAccessibleName(
          new RegExp(chapter.caption.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')),
        );
        await button.click();
        await expect
          .poll(() => video.evaluate((el) => el.currentTime))
          .toBeCloseTo(chapter.at_seconds, 0);
        await expect
          .poll(() => video.evaluate((el) => !el.seeking && el.readyState >= 2))
          .toBe(true);
        await expect
          .poll(() => page.locator('track').evaluate((el) => el.track.cues?.length))
          .toBe(capture.chapters.length);
        if (route === '/') {
          await expect
            .poll(() =>
              video.evaluate((el) =>
                [...(el.textTracks[0].activeCues ?? [])].map((cue) => cue.text),
              ),
            )
            .toEqual([chapter.caption]);
        }
      }
      if (route === '/') {
        await page.getByText('Ler a jornada sem reproduzir o vídeo', { exact: true }).click();
        await expect(page.locator('#transcript-inline li')).toHaveCount(capture.chapters.length);
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
      if (route === '/') {
        await mkdir(resolve(root, '.local/final-case/player'), { recursive: true });
        await video.evaluate((el) => {
          el.currentTime = 0;
        });
        await page.locator('details').evaluate((el) => {
          el.open = false;
        });
        await page.screenshot({
          path: resolve(root, '.local/final-case/player', 'player-' + width + '.png'),
          fullPage: true,
        });
      }
      results.push({
        route,
        width,
        local_links: true,
        range_206: true,
        video_duration: media.duration,
        captions: media.captions,
        chapter_seek_count: capture.chapters.length,
        axe_violations: violations,
        errors,
        reflow,
      });
      await context.close();
    }
  }
} finally {
  await browser.close();
  await new Promise((done) => {
    server.once('exit', done);
    server.kill();
  });
}
await mkdir(resolve(root, '.local/final-case'), { recursive: true });
await writeFile(
  resolve(root, '.local/final-case/player-verification.json'),
  JSON.stringify({ passed: true, results }, null, 2) + '\n',
);
console.log(
  'Final + historical players: 1280/320px, local links/ranges, all chapter seeks, captions, transcript, axe/reflow and no JS errors passed.',
);
