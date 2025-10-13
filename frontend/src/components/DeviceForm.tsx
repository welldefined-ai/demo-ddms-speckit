import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import './DeviceForm.css';

interface DeviceFormData {
  name: string;
  modbus_ip: string;
  modbus_port: number;
  modbus_slave_id: number;
  modbus_register: number;
  modbus_register_count: number;
  unit: string;
  sampling_interval: number;
  threshold_warning_lower: string;
  threshold_warning_upper: string;
  threshold_critical_lower: string;
  threshold_critical_upper: string;
  retention_days: number;
}

interface DeviceFormProps {
  initialData?: Partial<DeviceFormData>;
  onSubmit: (data: DeviceFormData) => Promise<void>;
  onCancel: () => void;
  isEdit?: boolean;
}

const DeviceForm: React.FC<DeviceFormProps> = ({
  initialData,
  onSubmit,
  onCancel,
  isEdit = false
}) => {
  const { t } = useTranslation();

  const [formData, setFormData] = useState<DeviceFormData>({
    name: initialData?.name || '',
    modbus_ip: initialData?.modbus_ip || '',
    modbus_port: initialData?.modbus_port || 502,
    modbus_slave_id: initialData?.modbus_slave_id || 1,
    modbus_register: initialData?.modbus_register || 0,
    modbus_register_count: initialData?.modbus_register_count || 1,
    unit: initialData?.unit || '',
    sampling_interval: initialData?.sampling_interval || 10,
    threshold_warning_lower: initialData?.threshold_warning_lower || '',
    threshold_warning_upper: initialData?.threshold_warning_upper || '',
    threshold_critical_lower: initialData?.threshold_critical_lower || '',
    threshold_critical_upper: initialData?.threshold_critical_upper || '',
    retention_days: initialData?.retention_days || 90
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    // Required fields
    if (!formData.name.trim()) {
      newErrors.name = t('deviceForm.errors.nameRequired');
    }

    if (!formData.modbus_ip.trim()) {
      newErrors.modbus_ip = t('deviceForm.errors.ipRequired');
    } else {
      // Basic IP validation
      const ipPattern = /^(\d{1,3}\.){3}\d{1,3}$/;
      if (!ipPattern.test(formData.modbus_ip)) {
        newErrors.modbus_ip = t('deviceForm.errors.invalidIp');
      }
    }

    if (!formData.unit.trim()) {
      newErrors.unit = t('deviceForm.errors.unitRequired');
    }

    // Validate thresholds ordering
    const warnLower = parseFloat(formData.threshold_warning_lower);
    const warnUpper = parseFloat(formData.threshold_warning_upper);
    const critLower = parseFloat(formData.threshold_critical_lower);
    const critUpper = parseFloat(formData.threshold_critical_upper);

    // Warning thresholds
    if (!isNaN(warnLower) && !isNaN(warnUpper)) {
      if (warnLower >= warnUpper) {
        newErrors.threshold_warning_upper = t('deviceForm.errors.warningOrderInvalid');
      }
    }

    // Critical thresholds
    if (!isNaN(critLower) && !isNaN(critUpper)) {
      if (critLower >= critUpper) {
        newErrors.threshold_critical_upper = t('deviceForm.errors.criticalOrderInvalid');
      }
    }

    // Critical must be outside warning
    if (!isNaN(critLower) && !isNaN(warnLower)) {
      if (critLower >= warnLower) {
        newErrors.threshold_critical_lower = t('deviceForm.errors.criticalInsideWarning');
      }
    }

    if (!isNaN(critUpper) && !isNaN(warnUpper)) {
      if (critUpper <= warnUpper) {
        newErrors.threshold_critical_upper = t('deviceForm.errors.criticalInsideWarning');
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? (value === '' ? '' : parseFloat(value) || 0) : value
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
      // Error handling is done by parent component
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form className="device-form" onSubmit={handleSubmit}>
      <h2>{isEdit ? t('deviceForm.titleEdit') : t('deviceForm.titleCreate')}</h2>

      <div className="form-section">
        <h3>{t('deviceForm.sectionBasic')}</h3>

        <div className="form-group">
          <label htmlFor="name">
            {t('deviceForm.name')} <span className="required">*</span>
          </label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            className={errors.name ? 'error' : ''}
            maxLength={100}
          />
          {errors.name && <span className="error-message">{errors.name}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="unit">
            {t('deviceForm.unit')} <span className="required">*</span>
          </label>
          <input
            type="text"
            id="unit"
            name="unit"
            value={formData.unit}
            onChange={handleChange}
            className={errors.unit ? 'error' : ''}
            placeholder="e.g., °C, RPM, bar"
            maxLength={20}
          />
          {errors.unit && <span className="error-message">{errors.unit}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="sampling_interval">{t('deviceForm.samplingInterval')}</label>
          <input
            type="number"
            id="sampling_interval"
            name="sampling_interval"
            value={formData.sampling_interval}
            onChange={handleChange}
            min={1}
            max={3600}
          />
          <span className="help-text">{t('deviceForm.samplingIntervalHelp')}</span>
        </div>

        <div className="form-group">
          <label htmlFor="retention_days">{t('deviceForm.retentionDays')}</label>
          <input
            type="number"
            id="retention_days"
            name="retention_days"
            value={formData.retention_days}
            onChange={handleChange}
            min={1}
            max={3650}
          />
        </div>
      </div>

      <div className="form-section">
        <h3>{t('deviceForm.sectionModbus')}</h3>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="modbus_ip">
              {t('deviceForm.modbusIp')} <span className="required">*</span>
            </label>
            <input
              type="text"
              id="modbus_ip"
              name="modbus_ip"
              value={formData.modbus_ip}
              onChange={handleChange}
              className={errors.modbus_ip ? 'error' : ''}
              placeholder="192.168.1.100"
            />
            {errors.modbus_ip && <span className="error-message">{errors.modbus_ip}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="modbus_port">{t('deviceForm.modbusPort')}</label>
            <input
              type="number"
              id="modbus_port"
              name="modbus_port"
              value={formData.modbus_port}
              onChange={handleChange}
              min={1}
              max={65535}
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="modbus_slave_id">{t('deviceForm.slaveId')}</label>
            <input
              type="number"
              id="modbus_slave_id"
              name="modbus_slave_id"
              value={formData.modbus_slave_id}
              onChange={handleChange}
              min={1}
              max={255}
            />
          </div>

          <div className="form-group">
            <label htmlFor="modbus_register">{t('deviceForm.register')}</label>
            <input
              type="number"
              id="modbus_register"
              name="modbus_register"
              value={formData.modbus_register}
              onChange={handleChange}
              min={0}
            />
          </div>

          <div className="form-group">
            <label htmlFor="modbus_register_count">{t('deviceForm.registerCount')}</label>
            <input
              type="number"
              id="modbus_register_count"
              name="modbus_register_count"
              value={formData.modbus_register_count}
              onChange={handleChange}
              min={1}
              max={100}
            />
          </div>
        </div>
      </div>

      <div className="form-section">
        <h3>{t('deviceForm.sectionThresholds')}</h3>
        <p className="section-help">{t('deviceForm.thresholdsHelp')}</p>

        <div className="thresholds-grid">
          <div className="form-group">
            <label htmlFor="threshold_warning_lower">{t('deviceForm.warningLower')}</label>
            <input
              type="number"
              id="threshold_warning_lower"
              name="threshold_warning_lower"
              value={formData.threshold_warning_lower}
              onChange={handleChange}
              step="any"
              placeholder="Optional"
            />
          </div>

          <div className="form-group">
            <label htmlFor="threshold_warning_upper">{t('deviceForm.warningUpper')}</label>
            <input
              type="number"
              id="threshold_warning_upper"
              name="threshold_warning_upper"
              value={formData.threshold_warning_upper}
              onChange={handleChange}
              step="any"
              placeholder="Optional"
              className={errors.threshold_warning_upper ? 'error' : ''}
            />
            {errors.threshold_warning_upper && (
              <span className="error-message">{errors.threshold_warning_upper}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="threshold_critical_lower">{t('deviceForm.criticalLower')}</label>
            <input
              type="number"
              id="threshold_critical_lower"
              name="threshold_critical_lower"
              value={formData.threshold_critical_lower}
              onChange={handleChange}
              step="any"
              placeholder="Optional"
              className={errors.threshold_critical_lower ? 'error' : ''}
            />
            {errors.threshold_critical_lower && (
              <span className="error-message">{errors.threshold_critical_lower}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="threshold_critical_upper">{t('deviceForm.criticalUpper')}</label>
            <input
              type="number"
              id="threshold_critical_upper"
              name="threshold_critical_upper"
              value={formData.threshold_critical_upper}
              onChange={handleChange}
              step="any"
              placeholder="Optional"
              className={errors.threshold_critical_upper ? 'error' : ''}
            />
            {errors.threshold_critical_upper && (
              <span className="error-message">{errors.threshold_critical_upper}</span>
            )}
          </div>
        </div>
      </div>

      <div className="form-actions">
        <button type="button" onClick={onCancel} className="btn-secondary" disabled={isSubmitting}>
          {t('common.cancel')}
        </button>
        <button type="submit" className="btn-primary" disabled={isSubmitting}>
          {isSubmitting ? t('common.saving') : isEdit ? t('common.update') : t('common.create')}
        </button>
      </div>
    </form>
  );
};

export default DeviceForm;
