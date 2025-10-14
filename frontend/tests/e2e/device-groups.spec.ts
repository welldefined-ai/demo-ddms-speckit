/**
 * E2E tests for device grouping and group dashboards (T127)
 */
import { test, expect, Page, Download } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

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

/**
 * Helper to login as read-only user
 */
async function loginAsReadOnly(page: Page) {
  await page.goto(`${BASE_URL}/login`);
  await page.fill('input[name="username"]', 'readonly');
  await page.fill('input[name="password"]', 'ReadOnly123!');
  await page.click('button[type="submit"]');

  // Wait for navigation to complete
  await page.waitForURL(`${BASE_URL}/dashboard`);
}

/**
 * Helper to generate mock readings for multiple devices
 */
function generateMultiDeviceReadings(devices: Array<{ id: string; name: string }>, count: number) {
  const readings = [];
  const now = new Date();

  for (let i = 0; i < count; i++) {
    const timestamp = new Date(now.getTime() - (count - i) * 60 * 1000);
    for (const device of devices) {
      readings.push({
        device_id: device.id,
        device_name: device.name,
        timestamp: timestamp.toISOString(),
        value: 20.0 + Math.sin(i / 10) * 5 + Math.random() * 2,
        unit: '°C',
      });
    }
  }

  return readings;
}

