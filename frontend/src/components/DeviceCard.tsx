/**
 * DeviceCard component - displays device info with status color coding
 *
 * Color coding:
 * - Green: Normal status
 * - Yellow/Orange: Warning status
 * - Red: Critical status
 */
import React from 'react';
import { useTranslation } from 'react-i18next';
import './DeviceCard.css';

export interface DeviceCardProps {
  deviceId: string;
  deviceName: string;
  value: number;
  unit: string;
  status: 'normal' | 'warning' | 'critical';
  timestamp: string;
  onClick?: () => void;
}

const DeviceCard: React.FC<DeviceCardProps> = ({
  deviceName,
  value,
  unit,
  status,
  timestamp,
  onClick,
}) => {
  const { t } = useTranslation();

  const getStatusColor = () => {
    switch (status) {
      case 'normal':
        return '#52c41a'; // Green
      case 'warning':
        return '#faad14'; // Orange
      case 'critical':
        return '#f5222d'; // Red
      default:
        return '#d9d9d9'; // Gray
    }
  };

  const formatTimestamp = (ts: string) => {
    const date = new Date(ts);
    return date.toLocaleString();
  };

  return (
    <div className="device-card" onClick={onClick} style={{ borderColor: getStatusColor() }}>
      <div className="device-card-header">
        <h3 className="device-card-title">{deviceName}</h3>
        <span
          className={`device-card-status device-card-status-${status}`}
          style={{ backgroundColor: getStatusColor() }}
        >
          {t(`device.status.${status}`)}
        </span>
      </div>

      <div className="device-card-body">
        <div className="device-card-value">
          <span className="value-number">{value.toFixed(2)}</span>
          <span className="value-unit">{unit}</span>
        </div>

        <div className="device-card-timestamp">
          <small>{formatTimestamp(timestamp)}</small>
        </div>
      </div>
    </div>
  );
};

export default DeviceCard;
