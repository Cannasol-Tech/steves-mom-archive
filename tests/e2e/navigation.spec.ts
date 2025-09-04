import { test, expect } from '@playwright/test';

test.describe('Navigation and Routing', () => {
  test('navigates between pages using navigation links', async ({ page }) => {
    await page.goto('/');
    
    // Verify we're on the chat page initially
    await expect(page.getByText(/Chat with Steve's Mom AI/i)).toBeVisible();
    
    // Navigate to Admin page
    await page.getByRole('link', { name: /Admin/i }).first().click();
    await expect(page).toHaveURL('/admin');
    await expect(page.getByText(/Admin Panel/i)).toBeVisible();
    
    // Navigate to Tasks page
    await page.getByRole('link', { name: /Tasks/i }).first().click();
    await expect(page).toHaveURL('/tasks');
    await expect(page.getByText(/Task Analytics/i)).toBeVisible();
    
    // Navigate back to Chat page
    await page.getByRole('link', { name: /Chat/i }).first().click();
    await expect(page).toHaveURL('/');
    await expect(page.getByText(/Chat with Steve's Mom AI/i)).toBeVisible();
  });

  test('handles direct navigation to different routes', async ({ page }) => {
    // Direct navigation to admin page
    await page.goto('/admin');
    await expect(page.getByText(/Admin Panel/i)).toBeVisible();
    
    // Direct navigation to tasks page
    await page.goto('/tasks');
    await expect(page.getByText(/Task Analytics/i)).toBeVisible();
    
    // Direct navigation to chat page
    await page.goto('/chat');
    await expect(page.getByText(/Chat with Steve's Mom AI/i)).toBeVisible();
  });

  test('shows 404 page for invalid routes', async ({ page }) => {
    await page.goto('/invalid-route');
    await expect(page.getByText(/404/i)).toBeVisible();
    await expect(page.getByText(/Page Not Found/i)).toBeVisible();
  });

  test('mobile navigation menu works correctly', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // Mobile menu should be hidden initially (check for the aside element)
    const mobileMenu = page.locator('aside.md\\:hidden');
    await expect(mobileMenu).not.toBeVisible();

    // Click hamburger menu button
    const menuButton = page.getByRole('button', { name: /open main menu/i });
    await menuButton.click();

    // Mobile menu should now be visible
    await expect(mobileMenu).toBeVisible();

    // Navigate using mobile menu
    await page.getByRole('link', { name: /Admin/i }).last().click();
    await expect(page).toHaveURL('/admin');

    // Menu should close after navigation
    await expect(mobileMenu).not.toBeVisible();
  });
});