test.describe('Device Groups E2E Tests', () => {
  let testGroupId: string;
  let testDevices: Array<{ id: string; name: string; status: string }>;

  test.beforeEach(async ({ page }) => {
    // Login before each test
    await loginAsAdmin(page);

    // Mock test data
    testGroupId = '11111111-1111-1111-1111-111111111111';
    testDevices = [
      {
        id: '22222222-2222-2222-2222-222222222222',
        name: 'Temperature Sensor 1',
        status: 'normal',
      },
      {
        id: '33333333-3333-3333-3333-333333333333',
        name: 'Temperature Sensor 2',
        status: 'warning',
      },
      {
        id: '44444444-4444-4444-4444-444444444444',
        name: 'Pressure Sensor 1',
        status: 'critical',
      },
    ];

    // Navigate to groups page
    await page.goto(`${BASE_URL}/groups`);
    await page.waitForLoadState('networkidle');
  });

  test('should display device groups page', async ({ page }) => {
    // Verify page title
    await expect(page.locator('h1')).toContainText('Device Groups');

    // Verify create group button is visible (admin only)
    await expect(page.locator('.btn-create-group')).toBeVisible();

    // Verify groups list container is visible
    await expect(page.locator('.groups-list')).toBeVisible();
  });

  test('should list all groups', async ({ page }) => {
    // Mock groups API
    await page.route(`${API_URL}/api/groups`, async route => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              id: testGroupId,
              name: 'Production Line 1',
              description: 'Main production line sensors',
              device_count: 5,
              created_at: new Date().toISOString(),
            },
            {
              id: '99999999-9999-9999-9999-999999999999',
              name: 'Testing Area',
              description: 'Quality control sensors',
              device_count: 3,
              created_at: new Date().toISOString(),
            },
          ]),
        });
      }
    });

    // Reload to trigger API call
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Verify groups are displayed
    await expect(page.locator('.group-card')).toHaveCount(2);
    await expect(page.locator('.group-card').first()).toContainText('Production Line 1');
    await expect(page.locator('.group-card').nth(1)).toContainText('Testing Area');
  });

  test('should create new group with devices', async ({ page }) => {
    // Mock devices API
    await page.route(`${API_URL}/api/devices`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(testDevices.map(d => ({
          id: d.id,
          name: d.name,
          unit: '°C',
          status: 'CONNECTED',
        }))),
      });
    });

    // Mock group creation API
    await page.route(`${API_URL}/api/groups`, async route => {
      if (route.request().method() === 'POST') {
        const postData = route.request().postDataJSON();
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: testGroupId,
            name: postData.name,
            description: postData.description,
            devices: postData.device_ids.map((id: string) =>
              testDevices.find(d => d.id === id)
            ),
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }),
        });
      }
    });

    // Click create group button
    await page.click('.btn-create-group');

    // Verify form dialog appears
    await expect(page.locator('.group-form-dialog')).toBeVisible();

    // Fill in group details
    await page.fill('input[name="name"]', 'Production Line 1');
    await page.fill('textarea[name="description"]', 'Main production line sensors');

    // Select devices (check first 2 devices)
    await page.check(`input[value="${testDevices[0].id}"]`);
    await page.check(`input[value="${testDevices[1].id}"]`);

    // Submit form
    await page.click('.btn-submit-group');

    // Verify success message
    await expect(page.locator('.alert-success')).toBeVisible();
    await expect(page.locator('.alert-success')).toContainText('Group created successfully');

    // Verify form closes
    await expect(page.locator('.group-form-dialog')).not.toBeVisible();
  });

  test('should validate group creation form', async ({ page }) => {
    // Click create group button
    await page.click('.btn-create-group');

    // Try to submit without filling required fields
    await page.click('.btn-submit-group');

    // Verify validation errors
    await expect(page.locator('.error-name')).toBeVisible();
    await expect(page.locator('.error-name')).toContainText('required');

    // Fill in name but leave devices empty
    await page.fill('input[name="name"]', 'Test Group');
    await page.click('.btn-submit-group');

    // Verify device selection validation
    await expect(page.locator('.error-devices')).toBeVisible();
    await expect(page.locator('.error-devices')).toContainText('at least one device');
  });

  test('should display group dashboard with alert summary', async ({ page }) => {
    // Mock group detail API
    await page.route(`${API_URL}/api/groups/${testGroupId}`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: testGroupId,
          name: 'Production Line 1',
          description: 'Main production line sensors',
          devices: testDevices,
          alert_summary: {
            normal: 1,
            warning: 1,
            critical: 1,
          },
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }),
      });
    });

    // Navigate to group detail
    await page.goto(`${BASE_URL}/groups/${testGroupId}`);
    await page.waitForLoadState('networkidle');

    // Verify group dashboard is displayed
    await expect(page.locator('.group-dashboard')).toBeVisible();
    await expect(page.locator('.group-name')).toContainText('Production Line 1');

    // Verify alert summary cards
    await expect(page.locator('.alert-card-normal')).toBeVisible();
    await expect(page.locator('.alert-card-normal')).toContainText('1');

    await expect(page.locator('.alert-card-warning')).toBeVisible();
    await expect(page.locator('.alert-card-warning')).toContainText('1');

    await expect(page.locator('.alert-card-critical')).toBeVisible();
    await expect(page.locator('.alert-card-critical')).toContainText('1');

    // Verify devices list
    await expect(page.locator('.device-item')).toHaveCount(3);
  });

  test('should display group readings chart', async ({ page }) => {
    // Mock group detail API
    await page.route(`${API_URL}/api/groups/${testGroupId}`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: testGroupId,
          name: 'Production Line 1',
          devices: testDevices,
          alert_summary: { normal: 1, warning: 1, critical: 1 },
        }),
      });
    });

    // Mock group readings API
    const mockReadings = generateMultiDeviceReadings(
      testDevices.slice(0, 2),
      50
    );

    await page.route(`${API_URL}/api/groups/${testGroupId}/readings*`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          group_id: testGroupId,
          readings: mockReadings,
          total: mockReadings.length,
        }),
      });
    });

    // Navigate to group detail
    await page.goto(`${BASE_URL}/groups/${testGroupId}`);
    await page.waitForLoadState('networkidle');

    // Verify readings chart is displayed
    await expect(page.locator('.group-chart')).toBeVisible();
    await expect(page.locator('.group-chart canvas')).toBeVisible();

    // Verify chart legend shows multiple devices
    const legend = page.locator('.chart-legend');
    if (await legend.isVisible()) {
      await expect(legend).toContainText('Temperature Sensor 1');
      await expect(legend).toContainText('Temperature Sensor 2');
    }
  });

  test('should support time range filtering for group readings', async ({ page }) => {
    // Mock APIs
    await page.route(`${API_URL}/api/groups/${testGroupId}`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: testGroupId,
          name: 'Production Line 1',
          devices: testDevices,
          alert_summary: { normal: 1, warning: 1, critical: 1 },
        }),
      });
    });

    await page.route(`${API_URL}/api/groups/${testGroupId}/readings*`, async route => {
      const url = new URL(route.request().url());
      const hours = url.searchParams.get('hours');

      const readings = generateMultiDeviceReadings(
        testDevices.slice(0, 2),
        hours === '1' ? 60 : 100
      );

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          group_id: testGroupId,
          readings,
          total: readings.length,
        }),
      });
    });

    // Navigate to group detail
    await page.goto(`${BASE_URL}/groups/${testGroupId}`);
    await page.waitForLoadState('networkidle');

    // Test time range selector
    await page.click('.time-range-picker');
    await page.click('[data-time-range="1h"]');
    await page.waitForTimeout(1000);

    // Verify chart updates
    await expect(page.locator('.group-chart')).toBeVisible();

    // Change to 24 hours
    await page.click('.time-range-picker');
    await page.click('[data-time-range="24h"]');
    await page.waitForTimeout(1000);

    // Verify chart updates again
    await expect(page.locator('.group-chart')).toBeVisible();
  });

  test('should export group data to CSV', async ({ page }) => {
    // Mock group detail
    await page.route(`${API_URL}/api/groups/${testGroupId}`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: testGroupId,
          name: 'Production Line 1',
          devices: testDevices,
          alert_summary: { normal: 1, warning: 1, critical: 1 },
        }),
      });
    });

    // Mock export API
    await page.route(`${API_URL}/api/export/group/${testGroupId}*`, async route => {
      const mockReadings = generateMultiDeviceReadings(testDevices.slice(0, 2), 50);

      // Generate CSV with device_name column
      const csvLines = ['timestamp,device_name,value,unit'];
      mockReadings.forEach(reading => {
        csvLines.push(
          `${reading.timestamp},${reading.device_name},${reading.value},${reading.unit}`
        );
      });

      await route.fulfill({
        status: 200,
        contentType: 'text/csv',
        headers: {
          'Content-Disposition': 'attachment; filename="Production_Line_1.csv"',
        },
        body: csvLines.join('\n'),
      });
    });

    // Navigate to group detail
    await page.goto(`${BASE_URL}/groups/${testGroupId}`);
    await page.waitForLoadState('networkidle');

    // Click export button
    const downloadPromise = page.waitForEvent('download');
    await page.click('.btn-export-group');
    const download: Download = await downloadPromise;

    // Verify download
    expect(download.suggestedFilename()).toMatch(/\.csv$/);
    expect(download.suggestedFilename()).toContain('Production_Line');

    // Save and verify file content
    const downloadPath = path.join(__dirname, '../../../downloads', download.suggestedFilename());
    await download.saveAs(downloadPath);

    // Read and verify CSV structure
    const fileContent = fs.readFileSync(downloadPath, 'utf-8');
    const lines = fileContent.split('\n');

    // Verify headers include device_name
    expect(lines[0]).toBe('timestamp,device_name,value,unit');
    expect(lines.length).toBeGreaterThan(1);

    // Verify data row format
    const dataRow = lines[1].split(',');
    expect(dataRow).toHaveLength(4);
    expect(dataRow[1]).toMatch(/Temperature Sensor|Pressure Sensor/);

    // Clean up
    fs.unlinkSync(downloadPath);
  });

  test('should update group devices', async ({ page }) => {
    // Mock group detail
    await page.route(`${API_URL}/api/groups/${testGroupId}`, async route => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: testGroupId,
            name: 'Production Line 1',
            description: 'Main production line sensors',
            devices: [testDevices[0]],
            alert_summary: { normal: 1, warning: 0, critical: 0 },
          }),
        });
      } else if (route.request().method() === 'PUT') {
        const putData = route.request().postDataJSON();
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: testGroupId,
            name: putData.name || 'Production Line 1',
            description: putData.description,
            devices: putData.device_ids.map((id: string) =>
              testDevices.find(d => d.id === id)
            ),
            alert_summary: { normal: 2, warning: 0, critical: 0 },
          }),
        });
      }
    });

    // Mock devices API
    await page.route(`${API_URL}/api/devices`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(testDevices.map(d => ({
          id: d.id,
          name: d.name,
          unit: '°C',
          status: 'CONNECTED',
        }))),
      });
    });

    // Navigate to group detail
    await page.goto(`${BASE_URL}/groups/${testGroupId}`);
    await page.waitForLoadState('networkidle');

    // Click edit button
    await page.click('.btn-edit-group');

    // Verify edit form appears with pre-filled data
    await expect(page.locator('.group-form-dialog')).toBeVisible();
    await expect(page.locator('input[name="name"]')).toHaveValue('Production Line 1');

    // Add another device
    await page.check(`input[value="${testDevices[1].id}"]`);

    // Submit update
    await page.click('.btn-submit-group');

    // Verify success message
    await expect(page.locator('.alert-success')).toBeVisible();
    await expect(page.locator('.alert-success')).toContainText('Group updated successfully');

    // Verify updated device count
    await page.waitForTimeout(500);
    await expect(page.locator('.device-item')).toHaveCount(2);
  });

  test('should delete group', async ({ page }) => {
    // Mock group detail
    await page.route(`${API_URL}/api/groups/${testGroupId}`, async route => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: testGroupId,
            name: 'Production Line 1',
            devices: [testDevices[0]],
            alert_summary: { normal: 1, warning: 0, critical: 0 },
          }),
        });
      } else if (route.request().method() === 'DELETE') {
        await route.fulfill({
          status: 204,
        });
      }
    });

    // Navigate to group detail
    await page.goto(`${BASE_URL}/groups/${testGroupId}`);
    await page.waitForLoadState('networkidle');

    // Click delete button
    await page.click('.btn-delete-group');

    // Verify confirmation dialog
    await expect(page.locator('.confirm-dialog')).toBeVisible();
    await expect(page.locator('.confirm-dialog')).toContainText('delete');

    // Confirm deletion
    await page.click('.btn-confirm-delete');

    // Verify redirect to groups list
    await page.waitForURL(`${BASE_URL}/groups`);

    // Verify success message
    await expect(page.locator('.alert-success')).toBeVisible();
    await expect(page.locator('.alert-success')).toContainText('Group deleted successfully');
  });

  test('should enforce RBAC - read-only cannot create groups', async ({ page }) => {
    // Logout and login as read-only user
    await page.click('.btn-logout');
    await loginAsReadOnly(page);

    // Navigate to groups page
    await page.goto(`${BASE_URL}/groups`);
    await page.waitForLoadState('networkidle');

    // Verify create button is not visible for read-only users
    await expect(page.locator('.btn-create-group')).not.toBeVisible();
  });

  test('should enforce RBAC - read-only cannot edit groups', async ({ page }) => {
    // Mock group detail
    await page.route(`${API_URL}/api/groups/${testGroupId}`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: testGroupId,
          name: 'Production Line 1',
          devices: [testDevices[0]],
          alert_summary: { normal: 1, warning: 0, critical: 0 },
        }),
      });
    });

    // Logout and login as read-only user
    await page.click('.btn-logout');
    await loginAsReadOnly(page);

    // Navigate to group detail
    await page.goto(`${BASE_URL}/groups/${testGroupId}`);
    await page.waitForLoadState('networkidle');

    // Verify edit and delete buttons are not visible
    await expect(page.locator('.btn-edit-group')).not.toBeVisible();
    await expect(page.locator('.btn-delete-group')).not.toBeVisible();

    // Verify view is still accessible
    await expect(page.locator('.group-dashboard')).toBeVisible();
  });

  test('should display empty state when group has no devices', async ({ page }) => {
    // Mock empty group
    await page.route(`${API_URL}/api/groups/${testGroupId}`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: testGroupId,
          name: 'Empty Group',
          description: 'Group with no devices',
          devices: [],
          alert_summary: { normal: 0, warning: 0, critical: 0 },
        }),
      });
    });

    // Navigate to group detail
    await page.goto(`${BASE_URL}/groups/${testGroupId}`);
    await page.waitForLoadState('networkidle');

    // Verify empty state message
    await expect(page.locator('.empty-devices-state')).toBeVisible();
    await expect(page.locator('.empty-devices-state')).toContainText('no devices');
  });

  test('should display empty state when no groups exist', async ({ page }) => {
    // Mock empty groups list
    await page.route(`${API_URL}/api/groups`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    // Reload page
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Verify empty state
    await expect(page.locator('.empty-groups-state')).toBeVisible();
    await expect(page.locator('.empty-groups-state')).toContainText('No groups');
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Mock API error
    await page.route(`${API_URL}/api/groups/${testGroupId}`, async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Internal server error',
        }),
      });
    });

    // Navigate to group detail
    await page.goto(`${BASE_URL}/groups/${testGroupId}`);

    // Verify error message
    await expect(page.locator('.alert-error')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.alert-error')).toContainText('Failed to load group');
  });

  test('should display loading state while fetching group data', async ({ page }) => {
    // Mock slow API response
    await page.route(`${API_URL}/api/groups/${testGroupId}`, async route => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: testGroupId,
          name: 'Production Line 1',
          devices: testDevices,
          alert_summary: { normal: 1, warning: 1, critical: 1 },
        }),
      });
    });

    // Navigate to group detail
    await page.goto(`${BASE_URL}/groups/${testGroupId}`);

    // Verify loading spinner appears
    await expect(page.locator('.loading-spinner')).toBeVisible();

    // Wait for data to load
    await page.waitForTimeout(2500);

    // Verify loading spinner disappears
    await expect(page.locator('.loading-spinner')).not.toBeVisible();
    await expect(page.locator('.group-dashboard')).toBeVisible();
  });

  test('should search/filter groups', async ({ page }) => {
    // Mock groups API
    await page.route(`${API_URL}/api/groups`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: '111', name: 'Production Line 1', device_count: 5 },
          { id: '222', name: 'Production Line 2', device_count: 3 },
          { id: '333', name: 'Testing Area', device_count: 2 },
        ]),
      });
    });

    // Reload page
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Verify all groups are displayed
    await expect(page.locator('.group-card')).toHaveCount(3);

    // Search for "Production"
    const searchInput = page.locator('input[name="search"]');
    if (await searchInput.isVisible()) {
      await searchInput.fill('Production');

      // Verify filtered results
      await expect(page.locator('.group-card')).toHaveCount(2);
      await expect(page.locator('.group-card').first()).toContainText('Production');
    }
  });
});
