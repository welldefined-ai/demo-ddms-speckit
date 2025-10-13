"""
Contract tests for device CRUD API endpoints
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.db.base import Base
from src.api.dependencies import get_db
from src.models.device import Device, DeviceStatus
from src.models.user import User
from src.services.auth_service import hash_password


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_db():
    """Create test database"""
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    yield db

    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create test client with database override"""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(test_db):
    """Create admin user for testing"""
    user = User(
        id=uuid.uuid4(),
        username="admin",
        password_hash=hash_password("Admin123!"),
        role="admin",
        language_preference="en"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, admin_user):
    """Get authentication headers for admin user"""
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "Admin123!"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_device(test_db):
    """Create sample device for testing"""
    device = Device(
        id=uuid.uuid4(),
        name="Test Device",
        modbus_ip="192.168.1.100",
        modbus_port=502,
        modbus_slave_id=1,
        modbus_register=0,
        modbus_register_count=1,
        unit="°C",
        sampling_interval=10,
        threshold_warning_lower=10.0,
        threshold_warning_upper=50.0,
        threshold_critical_lower=0.0,
        threshold_critical_upper=80.0,
        retention_days=90,
        status=DeviceStatus.DISCONNECTED
    )
    test_db.add(device)
    test_db.commit()
    test_db.refresh(device)
    return device


