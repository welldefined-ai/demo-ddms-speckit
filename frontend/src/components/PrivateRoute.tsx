/**
 * PrivateRoute component - protects routes requiring authentication (T095)
 *
 * Features:
 * - Checks if user is authenticated
 * - Redirects to login if not authenticated
 * - Preserves intended destination for redirect after login
 */
import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';

interface PrivateRouteProps {
  children: React.ReactNode;
}

const PrivateRoute: React.FC<PrivateRouteProps> = ({ children }) => {
  const location = useLocation();

  // Check if user is authenticated
  const isAuthenticated = (): boolean => {
    const token = localStorage.getItem('access_token');
    const user = localStorage.getItem('user');

    return !!(token && user);
  };

  if (!isAuthenticated()) {
    // Redirect to login, preserving intended destination
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};

export default PrivateRoute;
