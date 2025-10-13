"""
Integration test for RBAC enforcement (T082)
Tests role-based access control across different endpoints
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.db.base import Base
from src.api.dependencies import get_db
from src.models.user import User, UserRole
from src.models.device import Device, DeviceStatus
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
def users_all_roles(test_db):
    """Create users with all three roles"""
    owner = User(
        id=uuid.uuid4(),
        username="owner",
        password_hash=hash_password("Owner123!"),
        role=UserRole.OWNER,
        language_preference="en"
    )
    admin = User(
        id=uuid.uuid4(),
        username="admin",
        password_hash=hash_password("Admin123!"),
        role=UserRole.ADMIN,
        language_preference="en"
    )
    readonly = User(
        id=uuid.uuid4(),
        username="readonly",
        password_hash=hash_password("Read123!"),
        role=UserRole.READ_ONLY,
        language_preference="en"
    )

    test_db.add_all([owner, admin, readonly])
    test_db.commit()

    return {
        "owner": owner,
        "admin": admin,
        "readonly": readonly
    }


@pytest.fixture
def tokens_all_roles(users_all_roles):
    """Generate tokens for all roles"""
    return {
        "owner": create_access_token({"sub": users_all_roles["owner"].username, "role": "owner"}),
        "admin": create_access_token({"sub": users_all_roles["admin"].username, "role": "admin"}),
        "readonly": create_access_token({"sub": users_all_roles["readonly"].username, "role": "read_only"})
    }


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
        retention_days=90,
        status=DeviceStatus.DISCONNECTED
    )
    test_db.add(device)
    test_db.commit()
    test_db.refresh(device)
    return device


class TestRBACDeviceManagement:
    """Test RBAC enforcement for device management endpoints"""

    def test_create_device_owner_allowed(self, client, tokens_all_roles):
        """Test owner can create devices"""
        response = client.post(
            "/api/devices",
            headers={"Authorization": f"Bearer {tokens_all_roles['owner']}"},
            json={
                "name": "New Device",
                "modbus_ip": "192.168.1.101",
                "modbus_port": 502,
                "modbus_slave_id": 1,
                "modbus_register": 0,
                "modbus_register_count": 1,
                "unit": "bar"
            }
        )

        assert response.status_code == 200

    def test_create_device_admin_allowed(self, client, tokens_all_roles):
        """Test admin can create devices"""
        response = client.post(
            "/api/devices",
            headers={"Authorization": f"Bearer {tokens_all_roles['admin']}"},
            json={
                "name": "Admin Device",
                "modbus_ip": "192.168.1.102",
                "modbus_port": 502,
                "modbus_slave_id": 1,
                "modbus_register": 0,
                "modbus_register_count": 1,
                "unit": "bar"
            }
        )

        assert response.status_code == 200

    def test_create_device_readonly_forbidden(self, client, tokens_all_roles):
        """Test read-only user cannot create devices"""
        response = client.post(
            "/api/devices",
            headers={"Authorization": f"Bearer {tokens_all_roles['readonly']}"},
            json={
                "name": "Readonly Device",
                "modbus_ip": "192.168.1.103",
                "modbus_port": 502,
                "modbus_slave_id": 1,
                "modbus_register": 0,
                "modbus_register_count": 1,
                "unit": "bar"
            }
        )

        assert response.status_code == 403

    def test_read_devices_all_roles_allowed(self, client, tokens_all_roles, sample_device):
        """Test all roles can read devices"""
        for role, token in tokens_all_roles.items():
            response = client.get(
                "/api/devices",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200, f"{role} should be able to read devices"

    def test_update_device_admin_allowed(self, client, tokens_all_roles, sample_device):
        """Test admin can update devices"""
        response = client.put(
            f"/api/devices/{sample_device.id}",
            headers={"Authorization": f"Bearer {tokens_all_roles['admin']}"},
            json={"sampling_interval": 30}
        )

        assert response.status_code == 200

    def test_update_device_readonly_forbidden(self, client, tokens_all_roles, sample_device):
        """Test read-only user cannot update devices"""
        response = client.put(
            f"/api/devices/{sample_device.id}",
            headers={"Authorization": f"Bearer {tokens_all_roles['readonly']}"},
            json={"sampling_interval": 30}
        )

        assert response.status_code == 403

    def test_delete_device_admin_allowed(self, client, tokens_all_roles, test_db):
        """Test admin can delete devices"""
        # Create a device to delete
        device = Device(
            id=uuid.uuid4(),
            name="To Delete",
            modbus_ip="192.168.1.104",
            modbus_port=502,
            modbus_slave_id=1,
            modbus_register=0,
            modbus_register_count=1,
            unit="°C",
            sampling_interval=10,
            retention_days=90,
            status=DeviceStatus.DISCONNECTED
        )
        test_db.add(device)
        test_db.commit()

        response = client.delete(
            f"/api/devices/{device.id}",
            headers={"Authorization": f"Bearer {tokens_all_roles['admin']}"}
        )

        assert response.status_code == 204

    def test_delete_device_readonly_forbidden(self, client, tokens_all_roles, sample_device):
        """Test read-only user cannot delete devices"""
        response = client.delete(
            f"/api/devices/{sample_device.id}",
            headers={"Authorization": f"Bearer {tokens_all_roles['readonly']}"}
        )

        assert response.status_code == 403


class TestRBACUserManagement:
    """Test RBAC enforcement for user management endpoints"""

    def test_create_user_owner_only(self, client, tokens_all_roles):
        """Test only owner can create users"""
        # Owner should succeed
        response = client.post(
            "/api/users",
            headers={"Authorization": f"Bearer {tokens_all_roles['owner']}"},
            json={
                "username": "newuser",
                "password": "NewUser123!",
                "role": "admin",
                "language_preference": "en"
            }
        )
        assert response.status_code == 200

        # Admin should be forbidden
        response = client.post(
            "/api/users",
            headers={"Authorization": f"Bearer {tokens_all_roles['admin']}"},
            json={
                "username": "another",
                "password": "Another123!",
                "role": "admin",
                "language_preference": "en"
            }
        )
        assert response.status_code == 403

        # Read-only should be forbidden
        response = client.post(
            "/api/users",
            headers={"Authorization": f"Bearer {tokens_all_roles['readonly']}"},
            json={
                "username": "yetanother",
                "password": "YetAnother123!",
                "role": "admin",
                "language_preference": "en"
            }
        )
        assert response.status_code == 403

    def test_list_users_owner_and_admin_only(self, client, tokens_all_roles):
        """Test only owner and admin can list users"""
        # Owner should succeed
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {tokens_all_roles['owner']}"}
        )
        assert response.status_code == 200

        # Admin should succeed
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {tokens_all_roles['admin']}"}
        )
        assert response.status_code == 200

        # Read-only should be forbidden
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {tokens_all_roles['readonly']}"}
        )
        assert response.status_code == 403

    def test_delete_user_owner_only(self, client, tokens_all_roles, users_all_roles, test_db):
        """Test only owner can delete users"""
        # Create a user to delete
        temp_user = User(
            id=uuid.uuid4(),
            username="todelete",
            password_hash=hash_password("Delete123!"),
            role=UserRole.ADMIN,
            language_preference="en"
        )
        test_db.add(temp_user)
        test_db.commit()

        # Admin should be forbidden
        response = client.delete(
            f"/api/users/{temp_user.id}",
            headers={"Authorization": f"Bearer {tokens_all_roles['admin']}"}
        )
        assert response.status_code == 403

        # Owner should succeed
        response = client.delete(
            f"/api/users/{temp_user.id}",
            headers={"Authorization": f"Bearer {tokens_all_roles['owner']}"}
        )
        assert response.status_code == 204


class TestRBACSystemConfiguration:
    """Test RBAC enforcement for system configuration endpoints"""

    def test_update_config_owner_only(self, client, tokens_all_roles):
        """Test only owner can update system configuration"""
        # Skip if endpoint doesn't exist yet
        pytest.skip("System config endpoint not yet implemented")


class TestRBACWithoutAuth:
    """Test that endpoints require authentication"""

    def test_device_endpoints_require_auth(self, client, sample_device):
        """Test device endpoints require authentication"""
        # GET devices
        response = client.get("/api/devices")
        assert response.status_code == 401

        # POST device
        response = client.post(
            "/api/devices",
            json={"name": "Test", "modbus_ip": "192.168.1.1", "modbus_port": 502,
                  "modbus_slave_id": 1, "modbus_register": 0, "modbus_register_count": 1, "unit": "bar"}
        )
        assert response.status_code == 401

        # PUT device
        response = client.put(
            f"/api/devices/{sample_device.id}",
            json={"sampling_interval": 30}
        )
        assert response.status_code == 401

        # DELETE device
        response = client.delete(f"/api/devices/{sample_device.id}")
        assert response.status_code == 401

    def test_user_endpoints_require_auth(self, client):
        """Test user endpoints require authentication"""
        # GET users
        response = client.get("/api/users")
        assert response.status_code == 401

        # POST user
        response = client.post(
            "/api/users",
            json={"username": "test", "password": "Test123!", "role": "admin", "language_preference": "en"}
        )
        assert response.status_code == 401


class TestRBACTokenValidation:
    """Test token validation and expiration"""

    def test_invalid_token_rejected(self, client):
        """Test that invalid tokens are rejected"""
        response = client.get(
            "/api/devices",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    def test_malformed_token_rejected(self, client):
        """Test that malformed tokens are rejected"""
        response = client.get(
            "/api/devices",
            headers={"Authorization": "InvalidFormat"}
        )
        assert response.status_code == 401

    def test_missing_bearer_prefix_rejected(self, client, tokens_all_roles):
        """Test that tokens without Bearer prefix are rejected"""
        response = client.get(
            "/api/devices",
            headers={"Authorization": tokens_all_roles['owner']}
        )
        assert response.status_code == 401
