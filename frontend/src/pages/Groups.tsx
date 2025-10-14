import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import GroupList from '../components/GroupList';
import GroupForm from '../components/GroupForm';
import GroupDashboard from '../components/GroupDashboard';
import { useAuth } from '../contexts/AuthContext';
import './Groups.css';

interface Device {
  id: string;
  name: string;
  unit: string;
  status: string;
}

interface GroupListItem {
  id: string;
  name: string;
  description: string | null;
  device_count: number;
  created_at: string;
  updated_at: string;
}

interface GroupDetail {
  id: string;
  name: string;
  description: string | null;
  devices: Device[];
  alert_summary: {
    normal: number;
    warning: number;
    critical: number;
  };
  created_at: string;
  updated_at: string;
}

interface GroupReading {
  device_id: string;
  device_name: string;
  timestamp: string;
  value: number;
  unit: string;
}

const Groups: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { groupId } = useParams<{ groupId?: string }>();
  const { user } = useAuth();

  const [groups, setGroups] = useState<GroupListItem[]>([]);
  const [devices, setDevices] = useState<Device[]>([]);
  const [groupDetail, setGroupDetail] = useState<GroupDetail | null>(null);
  const [groupReadings, setGroupReadings] = useState<GroupReading[]>([]);

  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingGroupId, setEditingGroupId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isExporting, setIsExporting] = useState(false);

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  const canEdit = user?.role === 'owner' || user?.role === 'admin';

  useEffect(() => {
    if (groupId) {
      // Viewing a specific group
      fetchGroupDetail(groupId);
      fetchGroupReadings(groupId);
    } else {
      // Viewing list of groups
      fetchGroups();
    }
    fetchDevices();
  }, [groupId]);

  const fetchGroups = async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/groups`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(t('groups.errors.fetchFailed'));
      }

      const data = await response.json();
      setGroups(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('groups.errors.fetchFailed'));
    } finally {
      setLoading(false);
    }
  };

  const fetchDevices = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/devices`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setDevices(data);
      }
    } catch (err) {
      console.error('Failed to fetch devices:', err);
    }
  };

  const fetchGroupDetail = async (id: string) => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/groups/${id}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error(t('groups.errors.groupNotFound'));
        }
        throw new Error(t('groups.errors.fetchGroupFailed'));
      }

      const data = await response.json();
      setGroupDetail(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('groups.errors.fetchGroupFailed'));
    } finally {
      setLoading(false);
    }
  };

  const fetchGroupReadings = async (id: string, hours: number = 24) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/groups/${id}/readings?hours=${hours}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setGroupReadings(data.readings || []);
      }
    } catch (err) {
      console.error('Failed to fetch group readings:', err);
    }
  };

  const handleCreate = () => {
    setEditingGroupId(null);
    setShowForm(true);
    setError(null);
    setSuccessMessage(null);
  };

  const handleEdit = async (id: string) => {
    setEditingGroupId(id);
    setShowForm(true);
    setError(null);
    setSuccessMessage(null);

    // Fetch group details to populate form
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/groups/${id}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        // Form will receive this data
      }
    } catch (err) {
      console.error('Failed to fetch group for editing:', err);
    }
  };

  const handleCancelForm = () => {
    setShowForm(false);
    setEditingGroupId(null);
    setError(null);
  };

  const handleSubmitForm = async (formData: any) => {
    try {
      const url = editingGroupId
        ? `${API_BASE_URL}/api/groups/${editingGroupId}`
        : `${API_BASE_URL}/api/groups`;

      const method = editingGroupId ? 'PUT' : 'POST';

      const token = localStorage.getItem('token');
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || t('groups.errors.createFailed'));
      }

      const savedGroup = await response.json();

      setShowForm(false);
      setEditingGroupId(null);
      setSuccessMessage(
        editingGroupId
          ? t('groups.groupUpdated', { name: savedGroup.name })
          : t('groups.groupCreated', { name: savedGroup.name })
      );

      // Refresh the list
      if (groupId) {
        await fetchGroupDetail(groupId);
      } else {
        await fetchGroups();
      }

      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('groups.errors.createFailed'));
      throw err;
    }
  };

  const handleDelete = async (id: string) => {
    // Find group name for confirmation
    const group = groups.find(g => g.id === id) || groupDetail;
    if (!group) return;

    if (!confirm(t('groups.confirmDelete', { name: group.name }))) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/groups/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(t('groups.errors.deleteFailed'));
      }

      setSuccessMessage(t('groups.groupDeleted', { name: group.name }));

      // If viewing the deleted group, navigate back to list
      if (groupId === id) {
        navigate('/groups');
      } else {
        await fetchGroups();
      }

      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('groups.errors.deleteFailed'));
    }
  };

  const handleExport = async () => {
    if (!groupId || !groupDetail) return;

    setIsExporting(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/export/group/${groupId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(t('groups.errors.exportFailed'));
      }

      // Get filename from Content-Disposition header
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = 'group_export.csv';
      if (contentDisposition) {
        const matches = /filename="?([^"]+)"?/.exec(contentDisposition);
        if (matches && matches[1]) {
          filename = matches[1];
        }
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      setSuccessMessage(t('common.success'));
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('groups.errors.exportFailed'));
    } finally {
      setIsExporting(false);
    }
  };

  // Render group dashboard view
  if (groupId && groupDetail) {
    return (
      <div className="groups-page">
        {error && (
          <div className="alert alert-error">
            <span className="alert-icon">⚠️</span>
            <span>{error}</span>
            <button className="alert-close" onClick={() => setError(null)}>×</button>
          </div>
        )}

        {successMessage && (
          <div className="alert alert-success">
            <span className="alert-icon">✓</span>
            <span>{successMessage}</span>
            <button className="alert-close" onClick={() => setSuccessMessage(null)}>×</button>
          </div>
        )}

        {loading ? (
          <div className="loading-spinner">Loading...</div>
        ) : (
          <GroupDashboard
            groupId={groupDetail.id}
            groupName={groupDetail.name}
            groupDescription={groupDetail.description || undefined}
            devices={groupDetail.devices}
            alertSummary={groupDetail.alert_summary}
            readings={groupReadings}
            onExport={handleExport}
            onEdit={() => handleEdit(groupDetail.id)}
            onDelete={() => handleDelete(groupDetail.id)}
            canEdit={canEdit}
            isExporting={isExporting}
          />
        )}
      </div>
    );
  }

  // Render groups list view
  return (
    <div className="groups-page">
      <div className="page-header">
        <div>
          <h1>{t('groups.title')}</h1>
          <p className="page-description">{t('groups.description')}</p>
        </div>
        {!showForm && canEdit && (
          <button className="btn-create" onClick={handleCreate}>
            + {t('groups.createGroup')}
          </button>
        )}
      </div>

      {error && (
        <div className="alert alert-error">
          <span className="alert-icon">⚠️</span>
          <span>{error}</span>
          <button className="alert-close" onClick={() => setError(null)}>×</button>
        </div>
      )}

      {successMessage && (
        <div className="alert alert-success">
          <span className="alert-icon">✓</span>
          <span>{successMessage}</span>
          <button className="alert-close" onClick={() => setSuccessMessage(null)}>×</button>
        </div>
      )}

      {showForm ? (
        <GroupForm
          initialData={editingGroupId ? { name: '', description: '', device_ids: [] } : undefined}
          devices={devices}
          onSubmit={handleSubmitForm}
          onCancel={handleCancelForm}
          isEdit={!!editingGroupId}
        />
      ) : loading ? (
        <div className="loading-spinner">Loading...</div>
      ) : (
        <GroupList
          groups={groups}
          onEdit={canEdit ? handleEdit : undefined}
          onDelete={canEdit ? handleDelete : undefined}
          canEdit={canEdit}
        />
      )}
    </div>
  );
};

export default Groups;
