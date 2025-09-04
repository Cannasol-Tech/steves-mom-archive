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

test.describe('Model Selection', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForHealth(page);
  });

  test('displays model selector with default options', async ({ page }) => {
    // Find the model selector
    const modelSelector = page.locator('select').first();
    await expect(modelSelector).toBeVisible();
    
    // Check default options are available
    await modelSelector.click();
    await expect(page.getByRole('option', { name: /grok-3-mini \(proxy\)/i })).toBeVisible();
    await expect(page.getByRole('option', { name: /gpt-4o-mini \(AOAI\)/i })).toBeVisible();
    await expect(page.getByRole('option', { name: /local \(llama3\.1:8b\)/i })).toBeVisible();
  });

  test('changes model selection', async ({ page }) => {
    const modelSelector = page.locator('select').first();
    
    // Check initial selection (should be first option)
    await expect(modelSelector).toHaveValue('grok-3-mini (proxy)');
    
    // Change to different model
    await modelSelector.selectOption('gpt-4o-mini (AOAI)');
    await expect(modelSelector).toHaveValue('gpt-4o-mini (AOAI)');
    
    // Change to local model
    await modelSelector.selectOption('local (llama3.1:8b)');
    await expect(modelSelector).toHaveValue('local (llama3.1:8b)');
  });

  test('model selection persists during chat session', async ({ page }) => {
    const modelSelector = page.locator('select').first();
    const input = page.getByPlaceholder('Ask anything…');
    
    // Change to local model
    await modelSelector.selectOption('local (llama3.1:8b)');
    await expect(modelSelector).toHaveValue('local (llama3.1:8b)');
    
    // Send a message
    await input.fill('Test message');
    await page.getByRole('button', { name: 'Send' }).click();
    
    // Wait for response to start
    await expect(page.getByText('Test message')).toBeVisible();
    
    // Model selection should still be the same
    await expect(modelSelector).toHaveValue('local (llama3.1:8b)');
  });

  test('model selector is accessible', async ({ page }) => {
    const modelSelector = page.locator('select').first();
    
    // Should be focusable
    await modelSelector.focus();
    await expect(modelSelector).toBeFocused();
    
    // Should be navigable with keyboard
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('Enter');
    
    // Should have proper ARIA attributes
    await expect(modelSelector).toHaveAttribute('aria-label', 'Select AI model');
  });

  test('model selector visual styling', async ({ page }) => {
    // Check that the model selector has the expected visual elements
    const modelContainer = page.locator('div').filter({ hasText: /Model/ }).first();
    await expect(modelContainer).toBeVisible();
    
    // Should have AI icon
    const aiIcon = page.locator('span').filter({ hasText: 'AI' }).first();
    await expect(aiIcon).toBeVisible();
    
    // Should have chevron icon
    const chevron = page.locator('svg[viewBox="0 0 20 20"]');
    await expect(chevron).toBeVisible();
  });

  test('model selection affects chat requests', async ({ page }) => {
    let lastRequestModel = '';
    
    // Intercept chat API requests to check model parameter
    await page.route('/api/chat', async (route) => {
      const request = route.request();
      const postData = request.postData();
      if (postData) {
        const data = JSON.parse(postData);
        lastRequestModel = data.model || '';
      }
      
      // Return a mock response
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          response: 'Mock response',
          reasoning: 'Mock reasoning'
        })
      });
    });
    
    const modelSelector = page.locator('select').first();
    const input = page.getByPlaceholder('Ask anything…');
    
    // Test with default model
    await input.fill('Test with default model');
    await page.getByRole('button', { name: 'Send' }).click();
    await page.waitForTimeout(500); // Wait for request
    expect(lastRequestModel).toBe('grok-3-mini (proxy)');
    
    // Clear input for next test
    await input.clear();
    
    // Change model and test again
    await modelSelector.selectOption('gpt-4o-mini (AOAI)');
    await input.fill('Test with AOAI model');
    await page.getByRole('button', { name: 'Send' }).click();
    await page.waitForTimeout(500); // Wait for request
    expect(lastRequestModel).toBe('gpt-4o-mini (AOAI)');
  });

  test('model selector works in different themes', async ({ page }) => {
    const modelSelector = page.locator('select').first();
    
    // Test in dark theme (default)
    await expect(page.locator('html')).toHaveClass(/dark/);
    await expect(modelSelector).toBeVisible();
    
    // Switch to light theme
    const themeToggle = page.getByRole('button', { name: /toggle theme/i });
    await themeToggle.click();
    await expect(page.locator('html')).toHaveClass(/light/);
    
    // Model selector should still be visible and functional
    await expect(modelSelector).toBeVisible();
    await modelSelector.selectOption('local (llama3.1:8b)');
    await expect(modelSelector).toHaveValue('local (llama3.1:8b)');
  });
});
