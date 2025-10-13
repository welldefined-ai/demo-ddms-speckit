"""
Integration tests for device status calculation logic

Tests the business logic for determining device status based on thresholds
"""
import pytest
import uuid
from datetime import datetime

from src.db.session import SessionLocal
from src.models.device import Device, DeviceStatus
from src.models.reading import Reading
from src.services.device_service import get_device_status, DeviceStatusResult


@pytest.fixture
def test_device_with_thresholds():
    """Create a test device with threshold configuration"""
    db = SessionLocal()
    try:
        device = Device(
            id=uuid.uuid4(),
            name="Integration Test Device",
            modbus_ip="192.168.1.100",
            modbus_port=502,
            modbus_slave_id=1,
            modbus_register=0,
            unit="°C",
            sampling_interval=10,
            threshold_warning_lower=10.0,
            threshold_warning_upper=30.0,
            threshold_critical_lower=0.0,
            threshold_critical_upper=40.0,
            retention_days=90,
            status=DeviceStatus.ONLINE
        )
        db.add(device)
        db.commit()
        db.refresh(device)
        yield device
    finally:
        db.close()


class TestDeviceStatusCalculation:
    """Test device status calculation with various threshold scenarios"""

    def test_status_normal_within_thresholds(self, test_device_with_thresholds):
        """Test normal status when value is within warning thresholds"""
        db = SessionLocal()
        device = test_device_with_thresholds

        # Add reading within normal range
        reading = Reading(
            timestamp=datetime.utcnow(),
            device_id=device.id,
            value=20.0  # Between 10-30 (warning thresholds)
        )
        db.add(reading)
        db.commit()

        # Calculate status
        status = get_device_status(db, device.id)

        assert status is not None
        assert status.status == "normal"
        assert status.latest_value == 20.0
        db.close()

    def test_status_warning_above_upper_threshold(self, test_device_with_thresholds):
        """Test warning status when value exceeds warning upper threshold"""
        db = SessionLocal()
        device = test_device_with_thresholds

        reading = Reading(
            timestamp=datetime.utcnow(),
            device_id=device.id,
            value=35.0  # Above 30 (warning_upper), below 40 (critical_upper)
        )
        db.add(reading)
        db.commit()

        status = get_device_status(db, device.id)

        assert status is not None
        assert status.status == "warning"
        assert status.latest_value == 35.0
        db.close()

    def test_status_warning_below_lower_threshold(self, test_device_with_thresholds):
        """Test warning status when value is below warning lower threshold"""
        db = SessionLocal()
        device = test_device_with_thresholds

        reading = Reading(
            timestamp=datetime.utcnow(),
            device_id=device.id,
            value=5.0  # Below 10 (warning_lower), above 0 (critical_lower)
        )
        db.add(reading)
        db.commit()

        status = get_device_status(db, device.id)

        assert status is not None
        assert status.status == "warning"
        assert status.latest_value == 5.0
        db.close()

    def test_status_critical_above_upper_threshold(self, test_device_with_thresholds):
        """Test critical status when value exceeds critical upper threshold"""
        db = SessionLocal()
        device = test_device_with_thresholds

        reading = Reading(
            timestamp=datetime.utcnow(),
            device_id=device.id,
            value=45.0  # Above 40 (critical_upper)
        )
        db.add(reading)
        db.commit()

        status = get_device_status(db, device.id)

        assert status is not None
        assert status.status == "critical"
        assert status.latest_value == 45.0
        db.close()

    def test_status_critical_below_lower_threshold(self, test_device_with_thresholds):
        """Test critical status when value is below critical lower threshold"""
        db = SessionLocal()
        device = test_device_with_thresholds

        reading = Reading(
            timestamp=datetime.utcnow(),
            device_id=device.id,
            value=-5.0  # Below 0 (critical_lower)
        )
        db.add(reading)
        db.commit()

        status = get_device_status(db, device.id)

        assert status is not None
        assert status.status == "critical"
        assert status.latest_value == -5.0
        db.close()

    def test_status_no_readings_returns_none(self, test_device_with_thresholds):
        """Test that status returns None when device has no readings"""
        db = SessionLocal()
        device = test_device_with_thresholds

        status = get_device_status(db, device.id)

        assert status is None
        db.close()

    def test_status_uses_latest_reading(self, test_device_with_thresholds):
        """Test that status calculation uses the most recent reading"""
        db = SessionLocal()
        device = test_device_with_thresholds

        # Add multiple readings
        reading1 = Reading(
            timestamp=datetime(2024, 1, 1, 10, 0, 0),
            device_id=device.id,
            value=20.0
        )
        reading2 = Reading(
            timestamp=datetime(2024, 1, 1, 11, 0, 0),
            device_id=device.id,
            value=45.0  # Critical - this is the latest
        )
        db.add_all([reading1, reading2])
        db.commit()

        status = get_device_status(db, device.id)

        assert status is not None
        assert status.latest_value == 45.0
        assert status.status == "critical"
        db.close()

    def test_status_device_not_found(self):
        """Test that status returns None for non-existent device"""
        db = SessionLocal()
        fake_id = uuid.uuid4()

        status = get_device_status(db, fake_id)

        assert status is None
        db.close()
