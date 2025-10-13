/**
 * User Management page - manage user accounts (T094)
 *
 * Features:
 * - List all users with roles
 * - Create new users (owner only)
 * - Delete users (owner only)
 * - Cannot delete owner account
 * - Cannot create owner role
 */
import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '../services/api';
import './UserManagement.css';

interface User {
  id: string;
  username: string;
  role: string;
  language_preference: string;
  created_at: string;
  updated_at: string;
}

interface CreateUserFormData {
  username: string;
  password: string;
  confirmPassword: string;
  role: string;
  language_preference: string;
}

const UserManagement: React.FC = () => {
  const { t } = useTranslation();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState<CreateUserFormData>({
    username: '',
    password: '',
    confirmPassword: '',
    role: 'admin',
    language_preference: 'en',
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Get current user role
  const currentUserRole = JSON.parse(localStorage.getItem('user') || '{}').role;
  const isOwner = currentUserRole === 'owner';

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.getUsers();
      setUsers(response.data);
    } catch (err: any) {
      console.error('Failed to fetch users:', err);
      setError(
        err.response?.data?.detail ||
          t('userManagement.fetchError', {
            defaultValue: 'Failed to load users',
          })
      );
    } finally {
      setLoading(false);
    }
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!formData.username.trim()) {
      errors.username = t('userManagement.usernameRequired', {
        defaultValue: 'Username is required',
      });
    } else if (formData.username.length < 3) {
      errors.username = t('userManagement.usernameTooShort', {
        defaultValue: 'Username must be at least 3 characters',
      });
    }

    if (!formData.password) {
      errors.password = t('userManagement.passwordRequired', {
        defaultValue: 'Password is required',
      });
    } else if (formData.password.length < 8) {
      errors.password = t('userManagement.passwordTooShort', {
        defaultValue: 'Password must be at least 8 characters',
      });
    }

    if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = t('userManagement.passwordMismatch', {
        defaultValue: 'Passwords do not match',
      });
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      await api.createUser({
        username: formData.username,
        password: formData.password,
        role: formData.role,
        language_preference: formData.language_preference,
      });

      setSuccessMessage(
        t('userManagement.userCreated', {
          defaultValue: `User ${formData.username} created successfully`,
        })
      );

      // Reset form
      setFormData({
        username: '',
        password: '',
        confirmPassword: '',
        role: 'admin',
        language_preference: 'en',
      });
      setShowCreateForm(false);
      setFormErrors({});

      // Refresh user list
      fetchUsers();

      // Clear success message after 5 seconds
      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err: any) {
      console.error('Failed to create user:', err);
      const errorMessage =
        err.response?.data?.detail ||
        t('userManagement.createError', {
          defaultValue: 'Failed to create user',
        });
      setFormErrors({ general: errorMessage });
    }
  };

  const handleDeleteUser = async (userId: string, username: string, role: string) => {
    // Prevent deleting owner
    if (role === 'owner') {
      alert(
        t('userManagement.cannotDeleteOwner', {
          defaultValue: 'Cannot delete owner account',
        })
      );
      return;
    }

    const confirmDelete = window.confirm(
      t('userManagement.confirmDelete', {
        defaultValue: `Are you sure you want to delete user ${username}?`,
      })
    );

    if (!confirmDelete) {
      return;
    }

    try {
      await api.deleteUser(userId);
      setSuccessMessage(
        t('userManagement.userDeleted', {
          defaultValue: `User ${username} deleted successfully`,
        })
      );
      fetchUsers();

      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err: any) {
      console.error('Failed to delete user:', err);
      alert(
        err.response?.data?.detail ||
          t('userManagement.deleteError', {
            defaultValue: 'Failed to delete user',
          })
      );
    }
  };

  if (loading) {
    return (
      <div className="user-management">
        <h1>{t('userManagement.title', { defaultValue: 'User Management' })}</h1>
        <div className="loading">
          {t('common.loading', { defaultValue: 'Loading...' })}
        </div>
      </div>
    );
  }

  if (error && !isOwner && currentUserRole !== 'admin') {
    return (
      <div className="user-management">
        <h1>{t('userManagement.title', { defaultValue: 'User Management' })}</h1>
        <div className="error-message">
          {t('userManagement.accessDenied', {
            defaultValue: 'Access denied. Only owner and admin can view users.',
          })}
        </div>
      </div>
    );
  }

  return (
    <div className="user-management">
      <div className="user-management-header">
        <h1>{t('userManagement.title', { defaultValue: 'User Management' })}</h1>
        {isOwner && !showCreateForm && (
          <button
            className="btn-create"
            onClick={() => setShowCreateForm(true)}
          >
            {t('userManagement.createUser', { defaultValue: 'Create User' })}
          </button>
        )}
      </div>

      {successMessage && (
        <div className="success-message">{successMessage}</div>
      )}

      {error && (
        <div className="error-message">{error}</div>
      )}

      {showCreateForm && isOwner && (
        <div className="create-user-form">
          <h2>{t('userManagement.newUser', { defaultValue: 'New User' })}</h2>
          <form onSubmit={handleCreateUser}>
            {formErrors.general && (
              <div className="form-error">{formErrors.general}</div>
            )}

            <div className="form-group">
              <label htmlFor="username">
                {t('userManagement.username', { defaultValue: 'Username' })}
              </label>
              <input
                type="text"
                id="username"
                name="username"
                value={formData.username}
                onChange={(e) =>
                  setFormData({ ...formData, username: e.target.value })
                }
                className={formErrors.username ? 'input-error' : ''}
              />
              {formErrors.username && (
                <span className="field-error">{formErrors.username}</span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="password">
                {t('userManagement.password', { defaultValue: 'Password' })}
              </label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={(e) =>
                  setFormData({ ...formData, password: e.target.value })
                }
                className={formErrors.password ? 'input-error' : ''}
              />
              {formErrors.password && (
                <span className="field-error">{formErrors.password}</span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="confirmPassword">
                {t('userManagement.confirmPassword', {
                  defaultValue: 'Confirm Password',
                })}
              </label>
              <input
                type="password"
                id="confirmPassword"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={(e) =>
                  setFormData({ ...formData, confirmPassword: e.target.value })
                }
                className={formErrors.confirmPassword ? 'input-error' : ''}
              />
              {formErrors.confirmPassword && (
                <span className="field-error">{formErrors.confirmPassword}</span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="role">
                {t('userManagement.role', { defaultValue: 'Role' })}
              </label>
              <select
                id="role"
                name="role"
                value={formData.role}
                onChange={(e) =>
                  setFormData({ ...formData, role: e.target.value })
                }
              >
                <option value="admin">
                  {t('userManagement.roleAdmin', { defaultValue: 'Admin' })}
                </option>
                <option value="read_only">
                  {t('userManagement.roleReadOnly', { defaultValue: 'Read Only' })}
                </option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="language">
                {t('userManagement.language', { defaultValue: 'Language' })}
              </label>
              <select
                id="language"
                name="language_preference"
                value={formData.language_preference}
                onChange={(e) =>
                  setFormData({ ...formData, language_preference: e.target.value })
                }
              >
                <option value="en">English</option>
                <option value="zh">中文</option>
              </select>
            </div>

            <div className="form-actions">
              <button type="submit" className="btn-submit">
                {t('userManagement.createButton', { defaultValue: 'Create' })}
              </button>
              <button
                type="button"
                className="btn-cancel"
                onClick={() => {
                  setShowCreateForm(false);
                  setFormErrors({});
                }}
              >
                {t('common.cancel', { defaultValue: 'Cancel' })}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="users-table">
        <table>
          <thead>
            <tr>
              <th>{t('userManagement.username', { defaultValue: 'Username' })}</th>
              <th>{t('userManagement.role', { defaultValue: 'Role' })}</th>
              <th>{t('userManagement.language', { defaultValue: 'Language' })}</th>
              <th>{t('userManagement.created', { defaultValue: 'Created' })}</th>
              {isOwner && (
                <th>{t('userManagement.actions', { defaultValue: 'Actions' })}</th>
              )}
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td>{user.username}</td>
                <td>
                  <span className={`role-badge role-${user.role}`}>
                    {user.role.replace('_', ' ')}
                  </span>
                </td>
                <td>{user.language_preference === 'en' ? 'English' : '中文'}</td>
                <td>{new Date(user.created_at).toLocaleDateString()}</td>
                {isOwner && (
                  <td>
                    {user.role !== 'owner' ? (
                      <button
                        className="btn-delete"
                        onClick={() =>
                          handleDeleteUser(user.id, user.username, user.role)
                        }
                        title={t('userManagement.deleteUser', {
                          defaultValue: 'Delete user',
                        })}
                      >
                        {t('common.delete', { defaultValue: 'Delete' })}
                      </button>
                    ) : (
                      <span className="owner-label">
                        {t('userManagement.ownerAccount', {
                          defaultValue: 'Owner',
                        })}
                      </span>
                    )}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>

        {users.length === 0 && (
          <div className="empty-state">
            {t('userManagement.noUsers', { defaultValue: 'No users found' })}
          </div>
        )}
      </div>
    </div>
  );
};

export default UserManagement;
