/**
 * ExportButton component - Download historical data as CSV (User Story 4)
 */
import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import api from '../utils/api';

export interface ExportButtonProps {
  deviceId: string;
  startTime?: Date;
  endTime?: Date;
  aggregate?: string;
  disabled?: boolean;
}

const ExportButton: React.FC<ExportButtonProps> = ({
  deviceId,
  startTime,
  endTime,
  aggregate,
  disabled = false,
}) => {
  const { t } = useTranslation();
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async () => {
    setExporting(true);
    setError(null);

    try {
      // Build query parameters
      const params: Record<string, string> = {};

      if (startTime) {
        params.start_time = startTime.toISOString();
      }

      if (endTime) {
        params.end_time = endTime.toISOString();
      }

      if (aggregate) {
        params.aggregate = aggregate;
      }

      // Make API request for CSV export
      const response = await api.get(`/api/export/device/${deviceId}`, {
        params,
        responseType: 'blob', // Important: tells axios to treat response as binary
      });

      // Extract filename from Content-Disposition header
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'export.csv';

      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1];
        }
      }

      // Create blob URL and trigger download
      const blob = new Blob([response.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();

      // Cleanup
      window.URL.revokeObjectURL(url);
      document.body.removeChild(link);

      // Show success message (optional)
      console.log(`Successfully exported ${filename}`);

    } catch (err: any) {
      console.error('Export failed:', err);
      let errorMessage = t('historical.exportFailed', { defaultValue: 'Failed to export data' });

      if (err.response?.status === 404) {
        errorMessage = t('historical.deviceNotFound', { defaultValue: 'Device not found' });
      } else if (err.response?.status === 401) {
        errorMessage = t('auth.sessionExpired', { defaultValue: 'Session expired, please login again' });
      }

      setError(errorMessage);

      // Clear error after 5 seconds
      setTimeout(() => setError(null), 5000);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="export-button-container">
      <button
        className="btn-export"
        onClick={handleExport}
        disabled={disabled || exporting}
        style={{
          padding: '10px 20px',
          backgroundColor: disabled || exporting ? '#d9d9d9' : '#52c41a',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: disabled || exporting ? 'not-allowed' : 'pointer',
          fontSize: '14px',
          fontWeight: 'bold',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}
      >
        {/* Download icon */}
        <svg
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="currentColor"
          style={{ opacity: exporting ? 0.5 : 1 }}
        >
          <path d="M8 12l-4-4h2.5V4h3v4H12l-4 4z" />
          <path d="M14 14H2v-2h12v2z" />
        </svg>

        {exporting
          ? t('historical.exporting', { defaultValue: 'Exporting...' })
          : t('common.export', { defaultValue: 'Export CSV' })
        }
      </button>

      {error && (
        <div
          className="alert-error"
          style={{
            marginTop: '8px',
            padding: '8px 12px',
            backgroundColor: '#fff2f0',
            border: '1px solid #ffccc7',
            borderRadius: '4px',
            color: '#cf1322',
            fontSize: '14px',
          }}
        >
          {error}
        </div>
      )}
    </div>
  );
};

export default ExportButton;
