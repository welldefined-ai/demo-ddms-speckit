"""
CSV export service for historical data (User Story 4)
"""
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
import csv
import io
import re
import uuid

from src.models.device import Device
from src.services.reading_service import get_readings, get_aggregated_readings


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to remove dangerous characters

    Removes or replaces characters that could be problematic in filenames:
    - Slashes (/ \\)
    - Colons (:)
    - Asterisks (*)
    - Question marks (?)
    - Quotes (" ')
    - Less than/greater than (< >)
    - Pipe (|)

    Args:
        filename: Raw filename string

    Returns:
        Sanitized filename safe for filesystem use
    """
    # Replace problematic characters with underscores
    filename = re.sub(r'[/\\:*?"<>|]', '_', filename)

    # Remove any remaining control characters
    filename = re.sub(r'[\x00-\x1f\x7f]', '', filename)

    # Collapse multiple underscores
    filename = re.sub(r'_+', '_', filename)

    # Strip leading/trailing underscores and whitespace
    filename = filename.strip('_ ')

    # Ensure filename is not empty
    if not filename:
        filename = "export"

    return filename


def generate_csv_export(
    db: Session,
    device_id: uuid.UUID,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    aggregate: Optional[str] = None
) -> tuple[Optional[str], Optional[str]]:
    """
    Generate CSV export of device readings

    Args:
        db: Database session
        device_id: UUID of the device
        start_time: Optional start timestamp (inclusive)
        end_time: Optional end timestamp (inclusive)
        aggregate: Optional aggregation interval ("1min", "1hour", "1day")

    Returns:
        Tuple of (csv_content: str, filename: str) if successful, (None, None) if device not found

    Raises:
        ValueError: If parameters are invalid
    """
    # Validate device exists
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        return None, None

    # Validate time range
    if start_time and end_time and end_time < start_time:
        raise ValueError("end_time must be after start_time")

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Determine if we need aggregated or raw data
    if aggregate:
        # Export aggregated data
        aggregated_readings = get_aggregated_readings(
            db=db,
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
            aggregate_interval=aggregate,
            limit=10000  # Large limit for export
        )

        if aggregated_readings is None:
            return None, None

        # Write CSV headers for aggregated data
        writer.writerow(['time_bucket', 'avg_value', 'min_value', 'max_value', 'count', 'unit'])

        # Write aggregated data rows
        for reading in reversed(aggregated_readings):  # Reverse to get chronological order
            writer.writerow([
                reading.time_bucket,
                reading.avg_value,
                reading.min_value,
                reading.max_value,
                reading.count,
                device.unit
            ])
    else:
        # Export raw data
        readings_result = get_readings(
            db=db,
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
            limit=10000,  # Large limit for export
            offset=0
        )

        if readings_result is None:
            return None, None

        # Write CSV headers for raw data
        writer.writerow(['timestamp', 'value', 'unit'])

        # Write data rows (reverse to get chronological order - newest first becomes oldest first)
        for reading in reversed(readings_result.readings):
            writer.writerow([
                reading.timestamp.isoformat(),
                reading.value,
                device.unit
            ])

    # Get CSV content
    csv_content = output.getvalue()
    output.close()

    # Generate filename
    sanitized_name = sanitize_filename(device.name)
    timestamp_str = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = f"{sanitized_name}_{timestamp_str}.csv"

    return csv_content, filename


def generate_multi_device_csv_export(
    db: Session,
    device_ids: list[uuid.UUID],
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> tuple[Optional[str], Optional[str]]:
    """
    Generate CSV export for multiple devices

    Combines readings from multiple devices into a single CSV with device names.

    Args:
        db: Database session
        device_ids: List of device UUIDs
        start_time: Optional start timestamp (inclusive)
        end_time: Optional end timestamp (inclusive)

    Returns:
        Tuple of (csv_content: str, filename: str) if successful, (None, None) if no devices found

    Raises:
        ValueError: If parameters are invalid
    """
    if not device_ids:
        return None, None

    # Validate time range
    if start_time and end_time and end_time < start_time:
        raise ValueError("end_time must be after start_time")

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write CSV headers
    writer.writerow(['timestamp', 'device_name', 'value', 'unit'])

    # Fetch and write data for each device
    has_data = False
    for device_id in device_ids:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            continue

        readings_result = get_readings(
            db=db,
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
            limit=10000,
            offset=0
        )

        if readings_result and readings_result.readings:
            has_data = True
            for reading in reversed(readings_result.readings):
                writer.writerow([
                    reading.timestamp.isoformat(),
                    device.name,
                    reading.value,
                    device.unit
                ])

    if not has_data:
        return None, None

    # Get CSV content
    csv_content = output.getvalue()
    output.close()

    # Generate filename
    timestamp_str = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = f"multi_device_export_{timestamp_str}.csv"

    return csv_content, filename


def generate_group_csv_export(
    db: Session,
    group_id: uuid.UUID,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> tuple[Optional[str], Optional[str]]:
    """
    Generate CSV export for a device group

    Combines readings from all devices in a group into a single CSV.

    Args:
        db: Database session
        group_id: UUID of the group
        start_time: Optional start timestamp (inclusive)
        end_time: Optional end timestamp (inclusive)

    Returns:
        Tuple of (csv_content: str, filename: str) if successful, (None, None) if group not found

    Raises:
        ValueError: If parameters are invalid
    """
    from src.services.group_service import get_group_by_id, get_group_readings

    # Validate group exists
    group = get_group_by_id(db, group_id)
    if not group:
        return None, None

    # Validate time range
    if start_time and end_time and end_time < start_time:
        raise ValueError("end_time must be after start_time")

    # Get group readings
    readings = get_group_readings(
        db=db,
        group_id=group_id,
        start_time=start_time,
        end_time=end_time,
        limit=10000  # Large limit for export
    )

    if not readings:
        # Return empty CSV if no data
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['timestamp', 'device_name', 'value', 'unit'])
        csv_content = output.getvalue()
        output.close()

        sanitized_name = sanitize_filename(group.name)
        timestamp_str = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"{sanitized_name}_{timestamp_str}.csv"

        return csv_content, filename

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write CSV headers
    writer.writerow(['timestamp', 'device_name', 'value', 'unit'])

    # Write data rows (already in descending order, so reverse for chronological)
    for reading in reversed(readings):
        writer.writerow([
            reading.timestamp.isoformat(),
            reading.device_name,
            reading.value,
            reading.unit
        ])

    # Get CSV content
    csv_content = output.getvalue()
    output.close()

    # Generate filename
    sanitized_name = sanitize_filename(group.name)
    timestamp_str = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = f"{sanitized_name}_{timestamp_str}.csv"

    return csv_content, filename


def get_export_filename(device_name: str, extension: str = "csv") -> str:
    """
    Generate a safe export filename for a device

    Args:
        device_name: Name of the device
        extension: File extension (default: "csv")

    Returns:
        Sanitized filename with timestamp
    """
    sanitized_name = sanitize_filename(device_name)
    timestamp_str = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    return f"{sanitized_name}_{timestamp_str}.{extension}"
