"""
Device model for Modbus device configuration
"""
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Enum, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.db.base import Base


class DeviceStatus(PyEnum):
    """Device connection status"""
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"


class Device(Base):
    """
    Device model for Modbus device configuration

    Fields per data-model.md:
    - id: UUID primary key
    - name: Unique device name
    - modbus_ip: IP address for Modbus TCP connection
    - modbus_port: Port number (default 502)
    - modbus_slave_id: Slave ID (1-247)
    - modbus_register: Register address to read
    - modbus_register_count: Number of registers to read (default 1)
    - unit: Measurement unit string
    - sampling_interval: Collection interval in seconds
    - threshold_warning_lower: Lower warning threshold
    - threshold_warning_upper: Upper warning threshold
    - threshold_critical_lower: Lower critical threshold
    - threshold_critical_upper: Upper critical threshold
    - retention_days: Data retention period in days
    - status: Current connection status
    - last_reading_at: Timestamp of last successful reading
    - created_at: Device creation timestamp
    - updated_at: Last update timestamp
    """
    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)

    # Modbus connection parameters
    modbus_ip = Column(String(45), nullable=False)  # IPv4 or IPv6
    modbus_port = Column(Integer, default=502, nullable=False)
    modbus_slave_id = Column(Integer, nullable=False)  # 1-247
    modbus_register = Column(Integer, nullable=False)
    modbus_register_count = Column(Integer, default=1, nullable=False)

    # Measurement configuration
    unit = Column(String(20), nullable=False)
    sampling_interval = Column(Integer, nullable=False)  # seconds

    # Thresholds
    threshold_warning_lower = Column(Float, nullable=True)
    threshold_warning_upper = Column(Float, nullable=True)
    threshold_critical_lower = Column(Float, nullable=True)
    threshold_critical_upper = Column(Float, nullable=True)

    # Data retention
    retention_days = Column(Integer, default=90, nullable=False)

    # Status tracking
    status = Column(Enum(DeviceStatus), default=DeviceStatus.OFFLINE, nullable=False)
    last_reading_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<Device(id={self.id}, name={self.name}, status={self.status.value})>"
