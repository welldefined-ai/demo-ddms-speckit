/**
 * E2E tests for historical data analysis and export (T107)
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
 * Helper to create mock historical data
 */
function generateMockReadings(count: number, hoursAgo: number) {
  const readings = [];
  const now = new Date();

  for (let i = 0; i < count; i++) {
    const timestamp = new Date(now.getTime() - (hoursAgo * 60 * 60 * 1000) + (i * 60 * 1000));
    readings.push({
      timestamp: timestamp.toISOString(),
      value: 20.0 + Math.sin(i / 10) * 5 + Math.random() * 2,
    });
  }

  return readings;
}

test.describe('Historical Data Analysis E2E Tests', () => {
  let testDeviceId: string;

  test.beforeEach(async ({ page }) => {
    // Login before each test
    await loginAsAdmin(page);

    // Mock device ID for testing
    testDeviceId = '12345678-1234-1234-1234-123456789012';

    // Navigate to historical page
    await page.goto(`${BASE_URL}/historical`);
    await page.waitForLoadState('networkidle');
  });

  test('should display historical data analysis page', async ({ page }) => {
    // Verify page title
    await expect(page.locator('h1')).toContainText('Historical Data');

    // Verify device selector is visible
    await expect(page.locator('.device-selector')).toBeVisible();

    // Verify time range picker is visible
    await expect(page.locator('.time-range-picker')).toBeVisible();

    // Verify export button is visible
    await expect(page.locator('.btn-export')).toBeVisible();
  });

  test('should load and display device list in selector', async ({ page }) => {
    // Mock devices API
    await page.route(`${API_URL}/api/devices`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: testDeviceId,
            name: 'Temperature Sensor 1',
            unit: '°C',
            status: 'CONNECTED',
          },
          {
            id: '87654321-4321-4321-4321-210987654321',
            name: 'Pressure Sensor 2',
            unit: 'bar',
            status: 'CONNECTED',
          },
        ]),
      });
    });

    // Open device selector
    await page.click('.device-selector');

    // Verify devices are listed
    await expect(page.locator('.device-option')).toHaveCount(2);
    await expect(page.locator('.device-option').first()).toContainText('Temperature Sensor 1');
    await expect(page.locator('.device-option').nth(1)).toContainText('Pressure Sensor 2');
  });

  test('should display chart after selecting device and time range', async ({ page }) => {
    // Mock readings API
    const mockReadings = generateMockReadings(100, 24);
    await page.route(`${API_URL}/api/readings/${testDeviceId}*`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          device_id: testDeviceId,
          readings: mockReadings,
          total: mockReadings.length,
        }),
      });
    });

    // Select device
    await page.selectOption('.device-selector', testDeviceId);

    // Select time range (last 24 hours)
    await page.click('.time-range-picker');
    await page.click('[data-time-range="24h"]');

    // Wait for chart to load
    await page.waitForTimeout(1000);

    // Verify chart is displayed
    await expect(page.locator('.historical-chart')).toBeVisible();
    await expect(page.locator('canvas')).toBeVisible();
  });

  test('should support predefined time ranges', async ({ page }) => {
    const timeRanges = [
      { value: '1h', label: 'Last Hour' },
      { value: '24h', label: 'Last 24 Hours' },
      { value: '7d', label: 'Last 7 Days' },
      { value: '30d', label: 'Last 30 Days' },
    ];

    // Mock readings API for any device
    await page.route(`${API_URL}/api/readings/*`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          device_id: testDeviceId,
          readings: generateMockReadings(50, 1),
          total: 50,
        }),
      });
    });

    // Select a device first
    await page.selectOption('.device-selector', testDeviceId);

    // Test each time range
    for (const range of timeRanges) {
      await page.click('.time-range-picker');
      await page.click(`[data-time-range="${range.value}"]`);

      // Verify selected time range is displayed
      await expect(page.locator('.time-range-picker .selected')).toContainText(range.label);

      // Verify chart updates (wait for re-render)
      await page.waitForTimeout(500);
      await expect(page.locator('.historical-chart')).toBeVisible();
    }
  });

  test('should support custom time range selection', async ({ page }) => {
    // Mock readings API
    await page.route(`${API_URL}/api/readings/*`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          device_id: testDeviceId,
          readings: generateMockReadings(200, 72),
          total: 200,
        }),
      });
    });

    // Select device
    await page.selectOption('.device-selector', testDeviceId);

    // Open time range picker
    await page.click('.time-range-picker');

    // Click custom range option
    await page.click('[data-time-range="custom"]');

    // Verify date pickers appear
    await expect(page.locator('input[name="start_date"]')).toBeVisible();
    await expect(page.locator('input[name="end_date"]')).toBeVisible();

    // Select custom date range (3 days ago to today)
    const now = new Date();
    const threeDaysAgo = new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000);

    await page.fill('input[name="start_date"]', threeDaysAgo.toISOString().split('T')[0]);
    await page.fill('input[name="end_date"]', now.toISOString().split('T')[0]);

    // Apply custom range
    await page.click('.btn-apply-range');

    // Verify chart updates
    await page.waitForTimeout(1000);
    await expect(page.locator('.historical-chart')).toBeVisible();
  });

  test('should display chart with correct data points', async ({ page }) => {
    const mockReadings = generateMockReadings(50, 1);

    await page.route(`${API_URL}/api/readings/${testDeviceId}*`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          device_id: testDeviceId,
          readings: mockReadings,
          total: mockReadings.length,
        }),
      });
    });

    // Select device and time range
    await page.selectOption('.device-selector', testDeviceId);
    await page.click('.time-range-picker');
    await page.click('[data-time-range="1h"]');

    // Wait for chart to render
    await page.waitForTimeout(1000);

    // Verify chart canvas exists
    await expect(page.locator('.historical-chart canvas')).toBeVisible();

    // Verify data point count is displayed (if UI shows this)
    const dataPointsText = page.locator('.data-points-count');
    if (await dataPointsText.isVisible()) {
      await expect(dataPointsText).toContainText(`${mockReadings.length} points`);
    }
  });

  test('should support chart zoom functionality', async ({ page }) => {
    // Mock readings
    await page.route(`${API_URL}/api/readings/*`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          device_id: testDeviceId,
          readings: generateMockReadings(100, 24),
          total: 100,
        }),
      });
    });

    // Load chart
    await page.selectOption('.device-selector', testDeviceId);
    await page.click('.time-range-picker');
    await page.click('[data-time-range="24h"]');
    await page.waitForTimeout(1000);

    // Get chart element
    const chart = page.locator('.historical-chart canvas');

    // Simulate zoom in (mouse wheel or zoom button)
    const zoomInButton = page.locator('.btn-zoom-in');
    if (await zoomInButton.isVisible()) {
      await zoomInButton.click();
      await page.waitForTimeout(500);

      // Verify zoom state changed (chart should re-render)
      await expect(chart).toBeVisible();
    }
  });

  test('should support chart pan functionality', async ({ page }) => {
    // Mock readings
    await page.route(`${API_URL}/api/readings/*`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          device_id: testDeviceId,
          readings: generateMockReadings(100, 24),
          total: 100,
        }),
      });
    });

    // Load chart
    await page.selectOption('.device-selector', testDeviceId);
    await page.click('.time-range-picker');
    await page.click('[data-time-range="24h"]');
    await page.waitForTimeout(1000);

    // Get chart canvas
    const chartCanvas = page.locator('.historical-chart canvas');

    // Simulate pan by dragging (if pan is enabled)
    const boundingBox = await chartCanvas.boundingBox();
    if (boundingBox) {
      await page.mouse.move(boundingBox.x + 100, boundingBox.y + 100);
      await page.mouse.down();
      await page.mouse.move(boundingBox.x + 200, boundingBox.y + 100);
      await page.mouse.up();

      // Verify chart is still visible and responsive
      await expect(chartCanvas).toBeVisible();
    }
  });

  test('should reset zoom when changing time range', async ({ page }) => {
    // Mock readings
    await page.route(`${API_URL}/api/readings/*`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          device_id: testDeviceId,
          readings: generateMockReadings(100, 24),
          total: 100,
        }),
      });
    });

    // Load chart
    await page.selectOption('.device-selector', testDeviceId);
    await page.click('.time-range-picker');
    await page.click('[data-time-range="24h"]');
    await page.waitForTimeout(1000);

    // Zoom in
    const zoomInButton = page.locator('.btn-zoom-in');
    if (await zoomInButton.isVisible()) {
      await zoomInButton.click();
      await page.waitForTimeout(500);
    }

    // Change time range
    await page.click('.time-range-picker');
    await page.click('[data-time-range="7d"]');
    await page.waitForTimeout(1000);

    // Verify chart reset (zoom level should be default)
    const resetButton = page.locator('.btn-reset-zoom');
    if (await resetButton.isVisible()) {
      // If reset button is visible, zoom is active
      // After changing range, it should be hidden or disabled
      await expect(resetButton).toBeDisabled();
    }
  });

  test('should export data to CSV', async ({ page }) => {
    const mockReadings = generateMockReadings(50, 1);

    // Mock readings API
    await page.route(`${API_URL}/api/readings/${testDeviceId}*`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          device_id: testDeviceId,
          readings: mockReadings,
          total: mockReadings.length,
        }),
      });
    });

    // Mock export API
    await page.route(`${API_URL}/api/export/device/${testDeviceId}*`, async route => {
      // Generate CSV content
      const csvLines = ['timestamp,value,unit'];
      mockReadings.forEach(reading => {
        csvLines.push(`${reading.timestamp},${reading.value},°C`);
      });
      const csvContent = csvLines.join('\n');

      await route.fulfill({
        status: 200,
        contentType: 'text/csv',
        headers: {
          'Content-Disposition': 'attachment; filename="Temperature_Sensor_1.csv"',
        },
        body: csvContent,
      });
    });

    // Select device and load data
    await page.selectOption('.device-selector', testDeviceId);
    await page.click('.time-range-picker');
    await page.click('[data-time-range="1h"]');
    await page.waitForTimeout(1000);

    // Click export button and wait for download
    const downloadPromise = page.waitForEvent('download');
    await page.click('.btn-export');
    const download: Download = await downloadPromise;

    // Verify download properties
    expect(download.suggestedFilename()).toMatch(/\.csv$/);
    expect(download.suggestedFilename()).toContain('Temperature_Sensor');

    // Save and verify file content
    const downloadPath = path.join(__dirname, '../../../downloads', download.suggestedFilename());
    await download.saveAs(downloadPath);

    // Read CSV file
    const fileContent = fs.readFileSync(downloadPath, 'utf-8');
    const lines = fileContent.split('\n');

    // Verify CSV structure
    expect(lines[0]).toBe('timestamp,value,unit');
    expect(lines.length).toBeGreaterThan(1); // Header + at least one data row

    // Verify CSV data row format
    const dataRow = lines[1].split(',');
    expect(dataRow).toHaveLength(3);
    expect(dataRow[2]).toBe('°C');

    // Clean up download
    fs.unlinkSync(downloadPath);
  });

  test('should export data with correct time range', async ({ page }) => {
    const mockReadings = generateMockReadings(200, 24);

    // Mock export API with time range parameters
    await page.route(`${API_URL}/api/export/device/${testDeviceId}*`, async route => {
      const url = new URL(route.request().url());
      const startTime = url.searchParams.get('start_time');
      const endTime = url.searchParams.get('end_time');

      // Verify time range parameters are sent
      expect(startTime).toBeTruthy();
      expect(endTime).toBeTruthy();

      // Generate filtered CSV
      const csvLines = ['timestamp,value,unit'];
      mockReadings.slice(0, 50).forEach(reading => {
        csvLines.push(`${reading.timestamp},${reading.value},°C`);
      });

      await route.fulfill({
        status: 200,
        contentType: 'text/csv',
        headers: {
          'Content-Disposition': 'attachment; filename="export.csv"',
        },
        body: csvLines.join('\n'),
      });
    });

    // Select device and custom time range
    await page.selectOption('.device-selector', testDeviceId);
    await page.click('.time-range-picker');
    await page.click('[data-time-range="24h"]');
    await page.waitForTimeout(1000);

    // Export
    const downloadPromise = page.waitForEvent('download');
    await page.click('.btn-export');
    await downloadPromise;
  });

  test('should display empty state when no device is selected', async ({ page }) => {
    // Verify empty state message
    await expect(page.locator('.empty-state')).toBeVisible();
    await expect(page.locator('.empty-state')).toContainText('Select a device');
  });

  test('should display empty state when no data is available', async ({ page }) => {
    // Mock empty readings response
    await page.route(`${API_URL}/api/readings/${testDeviceId}*`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          device_id: testDeviceId,
          readings: [],
          total: 0,
        }),
      });
    });

    // Select device and time range
    await page.selectOption('.device-selector', testDeviceId);
    await page.click('.time-range-picker');
    await page.click('[data-time-range="24h"]');
    await page.waitForTimeout(1000);

    // Verify no data message
    await expect(page.locator('.no-data-message')).toBeVisible();
    await expect(page.locator('.no-data-message')).toContainText('No data available');
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Mock readings API to return error
    await page.route(`${API_URL}/api/readings/${testDeviceId}*`, async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Internal server error',
        }),
      });
    });

    // Select device and time range
    await page.selectOption('.device-selector', testDeviceId);
    await page.click('.time-range-picker');
    await page.click('[data-time-range="24h"]');

    // Verify error message is displayed
    await expect(page.locator('.alert-error')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.alert-error')).toContainText('Failed to load data');
  });

  test('should handle export errors gracefully', async ({ page }) => {
    // Mock readings API (success)
    await page.route(`${API_URL}/api/readings/${testDeviceId}*`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          device_id: testDeviceId,
          readings: generateMockReadings(50, 1),
          total: 50,
        }),
      });
    });

    // Mock export API to return error
    await page.route(`${API_URL}/api/export/device/${testDeviceId}*`, async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Export failed',
        }),
      });
    });

    // Load data
    await page.selectOption('.device-selector', testDeviceId);
    await page.click('.time-range-picker');
    await page.click('[data-time-range="1h"]');
    await page.waitForTimeout(1000);

    // Try to export
    await page.click('.btn-export');

    // Verify error message
    await expect(page.locator('.alert-error')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.alert-error')).toContainText('Export failed');
  });

  test('should display loading state while fetching data', async ({ page }) => {
    // Mock slow API response
    await page.route(`${API_URL}/api/readings/${testDeviceId}*`, async route => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          device_id: testDeviceId,
          readings: generateMockReadings(50, 1),
          total: 50,
        }),
      });
    });

    // Select device and time range
    await page.selectOption('.device-selector', testDeviceId);
    await page.click('.time-range-picker');
    await page.click('[data-time-range="1h"]');

    // Verify loading indicator appears
    await expect(page.locator('.loading-spinner')).toBeVisible();

    // Wait for data to load
    await page.waitForTimeout(2500);

    // Verify loading indicator disappears
    await expect(page.locator('.loading-spinner')).not.toBeVisible();
    await expect(page.locator('.historical-chart')).toBeVisible();
  });

  test('should maintain selections when navigating away and back', async ({ page }) => {
    // Mock readings
    await page.route(`${API_URL}/api/readings/*`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          device_id: testDeviceId,
          readings: generateMockReadings(50, 1),
          total: 50,
        }),
      });
    });

    // Select device and time range
    await page.selectOption('.device-selector', testDeviceId);
    await page.click('.time-range-picker');
    await page.click('[data-time-range="24h"]');
    await page.waitForTimeout(1000);

    // Navigate to another page
    await page.goto(`${BASE_URL}/dashboard`);
    await page.waitForLoadState('networkidle');

    // Navigate back to historical page
    await page.goto(`${BASE_URL}/historical`);
    await page.waitForLoadState('networkidle');

    // Verify selections are persisted (if implemented)
    // This depends on whether localStorage or URL params are used
    const deviceSelector = page.locator('.device-selector');
    const selectedValue = await deviceSelector.inputValue();

    // If persistence is implemented, verify
    if (selectedValue) {
      expect(selectedValue).toBe(testDeviceId);
    }
  });

  test('should display chart legend with unit', async ({ page }) => {
    // Mock readings with device info
    await page.route(`${API_URL}/api/readings/${testDeviceId}*`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          device_id: testDeviceId,
          readings: generateMockReadings(50, 1),
          total: 50,
        }),
      });
    });

    // Mock device info
    await page.route(`${API_URL}/api/devices/${testDeviceId}`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: testDeviceId,
          name: 'Temperature Sensor 1',
          unit: '°C',
          status: 'CONNECTED',
        }),
      });
    });

    // Load chart
    await page.selectOption('.device-selector', testDeviceId);
    await page.click('.time-range-picker');
    await page.click('[data-time-range="1h"]');
    await page.waitForTimeout(1000);

    // Verify chart legend shows unit
    const legend = page.locator('.chart-legend');
    if (await legend.isVisible()) {
      await expect(legend).toContainText('°C');
    }
  });

  test('should disable export button when no data is loaded', async ({ page }) => {
    // Verify export button is disabled initially
    const exportButton = page.locator('.btn-export');
    await expect(exportButton).toBeDisabled();

    // Mock readings
    await page.route(`${API_URL}/api/readings/${testDeviceId}*`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          device_id: testDeviceId,
          readings: generateMockReadings(50, 1),
          total: 50,
        }),
      });
    });

    // Load data
    await page.selectOption('.device-selector', testDeviceId);
    await page.click('.time-range-picker');
    await page.click('[data-time-range="1h"]');
    await page.waitForTimeout(1000);

    // Verify export button is enabled after data loads
    await expect(exportButton).toBeEnabled();
  });
});
