/**
 * Sidebar navigation component
 */
import React from 'react';
import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import './Sidebar.css';

const Sidebar: React.FC = () => {
  const { t } = useTranslation();

  const navItems = [
    { path: '/dashboard', label: t('nav.dashboard') },
    { path: '/devices', label: t('nav.devices') },
    { path: '/historical', label: t('nav.historical') },
    { path: '/groups', label: t('nav.groups') },
    { path: '/users', label: t('nav.users') },
    { path: '/settings', label: t('nav.settings') },
  ];

  return (
    <nav className="sidebar">
      <ul className="nav-list">
        {navItems.map(item => (
          <li key={item.path} className="nav-item">
            <NavLink
              to={item.path}
              className={({ isActive }) =>
                isActive ? 'nav-link active' : 'nav-link'
              }
            >
              {item.label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
};

export default Sidebar;
