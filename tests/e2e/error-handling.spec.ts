import { test, expect } from '@playwright/test';

test.describe('Error Handling', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('handles chat API errors gracefully', async ({ page }) => {
    // Mock API error response
    await page.route('/api/chat', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' })
      });
    });

    const input = page.getByPlaceholder('Ask anything…');
    await input.fill('This will cause an error');
    await page.getByRole('button', { name: 'Send' }).click();

    // Should show user message
    await expect(page.getByText('This will cause an error')).toBeVisible();

    // Should show error message or toast
    await expect(page.getByText(/error/i)).toBeVisible({ timeout: 10000 });

    // Input should be re-enabled after error
    await expect(input).toBeEnabled();
    await expect(page.getByRole('button', { name: 'Send' })).toBeEnabled();
  });

  test('handles network errors', async ({ page }) => {
    // Simulate network failure
    await page.route('/api/chat', async (route) => {
      await route.abort('failed');
    });

    const input = page.getByPlaceholder('Ask anything…');
    await input.fill('Network error test');
    await page.getByRole('button', { name: 'Send' }).click();

    // Should show user message
    await expect(page.getByText('Network error test')).toBeVisible();

    // Should handle the error gracefully
    await expect(input).toBeEnabled({ timeout: 10000 });
  });

  test('handles health check failures', async ({ page }) => {
    // Mock health check failure
    await page.route('/api/health', async (route) => {
      await route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'error' })
      });
    });

    // Reload page to trigger health check
    await page.reload();

    // App should still load even if health check fails
    await expect(page.getByPlaceholder('Ask anything…')).toBeVisible();
  });

  test('handles malformed API responses', async ({ page }) => {
    // Mock malformed response
    await page.route('/api/chat', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: 'invalid json'
      });
    });

    const input = page.getByPlaceholder('Ask anything…');
    await input.fill('Malformed response test');
    await page.getByRole('button', { name: 'Send' }).click();

    // Should handle parsing error gracefully
    await expect(input).toBeEnabled({ timeout: 10000 });
  });

  test('handles slow API responses with timeout', async ({ page }) => {
    // Mock slow response
    await page.route('/api/chat', async (route) => {
      // Delay response for longer than typical timeout
      await new Promise(resolve => setTimeout(resolve, 30000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ response: 'Slow response' })
      });
    });

    const input = page.getByPlaceholder('Ask anything…');
    await input.fill('Slow response test');
    await page.getByRole('button', { name: 'Send' }).click();

    // Should show loading state
    await expect(page.getByText(/Thinking…/i)).toBeVisible();

    // Should eventually timeout and re-enable input
    await expect(input).toBeEnabled({ timeout: 35000 });
  });

  test('handles WebSocket connection errors', async ({ page }) => {
    // Mock WebSocket connection failure
    await page.addInitScript(() => {
      const originalWebSocket = window.WebSocket;
      window.WebSocket = class extends originalWebSocket {
        constructor(url) {
          super(url);
          // Simulate connection error
          setTimeout(() => {
            this.onerror?.(new Event('error'));
            this.onclose?.(new CloseEvent('close', { code: 1006 }));
          }, 100);
        }
      };
    });

    await page.reload();

    // App should still function without WebSocket
    const input = page.getByPlaceholder('Ask anything…');
    await expect(input).toBeVisible();
    await expect(input).toBeEnabled();
  });

  test('shows retry functionality after errors', async ({ page }) => {
    let requestCount = 0;
    
    // Mock API that fails first time, succeeds second time
    await page.route('/api/chat', async (route) => {
      requestCount++;
      if (requestCount === 1) {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Server error' })
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ response: 'Success after retry' })
        });
      }
    });

    const input = page.getByPlaceholder('Ask anything…');
    await input.fill('Retry test');
    await page.getByRole('button', { name: 'Send' }).click();

    // Should show error first
    await expect(page.getByText(/error/i)).toBeVisible({ timeout: 10000 });

    // Look for retry button and click it
    const retryButton = page.getByRole('button', { name: /retry/i });
    if (await retryButton.isVisible()) {
      await retryButton.click();
      
      // Should succeed on retry
      await expect(page.getByText('Success after retry')).toBeVisible({ timeout: 10000 });
    }
  });

  test('handles empty or invalid input gracefully', async ({ page }) => {
    const input = page.getByPlaceholder('Ask anything…');
    const sendButton = page.getByRole('button', { name: 'Send' });

    // Send button should be disabled for empty input
    await expect(sendButton).toBeDisabled();

    // Try with whitespace only
    await input.fill('   ');
    await expect(sendButton).toBeDisabled();

    // Try with valid input
    await input.fill('Valid input');
    await expect(sendButton).toBeEnabled();

    // Clear input
    await input.clear();
    await expect(sendButton).toBeDisabled();
  });

  test('handles browser back/forward navigation errors', async ({ page }) => {
    // Navigate to different pages
    await page.goto('/admin');
    await expect(page.getByText(/Admin Panel/i)).toBeVisible();

    await page.goto('/tasks');
    await expect(page.getByText(/Task Analytics/i)).toBeVisible();

    // Use browser back button
    await page.goBack();
    await expect(page.getByText(/Admin Panel/i)).toBeVisible();

    // Use browser forward button
    await page.goForward();
    await expect(page.getByText(/Task Analytics/i)).toBeVisible();

    // Navigate to invalid route and back
    await page.goto('/invalid-route');
    await expect(page.getByText(/404/i)).toBeVisible();

    await page.goBack();
    await expect(page.getByText(/Task Analytics/i)).toBeVisible();
  });
});
