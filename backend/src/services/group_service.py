"""
Group service for business logic related to device groups (User Story 5)
"""
from typing import Optional, List, Dict
from dataclasses import dataclass
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from sqlalchemy.exc import IntegrityError
import uuid

from src.models.group import Group
from src.models.device_group import DeviceGroup
from src.models.device import Device
from src.models.reading import Reading


@dataclass
class GroupAlertSummary:
    """Alert summary for a group of devices"""
    normal: int
    warning: int
    critical: int


@dataclass
class GroupReadingResult:
    """Result object for a single reading from a device in a group"""
    device_id: uuid.UUID
    device_name: str
    timestamp: datetime
    value: float
    unit: str


def create_group(
    db: Session,
    name: str,
    description: Optional[str] = None,
    device_ids: Optional[List[uuid.UUID]] = None
) -> Group:
    """
    Create a new device group

    Args:
        db: Database session
        name: Group name (must be unique)
        description: Optional group description
        device_ids: Optional list of device IDs to add to the group

    Returns:
        Created Group object

    Raises:
        ValueError: If validation fails (name duplicate, device not found, etc.)
        IntegrityError: If database constraints are violated
    """
    # Check for duplicate name
    existing = db.query(Group).filter(Group.name == name).first()
    if existing:
        raise ValueError(f"Group with name '{name}' already exists")

    # Create group
    group = Group(
        name=name,
        description=description
    )

    db.add(group)
    db.flush()  # Flush to get group ID before adding devices

    # Add devices to group if specified
    if device_ids:
        for device_id in device_ids:
            # Verify device exists
            device = db.query(Device).filter(Device.id == device_id).first()
            if not device:
                db.rollback()
                raise ValueError(f"Device with ID '{device_id}' not found")

            # Check if device is already in group
            existing_membership = db.query(DeviceGroup).filter(
                and_(
                    DeviceGroup.device_id == device_id,
                    DeviceGroup.group_id == group.id
                )
            ).first()

            if not existing_membership:
                device_group = DeviceGroup(
                    device_id=device_id,
                    group_id=group.id
                )
                db.add(device_group)

    db.commit()
    db.refresh(group)

    return group


def update_group(
    db: Session,
    group_id: uuid.UUID,
    name: Optional[str] = None,
    description: Optional[str] = None,
    device_ids: Optional[List[uuid.UUID]] = None
) -> Optional[Group]:
    """
    Update an existing group

    Args:
        db: Database session
        group_id: UUID of the group to update
        name: New name for the group (optional)
        description: New description (optional)
        device_ids: New list of device IDs (replaces existing devices, optional)

    Returns:
        Updated Group object, or None if group not found

    Raises:
        ValueError: If validation fails
    """
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        return None

    # Check for duplicate name if updating name
    if name is not None and name != group.name:
        existing = db.query(Group).filter(Group.name == name).first()
        if existing:
            raise ValueError(f"Group with name '{name}' already exists")
        group.name = name

    # Update description if provided
    if description is not None:
        group.description = description

    # Update device membership if provided
    if device_ids is not None:
        # Remove all existing devices
        db.query(DeviceGroup).filter(DeviceGroup.group_id == group_id).delete()

        # Add new devices
        for device_id in device_ids:
            # Verify device exists
            device = db.query(Device).filter(Device.id == device_id).first()
            if not device:
                db.rollback()
                raise ValueError(f"Device with ID '{device_id}' not found")

            device_group = DeviceGroup(
                device_id=device_id,
                group_id=group_id
            )
            db.add(device_group)

    db.commit()
    db.refresh(group)

    return group


def delete_group(
    db: Session,
    group_id: uuid.UUID
) -> bool:
    """
    Delete a group (preserves devices)

    Args:
        db: Database session
        group_id: UUID of the group to delete

    Returns:
        True if group was deleted, False if group not found
    """
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        return False

    # Delete device associations (cascade delete should handle this, but explicit is better)
    db.query(DeviceGroup).filter(DeviceGroup.group_id == group_id).delete()

    # Delete the group
    db.delete(group)
    db.commit()

    return True


def list_groups(db: Session) -> List[Group]:
    """
    List all groups

    Args:
        db: Database session

    Returns:
        List of Group objects
    """
    return db.query(Group).order_by(Group.name).all()


