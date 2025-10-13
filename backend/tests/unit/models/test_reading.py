"""
Unit tests for Reading model
"""
import pytest
import uuid
from datetime import datetime
from src.models.reading import Reading
from src.models.device import Device


class TestReadingModel:
    """Test Reading model functionality"""

    def test_create_reading(self, db_session, sample_device_data):
        """Test creating a reading"""
        # Create a device first
        device = Device(id=uuid.uuid4(), **sample_device_data)
        db_session.add(device)
        db_session.commit()

        # Create a reading
        reading = Reading(
            timestamp=datetime.utcnow(),
            device_id=device.id,
            value=25.5
        )

        db_session.add(reading)
        db_session.commit()

        assert reading.timestamp is not None
        assert reading.device_id == device.id
        assert reading.value == 25.5

    def test_reading_repr(self, db_session, sample_device_data):
        """Test reading string representation"""
        device = Device(id=uuid.uuid4(), **sample_device_data)
        db_session.add(device)
        db_session.commit()

        reading = Reading(
            timestamp=datetime.utcnow(),
            device_id=device.id,
            value=30.0
        )
        db_session.add(reading)
        db_session.commit()

        repr_str = repr(reading)
        assert "Reading" in repr_str
        assert str(device.id) in repr_str
