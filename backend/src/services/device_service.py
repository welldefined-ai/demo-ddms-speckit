"""
Device service for business logic related to devices and readings
"""
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from sqlalchemy.exc import IntegrityError
import uuid

from src.models.device import Device, DeviceStatus
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


# Device CRUD operations (User Story 2)

def create_device(
    db: Session,
    name: str,
    modbus_ip: str,
    modbus_port: int,
    modbus_slave_id: int,
    modbus_register: int,
    modbus_register_count: int,
    unit: str,
    sampling_interval: int = 10,
    threshold_warning_lower: Optional[float] = None,
    threshold_warning_upper: Optional[float] = None,
    threshold_critical_lower: Optional[float] = None,
    threshold_critical_upper: Optional[float] = None,
    retention_days: int = 90
) -> Device:
    """
    Create a new device with validation

    Args:
        db: Database session
        name: Device name (must be unique)
        modbus_ip: Modbus device IP address
        modbus_port: Modbus device port
        modbus_slave_id: Modbus slave ID
        modbus_register: Starting register address
        modbus_register_count: Number of registers to read
        unit: Measurement unit
        sampling_interval: Data collection interval in seconds (default: 10)
        threshold_warning_lower: Lower warning threshold
        threshold_warning_upper: Upper warning threshold
        threshold_critical_lower: Lower critical threshold
        threshold_critical_upper: Upper critical threshold
        retention_days: Number of days to retain data (default: 90)

    Returns:
        Created Device object

    Raises:
        ValueError: If validation fails (name duplicate, threshold ordering, etc.)
        IntegrityError: If database constraints are violated
    """
    # Check for duplicate name
    existing = db.query(Device).filter(Device.name == name).first()
    if existing:
        raise ValueError(f"Device with name '{name}' already exists")

    # Validate threshold ordering
    if threshold_warning_lower is not None and threshold_warning_upper is not None:
        if threshold_warning_lower >= threshold_warning_upper:
            raise ValueError("Warning lower threshold must be less than warning upper threshold")

    if threshold_critical_lower is not None and threshold_critical_upper is not None:
        if threshold_critical_lower >= threshold_critical_upper:
            raise ValueError("Critical lower threshold must be less than critical upper threshold")

    # Validate critical thresholds are outside warning thresholds
    if threshold_critical_lower is not None and threshold_warning_lower is not None:
        if threshold_critical_lower >= threshold_warning_lower:
            raise ValueError("Critical lower threshold must be less than warning lower threshold")

    if threshold_critical_upper is not None and threshold_warning_upper is not None:
        if threshold_critical_upper <= threshold_warning_upper:
            raise ValueError("Critical upper threshold must be greater than warning upper threshold")

    # Create device
    device = Device(
        name=name,
        modbus_ip=modbus_ip,
        modbus_port=modbus_port,
        modbus_slave_id=modbus_slave_id,
        modbus_register=modbus_register,
        modbus_register_count=modbus_register_count,
        unit=unit,
        sampling_interval=sampling_interval,
        threshold_warning_lower=threshold_warning_lower,
        threshold_warning_upper=threshold_warning_upper,
        threshold_critical_lower=threshold_critical_lower,
        threshold_critical_upper=threshold_critical_upper,
        retention_days=retention_days,
        status=DeviceStatus.OFFLINE
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    return device


def update_device(
    db: Session,
    device_id: uuid.UUID,
    name: Optional[str] = None,
    modbus_ip: Optional[str] = None,
    modbus_port: Optional[int] = None,
    modbus_slave_id: Optional[int] = None,
    modbus_register: Optional[int] = None,
    modbus_register_count: Optional[int] = None,
    unit: Optional[str] = None,
    sampling_interval: Optional[int] = None,
    threshold_warning_lower: Optional[float] = None,
    threshold_warning_upper: Optional[float] = None,
    threshold_critical_lower: Optional[float] = None,
    threshold_critical_upper: Optional[float] = None,
    retention_days: Optional[int] = None
) -> Optional[Device]:
    """
    Update an existing device

    Args:
        db: Database session
        device_id: UUID of the device to update
        **kwargs: Fields to update (only provided fields will be updated)

    Returns:
        Updated Device object, or None if device not found

    Raises:
        ValueError: If validation fails
    """
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        return None

    # Check for duplicate name if updating name
    if name is not None and name != device.name:
        existing = db.query(Device).filter(Device.name == name).first()
        if existing:
            raise ValueError(f"Device with name '{name}' already exists")
        device.name = name

    # Update fields if provided
    if modbus_ip is not None:
        device.modbus_ip = modbus_ip
    if modbus_port is not None:
        device.modbus_port = modbus_port
    if modbus_slave_id is not None:
        device.modbus_slave_id = modbus_slave_id
    if modbus_register is not None:
        device.modbus_register = modbus_register
    if modbus_register_count is not None:
        device.modbus_register_count = modbus_register_count
    if unit is not None:
        device.unit = unit
    if sampling_interval is not None:
        device.sampling_interval = sampling_interval
    if retention_days is not None:
        device.retention_days = retention_days

    # Update thresholds
    if threshold_warning_lower is not None:
        device.threshold_warning_lower = threshold_warning_lower
    if threshold_warning_upper is not None:
        device.threshold_warning_upper = threshold_warning_upper
    if threshold_critical_lower is not None:
        device.threshold_critical_lower = threshold_critical_lower
    if threshold_critical_upper is not None:
        device.threshold_critical_upper = threshold_critical_upper

    # Validate threshold ordering after updates
    if device.threshold_warning_lower is not None and device.threshold_warning_upper is not None:
        if device.threshold_warning_lower >= device.threshold_warning_upper:
            raise ValueError("Warning lower threshold must be less than warning upper threshold")

    if device.threshold_critical_lower is not None and device.threshold_critical_upper is not None:
        if device.threshold_critical_lower >= device.threshold_critical_upper:
            raise ValueError("Critical lower threshold must be less than critical upper threshold")

    db.commit()
    db.refresh(device)

    return device


def delete_device(
    db: Session,
    device_id: uuid.UUID,
    keep_data: bool = False
) -> bool:
    """
    Delete a device, optionally keeping historical readings

    Args:
        db: Database session
        device_id: UUID of the device to delete
        keep_data: If True, keep historical readings; if False, delete them (default: False)

    Returns:
        True if device was deleted, False if device not found
    """
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        return False

    if not keep_data:
        # Delete all readings for this device
        db.query(Reading).filter(Reading.device_id == device_id).delete()

    # Delete the device
    db.delete(device)
    db.commit()

    return True


def list_devices(
    db: Session,
    status_filter: Optional[DeviceStatus] = None
) -> List[Device]:
    """
    List all devices, optionally filtered by status

    Args:
        db: Database session
        status_filter: Optional DeviceStatus to filter by

    Returns:
        List of Device objects
    """
    query = db.query(Device)

    if status_filter:
        query = query.filter(Device.status == status_filter)

    return query.order_by(Device.name).all()


def get_device_by_id(db: Session, device_id: uuid.UUID) -> Optional[Device]:
    """
    Get a device by its ID

    Args:
        db: Database session
        device_id: UUID of the device

    Returns:
        Device object or None if not found
    """
    return db.query(Device).filter(Device.id == device_id).first()


async def test_modbus_connection(
    modbus_ip: str,
    modbus_port: int,
    modbus_slave_id: int,
    modbus_register: int,
    modbus_register_count: int,
    timeout: int = 5
) -> tuple[bool, Optional[str]]:
    """
    Test Modbus device connection and read capability

    Args:
        modbus_ip: Modbus device IP address
        modbus_port: Modbus device port
        modbus_slave_id: Modbus slave ID
        modbus_register: Starting register address
        modbus_register_count: Number of registers to read
        timeout: Connection timeout in seconds (default: 5)

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    from pymodbus.client import AsyncModbusTcpClient

    client = AsyncModbusTcpClient(
        host=modbus_ip,
        port=modbus_port,
        timeout=timeout
    )

    try:
        # Attempt to connect
        await client.connect()

        if not client.connected:
            return False, "Failed to establish connection"

        # Attempt to read registers
        result = await client.read_holding_registers(
            address=modbus_register,
            count=modbus_register_count,
            slave=modbus_slave_id
        )

        if result.isError():
            return False, f"Failed to read registers: {result}"

        # Success
        return True, None

    except Exception as e:
        return False, str(e)

    finally:
        client.close()
