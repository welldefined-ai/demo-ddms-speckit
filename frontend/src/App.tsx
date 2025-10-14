/**
 * Main App component with React Router setup and authentication (T098)
 */
import React, { Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { I18nextProvider } from 'react-i18next';
import i18n from './services/i18n';
import { AuthProvider } from './contexts/AuthContext';
import Layout from './components/Layout';
import PrivateRoute from './components/PrivateRoute';
import RoleGuard from './components/RoleGuard';

// Import pages
import Dashboard from './pages/Dashboard';
import DeviceConfig from './pages/DeviceConfig';
import Login from './pages/Login';
import UserManagement from './pages/UserManagement';
import Historical from './pages/Historical';
import Groups from './pages/Groups';

// Placeholder pages - will be implemented in upcoming user stories
const SettingsPage = () => <div>Settings Page (Coming in Polish phase)</div>;

const App: React.FC = () => {
  return (
    <I18nextProvider i18n={i18n}>
      <Suspense fallback={<div>Loading...</div>}>
        <BrowserRouter>
          <AuthProvider>
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<Login />} />

              {/* Protected routes with layout */}
              <Route
                element={
                  <PrivateRoute>
                    <Layout />
                  </PrivateRoute>
                }
              >
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/devices" element={<DeviceConfig />} />
                <Route path="/historical" element={<Historical />} />
                <Route path="/groups" element={<Groups />} />
                <Route path="/groups/:groupId" element={<Groups />} />
                <Route
                  path="/users"
                  element={
                    <RoleGuard allowedRoles={['owner', 'admin']}>
                      <UserManagement />
                    </RoleGuard>
                  }
                />
                <Route path="/settings" element={<SettingsPage />} />

                {/* Redirect root to dashboard */}
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
              </Route>

              {/* 404 catch-all */}
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </AuthProvider>
        </BrowserRouter>
      </Suspense>
    </I18nextProvider>
  );
};

export default App;
