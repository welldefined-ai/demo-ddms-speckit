"""
Export API endpoints for CSV data export (User Story 4)
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from uuid import UUID

from src.db.session import get_db
from src.services import export_service
from src.utils.logging import get_logger
from src.api.dependencies import get_current_user

router = APIRouter(prefix="/export", tags=["Export"])
logger = get_logger("ddms.api.export")


@router.get("/device/{device_id}")
def export_device_data(
    device_id: UUID,
    start_time: Optional[str] = Query(default=None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(default=None, description="End time (ISO format)"),
    aggregate: Optional[str] = Query(default=None, description="Aggregation interval (1min, 1hour, 1day)"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Export device readings to CSV format

    Generates a CSV file with device readings for download.

    Supports:
    - Time range filtering with start_time and end_time
    - Data aggregation with aggregate parameter
    - Automatic filename generation with device name and timestamp

    Args:
        device_id: UUID of the device
        start_time: Optional start timestamp in ISO format (inclusive)
        end_time: Optional end timestamp in ISO format (inclusive)
        aggregate: Optional aggregation interval ("1min", "1hour", "1day")

    Returns:
        CSV file as attachment with:
        - Content-Type: text/csv
        - Content-Disposition: attachment with sanitized filename

    Headers:
        - Raw data: timestamp, value, unit
        - Aggregated data: time_bucket, avg_value, min_value, max_value, count, unit

    Raises:
        400: Invalid time range or parameters
        401: Not authenticated
        404: Device not found
    """
    logger.info(f"Exporting data for device {device_id} (user: {current_user.username}, aggregate: {aggregate})")

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
        # Generate CSV export
        csv_content, filename = export_service.generate_csv_export(
            db=db,
            device_id=device_id,
            start_time=parsed_start_time,
            end_time=parsed_end_time,
            aggregate=aggregate
        )

        if csv_content is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device {device_id} not found"
            )

        logger.info(f"Generated CSV export: {filename} ({len(csv_content)} bytes)")

        # Return CSV as downloadable file
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "no-cache"
            }
        )

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/group/{group_id}")
def export_group_data(
    group_id: UUID,
    start_time: Optional[str] = Query(default=None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(default=None, description="End time (ISO format)"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Export readings from all devices in a group to CSV format (User Story 5)

    Combines data from all devices in the group into one CSV with device names.

    Args:
        group_id: UUID of the group
        start_time: Optional start timestamp in ISO format (inclusive)
        end_time: Optional end timestamp in ISO format (inclusive)

    Returns:
        CSV file with columns: timestamp, device_name, value, unit

    Raises:
        400: Invalid time range or parameters
        401: Not authenticated
        404: Group not found
    """
    logger.info(f"Exporting data for group {group_id} (user: {current_user.username})")

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
        # Generate CSV export
        csv_content, filename = export_service.generate_group_csv_export(
            db=db,
            group_id=group_id,
            start_time=parsed_start_time,
            end_time=parsed_end_time
        )

        if csv_content is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Group {group_id} not found"
            )

        logger.info(f"Generated CSV export: {filename} ({len(csv_content)} bytes)")

        # Return CSV as downloadable file
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "no-cache"
            }
        )

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/devices")
def export_multi_device_data(
    device_ids: str = Query(..., description="Comma-separated list of device UUIDs"),
    start_time: Optional[str] = Query(default=None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(default=None, description="End time (ISO format)"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Export readings from multiple devices to a single CSV file

    Combines data from multiple devices into one CSV with device names.

    Args:
        device_ids: Comma-separated list of device UUIDs (e.g., "id1,id2,id3")
        start_time: Optional start timestamp in ISO format (inclusive)
        end_time: Optional end timestamp in ISO format (inclusive)

    Returns:
        CSV file with columns: timestamp, device_name, value, unit

    Raises:
        400: Invalid parameters or no devices specified
        401: Not authenticated
        404: No devices found or no data available
    """
    logger.info(f"Exporting multi-device data (user: {current_user.username})")

    # Parse device IDs
    try:
        device_uuid_list = [UUID(device_id.strip()) for device_id in device_ids.split(',')]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid device ID format: {e}"
        )

    if not device_uuid_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one device ID must be specified"
        )

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
        # Generate multi-device CSV export
        csv_content, filename = export_service.generate_multi_device_csv_export(
            db=db,
            device_ids=device_uuid_list,
            start_time=parsed_start_time,
            end_time=parsed_end_time
        )

        if csv_content is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No devices found or no data available for the specified devices"
            )

        logger.info(f"Generated multi-device CSV export: {filename} ({len(csv_content)} bytes)")

        # Return CSV as downloadable file
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "no-cache"
            }
        )

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/group/{group_id}")
def export_group_data(
    group_id: UUID,
    start_time: Optional[str] = Query(default=None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(default=None, description="End time (ISO format)"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Export readings from all devices in a group to CSV format (User Story 5)

    Combines data from all devices in the group into one CSV with device names.

    Args:
        group_id: UUID of the group
        start_time: Optional start timestamp in ISO format (inclusive)
        end_time: Optional end timestamp in ISO format (inclusive)

    Returns:
        CSV file with columns: timestamp, device_name, value, unit

    Raises:
        400: Invalid time range or parameters
        401: Not authenticated
        404: Group not found
    """
    logger.info(f"Exporting data for group {group_id} (user: {current_user.username})")

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
        # Generate CSV export
        csv_content, filename = export_service.generate_group_csv_export(
            db=db,
            group_id=group_id,
            start_time=parsed_start_time,
            end_time=parsed_end_time
        )

        if csv_content is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Group {group_id} not found"
            )

        logger.info(f"Generated CSV export: {filename} ({len(csv_content)} bytes)")

        # Return CSV as downloadable file
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "no-cache"
            }
        )

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
