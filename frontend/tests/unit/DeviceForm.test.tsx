/**
 * Unit tests for DeviceForm component (T075)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { I18nextProvider } from 'react-i18next';
import i18n from '../../src/services/i18n';
import DeviceForm from '../../src/components/DeviceForm';

// Test helpers
const renderWithI18n = (component: React.ReactElement) => {
  return render(
    <I18nextProvider i18n={i18n}>
      {component}
    </I18nextProvider>
  );
};

describe('DeviceForm Component', () => {
  const mockOnSubmit = vi.fn();
  const mockOnCancel = vi.fn();

  beforeEach(() => {
    mockOnSubmit.mockClear();
    mockOnCancel.mockClear();
  });

  describe('Rendering', () => {
    it('should render create form with correct title', () => {
      renderWithI18n(
        <DeviceForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          isEdit={false}
        />
      );

      expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Create New Device');
    });

    it('should render edit form with correct title', () => {
      renderWithI18n(
        <DeviceForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          isEdit={true}
        />
      );

      expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Edit Device');
    });

    it('should render all required form fields', () => {
      renderWithI18n(
        <DeviceForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      // Basic fields
      expect(screen.getByLabelText(/Device Name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Unit of Measurement/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Sampling Interval/i)).toBeInTheDocument();

      // Modbus fields
      expect(screen.getByLabelText(/Modbus IP Address/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Modbus Port/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Slave ID/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Register Address/i)).toBeInTheDocument();

      // Threshold fields
      expect(screen.getByLabelText(/Warning Lower Threshold/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Warning Upper Threshold/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Critical Lower Threshold/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Critical Upper Threshold/i)).toBeInTheDocument();
    });

    it('should pre-fill form with initial data', () => {
      const initialData = {
        name: 'Existing Device',
        modbus_ip: '192.168.1.100',
        modbus_port: 502,
        modbus_slave_id: 1,
        modbus_register: 0,
        modbus_register_count: 1,
        unit: '°C',
        sampling_interval: 30,
        threshold_warning_lower: '10',
        threshold_warning_upper: '50',
        threshold_critical_lower: '0',
        threshold_critical_upper: '80',
        retention_days: 90
      };

      renderWithI18n(
        <DeviceForm
          initialData={initialData}
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          isEdit={true}
        />
      );

      expect(screen.getByDisplayValue('Existing Device')).toBeInTheDocument();
      expect(screen.getByDisplayValue('192.168.1.100')).toBeInTheDocument();
      expect(screen.getByDisplayValue('°C')).toBeInTheDocument();
      expect(screen.getByDisplayValue('30')).toBeInTheDocument();
    });
  });

  describe('Validation', () => {
    it('should validate required name field', async () => {
      const user = userEvent.setup();

      renderWithI18n(
        <DeviceForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      const submitButton = screen.getByRole('button', { name: /Create/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/Device name is required/i)).toBeInTheDocument();
      });

      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('should validate required IP address field', async () => {
      const user = userEvent.setup();

      renderWithI18n(
        <DeviceForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      // Fill name and unit only
      await user.type(screen.getByLabelText(/Device Name/i), 'Test Device');
      await user.type(screen.getByLabelText(/Unit of Measurement/i), 'bar');

      const submitButton = screen.getByRole('button', { name: /Create/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/IP address is required/i)).toBeInTheDocument();
      });
    });

    it('should validate IP address format', async () => {
      const user = userEvent.setup();

      renderWithI18n(
        <DeviceForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      await user.type(screen.getByLabelText(/Device Name/i), 'Test Device');
      await user.type(screen.getByLabelText(/Modbus IP Address/i), 'invalid-ip');
      await user.type(screen.getByLabelText(/Unit of Measurement/i), 'bar');

      const submitButton = screen.getByRole('button', { name: /Create/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/Invalid IP address format/i)).toBeInTheDocument();
      });
    });

    it('should validate warning threshold ordering', async () => {
      const user = userEvent.setup();

      renderWithI18n(
        <DeviceForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      await user.type(screen.getByLabelText(/Device Name/i), 'Test Device');
      await user.type(screen.getByLabelText(/Modbus IP Address/i), '192.168.1.100');
      await user.type(screen.getByLabelText(/Unit of Measurement/i), 'bar');

      // Invalid: lower >= upper
      await user.type(screen.getByLabelText(/Warning Lower Threshold/i), '60');
      await user.type(screen.getByLabelText(/Warning Upper Threshold/i), '40');

      const submitButton = screen.getByRole('button', { name: /Create/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/Warning lower threshold must be less than/i)).toBeInTheDocument();
      });
    });

    it('should validate critical thresholds outside warning thresholds', async () => {
      const user = userEvent.setup();

      renderWithI18n(
        <DeviceForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      await user.type(screen.getByLabelText(/Device Name/i), 'Test Device');
      await user.type(screen.getByLabelText(/Modbus IP Address/i), '192.168.1.100');
      await user.type(screen.getByLabelText(/Unit of Measurement/i), 'bar');

      await user.type(screen.getByLabelText(/Warning Lower Threshold/i), '10');
      await user.type(screen.getByLabelText(/Warning Upper Threshold/i), '50');

      // Invalid: critical lower >= warning lower
      await user.type(screen.getByLabelText(/Critical Lower Threshold/i), '15');
      await user.type(screen.getByLabelText(/Critical Upper Threshold/i), '80');

      const submitButton = screen.getByRole('button', { name: /Create/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/Critical thresholds must be outside warning thresholds/i)).toBeInTheDocument();
      });
    });

    it('should clear validation errors when field is corrected', async () => {
      const user = userEvent.setup();

      renderWithI18n(
        <DeviceForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      // Submit empty form to trigger validation
      const submitButton = screen.getByRole('button', { name: /Create/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/Device name is required/i)).toBeInTheDocument();
      });

      // Correct the field
      await user.type(screen.getByLabelText(/Device Name/i), 'Corrected Name');

      // Error should be cleared
      await waitFor(() => {
        expect(screen.queryByText(/Device name is required/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Form Submission', () => {
    it('should submit form with valid data', async () => {
      const user = userEvent.setup();
      mockOnSubmit.mockResolvedValue(undefined);

      renderWithI18n(
        <DeviceForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      // Fill all required fields
      await user.type(screen.getByLabelText(/Device Name/i), 'New Device');
      await user.type(screen.getByLabelText(/Modbus IP Address/i), '192.168.1.100');
      await user.type(screen.getByLabelText(/Unit of Measurement/i), 'bar');

      const submitButton = screen.getByRole('button', { name: /Create/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith(
          expect.objectContaining({
            name: 'New Device',
            modbus_ip: '192.168.1.100',
            unit: 'bar'
          })
        );
      });
    });

    it('should disable submit button while submitting', async () => {
      const user = userEvent.setup();
      let resolveSubmit: () => void;
      const submitPromise = new Promise<void>((resolve) => {
        resolveSubmit = resolve;
      });
      mockOnSubmit.mockReturnValue(submitPromise);

      renderWithI18n(
        <DeviceForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      // Fill required fields
      await user.type(screen.getByLabelText(/Device Name/i), 'Test Device');
      await user.type(screen.getByLabelText(/Modbus IP Address/i), '192.168.1.100');
      await user.type(screen.getByLabelText(/Unit of Measurement/i), 'bar');

      const submitButton = screen.getByRole('button', { name: /Create/i });
      await user.click(submitButton);

      // Button should be disabled
      await waitFor(() => {
        expect(submitButton).toBeDisabled();
      });

      // Resolve the promise
      resolveSubmit!();

      // Button should be enabled again
      await waitFor(() => {
        expect(submitButton).not.toBeDisabled();
      });
    });

    it('should handle submission errors gracefully', async () => {
      const user = userEvent.setup();
      const error = new Error('Submission failed');
      mockOnSubmit.mockRejectedValue(error);

      renderWithI18n(
        <DeviceForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      // Fill required fields
      await user.type(screen.getByLabelText(/Device Name/i), 'Test Device');
      await user.type(screen.getByLabelText(/Modbus IP Address/i), '192.168.1.100');
      await user.type(screen.getByLabelText(/Unit of Measurement/i), 'bar');

      const submitButton = screen.getByRole('button', { name: /Create/i });
      await user.click(submitButton);

      // Form should still be visible (not closed on error)
      await waitFor(() => {
        expect(screen.getByRole('heading', { level: 2 })).toBeInTheDocument();
      });
    });
  });

  describe('Form Actions', () => {
    it('should call onCancel when cancel button is clicked', async () => {
      const user = userEvent.setup();

      renderWithI18n(
        <DeviceForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      const cancelButton = screen.getByRole('button', { name: /Cancel/i });
      await user.click(cancelButton);

      expect(mockOnCancel).toHaveBeenCalled();
    });

    it('should disable cancel button while submitting', async () => {
      const user = userEvent.setup();
      let resolveSubmit: () => void;
      const submitPromise = new Promise<void>((resolve) => {
        resolveSubmit = resolve;
      });
      mockOnSubmit.mockReturnValue(submitPromise);

      renderWithI18n(
        <DeviceForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      // Fill and submit
      await user.type(screen.getByLabelText(/Device Name/i), 'Test Device');
      await user.type(screen.getByLabelText(/Modbus IP Address/i), '192.168.1.100');
      await user.type(screen.getByLabelText(/Unit of Measurement/i), 'bar');

      const submitButton = screen.getByRole('button', { name: /Create/i });
      await user.click(submitButton);

      // Cancel button should also be disabled
      const cancelButton = screen.getByRole('button', { name: /Cancel/i });
      await waitFor(() => {
        expect(cancelButton).toBeDisabled();
      });

      // Resolve
      resolveSubmit!();

      await waitFor(() => {
        expect(cancelButton).not.toBeDisabled();
      });
    });
  });

  describe('Field Updates', () => {
    it('should update field values on user input', async () => {
      const user = userEvent.setup();

      renderWithI18n(
        <DeviceForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      const nameInput = screen.getByLabelText(/Device Name/i) as HTMLInputElement;
      await user.type(nameInput, 'Updated Name');

      expect(nameInput.value).toBe('Updated Name');
    });

    it('should handle numeric field inputs', async () => {
      const user = userEvent.setup();

      renderWithI18n(
        <DeviceForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      );

      const portInput = screen.getByLabelText(/Modbus Port/i) as HTMLInputElement;
      await user.clear(portInput);
      await user.type(portInput, '5020');

      expect(portInput.value).toBe('5020');
    });
  });
});
