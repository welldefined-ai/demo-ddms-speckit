/**
 * Main App component with React Router setup
 */
import React, { Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { I18nextProvider } from 'react-i18next';
import i18n from './services/i18n';
import Layout from './components/Layout';

// Import pages
import Dashboard from './pages/Dashboard';
import DeviceConfig from './pages/DeviceConfig';

// Placeholder pages - will be implemented in upcoming user stories
const HistoricalPage = () => <div>Historical Page (Coming in US4)</div>;
const GroupsPage = () => <div>Groups Page (Coming in US5)</div>;
const UsersPage = () => <div>Users Page (Coming in US3)</div>;
const SettingsPage = () => <div>Settings Page (Coming in Polish phase)</div>;
const LoginPage = () => <div>Login Page (Coming in US3)</div>;

const App: React.FC = () => {
  return (
    <I18nextProvider i18n={i18n}>
      <Suspense fallback={<div>Loading...</div>}>
        <BrowserRouter>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginPage />} />

            {/* Protected routes with layout */}
            <Route element={<Layout />}>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/devices" element={<DeviceConfig />} />
              <Route path="/historical" element={<HistoricalPage />} />
              <Route path="/groups" element={<GroupsPage />} />
              <Route path="/users" element={<UsersPage />} />
              <Route path="/settings" element={<SettingsPage />} />

              {/* Redirect root to dashboard */}
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
            </Route>

            {/* 404 catch-all */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </Suspense>
    </I18nextProvider>
  );
};

export default App;