class TestCreateDeviceEndpoint:
    """Contract tests for POST /api/devices"""

    def test_create_device_success(self, client, auth_headers):
        """Test successful device creation (T055)"""
        device_data = {
            "name": "New Device",
            "modbus_ip": "192.168.1.101",
            "modbus_port": 502,
            "modbus_slave_id": 1,
            "modbus_register": 0,
            "modbus_register_count": 1,
            "unit": "bar",
            "sampling_interval": 15,
            "threshold_warning_lower": 5.0,
            "threshold_warning_upper": 45.0,
            "threshold_critical_lower": -5.0,
            "threshold_critical_upper": 60.0,
            "retention_days": 120
        }

        response = client.post(
            "/api/devices",
            json=device_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == device_data["name"]
        assert data["modbus_ip"] == device_data["modbus_ip"]
        assert data["unit"] == device_data["unit"]
        assert data["status"] == "disconnected"
        assert "id" in data

    def test_create_device_minimal_fields(self, client, auth_headers):
        """Test device creation with minimal required fields"""
        device_data = {
            "name": "Minimal Device",
            "modbus_ip": "192.168.1.102",
            "modbus_port": 502,
            "modbus_slave_id": 1,
            "modbus_register": 0,
            "modbus_register_count": 1,
            "unit": "units"
        }

        response = client.post(
            "/api/devices",
            json=device_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sampling_interval"] == 10  # Default
        assert data["retention_days"] == 90  # Default

    def test_create_device_duplicate_name_fails(self, client, auth_headers, sample_device):
        """Test that duplicate device name fails"""
        device_data = {
            "name": sample_device.name,  # Duplicate name
            "modbus_ip": "192.168.1.200",
            "modbus_port": 502,
            "modbus_slave_id": 1,
            "modbus_register": 0,
            "modbus_register_count": 1,
            "unit": "°C"
        }

        response = client.post(
            "/api/devices",
            json=device_data,
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_create_device_invalid_thresholds(self, client, auth_headers):
        """Test device creation with invalid threshold configuration"""
        device_data = {
            "name": "Invalid Thresholds",
            "modbus_ip": "192.168.1.103",
            "modbus_port": 502,
            "modbus_slave_id": 1,
            "modbus_register": 0,
            "modbus_register_count": 1,
            "unit": "°C",
            "threshold_warning_lower": 50.0,
            "threshold_warning_upper": 30.0  # Invalid: lower >= upper
        }

        response = client.post(
            "/api/devices",
            json=device_data,
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "threshold" in response.json()["detail"].lower()

    def test_create_device_unauthorized(self, client):
        """Test device creation without authentication"""
        device_data = {
            "name": "Unauthorized Device",
            "modbus_ip": "192.168.1.104",
            "modbus_port": 502,
            "modbus_slave_id": 1,
            "modbus_register": 0,
            "modbus_register_count": 1,
            "unit": "°C"
        }

        response = client.post("/api/devices", json=device_data)

        assert response.status_code == 401

    def test_create_device_missing_required_field(self, client, auth_headers):
        """Test device creation with missing required field"""
        device_data = {
            "name": "Missing Fields",
            # Missing modbus_ip
            "modbus_port": 502,
            "modbus_slave_id": 1,
            "modbus_register": 0,
            "modbus_register_count": 1,
            "unit": "°C"
        }

        response = client.post(
            "/api/devices",
            json=device_data,
            headers=auth_headers
        )

        assert response.status_code == 422  # Validation error


class TestUpdateDeviceEndpoint:
    """Contract tests for PUT /api/devices/{device_id}"""

    def test_update_device_success(self, client, auth_headers, sample_device):
        """Test successful device update (T056)"""
        update_data = {
            "name": "Updated Device Name",
            "sampling_interval": 30,
            "unit": "kPa"
        }

        response = client.put(
            f"/api/devices/{sample_device.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["sampling_interval"] == update_data["sampling_interval"]
        assert data["unit"] == update_data["unit"]
        # Unchanged fields should remain the same
        assert data["modbus_ip"] == sample_device.modbus_ip

    def test_update_device_partial_update(self, client, auth_headers, sample_device):
        """Test partial device update with single field"""
        update_data = {
            "sampling_interval": 60
        }

        response = client.put(
            f"/api/devices/{sample_device.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sampling_interval"] == 60
        assert data["name"] == sample_device.name  # Unchanged

    def test_update_device_thresholds(self, client, auth_headers, sample_device):
        """Test updating device thresholds"""
        update_data = {
            "threshold_warning_lower": 15.0,
            "threshold_warning_upper": 45.0,
            "threshold_critical_lower": 5.0,
            "threshold_critical_upper": 70.0
        }

        response = client.put(
            f"/api/devices/{sample_device.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["threshold_warning_lower"] == 15.0
        assert data["threshold_warning_upper"] == 45.0

    def test_update_device_not_found(self, client, auth_headers):
        """Test updating non-existent device"""
        fake_id = str(uuid.uuid4())
        update_data = {"name": "New Name"}

        response = client.put(
            f"/api/devices/{fake_id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_update_device_invalid_threshold_validation(self, client, auth_headers, sample_device):
        """Test update with invalid threshold configuration"""
        update_data = {
            "threshold_warning_lower": 60.0,
            "threshold_warning_upper": 40.0  # Invalid
        }

        response = client.put(
            f"/api/devices/{sample_device.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 400

    def test_update_device_unauthorized(self, client, sample_device):
        """Test device update without authentication"""
        update_data = {"name": "Unauthorized Update"}

        response = client.put(
            f"/api/devices/{sample_device.id}",
            json=update_data
        )

        assert response.status_code == 401


class TestDeleteDeviceEndpoint:
    """Contract tests for DELETE /api/devices/{device_id}"""

    def test_delete_device_without_keeping_data(self, client, auth_headers, sample_device):
        """Test deleting device without keeping data (T057)"""
        response = client.delete(
            f"/api/devices/{sample_device.id}?keep_data=false",
            headers=auth_headers
        )

        assert response.status_code == 204

        # Verify device is deleted
        get_response = client.get(
            f"/api/devices/{sample_device.id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404

    def test_delete_device_keep_data(self, client, auth_headers, sample_device):
        """Test deleting device while keeping data"""
        response = client.delete(
            f"/api/devices/{sample_device.id}?keep_data=true",
            headers=auth_headers
        )

        assert response.status_code == 204

        # Verify device is deleted
        get_response = client.get(
            f"/api/devices/{sample_device.id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404

    def test_delete_device_default_keep_data_false(self, client, auth_headers, sample_device):
        """Test delete device with default keep_data parameter"""
        response = client.delete(
            f"/api/devices/{sample_device.id}",
            headers=auth_headers
        )

        assert response.status_code == 204

    def test_delete_device_not_found(self, client, auth_headers):
        """Test deleting non-existent device"""
        fake_id = str(uuid.uuid4())

        response = client.delete(
            f"/api/devices/{fake_id}",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_delete_device_unauthorized(self, client, sample_device):
        """Test device deletion without authentication"""
        response = client.delete(f"/api/devices/{sample_device.id}")

        assert response.status_code == 401


class TestListDevicesEndpoint:
    """Contract tests for GET /api/devices"""

    def test_list_all_devices(self, client, auth_headers, sample_device):
        """Test listing all devices"""
        response = client.get("/api/devices", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(d["id"] == str(sample_device.id) for d in data)

    def test_list_devices_with_status_filter(self, client, auth_headers, test_db):
        """Test listing devices with status filter"""
        # Create devices with different statuses
        devices = []
        for i, status in enumerate([DeviceStatus.CONNECTED, DeviceStatus.DISCONNECTED]):
            device = Device(
                id=uuid.uuid4(),
                name=f"Device {i}",
                modbus_ip=f"192.168.1.{110 + i}",
                modbus_port=502,
                modbus_slave_id=1,
                modbus_register=0,
                modbus_register_count=1,
                unit="units",
                sampling_interval=10,
                retention_days=90,
                status=status
            )
            test_db.add(device)
            devices.append(device)
        test_db.commit()

        # Filter by CONNECTED
        response = client.get(
            "/api/devices?status_filter=connected",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert all(d["status"] == "connected" for d in data)

    def test_list_devices_empty(self, client, auth_headers):
        """Test listing devices when none exist"""
        response = client.get("/api/devices", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestGetDeviceEndpoint:
    """Contract tests for GET /api/devices/{device_id}"""

    def test_get_device_by_id_success(self, client, auth_headers, sample_device):
        """Test getting device by ID"""
        response = client.get(
            f"/api/devices/{sample_device.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_device.id)
        assert data["name"] == sample_device.name
        assert data["modbus_ip"] == sample_device.modbus_ip

    def test_get_device_not_found(self, client, auth_headers):
        """Test getting non-existent device"""
        fake_id = str(uuid.uuid4())

        response = client.get(
            f"/api/devices/{fake_id}",
            headers=auth_headers
        )

        assert response.status_code == 404


class TestTestConnectionEndpoint:
    """Contract tests for POST /api/devices/{device_id}/test-connection"""

    @pytest.mark.asyncio
    async def test_test_connection_endpoint(self, client, auth_headers, sample_device):
        """Test connection testing endpoint"""
        with pytest.patch('src.services.device_service.test_modbus_connection') as mock_test:
            mock_test.return_value = (True, None)

            response = client.post(
                f"/api/devices/{sample_device.id}/test-connection",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert "success" in data
