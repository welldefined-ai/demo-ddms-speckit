"""
Device manager for scheduling and coordinating device data collection
"""
import asyncio
from typing import Dict, Optional
from datetime import datetime
import uuid

from sqlalchemy.orm import Session

from src.models.device import Device, DeviceStatus
from src.models.reading import Reading
from src.collectors.modbus_collector import ModbusCollector
from src.db.session import SessionLocal
from src.utils.logging import get_logger
from src.services.notification_service import create_device_disconnect_notification

logger = get_logger(__name__)


class DeviceManager:
    """
    Manages data collection from multiple devices

    Responsibilities:
    - Schedule periodic data collection based on sampling_interval
    - Handle device connection/disconnection
    - Implement reconnection policy (60s retry, notify after 3 failures)
    - Store readings in database
    """

    def __init__(self):
        """Initialize device manager"""
        self.collectors: Dict[uuid.UUID, ModbusCollector] = {}
        self.tasks: Dict[uuid.UUID, asyncio.Task] = {}
        self.running = False
        self._stop_event = asyncio.Event()

    async def start(self):
        """Start device manager and begin monitoring devices"""
        self.running = True
        self._stop_event.clear()
        logger.info("Device manager started")

        # Load all active devices and start collection tasks
        db = SessionLocal()
        try:
            devices = db.query(Device).all()
            for device in devices:
                await self.add_device(device.id)
        finally:
            db.close()

    async def stop(self):
        """Stop device manager and all collection tasks"""
        self.running = False
        self._stop_event.set()
        logger.info("Stopping device manager...")

        # Stop all collection tasks
        for device_id in list(self.tasks.keys()):
            await self.remove_device(device_id)

        logger.info("Device manager stopped")

    async def add_device(self, device_id: uuid.UUID):
        """
        Add a device to be monitored

        Args:
            device_id: UUID of the device to add
        """
        if device_id in self.tasks:
            logger.warning(f"Device {device_id} is already being monitored")
            return

        # Get device info
        db = SessionLocal()
        try:
            device = db.query(Device).filter(Device.id == device_id).first()
            if not device:
                logger.error(f"Device {device_id} not found in database")
                return

            # Create collection task
            task = asyncio.create_task(self._collection_loop(device_id))
            self.tasks[device_id] = task

            logger.info(
                f"Started monitoring device {device.name} (ID: {device_id}) "
                f"with {device.sampling_interval}s interval"
            )

        finally:
            db.close()

    async def remove_device(self, device_id: uuid.UUID):
        """
        Stop monitoring a device

        Args:
            device_id: UUID of the device to remove
        """
        if device_id not in self.tasks:
            logger.warning(f"Device {device_id} is not being monitored")
            return

        # Cancel collection task
        task = self.tasks.pop(device_id)
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        # Close collector if exists
        if device_id in self.collectors:
            collector = self.collectors.pop(device_id)
            await collector.disconnect()

        logger.info(f"Stopped monitoring device {device_id}")

    async def _collection_loop(self, device_id: uuid.UUID):
        """
        Main collection loop for a device

        Handles:
        - Periodic data collection
        - Connection management
        - Error handling and reconnection
        - Status updates

        Args:
            device_id: UUID of the device
        """
        consecutive_failures = 0
        max_failures_before_notify = 3
        reconnection_delay = 60  # seconds

        while self.running:
            db = SessionLocal()
            try:
                # Get device info
                device = db.query(Device).filter(Device.id == device_id).first()
                if not device:
                    logger.error(f"Device {device_id} no longer exists, stopping collection")
                    break

                # Create or get collector
                if device_id not in self.collectors:
                    self.collectors[device_id] = ModbusCollector(
                        host=device.modbus_ip,
                        port=device.modbus_port,
                        timeout=10
                    )

                collector = self.collectors[device_id]

                # Attempt to read value
                value = await collector.read_value(
                    slave_id=device.modbus_slave_id,
                    register=device.modbus_register,
                    count=device.modbus_register_count
                )

                if value is not None:
                    # Success - store reading
                    reading = Reading(
                        device_id=device_id,
                        value=value,
                        timestamp=datetime.utcnow()
                    )
                    db.add(reading)

                    # Update device status
                    device.status = DeviceStatus.ONLINE
                    device.last_reading_at = datetime.utcnow()
                    db.commit()

                    # Reset failure counter
                    consecutive_failures = 0

                    logger.debug(
                        f"Collected reading from device {device.name}: {value} {device.unit}"
                    )

                else:
                    # Failure - handle reconnection
                    consecutive_failures += 1

                    logger.warning(
                        f"Failed to read from device {device.name} "
                        f"(failure {consecutive_failures})"
                    )

                    # Update device status
                    device.status = DeviceStatus.ERROR
                    db.commit()

                    # Notify after max failures
                    if consecutive_failures >= max_failures_before_notify:
                        logger.error(
                            f"Device {device.name} has failed {consecutive_failures} times. "
                            f"Connection lost. Will retry every {reconnection_delay}s."
                        )

                        # Create notification for all admin/owner users
                        try:
                            create_device_disconnect_notification(
                                db=db,
                                device_id=device.id,
                                device_name=device.name,
                                device_ip=device.modbus_ip,
                                last_reading_at=device.last_reading_at
                            )
                        except Exception as e:
                            # Don't let notification failures block device polling
                            logger.error(f"Failed to create device disconnect notification: {e}")

                    # Reconnection delay
                    await asyncio.sleep(reconnection_delay)
                    continue

                # Wait for next sampling interval
                await asyncio.sleep(device.sampling_interval)

            except asyncio.CancelledError:
                logger.info(f"Collection loop for device {device_id} cancelled")
                break

            except Exception as e:
                logger.error(
                    f"Unexpected error in collection loop for device {device_id}: {e}",
                    exc_info=True
                )
                consecutive_failures += 1

                # Update device status
                try:
                    device = db.query(Device).filter(Device.id == device_id).first()
                    if device:
                        device.status = DeviceStatus.ERROR
                        db.commit()
                except Exception:
                    pass

                await asyncio.sleep(reconnection_delay)

            finally:
                db.close()

    async def reload_device(self, device_id: uuid.UUID):
        """
        Reload device configuration (restart collection with new settings)

        Args:
            device_id: UUID of the device to reload
        """
        await self.remove_device(device_id)
        await self.add_device(device_id)
        logger.info(f"Reloaded device {device_id}")


# Global device manager instance
device_manager = DeviceManager()
