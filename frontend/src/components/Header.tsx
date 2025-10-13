/**
 * Header component with app title and user menu
 */
import React from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';

const Header: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
  };

  const toggleLanguage = () => {
    const newLang = i18n.language === 'en' ? 'zh' : 'en';
    i18n.changeLanguage(newLang);
  };

  return (
    <header className="header">
      <div className="header-left">
        <h1 className="app-title">{t('app.title')}</h1>
      </div>
      <div className="header-right">
        {user && (
          <span className="user-info">
            {user.username} ({user.role})
          </span>
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
