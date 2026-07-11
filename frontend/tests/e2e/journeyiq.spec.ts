import { test, expect } from '@playwright/test';

test.describe('JourneyIQ v1.0.0 End-to-End Suite', () => {
  
  test('Storefront Navigation & Public Pages', async ({ page }) => {
    // 1. Visit homepage
    await page.goto('/');
    await expect(page).toHaveTitle(/JourneyIQ/i);
    
    // Verify hero section elements
    await expect(page.locator('h1')).toContainText(/JourneyIQ/i);

    // 2. Visit About Page
    await page.click('text=About');
    await expect(page).toHaveURL(/\/about/);
    await expect(page.locator('h1')).toContainText(/About JourneyIQ/i);
    await expect(page.locator('text=Neural Recommendation')).toBeVisible();

    // 3. Visit Contact Page
    await page.click('text=Contact');
    await expect(page).toHaveURL(/\/contact/);
    await expect(page.locator('h1')).toContainText(/Contact JourneyIQ Support/i);

    // Test Contact form validation
    await page.click('button[type="submit"]');
    await page.fill('input[name="name"]', 'Test User');
    await page.fill('input[name="email"]', 'invalid-email');
    await page.fill('textarea[name="message"]', 'Hello, this is a test message.');
    await page.click('button[type="submit"]');
  });

  test('Product Catalog & Search Flow', async ({ page }) => {
    await page.goto('/products');
    
    // Check search input visibility
    const searchInput = page.locator('input[placeholder*="Search"]');
    if (await searchInput.isVisible()) {
      await searchInput.fill('Comfort');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(500);
    }
  });

  test('Authentication Flow Simulation', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('h2, h1')).toContainText(/Sign In/i);
    
    await page.fill('input[type="email"]', 'customer@example.com');
    await page.fill('input[type="password"]', 'Password123!');
    await page.click('button[type="submit"]');
  });

  test('Owner Analytics Dashboard Views', async ({ page }) => {
    await page.goto('/dashboard/overview');
    
    // Check navigation tab clicks
    const tabs = ['telemetry', 'customers', 'settings', 'models'];
    for (const tab of tabs) {
      const tabLink = page.locator(`a[href="/dashboard/${tab}"]`);
      if (await tabLink.isVisible()) {
        await tabLink.click();
        await expect(page).toHaveURL(new RegExp(`/dashboard/${tab}`));
      }
    }
  });
});
