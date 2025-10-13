"""
Unit tests for device service
"""
import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from src.services.device_service import (
    get_device_status,
    get_latest_reading_with_status,
    create_device,
    update_device,
    delete_device,
    list_devices,
    get_device_by_id,
    test_modbus_connection
)
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


class TestCreateDevice:
    """Test create_device function"""

    def test_create_device_success(self, db_session, sample_device_data):
        """Test successful device creation"""
        device = create_device(db_session, **sample_device_data)

        assert device.id is not None
        assert device.name == sample_device_data["name"]
        assert device.modbus_ip == sample_device_data["modbus_ip"]
        assert device.modbus_port == sample_device_data["modbus_port"]
        assert device.unit == sample_device_data["unit"]
        assert device.status == DeviceStatus.DISCONNECTED

    def test_create_device_duplicate_name_fails(self, db_session, sample_device_data):
        """Test that creating device with duplicate name fails"""
        create_device(db_session, **sample_device_data)

        with pytest.raises(ValueError, match="Device with name .* already exists"):
            create_device(db_session, **sample_device_data)

    def test_create_device_threshold_validation(self, db_session):
        """Test threshold validation during device creation"""
        # Warning thresholds invalid (lower >= upper)
        with pytest.raises(ValueError, match="Warning lower threshold must be less than"):
            create_device(
                db_session,
                name="Test Device",
                modbus_ip="192.168.1.100",
                modbus_port=502,
                modbus_slave_id=1,
                modbus_register=0,
                modbus_register_count=1,
                unit="°C",
                threshold_warning_lower=50.0,
                threshold_warning_upper=30.0  # Invalid: lower >= upper
            )

    def test_create_device_critical_outside_warning_validation(self, db_session):
        """Test that critical thresholds must be outside warning thresholds"""
        # Critical lower >= warning lower (invalid)
        with pytest.raises(ValueError, match="Critical lower threshold must be less than"):
            create_device(
                db_session,
                name="Test Device",
                modbus_ip="192.168.1.100",
                modbus_port=502,
                modbus_slave_id=1,
                modbus_register=0,
                modbus_register_count=1,
                unit="°C",
                threshold_warning_lower=10.0,
                threshold_warning_upper=50.0,
                threshold_critical_lower=15.0,  # Invalid: >= warning lower
                threshold_critical_upper=80.0
            )

    def test_create_device_minimal_fields(self, db_session):
        """Test device creation with only required fields"""
        device = create_device(
            db_session,
            name="Minimal Device",
            modbus_ip="192.168.1.100",
            modbus_port=502,
            modbus_slave_id=1,
            modbus_register=0,
            modbus_register_count=1,
            unit="units"
        )

        assert device.id is not None
        assert device.sampling_interval == 10  # Default
        assert device.retention_days == 90  # Default
        assert device.threshold_warning_lower is None
        assert device.threshold_warning_upper is None


class TestUpdateDevice:
    """Test update_device function"""

    def test_update_device_success(self, db_session, sample_device):
        """Test successful device update"""
        updated = update_device(
            db_session,
            sample_device.id,
            name="Updated Name",
            sampling_interval=30
        )

        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.sampling_interval == 30
        assert updated.modbus_ip == sample_device.modbus_ip  # Unchanged

    def test_update_device_not_found(self, db_session):
        """Test updating non-existent device"""
        fake_id = uuid.uuid4()
        result = update_device(db_session, fake_id, name="New Name")
        assert result is None

    def test_update_device_thresholds(self, db_session, sample_device):
        """Test updating device thresholds"""
        updated = update_device(
            db_session,
            sample_device.id,
            threshold_warning_lower=5.0,
            threshold_warning_upper=55.0,
            threshold_critical_lower=-5.0,
            threshold_critical_upper=65.0
        )

        assert updated is not None
        assert updated.threshold_warning_lower == 5.0
        assert updated.threshold_warning_upper == 55.0

    def test_update_device_partial_update(self, db_session, sample_device):
        """Test partial update with only one field"""
        original_name = sample_device.name
        updated = update_device(db_session, sample_device.id, unit="bar")

        assert updated is not None
        assert updated.unit == "bar"
        assert updated.name == original_name  # Unchanged


class TestDeleteDevice:
    """Test delete_device function"""

    def test_delete_device_without_data(self, db_session, sample_device):
        """Test deleting device without keeping data"""
        # Add some readings
        reading = Reading(
            timestamp=datetime.utcnow(),
            device_id=sample_device.id,
            value=25.0
        )
        db_session.add(reading)
        db_session.commit()

        success = delete_device(db_session, sample_device.id, keep_data=False)

        assert success is True
        # Device should be deleted
        device = db_session.query(Device).filter(Device.id == sample_device.id).first()
        assert device is None
        # Readings should also be deleted
        readings = db_session.query(Reading).filter(Reading.device_id == sample_device.id).all()
        assert len(readings) == 0

    def test_delete_device_keep_data(self, db_session, sample_device):
        """Test deleting device while keeping data"""
        # Add some readings
        reading = Reading(
            timestamp=datetime.utcnow(),
            device_id=sample_device.id,
            value=25.0
        )
        db_session.add(reading)
        db_session.commit()

        success = delete_device(db_session, sample_device.id, keep_data=True)

        assert success is True
        # Device should be deleted
        device = db_session.query(Device).filter(Device.id == sample_device.id).first()
        assert device is None
        # Readings should be kept
        readings = db_session.query(Reading).filter(Reading.device_id == sample_device.id).all()
        assert len(readings) == 1

    def test_delete_device_not_found(self, db_session):
        """Test deleting non-existent device"""
        fake_id = uuid.uuid4()
        success = delete_device(db_session, fake_id)
        assert success is False


