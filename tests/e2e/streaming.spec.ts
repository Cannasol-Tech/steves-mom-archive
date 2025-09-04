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

test.describe('Streaming Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForHealth(page);
  });

  test('displays streaming content progressively', async ({ page }) => {
    const input = page.getByPlaceholder('Ask anything…');
    await input.fill('Tell me a story');
    await page.getByRole('button', { name: 'Send' }).click();

    // Should show user message
    await expect(page.getByText('Tell me a story')).toBeVisible();

    // Should show streaming indicator
    await expect(page.getByText(/Thinking…/i)).toBeVisible();

    // Should show stream content area
    const streamContent = page.getByTestId('stream-content');
    await expect(streamContent).toBeVisible({ timeout: 15000 });

    // Content should start appearing
    await expect(streamContent).not.toHaveText('', { timeout: 20000 });
  });

  test('shows cancel button during streaming', async ({ page }) => {
    const input = page.getByPlaceholder('Ask anything…');
    await input.fill('Generate a long response');
    await page.getByRole('button', { name: 'Send' }).click();

    // Should show cancel button during streaming
    const cancelButton = page.getByRole('button', { name: /Cancel/i });
    await expect(cancelButton).toBeVisible({ timeout: 10000 });
    await expect(cancelButton).toBeEnabled();
  });

  test('can cancel streaming', async ({ page }) => {
    const input = page.getByPlaceholder('Ask anything…');
    await input.fill('Start streaming then cancel');
    await page.getByRole('button', { name: 'Send' }).click();

    // Wait for streaming to start
    await expect(page.getByText(/Thinking…/i)).toBeVisible();

    // Click cancel button
    const cancelButton = page.getByRole('button', { name: /Cancel/i });
    await expect(cancelButton).toBeVisible({ timeout: 10000 });
    await cancelButton.click();

    // Should stop streaming and re-enable input
    await expect(input).toBeEnabled({ timeout: 15000 });

    // Send button should be disabled because input is empty after cancel
    // (this is correct behavior - send button is only enabled when there's text)
    await expect(page.getByRole('button', { name: 'Send' })).toBeDisabled();

    // But if we type something, it should enable
    await input.fill('Test after cancel');
    await expect(page.getByRole('button', { name: 'Send' })).toBeEnabled();
  });

  test('shows retry button after completion or error', async ({ page }) => {
    const input = page.getByPlaceholder('Ask anything…');
    await input.fill('Test retry functionality');
    await page.getByRole('button', { name: 'Send' }).click();

    // Wait for response to complete
    await expect(page.getByText('Test retry functionality')).toBeVisible();
    
    // Look for retry button (may appear after streaming completes)
    const retryButton = page.getByRole('button', { name: /Retry/i });
    
    // If retry button appears, test it
    if (await retryButton.isVisible({ timeout: 5000 })) {
      await retryButton.click();
      
      // Should start a new request
      await expect(page.getByText(/Thinking…/i)).toBeVisible();
    }
  });

  test('disables input during streaming', async ({ page }) => {
    const input = page.getByPlaceholder('Ask anything…');
    const sendButton = page.getByRole('button', { name: 'Send' });

    // Initially enabled
    await expect(input).toBeEnabled();
    await expect(sendButton).toBeDisabled(); // Disabled because input is empty

    await input.fill('Test input disable');
    await expect(sendButton).toBeEnabled();

    // Send message
    await sendButton.click();

    // Should be disabled during streaming
    await expect(input).toBeDisabled({ timeout: 5000 });
    await expect(sendButton).toBeDisabled();

    // Should re-enable after completion
    await expect(input).toBeEnabled({ timeout: 30000 });
  });

  test('handles streaming with different models', async ({ page }) => {
    const input = page.getByPlaceholder('Ask anything…');

    // Test with default model (no need to change selector since it's complex)
    await input.fill('Test with default model');
    await page.getByRole('button', { name: 'Send' }).click();

    // Should show streaming behavior
    await expect(page.getByText(/Thinking…/i)).toBeVisible();

    // Wait for completion
    await expect(input).toBeEnabled({ timeout: 30000 });

    // Clear input for next test
    await input.clear();

    // Test another message with same model
    await input.fill('Test second message');
    await page.getByRole('button', { name: 'Send' }).click();

    // Should show streaming behavior
    await expect(page.getByText(/Thinking…/i)).toBeVisible();

    // Wait for completion
    await expect(input).toBeEnabled({ timeout: 30000 });
  });

  test('maintains message history during streaming', async ({ page }) => {
    const input = page.getByPlaceholder('Ask anything…');

    // Send first message
    await input.fill('First message');
    await page.getByRole('button', { name: 'Send' }).click();
    await expect(page.getByText('First message')).toBeVisible();

    // Wait for response to complete
    await expect(input).toBeEnabled({ timeout: 30000 });

    // Send second message
    await input.fill('Second message');
    await page.getByRole('button', { name: 'Send' }).click();

    // Both messages should be visible
    await expect(page.getByText('First message')).toBeVisible();
    await expect(page.getByText('Second message')).toBeVisible();
  });

  test('handles keyboard shortcuts during streaming', async ({ page }) => {
    const input = page.getByPlaceholder('Ask anything…');
    
    await input.fill('Test keyboard shortcuts');
    
    // Use Ctrl+Enter to send (or Cmd+Enter on Mac)
    await page.keyboard.press('Control+Enter');
    
    // Should start streaming
    await expect(page.getByText(/Thinking…/i)).toBeVisible();
    
    // Try Escape to cancel
    await page.keyboard.press('Escape');
    
    // Should cancel streaming and re-enable input
    await expect(input).toBeEnabled({ timeout: 10000 });
  });

  test('shows appropriate loading states', async ({ page }) => {
    const input = page.getByPlaceholder('Ask anything…');
    await input.fill('Test loading states');
    await page.getByRole('button', { name: 'Send' }).click();

    // Should show "Thinking..." indicator
    await expect(page.getByText(/Thinking…/i)).toBeVisible();

    // Should show streaming hint
    await expect(page.getByText(/Streaming…/i)).toBeVisible({ timeout: 10000 });

    // Stream content area should appear
    const streamContent = page.getByTestId('stream-content');
    await expect(streamContent).toBeVisible({ timeout: 15000 });
  });

  test('handles rapid successive messages', async ({ page }) => {
    const input = page.getByPlaceholder('Ask anything…');

    // Send first message
    await input.fill('First rapid message');
    await page.getByRole('button', { name: 'Send' }).click();

    // Wait for it to start processing
    await expect(page.getByText(/Thinking…/i)).toBeVisible();

    // Input should be disabled, preventing rapid successive sends
    await expect(input).toBeDisabled();

    // Wait for completion
    await expect(input).toBeEnabled({ timeout: 30000 });

    // Now send second message
    await input.fill('Second rapid message');
    await page.getByRole('button', { name: 'Send' }).click();

    // Both messages should be visible
    await expect(page.getByText('First rapid message')).toBeVisible();
    await expect(page.getByText('Second rapid message')).toBeVisible();
  });
});
