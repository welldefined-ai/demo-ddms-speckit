/**
 * E2E tests for login and user management (T083)
 */
import { test, expect, Page } from '@playwright/test';

const BASE_URL = process.env.VITE_APP_BASE_URL || 'http://localhost:5173';
const API_URL = process.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Helper to login as specific user
 */
async function login(page: Page, username: string, password: string) {
  await page.goto(`${BASE_URL}/login`);
  await page.fill('input[name="username"]', username);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');

  // Wait for successful login
  await page.waitForURL(`${BASE_URL}/dashboard`, { timeout: 5000 });
}

test.describe('User Authentication E2E Tests', () => {
  test('should display login page', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    await expect(page.locator('h1, h2')).toContainText(/login/i);
    await expect(page.locator('input[name="username"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should login successfully with valid credentials', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'Admin123!');
    await page.click('button[type="submit"]');

    // Should redirect to dashboard
    await expect(page).toHaveURL(`${BASE_URL}/dashboard`);

    // Should display user info or logout button
    await expect(page.locator('text=/logout/i, text=/admin/i')).toBeVisible({ timeout: 5000 });
  });

  test('should show error with invalid credentials', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'WrongPassword');
    await page.click('button[type="submit"]');

    // Should show error message
    await expect(page.locator('text=/invalid|error|incorrect/i')).toBeVisible({ timeout: 3000 });

    // Should stay on login page
    await expect(page).toHaveURL(`${BASE_URL}/login`);
  });

  test('should validate required fields', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Try to submit empty form
    await page.click('button[type="submit"]');

    // Should show validation errors
    await expect(page.locator('text=/required/i')).toBeVisible();
  });

  test('should logout successfully', async ({ page }) => {
    // Login first
    await login(page, 'admin', 'Admin123!');

    // Click logout
    await page.click('text=/logout/i');

    // Should redirect to login
    await expect(page).toHaveURL(`${BASE_URL}/login`);
  });

  test('should protect routes when not authenticated', async ({ page }) => {
    // Try to access protected route without login
    await page.goto(`${BASE_URL}/devices`);

    // Should redirect to login
    await expect(page).toHaveURL(`${BASE_URL}/login`);
  });
});

test.describe('User Management E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Login as owner before each test
    await login(page, 'owner', 'Owner123!');
  });

  test('should display user management page', async ({ page }) => {
    await page.goto(`${BASE_URL}/users`);

    await expect(page.locator('h1')).toContainText(/user/i);
    await expect(page.locator('button')).toContainText(/create|add/i);
  });

  test('should create new user as owner', async ({ page }) => {
    await page.goto(`${BASE_URL}/users`);

    // Click create user button
    await page.click('button:has-text("Create"), button:has-text("Add")');

    // Fill user form
    await page.fill('input[name="username"]', 'newuser');
    await page.fill('input[name="password"]', 'NewUser123!');
    await page.selectOption('select[name="role"]', 'admin');

    // Submit form
    await page.click('button[type="submit"]');

    // Should show success message
    await expect(page.locator('text=/success|created/i')).toBeVisible({ timeout: 5000 });

    // New user should appear in list
    await expect(page.locator('text=newuser')).toBeVisible();
  });

  test('should not allow creating user with duplicate username', async ({ page }) => {
    await page.goto(`${BASE_URL}/users`);

    await page.click('button:has-text("Create"), button:has-text("Add")');

    // Try to create user with existing username
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'Test123!');
    await page.selectOption('select[name="role"]', 'admin');

    await page.click('button[type="submit"]');

    // Should show error
    await expect(page.locator('text=/already exists|duplicate/i')).toBeVisible({ timeout: 3000 });
  });

  test('should not allow creating owner role', async ({ page }) => {
    await page.goto(`${BASE_URL}/users`);

    await page.click('button:has-text("Create"), button:has-text("Add")');

    // Owner role should not be available in dropdown
    const roleSelect = page.locator('select[name="role"]');
    const ownerOption = roleSelect.locator('option[value="owner"]');

    // Owner option should either not exist or be disabled
    const ownerCount = await ownerOption.count();
    if (ownerCount > 0) {
      await expect(ownerOption).toBeDisabled();
    }
  });

  test('should delete user as owner', async ({ page }) => {
    await page.goto(`${BASE_URL}/users`);

    // Create a user to delete first
    await page.click('button:has-text("Create"), button:has-text("Add")');
    await page.fill('input[name="username"]', 'todelete');
    await page.fill('input[name="password"]', 'Delete123!');
    await page.selectOption('select[name="role"]', 'read_only');
    await page.click('button[type="submit"]');

    // Wait for user to appear
    await expect(page.locator('text=todelete')).toBeVisible();

    // Setup dialog handler
    page.on('dialog', async dialog => {
      expect(dialog.type()).toBe('confirm');
      await dialog.accept();
    });

    // Delete the user
    const deleteButton = page.locator('tr:has-text("todelete") button:has-text("Delete"), tr:has-text("todelete") [title*="Delete"]');
    await deleteButton.click();

    // User should be removed
    await expect(page.locator('text=todelete')).not.toBeVisible({ timeout: 5000 });
  });

  test('should not allow owner to delete themselves', async ({ page }) => {
    await page.goto(`${BASE_URL}/users`);

    // Try to find delete button for owner
    const ownerRow = page.locator('tr:has-text("owner")');
    const deleteButton = ownerRow.locator('button:has-text("Delete")');

    // Delete button should either not exist or be disabled
    const buttonCount = await deleteButton.count();
    if (buttonCount > 0) {
      await expect(deleteButton).toBeDisabled();
    }
  });

  test('should change own password', async ({ page }) => {
    await page.goto(`${BASE_URL}/settings`);

    // Fill change password form
    await page.fill('input[name="old_password"]', 'Owner123!');
    await page.fill('input[name="new_password"]', 'NewOwner123!');
    await page.fill('input[name="confirm_password"]', 'NewOwner123!');

    await page.click('button:has-text("Change Password")');

    // Should show success message
    await expect(page.locator('text=/success/i')).toBeVisible({ timeout: 3000 });

    // Logout and try logging in with new password
    await page.click('text=/logout/i');

    await page.fill('input[name="username"]', 'owner');
    await page.fill('input[name="password"]', 'NewOwner123!');
    await page.click('button[type="submit"]');

    // Should login successfully
    await expect(page).toHaveURL(`${BASE_URL}/dashboard`);
  });
});

