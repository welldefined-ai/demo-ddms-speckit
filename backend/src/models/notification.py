"""
Notification model for in-app alerts and notifications
"""
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey, func, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from src.db.base import Base


class NotificationType(PyEnum):
    """Notification type enumeration"""
    DEVICE_DISCONNECT = "device_disconnect"
    DEVICE_ALERT = "device_alert"
    SYSTEM = "system"


class NotificationSeverity(PyEnum):
    """Notification severity level"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Notification(Base):
    """
    Notification model for in-app alerts

    Fields:
    - id: UUID primary key
    - type: NotificationType enum (device_disconnect/device_alert/system)
    - severity: NotificationSeverity enum (info/warning/error/critical)
    - title: Short notification title
    - message: Detailed notification message
    - user_id: Foreign key to user who should receive notification
    - device_id: Optional foreign key to related device
    - metadata: JSON field for additional context
    - read_at: Timestamp when notification was read (null if unread)
    - dismissed_at: Timestamp when notification was dismissed (null if not dismissed)
    - created_at: Timestamp of notification creation
    - updated_at: Timestamp of last update
    """
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(Enum(NotificationType), nullable=False)
    severity = Column(Enum(NotificationSeverity), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)

    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey('devices.id', ondelete='CASCADE'), nullable=True, index=True)

    # Additional data (use extra_data to avoid SQLAlchemy reserved name 'metadata')
    extra_data = Column('metadata', JSON, nullable=True, default=dict)

    # Status tracking
    read_at = Column(DateTime(timezone=True), nullable=True)
    dismissed_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", backref="notifications")
    device = relationship("Device", backref="notifications")

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, type={self.type.value}, user_id={self.user_id}, read={self.read_at is not None})>"
