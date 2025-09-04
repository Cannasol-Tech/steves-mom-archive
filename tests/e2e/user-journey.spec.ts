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

test.describe('Complete User Journey', () => {
  test('complete user workflow from landing to task completion', async ({ page }) => {
    // Step 1: Landing on the application
    await page.goto('/');
    await waitForHealth(page);
    
    // Verify initial state
    await expect(page.getByText(/Chat with Steve's Mom AI/i)).toBeVisible();
    await expect(page.getByText(/Hello! I'm Steve's Mom AI assistant/i)).toBeVisible();
    
    // Step 2: Explore navigation
    await page.getByRole('link', { name: /Admin/i }).first().click();
    await expect(page).toHaveURL('/admin');
    await expect(page.getByText(/Admin Panel/i)).toBeVisible();
    
    // Check admin features
    await expect(page.getByLabelText(/NL→SQL Queries/i)).toBeChecked();
    await expect(page.getByText(/System Status/i)).toBeVisible();
    
    // Step 3: Visit task analytics
    await page.getByRole('link', { name: /Tasks/i }).first().click();
    await expect(page).toHaveURL('/tasks');
    
    // Mock analytics data
    await page.route('/api/tasks/analytics', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          totalTasks: 50,
          accepted: 40,
          rejected: 5,
          modified: 5
        })
      });
    });
    
    await page.reload();
    await expect(page.getByText(/Task Analytics/i)).toBeVisible();
    await expect(page.getByText('50')).toBeVisible(); // Total tasks
    
    // Step 4: Return to chat and test theme switching
    await page.getByRole('link', { name: /Chat/i }).first().click();
    await expect(page).toHaveURL('/chat');
    
    // Switch to light theme
    const themeToggle = page.getByRole('button', { name: /toggle theme/i });
    await themeToggle.click();
    await expect(page.locator('html')).toHaveClass(/light/);
    
    // Step 5: Test model selection
    const modelSelector = page.getByLabelText(/Select AI model/i);
    await modelSelector.selectOption('gpt-4o-mini (AOAI)');
    await expect(modelSelector).toHaveValue('gpt-4o-mini (AOAI)');
    
    // Step 6: Send a chat message
    const input = page.getByPlaceholder('Ask anything…');
    await input.fill('Help me manage my inventory');
    
    // Mock chat response with task
    await page.route('/api/chat', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          response: 'I can help you with inventory management. Let me create a task: [TASK:inventory-123] Update inventory levels for all products [/TASK]',
          reasoning: 'Created inventory management task'
        })
      });
    });
    
    await page.getByRole('button', { name: 'Send' }).click();
    
    // Verify message appears
    await expect(page.getByText('Help me manage my inventory')).toBeVisible();
    
    // Step 7: Wait for AI response and task
    await expect(page.getByText(/Update inventory levels for all products/i)).toBeVisible({ timeout: 15000 });
    
    // Verify task approval buttons appear
    await expect(page.getByRole('button', { name: /Approve/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Reject/i })).toBeVisible();
    
    // Step 8: Approve the task
    let taskApproved = false;
    await page.route('/api/tasks/inventory-123/approve', async (route) => {
      taskApproved = true;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'approved', message: 'Task approved successfully' })
      });
    });
    
    await page.getByRole('button', { name: /Approve/i }).click();
    
    // Verify approval was called
    await expect.poll(() => taskApproved).toBe(true);
    
    // Step 9: Send follow-up message
    await input.fill('What else can you help me with?');
    
    // Mock follow-up response
    await page.route('/api/chat', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          response: 'I can help with many things including email management, document generation, and data analysis. What would you like to work on next?',
          reasoning: 'Provided capabilities overview'
        })
      });
    });
    
    await page.getByRole('button', { name: 'Send' }).click();
    
    // Verify follow-up response
    await expect(page.getByText(/I can help with many things/i)).toBeVisible({ timeout: 15000 });
    
    // Step 10: Test accessibility features
    // Navigate using keyboard
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    // Verify focus management
    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeVisible();
    
    // Step 11: Test error handling
    await input.fill('Trigger an error');
    
    // Mock error response
    await page.route('/api/chat', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' })
      });
    });
    
    await page.getByRole('button', { name: 'Send' }).click();
    
    // Verify error is handled gracefully
    await expect(page.getByText(/error/i)).toBeVisible({ timeout: 10000 });
    await expect(input).toBeEnabled({ timeout: 5000 });
    
    // Step 12: Test mobile responsiveness
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Verify mobile layout
    await expect(page.getByPlaceholder('Ask anything…')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Send' })).toBeVisible();
    
    // Test mobile navigation
    const mobileMenuButton = page.getByRole('button', { name: /menu/i });
    if (await mobileMenuButton.isVisible()) {
      await mobileMenuButton.click();
      
      // Mobile menu should be visible
      const mobileMenu = page.locator('[data-testid="mobile-menu"]');
      await expect(mobileMenu).toBeVisible();
    }
    
    // Step 13: Return to desktop view and verify state persistence
    await page.setViewportSize({ width: 1200, height: 800 });
    
    // Theme should still be light
    await expect(page.locator('html')).toHaveClass(/light/);
    
    // Model selection should be preserved
    await expect(modelSelector).toHaveValue('gpt-4o-mini (AOAI)');
    
    // Message history should be preserved
    await expect(page.getByText('Help me manage my inventory')).toBeVisible();
    await expect(page.getByText(/Update inventory levels for all products/i)).toBeVisible();
    
    // Step 14: Final verification - send one more successful message
    await input.fill('Thank you for your help!');
    
    // Mock final response
    await page.route('/api/chat', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          response: 'You\'re welcome! I\'m always here to help with your business needs.',
          reasoning: 'Provided friendly closing response'
        })
      });
    });
    
    await page.getByRole('button', { name: 'Send' }).click();
    
    // Verify final response
    await expect(page.getByText(/You're welcome! I'm always here to help/i)).toBeVisible({ timeout: 15000 });
    
    // Verify application is in a good final state
    await expect(input).toBeEnabled();
    await expect(page.getByRole('button', { name: 'Send' })).toBeDisabled(); // Empty input
    await expect(page.getByText(/Chat with Steve's Mom AI/i)).toBeVisible();
  });

  test('handles complete workflow with WebSocket updates', async ({ page }) => {
    // Mock WebSocket for real-time updates
    await page.addInitScript(() => {
      const originalWebSocket = window.WebSocket;
      window.WebSocket = class extends originalWebSocket {
        constructor(url) {
          super(url);
          
          setTimeout(() => {
            this.onopen?.(new Event('open'));
            
            // Send periodic updates
            setTimeout(() => {
              const update = {
                id: 'live-update-1',
                title: 'Inventory sync completed',
                status: 'completed',
                timestamp: new Date().toISOString()
              };
              this.onmessage?.(new MessageEvent('message', {
                data: JSON.stringify(update)
              }));
            }, 3000);
          }, 100);
        }
      };
    });

    await page.goto('/');
    await waitForHealth(page);
    
    // Send a message to start the workflow
    const input = page.getByPlaceholder('Ask anything…');
    await input.fill('Start inventory sync');
    await page.getByRole('button', { name: 'Send' }).click();
    
    // Should receive WebSocket update
    await expect(page.getByText(/Inventory sync completed/i)).toBeVisible({ timeout: 10000 });
  });
});
