"""
Contract test for GET /api/export/device/{device_id} (T105)
Tests CSV export functionality with time ranges and formats
"""
import pytest
import uuid
import csv
import io
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.db.base import Base
from src.api.dependencies import get_db
from src.models.user import User, UserRole
from src.models.device import Device, DeviceStatus
from src.models.reading import Reading
from src.utils.auth import hash_password, create_access_token


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
    """Create test client"""
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
def test_user(test_db):
    """Create test user"""
    user = User(
        id=uuid.uuid4(),
        username="testuser",
        password_hash=hash_password("Test123!"),
        role=UserRole.ADMIN,
        language_preference="en"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user):
    """Generate auth token"""
    return create_access_token({
        "sub": test_user.username,
        "user_id": str(test_user.id),
        "role": test_user.role.value
    })


@pytest.fixture
def test_device(test_db):
    """Create test device"""
    device = Device(
        id=uuid.uuid4(),
        name="Temperature Sensor",
        modbus_ip="192.168.1.100",
        modbus_port=502,
        modbus_slave_id=1,
        modbus_register=0,
        modbus_register_count=1,
        unit="°C",
        sampling_interval=10,
        retention_days=90,
        status=DeviceStatus.CONNECTED
    )
    test_db.add(device)
    test_db.commit()
    test_db.refresh(device)
    return device


@pytest.fixture
def export_readings(test_db, test_device):
    """Create readings for export testing"""
    base_time = datetime.utcnow() - timedelta(hours=24)
    readings = []

    # Create 100 readings over 24 hours
    for i in range(100):
        timestamp = base_time + timedelta(minutes=i * 14.4)  # ~15 min intervals
        reading = Reading(
            timestamp=timestamp,
            device_id=test_device.id,
            value=20.0 + (i * 0.1)
        )
        readings.append(reading)

    test_db.add_all(readings)
    test_db.commit()

    return readings


