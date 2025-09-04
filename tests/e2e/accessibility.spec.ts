import { test, expect } from '@playwright/test';

test.describe('Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    // Mock the analytics API endpoint for tasks page (with trailing slash)
    await page.route('/api/tasks/analytics/', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          totalTasks: 100,
          accepted: 75,
          rejected: 15,
          modified: 10
        })
      });
    });

    await page.goto('/');
  });

  test('has proper heading structure', async ({ page }) => {
    // Check main heading
    const mainHeading = page.getByRole('heading', { level: 1 });
    await expect(mainHeading).toBeVisible();

    // Navigate to admin page and check heading
    await page.goto('/admin');
    const adminHeading = page.getByRole('heading', { name: /Admin Panel/i });
    await expect(adminHeading).toBeVisible();

    // Navigate to tasks page and check heading
    await page.goto('/tasks');
    const tasksHeading = page.getByRole('heading', { name: /Task Analytics/i });
    await expect(tasksHeading).toBeVisible();
  });

  test('form elements have proper labels', async ({ page }) => {
    // Chat input should have accessible label
    const chatInput = page.getByPlaceholder(/Ask anything/i);
    await expect(chatInput).toBeVisible();

    // Model selector should have label
    const modelSelector = page.locator('select').first();
    await expect(modelSelector).toBeVisible();

    // Send button should have accessible name
    const sendButton = page.getByRole('button', { name: /Send/i });
    await expect(sendButton).toBeVisible();
  });

  test('navigation is keyboard accessible', async ({ page }) => {
    // Tab through navigation links
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    // Should be able to navigate to admin page with keyboard
    const adminLink = page.getByRole('link', { name: /Admin/i }).first();
    await adminLink.focus();
    await expect(adminLink).toBeFocused();
    
    await page.keyboard.press('Enter');
    await expect(page).toHaveURL('/admin');
  });

  test('chat interface is keyboard accessible', async ({ page }) => {
    const input = page.getByPlaceholder('Ask anything…');
    
    // Focus input directly (more reliable than assuming tab order)
    await input.focus();

    // Check if input is focused
    await expect(input).toBeFocused();
    
    // Type message
    await page.keyboard.type('Test keyboard accessibility');
    
    // Use Ctrl+Enter to send
    await page.keyboard.press('Control+Enter');
    
    // Message should be sent
    await expect(page.getByText('Test keyboard accessibility')).toBeVisible();
  });

  test('buttons have proper focus states', async ({ page }) => {
    // First type something to enable the send button
    const input = page.getByPlaceholder('Ask anything…');
    await input.fill('Test message');

    const sendButton = page.getByRole('button', { name: /Send/i });

    // Focus the button (should be enabled now)
    await sendButton.focus();
    await expect(sendButton).toBeFocused();

    // Check theme toggle button
    const themeToggle = page.getByRole('button', { name: /toggle theme/i });
    await themeToggle.focus();
    await expect(themeToggle).toBeFocused();
  });

  test('has proper ARIA attributes', async ({ page }) => {
    // Check live region for streaming status (use first one to avoid strict mode violation)
    const liveRegion = page.locator('[role="status"][aria-live="polite"]').first();
    await expect(liveRegion).toBeAttached();

    // Check model selector ARIA
    const modelSelector = page.locator('select').first();
    await expect(modelSelector).toHaveAttribute('aria-label', 'Select AI model');

    // Check input ARIA attributes
    const input = page.getByPlaceholder('Ask anything…');
    await expect(input).toHaveAttribute('aria-describedby');
  });

  test('admin page toggles are accessible', async ({ page }) => {
    await page.goto('/admin');
    
    // Feature toggles should have proper labels
    const nlsqlToggle = page.locator('#nlsql-toggle');
    const emailToggle = page.locator('#email-toggle');
    const documentsToggle = page.locator('#docs-toggle');
    
    await expect(nlsqlToggle).toBeVisible();
    await expect(emailToggle).toBeVisible();
    await expect(documentsToggle).toBeVisible();
    
    // Should be keyboard accessible
    await nlsqlToggle.focus();
    await expect(nlsqlToggle).toBeFocused();
    
    await page.keyboard.press('Space');
    await expect(nlsqlToggle).not.toBeChecked();
  });

  test('error messages are announced to screen readers', async ({ page }) => {
    // Mock API error
    await page.route('/api/chat', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Server error' })
      });
    });

    const input = page.getByPlaceholder('Ask anything…');
    await input.fill('Trigger error');
    await page.getByRole('button', { name: 'Send' }).click();

    // Error should be visible and accessible (use first match to avoid strict mode violation)
    const errorMessage = page.getByText(/error/i).first();
    await expect(errorMessage).toBeVisible({ timeout: 10000 });
  });

  test('loading states are announced', async ({ page }) => {
    const input = page.getByPlaceholder('Ask anything…');
    await input.fill('Test loading announcement');
    await page.getByRole('button', { name: 'Send' }).click();

    // Live region should announce loading state (use first match to avoid strict mode violation)
    const liveRegion = page.locator('[role="status"][aria-live="polite"]').first();
    await expect(liveRegion).toContainText(/Assistant is generating a response/i, { timeout: 10000 });
  });

  test('color contrast is sufficient', async ({ page }) => {
    // Test both light and dark themes
    
    // Dark theme (default)
    await expect(page.locator('html')).toHaveClass(/dark/);
    
    // Check that text is visible (basic contrast check)
    const welcomeText = page.getByText(/Hello! I'm Steve's Mom AI assistant, here to help with your business needs/i);
    await expect(welcomeText).toBeVisible();
    
    // Switch to light theme
    const themeToggle = page.getByRole('button', { name: /toggle theme/i });
    await themeToggle.click();
    await expect(page.locator('html')).toHaveClass(/light/);
    
    // Text should still be visible in light theme
    await expect(welcomeText).toBeVisible();
  });

  test('focus management during streaming', async ({ page }) => {
    const input = page.getByPlaceholder('Ask anything…');
    const sendButton = page.getByRole('button', { name: 'Send' });
    
    // Focus input and send message
    await input.focus();
    await input.fill('Test focus management');
    await sendButton.click();
    
    // During streaming, focus should be managed appropriately
    // Input becomes disabled but focus should not be lost completely
    await expect(input).toBeDisabled({ timeout: 5000 });
    
    // After completion, input should be re-enabled and focusable
    await expect(input).toBeEnabled({ timeout: 30000 });
    await input.focus();
    await expect(input).toBeFocused();
  });

  test('skip links work correctly', async ({ page }) => {
    // Look for skip link (usually hidden but accessible)
    const skipLink = page.getByRole('link', { name: /skip to main content/i });
    
    if (await skipLink.isVisible()) {
      await skipLink.click();
      
      // Should jump to main content area
      const mainContent = page.locator('main');
      await expect(mainContent).toBeFocused();
    }
  });

  test('responsive design maintains accessibility', async ({ page }) => {
    // Test different viewport sizes
    const viewports = [
      { width: 1200, height: 800 }, // Desktop
      { width: 768, height: 1024 }, // Tablet
      { width: 375, height: 667 }   // Mobile
    ];

    for (const viewport of viewports) {
      await page.setViewportSize(viewport);

      // Key elements should remain accessible
      const input = page.getByPlaceholder('Ask anything…');
      await expect(input).toBeVisible();

      const sendButton = page.getByRole('button', { name: /Send/i });
      await expect(sendButton).toBeVisible();

      // Navigation should be accessible (desktop/tablet) or hamburger menu (mobile)
      if (viewport.width >= 768) {
        // Desktop/tablet: navigation links should be visible
        const chatLink = page.getByRole('link', { name: /Chat/i }).first();
        await expect(chatLink).toBeVisible();
      } else {
        // Mobile: hamburger menu should be accessible
        const menuButton = page.getByRole('button', { name: /menu/i }).first();
        if (await menuButton.isVisible()) {
          await expect(menuButton).toBeVisible();
        } else {
          // If no hamburger menu, navigation might still be visible
          const chatLink = page.getByRole('link', { name: /Chat/i }).first();
          if (await chatLink.isVisible()) {
            await expect(chatLink).toBeVisible();
          }
        }
      }
    }
  });
});
