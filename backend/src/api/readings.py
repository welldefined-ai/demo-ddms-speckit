"""
Readings API endpoints for historical data (User Story 4)
"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel, Field

from src.db.session import get_db
from src.services import reading_service
from src.utils.logging import get_logger
from src.api.dependencies import get_current_user

router = APIRouter(prefix="/readings", tags=["Readings"])
logger = get_logger("ddms.api.readings")


# Request/Response schemas
class ReadingResponse(BaseModel):
    """Response schema for a single reading"""
    timestamp: str
    value: float


class AggregatedReadingResponse(BaseModel):
    """Response schema for aggregated reading data"""
    time_bucket: str
    avg_value: float
    min_value: float
    max_value: float
    count: int


class ReadingsListResponse(BaseModel):
    """Response schema for list of readings"""
    device_id: str
    readings: List[ReadingResponse]
    total: int


# API endpoints

@router.get("/{device_id}", response_model=ReadingsListResponse)
def get_device_readings(
    device_id: UUID,
    start_time: Optional[str] = Query(default=None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(default=None, description="End time (ISO format)"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of readings"),
    offset: int = Query(default=0, ge=0, description="Number of readings to skip"),
    aggregate: Optional[str] = Query(default=None, description="Aggregation interval (1min, 1hour, 1day)"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Get historical readings for a device

    Supports:
    - Time range filtering with start_time and end_time
    - Pagination with limit and offset
    - Data aggregation with aggregate parameter

    Args:
        device_id: UUID of the device
        start_time: Optional start timestamp in ISO format (inclusive)
        end_time: Optional end timestamp in ISO format (inclusive)
        limit: Maximum number of readings to return (1-1000, default: 100)
        offset: Number of readings to skip for pagination (default: 0)
        aggregate: Optional aggregation interval ("1min", "1hour", "1day")

    Returns:
        ReadingsListResponse with device_id, readings list, and total count

    Raises:
        400: Invalid time range or parameters
        401: Not authenticated
        404: Device not found
    """
    logger.info(f"Fetching readings for device {device_id} (user: {current_user['username']})")

    # Parse timestamps
    parsed_start_time = None
    parsed_end_time = None

    try:
        if start_time:
            parsed_start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        if end_time:
            parsed_end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid timestamp format: {e}"
        )

    try:
        if aggregate:
            # Return aggregated data
            aggregated_readings = reading_service.get_aggregated_readings(
                db=db,
                device_id=device_id,
                start_time=parsed_start_time,
                end_time=parsed_end_time,
                aggregate_interval=aggregate,
                limit=limit,
                offset=offset
            )

            if aggregated_readings is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Device {device_id} not found"
                )

            # Convert to response format
            # Note: For aggregated data, we return it in a different format
            # but still use ReadingsListResponse structure
            # This is a simplification - in production, you might want separate response types
            logger.info(f"Returning {len(aggregated_readings)} aggregated readings")

            return ReadingsListResponse(
                device_id=str(device_id),
                readings=[
                    ReadingResponse(
                        timestamp=r.time_bucket,
                        value=r.avg_value
                    )
                    for r in aggregated_readings
                ],
                total=len(aggregated_readings)
            )

        else:
            # Return raw readings
            result = reading_service.get_readings(
                db=db,
                device_id=device_id,
                start_time=parsed_start_time,
                end_time=parsed_end_time,
                limit=limit,
                offset=offset
            )

            if result is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Device {device_id} not found"
                )

            logger.info(f"Returning {len(result.readings)} readings out of {result.total} total")

            return ReadingsListResponse(
                device_id=str(device_id),
                readings=[
                    ReadingResponse(
                        timestamp=r.timestamp.isoformat(),
                        value=r.value
                    )
                    for r in result.readings
                ],
                total=result.total
            )

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{device_id}/latest")
def get_latest_reading(
    device_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Get the most recent reading for a device

    Args:
        device_id: UUID of the device

    Returns:
        Single reading with timestamp and value

    Raises:
        401: Not authenticated
        404: Device not found or has no readings
    """
    logger.info(f"Fetching latest reading for device {device_id}")

    result = reading_service.get_latest_reading(db, device_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found or has no readings"
        )

    return {
        "device_id": str(device_id),
        "timestamp": result.timestamp.isoformat(),
        "value": result.value
    }


@router.get("/{device_id}/count")
def get_reading_count(
    device_id: UUID,
    start_time: Optional[str] = Query(default=None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(default=None, description="End time (ISO format)"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Get count of readings for a device in a time range

    Args:
        device_id: UUID of the device
        start_time: Optional start timestamp in ISO format
        end_time: Optional end timestamp in ISO format

    Returns:
        Object with device_id and count

    Raises:
        401: Not authenticated
        400: Invalid time range
    """
    logger.info(f"Counting readings for device {device_id}")

    # Parse timestamps
    parsed_start_time = None
    parsed_end_time = None

    try:
        if start_time:
            parsed_start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        if end_time:
            parsed_end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid timestamp format: {e}"
        )

    count = reading_service.get_reading_count(
        db=db,
        device_id=device_id,
        start_time=parsed_start_time,
        end_time=parsed_end_time
    )

    return {
        "device_id": str(device_id),
        "count": count
    }
