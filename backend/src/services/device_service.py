"""
Device service for business logic related to devices and readings
"""
from typing import Optional
from dataclasses import dataclass
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
import uuid

from src.models.device import Device
from src.models.reading import Reading


@dataclass
class DeviceStatusResult:
    """Result object for device status calculation"""
    device_id: uuid.UUID
    device_name: str
    unit: str
    status: str  # "normal", "warning", "critical"
    latest_value: float
    latest_timestamp: datetime


def get_device_status(db: Session, device_id: uuid.UUID) -> Optional[DeviceStatusResult]:
    """
    Calculate device status based on latest reading and thresholds

    Status determination with hysteresis:
    - Critical: value < critical_lower OR value > critical_upper
    - Warning: value < warning_lower OR value > warning_upper (but not critical)
    - Normal: within warning thresholds

    Args:
        db: Database session
        device_id: UUID of the device

    Returns:
        DeviceStatusResult if device and reading exist, None otherwise
    """
    # Fetch device
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        return None

    # Fetch latest reading
    latest_reading = (
        db.query(Reading)
        .filter(Reading.device_id == device_id)
        .order_by(desc(Reading.timestamp))
        .first()
    )

    if not latest_reading:
        return None

    # Calculate status based on thresholds
    value = latest_reading.value
    status = "normal"

    # Check critical thresholds first
    if device.threshold_critical_lower is not None and value < device.threshold_critical_lower:
        status = "critical"
    elif device.threshold_critical_upper is not None and value > device.threshold_critical_upper:
        status = "critical"
    # Check warning thresholds
    elif device.threshold_warning_lower is not None and value < device.threshold_warning_lower:
        status = "warning"
    elif device.threshold_warning_upper is not None and value > device.threshold_warning_upper:
        status = "warning"

    return DeviceStatusResult(
        device_id=device.id,
        device_name=device.name,
        unit=device.unit,
        status=status,
        latest_value=value,
        latest_timestamp=latest_reading.timestamp
    )


def get_latest_reading_with_status(
    db: Session, device_id: uuid.UUID
) -> Optional[DeviceStatusResult]:
    """
    Get the latest reading for a device along with its calculated status

    This is a convenience function that wraps get_device_status for API use

    Args:
        db: Database session
        device_id: UUID of the device

    Returns:
        DeviceStatusResult if device and reading exist, None otherwise
    """
    return get_device_status(db, device_id)
