/**
 * Header component with app title, notifications, and user menu
 */
import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import NotificationCenter from './NotificationCenter';
import { notificationApi } from '../services/notifications';
import './Header.css';

const Header: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { user, logout } = useAuth();
  const [notificationOpen, setNotificationOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  // Fetch initial unread count
  useEffect(() => {
    if (user) {
      fetchUnreadCount();
    }
  }, [user]);

  const fetchUnreadCount = async () => {
    try {
      const count = await notificationApi.getUnreadCount();
      setUnreadCount(count);
    } catch (err) {
      console.error('Failed to fetch unread count:', err);
    }
  };

  const handleLogout = async () => {
    await logout();
  };

  const toggleLanguage = () => {
    const newLang = i18n.language === 'en' ? 'zh' : 'en';
    i18n.changeLanguage(newLang);
  };

  const toggleNotifications = () => {
    setNotificationOpen(!notificationOpen);
  };

  const handleUnreadCountChange = (count: number) => {
    setUnreadCount(count);
  };

  return (
    <header className="header">
      <div className="header-left">
        <h1 className="app-title">{t('app.title')}</h1>
      </div>
      <div className="header-right">
        {user && (
          <>
            <span className="user-info">
              {user.username} ({user.role})
            </span>
            <div className="notification-bell-container">
              <button
                onClick={toggleNotifications}
                className="btn-notification"
                title="Notifications"
                aria-label="Notifications"
              >
                <span className="bell-icon">🔔</span>
                {unreadCount > 0 && (
                  <span className="notification-badge">{unreadCount > 99 ? '99+' : unreadCount}</span>
                )}
              </button>
              <NotificationCenter
                isOpen={notificationOpen}
                onClose={() => setNotificationOpen(false)}
                onUnreadCountChange={handleUnreadCountChange}
              />
            </div>
          </>
        )}
        <button onClick={toggleLanguage} className="btn-language">
          {i18n.language === 'en' ? '中文' : 'English'}
        </button>
        <button onClick={handleLogout} className="btn-logout">
          {t('auth.logout')}
        </button>
      </div>
    </header>
  );
};

export default Header;
