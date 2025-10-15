/**
 * Login page - user authentication (T093)
 *
 * Features:
 * - Username and password authentication
 * - Form validation
 * - Error handling
 * - Rate limit feedback
 * - Redirect to dashboard on success
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api } from '../services/api';
import './Login.css';

interface LoginFormData {
  username: string;
  password: string;
}

interface LoginFormErrors {
  username?: string;
  password?: string;
  general?: string;
}

const Login: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [formData, setFormData] = useState<LoginFormData>({
    username: '',
    password: '',
  });

  const [errors, setErrors] = useState<LoginFormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validateForm = (): boolean => {
    const newErrors: LoginFormErrors = {};

    if (!formData.username.trim()) {
      newErrors.username = t('login.usernameRequired', {
        defaultValue: 'Username is required',
      });
    }

    if (!formData.password) {
      newErrors.password = t('login.passwordRequired', {
        defaultValue: 'Password is required',
      });
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear error for this field when user starts typing
    if (errors[name as keyof LoginFormErrors]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    setErrors({});

    try {
      const response = await api.login(formData.username, formData.password);

      // Store access token and user data
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));

      // Redirect to dashboard
      navigate('/dashboard');
    } catch (error: any) {
      console.error('Login error:', error);

      let errorMessage = t('login.loginFailed', {
        defaultValue: 'Login failed. Please try again.',
      });

      if (error.response) {
        if (error.response.status === 401) {
          errorMessage = t('login.invalidCredentials', {
            defaultValue: 'Invalid username or password',
          });
        } else if (error.response.status === 429) {
          // Rate limited
          errorMessage = error.response.data.detail || t('login.rateLimited', {
            defaultValue: 'Too many login attempts. Please try again later.',
          });
        } else if (error.response.data?.detail) {
          errorMessage = error.response.data.detail;
        }
      } else if (error.request) {
        errorMessage = t('login.networkError', {
          defaultValue: 'Network error. Please check your connection.',
        });
      }

      setErrors({ general: errorMessage });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>{t('login.title', { defaultValue: 'Login' })}</h1>
          <p className="login-subtitle">
            {t('login.subtitle', {
              defaultValue: 'Device Data Monitoring System',
            })}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {errors.general && (
            <div className="login-error-banner" role="alert">
              {errors.general}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="username">
              {t('login.username', { defaultValue: 'Username' })}
            </label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              className={errors.username ? 'input-error' : ''}
              disabled={isSubmitting}
              autoComplete="username"
            />
            {errors.username && (
              <span className="field-error">{errors.username}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="password">
              {t('login.password', { defaultValue: 'Password' })}
            </label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className={errors.password ? 'input-error' : ''}
              disabled={isSubmitting}
              autoComplete="current-password"
            />
            {errors.password && (
              <span className="field-error">{errors.password}</span>
            )}
          </div>

          <button
            type="submit"
            className="login-button"
            disabled={isSubmitting}
          >
            {isSubmitting
              ? t('login.loggingIn', { defaultValue: 'Logging in...' })
              : t('login.loginButton', { defaultValue: 'Login' })}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Login;
