/**
 * E2E tests for device creation workflow (T059)
 */
import { test, expect, Page } from '@playwright/test';

// Test configuration
const BASE_URL = process.env.VITE_APP_BASE_URL || 'http://localhost:5173';
const API_URL = process.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Helper to login as admin
 */
async function loginAsAdmin(page: Page) {
  await page.goto(`${BASE_URL}/login`);
  await page.fill('input[name="username"]', 'admin');
  await page.fill('input[name="password"]', 'Admin123!');
  await page.click('button[type="submit"]');

  // Wait for navigation to complete
  await page.waitForURL(`${BASE_URL}/dashboard`);
}

test.describe('Device Configuration E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await loginAsAdmin(page);

    // Navigate to device configuration page
    await page.goto(`${BASE_URL}/devices`);
    await page.waitForLoadState('networkidle');
  });

  test('should display device configuration page', async ({ page }) => {
    // Verify page title and description
    await expect(page.locator('h1')).toContainText('Device Configuration');
    await expect(page.locator('.page-description')).toContainText('Manage Modbus devices');

    // Verify create button exists
    await expect(page.locator('.btn-create')).toBeVisible();
  });

  test('should create a new device successfully', async ({ page }) => {
    // Click create device button
    await page.click('.btn-create');

    // Wait for form to appear
    await expect(page.locator('.device-form')).toBeVisible();
    await expect(page.locator('h2')).toContainText('Create New Device');

    // Fill in basic information
    await page.fill('input[name="name"]', 'Test E2E Device');
    await page.fill('input[name="unit"]', '°C');
    await page.fill('input[name="sampling_interval"]', '30');

    // Fill in Modbus configuration
    await page.fill('input[name="modbus_ip"]', '192.168.1.200');
    await page.fill('input[name="modbus_port"]', '502');
    await page.fill('input[name="modbus_slave_id"]', '1');
    await page.fill('input[name="modbus_register"]', '0');
    await page.fill('input[name="modbus_register_count"]', '1');

    // Fill in thresholds
    await page.fill('input[name="threshold_warning_lower"]', '10');
    await page.fill('input[name="threshold_warning_upper"]', '50');
    await page.fill('input[name="threshold_critical_lower"]', '0');
    await page.fill('input[name="threshold_critical_upper"]', '80');

    // Submit form
    await page.click('button[type="submit"]');

    // Wait for success message
    await expect(page.locator('.alert-success')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.alert-success')).toContainText('Device created successfully');

    // Verify device appears in list
    await expect(page.locator('.devices-table')).toBeVisible();
    await expect(page.locator('.device-name')).toContainText('Test E2E Device');
  });

  test('should validate required fields', async ({ page }) => {
    // Click create device button
    await page.click('.btn-create');

    // Try to submit empty form
    await page.click('button[type="submit"]');

    // Verify error messages appear
    await expect(page.locator('.error-message')).toHaveCount(3); // name, modbus_ip, unit are required
    await expect(page.locator('input[name="name"]').locator('..').locator('.error-message'))
      .toContainText('Device name is required');
  });

  test('should validate IP address format', async ({ page }) => {
    await page.click('.btn-create');

    // Fill in name and unit
    await page.fill('input[name="name"]', 'Invalid IP Device');
    await page.fill('input[name="unit"]', 'bar');

    // Enter invalid IP
    await page.fill('input[name="modbus_ip"]', 'not-an-ip');

    // Submit form
    await page.click('button[type="submit"]');

    // Verify IP validation error
    await expect(page.locator('input[name="modbus_ip"].error')).toBeVisible();
  });

  test('should validate threshold ordering', async ({ page }) => {
    await page.click('.btn-create');

    // Fill in required fields
    await page.fill('input[name="name"]', 'Invalid Thresholds Device');
    await page.fill('input[name="modbus_ip"]', '192.168.1.201');
    await page.fill('input[name="unit"]', 'kPa');

    // Enter invalid thresholds (lower >= upper)
    await page.fill('input[name="threshold_warning_lower"]', '60');
    await page.fill('input[name="threshold_warning_upper"]', '40');

    // Submit form
    await page.click('button[type="submit"]');

    // Verify threshold validation error
    await expect(page.locator('.error-message')).toContainText('Warning lower threshold must be less than');
  });

  test('should edit an existing device', async ({ page }) => {
    // Wait for device list to load
    await expect(page.locator('.devices-table')).toBeVisible();

    // Click edit button on first device
    const editButton = page.locator('.btn-edit').first();
    await editButton.click();

    // Wait for form to appear with data
    await expect(page.locator('.device-form')).toBeVisible();
    await expect(page.locator('h2')).toContainText('Edit Device');

    // Verify form is pre-filled
    const nameInput = page.locator('input[name="name"]');
    await expect(nameInput).not.toHaveValue('');

    // Update sampling interval
    await page.fill('input[name="sampling_interval"]', '60');

    // Submit form
    await page.click('button[type="submit"]');

    // Wait for success message
    await expect(page.locator('.alert-success')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.alert-success')).toContainText('Device updated successfully');
  });

  test('should delete a device', async ({ page }) => {
    // Intercept confirm dialogs
    page.on('dialog', async dialog => {
      expect(dialog.type()).toBe('confirm');
      await dialog.accept();
    });

    // Wait for device list
    await expect(page.locator('.devices-table')).toBeVisible();

    // Get device name before deletion
    const deviceName = await page.locator('.device-name').first().textContent();

    // Click delete button on first device
    const deleteButton = page.locator('.btn-delete').first();
    await deleteButton.click();

    // Wait for success message
    await expect(page.locator('.alert-success')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.alert-success')).toContainText('Device deleted successfully');

    // Verify device is removed from list
    if (deviceName) {
      await expect(page.locator('.device-name')).not.toContainText(deviceName);
    }
  });

  test('should test device connection', async ({ page }) => {
    // Mock the test connection API endpoint to return success
    await page.route(`${API_URL}/api/devices/*/test-connection`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          error: null
        })
      });
    });

    // Wait for device list
    await expect(page.locator('.devices-table')).toBeVisible();

    // Click test connection button on first device
    const testButton = page.locator('.btn-test').first();
    await testButton.click();

    // Wait for success message
    await expect(page.locator('.alert-success')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.alert-success')).toContainText('Connection test successful');
  });

  test('should handle connection test failure', async ({ page }) => {
    // Mock the test connection API endpoint to return failure
    await page.route(`${API_URL}/api/devices/*/test-connection`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: false,
          error: 'Connection timeout'
        })
      });
    });

    // Wait for device list
    await expect(page.locator('.devices-table')).toBeVisible();

    // Click test connection button on first device
    const testButton = page.locator('.btn-test').first();
    await testButton.click();

    // Wait for error message
    await expect(page.locator('.alert-error')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.alert-error')).toContainText('Connection test failed');
  });

  test('should cancel form and return to list', async ({ page }) => {
    // Click create device button
    await page.click('.btn-create');

    // Wait for form
    await expect(page.locator('.device-form')).toBeVisible();

    // Fill in some data
    await page.fill('input[name="name"]', 'Will be canceled');

    // Click cancel button
    await page.click('.btn-secondary');

    // Verify form is hidden and list is shown
    await expect(page.locator('.device-form')).not.toBeVisible();
    await expect(page.locator('.devices-table')).toBeVisible();
  });

  test('should display empty state when no devices exist', async ({ page }) => {
    // Mock API to return empty device list
    await page.route(`${API_URL}/api/devices`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([])
      });
    });

    // Reload page
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Verify empty state message
    await expect(page.locator('.empty-state')).toBeVisible();
    await expect(page.locator('.empty-state')).toContainText('No devices configured');
  });

  test('should filter devices by status', async ({ page }) => {
    // This test assumes filtering UI exists or can be added
    // Skip if not implemented yet
    test.skip();
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Mock API to return error
    await page.route(`${API_URL}/api/devices`, async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Internal server error'
        })
      });
    });

    // Reload page
    await page.reload();

    // Verify error message is displayed
    await expect(page.locator('.alert-error')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.alert-error')).toContainText('Failed to fetch devices');
  });
});
