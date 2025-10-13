import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import DeviceList from '../components/DeviceList';
import DeviceForm from '../components/DeviceForm';
import './DeviceConfig.css';

interface Device {
  id: string;
  name: string;
  modbus_ip: string;
  modbus_port: number;
  modbus_slave_id: number;
  modbus_register: number;
  modbus_register_count: number;
  unit: string;
  sampling_interval: number;
  threshold_warning_lower: number | null;
  threshold_warning_upper: number | null;
  threshold_critical_lower: number | null;
  threshold_critical_upper: number | null;
  retention_days: number;
  status: string;
  last_reading_at: string | null;
}

const DeviceConfig: React.FC = () => {
  const { t } = useTranslation();
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingDevice, setEditingDevice] = useState<Device | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  useEffect(() => {
    fetchDevices();
  }, []);

  const fetchDevices = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/devices`);

      if (!response.ok) {
        throw new Error(t('deviceConfig.errors.fetchFailed'));
      }

      const data = await response.json();
      setDevices(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('deviceConfig.errors.unknown'));
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingDevice(null);
    setShowForm(true);
    setError(null);
    setSuccessMessage(null);
  };

  const handleEdit = (device: Device) => {
    setEditingDevice(device);
    setShowForm(true);
    setError(null);
    setSuccessMessage(null);
  };

  const handleCancelForm = () => {
    setShowForm(false);
    setEditingDevice(null);
    setError(null);
  };

  const handleSubmitForm = async (formData: any) => {
    try {
      const url = editingDevice
        ? `${API_BASE_URL}/api/devices/${editingDevice.id}`
        : `${API_BASE_URL}/api/devices`;

      const method = editingDevice ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || t('deviceConfig.errors.saveFailed'));
      }

      setShowForm(false);
      setEditingDevice(null);
      setSuccessMessage(
        editingDevice
          ? t('deviceConfig.success.deviceUpdated')
          : t('deviceConfig.success.deviceCreated')
      );

      // Refresh the list
      await fetchDevices();

      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('deviceConfig.errors.unknown'));
      throw err; // Re-throw to prevent form from closing
    }
  };

  const handleDelete = async (device: Device) => {
    if (!confirm(t('deviceConfig.confirmDelete', { name: device.name }))) {
      return;
    }

    const keepData = confirm(t('deviceConfig.confirmKeepData'));

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/devices/${device.id}?keep_data=${keepData}`,
        {
          method: 'DELETE',
        }
      );

      if (!response.ok) {
        throw new Error(t('deviceConfig.errors.deleteFailed'));
      }

      setSuccessMessage(t('deviceConfig.success.deviceDeleted'));
      await fetchDevices();

      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('deviceConfig.errors.unknown'));
    }
  };

  const handleTestConnection = async (device: Device) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/devices/${device.id}/test-connection`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(t('deviceConfig.errors.testFailed'));
      }

      const result = await response.json();

      if (result.success) {
        setSuccessMessage(t('deviceConfig.success.connectionSuccess', { name: device.name }));
      } else {
        setError(t('deviceConfig.errors.connectionFailed', { name: device.name, error: result.error }));
      }

      setTimeout(() => {
        setSuccessMessage(null);
        setError(null);
      }, 5000);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('deviceConfig.errors.unknown'));
    }
  };

  return (
    <div className="device-config-page">
      <div className="page-header">
        <div>
          <h1>{t('deviceConfig.title')}</h1>
          <p className="page-description">{t('deviceConfig.description')}</p>
        </div>
        {!showForm && (
          <button className="btn-create" onClick={handleCreate}>
            + {t('deviceConfig.createDevice')}
          </button>
        )}
      </div>

      {error && (
        <div className="alert alert-error">
          <span className="alert-icon">⚠️</span>
          <span>{error}</span>
          <button className="alert-close" onClick={() => setError(null)}>
            ×
          </button>
        </div>
      )}

      {successMessage && (
        <div className="alert alert-success">
          <span className="alert-icon">✓</span>
          <span>{successMessage}</span>
          <button className="alert-close" onClick={() => setSuccessMessage(null)}>
            ×
          </button>
        </div>
      )}

      {showForm ? (
        <DeviceForm
          initialData={editingDevice || undefined}
          onSubmit={handleSubmitForm}
          onCancel={handleCancelForm}
          isEdit={!!editingDevice}
        />
      ) : (
        <DeviceList
          devices={devices}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onTestConnection={handleTestConnection}
          loading={loading}
        />
      )}
    </div>
  );
};

export default DeviceConfig;
