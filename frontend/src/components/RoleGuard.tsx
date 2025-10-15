/**
 * RoleGuard component - restricts access based on user role (T096)
 *
 * Features:
 * - Checks if user has required role
 * - Shows forbidden message or redirects if unauthorized
 * - Supports multiple allowed roles
 */
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

interface RoleGuardProps {
  children: React.ReactNode;
  allowedRoles: string[];
  fallbackPath?: string;
  showForbiddenMessage?: boolean;
}

const RoleGuard: React.FC<RoleGuardProps> = ({
  children,
  allowedRoles,
  fallbackPath = '/dashboard',
  showForbiddenMessage = true,
}) => {
  const { t } = useTranslation();

  // Get current user role
  const getCurrentUserRole = (): string | null => {
    try {
      const userStr = localStorage.getItem('user');
      if (!userStr) return null;

      const user = JSON.parse(userStr);
      return user.role || null;
    } catch (error) {
      console.error('Failed to parse user data:', error);
      return null;
    }
  };

  const userRole = getCurrentUserRole();

  // Check if user has required role
  if (!userRole || !allowedRoles.includes(userRole)) {
    if (showForbiddenMessage) {
      return (
        <div style={forbiddenStyles.container}>
          <div style={forbiddenStyles.content}>
            <h1 style={forbiddenStyles.title}>
              {t('roleGuard.accessDenied', { defaultValue: 'Access Denied' })}
            </h1>
            <p style={forbiddenStyles.message}>
              {t('roleGuard.insufficientPermissions', {
                defaultValue:
                  'You do not have permission to access this page. Required roles: ' +
                  allowedRoles.join(', '),
              })}
            </p>
            <a href={fallbackPath} style={forbiddenStyles.link}>
              {t('roleGuard.goBack', { defaultValue: 'Go to Dashboard' })}
            </a>
          </div>
        </div>
      );
    }

    // Redirect without message
    return <Navigate to={fallbackPath} replace />;
  }

  return <>{children}</>;
};

// Inline styles for forbidden message
const forbiddenStyles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '100vh',
    padding: '2rem',
    background: '#f5f5f5',
  },
  content: {
    textAlign: 'center',
    background: 'white',
    padding: '3rem',
    borderRadius: '8px',
    boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
    maxWidth: '500px',
  },
  title: {
    color: '#dc3545',
    marginBottom: '1rem',
    fontSize: '2rem',
  },
  message: {
    color: '#6c757d',
    marginBottom: '2rem',
    lineHeight: '1.6',
  },
  link: {
    display: 'inline-block',
    padding: '0.75rem 1.5rem',
    background: '#667eea',
    color: 'white',
    textDecoration: 'none',
    borderRadius: '4px',
    fontWeight: '500',
    transition: 'background 0.2s',
  },
};

export default RoleGuard;