def get_group_by_id(db: Session, group_id: uuid.UUID) -> Optional[Group]:
    """
    Get a group by its ID

    Args:
        db: Database session
        group_id: UUID of the group

    Returns:
        Group object or None if not found
    """
    return db.query(Group).filter(Group.id == group_id).first()


def get_group_devices(db: Session, group_id: uuid.UUID) -> List[Device]:
    """
    Get all devices in a group

    Args:
        db: Database session
        group_id: UUID of the group

    Returns:
        List of Device objects
    """
    device_groups = db.query(DeviceGroup).filter(
        DeviceGroup.group_id == group_id
    ).all()

    device_ids = [dg.device_id for dg in device_groups]

    devices = db.query(Device).filter(Device.id.in_(device_ids)).all()

    return devices


def get_group_alert_summary(db: Session, group_id: uuid.UUID) -> GroupAlertSummary:
    """
    Calculate alert summary for all devices in a group

    Args:
        db: Database session
        group_id: UUID of the group

    Returns:
        GroupAlertSummary with counts of normal/warning/critical devices
    """
    from src.services.device_service import get_device_status

    devices = get_group_devices(db, group_id)

    normal_count = 0
    warning_count = 0
    critical_count = 0

    for device in devices:
        status_result = get_device_status(db, device.id)

        if status_result:
            if status_result.status == "critical":
                critical_count += 1
            elif status_result.status == "warning":
                warning_count += 1
            else:
                normal_count += 1
        # If no readings, consider device as normal
        else:
            normal_count += 1

    return GroupAlertSummary(
        normal=normal_count,
        warning=warning_count,
        critical=critical_count
    )


def get_group_readings(
    db: Session,
    group_id: uuid.UUID,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: Optional[int] = None
) -> List[GroupReadingResult]:
    """
    Get readings from all devices in a group

    Args:
        db: Database session
        group_id: UUID of the group
        start_time: Optional start time for filtering
        end_time: Optional end time for filtering
        limit: Optional limit on number of readings per device

    Returns:
        List of GroupReadingResult objects, sorted by timestamp (descending)
    """
    devices = get_group_devices(db, group_id)

    if not devices:
        return []

    device_ids = [device.id for device in devices]

    # Build query
    query = db.query(Reading, Device).join(
        Device, Reading.device_id == Device.id
    ).filter(
        Reading.device_id.in_(device_ids)
    )

    # Apply time filters
    if start_time:
        query = query.filter(Reading.timestamp >= start_time)
    if end_time:
        query = query.filter(Reading.timestamp <= end_time)

    # Order by timestamp descending
    query = query.order_by(desc(Reading.timestamp))

    # Apply limit if specified
    if limit:
        query = query.limit(limit)

    results = query.all()

    # Convert to GroupReadingResult objects
    group_readings = [
        GroupReadingResult(
            device_id=reading.device_id,
            device_name=device.name,
            timestamp=reading.timestamp,
            value=reading.value,
            unit=device.unit
        )
        for reading, device in results
    ]

    return group_readings


def add_device_to_group(
    db: Session,
    group_id: uuid.UUID,
    device_id: uuid.UUID
) -> bool:
    """
    Add a device to a group

    Args:
        db: Database session
        group_id: UUID of the group
        device_id: UUID of the device

    Returns:
        True if device was added, False if already in group

    Raises:
        ValueError: If group or device not found
    """
    # Verify group exists
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise ValueError(f"Group with ID '{group_id}' not found")

    # Verify device exists
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise ValueError(f"Device with ID '{device_id}' not found")

    # Check if device is already in group
    existing = db.query(DeviceGroup).filter(
        and_(
            DeviceGroup.device_id == device_id,
            DeviceGroup.group_id == group_id
        )
    ).first()

    if existing:
        return False  # Already in group

    # Add device to group
    device_group = DeviceGroup(
        device_id=device_id,
        group_id=group_id
    )
    db.add(device_group)
    db.commit()

    return True


def remove_device_from_group(
    db: Session,
    group_id: uuid.UUID,
    device_id: uuid.UUID
) -> bool:
    """
    Remove a device from a group

    Args:
        db: Database session
        group_id: UUID of the group
        device_id: UUID of the device

    Returns:
        True if device was removed, False if not in group
    """
    result = db.query(DeviceGroup).filter(
        and_(
            DeviceGroup.device_id == device_id,
            DeviceGroup.group_id == group_id
        )
    ).delete()

    db.commit()

    return result > 0
