import React from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import './GroupList.css';

interface GroupListItem {
  id: string;
  name: string;
  description: string | null;
  device_count: number;
  created_at: string;
  updated_at: string;
}

interface GroupListProps {
  groups: GroupListItem[];
  onEdit?: (groupId: string) => void;
  onDelete?: (groupId: string) => void;
  canEdit?: boolean;
}

const GroupList: React.FC<GroupListProps> = ({
  groups,
  onEdit,
  onDelete,
  canEdit = false
}) => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const handleViewGroup = (groupId: string) => {
    navigate(`/groups/${groupId}`);
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (groups.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">📦</div>
        <h3>{t('groups.noGroups')}</h3>
        <p>{t('groups.addGroupHint')}</p>
      </div>
    );
  }

  return (
    <div className="group-list">
      {groups.map(group => (
        <div key={group.id} className="group-card">
          <div className="group-card-header">
            <h3 className="group-name">{group.name}</h3>
          </div>

          {group.description && (
            <p className="group-description">{group.description}</p>
          )}

          <div className="group-metadata">
            <div className="metadata-item">
              <span className="metadata-label">{t('groups.deviceCount', { count: 0 })}:</span>
              <span className="metadata-value">
                {group.device_count}
              </span>
            </div>
            <div className="metadata-item">
              <span className="metadata-label">Created:</span>
              <span className="metadata-value">{formatDate(group.created_at)}</span>
            </div>
          </div>

          <div className="group-actions">
            <button
              className="btn-view"
              onClick={() => handleViewGroup(group.id)}
              title={t('groups.viewGroup')}
            >
              {t('common.view', { defaultValue: 'View' })}
            </button>
            {canEdit && onEdit && (
              <button
                className="btn-edit"
                onClick={() => onEdit(group.id)}
                title={t('groups.editGroup')}
              >
                {t('common.edit', { defaultValue: 'Edit' })}
              </button>
            )}
            {canEdit && onDelete && (
              <button
                className="btn-delete"
                onClick={() => onDelete(group.id)}
                title={t('groups.deleteGroup')}
              >
                {t('common.delete', { defaultValue: 'Delete' })}
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default GroupList;
