"""
Device Groups API endpoints (User Story 5)
"""
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel, Field

from src.db.session import get_db
from src.services import group_service
from src.models.group import Group
from src.utils.logging import get_logger
from src.utils.rbac import require_admin

router = APIRouter(prefix="/groups", tags=["Groups"])
logger = get_logger("ddms.api.groups")


# Request/Response schemas

class GroupCreateRequest(BaseModel):
    """Request schema for creating a group"""
    name: str = Field(..., min_length=1, max_length=100, description="Group name (must be unique)")
    description: Optional[str] = Field(default=None, max_length=500, description="Group description")
    device_ids: List[str] = Field(default=[], description="List of device IDs to add to group")


class GroupUpdateRequest(BaseModel):
    """Request schema for updating a group"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="Group name")
    description: Optional[str] = Field(default=None, max_length=500, description="Group description")
    device_ids: Optional[List[str]] = Field(default=None, description="List of device IDs (replaces existing)")


class DeviceInGroupResponse(BaseModel):
    """Response schema for a device within a group"""
    id: str
    name: str
    unit: str
    status: str


class AlertSummaryResponse(BaseModel):
    """Response schema for group alert summary"""
    normal: int
    warning: int
    critical: int


class GroupResponse(BaseModel):
    """Response schema for group data"""
    id: str
    name: str
    description: Optional[str]
    devices: List[DeviceInGroupResponse]
    alert_summary: AlertSummaryResponse
    created_at: str
    updated_at: str


class GroupListItemResponse(BaseModel):
    """Response schema for group list item (without full device details)"""
    id: str
    name: str
    description: Optional[str]
    device_count: int
    created_at: str
    updated_at: str


class GroupReadingResponse(BaseModel):
    """Response schema for a group reading"""
    device_id: str
    device_name: str
    timestamp: str
    value: float
    unit: str


class GroupReadingsResponse(BaseModel):
    """Response schema for group readings collection"""
    group_id: str
    readings: List[GroupReadingResponse]
    total: int


# Group CRUD endpoints (User Story 5)

@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
@require_admin
def create_group_endpoint(
    group_data: GroupCreateRequest,
    db: Session = Depends(get_db),
    current_user = None  # Injected by require_admin decorator
):
    """
    Create a new device group (admin/owner only)

    Args:
        group_data: Group configuration data

    Returns:
        Created group object with devices

    Raises:
        400: Validation error (duplicate name, device not found, etc.)
        403: Insufficient permissions (not admin/owner)
    """
    logger.info(f"Creating new group: {group_data.name}")

    try:
        # Convert device ID strings to UUIDs
        device_ids = [UUID(device_id) for device_id in group_data.device_ids] if group_data.device_ids else None

        group = group_service.create_group(
            db=db,
            name=group_data.name,
            description=group_data.description,
            device_ids=device_ids
        )

        logger.info(f"Group created successfully: {group.name} (ID: {group.id})")

        # Get devices and alert summary for response
        devices = group_service.get_group_devices(db, group.id)
        alert_summary = group_service.get_group_alert_summary(db, group.id)

        return GroupResponse(
            id=str(group.id),
            name=group.name,
            description=group.description,
            devices=[
                DeviceInGroupResponse(
                    id=str(device.id),
                    name=device.name,
                    unit=device.unit,
                    status=device.status.value
                )
                for device in devices
            ],
            alert_summary=AlertSummaryResponse(
                normal=alert_summary.normal,
                warning=alert_summary.warning,
                critical=alert_summary.critical
            ),
            created_at=group.created_at.isoformat(),
            updated_at=group.updated_at.isoformat()
        )

    except ValueError as e:
        logger.warning(f"Validation error creating group: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[GroupListItemResponse])
def list_groups_endpoint(
    db: Session = Depends(get_db)
):
    """
    List all device groups (accessible to all authenticated users)

    Returns:
        List of group objects with device counts
    """
    logger.info("Listing all groups")

    groups = group_service.list_groups(db)

    response = []
    for group in groups:
        # Get device count
        devices = group_service.get_group_devices(db, group.id)

        response.append(
            GroupListItemResponse(
                id=str(group.id),
                name=group.name,
                description=group.description,
                device_count=len(devices),
                created_at=group.created_at.isoformat(),
                updated_at=group.updated_at.isoformat()
            )
        )

    return response


@router.get("/{group_id}", response_model=GroupResponse)
def get_group_endpoint(
    group_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific group by ID with devices and alert summary

    Args:
        group_id: UUID of the group

    Returns:
        Group object with devices and alert summary

    Raises:
        404: Group not found
    """
    logger.info(f"Fetching group {group_id}")

    group = group_service.get_group_by_id(db, group_id)

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group {group_id} not found"
        )

    # Get devices and alert summary
    devices = group_service.get_group_devices(db, group_id)
    alert_summary = group_service.get_group_alert_summary(db, group_id)

    return GroupResponse(
        id=str(group.id),
        name=group.name,
        description=group.description,
        devices=[
            DeviceInGroupResponse(
                id=str(device.id),
                name=device.name,
                unit=device.unit,
                status=device.status.value
            )
            for device in devices
        ],
        alert_summary=AlertSummaryResponse(
            normal=alert_summary.normal,
            warning=alert_summary.warning,
            critical=alert_summary.critical
        ),
        created_at=group.created_at.isoformat(),
        updated_at=group.updated_at.isoformat()
    )


