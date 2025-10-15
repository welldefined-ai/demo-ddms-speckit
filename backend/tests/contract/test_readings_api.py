"""
Contract tests for readings API endpoints

These tests verify the API contract matches the OpenAPI specification
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import uuid

from src.main import app
from src.db.session import SessionLocal
from src.models.device import Device, DeviceStatus
from src.models.reading import Reading

client = TestClient(app)


@pytest.fixture
def test_device():
    """Create a test device with readings"""
    db = SessionLocal()
    try:
        device = Device(
            id=uuid.uuid4(),
            name="Test Temperature Sensor",
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

        # Add a reading
        reading = Reading(
            timestamp=datetime.utcnow(),
            device_id=device.id,
            value=25.5
        )
        db.add(reading)
        db.commit()

        yield device
    finally:
        db.close()


class TestGetLatestReading:
    """Test GET /api/devices/{device_id}/latest endpoint"""

    def test_get_latest_reading_success(self, test_device):
        """Test getting latest reading for a device"""
        response = client.get(f"/api/devices/{test_device.id}/latest")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "device_id" in data
        assert "timestamp" in data
        assert "value" in data
        assert "status" in data
        assert "device_name" in data
        assert "unit" in data

        # Verify data values
        assert data["device_id"] == str(test_device.id)
        assert data["device_name"] == test_device.name
        assert data["unit"] == test_device.unit
        assert data["value"] == 25.5
        assert data["status"] in ["normal", "warning", "critical"]

    def test_get_latest_reading_device_not_found(self):
        """Test getting latest reading for non-existent device"""
        fake_id = uuid.uuid4()
        response = client.get(f"/api/devices/{fake_id}/latest")

        assert response.status_code == 404
        data = response.json()
        assert "error" in data or "detail" in data

    def test_get_latest_reading_no_readings(self, test_device):
        """Test getting latest reading when device has no readings"""
        # Delete all readings
        db = SessionLocal()
        db.query(Reading).filter(Reading.device_id == test_device.id).delete()
        db.commit()
        db.close()

        response = client.get(f"/api/devices/{test_device.id}/latest")

        assert response.status_code == 404
        data = response.json()
        assert "error" in data or "detail" in data

    def test_get_latest_reading_normal_status(self, test_device):
        """Test that reading within thresholds returns normal status"""
        response = client.get(f"/api/devices/{test_device.id}/latest")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "normal"  # 25.5 is between 10-30 (warning thresholds)

    def test_get_latest_reading_warning_status(self, test_device):
        """Test that reading at warning threshold returns warning status"""
        db = SessionLocal()
        # Add reading at warning threshold
        reading = Reading(
            timestamp=datetime.utcnow(),
            device_id=test_device.id,
            value=35.0  # Above warning_upper (30), below critical_upper (40)
        )
        db.add(reading)
        db.commit()
        db.close()

        response = client.get(f"/api/devices/{test_device.id}/latest")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "warning"

    def test_get_latest_reading_critical_status(self, test_device):
        """Test that reading at critical threshold returns critical status"""
        db = SessionLocal()
        # Add reading at critical threshold
        reading = Reading(
            timestamp=datetime.utcnow(),
            device_id=test_device.id,
            value=45.0  # Above critical_upper (40)
        )
        db.add(reading)
        db.commit()
        db.close()

        response = client.get(f"/api/devices/{test_device.id}/latest")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "critical"
