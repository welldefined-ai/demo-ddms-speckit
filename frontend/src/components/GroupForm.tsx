import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import './GroupForm.css';

interface Device {
  id: string;
  name: string;
  unit: string;
  status: string;
}

interface GroupFormData {
  name: string;
  description: string;
  device_ids: string[];
}

interface GroupFormProps {
  initialData?: Partial<GroupFormData>;
  devices: Device[];
  onSubmit: (data: GroupFormData) => Promise<void>;
  onCancel: () => void;
  isEdit?: boolean;
}

const GroupForm: React.FC<GroupFormProps> = ({
  initialData,
  devices,
  onSubmit,
  onCancel,
  isEdit = false
}) => {
  const { t } = useTranslation();

  const [formData, setFormData] = useState<GroupFormData>({
    name: initialData?.name || '',
    description: initialData?.description || '',
    device_ids: initialData?.device_ids || []
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    // Required fields
    if (!formData.name.trim()) {
      newErrors.name = t('groups.errors.nameRequired');
    } else if (formData.name.length > 100) {
      newErrors.name = t('groups.errors.nameTooLong');
    }

    if (formData.device_ids.length === 0) {
      newErrors.devices = t('groups.errors.devicesRequired');
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Clear error for this field
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const handleDeviceToggle = (deviceId: string) => {
    setFormData(prev => {
      const isSelected = prev.device_ids.includes(deviceId);
      return {
        ...prev,
        device_ids: isSelected
          ? prev.device_ids.filter(id => id !== deviceId)
          : [...prev.device_ids, deviceId]
      };
    });

    // Clear devices error when user selects at least one device
    if (errors.devices) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors.devices;
        return newErrors;
      });
    }
  };

  const handleSelectAll = () => {
    const filteredDeviceIds = filteredDevices.map(d => d.id);
    setFormData(prev => ({
      ...prev,
      device_ids: filteredDeviceIds
    }));
  };

  const handleDeselectAll = () => {
    setFormData(prev => ({
      ...prev,
      device_ids: []
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      await onSubmit(formData);
    } catch (error) {
      console.error('Error submitting form:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Filter devices based on search term
  const filteredDevices = devices.filter(device =>
    device.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <form className="group-form" onSubmit={handleSubmit}>
      <h2>{isEdit ? t('groups.editGroup') : t('groups.createGroup')}</h2>

      <div className="form-section">
        <div className="form-group">
          <label htmlFor="name">
            {t('groups.groupName')} <span className="required">*</span>
          </label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            className={errors.name ? 'error' : ''}
            maxLength={100}
            autoFocus
          />
          {errors.name && <span className="error-message">{errors.name}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="description">{t('groups.groupDescription')}</label>
          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            rows={3}
            maxLength={500}
          />
        </div>
      </div>

      <div className="form-section">
        <h3>
          {t('groups.selectDevices')} <span className="required">*</span>
        </h3>

        <div className="device-selection-header">
          <div className="search-box">
            <input
              type="text"
              placeholder={t('common.search')}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
          </div>

          <div className="selection-actions">
            <button
              type="button"
              onClick={handleSelectAll}
              className="btn-link"
            >
              Select All
            </button>
            <button
              type="button"
              onClick={handleDeselectAll}
              className="btn-link"
            >
              Deselect All
            </button>
          </div>
        </div>

        <div className="device-selection-summary">
          {formData.device_ids.length === 0 ? (
            <span className="text-muted">{t('groups.noDevicesSelected')}</span>
          ) : (
            <span className="text-success">
              {t('groups.devicesSelected', { count: formData.device_ids.length })}
            </span>
          )}
        </div>

        {errors.devices && (
          <div className="error-message devices-error">{errors.devices}</div>
        )}

        <div className="device-list">
          {filteredDevices.length === 0 ? (
            <div className="no-devices">
              {searchTerm ? 'No devices match your search' : 'No devices available'}
            </div>
          ) : (
            filteredDevices.map(device => (
              <label key={device.id} className="device-item">
                <input
                  type="checkbox"
                  checked={formData.device_ids.includes(device.id)}
                  onChange={() => handleDeviceToggle(device.id)}
                />
                <div className="device-info">
                  <span className="device-name">{device.name}</span>
                  <span className="device-unit">{device.unit}</span>
                </div>
                <span className={`device-status status-${device.status.toLowerCase()}`}>
                  {device.status}
                </span>
              </label>
            ))
          )}
        </div>
      </div>

      <div className="form-actions">
        <button
          type="button"
          onClick={onCancel}
          className="btn-secondary"
          disabled={isSubmitting}
        >
          {t('common.cancel')}
        </button>
        <button
          type="submit"
          className="btn-primary"
          disabled={isSubmitting}
        >
          {isSubmitting
            ? t('common.saving')
            : isEdit
            ? t('common.update')
            : t('common.create')}
        </button>
      </div>
    </form>
  );
};

export default GroupForm;
