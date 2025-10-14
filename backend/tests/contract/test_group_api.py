"""
Contract tests for Group API endpoints (T123, T124, T125, T126)
Tests device grouping and group management functionality
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
from src.models.group import Group
from src.models.device_group import DeviceGroup
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
def test_admin(test_db):
    """Create test admin user"""
    user = User(
        id=uuid.uuid4(),
        username="admin",
        password_hash=hash_password("Admin123!"),
        role=UserRole.ADMIN,
        language_preference="en"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_read_only_user(test_db):
    """Create test read-only user"""
    user = User(
        id=uuid.uuid4(),
        username="readonly",
        password_hash=hash_password("Read123!"),
        role=UserRole.READ_ONLY,
        language_preference="en"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def admin_token(test_admin):
    """Generate admin auth token"""
    return create_access_token({
        "sub": test_admin.username,
        "user_id": str(test_admin.id),
        "role": test_admin.role.value
    })


@pytest.fixture
def readonly_token(test_read_only_user):
    """Generate read-only auth token"""
    return create_access_token({
        "sub": test_read_only_user.username,
        "user_id": str(test_read_only_user.id),
        "role": test_read_only_user.role.value
    })


@pytest.fixture
def test_devices(test_db):
    """Create test devices"""
    devices = []
    for i in range(3):
        device = Device(
            id=uuid.uuid4(),
            name=f"Test Device {i+1}",
            modbus_ip=f"192.168.1.{100+i}",
            modbus_port=502,
            modbus_slave_id=i+1,
            modbus_register=0,
            modbus_register_count=1,
            unit="°C",
            sampling_interval=10,
            retention_days=90,
            status=DeviceStatus.ONLINE
        )
        devices.append(device)
        test_db.add(device)

    test_db.commit()
    for device in devices:
        test_db.refresh(device)

    return devices


@pytest.fixture
def test_group(test_db):
    """Create test group"""
    group = Group(
        id=uuid.uuid4(),
        name="Test Group",
        description="Test group description"
    )
    test_db.add(group)
    test_db.commit()
    test_db.refresh(group)
    return group


@pytest.fixture
def test_group_with_devices(test_db, test_devices):
    """Create test group with devices"""
    group = Group(
        id=uuid.uuid4(),
        name="Group with Devices",
        description="Group containing multiple devices"
    )
    test_db.add(group)
    test_db.commit()
    test_db.refresh(group)

    # Add devices to group
    for device in test_devices[:2]:  # Add first 2 devices
        device_group = DeviceGroup(
            device_id=device.id,
            group_id=group.id
        )
        test_db.add(device_group)

    test_db.commit()
    return group


class TestGroupCreation:
    """Test POST /api/groups endpoint (T123)"""

    def test_create_group_requires_authentication(self, client):
        """Test that creating a group requires authentication"""
        response = client.post(
            "/api/groups",
            json={"name": "New Group", "description": "Description"}
        )

        assert response.status_code == 401

    def test_create_group_requires_admin(self, client, readonly_token):
        """Test that creating a group requires admin/owner role"""
        response = client.post(
            "/api/groups",
            json={"name": "New Group", "description": "Description"},
            headers={"Authorization": f"Bearer {readonly_token}"}
        )

        assert response.status_code == 403

    def test_create_group_successfully(self, client, admin_token):
        """Test successful group creation"""
        response = client.post(
            "/api/groups",
            json={
                "name": "Production Line 1",
                "description": "All devices on production line 1"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 201
        data = response.json()

        assert "id" in data
        assert data["name"] == "Production Line 1"
        assert data["description"] == "All devices on production line 1"
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_group_with_name_only(self, client, admin_token):
        """Test creating group with just a name (description optional)"""
        response = client.post(
            "/api/groups",
            json={"name": "Simple Group"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 201
        data = response.json()

        assert data["name"] == "Simple Group"
        assert data["description"] is None or data["description"] == ""

    def test_create_group_duplicate_name(self, client, admin_token, test_group):
        """Test that duplicate group names are rejected"""
        response = client.post(
            "/api/groups",
            json={"name": test_group.name, "description": "Different description"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_create_group_invalid_name(self, client, admin_token):
        """Test validation for invalid group names"""
        # Empty name
        response = client.post(
            "/api/groups",
            json={"name": "", "description": "Description"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 422  # Validation error

        # Name too long
        response = client.post(
            "/api/groups",
            json={"name": "A" * 101, "description": "Description"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 422


class TestGroupList:
    """Test GET /api/groups endpoint (T130)"""

    def test_list_groups_requires_authentication(self, client):
        """Test that listing groups requires authentication"""
        response = client.get("/api/groups")

        assert response.status_code == 401

    def test_list_groups_empty(self, client, admin_token):
        """Test listing groups when none exist"""
        response = client.get(
            "/api/groups",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_groups_multiple(self, client, admin_token, test_db):
        """Test listing multiple groups"""
        # Create multiple groups
        groups = []
        for i in range(3):
            group = Group(
                id=uuid.uuid4(),
                name=f"Group {i+1}",
                description=f"Description {i+1}"
            )
            groups.append(group)
            test_db.add(group)

        test_db.commit()

        response = client.get(
            "/api/groups",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 3
        assert all("id" in group for group in data)
        assert all("name" in group for group in data)

    def test_list_groups_accessible_to_all_roles(self, client, readonly_token):
        """Test that all authenticated users can list groups"""
        response = client.get(
            "/api/groups",
            headers={"Authorization": f"Bearer {readonly_token}"}
        )

        assert response.status_code == 200


class TestGroupDetail:
    """Test GET /api/groups/{group_id} endpoint (T131)"""

    def test_get_group_requires_authentication(self, client, test_group):
        """Test that getting group details requires authentication"""
        response = client.get(f"/api/groups/{test_group.id}")

        assert response.status_code == 401

    def test_get_group_not_found(self, client, admin_token):
        """Test getting non-existent group"""
        fake_id = uuid.uuid4()
        response = client.get(
            f"/api/groups/{fake_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 404

    def test_get_group_details(self, client, admin_token, test_group):
        """Test getting group details"""
        response = client.get(
            f"/api/groups/{test_group.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(test_group.id)
        assert data["name"] == test_group.name
        assert data["description"] == test_group.description
        assert "devices" in data
        assert "alert_summary" in data

    def test_get_group_with_devices(self, client, admin_token, test_group_with_devices):
        """Test getting group details with device list"""
        response = client.get(
            f"/api/groups/{test_group_with_devices.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "devices" in data
        assert len(data["devices"]) == 2

        # Verify device structure
        device = data["devices"][0]
        assert "id" in device
        assert "name" in device
        assert "status" in device

    def test_get_group_alert_summary(self, client, admin_token, test_group_with_devices, test_db):
        """Test group alert summary calculation"""
        # Get devices in group
        device_groups = test_db.query(DeviceGroup).filter(
            DeviceGroup.group_id == test_group_with_devices.id
        ).all()

        devices = [test_db.query(Device).filter(Device.id == dg.device_id).first()
                  for dg in device_groups]

        # Add readings with different statuses (requires threshold configuration)
        for device in devices:
            # Set thresholds
            device.threshold_warning_lower = 10.0
            device.threshold_warning_upper = 30.0
            device.threshold_critical_lower = 0.0
            device.threshold_critical_upper = 40.0

            # Add reading that triggers warning
            reading = Reading(
                timestamp=datetime.utcnow(),
                device_id=device.id,
                value=35.0  # Above warning threshold
            )
            test_db.add(reading)

        test_db.commit()

        response = client.get(
            f"/api/groups/{test_group_with_devices.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "alert_summary" in data
        assert "normal" in data["alert_summary"]
        assert "warning" in data["alert_summary"]
        assert "critical" in data["alert_summary"]


class TestGroupUpdate:
    """Test PUT /api/groups/{group_id} endpoint (T124, T132)"""

    def test_update_group_requires_authentication(self, client, test_group):
        """Test that updating group requires authentication"""
        response = client.put(
            f"/api/groups/{test_group.id}",
            json={"name": "Updated Name"}
        )

        assert response.status_code == 401

    def test_update_group_requires_admin(self, client, readonly_token, test_group):
        """Test that updating group requires admin/owner role"""
        response = client.put(
            f"/api/groups/{test_group.id}",
            json={"name": "Updated Name"},
            headers={"Authorization": f"Bearer {readonly_token}"}
        )

        assert response.status_code == 403

    def test_update_group_name_and_description(self, client, admin_token, test_group):
        """Test updating group name and description"""
        response = client.put(
            f"/api/groups/{test_group.id}",
            json={
                "name": "Updated Group Name",
                "description": "Updated description"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "Updated Group Name"
        assert data["description"] == "Updated description"

    def test_update_group_device_membership(self, client, admin_token, test_group, test_devices):
        """Test updating device membership in group (T124)"""
        device_ids = [str(device.id) for device in test_devices]

        response = client.put(
            f"/api/groups/{test_group.id}",
            json={"device_ids": device_ids},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "devices" in data
        assert len(data["devices"]) == len(test_devices)

    def test_update_group_remove_devices(self, client, admin_token, test_group_with_devices):
        """Test removing devices from group"""
        response = client.put(
            f"/api/groups/{test_group_with_devices.id}",
            json={"device_ids": []},  # Empty list removes all devices
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["devices"]) == 0

    def test_update_group_not_found(self, client, admin_token):
        """Test updating non-existent group"""
        fake_id = uuid.uuid4()
        response = client.put(
            f"/api/groups/{fake_id}",
            json={"name": "Updated Name"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 404


class TestGroupDeletion:
    """Test DELETE /api/groups/{group_id} endpoint (T133)"""

    def test_delete_group_requires_authentication(self, client, test_group):
        """Test that deleting group requires authentication"""
        response = client.delete(f"/api/groups/{test_group.id}")

        assert response.status_code == 401

    def test_delete_group_requires_admin(self, client, readonly_token, test_group):
        """Test that deleting group requires admin/owner role"""
        response = client.delete(
            f"/api/groups/{test_group.id}",
            headers={"Authorization": f"Bearer {readonly_token}"}
        )

        assert response.status_code == 403

    def test_delete_group_successfully(self, client, admin_token, test_group):
        """Test successful group deletion"""
        group_id = test_group.id

        response = client.delete(
            f"/api/groups/{group_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 204

        # Verify group is deleted
        response = client.get(
            f"/api/groups/{group_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 404

    def test_delete_group_with_devices(self, client, admin_token, test_group_with_devices, test_db):
        """Test deleting group preserves devices (only association is removed)"""
        group_id = test_group_with_devices.id

        # Get device IDs before deletion
        device_groups = test_db.query(DeviceGroup).filter(
            DeviceGroup.group_id == group_id
        ).all()
        device_ids = [dg.device_id for dg in device_groups]

        response = client.delete(
            f"/api/groups/{group_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 204

        # Verify devices still exist
        for device_id in device_ids:
            device = test_db.query(Device).filter(Device.id == device_id).first()
            assert device is not None

        # Verify associations are removed
        remaining_associations = test_db.query(DeviceGroup).filter(
            DeviceGroup.group_id == group_id
        ).all()
        assert len(remaining_associations) == 0

    def test_delete_group_not_found(self, client, admin_token):
        """Test deleting non-existent group"""
        fake_id = uuid.uuid4()
        response = client.delete(
            f"/api/groups/{fake_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 404


class TestGroupReadings:
    """Test GET /api/groups/{group_id}/readings endpoint (T125)"""

    def test_group_readings_requires_authentication(self, client, test_group):
        """Test that getting group readings requires authentication"""
        response = client.get(f"/api/groups/{test_group.id}/readings")

        assert response.status_code == 401

    def test_group_readings_not_found(self, client, admin_token):
        """Test getting readings for non-existent group"""
        fake_id = uuid.uuid4()
        response = client.get(
            f"/api/groups/{fake_id}/readings",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 404

    def test_group_readings_empty_group(self, client, admin_token, test_group):
        """Test getting readings for group with no devices"""
        response = client.get(
            f"/api/groups/{test_group.id}/readings",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "readings" in data
        assert len(data["readings"]) == 0

    def test_group_readings_multiple_devices(self, client, admin_token, test_group_with_devices, test_db):
        """Test getting readings from multiple devices in a group"""
        # Get devices in group
        device_groups = test_db.query(DeviceGroup).filter(
            DeviceGroup.group_id == test_group_with_devices.id
        ).all()

        devices = [test_db.query(Device).filter(Device.id == dg.device_id).first()
                  for dg in device_groups]

        # Add readings for each device
        base_time = datetime.utcnow() - timedelta(hours=1)
        for i, device in enumerate(devices):
            for j in range(5):
                reading = Reading(
                    timestamp=base_time + timedelta(minutes=j * 10),
                    device_id=device.id,
                    value=20.0 + i + j
                )
                test_db.add(reading)

        test_db.commit()

        response = client.get(
            f"/api/groups/{test_group_with_devices.id}/readings",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "readings" in data
        assert len(data["readings"]) > 0

        # Verify each reading has device_id, timestamp, value
        for reading in data["readings"]:
            assert "device_id" in reading
            assert "device_name" in reading
            assert "timestamp" in reading
            assert "value" in reading
            assert "unit" in reading

    def test_group_readings_with_time_range(self, client, admin_token, test_group_with_devices, test_db):
        """Test getting group readings with time range filter"""
        # Get devices in group
        device_groups = test_db.query(DeviceGroup).filter(
            DeviceGroup.group_id == test_group_with_devices.id
        ).all()

        devices = [test_db.query(Device).filter(Device.id == dg.device_id).first()
                  for dg in device_groups]

        # Add readings over 24 hours
        base_time = datetime.utcnow() - timedelta(hours=24)
        for device in devices:
            for hour in range(24):
                reading = Reading(
                    timestamp=base_time + timedelta(hours=hour),
                    device_id=device.id,
                    value=20.0 + hour
                )
                test_db.add(reading)

        test_db.commit()

        # Query with time range (last 12 hours)
        start_time = datetime.utcnow() - timedelta(hours=12)
        end_time = datetime.utcnow()

        response = client.get(
            f"/api/groups/{test_group_with_devices.id}/readings",
            params={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify readings are within time range
        for reading in data["readings"]:
            reading_time = datetime.fromisoformat(reading["timestamp"].replace('Z', '+00:00'))
            assert start_time <= reading_time <= end_time


class TestGroupExport:
    """Test GET /api/export/group/{group_id} endpoint (T126)"""

    def test_group_export_requires_authentication(self, client, test_group):
        """Test that exporting group data requires authentication"""
        response = client.get(f"/api/export/group/{test_group.id}")

        assert response.status_code == 401

    def test_group_export_not_found(self, client, admin_token):
        """Test exporting non-existent group"""
        fake_id = uuid.uuid4()
        response = client.get(
            f"/api/export/group/{fake_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 404

    def test_group_export_returns_csv(self, client, admin_token, test_group_with_devices, test_db):
        """Test that group export returns CSV format"""
        # Add some readings
        device_groups = test_db.query(DeviceGroup).filter(
            DeviceGroup.group_id == test_group_with_devices.id
        ).all()

        devices = [test_db.query(Device).filter(Device.id == dg.device_id).first()
                  for dg in device_groups]

        base_time = datetime.utcnow() - timedelta(hours=1)
        for device in devices:
            for i in range(5):
                reading = Reading(
                    timestamp=base_time + timedelta(minutes=i * 10),
                    device_id=device.id,
                    value=20.0 + i
                )
                test_db.add(reading)

        test_db.commit()

        response = client.get(
            f"/api/export/group/{test_group_with_devices.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

    def test_group_export_has_content_disposition(self, client, admin_token, test_group_with_devices, test_db):
        """Test that export has proper content-disposition header"""
        # Add a reading
        device_groups = test_db.query(DeviceGroup).filter(
            DeviceGroup.group_id == test_group_with_devices.id
        ).all()

        device = test_db.query(Device).filter(Device.id == device_groups[0].device_id).first()

        reading = Reading(
            timestamp=datetime.utcnow(),
            device_id=device.id,
            value=25.0
        )
        test_db.add(reading)
        test_db.commit()

        response = client.get(
            f"/api/export/group/{test_group_with_devices.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        assert "content-disposition" in response.headers
        assert "attachment" in response.headers["content-disposition"]
        assert ".csv" in response.headers["content-disposition"]

    def test_group_export_csv_structure(self, client, admin_token, test_group_with_devices, test_db):
        """Test that CSV has correct structure for multi-device data"""
        # Add readings
        device_groups = test_db.query(DeviceGroup).filter(
            DeviceGroup.group_id == test_group_with_devices.id
        ).all()

        devices = [test_db.query(Device).filter(Device.id == dg.device_id).first()
                  for dg in device_groups]

        base_time = datetime.utcnow() - timedelta(hours=1)
        for device in devices:
            reading = Reading(
                timestamp=base_time,
                device_id=device.id,
                value=20.0
            )
            test_db.add(reading)

        test_db.commit()

        response = client.get(
            f"/api/export/group/{test_group_with_devices.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200

        # Parse CSV
        import csv
        import io

        csv_content = response.text
        csv_reader = csv.DictReader(io.StringIO(csv_content))

        # Check headers include device_name for multi-device export
        headers = csv_reader.fieldnames
        assert "timestamp" in headers
        assert "device_name" in headers
        assert "value" in headers
        assert "unit" in headers

    def test_group_export_accessible_to_all_roles(self, client, readonly_token, test_group):
        """Test that all authenticated users can export group data"""
        response = client.get(
            f"/api/export/group/{test_group.id}",
            headers={"Authorization": f"Bearer {readonly_token}"}
        )

        # Should succeed (200) or return 404 if no data, but not 403
        assert response.status_code in [200, 404]
