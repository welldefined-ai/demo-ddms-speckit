import React from 'react';
import { useTranslation } from 'react-i18next';
import './DeviceList.css';

interface Device {
  id: string;
  name: string;
  modbus_ip: string;
  modbus_port: number;
  unit: string;
  status: string;
  last_reading_at: string | null;
  sampling_interval: number;
}

interface DeviceListProps {
  devices: Device[];
  onEdit: (device: Device) => void;
  onDelete: (device: Device) => void;
  onTestConnection: (device: Device) => void;
  loading?: boolean;
}

const DeviceList: React.FC<DeviceListProps> = ({
  devices,
  onEdit,
  onDelete,
  onTestConnection,
  loading = false
}) => {
  const { t } = useTranslation();

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, { class: string; label: string }> = {
      connected: { class: 'status-connected', label: t('deviceList.statusConnected') },
      disconnected: { class: 'status-disconnected', label: t('deviceList.statusDisconnected') },
      error: { class: 'status-error', label: t('deviceList.statusError') }
    };

    const statusInfo = statusMap[status.toLowerCase()] || statusMap.disconnected;
    return <span className={`status-badge ${statusInfo.class}`}>{statusInfo.label}</span>;
  };

  const formatLastReading = (timestamp: string | null) => {
    if (!timestamp) {
      return t('deviceList.noReadings');
    }

    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) {
      return t('deviceList.justNow');
    } else if (diffMins < 60) {
      return t('deviceList.minutesAgo', { count: diffMins });
    } else {
      return date.toLocaleString();
    }
  };

  if (loading) {
    return (
      <div className="device-list">
        <div className="loading">
          <div className="spinner"></div>
          <p>{t('common.loading')}</p>
        </div>
      </div>
    );
  }

  if (devices.length === 0) {
    return (
      <div className="device-list">
        <div className="empty-state">
          <p>{t('deviceList.noDevices')}</p>
          <p className="empty-hint">{t('deviceList.addDeviceHint')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="device-list">
      <table className="devices-table">
        <thead>
          <tr>
            <th>{t('deviceList.name')}</th>
            <th>{t('deviceList.address')}</th>
            <th>{t('deviceList.unit')}</th>
            <th>{t('deviceList.status')}</th>
            <th>{t('deviceList.lastReading')}</th>
            <th>{t('deviceList.interval')}</th>
            <th className="actions-column">{t('deviceList.actions')}</th>
          </tr>
        </thead>
        <tbody>
          {devices.map((device) => (
            <tr key={device.id}>
              <td className="device-name">{device.name}</td>
              <td className="device-address">
                {device.modbus_ip}:{device.modbus_port}
              </td>
              <td>{device.unit}</td>
              <td>{getStatusBadge(device.status)}</td>
              <td className="last-reading">{formatLastReading(device.last_reading_at)}</td>
              <td>{device.sampling_interval}s</td>
              <td className="actions-cell">
                <div className="actions-group">
                  <button
                    className="btn-icon btn-test"
                    onClick={() => onTestConnection(device)}
                    title={t('deviceList.testConnection')}
                  >
                    <span className="icon">🔌</span>
                  </button>
                  <button
                    className="btn-icon btn-edit"
                    onClick={() => onEdit(device)}
                    title={t('common.edit')}
                  >
                    <span className="icon">✏️</span>
                  </button>
                  <button
                    className="btn-icon btn-delete"
                    onClick={() => onDelete(device)}
                    title={t('common.delete')}
                  >
                    <span className="icon">🗑️</span>
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default DeviceList;
