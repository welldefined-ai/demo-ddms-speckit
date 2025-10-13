"""
Contract test for GET /api/readings/{device_id} with time range (T104)
Tests historical data retrieval with various time ranges and pagination
"""
import pytest
import uuid
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
        name="Test Device",
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
def historical_readings(test_db, test_device):
    """Create historical readings for testing"""
    base_time = datetime.utcnow() - timedelta(days=7)
    readings = []

    # Create readings over 7 days with 1 hour intervals
    for day in range(7):
        for hour in range(24):
            timestamp = base_time + timedelta(days=day, hours=hour)
            reading = Reading(
                timestamp=timestamp,
                device_id=test_device.id,
                value=20.0 + (day * 2) + (hour * 0.1)  # Varying values
            )
            readings.append(reading)

    test_db.add_all(readings)
    test_db.commit()

    return readings


class TestGetDeviceReadings:
    """Test GET /api/readings/{device_id} endpoint"""

    def test_get_readings_requires_authentication(self, client, test_device):
        """Test that endpoint requires authentication"""
        response = client.get(f"/api/readings/{test_device.id}")

        assert response.status_code == 401

    def test_get_readings_with_invalid_device_id(self, client, auth_token):
        """Test with non-existent device ID"""
        fake_id = uuid.uuid4()
        response = client.get(
            f"/api/readings/{fake_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 404

    def test_get_all_readings_no_time_filter(self, client, auth_token, test_device, historical_readings):
        """Test getting all readings without time filter"""
        response = client.get(
            f"/api/readings/{test_device.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "readings" in data
        assert "total" in data
        assert isinstance(data["readings"], list)
        assert data["total"] == len(historical_readings)

    def test_get_readings_with_time_range(self, client, auth_token, test_device, historical_readings):
        """Test getting readings with start_time and end_time"""
        start_time = datetime.utcnow() - timedelta(days=3)
        end_time = datetime.utcnow() - timedelta(days=1)

        response = client.get(
            f"/api/readings/{test_device.id}",
            params={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "readings" in data
        assert len(data["readings"]) > 0

        # Verify readings are within time range
        for reading in data["readings"]:
            reading_time = datetime.fromisoformat(reading["timestamp"].replace('Z', '+00:00'))
            assert start_time <= reading_time <= end_time

    def test_get_readings_with_pagination(self, client, auth_token, test_device, historical_readings):
        """Test pagination with limit and offset"""
        response = client.get(
            f"/api/readings/{test_device.id}",
            params={"limit": 10, "offset": 0},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["readings"]) == 10
        assert data["total"] == len(historical_readings)

    def test_get_readings_with_offset(self, client, auth_token, test_device, historical_readings):
        """Test pagination offset"""
        # First page
        response1 = client.get(
            f"/api/readings/{test_device.id}",
            params={"limit": 10, "offset": 0},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Second page
        response2 = client.get(
            f"/api/readings/{test_device.id}",
            params={"limit": 10, "offset": 10},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        # Ensure different readings
        assert data1["readings"][0]["timestamp"] != data2["readings"][0]["timestamp"]

    def test_get_readings_ordered_by_time_desc(self, client, auth_token, test_device, historical_readings):
        """Test that readings are ordered by timestamp descending (newest first)"""
        response = client.get(
            f"/api/readings/{test_device.id}",
            params={"limit": 5},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        readings = data["readings"]
        timestamps = [datetime.fromisoformat(r["timestamp"].replace('Z', '+00:00'))
                     for r in readings]

        # Verify descending order
        for i in range(len(timestamps) - 1):
            assert timestamps[i] >= timestamps[i + 1]

    def test_get_readings_with_aggregate_level(self, client, auth_token, test_device, historical_readings):
        """Test getting readings with aggregation level"""
        response = client.get(
            f"/api/readings/{test_device.id}",
            params={"aggregate": "1hour"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "readings" in data
        # With aggregation, should have fewer readings
        assert len(data["readings"]) <= len(historical_readings)

    def test_get_readings_response_schema(self, client, auth_token, test_device, historical_readings):
        """Test response schema structure"""
        response = client.get(
            f"/api/readings/{test_device.id}",
            params={"limit": 1},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Check top-level structure
        assert "readings" in data
        assert "total" in data
        assert "device_id" in data

        # Check reading structure
        reading = data["readings"][0]
        assert "timestamp" in reading
        assert "value" in reading
        assert isinstance(reading["value"], (int, float))

    def test_get_readings_with_invalid_time_range(self, client, auth_token, test_device):
        """Test with end_time before start_time"""
        start_time = datetime.utcnow()
        end_time = datetime.utcnow() - timedelta(days=1)

        response = client.get(
            f"/api/readings/{test_device.id}",
            params={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 400

    def test_get_readings_with_invalid_limit(self, client, auth_token, test_device):
        """Test with invalid limit value"""
        response = client.get(
            f"/api/readings/{test_device.id}",
            params={"limit": -1},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 400

    def test_get_readings_with_large_limit(self, client, auth_token, test_device, historical_readings):
        """Test with very large limit value"""
        response = client.get(
            f"/api/readings/{test_device.id}",
            params={"limit": 10000},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Should cap at reasonable maximum
        assert len(data["readings"]) <= 1000

    def test_get_readings_empty_result(self, client, auth_token, test_device):
        """Test with device that has no readings"""
        # Query future time range
        start_time = datetime.utcnow() + timedelta(days=1)
        end_time = datetime.utcnow() + timedelta(days=2)

        response = client.get(
            f"/api/readings/{test_device.id}",
            params={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["readings"] == []
        assert data["total"] == 0

    def test_get_readings_with_multiple_aggregates(self, client, auth_token, test_device, historical_readings):
        """Test different aggregate levels"""
        aggregate_levels = ["1min", "1hour", "1day"]

        for level in aggregate_levels:
            response = client.get(
                f"/api/readings/{test_device.id}",
                params={"aggregate": level},
                headers={"Authorization": f"Bearer {auth_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "readings" in data

    def test_get_readings_rbac_all_roles_allowed(self, client, test_db, test_device, historical_readings):
        """Test that all authenticated roles can read data"""
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

            # Test read access
            response = client.get(
                f"/api/readings/{test_device.id}",
                headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200, f"{role.value} should be able to read readings"
