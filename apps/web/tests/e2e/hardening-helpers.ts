import { expect, test, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

/** Keyboard and browser accessibility-tree evidence; not an auditory screen-reader test. */
export async function keyboardAndSemantics(page: Page, profile: string) {
  const viewport = page.viewportSize();
  const heading = page.getByRole('heading', { level: 1 });
  await expect(heading).toBeVisible();
  await expect(heading).toBeFocused();
  expect(await page.title()).toBe(`${(await heading.textContent())?.trim()} · PetLand`);
  const skip = page.getByRole('link', { name: 'Pular para o conteúdo' });
  // Reach the skip link from the automatically focused content using only keyboard keys.
  for (let i = 0; i < 60 && !(await skip.evaluate((el) => el === document.activeElement)); i++) {
    await page.keyboard.press('Shift+Tab');
  }
  await expect(skip).toBeFocused();
  await expect(skip).toBeInViewport();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('main')).toBeFocused();
  await page.keyboard.press('Tab');
  expect(await page.getByRole('main').evaluate((el) => el.contains(document.activeElement))).toBe(
    true,
  );
  await page.setViewportSize({ width: 320, height: 800 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'])
        .analyze()
    ).violations,
  ).toEqual([]);
  await expect(page.getByRole('main')).toHaveCount(1);
  const tree = await page.getByRole('main').ariaSnapshot();
  expect(tree).toContain('heading');
  await expect(skip).not.toBeInViewport();
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
  await page.screenshot({
    path: `test-results/p06-${profile}-${test.info().project.name}-320.png`,
    fullPage: false,
  });
  if (viewport) await page.setViewportSize(viewport);
}
