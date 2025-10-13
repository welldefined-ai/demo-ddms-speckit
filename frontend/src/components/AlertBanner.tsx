/**
 * AlertBanner component - displays connection failure notifications
 */
import React from 'react';
import { useTranslation } from 'react-i18next';
import './AlertBanner.css';

export interface AlertBannerProps {
  message: string;
  type?: 'info' | 'warning' | 'error' | 'success';
  onClose?: () => void;
  closeable?: boolean;
}

const AlertBanner: React.FC<AlertBannerProps> = ({
  message,
  type = 'info',
  onClose,
  closeable = true,
}) => {
  const { t } = useTranslation();

  const getIcon = () => {
    switch (type) {
      case 'success':
        return '✓';
      case 'warning':
        return '⚠';
      case 'error':
        return '✕';
      default:
        return 'ℹ';
    }
  };

  return (
    <div className={`alert-banner alert-banner-${type}`}>
      <span className="alert-banner-icon">{getIcon()}</span>
      <span className="alert-banner-message">{message}</span>
      {closeable && (
        <button className="alert-banner-close" onClick={onClose} aria-label="Close">
          ×
        </button>
      )}
    </div>
  );
};

export default AlertBanner;
