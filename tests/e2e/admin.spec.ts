import { test, expect } from '@playwright/test';

test.describe('Admin Page Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/admin');
  });

  test('renders admin page with all sections', async ({ page }) => {
    // Check main heading
    await expect(page.getByRole('heading', { name: /Admin Panel/i })).toBeVisible();
    
    // Check feature toggles section
    await expect(page.getByText(/Feature Toggles/i)).toBeVisible();
    await expect(page.locator('input[type="checkbox"]').first()).toBeVisible();

    // Check for toggle-related text (may be in spans, divs, or other elements)
    const hasToggleText = await page.getByText(/SQL/i).isVisible() ||
                         await page.getByText(/Email/i).isVisible() ||
                         await page.getByText(/Document/i).isVisible();
    expect(hasToggleText).toBe(true);
    
    // Check system status section
    await expect(page.getByText(/System Status/i)).toBeVisible();
    await expect(page.getByText(/API Status/i)).toBeVisible();
    await expect(page.getByText(/Database/i)).toBeVisible();
    await expect(page.getByText(/AI Model/i)).toBeVisible();
    
    // Check quick actions section
    await expect(page.getByText(/Quick Actions/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /View System Logs/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Export Analytics/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Manage Users/i })).toBeVisible();
    
    // Check performance metrics section
    await expect(page.getByText(/Performance Metrics/i)).toBeVisible();
    await expect(page.getByText(/Requests\/Hour/i)).toBeVisible();
    await expect(page.getByText(/Avg Response Time/i)).toBeVisible();
    await expect(page.getByText(/Uptime/i)).toBeVisible();
  });

  test('feature toggles work correctly', async ({ page }) => {
    // All toggles should be enabled by default
    const nlsqlToggle = page.locator('input[type="checkbox"]').first();
    const emailToggle = page.locator('input[type="checkbox"]').nth(1);
    const documentsToggle = page.locator('input[type="checkbox"]').nth(2);
    
    await expect(nlsqlToggle).toBeChecked();
    await expect(emailToggle).toBeChecked();
    await expect(documentsToggle).toBeChecked();
    
    // Toggle NL→SQL off
    await nlsqlToggle.click();
    await expect(nlsqlToggle).not.toBeChecked();
    
    // Toggle email off
    await emailToggle.click();
    await expect(emailToggle).not.toBeChecked();
    
    // Toggle documents off
    await documentsToggle.click();
    await expect(documentsToggle).not.toBeChecked();
    
    // Toggle them back on
    await nlsqlToggle.click();
    await expect(nlsqlToggle).toBeChecked();
    
    await emailToggle.click();
    await expect(emailToggle).toBeChecked();
    
    await documentsToggle.click();
    await expect(documentsToggle).toBeChecked();
  });

  test('system status indicators are visible', async ({ page }) => {
    // Check status badges
    const onlineStatus = page.getByText('Online');
    const connectedStatus = page.getByText('Connected');
    const pendingStatus = page.getByText('Pending');
    
    await expect(onlineStatus).toBeVisible();
    await expect(connectedStatus).toBeVisible();
    await expect(pendingStatus).toBeVisible();
  });

  test('quick action buttons are clickable', async ({ page }) => {
    const systemLogsBtn = page.getByRole('button', { name: /View System Logs/i });
    const exportAnalyticsBtn = page.getByRole('button', { name: /Export Analytics/i });
    const manageUsersBtn = page.getByRole('button', { name: /Manage Users/i });
    
    // Buttons should be enabled and clickable
    await expect(systemLogsBtn).toBeEnabled();
    await expect(exportAnalyticsBtn).toBeEnabled();
    await expect(manageUsersBtn).toBeEnabled();
    
    // Click each button (they don't have functionality yet, but should be clickable)
    await systemLogsBtn.click();
    await exportAnalyticsBtn.click();
    await manageUsersBtn.click();
  });

  test('performance metrics display placeholder values', async ({ page }) => {
    // Check that metric placeholders are displayed
    await expect(page.getByText('--')).toHaveCount(4); // 4 metrics with -- placeholder
    await expect(page.getByText('--ms')).toBeVisible();
    await expect(page.getByText('--%')).toBeVisible();
  });

  test('admin page is responsive', async ({ page }) => {
    // Test desktop view
    await page.setViewportSize({ width: 1200, height: 800 });
    await expect(page.getByRole('heading', { name: /Admin Panel/i })).toBeVisible();
    
    // Test tablet view
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.getByRole('heading', { name: /Admin Panel/i })).toBeVisible();
    
    // Test mobile view
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.getByRole('heading', { name: /Admin Panel/i })).toBeVisible();
    
    // Feature toggles should still be accessible on mobile
    await expect(page.locator('input[type="checkbox"]').first()).toBeVisible();
  });
});