class TestListDevices:
    """Test list_devices function"""

    def test_list_all_devices(self, db_session):
        """Test listing all devices"""
        # Create multiple devices
        for i in range(3):
            device = Device(
                id=uuid.uuid4(),
                name=f"Device {i}",
                modbus_ip=f"192.168.1.{100 + i}",
                modbus_port=502,
                modbus_slave_id=1,
                modbus_register=0,
                unit="units",
                sampling_interval=10,
                retention_days=90,
                status=DeviceStatus.CONNECTED if i % 2 == 0 else DeviceStatus.DISCONNECTED
            )
            db_session.add(device)
        db_session.commit()

        devices = list_devices(db_session)
        assert len(devices) == 3

    def test_list_devices_with_status_filter(self, db_session):
        """Test listing devices with status filter"""
        # Create devices with different statuses
        for i, status in enumerate([DeviceStatus.CONNECTED, DeviceStatus.DISCONNECTED, DeviceStatus.ERROR]):
            device = Device(
                id=uuid.uuid4(),
                name=f"Device {i}",
                modbus_ip=f"192.168.1.{100 + i}",
                modbus_port=502,
                modbus_slave_id=1,
                modbus_register=0,
                unit="units",
                sampling_interval=10,
                retention_days=90,
                status=status
            )
            db_session.add(device)
        db_session.commit()

        connected_devices = list_devices(db_session, status_filter=DeviceStatus.CONNECTED)
        assert len(connected_devices) == 1
        assert connected_devices[0].status == DeviceStatus.CONNECTED

    def test_list_devices_empty(self, db_session):
        """Test listing devices when none exist"""
        devices = list_devices(db_session)
        assert len(devices) == 0


class TestGetDeviceById:
    """Test get_device_by_id function"""

    def test_get_existing_device(self, db_session, sample_device):
        """Test getting an existing device"""
        device = get_device_by_id(db_session, sample_device.id)
        assert device is not None
        assert device.id == sample_device.id
        assert device.name == sample_device.name

    def test_get_non_existent_device(self, db_session):
        """Test getting a non-existent device"""
        fake_id = uuid.uuid4()
        device = get_device_by_id(db_session, fake_id)
        assert device is None


class TestModbusConnectionTest:
    """Test test_modbus_connection function"""

    @pytest.mark.asyncio
    async def test_connection_success(self, db_session, sample_device):
        """Test successful Modbus connection"""
        with patch('src.services.device_service.ModbusCollector') as mock_collector_class:
            mock_collector = AsyncMock()
            mock_collector.connect.return_value = True
            mock_collector.read_value.return_value = 25.5
            mock_collector.close = AsyncMock()
            mock_collector_class.return_value = mock_collector

            success, error = await test_modbus_connection(
                db_session,
                sample_device.id
            )

            assert success is True
            assert error is None
            mock_collector.connect.assert_called_once()
            mock_collector.read_value.assert_called_once()
            mock_collector.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_connection_failure(self, db_session, sample_device):
        """Test failed Modbus connection"""
        with patch('src.services.device_service.ModbusCollector') as mock_collector_class:
            mock_collector = AsyncMock()
            mock_collector.connect.return_value = False
            mock_collector.close = AsyncMock()
            mock_collector_class.return_value = mock_collector

            success, error = await test_modbus_connection(
                db_session,
                sample_device.id
            )

            assert success is False
            assert error is not None
            assert "Failed to connect" in error

    @pytest.mark.asyncio
    async def test_connection_device_not_found(self, db_session):
        """Test connection test with non-existent device"""
        fake_id = uuid.uuid4()
        success, error = await test_modbus_connection(db_session, fake_id)

        assert success is False
        assert error is not None
        assert "not found" in error.lower()

    @pytest.mark.asyncio
    async def test_connection_read_failure(self, db_session, sample_device):
        """Test connection with read failure"""
        with patch('src.services.device_service.ModbusCollector') as mock_collector_class:
            mock_collector = AsyncMock()
            mock_collector.connect.return_value = True
            mock_collector.read_value.return_value = None  # Read failed
            mock_collector.close = AsyncMock()
            mock_collector_class.return_value = mock_collector

            success, error = await test_modbus_connection(
                db_session,
                sample_device.id
            )

            assert success is False
            assert error is not None
            assert "Failed to read" in error