test.describe('RBAC E2E Tests', () => {
  test('should restrict user creation for admin role', async ({ page }) => {
    // Login as admin
    await login(page, 'admin', 'Admin123!');

    // Try to access user management
    await page.goto(`${BASE_URL}/users`);

    // Admin should not see create button or should get forbidden error
    const createButton = page.locator('button:has-text("Create")');
    const buttonCount = await createButton.count();

    if (buttonCount > 0) {
      await createButton.click();
      // Should show forbidden message
      await expect(page.locator('text=/forbidden|permission/i')).toBeVisible({ timeout: 3000 });
    }
  });

  test('should restrict user management for read-only role', async ({ page }) => {
    // Login as read-only user
    await login(page, 'readonly', 'Read123!');

    // Try to access user management
    await page.goto(`${BASE_URL}/users`);

    // Should either redirect or show forbidden message
    const url = page.url();
    if (url === `${BASE_URL}/users`) {
      await expect(page.locator('text=/forbidden|access denied/i')).toBeVisible({ timeout: 3000 });
    } else {
      // Should redirect to dashboard or home
      expect(url).not.toBe(`${BASE_URL}/users`);
    }
  });

  test('should show different UI based on role', async ({ page }) => {
    // Login as read-only
    await login(page, 'readonly', 'Read123!');

    await page.goto(`${BASE_URL}/devices`);

    // Read-only user should not see create/edit/delete buttons
    const createButton = page.locator('button:has-text("Create")');
    await expect(createButton).not.toBeVisible();

    const editButtons = page.locator('button:has-text("Edit"), [title*="Edit"]');
    const editCount = await editButtons.count();
    expect(editCount).toBe(0);
  });
});

test.describe('Token Refresh E2E Tests', () => {
  test('should maintain session across page refreshes', async ({ page }) => {
    await login(page, 'admin', 'Admin123!');

    // Navigate to different page
    await page.goto(`${BASE_URL}/devices`);

    // Refresh page
    await page.reload();

    // Should still be authenticated
    await expect(page).toHaveURL(`${BASE_URL}/devices`);
    await expect(page.locator('text=/logout/i')).toBeVisible();
  });

  test('should handle expired session', async ({ page }) => {
    // This test would require manipulating token expiration
    // Skip for now as it's complex to test
    test.skip();
  });
});
