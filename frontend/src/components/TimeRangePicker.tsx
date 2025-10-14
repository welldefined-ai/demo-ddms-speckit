/**
 * TimeRangePicker component - Select time ranges for historical data (User Story 4)
 */
import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

export interface TimeRange {
  start: Date;
  end: Date;
  label: string;
}

export interface TimeRangePickerProps {
  onRangeChange: (range: TimeRange) => void;
  defaultRange?: string; // '1h', '24h', '7d', '30d', 'custom'
}

const TimeRangePicker: React.FC<TimeRangePickerProps> = ({
  onRangeChange,
  defaultRange = '24h',
}) => {
  const { t } = useTranslation();
  const [selectedRange, setSelectedRange] = useState(defaultRange);
  const [showCustomPicker, setShowCustomPicker] = useState(false);
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');

  // Predefined time ranges
  const predefinedRanges = [
    { value: '1h', label: t('historical.lastHour', { defaultValue: 'Last Hour' }), hours: 1 },
    { value: '24h', label: t('historical.last24Hours', { defaultValue: 'Last 24 Hours' }), hours: 24 },
    { value: '7d', label: t('historical.last7Days', { defaultValue: 'Last 7 Days' }), hours: 7 * 24 },
    { value: '30d', label: t('historical.last30Days', { defaultValue: 'Last 30 Days' }), hours: 30 * 24 },
  ];

  // Automatically trigger the default range on mount
  useEffect(() => {
    const defaultRangeConfig = predefinedRanges.find(r => r.value === defaultRange);
    if (defaultRangeConfig) {
      const end = new Date();
      const start = new Date(end.getTime() - defaultRangeConfig.hours * 60 * 60 * 1000);
      onRangeChange({ start, end, label: defaultRangeConfig.label });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run on mount

  const handlePredefinedRangeClick = (rangeValue: string, hours: number, label: string) => {
    setSelectedRange(rangeValue);
    setShowCustomPicker(false);

    const end = new Date();
    const start = new Date(end.getTime() - hours * 60 * 60 * 1000);

    onRangeChange({ start, end, label });
  };

  const handleCustomRangeClick = () => {
    setSelectedRange('custom');
    setShowCustomPicker(true);

    // Set default dates to last 7 days
    const end = new Date();
    const start = new Date(end.getTime() - 7 * 24 * 60 * 60 * 1000);

    setCustomStart(start.toISOString().slice(0, 16)); // YYYY-MM-DDTHH:mm format
    setCustomEnd(end.toISOString().slice(0, 16));
  };

  const handleCustomRangeApply = () => {
    if (!customStart || !customEnd) {
      alert(t('historical.selectBothDates', { defaultValue: 'Please select both start and end dates' }));
      return;
    }

    const start = new Date(customStart);
    const end = new Date(customEnd);

    if (start >= end) {
      alert(t('historical.invalidDateRange', { defaultValue: 'Start date must be before end date' }));
      return;
    }

    const label = t('historical.customRange', {
      defaultValue: `${start.toLocaleDateString()} - ${end.toLocaleDateString()}`,
      start: start.toLocaleDateString(),
      end: end.toLocaleDateString(),
    });

    onRangeChange({ start, end, label });
  };

  return (
    <div className="time-range-picker" style={{ marginBottom: '16px' }}>
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
        <label style={{ fontWeight: 'bold', marginRight: '8px' }}>
          {t('historical.timeRange', { defaultValue: 'Time Range:' })}
        </label>

        {/* Predefined ranges */}
        {predefinedRanges.map((range) => (
          <button
            key={range.value}
            data-time-range={range.value}
            className={`btn ${selectedRange === range.value ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => handlePredefinedRangeClick(range.value, range.hours, range.label)}
            style={{
              padding: '8px 16px',
              border: selectedRange === range.value ? '2px solid #1890ff' : '1px solid #d9d9d9',
              backgroundColor: selectedRange === range.value ? '#1890ff' : 'white',
              color: selectedRange === range.value ? 'white' : '#333',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px',
            }}
          >
            {range.label}
          </button>
        ))}

        {/* Custom range button */}
        <button
          data-time-range="custom"
          className={`btn ${selectedRange === 'custom' ? 'btn-primary' : 'btn-outline'}`}
          onClick={handleCustomRangeClick}
          style={{
            padding: '8px 16px',
            border: selectedRange === 'custom' ? '2px solid #1890ff' : '1px solid #d9d9d9',
            backgroundColor: selectedRange === 'custom' ? '#1890ff' : 'white',
            color: selectedRange === 'custom' ? 'white' : '#333',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '14px',
          }}
        >
          {t('historical.custom', { defaultValue: 'Custom' })}
        </button>
      </div>

      {/* Custom date picker */}
      {showCustomPicker && (
        <div
          className="custom-date-picker"
          style={{
            marginTop: '16px',
            padding: '16px',
            border: '1px solid #d9d9d9',
            borderRadius: '4px',
            backgroundColor: '#fafafa',
          }}
        >
          <div style={{ display: 'flex', gap: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '4px', fontWeight: 'bold', fontSize: '14px' }}>
                {t('historical.startDate', { defaultValue: 'Start Date:' })}
              </label>
              <input
                type="datetime-local"
                name="start_date"
                value={customStart}
                onChange={(e) => setCustomStart(e.target.value)}
                style={{
                  padding: '8px',
                  border: '1px solid #d9d9d9',
                  borderRadius: '4px',
                  fontSize: '14px',
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '4px', fontWeight: 'bold', fontSize: '14px' }}>
                {t('historical.endDate', { defaultValue: 'End Date:' })}
              </label>
              <input
                type="datetime-local"
                name="end_date"
                value={customEnd}
                onChange={(e) => setCustomEnd(e.target.value)}
                style={{
                  padding: '8px',
                  border: '1px solid #d9d9d9',
                  borderRadius: '4px',
                  fontSize: '14px',
                }}
              />
            </div>

            <div style={{ marginTop: '20px' }}>
              <button
                className="btn-apply-range"
                onClick={handleCustomRangeApply}
                style={{
                  padding: '8px 24px',
                  backgroundColor: '#52c41a',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: 'bold',
                }}
              >
                {t('common.apply', { defaultValue: 'Apply' })}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Selected range display */}
      {selectedRange !== 'custom' && (
        <div className="selected" style={{ marginTop: '8px', color: '#888', fontSize: '14px' }}>
          {predefinedRanges.find(r => r.value === selectedRange)?.label}
        </div>
      )}
    </div>
  );
};

export default TimeRangePicker;
