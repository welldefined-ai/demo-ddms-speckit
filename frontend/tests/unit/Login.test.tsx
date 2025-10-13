/**
 * Unit tests for Login component (T102)
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { I18nextProvider } from 'react-i18next';
import { BrowserRouter } from 'react-router-dom';
import i18n from '../../src/services/i18n';
import Login from '../../src/pages/Login';
import { api } from '../../src/services/api';

// Mock the API module
vi.mock('../../src/services/api', () => ({
  api: {
    login: vi.fn(),
  },
}));

// Mock react-router-dom navigation
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Test helper to render with providers
const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <I18nextProvider i18n={i18n}>
        {component}
      </I18nextProvider>
    </BrowserRouter>
  );
};

describe('Login Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe('Rendering', () => {
    it('should render login form with all fields', () => {
      renderWithProviders(<Login />);

      expect(screen.getByRole('heading', { name: /login/i })).toBeInTheDocument();
      expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
    });

    it('should render subtitle', () => {
      renderWithProviders(<Login />);

      expect(screen.getByText(/Device Data Monitoring System/i)).toBeInTheDocument();
    });

    it('should have password input type', () => {
      renderWithProviders(<Login />);

      const passwordInput = screen.getByLabelText(/password/i);
      expect(passwordInput).toHaveAttribute('type', 'password');
    });

    it('should have autocomplete attributes', () => {
      renderWithProviders(<Login />);

      const usernameInput = screen.getByLabelText(/username/i);
      const passwordInput = screen.getByLabelText(/password/i);

      expect(usernameInput).toHaveAttribute('autocomplete', 'username');
      expect(passwordInput).toHaveAttribute('autocomplete', 'current-password');
    });
  });

  describe('Form Validation', () => {
    it('should show error when username is empty', async () => {
      const user = userEvent.setup();
      renderWithProviders(<Login />);

      const submitButton = screen.getByRole('button', { name: /login/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/username is required/i)).toBeInTheDocument();
      });

      expect(api.login).not.toHaveBeenCalled();
    });

    it('should show error when password is empty', async () => {
      const user = userEvent.setup();
      renderWithProviders(<Login />);

      await user.type(screen.getByLabelText(/username/i), 'testuser');

      const submitButton = screen.getByRole('button', { name: /login/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/password is required/i)).toBeInTheDocument();
      });

      expect(api.login).not.toHaveBeenCalled();
    });

    it('should show error when both fields are empty', async () => {
      const user = userEvent.setup();
      renderWithProviders(<Login />);

      const submitButton = screen.getByRole('button', { name: /login/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/username is required/i)).toBeInTheDocument();
        expect(screen.getByText(/password is required/i)).toBeInTheDocument();
      });
    });

    it('should clear field errors when user starts typing', async () => {
      const user = userEvent.setup();
      renderWithProviders(<Login />);

      // Trigger validation errors
      const submitButton = screen.getByRole('button', { name: /login/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/username is required/i)).toBeInTheDocument();
      });

      // Start typing in username
      await user.type(screen.getByLabelText(/username/i), 'a');

      await waitFor(() => {
        expect(screen.queryByText(/username is required/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Successful Login', () => {
    it('should call API and navigate on successful login', async () => {
      const user = userEvent.setup();
      const mockResponse = {
        data: {
          access_token: 'test-access-token',
          refresh_token: 'test-refresh-token',
          token_type: 'bearer',
          user: {
            id: '123',
            username: 'testuser',
            role: 'admin',
            language_preference: 'en',
          },
        },
      };

      vi.mocked(api.login).mockResolvedValue(mockResponse);

      renderWithProviders(<Login />);

      await user.type(screen.getByLabelText(/username/i), 'testuser');
      await user.type(screen.getByLabelText(/password/i), 'password123');

      const submitButton = screen.getByRole('button', { name: /login/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(api.login).toHaveBeenCalledWith('testuser', 'password123');
      });

      // Check localStorage
      expect(localStorage.getItem('access_token')).toBe('test-access-token');
      expect(localStorage.getItem('user')).toBe(
        JSON.stringify(mockResponse.data.user)
      );

      // Check navigation
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });

    it('should disable form during submission', async () => {
      const user = userEvent.setup();
      let resolveLogin: () => void;
      const loginPromise = new Promise<any>((resolve) => {
        resolveLogin = () => resolve({
          data: {
            access_token: 'token',
            user: { id: '1', username: 'test', role: 'admin', language_preference: 'en' },
          },
        });
      });

      vi.mocked(api.login).mockReturnValue(loginPromise);

      renderWithProviders(<Login />);

      await user.type(screen.getByLabelText(/username/i), 'testuser');
      await user.type(screen.getByLabelText(/password/i), 'password123');

      const submitButton = screen.getByRole('button', { name: /login/i });
      await user.click(submitButton);

      // Button should be disabled
      await waitFor(() => {
        expect(submitButton).toBeDisabled();
        expect(submitButton).toHaveTextContent(/logging in/i);
      });

      // Resolve the promise
      resolveLogin!();

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalled();
      });
    });
  });

  describe('Login Errors', () => {
    it('should show error for invalid credentials (401)', async () => {
      const user = userEvent.setup();
      const mockError = {
        response: {
          status: 401,
          data: {
            detail: 'Invalid username or password',
          },
        },
      };

      vi.mocked(api.login).mockRejectedValue(mockError);

      renderWithProviders(<Login />);

      await user.type(screen.getByLabelText(/username/i), 'testuser');
      await user.type(screen.getByLabelText(/password/i), 'wrongpassword');

      const submitButton = screen.getByRole('button', { name: /login/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/invalid username or password/i)).toBeInTheDocument();
      });

      // Should not store anything or navigate
      expect(localStorage.getItem('access_token')).toBeNull();
      expect(mockNavigate).not.toHaveBeenCalled();
    });

    it('should show error for rate limiting (429)', async () => {
      const user = userEvent.setup();
      const mockError = {
        response: {
          status: 429,
          data: {
            detail: 'Too many failed login attempts. Try again in 300 seconds.',
          },
        },
      };

      vi.mocked(api.login).mockRejectedValue(mockError);

      renderWithProviders(<Login />);

      await user.type(screen.getByLabelText(/username/i), 'testuser');
      await user.type(screen.getByLabelText(/password/i), 'password123');

      const submitButton = screen.getByRole('button', { name: /login/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/Too many failed login attempts/i)).toBeInTheDocument();
      });
    });

    it('should show generic error for network issues', async () => {
      const user = userEvent.setup();
      const mockError = {
        request: {},
        message: 'Network Error',
      };

      vi.mocked(api.login).mockRejectedValue(mockError);

      renderWithProviders(<Login />);

      await user.type(screen.getByLabelText(/username/i), 'testuser');
      await user.type(screen.getByLabelText(/password/i), 'password123');

      const submitButton = screen.getByRole('button', { name: /login/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });
    });

    it('should show custom error message from server', async () => {
      const user = userEvent.setup();
      const mockError = {
        response: {
          status: 500,
          data: {
            detail: 'Server is temporarily unavailable',
          },
        },
      };

      vi.mocked(api.login).mockRejectedValue(mockError);

      renderWithProviders(<Login />);

      await user.type(screen.getByLabelText(/username/i), 'testuser');
      await user.type(screen.getByLabelText(/password/i), 'password123');

      const submitButton = screen.getByRole('button', { name: /login/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/Server is temporarily unavailable/i)).toBeInTheDocument();
      });
    });

    it('should re-enable form after error', async () => {
      const user = userEvent.setup();
      const mockError = {
        response: {
          status: 401,
          data: { detail: 'Invalid credentials' },
        },
      };

      vi.mocked(api.login).mockRejectedValue(mockError);

      renderWithProviders(<Login />);

      await user.type(screen.getByLabelText(/username/i), 'testuser');
      await user.type(screen.getByLabelText(/password/i), 'wrongpassword');

      const submitButton = screen.getByRole('button', { name: /login/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
      });

      // Form should be enabled again
      expect(submitButton).not.toBeDisabled();
      expect(screen.getByLabelText(/username/i)).not.toBeDisabled();
      expect(screen.getByLabelText(/password/i)).not.toBeDisabled();
    });
  });

  describe('Form Interaction', () => {
    it('should allow typing in username field', async () => {
      const user = userEvent.setup();
      renderWithProviders(<Login />);

      const usernameInput = screen.getByLabelText(/username/i) as HTMLInputElement;
      await user.type(usernameInput, 'myusername');

      expect(usernameInput.value).toBe('myusername');
    });

    it('should allow typing in password field', async () => {
      const user = userEvent.setup();
      renderWithProviders(<Login />);

      const passwordInput = screen.getByLabelText(/password/i) as HTMLInputElement;
      await user.type(passwordInput, 'mypassword123');

      expect(passwordInput.value).toBe('mypassword123');
    });

    it('should submit form on Enter key in password field', async () => {
      const user = userEvent.setup();
      const mockResponse = {
        data: {
          access_token: 'token',
          user: { id: '1', username: 'test', role: 'admin', language_preference: 'en' },
        },
      };

      vi.mocked(api.login).mockResolvedValue(mockResponse);

      renderWithProviders(<Login />);

      await user.type(screen.getByLabelText(/username/i), 'testuser');
      await user.type(screen.getByLabelText(/password/i), 'password123{Enter}');

      await waitFor(() => {
        expect(api.login).toHaveBeenCalled();
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper form structure', () => {
      renderWithProviders(<Login />);

      const form = screen.getByRole('button', { name: /login/i }).closest('form');
      expect(form).toBeInTheDocument();
    });

    it('should have alert role for error messages', async () => {
      const user = userEvent.setup();
      const mockError = {
        response: {
          status: 401,
          data: { detail: 'Invalid credentials' },
        },
      };

      vi.mocked(api.login).mockRejectedValue(mockError);

      renderWithProviders(<Login />);

      await user.type(screen.getByLabelText(/username/i), 'test');
      await user.type(screen.getByLabelText(/password/i), 'test');
      await user.click(screen.getByRole('button', { name: /login/i }));

      await waitFor(() => {
        const errorBanner = screen.getByRole('alert');
        expect(errorBanner).toBeInTheDocument();
      });
    });

    it('should have proper label associations', () => {
      renderWithProviders(<Login />);

      const usernameInput = screen.getByLabelText(/username/i);
      const passwordInput = screen.getByLabelText(/password/i);

      expect(usernameInput).toHaveAttribute('id');
      expect(passwordInput).toHaveAttribute('id');
    });
  });
});
