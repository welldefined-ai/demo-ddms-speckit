"""
Reading model for time-series device data (TimescaleDB hypertable)
"""
from sqlalchemy import Column, Float, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID

from src.db.base import Base


class Reading(Base):
    """
    Reading model for time-series device measurements

    This table will be converted to a TimescaleDB hypertable
    partitioned by timestamp for optimal time-series performance.

    Fields:
    - timestamp: Measurement timestamp (partition key)
    - device_id: Foreign key to devices table
    - value: Measured value
    """
    __tablename__ = "readings"

    timestamp = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), primary_key=True, nullable=False, index=True)
    value = Column(Float, nullable=False)

    # Composite index for efficient queries
    __table_args__ = (
        Index("idx_readings_device_timestamp", "device_id", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<Reading(device_id={self.device_id}, timestamp={self.timestamp}, value={self.value})>"
