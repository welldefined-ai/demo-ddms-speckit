"""
Configuration singleton model for system-wide settings
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.db.base import Base


class Configuration(Base):
    """
    Configuration singleton model for system settings

    This table should contain only ONE row (enforced by application logic)

    Fields:
    - id: UUID primary key (singleton - only one row)
    - system_name: Display name for the system
    - data_retention_days_default: Default retention period for new devices
    - backup_enabled: Whether automatic backups are enabled
    - backup_schedule: Cron expression for backup schedule
    - created_at: Configuration creation timestamp
    - updated_at: Last update timestamp
    """
    __tablename__ = "configuration"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    system_name = Column(String(100), default="DDMS - Device Data Monitoring System", nullable=False)
    data_retention_days_default = Column(Integer, default=90, nullable=False)
    backup_enabled = Column(Boolean, default=True, nullable=False)
    backup_schedule = Column(String(100), default="0 2 * * *", nullable=False)  # Daily at 2 AM
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("data_retention_days_default > 0", name="chk_positive_retention"),
    )

    def __repr__(self) -> str:
        return f"<Configuration(system_name={self.system_name})>"
