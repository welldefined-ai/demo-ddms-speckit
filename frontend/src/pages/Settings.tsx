import React from 'react';
import { useTranslation } from 'react-i18next';
import './Settings.css';

const Settings: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="settings-page">
      <div className="page-header">
        <div>
          <h1>{t('nav.settings')}</h1>
          <p className="page-description">
            {t('settings.description', { defaultValue: 'Manage your application settings and preferences' })}
          </p>
        </div>
      </div>

      <div className="settings-sections">
        <div className="settings-card">
          <div className="card-icon">🎨</div>
          <h2>Theme Settings</h2>
          <p>Customize the appearance of your application</p>
          <span className="badge">Coming Soon</span>
        </div>

        <div className="settings-card">
          <div className="card-icon">🔔</div>
          <h2>Notifications</h2>
          <p>Configure alert and notification preferences</p>
          <span className="badge">Coming Soon</span>
        </div>

        <div className="settings-card">
          <div className="card-icon">🔐</div>
          <h2>Security</h2>
          <p>Manage security settings and authentication</p>
          <span className="badge">Coming Soon</span>
        </div>

        <div className="settings-card">
          <div className="card-icon">⚙️</div>
          <h2>System Settings</h2>
          <p>Configure system-wide application settings</p>
          <span className="badge">Coming Soon</span>
        </div>

        <div className="settings-card">
          <div className="card-icon">📊</div>
          <h2>Data Management</h2>
          <p>Control data retention and export settings</p>
          <span className="badge">Coming Soon</span>
        </div>

        <div className="settings-card">
          <div className="card-icon">🔌</div>
          <h2>Integrations</h2>
          <p>Connect with external services and APIs</p>
          <span className="badge">Coming Soon</span>
        </div>
      </div>
    </div>
  );
};

export default Settings;
