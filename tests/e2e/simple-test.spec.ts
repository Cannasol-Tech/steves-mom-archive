import { test, expect } from '@playwright/test';

test.describe('Simple Test', () => {
  test('can navigate to google', async ({ page }) => {
    await page.goto('https://www.google.com');
    await expect(page.getByRole('button', { name: /Google Search/i })).toBeVisible();
  });
});
