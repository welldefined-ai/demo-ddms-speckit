"""
Device API endpoints
"""
import asyncio
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel, Field

from src.db.session import get_db
from src.services import device_service
from src.services.device_service import get_latest_reading_with_status
from src.models.device import Device, DeviceStatus
from src.utils.logging import get_logger
from src.utils.rbac import require_admin

router = APIRouter(prefix="/devices", tags=["Devices"])
logger = get_logger("ddms.api.devices")


# Request/Response schemas
class DeviceCreateRequest(BaseModel):
    """Request schema for creating a device"""
    name: str = Field(..., min_length=1, max_length=100, description="Device name (must be unique)")
    modbus_ip: str = Field(..., description="Modbus device IP address")
    modbus_port: int = Field(default=502, ge=1, le=65535, description="Modbus device port")
    modbus_slave_id: int = Field(..., ge=1, le=255, description="Modbus slave ID")
    modbus_register: int = Field(..., ge=0, description="Starting register address")
    modbus_register_count: int = Field(default=1, ge=1, le=100, description="Number of registers to read")
    unit: str = Field(..., min_length=1, max_length=20, description="Measurement unit")
    sampling_interval: int = Field(default=10, ge=1, le=3600, description="Data collection interval in seconds")
    threshold_warning_lower: Optional[float] = Field(default=None, description="Lower warning threshold")
    threshold_warning_upper: Optional[float] = Field(default=None, description="Upper warning threshold")
    threshold_critical_lower: Optional[float] = Field(default=None, description="Lower critical threshold")
    threshold_critical_upper: Optional[float] = Field(default=None, description="Upper critical threshold")
    retention_days: int = Field(default=90, ge=1, le=3650, description="Number of days to retain data")


class DeviceUpdateRequest(BaseModel):
    """Request schema for updating a device"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    modbus_ip: Optional[str] = None
    modbus_port: Optional[int] = Field(default=None, ge=1, le=65535)
    modbus_slave_id: Optional[int] = Field(default=None, ge=1, le=255)
    modbus_register: Optional[int] = Field(default=None, ge=0)
    modbus_register_count: Optional[int] = Field(default=None, ge=1, le=100)
    unit: Optional[str] = Field(default=None, min_length=1, max_length=20)
    sampling_interval: Optional[int] = Field(default=None, ge=1, le=3600)
    threshold_warning_lower: Optional[float] = None
    threshold_warning_upper: Optional[float] = None
    threshold_critical_lower: Optional[float] = None
    threshold_critical_upper: Optional[float] = None
    retention_days: Optional[int] = Field(default=None, ge=1, le=3650)


class DeviceResponse(BaseModel):
    """Response schema for device data"""
    id: str
    name: str
    modbus_ip: str
    modbus_port: int
    modbus_slave_id: int
    modbus_register: int
    modbus_register_count: int
    unit: str
    sampling_interval: int
    threshold_warning_lower: Optional[float]
    threshold_warning_upper: Optional[float]
    threshold_critical_lower: Optional[float]
    threshold_critical_upper: Optional[float]
    retention_days: int
    status: str
    last_reading_at: Optional[str]
    created_at: str
    updated_at: str


@router.get("/{device_id}/latest")
def get_device_latest_reading(
    device_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get the latest reading for a device with calculated status

    Returns:
        - device_id: UUID of the device
        - device_name: Name of the device
        - unit: Measurement unit
        - timestamp: Timestamp of the reading
        - value: Measured value
        - status: Calculated status (normal/warning/critical)

    Raises:
        404: Device not found or has no readings
    """
    logger.info(f"Fetching latest reading for device {device_id}")

    result = get_latest_reading_with_status(db, device_id)

    if result is None:
        logger.warning(f"Device {device_id} not found or has no readings")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found or has no readings"
        )

    return {
        "device_id": str(result.device_id),
        "device_name": result.device_name,
        "unit": result.unit,
        "timestamp": result.latest_timestamp.isoformat(),
        "value": result.latest_value,
        "status": result.status
    }


async def device_stream_generator(db: Session):
    """
    Generator function for SSE stream of device readings

    Yields device readings in Server-Sent Events format
    """
    try:
        while True:
            # Fetch all online devices
            devices = db.query(Device).all()

            # Collect latest readings for all devices
            devices_data = []
            for device in devices:
                result = get_latest_reading_with_status(db, device.id)
                if result:
                    devices_data.append({
                        "device_id": str(result.device_id),
                        "device_name": result.device_name,
                        "unit": result.unit,
                        "timestamp": result.latest_timestamp.isoformat(),
                        "value": result.latest_value,
                        "status": result.status
                    })

            # Send as SSE event
            if devices_data:
                yield f"data: {json.dumps(devices_data)}\n\n"

            # Wait before next update (5 seconds)
            await asyncio.sleep(5)

    except asyncio.CancelledError:
        logger.info("SSE stream cancelled by client")
    except Exception as e:
        logger.error(f"Error in SSE stream: {e}")
        yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"


