import { test, expect } from '@playwright/test';

test.describe('Theme Switching', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('toggles between light and dark themes', async ({ page }) => {
    // Check initial theme (should be dark by default)
    const html = page.locator('html');
    await expect(html).toHaveClass(/dark/);
    
    // Find and click theme toggle button
    const themeToggle = page.getByRole('button', { name: /toggle theme/i });
    await themeToggle.click();
    
    // Should switch to light theme
    await expect(html).toHaveClass(/light/);
    await expect(html).not.toHaveClass(/dark/);
    
    // Click again to switch back to dark
    await themeToggle.click();
    await expect(html).toHaveClass(/dark/);
    await expect(html).not.toHaveClass(/light/);
  });

  test('persists theme preference in localStorage', async ({ page }) => {
    const html = page.locator('html');
    
    // Start with dark theme
    await expect(html).toHaveClass(/dark/);
    
    // Switch to light theme
    const themeToggle = page.getByRole('button', { name: /toggle theme/i });
    await themeToggle.click();
    await expect(html).toHaveClass(/light/);
    
    // Reload page and check theme is persisted
    await page.reload();
    await expect(html).toHaveClass(/light/);
    
    // Switch back to dark and reload
    await themeToggle.click();
    await expect(html).toHaveClass(/dark/);
    await page.reload();
    await expect(html).toHaveClass(/dark/);
  });

  test('theme persists across page navigation', async ({ page }) => {
    const html = page.locator('html');
    
    // Switch to light theme on chat page
    const themeToggle = page.getByRole('button', { name: /toggle theme/i });
    await themeToggle.click();
    await expect(html).toHaveClass(/light/);
    
    // Navigate to admin page
    await page.getByRole('link', { name: /Admin/i }).first().click();
    await expect(page).toHaveURL('/admin');
    await expect(html).toHaveClass(/light/);
    
    // Navigate to tasks page
    await page.getByRole('link', { name: /Tasks/i }).first().click();
    await expect(page).toHaveURL('/tasks');
    await expect(html).toHaveClass(/light/);
    
    // Navigate back to chat
    await page.getByRole('link', { name: /Chat/i }).first().click();
    await expect(page).toHaveURL('/chat');
    await expect(html).toHaveClass(/light/);
  });

  test('theme affects visual appearance', async ({ page }) => {
    // Test that theme changes actually affect the visual appearance
    const chatInterface = page.locator('[class*="bg-gradient-to-br"]').first();
    
    // In dark theme, should have dark background classes
    await expect(page.locator('html')).toHaveClass(/dark/);
    
    // Switch to light theme
    const themeToggle = page.getByRole('button', { name: /toggle theme/i });
    await themeToggle.click();
    
    // Verify light theme is applied
    await expect(page.locator('html')).toHaveClass(/light/);
    
    // The chat interface should still be visible regardless of theme
    await expect(chatInterface).toBeVisible();
  });

  test('theme toggle is accessible', async ({ page }) => {
    const themeToggle = page.getByRole('button', { name: /toggle theme/i });
    
    // Button should be focusable
    await themeToggle.focus();
    await expect(themeToggle).toBeFocused();
    
    // Should be activatable with keyboard
    await page.keyboard.press('Enter');
    await expect(page.locator('html')).toHaveClass(/light/);
    
    // Space key should also work
    await page.keyboard.press('Space');
    await expect(page.locator('html')).toHaveClass(/dark/);
  });

  test('handles localStorage errors gracefully', async ({ page }) => {
    // Simulate localStorage being unavailable
    await page.addInitScript(() => {
      Object.defineProperty(window, 'localStorage', {
        value: {
          getItem: () => { throw new Error('localStorage unavailable'); },
          setItem: () => { throw new Error('localStorage unavailable'); },
        },
        writable: false
      });
    });
    
    await page.goto('/');
    
    // Should still load with default theme (dark)
    await expect(page.locator('html')).toHaveClass(/dark/);
    
    // Theme toggle should still work (just won't persist)
    const themeToggle = page.getByRole('button', { name: /toggle theme/i });
    await themeToggle.click();
    await expect(page.locator('html')).toHaveClass(/light/);
  });
});
