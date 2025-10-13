"""
Reading service for querying historical time-series data (User Story 4)
"""
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_
import uuid

from src.models.reading import Reading
from src.models.device import Device


@dataclass
class ReadingResult:
    """Result object for a single reading"""
    timestamp: datetime
    value: float


@dataclass
class AggregatedReadingResult:
    """Result object for aggregated reading data"""
    time_bucket: str
    avg_value: float
    min_value: float
    max_value: float
    count: int


@dataclass
class ReadingsQueryResult:
    """Result object for readings query with pagination"""
    readings: List[ReadingResult]
    total: int
    device_id: uuid.UUID


def get_readings(
    db: Session,
    device_id: uuid.UUID,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0
) -> Optional[ReadingsQueryResult]:
    """
    Query readings for a device with time range and pagination

    Args:
        db: Database session
        device_id: UUID of the device
        start_time: Optional start timestamp (inclusive)
        end_time: Optional end timestamp (inclusive)
        limit: Maximum number of readings to return (max 1000)
        offset: Number of readings to skip for pagination

    Returns:
        ReadingsQueryResult if device exists, None otherwise

    Raises:
        ValueError: If end_time is before start_time or limit is invalid
    """
    # Validate device exists
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        return None

    # Validate time range
    if start_time and end_time and end_time < start_time:
        raise ValueError("end_time must be after start_time")

    # Validate and cap limit
    if limit <= 0:
        raise ValueError("limit must be positive")

    limit = min(limit, 1000)  # Cap at 1000

    # Build base query
    query = db.query(Reading).filter(Reading.device_id == device_id)

    # Apply time range filters
    if start_time:
        query = query.filter(Reading.timestamp >= start_time)
    if end_time:
        query = query.filter(Reading.timestamp <= end_time)

    # Get total count
    total = query.count()

    # Apply ordering and pagination
    readings_data = (
        query
        .order_by(desc(Reading.timestamp))
        .limit(limit)
        .offset(offset)
        .all()
    )

    # Convert to result objects
    readings = [
        ReadingResult(
            timestamp=reading.timestamp,
            value=reading.value
        )
        for reading in readings_data
    ]

    return ReadingsQueryResult(
        readings=readings,
        total=total,
        device_id=device_id
    )


def get_aggregated_readings(
    db: Session,
    device_id: uuid.UUID,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    aggregate_interval: str = "1hour",
    limit: int = 1000,
    offset: int = 0
) -> Optional[List[AggregatedReadingResult]]:
    """
    Query aggregated readings for a device with time buckets

    Supports downsampling data into time buckets with AVG, MIN, MAX statistics.

    Args:
        db: Database session
        device_id: UUID of the device
        start_time: Optional start timestamp (inclusive)
        end_time: Optional end timestamp (inclusive)
        aggregate_interval: Aggregation interval ("1min", "1hour", "1day")
        limit: Maximum number of buckets to return
        offset: Number of buckets to skip for pagination

    Returns:
        List of AggregatedReadingResult if device exists, None otherwise

    Raises:
        ValueError: If parameters are invalid
    """
    # Validate device exists
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        return None

    # Validate time range
    if start_time and end_time and end_time < start_time:
        raise ValueError("end_time must be after start_time")

    # Map aggregate interval to SQL time format
    time_format_map = {
        "1min": "%Y-%m-%d %H:%M:00",
        "1hour": "%Y-%m-%d %H:00:00",
        "1day": "%Y-%m-%d",
    }

    if aggregate_interval not in time_format_map:
        raise ValueError(f"Invalid aggregate_interval. Must be one of: {', '.join(time_format_map.keys())}")

    time_format = time_format_map[aggregate_interval]

    # Build aggregation query
    query = db.query(
        func.strftime(time_format, Reading.timestamp).label('time_bucket'),
        func.avg(Reading.value).label('avg_value'),
        func.min(Reading.value).label('min_value'),
        func.max(Reading.value).label('max_value'),
        func.count(Reading.id).label('count')
    ).filter(Reading.device_id == device_id)

    # Apply time range filters
    if start_time:
        query = query.filter(Reading.timestamp >= start_time)
    if end_time:
        query = query.filter(Reading.timestamp <= end_time)

    # Group by time bucket and order descending
    results = (
        query
        .group_by(func.strftime(time_format, Reading.timestamp))
        .order_by(desc(func.strftime(time_format, Reading.timestamp)))
        .limit(limit)
        .offset(offset)
        .all()
    )

    # Convert to result objects
    aggregated_readings = [
        AggregatedReadingResult(
            time_bucket=result.time_bucket,
            avg_value=result.avg_value,
            min_value=result.min_value,
            max_value=result.max_value,
            count=result.count
        )
        for result in results
    ]

    return aggregated_readings


def get_latest_reading(
    db: Session,
    device_id: uuid.UUID
) -> Optional[ReadingResult]:
    """
    Get the most recent reading for a device

    Args:
        db: Database session
        device_id: UUID of the device

    Returns:
        ReadingResult if reading exists, None otherwise
    """
    reading = (
        db.query(Reading)
        .filter(Reading.device_id == device_id)
        .order_by(desc(Reading.timestamp))
        .first()
    )

    if not reading:
        return None

    return ReadingResult(
        timestamp=reading.timestamp,
        value=reading.value
    )


def get_reading_count(
    db: Session,
    device_id: uuid.UUID,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> int:
    """
    Get count of readings for a device in a time range

    Args:
        db: Database session
        device_id: UUID of the device
        start_time: Optional start timestamp (inclusive)
        end_time: Optional end timestamp (inclusive)

    Returns:
        Count of readings
    """
    query = db.query(func.count(Reading.id)).filter(Reading.device_id == device_id)

    if start_time:
        query = query.filter(Reading.timestamp >= start_time)
    if end_time:
        query = query.filter(Reading.timestamp <= end_time)

    return query.scalar()


def delete_old_readings(
    db: Session,
    device_id: uuid.UUID,
    cutoff_date: datetime
) -> int:
    """
    Delete readings older than cutoff date for a device

    Used for data retention policies.

    Args:
        db: Database session
        device_id: UUID of the device
        cutoff_date: Delete readings before this date

    Returns:
        Number of readings deleted
    """
    deleted_count = (
        db.query(Reading)
        .filter(
            and_(
                Reading.device_id == device_id,
                Reading.timestamp < cutoff_date
            )
        )
        .delete()
    )

    db.commit()

    return deleted_count
