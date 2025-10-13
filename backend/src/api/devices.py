"""
Device API endpoints
"""
import asyncio
import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from uuid import UUID

from src.db.session import get_db
from src.services.device_service import get_latest_reading_with_status
from src.models.device import Device
from src.utils.logging import get_logger

router = APIRouter(prefix="/devices", tags=["Devices"])
logger = get_logger("ddms.api.devices")


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