class TestExportDeviceData:
    """Test GET /api/export/device/{device_id} endpoint"""

    def test_export_requires_authentication(self, client, test_device):
        """Test that export requires authentication"""
        response = client.get(f"/api/export/device/{test_device.id}")

        assert response.status_code == 401

    def test_export_with_invalid_device_id(self, client, auth_token):
        """Test export with non-existent device"""
        fake_id = uuid.uuid4()
        response = client.get(
            f"/api/export/device/{fake_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 404

    def test_export_returns_csv_format(self, client, auth_token, test_device, export_readings):
        """Test that export returns CSV content type"""
        response = client.get(
            f"/api/export/device/{test_device.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

    def test_export_has_content_disposition_header(self, client, auth_token, test_device, export_readings):
        """Test that export has proper content-disposition header"""
        response = client.get(
            f"/api/export/device/{test_device.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        assert "content-disposition" in response.headers
        assert "attachment" in response.headers["content-disposition"]
        assert "Temperature_Sensor" in response.headers["content-disposition"]
        assert ".csv" in response.headers["content-disposition"]

    def test_export_csv_structure(self, client, auth_token, test_device, export_readings):
        """Test that CSV has correct structure"""
        response = client.get(
            f"/api/export/device/{test_device.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200

        # Parse CSV
        csv_content = response.text
        csv_reader = csv.DictReader(io.StringIO(csv_content))

        # Check headers
        headers = csv_reader.fieldnames
        assert "timestamp" in headers
        assert "value" in headers
        assert "unit" in headers

    def test_export_csv_data_integrity(self, client, auth_token, test_device, export_readings):
        """Test that exported data matches database"""
        response = client.get(
            f"/api/export/device/{test_device.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200

        # Parse CSV
        csv_content = response.text
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(csv_reader)

        # Check row count
        assert len(rows) == len(export_readings)

        # Check first row data
        first_row = rows[0]
        assert "timestamp" in first_row
        assert "value" in first_row
        assert first_row["unit"] == "°C"

    def test_export_with_time_range(self, client, auth_token, test_device, export_readings):
        """Test export with start_time and end_time parameters"""
        start_time = datetime.utcnow() - timedelta(hours=12)
        end_time = datetime.utcnow() - timedelta(hours=6)

        response = client.get(
            f"/api/export/device/{test_device.id}",
            params={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200

        # Parse CSV and verify time range
        csv_content = response.text
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(csv_reader)

        assert len(rows) > 0
        assert len(rows) < len(export_readings)  # Should be filtered

    def test_export_empty_result(self, client, auth_token, test_device):
        """Test export with no data in range"""
        start_time = datetime.utcnow() + timedelta(days=1)
        end_time = datetime.utcnow() + timedelta(days=2)

        response = client.get(
            f"/api/export/device/{test_device.id}",
            params={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200

        # Parse CSV
        csv_content = response.text
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(csv_reader)

        # Should have headers but no data rows
        assert len(rows) == 0

    def test_export_with_invalid_time_range(self, client, auth_token, test_device):
        """Test export with end_time before start_time"""
        start_time = datetime.utcnow()
        end_time = datetime.utcnow() - timedelta(days=1)

        response = client.get(
            f"/api/export/device/{test_device.id}",
            params={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 400

    def test_export_timestamp_format(self, client, auth_token, test_device, export_readings):
        """Test that timestamps are in ISO format"""
        response = client.get(
            f"/api/export/device/{test_device.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200

        # Parse CSV
        csv_content = response.text
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        first_row = next(csv_reader)

        # Verify ISO format
        timestamp_str = first_row["timestamp"]
        try:
            datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except ValueError:
            pytest.fail("Timestamp not in ISO format")

    def test_export_numeric_values(self, client, auth_token, test_device, export_readings):
        """Test that values are numeric"""
        response = client.get(
            f"/api/export/device/{test_device.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200

        # Parse CSV
        csv_content = response.text
        csv_reader = csv.DictReader(io.StringIO(csv_content))

        for row in csv_reader:
            value = row["value"]
            # Should be parseable as float
            assert float(value) >= 0

    def test_export_includes_device_metadata(self, client, auth_token, test_device, export_readings):
        """Test that CSV includes device metadata in headers or comments"""
        response = client.get(
            f"/api/export/device/{test_device.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        csv_content = response.text

        # Check if device name appears in content (either as comment or in filename)
        assert test_device.name in response.headers["content-disposition"] or \
               test_device.name in csv_content

    def test_export_rbac_all_roles_allowed(self, client, test_db, test_device, export_readings):
        """Test that all authenticated roles can export data"""
        roles = [UserRole.OWNER, UserRole.ADMIN, UserRole.READ_ONLY]

        for role in roles:
            # Create user with role
            user = User(
                id=uuid.uuid4(),
                username=f"user_{role.value}",
                password_hash=hash_password("Test123!"),
                role=role,
                language_preference="en"
            )
            test_db.add(user)
            test_db.commit()

            # Generate token
            token = create_access_token({
                "sub": user.username,
                "user_id": str(user.id),
                "role": role.value
            })

            # Test export access
            response = client.get(
                f"/api/export/device/{test_device.id}",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200, f"{role.value} should be able to export data"
            assert "text/csv" in response.headers["content-type"]

    def test_export_with_aggregation(self, client, auth_token, test_device, export_readings):
        """Test export with data aggregation"""
        response = client.get(
            f"/api/export/device/{test_device.id}",
            params={"aggregate": "1hour"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200

        # Parse CSV
        csv_content = response.text
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(csv_reader)

        # With aggregation, should have fewer rows
        assert len(rows) <= len(export_readings)

    def test_export_filename_sanitization(self, client, auth_token, test_db):
        """Test that device names with special characters are sanitized in filename"""
        # Create device with special characters in name
        device = Device(
            id=uuid.uuid4(),
            name="Test/Device:Special*Chars",
            modbus_ip="192.168.1.100",
            modbus_port=502,
            modbus_slave_id=1,
            modbus_register=0,
            modbus_register_count=1,
            unit="bar",
            sampling_interval=10,
            retention_days=90,
            status=DeviceStatus.CONNECTED
        )
        test_db.add(device)
        test_db.commit()

        response = client.get(
            f"/api/export/device/{device.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200

        # Filename should not contain dangerous characters
        filename = response.headers["content-disposition"]
        assert "/" not in filename.split("filename=")[1]
        assert "\\" not in filename.split("filename=")[1]
        assert "*" not in filename.split("filename=")[1]
