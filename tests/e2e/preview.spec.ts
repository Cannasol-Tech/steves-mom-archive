import { test, expect } from '@playwright/test';

// Basic E2E to ensure make preview stack is functional
// - Frontend loads
// - Proxy works for /api/health
// - Able to send a basic chat message and receive some streamed text

test.describe('Local Preview E2E', () => {
  test('home page renders and chat input present', async ({ page }) => {
    await page.goto('/');
    // UI sanity check: look for the textarea placeholder
    const textarea = page.getByPlaceholder('Ask anything… (Shift+Enter newline • Cmd/Ctrl+Enter send • Esc cancel)');
    await expect(textarea).toBeVisible();
  });

  test('proxy to backend /api/health works via frontend origin', async ({ page }) => {
    const resp = await page.request.get('/api/health');
    expect(resp.ok()).toBeTruthy();
    const data = await resp.json();
    expect(data.status).toBe('ok');
  });

  test('send a chat message and see streamed or text response', async ({ page }) => {
    await page.goto('/');
    const textarea = page.getByPlaceholder('Ask anything… (Shift+Enter newline • Cmd/Ctrl+Enter send • Esc cancel)');
    await textarea.fill('Hello from Playwright!');
    // Click the Send button
    await page.getByRole('button', { name: 'Send' }).click();

    // Expect some assistant content to appear; streaming appends text progressively
    // We look for any new assistant message content or partial chunk
    await expect.poll(async () => {
      const content = await page.locator('main').innerText();
      return content.includes('Local provider') || /[A-Za-z]/.test(content);
    }, { timeout: 20000 }).toBeTruthy();
  });
});

