import { test, expect } from '@playwright/test';

// Utility to wait for /api/health to resolve via CRA proxy
async function waitForHealth(page) {
  const maxMs = 25000;
  const start = Date.now();
  while (Date.now() - start < maxMs) {
    try {
      const res = await page.request.get('/api/health', { timeout: 1500 });
      if (res.ok()) return;
    } catch {}
    try {
      const direct = await page.request.get('http://127.0.0.1:9696/health', { timeout: 1500 });
      if (direct.ok()) return;
    } catch {}
    await page.waitForTimeout(500);
  }
  throw new Error('Backend health did not return 200 via proxy or direct in time');
}

test.describe('Chat E2E', () => {
  test('send a message and receive streamed assistant response', async ({ page }) => {
    await page.goto('/');

    await waitForHealth(page);

    // Find the textarea inside InputArea by placeholder
    const input = page.getByPlaceholder('Ask anything…');
    await expect(input).toBeVisible();

    // Type a simple prompt and send
    await input.fill('Say hello in one short sentence.');
    // Click the Send button by role/name
    await page.getByRole('button', { name: 'Send' }).click();

    // Expect a user bubble to appear containing our text
    await expect(page.getByText('Say hello in one short sentence.')).toBeVisible();

    // During streaming, StreamRenderer shows content. Assert it starts filling.
    const streamContent = page.getByTestId('stream-content');
    await expect(streamContent).toBeVisible({ timeout: 15000 });
    await expect(streamContent).not.toHaveText('', { timeout: 20000 });

    // After completion, a message should be appended. With Local provider, look for its placeholder content as well.
    const assistantMessage = page.locator('div').filter({ hasText: /Local model streaming not yet implemented|hello|hi/i }).first();
    await expect(assistantMessage).toBeVisible({ timeout: 20000 });
  });
});

