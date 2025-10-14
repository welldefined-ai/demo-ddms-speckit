import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
} from 'chart.js';
import 'chartjs-adapter-date-fns';
import './GroupDashboard.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
);

interface Device {
  id: string;
  name: string;
  unit: string;
  status: string;
}

interface AlertSummary {
  normal: number;
  warning: number;
  critical: number;
}

interface GroupReading {
  device_id: string;
  device_name: string;
  timestamp: string;
  value: number;
  unit: string;
}

interface GroupDashboardProps {
  groupId: string;
  groupName: string;
  groupDescription?: string;
  devices: Device[];
  alertSummary: AlertSummary;
  readings: GroupReading[];
  onExport: () => void;
  onEdit?: () => void;
  onDelete?: () => void;
  canEdit?: boolean;
  isExporting?: boolean;
}

const GroupDashboard: React.FC<GroupDashboardProps> = ({
  groupId,
  groupName,
  groupDescription,
  devices,
  alertSummary,
  readings,
  onExport,
  onEdit,
  onDelete,
  canEdit = false,
  isExporting = false
}) => {
  const { t } = useTranslation();
  const [timeRange, setTimeRange] = useState<'1h' | '24h' | '7d' | '30d'>('24h');

  // Group readings by device
  const deviceReadingsMap = new Map<string, GroupReading[]>();
  readings.forEach(reading => {
    if (!deviceReadingsMap.has(reading.device_name)) {
      deviceReadingsMap.set(reading.device_name, []);
    }
    deviceReadingsMap.get(reading.device_name)!.push(reading);
  });

  // Generate chart data
  const chartData = {
    datasets: Array.from(deviceReadingsMap.entries()).map(([deviceName, deviceReadings], index) => {
      const colors = [
        '#3b82f6', // blue
        '#10b981', // green
        '#f59e0b', // amber
        '#ef4444', // red
        '#8b5cf6', // purple
        '#ec4899', // pink
      ];
      const color = colors[index % colors.length];

      return {
        label: deviceName,
        data: deviceReadings.map(r => ({
          x: new Date(r.timestamp).getTime(),
          y: r.value
        })),
        borderColor: color,
        backgroundColor: color + '20',
        borderWidth: 2,
        pointRadius: 2,
        pointHoverRadius: 5,
        tension: 0.1
      };
    })
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          padding: 15
        }
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            const deviceName = context.dataset.label;
            const value = context.parsed.y.toFixed(2);
            const reading = deviceReadingsMap.get(deviceName)?.[0];
            const unit = reading?.unit || '';
            return `${deviceName}: ${value} ${unit}`;
          }
        }
      }
    },
    scales: {
      x: {
        type: 'time' as const,
        time: {
          unit: timeRange === '1h' ? 'minute' : timeRange === '24h' ? 'hour' : 'day',
          displayFormats: {
            minute: 'HH:mm',
            hour: 'MMM d, HH:mm',
            day: 'MMM d'
          }
        },
        title: {
          display: true,
          text: 'Time'
        }
      },
      y: {
        title: {
          display: true,
          text: 'Value'
        }
      }
    }
  };

  return (
    <div className="group-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div className="header-info">
          <h1>{groupName}</h1>
          {groupDescription && <p className="description">{groupDescription}</p>}
        </div>
        <div className="header-actions">
          <button
            className="btn-export"
            onClick={onExport}
            disabled={isExporting}
          >
            📥 {isExporting ? t('common.loading') : t('groups.exportGroupData')}
          </button>
          {canEdit && onEdit && (
            <button className="btn-edit" onClick={onEdit}>
              ✏️ {t('groups.editGroup')}
            </button>
          )}
          {canEdit && onDelete && (
            <button className="btn-delete" onClick={onDelete}>
              🗑️ {t('groups.deleteGroup')}
            </button>
          )}
        </div>
      </div>

      {/* Alert Summary Cards */}
      <div className="alert-summary">
        <h2>{t('groups.alertSummary')}</h2>
        <div className="alert-cards">
          <div className="alert-card alert-card-normal">
            <div className="alert-icon">✓</div>
            <div className="alert-info">
              <div className="alert-count">{alertSummary.normal}</div>
              <div className="alert-label">{t('groups.normalDevices')}</div>
            </div>
          </div>
          <div className="alert-card alert-card-warning">
            <div className="alert-icon">⚠</div>
            <div className="alert-info">
              <div className="alert-count">{alertSummary.warning}</div>
              <div className="alert-label">{t('groups.warningDevices')}</div>
            </div>
          </div>
          <div className="alert-card alert-card-critical">
            <div className="alert-icon">✕</div>
            <div className="alert-info">
              <div className="alert-count">{alertSummary.critical}</div>
              <div className="alert-label">{t('groups.criticalDevices')}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Devices List */}
      <div className="devices-section">
        <h2>{t('groups.deviceCount', { count: devices.length })}</h2>
        {devices.length === 0 ? (
          <div className="empty-devices-state">
            <p>{t('groups.noDevicesInGroup')}</p>
            <p>{t('groups.addDevicesHint')}</p>
          </div>
        ) : (
          <div className="devices-grid">
            {devices.map(device => (
              <div key={device.id} className="device-item">
                <div className="device-name">{device.name}</div>
                <div className="device-details">
                  <span className="device-unit">{device.unit}</span>
                  <span className={`device-status status-${device.status.toLowerCase()}`}>
                    {device.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Readings Chart */}
      {readings.length > 0 && (
        <div className="readings-section">
          <div className="readings-header">
            <h2>{t('groups.groupReadings')}</h2>
            <div className="time-range-selector">
              <button
                className={timeRange === '1h' ? 'active' : ''}
                onClick={() => setTimeRange('1h')}
              >
                {t('historical.lastHour')}
              </button>
              <button
                className={timeRange === '24h' ? 'active' : ''}
                onClick={() => setTimeRange('24h')}
              >
                {t('historical.last24Hours')}
              </button>
              <button
                className={timeRange === '7d' ? 'active' : ''}
                onClick={() => setTimeRange('7d')}
              >
                {t('historical.last7Days')}
              </button>
              <button
                className={timeRange === '30d' ? 'active' : ''}
                onClick={() => setTimeRange('30d')}
              >
                {t('historical.last30Days')}
              </button>
            </div>
          </div>
          <div className="group-chart">
            <Line data={chartData} options={chartOptions} />
          </div>
          <div className="chart-info">
            {t('historical.dataPoints', { count: readings.length })}
          </div>
        </div>
      )}
    </div>
  );
};

export default GroupDashboard;
