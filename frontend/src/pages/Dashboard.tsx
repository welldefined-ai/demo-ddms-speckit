/**
 * Dashboard page - real-time device monitoring
 *
 * Features:
 * - Real-time device readings via SSE
 * - Device cards with status indicators
 * - Historical chart for selected device
 * - Connection status alerts
 */
import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import DeviceCard from '../components/DeviceCard';
import Chart, { ChartDataPoint } from '../components/Chart';
import AlertBanner from '../components/AlertBanner';
import { SSEClient, DeviceReading, SSEConnectionState } from '../services/sse';
import './Dashboard.css';

const Dashboard: React.FC = () => {
  const { t } = useTranslation();
  const [devices, setDevices] = useState<DeviceReading[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<DeviceReading | null>(null);
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);
  const [connectionState, setConnectionState] = useState<SSEConnectionState>('disconnected');
  const [showConnectionAlert, setShowConnectionAlert] = useState(false);
  const sseClient = useRef<SSEClient | null>(null);

  // Initialize SSE connection
  useEffect(() => {
    sseClient.current = new SSEClient({
      onMessage: (data: DeviceReading[]) => {
        setDevices(data);

        // Update chart data if a device is selected
        if (selectedDevice) {
          const updatedDevice = data.find(d => d.device_id === selectedDevice.device_id);
          if (updatedDevice) {
            setSelectedDevice(updatedDevice);
            setChartData(prev => {
              const newData = [
                ...prev,
                { timestamp: updatedDevice.timestamp, value: updatedDevice.value },
              ];

              // Keep last 100 points
              return newData.slice(-100);
            });
          }
        }
      },
      onError: () => {
        setShowConnectionAlert(true);
      },
      onStateChange: (state: SSEConnectionState) => {
        setConnectionState(state);
        if (state === 'error' || state === 'disconnected') {
          setShowConnectionAlert(true);
        }
      },
    });

    sseClient.current.connect();

    // Cleanup on unmount
    return () => {
      sseClient.current?.disconnect();
    };
  }, [selectedDevice]);

  const handleDeviceClick = (device: DeviceReading) => {
    setSelectedDevice(device);
    // Initialize chart with current reading
    setChartData([{ timestamp: device.timestamp, value: device.value }]);
  };

  const getConnectionMessage = () => {
    switch (connectionState) {
      case 'connecting':
        return t('dashboard.connectionConnecting', {
          defaultValue: 'Connecting to server...',
        });
      case 'error':
        return t('dashboard.connectionError', {
          defaultValue: 'Connection error. Retrying...',
        });
      case 'disconnected':
        return t('dashboard.connectionDisconnected', {
          defaultValue: 'Disconnected from server',
        });
      default:
        return '';
    }
  };

  return (
    <div className="dashboard">
      <h1 className="dashboard-title">{t('nav.dashboard')}</h1>

      {showConnectionAlert && connectionState !== 'connected' && (
        <AlertBanner
          message={getConnectionMessage()}
          type={connectionState === 'connecting' ? 'info' : 'error'}
          onClose={() => setShowConnectionAlert(false)}
        />
      )}

      {devices.length === 0 && connectionState === 'connected' && (
        <div className="dashboard-empty">
          <p>
            {t('dashboard.noDevices', {
              defaultValue: 'No devices configured. Add devices to start monitoring.',
            })}
          </p>
        </div>
      )}

      <div className="dashboard-devices">
        {devices.map(device => (
          <DeviceCard
            key={device.device_id}
            deviceId={device.device_id}
            deviceName={device.device_name}
            value={device.value}
            unit={device.unit}
            status={device.status}
            timestamp={device.timestamp}
            onClick={() => handleDeviceClick(device)}
          />
        ))}
      </div>

      {selectedDevice && (
        <div className="dashboard-chart-section">
          <h2>
            {selectedDevice.device_name} - {t('dashboard.realTimeChart', { defaultValue: 'Real-Time Chart' })}
          </h2>
          <Chart
            data={chartData}
            unit={selectedDevice.unit}
            height={400}
            onPointHover={(point) => {
              console.log('Hovered point:', point);
            }}
          />
        </div>
      )}
    </div>
  );
};

export default Dashboard;