@router.get("/stream")
async def stream_device_readings(db: Session = Depends(get_db)):
    """
    Server-Sent Events (SSE) stream of real-time device readings

    This endpoint streams device readings to clients using the SSE protocol.
    Clients should use EventSource API to consume this stream.

    Returns:
        StreamingResponse with text/event-stream content type

    Example usage in JavaScript:
        const eventSource = new EventSource('/api/devices/stream');
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Received devices:', data);
        };
    """
    logger.info("Starting SSE stream for device readings")

    return StreamingResponse(
        device_stream_generator(db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


# Device CRUD endpoints (User Story 2)

@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
@require_admin
def create_device_endpoint(
    device_data: DeviceCreateRequest,
    db: Session = Depends(get_db),
    current_user = None  # Injected by require_admin decorator
):
    """
    Create a new device (admin/owner only)

    Args:
        device_data: Device configuration data

    Returns:
        Created device object

    Raises:
        400: Validation error (duplicate name, invalid thresholds, etc.)
        403: Insufficient permissions (not admin/owner)
    """
    logger.info(f"Creating new device: {device_data.name}")

    try:
        device = device_service.create_device(
            db=db,
            name=device_data.name,
            modbus_ip=device_data.modbus_ip,
            modbus_port=device_data.modbus_port,
            modbus_slave_id=device_data.modbus_slave_id,
            modbus_register=device_data.modbus_register,
            modbus_register_count=device_data.modbus_register_count,
            unit=device_data.unit,
            sampling_interval=device_data.sampling_interval,
            threshold_warning_lower=device_data.threshold_warning_lower,
            threshold_warning_upper=device_data.threshold_warning_upper,
            threshold_critical_lower=device_data.threshold_critical_lower,
            threshold_critical_upper=device_data.threshold_critical_upper,
            retention_days=device_data.retention_days
        )

        logger.info(f"Device created successfully: {device.name} (ID: {device.id})")

        # TODO: Start monitoring this device via device_manager
        # This will be wired up when device_manager is integrated

        return DeviceResponse(
            id=str(device.id),
            name=device.name,
            modbus_ip=device.modbus_ip,
            modbus_port=device.modbus_port,
            modbus_slave_id=device.modbus_slave_id,
            modbus_register=device.modbus_register,
            modbus_register_count=device.modbus_register_count,
            unit=device.unit,
            sampling_interval=device.sampling_interval,
            threshold_warning_lower=device.threshold_warning_lower,
            threshold_warning_upper=device.threshold_warning_upper,
            threshold_critical_lower=device.threshold_critical_lower,
            threshold_critical_upper=device.threshold_critical_upper,
            retention_days=device.retention_days,
            status=device.status.value,
            last_reading_at=device.last_reading_at.isoformat() if device.last_reading_at else None,
            created_at=device.created_at.isoformat(),
            updated_at=device.updated_at.isoformat()
        )

    except ValueError as e:
        logger.warning(f"Validation error creating device: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[DeviceResponse])
def list_devices_endpoint(
    status_filter: Optional[str] = Query(default=None, description="Filter by status (connected/disconnected/error)"),
    db: Session = Depends(get_db)
):
    """
    List all devices, optionally filtered by status

    Args:
        status_filter: Optional status filter (connected, disconnected, error)

    Returns:
        List of device objects
    """
    logger.info(f"Listing devices (status_filter={status_filter})")

    # Parse status filter
    status_enum = None
    if status_filter:
        try:
            status_enum = DeviceStatus(status_filter.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status filter: {status_filter}. Must be one of: connected, disconnected, error"
            )

    devices = device_service.list_devices(db, status_filter=status_enum)

    return [
        DeviceResponse(
            id=str(device.id),
            name=device.name,
            modbus_ip=device.modbus_ip,
            modbus_port=device.modbus_port,
            modbus_slave_id=device.modbus_slave_id,
            modbus_register=device.modbus_register,
            modbus_register_count=device.modbus_register_count,
            unit=device.unit,
            sampling_interval=device.sampling_interval,
            threshold_warning_lower=device.threshold_warning_lower,
            threshold_warning_upper=device.threshold_warning_upper,
            threshold_critical_lower=device.threshold_critical_lower,
            threshold_critical_upper=device.threshold_critical_upper,
            retention_days=device.retention_days,
            status=device.status.value,
            last_reading_at=device.last_reading_at.isoformat() if device.last_reading_at else None,
            created_at=device.created_at.isoformat(),
            updated_at=device.updated_at.isoformat()
        )
        for device in devices
    ]


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device_endpoint(
    device_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific device by ID

    Args:
        device_id: UUID of the device

    Returns:
        Device object

    Raises:
        404: Device not found
    """
    logger.info(f"Fetching device {device_id}")

    device = device_service.get_device_by_id(db, device_id)

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device {device_id} not found"
        )

    return DeviceResponse(
        id=str(device.id),
        name=device.name,
        modbus_ip=device.modbus_ip,
        modbus_port=device.modbus_port,
        modbus_slave_id=device.modbus_slave_id,
        modbus_register=device.modbus_register,
        modbus_register_count=device.modbus_register_count,
        unit=device.unit,
        sampling_interval=device.sampling_interval,
        threshold_warning_lower=device.threshold_warning_lower,
        threshold_warning_upper=device.threshold_warning_upper,
        threshold_critical_lower=device.threshold_critical_lower,
        threshold_critical_upper=device.threshold_critical_upper,
        retention_days=device.retention_days,
        status=device.status.value,
        last_reading_at=device.last_reading_at.isoformat() if device.last_reading_at else None,
        created_at=device.created_at.isoformat(),
        updated_at=device.updated_at.isoformat()
    )


@router.put("/{device_id}", response_model=DeviceResponse)
@require_admin
def update_device_endpoint(
    device_id: UUID,
    device_data: DeviceUpdateRequest,
    db: Session = Depends(get_db),
    current_user = None  # Injected by require_admin decorator
):
    """
    Update an existing device (admin/owner only)

    Args:
        device_id: UUID of the device to update
        device_data: Fields to update

    Returns:
        Updated device object

    Raises:
        400: Validation error
        403: Insufficient permissions
        404: Device not found
    """
    logger.info(f"Updating device {device_id}")

    try:
        device = device_service.update_device(
            db=db,
            device_id=device_id,
            name=device_data.name,
            modbus_ip=device_data.modbus_ip,
            modbus_port=device_data.modbus_port,
            modbus_slave_id=device_data.modbus_slave_id,
            modbus_register=device_data.modbus_register,
            modbus_register_count=device_data.modbus_register_count,
            unit=device_data.unit,
            sampling_interval=device_data.sampling_interval,
            threshold_warning_lower=device_data.threshold_warning_lower,
            threshold_warning_upper=device_data.threshold_warning_upper,
            threshold_critical_lower=device_data.threshold_critical_lower,
            threshold_critical_upper=device_data.threshold_critical_upper,
            retention_days=device_data.retention_days
        )

        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device {device_id} not found"
            )

        logger.info(f"Device updated successfully: {device.name} (ID: {device.id})")

        # TODO: Reload device in device_manager if monitoring

        return DeviceResponse(
            id=str(device.id),
            name=device.name,
            modbus_ip=device.modbus_ip,
            modbus_port=device.modbus_port,
            modbus_slave_id=device.modbus_slave_id,
            modbus_register=device.modbus_register,
            modbus_register_count=device.modbus_register_count,
            unit=device.unit,
            sampling_interval=device.sampling_interval,
            threshold_warning_lower=device.threshold_warning_lower,
            threshold_warning_upper=device.threshold_warning_upper,
            threshold_critical_lower=device.threshold_critical_lower,
            threshold_critical_upper=device.threshold_critical_upper,
            retention_days=device.retention_days,
            status=device.status.value,
            last_reading_at=device.last_reading_at.isoformat() if device.last_reading_at else None,
            created_at=device.created_at.isoformat(),
            updated_at=device.updated_at.isoformat()
        )

    except ValueError as e:
        logger.warning(f"Validation error updating device: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_admin
def delete_device_endpoint(
    device_id: UUID,
    keep_data: bool = Query(default=False, description="Keep historical data after deleting device"),
    db: Session = Depends(get_db),
    current_user = None  # Injected by require_admin decorator
):
    """
    Delete a device (admin/owner only)

    Args:
        device_id: UUID of the device to delete
        keep_data: If True, keep historical readings; if False, delete them

    Returns:
        204 No Content on success

    Raises:
        403: Insufficient permissions
        404: Device not found
    """
    logger.info(f"Deleting device {device_id} (keep_data={keep_data})")

    success = device_service.delete_device(db, device_id, keep_data=keep_data)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device {device_id} not found"
        )

    logger.info(f"Device {device_id} deleted successfully")

    # TODO: Stop monitoring this device in device_manager


@router.post("/{device_id}/test-connection")
@require_admin
async def test_device_connection_endpoint(
    device_id: UUID,
    db: Session = Depends(get_db),
    current_user = None  # Injected by require_admin decorator
):
    """
    Test connection to a device (admin/owner only)

    Args:
        device_id: UUID of the device to test

    Returns:
        Connection test result with success status and error message if failed

    Raises:
        403: Insufficient permissions
        404: Device not found
    """
    logger.info(f"Testing connection to device {device_id}")

    device = device_service.get_device_by_id(db, device_id)

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device {device_id} not found"
        )

    # Test connection
    success, error = await device_service.test_modbus_connection(
        modbus_ip=device.modbus_ip,
        modbus_port=device.modbus_port,
        modbus_slave_id=device.modbus_slave_id,
        modbus_register=device.modbus_register,
        modbus_register_count=device.modbus_register_count,
        timeout=5
    )

    logger.info(f"Connection test for device {device.name}: {'success' if success else 'failed'}")

    return {
        "success": success,
        "error": error,
        "device_id": str(device_id),
        "device_name": device.name
    }
