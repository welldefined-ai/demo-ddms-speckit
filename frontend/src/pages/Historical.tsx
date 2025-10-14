/**
 * Historical page - historical data analysis and export (User Story 4)
 *
 * Features:
 * - Device selection dropdown
 * - Time range picker (predefined and custom ranges)
 * - Historical chart with zoom/pan
 * - CSV export button
 * - Loading states and error handling
 */
import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import HistoricalChart, { HistoricalDataPoint } from '../components/HistoricalChart';
import TimeRangePicker, { TimeRange } from '../components/TimeRangePicker';
import ExportButton from '../components/ExportButton';
import api from '../utils/api';
import './Historical.css';

interface Device {
  id: string;
  name: string;
  unit: string;
  status: string;
}

const Historical: React.FC = () => {
  const { t } = useTranslation();
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('');
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [timeRange, setTimeRange] = useState<TimeRange | null>(null);
  const [chartData, setChartData] = useState<HistoricalDataPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [devicesLoading, setDevicesLoading] = useState(true);

  // Load devices on mount
  useEffect(() => {
    const fetchDevices = async () => {
      try {
        setDevicesLoading(true);
        const response = await api.get('/api/devices');
        setDevices(response.data);
      } catch (err) {
        console.error('Failed to fetch devices:', err);
        setError(t('historical.fetchDevicesFailed', { defaultValue: 'Failed to load devices' }));
      } finally {
        setDevicesLoading(false);
      }
    };

    fetchDevices();
  }, [t]);

  // Load historical data when device and time range are selected
  useEffect(() => {
    if (!selectedDeviceId || !timeRange) {
      return;
    }

    const fetchHistoricalData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Determine aggregation level based on time range
        const rangeMs = timeRange.end.getTime() - timeRange.start.getTime();
        const oneHour = 60 * 60 * 1000;
        const oneDay = 24 * oneHour;

        let aggregate: string | undefined;
        if (rangeMs > 90 * oneDay) {
          aggregate = '1day'; // For ranges > 90 days, use daily aggregation
        } else if (rangeMs > 30 * oneDay) {
          aggregate = '1hour'; // For ranges > 30 days, use hourly aggregation
        }
        // For ranges <= 30 days, use raw data (no aggregation) to preserve all data points

        const params: any = {
          start_time: timeRange.start.toISOString(),
          end_time: timeRange.end.toISOString(),
          limit: 1000,
        };

        if (aggregate) {
          params.aggregate = aggregate;
        }

        const response = await api.get(`/api/readings/${selectedDeviceId}`, { params });

        const readings: HistoricalDataPoint[] = response.data.readings.map((r: any) => ({
          timestamp: r.timestamp,
          value: r.value,
        }));

        setChartData(readings);

        if (readings.length === 0) {
          setError(t('historical.noData', { defaultValue: 'No data available for selected time range' }));
        }

      } catch (err: any) {
        console.error('Failed to fetch historical data:', err);
        let errorMessage = t('historical.fetchDataFailed', { defaultValue: 'Failed to load data' });

        if (err.response?.status === 404) {
          errorMessage = t('historical.deviceNotFound', { defaultValue: 'Device not found' });
        } else if (err.response?.status === 401) {
          errorMessage = t('auth.sessionExpired', { defaultValue: 'Session expired, please login again' });
        }

        setError(errorMessage);
        setChartData([]);
      } finally {
        setLoading(false);
      }
    };

    fetchHistoricalData();
  }, [selectedDeviceId, timeRange, t]);

  const handleDeviceChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const deviceId = event.target.value;
    setSelectedDeviceId(deviceId);

    const device = devices.find(d => d.id === deviceId);
    setSelectedDevice(device || null);

    // Clear data when device changes
    setChartData([]);
    setError(null);
  };

  const handleTimeRangeChange = (range: TimeRange) => {
    setTimeRange(range);
  };

  return (
    <div className="historical">
      <h1>{t('nav.historical', { defaultValue: 'Historical Data' })}</h1>
      <p className="page-description">
        {t('historical.description', {
          defaultValue: 'View and analyze historical device data with customizable time ranges',
        })}
      </p>

      {/* Device selector */}
      <div className="device-selector-section" style={{ marginBottom: '24px' }}>
        <label htmlFor="device-select" style={{ fontWeight: 'bold', marginRight: '12px', fontSize: '16px' }}>
          {t('historical.selectDevice', { defaultValue: 'Select Device:' })}
        </label>
        <select
          id="device-select"
          className="device-selector"
          value={selectedDeviceId}
          onChange={handleDeviceChange}
          disabled={devicesLoading || devices.length === 0}
          style={{
            padding: '10px 16px',
            fontSize: '14px',
            border: '1px solid #d9d9d9',
            borderRadius: '4px',
            minWidth: '250px',
            cursor: 'pointer',
          }}
        >
          <option value="">
            {devicesLoading
              ? t('common.loading', { defaultValue: 'Loading...' })
              : t('historical.selectDevicePlaceholder', { defaultValue: '-- Select a device --' })
            }
          </option>
          {devices.map(device => (
            <option key={device.id} value={device.id} className="device-option">
              {device.name} ({device.unit})
            </option>
          ))}
        </select>
      </div>

      {/* Time range picker */}
      {selectedDeviceId && (
        <TimeRangePicker
          onRangeChange={handleTimeRangeChange}
          defaultRange="24h"
        />
      )}

      {/* Error message */}
      {error && (
        <div
          className="alert-error"
          style={{
            marginTop: '16px',
            padding: '12px 16px',
            backgroundColor: '#fff2f0',
            border: '1px solid #ffccc7',
            borderRadius: '4px',
            color: '#cf1322',
          }}
        >
          {error}
        </div>
      )}

      {/* Loading spinner */}
      {loading && (
        <div className="loading-spinner" style={{ textAlign: 'center', marginTop: '32px' }}>
          <div
            style={{
              border: '4px solid #f3f3f3',
              borderTop: '4px solid #1890ff',
              borderRadius: '50%',
              width: '40px',
              height: '40px',
              animation: 'spin 1s linear infinite',
              margin: '0 auto',
            }}
          />
          <p style={{ marginTop: '16px', color: '#888' }}>
            {t('common.loading', { defaultValue: 'Loading...' })}
          </p>
        </div>
      )}

      {/* Chart */}
      {!loading && chartData.length > 0 && selectedDevice && (
        <div className="historical-chart-section" style={{ marginTop: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h2 style={{ margin: 0 }}>
              {selectedDevice.name}
            </h2>

            {/* Export button */}
            <ExportButton
              deviceId={selectedDeviceId}
              startTime={timeRange?.start}
              endTime={timeRange?.end}
              disabled={chartData.length === 0}
            />
          </div>

          <HistoricalChart
            data={chartData}
            unit={selectedDevice.unit}
            deviceName={selectedDevice.name}
            height={500}
            enableZoom={true}
            enableDataZoom={true}
            loading={loading}
          />
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && !selectedDeviceId && (
        <div className="empty-state" style={{ textAlign: 'center', marginTop: '64px', color: '#888' }}>
          <svg
            width="64"
            height="64"
            viewBox="0 0 64 64"
            fill="none"
            style={{ margin: '0 auto 16px' }}
          >
            <circle cx="32" cy="32" r="30" stroke="#d9d9d9" strokeWidth="2" />
            <path d="M20 32h24M32 20v24" stroke="#d9d9d9" strokeWidth="2" strokeLinecap="round" />
          </svg>
          <p style={{ fontSize: '16px' }}>
            {t('historical.selectDeviceToStart', { defaultValue: 'Select a device to view historical data' })}
          </p>
        </div>
      )}

      {!loading && !error && selectedDeviceId && !timeRange && (
        <div className="empty-state" style={{ textAlign: 'center', marginTop: '64px', color: '#888' }}>
          <p style={{ fontSize: '16px' }}>
            {t('historical.selectTimeRange', { defaultValue: 'Select a time range to view data' })}
          </p>
        </div>
      )}

      {!loading && chartData.length === 0 && selectedDeviceId && timeRange && !error && (
        <div className="no-data-message" style={{ textAlign: 'center', marginTop: '64px', color: '#888' }}>
          <svg
            width="64"
            height="64"
            viewBox="0 0 64 64"
            fill="none"
            style={{ margin: '0 auto 16px' }}
          >
            <circle cx="32" cy="32" r="30" stroke="#d9d9d9" strokeWidth="2" />
            <path d="M20 32h24" stroke="#d9d9d9" strokeWidth="2" strokeLinecap="round" />
          </svg>
          <p style={{ fontSize: '16px' }}>
            {t('historical.noDataAvailable', {
              defaultValue: 'No data available for the selected time range',
            })}
          </p>
        </div>
      )}

      {/* Add CSS for spinner animation */}
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default Historical;
