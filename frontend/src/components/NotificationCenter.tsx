/**
 * NotificationCenter component - Dropdown panel for displaying notifications
 *
 * Features:
 * - Display list of notifications with icons based on severity
 * - Mark as read/unread functionality
 * - Dismiss notifications
 * - Mark all as read
 * - Empty state when no notifications
 * - Loading state
 * - Real-time updates via SSE
 */
import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import {
  notificationApi,
  Notification,
  NotificationSSEClient,
  NotificationStreamData,
} from '../services/notifications';
import {
  requestNotificationPermission,
  shouldRequestPermission,
  markPermissionAsked,
  showDeviceDisconnectNotification,
  getNotificationPermission,
} from '../utils/browserNotifications';
import './NotificationCenter.css';

interface NotificationCenterProps {
  isOpen: boolean;
  onClose: () => void;
  onUnreadCountChange?: (count: number) => void;
}

const NotificationCenter: React.FC<NotificationCenterProps> = ({
  isOpen,
  onClose,
  onUnreadCountChange,
}) => {
  const { t } = useTranslation();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const sseClientRef = useRef<NotificationSSEClient | null>(null);
  const previousNotificationsRef = useRef<Notification[]>([]);

  // Request notification permission on mount
  useEffect(() => {
    const requestPermission = async () => {
      if (shouldRequestPermission()) {
        markPermissionAsked();
        const permission = await requestNotificationPermission();
        if (permission === 'granted') {
          console.log('Browser notification permission granted');
        }
      }
    };

    requestPermission();
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

  // Fetch notifications and set up SSE
  useEffect(() => {
    if (isOpen) {
      fetchNotifications();
    }

    // Set up SSE for real-time updates
    if (!sseClientRef.current) {
      sseClientRef.current = new NotificationSSEClient({
        onMessage: (data: NotificationStreamData) => {
          const previousNotifications = previousNotificationsRef.current;
          const currentNotifications = data.notifications;

          // Detect new device disconnect notifications
          if (previousNotifications.length > 0 && getNotificationPermission() === 'granted') {
            const newNotifications = currentNotifications.filter(
              (current) =>
                !previousNotifications.some((prev) => prev.id === current.id) &&
                current.type === 'device_disconnect' &&
                !current.read_at
            );

            // Show browser notification for each new device disconnect
            newNotifications.forEach((notification) => {
              const deviceName = notification.metadata?.device_name || 'Unknown Device';
              const deviceIp = notification.metadata?.device_ip || '';

              showDeviceDisconnectNotification(deviceName, deviceIp, () => {
                // Bring window to focus when browser notification is clicked
                // The user will see updated notification count in header
              });
            });
          }

          // Update state
          previousNotificationsRef.current = currentNotifications;
          setNotifications(currentNotifications);
          setUnreadCount(data.unread_count);
          if (onUnreadCountChange) {
            onUnreadCountChange(data.unread_count);
          }
        },
        onError: (error) => {
          console.error('Notification SSE error:', error);
        },
      });

      sseClientRef.current.connect();
    }

    return () => {
      // Cleanup SSE connection on unmount
      if (sseClientRef.current) {
        sseClientRef.current.disconnect();
        sseClientRef.current = null;
      }
    };
  }, [isOpen, onUnreadCountChange]);

  const fetchNotifications = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await notificationApi.getNotifications(false, 50, 0);
      setNotifications(response.notifications);
      setUnreadCount(response.unread_count);
      if (onUnreadCountChange) {
        onUnreadCountChange(response.unread_count);
      }
    } catch (err) {
      console.error('Failed to fetch notifications:', err);
      setError('Failed to load notifications');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsRead = async (notificationId: string) => {
    try {
      await notificationApi.markAsRead(notificationId);
      // Update local state
      setNotifications((prev) =>
        prev.map((n) =>
          n.id === notificationId ? { ...n, read_at: new Date().toISOString() } : n
        )
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
      if (onUnreadCountChange) {
        onUnreadCountChange(Math.max(0, unreadCount - 1));
      }
    } catch (err) {
      console.error('Failed to mark notification as read:', err);
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await notificationApi.markAllAsRead();
      // Update local state
      setNotifications((prev) =>
        prev.map((n) => ({ ...n, read_at: new Date().toISOString() }))
      );
      setUnreadCount(0);
      if (onUnreadCountChange) {
        onUnreadCountChange(0);
      }
    } catch (err) {
      console.error('Failed to mark all as read:', err);
    }
  };

  const handleDismiss = async (notificationId: string) => {
    try {
      await notificationApi.dismiss(notificationId);
      // Remove from local state
      setNotifications((prev) => prev.filter((n) => n.id !== notificationId));
      const notification = notifications.find((n) => n.id === notificationId);
      if (notification && !notification.read_at) {
        setUnreadCount((prev) => Math.max(0, prev - 1));
        if (onUnreadCountChange) {
          onUnreadCountChange(Math.max(0, unreadCount - 1));
        }
      }
    } catch (err) {
      console.error('Failed to dismiss notification:', err);
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return '🔴';
      case 'error':
        return '❌';
      case 'warning':
        return '⚠️';
      case 'info':
        return 'ℹ️';
      default:
        return '📢';
    }
  };

  const getSeverityClass = (severity: string) => {
    return `notification-severity-${severity}`;
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return date.toLocaleDateString();
  };

  if (!isOpen) return null;

  return (
    <div className="notification-center-dropdown" ref={dropdownRef}>
      <div className="notification-header">
        <h3 className="notification-title">
          Notifications {unreadCount > 0 && <span className="unread-badge">({unreadCount})</span>}
        </h3>
        {notifications.length > 0 && unreadCount > 0 && (
          <button className="btn-mark-all-read" onClick={handleMarkAllAsRead}>
            Mark all as read
          </button>
        )}
      </div>

      <div className="notification-list">
        {loading && (
          <div className="notification-loading">
            <div className="spinner"></div>
            <p>Loading notifications...</p>
          </div>
        )}

        {error && (
          <div className="notification-error">
            <p>{error}</p>
            <button onClick={fetchNotifications}>Retry</button>
          </div>
        )}

        {!loading && !error && notifications.length === 0 && (
          <div className="notification-empty">
            <div className="empty-icon">🔔</div>
            <p className="empty-title">No notifications</p>
            <p className="empty-subtitle">You're all caught up!</p>
          </div>
        )}

        {!loading &&
          !error &&
          notifications.map((notification) => (
            <div
              key={notification.id}
              className={`notification-item ${
                !notification.read_at ? 'notification-unread' : ''
              } ${getSeverityClass(notification.severity)}`}
            >
              <div className="notification-icon">
                {getSeverityIcon(notification.severity)}
              </div>
              <div className="notification-content">
                <div className="notification-header-row">
                  <h4 className="notification-item-title">{notification.title}</h4>
                  <button
                    className="btn-dismiss"
                    onClick={() => handleDismiss(notification.id)}
                    title="Dismiss"
                  >
                    ×
                  </button>
                </div>
                <p className="notification-message">{notification.message}</p>
                <div className="notification-footer">
                  <span className="notification-time">
                    {formatTimestamp(notification.created_at)}
                  </span>
                  {!notification.read_at && (
                    <button
                      className="btn-mark-read"
                      onClick={() => handleMarkAsRead(notification.id)}
                    >
                      Mark as read
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
      </div>
    </div>
  );
};

export default NotificationCenter;