@router.put("/{group_id}", response_model=GroupResponse)
@require_admin
def update_group_endpoint(
    group_id: UUID,
    group_data: GroupUpdateRequest,
    db: Session = Depends(get_db),
    current_user = None  # Injected by require_admin decorator
):
    """
    Update an existing group (admin/owner only)

    Args:
        group_id: UUID of the group to update
        group_data: Fields to update

    Returns:
        Updated group object

    Raises:
        400: Validation error
        403: Insufficient permissions
        404: Group not found
    """
    logger.info(f"Updating group {group_id}")

    try:
        # Convert device ID strings to UUIDs if provided
        device_ids = None
        if group_data.device_ids is not None:
            device_ids = [UUID(device_id) for device_id in group_data.device_ids]

        group = group_service.update_group(
            db=db,
            group_id=group_id,
            name=group_data.name,
            description=group_data.description,
            device_ids=device_ids
        )

        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Group {group_id} not found"
            )

        logger.info(f"Group updated successfully: {group.name} (ID: {group.id})")

        # Get devices and alert summary for response
        devices = group_service.get_group_devices(db, group.id)
        alert_summary = group_service.get_group_alert_summary(db, group.id)

        return GroupResponse(
            id=str(group.id),
            name=group.name,
            description=group.description,
            devices=[
                DeviceInGroupResponse(
                    id=str(device.id),
                    name=device.name,
                    unit=device.unit,
                    status=device.status.value
                )
                for device in devices
            ],
            alert_summary=AlertSummaryResponse(
                normal=alert_summary.normal,
                warning=alert_summary.warning,
                critical=alert_summary.critical
            ),
            created_at=group.created_at.isoformat(),
            updated_at=group.updated_at.isoformat()
        )

    except ValueError as e:
        logger.warning(f"Validation error updating group: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_admin
def delete_group_endpoint(
    group_id: UUID,
    db: Session = Depends(get_db),
    current_user = None  # Injected by require_admin decorator
):
    """
    Delete a group (admin/owner only)

    Devices in the group are preserved.

    Args:
        group_id: UUID of the group to delete

    Returns:
        204 No Content on success

    Raises:
        403: Insufficient permissions
        404: Group not found
    """
    logger.info(f"Deleting group {group_id}")

    success = group_service.delete_group(db, group_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group {group_id} not found"
        )

    logger.info(f"Group {group_id} deleted successfully")


@router.get("/{group_id}/readings", response_model=GroupReadingsResponse)
def get_group_readings_endpoint(
    group_id: UUID,
    hours: Optional[int] = Query(default=24, description="Number of hours to look back"),
    limit: Optional[int] = Query(default=1000, description="Maximum number of readings"),
    db: Session = Depends(get_db)
):
    """
    Get readings from all devices in a group

    Args:
        group_id: UUID of the group
        hours: Number of hours to look back (default: 24)
        limit: Maximum number of readings (default: 1000)

    Returns:
        Collection of readings from all devices in the group

    Raises:
        404: Group not found
    """
    logger.info(f"Fetching readings for group {group_id} (hours={hours}, limit={limit})")

    # Verify group exists
    group = group_service.get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group {group_id} not found"
        )

    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)

    # Get readings
    readings = group_service.get_group_readings(
        db=db,
        group_id=group_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )

    return GroupReadingsResponse(
        group_id=str(group_id),
        readings=[
            GroupReadingResponse(
                device_id=str(reading.device_id),
                device_name=reading.device_name,
                timestamp=reading.timestamp.isoformat(),
                value=reading.value,
                unit=reading.unit
            )
            for reading in readings
        ],
        total=len(readings)
    )
