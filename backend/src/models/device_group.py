"""
DeviceGroup association model for many-to-many relationship
"""
from sqlalchemy import Column, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from src.db.base import Base


class DeviceGroup(Base):
    """
    DeviceGroup association model

    Implements many-to-many relationship between devices and groups

    Fields:
    - device_id: Foreign key to devices table
    - group_id: Foreign key to groups table
    - added_at: Timestamp when device was added to group
    """
    __tablename__ = "device_groups"

    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("device_id", "group_id", name="uq_device_group"),
    )

    def __repr__(self) -> str:
        return f"<DeviceGroup(device_id={self.device_id}, group_id={self.group_id})>"
