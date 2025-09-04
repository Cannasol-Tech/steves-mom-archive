import { test, expect } from '@playwright/test';

test.describe('Task Analytics Page', () => {
  test.beforeEach(async ({ page }) => {
    // Mock the analytics API endpoint
    await page.route('/api/tasks/analytics', async (route) => {
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
  });

  test('displays task analytics with loading state', async ({ page }) => {
    await page.goto('/tasks');
    
    // Should show loading initially
    await expect(page.getByText(/loading analytics/i)).toBeVisible();
    
    // Then show the analytics data
    await expect(page.getByRole('heading', { name: /Task Analytics/i })).toBeVisible();
    await expect(page.getByText(/75%/i)).toBeVisible(); // Accepted percentage
    await expect(page.getByText(/15%/i)).toBeVisible(); // Rejected percentage
    await expect(page.getByText(/10%/i)).toBeVisible(); // Modified percentage
  });

  test('handles API error gracefully', async ({ page }) => {
    // Mock API error
    await page.route('/api/tasks/analytics', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' })
      });
    });

    await page.goto('/tasks');
    
    // Should show loading first
    await expect(page.getByText(/loading analytics/i)).toBeVisible();
    
    // Then show error message
    await expect(page.getByText(/error loading analytics/i)).toBeVisible();
  });

  test('displays correct analytics data', async ({ page }) => {
    await page.goto('/tasks');
    
    // Wait for data to load
    await expect(page.getByRole('heading', { name: /Task Analytics/i })).toBeVisible();
    
    // Check that all metrics are displayed
    await expect(page.getByText('100')).toBeVisible(); // Total tasks
    await expect(page.getByText('75')).toBeVisible();  // Accepted count
    await expect(page.getByText('15')).toBeVisible();  // Rejected count
    await expect(page.getByText('10')).toBeVisible();  // Modified count
    
    // Check percentages
    await expect(page.getByText('75%')).toBeVisible(); // Accepted percentage
    await expect(page.getByText('15%')).toBeVisible(); // Rejected percentage
    await expect(page.getByText('10%')).toBeVisible(); // Modified percentage
  });

  test('analytics page is responsive', async ({ page }) => {
    await page.goto('/tasks');
    
    // Wait for content to load
    await expect(page.getByRole('heading', { name: /Task Analytics/i })).toBeVisible();
    
    // Test different viewport sizes
    await page.setViewportSize({ width: 1200, height: 800 });
    await expect(page.getByRole('heading', { name: /Task Analytics/i })).toBeVisible();
    
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.getByRole('heading', { name: /Task Analytics/i })).toBeVisible();
    
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.getByRole('heading', { name: /Task Analytics/i })).toBeVisible();
  });

  test('refreshes data when navigating back to page', async ({ page }) => {
    let requestCount = 0;
    
    // Track API calls
    await page.route('/api/tasks/analytics', async (route) => {
      requestCount++;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          totalTasks: 100 + requestCount,
          accepted: 75,
          rejected: 15,
          modified: 10
        })
      });
    });

    // First visit
    await page.goto('/tasks');
    await expect(page.getByText('101')).toBeVisible(); // 100 + 1 from first request
    
    // Navigate away
    await page.goto('/chat');
    await expect(page.getByText(/Chat with Steve's Mom AI/i)).toBeVisible();
    
    // Navigate back
    await page.goto('/tasks');
    await expect(page.getByText('102')).toBeVisible(); // 100 + 2 from second request
    
    expect(requestCount).toBe(2);
  });
});
