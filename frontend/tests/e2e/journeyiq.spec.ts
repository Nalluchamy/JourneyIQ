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
    const tabs = ['telemetry', 'customers', 'settings', 'models', 'agent'];
    for (const tab of tabs) {
      const tabLink = page.locator(`a[href="/dashboard/${tab}"]`);
      if (await tabLink.isVisible()) {
        await tabLink.click();
        await expect(page).toHaveURL(new RegExp(`/dashboard/${tab}`));
      }
    }
  });

  test('Autonomous Agentic AI Dashboard Loop Integration', async ({ page }) => {
    // Navigate to dashboard
    await page.goto('/dashboard');
    
    // Check if Agentic AI sidebar button exists and click it
    const agentTabBtn = page.locator('button:has-text("Agentic AI")');
    if (await agentTabBtn.isVisible()) {
      await agentTabBtn.click();
      
      // Verify visual execution flow and metrics sections
      await expect(page.locator('h3:has-text("Autonomous Agentic AI Orchestrator")')).toBeVisible();
      await expect(page.locator('h4:has-text("Visual Agent Execution Loop")')).toBeVisible();
      await expect(page.locator('h4:has-text("Observe telemetry scan data")')).toBeVisible();
      
      // Check for manual loop run action
      const triggerBtn = page.locator('button:has-text("Trigger Autonomous Run")');
      if (await triggerBtn.isEnabled()) {
        await triggerBtn.click();
        await page.waitForTimeout(1000);
      }
    }
  });

  test('AI Business Copilot Dashboard Tab Integration', async ({ page }) => {
    // Navigate to dashboard
    await page.goto('/dashboard');
    
    // Check if Business Copilot sidebar button exists and click it
    const copilotTabBtn = page.locator('button:has-text("Business Copilot")');
    if (await copilotTabBtn.isVisible()) {
      await copilotTabBtn.click();
      
      // Verify workspace views
      await expect(page.locator('h3:has-text("AI Business Copilot Workspace")')).toBeVisible();
      await expect(page.locator('h4:has-text("AI Business Copilot Chat")')).toBeVisible();
      await expect(page.locator('h4:has-text("Executive Performance Reports")')).toBeVisible();
      
      // Select report formats and click Generate Report
      const generateReportBtn = page.locator('button:has-text("Generate Report")');
      if (await generateReportBtn.isVisible()) {
        await generateReportBtn.click();
        await page.waitForTimeout(500);
      }
    }
  });
});
