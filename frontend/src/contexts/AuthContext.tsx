/**
 * AuthContext - manages authentication state across the application (T097)
 *
 * Features:
 * - Global authentication state
 * - Login/logout functions
 * - Current user data
 * - Role-based access helpers
 */
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';

interface User {
  id: string;
  username: string;
  role: string;
  language_preference: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  hasRole: (roles: string | string[]) => boolean;
  updateUser: (user: User) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  // Initialize auth state from localStorage
  useEffect(() => {
    const initAuth = () => {
      try {
        const token = localStorage.getItem('access_token');
        const userStr = localStorage.getItem('user');

        if (token && userStr) {
          const userData = JSON.parse(userStr);
          setUser(userData);
        }
      } catch (error) {
        console.error('Failed to initialize auth:', error);
        // Clear invalid data
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = async (username: string, password: string) => {
    try {
      const response = await api.login(username, password);

      // Store access token and user data
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));

      setUser(response.data.user);
    } catch (error) {
      // Re-throw to let the caller handle the error
      throw error;
    }
  };

  const logout = async () => {
    try {
      // Call logout API
      await api.logout();
    } catch (error) {
      console.error('Logout API call failed:', error);
      // Continue with local logout even if API call fails
    } finally {
      // Clear local storage and state
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      setUser(null);

      // Redirect to login
      navigate('/login');
    }
  };

  const hasRole = (roles: string | string[]): boolean => {
    if (!user) return false;

    const rolesArray = Array.isArray(roles) ? roles : [roles];
    return rolesArray.includes(user.role);
  };

  const updateUser = (updatedUser: User) => {
    setUser(updatedUser);
    localStorage.setItem('user', JSON.stringify(updatedUser));
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    hasRole,
    updateUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Custom hook to use auth context
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
};

export default AuthContext;
