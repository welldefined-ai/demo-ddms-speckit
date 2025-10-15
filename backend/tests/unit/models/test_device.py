"""
Unit tests for Device model
"""
import pytest
import uuid
from sqlalchemy.exc import IntegrityError
from src.models.device import Device, DeviceStatus


class TestDeviceModel:
    """Test Device model functionality"""

    def test_create_device(self, db_session, sample_device_data):
        """Test creating a device"""
        device = Device(
            id=uuid.uuid4(),
            **sample_device_data
        )

        db_session.add(device)
        db_session.commit()

        assert device.id is not None
        assert device.name == sample_device_data["name"]
        assert device.modbus_ip == sample_device_data["modbus_ip"]
        assert device.modbus_port == sample_device_data["modbus_port"]
        assert device.status == DeviceStatus.OFFLINE
        assert device.created_at is not None

    def test_device_unique_name(self, db_session, sample_device_data):
        """Test that device name must be unique"""
        device1 = Device(id=uuid.uuid4(), **sample_device_data)
        db_session.add(device1)
        db_session.commit()

        # Attempt to create second device with same name
        device2_data = sample_device_data.copy()
        device2_data["modbus_ip"] = "192.168.1.101"
        device2 = Device(id=uuid.uuid4(), **device2_data)
        db_session.add(device2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_device_default_status(self, db_session, sample_device_data):
        """Test default device status is OFFLINE"""
        device = Device(id=uuid.uuid4(), **sample_device_data)
        db_session.add(device)
        db_session.commit()

        assert device.status == DeviceStatus.OFFLINE

    def test_device_default_retention_days(self, db_session, sample_device_data):
        """Test default retention days"""
        data = sample_device_data.copy()
        del data["retention_days"]

        device = Device(id=uuid.uuid4(), **data)
        db_session.add(device)
        db_session.commit()

        assert device.retention_days == 90

    def test_device_repr(self, db_session, sample_device_data):
        """Test device string representation"""
        device = Device(id=uuid.uuid4(), **sample_device_data)
        db_session.add(device)
        db_session.commit()

        repr_str = repr(device)
        assert "Device" in repr_str
        assert sample_device_data["name"] in repr_str
