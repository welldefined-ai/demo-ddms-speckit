"""
Unit tests for device service
"""
import pytest
import uuid
from datetime import datetime

from src.services.device_service import get_device_status, get_latest_reading_with_status
from src.models.device import Device, DeviceStatus
from src.models.reading import Reading


@pytest.fixture
def sample_device(db_session):
    """Create a sample device for testing"""
    device = Device(
        id=uuid.uuid4(),
        name="Test Sensor",
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
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)
    return device


class TestGetDeviceStatus:
    """Test get_device_status function"""

    def test_normal_status_within_thresholds(self, db_session, sample_device):
        """Test normal status calculation"""
        # Add reading within normal range
        reading = Reading(
            timestamp=datetime.utcnow(),
            device_id=sample_device.id,
            value=20.0
        )
        db_session.add(reading)
        db_session.commit()

        result = get_device_status(db_session, sample_device.id)

        assert result is not None
        assert result.status == "normal"
        assert result.latest_value == 20.0
        assert result.device_name == sample_device.name
        assert result.unit == sample_device.unit

    def test_warning_status_above_upper(self, db_session, sample_device):
        """Test warning status when above upper threshold"""
        reading = Reading(
            timestamp=datetime.utcnow(),
            device_id=sample_device.id,
            value=35.0  # Above warning, below critical
        )
        db_session.add(reading)
        db_session.commit()

        result = get_device_status(db_session, sample_device.id)

        assert result is not None
        assert result.status == "warning"
        assert result.latest_value == 35.0

    def test_warning_status_below_lower(self, db_session, sample_device):
        """Test warning status when below lower threshold"""
        reading = Reading(
            timestamp=datetime.utcnow(),
            device_id=sample_device.id,
            value=5.0  # Below warning, above critical
        )
        db_session.add(reading)
        db_session.commit()

        result = get_device_status(db_session, sample_device.id)

        assert result is not None
        assert result.status == "warning"
        assert result.latest_value == 5.0

    def test_critical_status_above_upper(self, db_session, sample_device):
        """Test critical status when above upper critical threshold"""
        reading = Reading(
            timestamp=datetime.utcnow(),
            device_id=sample_device.id,
            value=45.0  # Above critical
        )
        db_session.add(reading)
        db_session.commit()

        result = get_device_status(db_session, sample_device.id)

        assert result is not None
        assert result.status == "critical"
        assert result.latest_value == 45.0

    def test_critical_status_below_lower(self, db_session, sample_device):
        """Test critical status when below lower critical threshold"""
        reading = Reading(
            timestamp=datetime.utcnow(),
            device_id=sample_device.id,
            value=-5.0  # Below critical
        )
        db_session.add(reading)
        db_session.commit()

        result = get_device_status(db_session, sample_device.id)

        assert result is not None
        assert result.status == "critical"
        assert result.latest_value == -5.0

    def test_no_readings_returns_none(self, db_session, sample_device):
        """Test that None is returned when device has no readings"""
        result = get_device_status(db_session, sample_device.id)
        assert result is None

    def test_device_not_found_returns_none(self, db_session):
        """Test that None is returned for non-existent device"""
        fake_id = uuid.uuid4()
        result = get_device_status(db_session, fake_id)
        assert result is None

    def test_uses_latest_reading(self, db_session, sample_device):
        """Test that the latest reading is used for status calculation"""
        # Add multiple readings
        reading1 = Reading(
            timestamp=datetime(2024, 1, 1, 10, 0, 0),
            device_id=sample_device.id,
            value=20.0
        )
        reading2 = Reading(
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            device_id=sample_device.id,
            value=45.0  # Latest - critical
        )
        db_session.add_all([reading1, reading2])
        db_session.commit()

        result = get_device_status(db_session, sample_device.id)

        assert result is not None
        assert result.latest_value == 45.0
        assert result.status == "critical"

    def test_status_at_exact_threshold(self, db_session, sample_device):
        """Test status at exact threshold boundary"""
        # At warning upper threshold
        reading = Reading(
            timestamp=datetime.utcnow(),
            device_id=sample_device.id,
            value=30.0  # Exactly at warning_upper
        )
        db_session.add(reading)
        db_session.commit()

        result = get_device_status(db_session, sample_device.id)

        assert result is not None
        # At threshold is normal (not warning)
        assert result.status == "normal"

    def test_get_latest_reading_with_status_wrapper(self, db_session, sample_device):
        """Test the convenience wrapper function"""
        reading = Reading(
            timestamp=datetime.utcnow(),
            device_id=sample_device.id,
            value=25.0
        )
        db_session.add(reading)
        db_session.commit()

        result = get_latest_reading_with_status(db_session, sample_device.id)

        assert result is not None
        assert result.status == "normal"
        assert result.latest_value == 25.0


class TestDeviceStatusEdgeCases:
    """Test edge cases for device status calculation"""

    def test_device_without_thresholds(self, db_session):
        """Test device with no thresholds configured"""
        device = Device(
            id=uuid.uuid4(),
            name="No Threshold Device",
            modbus_ip="192.168.1.101",
            modbus_port=502,
            modbus_slave_id=1,
            modbus_register=0,
            unit="units",
            sampling_interval=10,
            retention_days=90
        )
        db_session.add(device)
        db_session.commit()

        reading = Reading(
            timestamp=datetime.utcnow(),
            device_id=device.id,
            value=100.0
        )
        db_session.add(reading)
        db_session.commit()

        result = get_device_status(db_session, device.id)

        # Without thresholds, status should be normal
        assert result is not None
        assert result.status == "normal"

    def test_negative_values(self, db_session, sample_device):
        """Test handling of negative values"""
        reading = Reading(
            timestamp=datetime.utcnow(),
            device_id=sample_device.id,
            value=-10.0  # Below critical_lower (0.0)
        )
        db_session.add(reading)
        db_session.commit()

        result = get_device_status(db_session, sample_device.id)

        assert result is not None
        assert result.status == "critical"

    def test_very_large_values(self, db_session, sample_device):
        """Test handling of very large values"""
        reading = Reading(
            timestamp=datetime.utcnow(),
            device_id=sample_device.id,
            value=999999.0
        )
        db_session.add(reading)
        db_session.commit()

        result = get_device_status(db_session, sample_device.id)

        assert result is not None
        assert result.status == "critical"
        assert result.latest_value == 999999.0
