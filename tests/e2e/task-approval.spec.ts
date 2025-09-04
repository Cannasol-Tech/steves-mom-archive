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

test.describe('Task Approval Workflow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForHealth(page);
  });

  test('displays task approval buttons when tasks are generated', async ({ page }) => {
    // Mock chat response that includes a task
    await page.route('/api/chat', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          response: 'I can help you with that. Here\'s a task: [TASK:task-123] Update inventory for SKU-456 [/TASK]',
          reasoning: 'Generated a task for inventory update'
        })
      });
    });

    const input = page.getByPlaceholder('Ask anything…');
    await input.fill('Please update my inventory');
    await page.getByRole('button', { name: 'Send' }).click();

    // Should show the response with task
    await expect(page.getByText(/Update inventory for SKU-456/i)).toBeVisible({ timeout: 15000 });

    // Should show approve and reject buttons
    await expect(page.getByRole('button', { name: /Approve/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Reject/i })).toBeVisible();
  });

  test('approves tasks successfully', async ({ page }) => {
    let approvalCalled = false;
    
    // Mock chat response with task
    await page.route('/api/chat', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          response: 'Task created: [TASK:task-approve-123] Send email to customer about order status [/TASK]',
          reasoning: 'Created email task'
        })
      });
    });

    // Mock task approval API
    await page.route('/api/tasks/task-approve-123/approve', async (route) => {
      approvalCalled = true;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'approved' })
      });
    });

    const input = page.getByPlaceholder('Ask anything…');
    await input.fill('Send an email to the customer');
    await page.getByRole('button', { name: 'Send' }).click();

    // Wait for task to appear
    await expect(page.getByText(/Send email to customer/i)).toBeVisible({ timeout: 15000 });

    // Click approve button
    const approveButton = page.getByRole('button', { name: /Approve/i });
    await approveButton.click();

    // Should call approval API
    await expect.poll(() => approvalCalled).toBe(true);

    // Should show success feedback
    await expect(page.getByText(/approved/i)).toBeVisible({ timeout: 5000 });
  });

  test('rejects tasks successfully', async ({ page }) => {
    let rejectionCalled = false;
    
    // Mock chat response with task
    await page.route('/api/chat', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          response: 'Task created: [TASK:task-reject-123] Delete all customer data [/TASK]',
          reasoning: 'Created dangerous task'
        })
      });
    });

    // Mock task rejection API
    await page.route('/api/tasks/task-reject-123/reject', async (route) => {
      rejectionCalled = true;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'rejected' })
      });
    });

    const input = page.getByPlaceholder('Ask anything…');
    await input.fill('Delete customer data');
    await page.getByRole('button', { name: 'Send' }).click();

    // Wait for task to appear
    await expect(page.getByText(/Delete all customer data/i)).toBeVisible({ timeout: 15000 });

    // Click reject button
    const rejectButton = page.getByRole('button', { name: /Reject/i });
    await rejectButton.click();

    // Should call rejection API
    await expect.poll(() => rejectionCalled).toBe(true);

    // Should show rejection feedback
    await expect(page.getByText(/rejected/i)).toBeVisible({ timeout: 5000 });
  });

  test('handles task approval errors gracefully', async ({ page }) => {
    // Mock chat response with task
    await page.route('/api/chat', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          response: 'Task: [TASK:task-error-123] Process payment [/TASK]',
          reasoning: 'Payment task'
        })
      });
    });

    // Mock task approval API error
    await page.route('/api/tasks/task-error-123/approve', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Approval failed' })
      });
    });

    const input = page.getByPlaceholder('Ask anything…');
    await input.fill('Process a payment');
    await page.getByRole('button', { name: 'Send' }).click();

    // Wait for task to appear
    await expect(page.getByText(/Process payment/i)).toBeVisible({ timeout: 15000 });

    // Click approve button
    const approveButton = page.getByRole('button', { name: /Approve/i });
    await approveButton.click();

    // Should show error message
    await expect(page.getByText(/error/i)).toBeVisible({ timeout: 5000 });

    // Buttons should remain available for retry
    await expect(approveButton).toBeVisible();
    await expect(page.getByRole('button', { name: /Reject/i })).toBeVisible();
  });

  test('shows task status updates via WebSocket', async ({ page }) => {
    // Mock WebSocket for task updates
    await page.addInitScript(() => {
      const originalWebSocket = window.WebSocket;
      window.WebSocket = class extends originalWebSocket {
        constructor(url) {
          super(url);
          
          // Simulate successful connection
          setTimeout(() => {
            this.onopen?.(new Event('open'));
            
            // Send task update after a delay
            setTimeout(() => {
              const taskUpdate = {
                id: 'task-ws-123',
                title: 'Email sent successfully',
                status: 'completed',
                timestamp: new Date().toISOString()
              };
              this.onmessage?.(new MessageEvent('message', {
                data: JSON.stringify(taskUpdate)
              }));
            }, 2000);
          }, 100);
        }
      };
    });

    await page.reload();

    // Should eventually show the task update
    await expect(page.getByText(/Email sent successfully/i)).toBeVisible({ timeout: 10000 });
  });

  test('displays multiple tasks in conversation', async ({ page }) => {
    // Mock chat response with multiple tasks
    await page.route('/api/chat', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          response: 'I\'ll help with both: [TASK:task-multi-1] Update inventory [/TASK] and [TASK:task-multi-2] Send notification [/TASK]',
          reasoning: 'Created multiple tasks'
        })
      });
    });

    const input = page.getByPlaceholder('Ask anything…');
    await input.fill('Update inventory and send notification');
    await page.getByRole('button', { name: 'Send' }).click();

    // Should show both tasks
    await expect(page.getByText(/Update inventory/i)).toBeVisible({ timeout: 15000 });
    await expect(page.getByText(/Send notification/i)).toBeVisible({ timeout: 15000 });

    // Should show approve/reject buttons for both tasks
    const approveButtons = page.getByRole('button', { name: /Approve/i });
    const rejectButtons = page.getByRole('button', { name: /Reject/i });
    
    await expect(approveButtons).toHaveCount(2);
    await expect(rejectButtons).toHaveCount(2);
  });

  test('task approval buttons are accessible', async ({ page }) => {
    // Mock chat response with task
    await page.route('/api/chat', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          response: 'Task: [TASK:task-a11y-123] Accessible task [/TASK]',
          reasoning: 'Accessibility test task'
        })
      });
    });

    const input = page.getByPlaceholder('Ask anything…');
    await input.fill('Create an accessible task');
    await page.getByRole('button', { name: 'Send' }).click();

    // Wait for task to appear
    await expect(page.getByText(/Accessible task/i)).toBeVisible({ timeout: 15000 });

    // Buttons should be keyboard accessible
    const approveButton = page.getByRole('button', { name: /Approve/i });
    const rejectButton = page.getByRole('button', { name: /Reject/i });

    await approveButton.focus();
    await expect(approveButton).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(rejectButton).toBeFocused();

    // Should be activatable with keyboard
    await page.keyboard.press('Enter');
    // This would trigger the reject action
  });

  test('shows task panel with pending tasks', async ({ page }) => {
    // Look for task panel toggle button
    const taskPanelButton = page.locator('button').filter({ hasText: /task/i }).first();
    
    if (await taskPanelButton.isVisible()) {
      await taskPanelButton.click();
      
      // Task panel should open
      const taskPanel = page.getByText(/Agent Tasks/i);
      await expect(taskPanel).toBeVisible();
    }
  });
});
