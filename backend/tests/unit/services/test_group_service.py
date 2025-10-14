"""
Unit tests for group service (User Story 5)
"""
import pytest
import uuid
from datetime import datetime, timedelta

from src.services.group_service import (
    create_group,
    update_group,
    delete_group,
    list_groups,
    get_group_by_id,
    get_group_devices,
    get_group_alert_summary,
    get_group_readings,
    add_device_to_group,
    remove_device_from_group
)
from src.models.group import Group
from src.models.device_group import DeviceGroup
from src.models.device import Device, DeviceStatus
from src.models.reading import Reading


@pytest.fixture
def sample_devices(db_session):
    """Create sample devices for testing"""
    devices = []
    for i in range(3):
        device = Device(
            id=uuid.uuid4(),
            name=f"Test Device {i+1}",
            modbus_ip=f"192.168.1.{100+i}",
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
        devices.append(device)
        db_session.add(device)
    db_session.commit()

    for device in devices:
        db_session.refresh(device)

    return devices


@pytest.fixture
def sample_group(db_session, sample_devices):
    """Create a sample group with devices"""
    group = Group(
        id=uuid.uuid4(),
        name="Test Group",
        description="A test group"
    )
    db_session.add(group)
    db_session.commit()
    db_session.refresh(group)

    # Add first two devices to group
    for device in sample_devices[:2]:
        device_group = DeviceGroup(
            device_id=device.id,
            group_id=group.id
        )
        db_session.add(device_group)
    db_session.commit()

    return group


class TestCreateGroup:
    """Test create_group function"""

    def test_create_group_without_devices(self, db_session):
        """Test creating an empty group"""
        group = create_group(
            db_session,
            name="Empty Group",
            description="Group with no devices"
        )

        assert group.id is not None
        assert group.name == "Empty Group"
        assert group.description == "Group with no devices"

    def test_create_group_with_devices(self, db_session, sample_devices):
        """Test creating group with devices"""
        device_ids = [device.id for device in sample_devices[:2]]

        group = create_group(
            db_session,
            name="Group with Devices",
            description="Test group",
            device_ids=device_ids
        )

        assert group.id is not None

        # Verify devices were added
        devices = get_group_devices(db_session, group.id)
        assert len(devices) == 2

    def test_create_group_duplicate_name_fails(self, db_session):
        """Test that creating group with duplicate name fails"""
        create_group(db_session, name="Duplicate Group")

        with pytest.raises(ValueError, match="Group with name .* already exists"):
            create_group(db_session, name="Duplicate Group")

    def test_create_group_nonexistent_device_fails(self, db_session):
        """Test that creating group with non-existent device fails"""
        fake_device_id = uuid.uuid4()

        with pytest.raises(ValueError, match="Device with ID .* not found"):
            create_group(
                db_session,
                name="Test Group",
                device_ids=[fake_device_id]
            )


class TestUpdateGroup:
    """Test update_group function"""

    def test_update_group_name(self, db_session, sample_group):
        """Test updating group name"""
        updated = update_group(
            db_session,
            sample_group.id,
            name="Updated Name"
        )

        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.description == sample_group.description

    def test_update_group_description(self, db_session, sample_group):
        """Test updating group description"""
        updated = update_group(
            db_session,
            sample_group.id,
            description="New description"
        )

        assert updated is not None
        assert updated.description == "New description"

    def test_update_group_devices(self, db_session, sample_group, sample_devices):
        """Test updating group device membership"""
        # Change to use all devices
        device_ids = [device.id for device in sample_devices]

        updated = update_group(
            db_session,
            sample_group.id,
            device_ids=device_ids
        )

        assert updated is not None

        # Verify devices were updated
        devices = get_group_devices(db_session, sample_group.id)
        assert len(devices) == 3

    def test_update_group_remove_all_devices(self, db_session, sample_group):
        """Test removing all devices from group"""
        updated = update_group(
            db_session,
            sample_group.id,
            device_ids=[]
        )

        assert updated is not None

        # Verify no devices remain
        devices = get_group_devices(db_session, sample_group.id)
        assert len(devices) == 0

    def test_update_group_not_found(self, db_session):
        """Test updating non-existent group"""
        fake_id = uuid.uuid4()
        result = update_group(db_session, fake_id, name="New Name")
        assert result is None

    def test_update_group_duplicate_name_fails(self, db_session, sample_group):
        """Test that updating to duplicate name fails"""
        create_group(db_session, name="Other Group")

        with pytest.raises(ValueError, match="Group with name .* already exists"):
            update_group(db_session, sample_group.id, name="Other Group")


class TestDeleteGroup:
    """Test delete_group function"""

    def test_delete_group_success(self, db_session, sample_group, sample_devices):
        """Test successful group deletion"""
        group_id = sample_group.id

        success = delete_group(db_session, group_id)

        assert success is True

        # Group should be deleted
        group = db_session.query(Group).filter(Group.id == group_id).first()
        assert group is None

        # Device associations should be deleted
        associations = db_session.query(DeviceGroup).filter(
            DeviceGroup.group_id == group_id
        ).all()
        assert len(associations) == 0

        # Devices should still exist
        devices = db_session.query(Device).filter(
            Device.id.in_([d.id for d in sample_devices])
        ).all()
        assert len(devices) == 3

    def test_delete_group_not_found(self, db_session):
        """Test deleting non-existent group"""
        fake_id = uuid.uuid4()
        success = delete_group(db_session, fake_id)
        assert success is False


class TestListGroups:
    """Test list_groups function"""

    def test_list_all_groups(self, db_session):
        """Test listing all groups"""
        # Create multiple groups
        for i in range(3):
            group = Group(
                id=uuid.uuid4(),
                name=f"Group {i}",
                description=f"Description {i}"
            )
            db_session.add(group)
        db_session.commit()

        groups = list_groups(db_session)
        assert len(groups) == 3

    def test_list_groups_empty(self, db_session):
        """Test listing groups when none exist"""
        groups = list_groups(db_session)
        assert len(groups) == 0

    def test_list_groups_ordered_by_name(self, db_session):
        """Test that groups are ordered by name"""
        names = ["Zebra Group", "Alpha Group", "Beta Group"]
        for name in names:
            group = Group(id=uuid.uuid4(), name=name)
            db_session.add(group)
        db_session.commit()

        groups = list_groups(db_session)
        assert groups[0].name == "Alpha Group"
        assert groups[1].name == "Beta Group"
        assert groups[2].name == "Zebra Group"


class TestGetGroupById:
    """Test get_group_by_id function"""

    def test_get_existing_group(self, db_session, sample_group):
        """Test getting an existing group"""
        group = get_group_by_id(db_session, sample_group.id)
        assert group is not None
        assert group.id == sample_group.id
        assert group.name == sample_group.name

    def test_get_non_existent_group(self, db_session):
        """Test getting a non-existent group"""
        fake_id = uuid.uuid4()
        group = get_group_by_id(db_session, fake_id)
        assert group is None


class TestGetGroupDevices:
    """Test get_group_devices function"""

    def test_get_devices_from_group(self, db_session, sample_group, sample_devices):
        """Test getting devices from a group"""
        devices = get_group_devices(db_session, sample_group.id)

        assert len(devices) == 2
        device_names = [d.name for d in devices]
        assert "Test Device 1" in device_names
        assert "Test Device 2" in device_names

    def test_get_devices_from_empty_group(self, db_session):
        """Test getting devices from group with no devices"""
        group = create_group(db_session, name="Empty Group")
        devices = get_group_devices(db_session, group.id)
        assert len(devices) == 0


class TestGetGroupAlertSummary:
    """Test get_group_alert_summary function"""

    def test_alert_summary_all_normal(self, db_session, sample_group, sample_devices):
        """Test alert summary when all devices are normal"""
        # Add normal readings for all devices in group
        for device in sample_devices[:2]:
            reading = Reading(
                timestamp=datetime.utcnow(),
                device_id=device.id,
                value=20.0  # Within normal range
            )
            db_session.add(reading)
        db_session.commit()

        summary = get_group_alert_summary(db_session, sample_group.id)

        assert summary.normal == 2
        assert summary.warning == 0
        assert summary.critical == 0

    def test_alert_summary_mixed_statuses(self, db_session, sample_group, sample_devices):
        """Test alert summary with mixed device statuses"""
        # Add readings with different statuses
        readings = [
            Reading(timestamp=datetime.utcnow(), device_id=sample_devices[0].id, value=20.0),  # normal
            Reading(timestamp=datetime.utcnow(), device_id=sample_devices[1].id, value=35.0),  # warning
        ]
        for reading in readings:
            db_session.add(reading)
        db_session.commit()

        summary = get_group_alert_summary(db_session, sample_group.id)

        assert summary.normal == 1
        assert summary.warning == 1
        assert summary.critical == 0

    def test_alert_summary_no_readings(self, db_session, sample_group):
        """Test alert summary when devices have no readings"""
        summary = get_group_alert_summary(db_session, sample_group.id)

        # Devices without readings are considered normal
        assert summary.normal == 2
        assert summary.warning == 0
        assert summary.critical == 0


class TestGetGroupReadings:
    """Test get_group_readings function"""

    def test_get_readings_from_multiple_devices(self, db_session, sample_group, sample_devices):
        """Test getting readings from multiple devices in group"""
        # Add readings for each device
        base_time = datetime.utcnow()
        for i, device in enumerate(sample_devices[:2]):
            for j in range(3):
                reading = Reading(
                    timestamp=base_time - timedelta(minutes=j),
                    device_id=device.id,
                    value=20.0 + i + j
                )
                db_session.add(reading)
        db_session.commit()

        readings = get_group_readings(db_session, sample_group.id)

        assert len(readings) == 6  # 3 readings × 2 devices

        # Verify readings have device info
        assert all(r.device_name is not None for r in readings)
        assert all(r.unit == "°C" for r in readings)

    def test_get_readings_with_time_range(self, db_session, sample_group, sample_devices):
        """Test getting readings within time range"""
        base_time = datetime.utcnow()

        # Add readings at different times
        for device in sample_devices[:2]:
            reading1 = Reading(
                timestamp=base_time - timedelta(hours=2),
                device_id=device.id,
                value=20.0
            )
            reading2 = Reading(
                timestamp=base_time - timedelta(hours=1),
                device_id=device.id,
                value=25.0
            )
            db_session.add_all([reading1, reading2])
        db_session.commit()

        # Get readings from last 1.5 hours
        start_time = base_time - timedelta(hours=1.5)
        readings = get_group_readings(
            db_session,
            sample_group.id,
            start_time=start_time
        )

        assert len(readings) == 2  # Only recent readings

    def test_get_readings_with_limit(self, db_session, sample_group, sample_devices):
        """Test getting limited number of readings"""
        # Add many readings
        base_time = datetime.utcnow()
        for device in sample_devices[:2]:
            for i in range(10):
                reading = Reading(
                    timestamp=base_time - timedelta(minutes=i),
                    device_id=device.id,
                    value=20.0 + i
                )
                db_session.add(reading)
        db_session.commit()

        readings = get_group_readings(db_session, sample_group.id, limit=5)

        assert len(readings) == 5

    def test_get_readings_empty_group(self, db_session):
        """Test getting readings from group with no devices"""
        group = create_group(db_session, name="Empty Group")
        readings = get_group_readings(db_session, group.id)
        assert len(readings) == 0


class TestAddDeviceToGroup:
    """Test add_device_to_group function"""

    def test_add_device_success(self, db_session, sample_group, sample_devices):
        """Test successfully adding device to group"""
        # Add third device (not currently in group)
        success = add_device_to_group(
            db_session,
            sample_group.id,
            sample_devices[2].id
        )

        assert success is True

        # Verify device was added
        devices = get_group_devices(db_session, sample_group.id)
        assert len(devices) == 3

    def test_add_device_already_in_group(self, db_session, sample_group, sample_devices):
        """Test adding device that's already in group"""
        # Try to add device that's already in group
        success = add_device_to_group(
            db_session,
            sample_group.id,
            sample_devices[0].id
        )

        assert success is False  # Already in group

    def test_add_device_group_not_found(self, db_session, sample_devices):
        """Test adding device to non-existent group"""
        fake_group_id = uuid.uuid4()

        with pytest.raises(ValueError, match="Group with ID .* not found"):
            add_device_to_group(
                db_session,
                fake_group_id,
                sample_devices[0].id
            )

    def test_add_device_device_not_found(self, db_session, sample_group):
        """Test adding non-existent device to group"""
        fake_device_id = uuid.uuid4()

        with pytest.raises(ValueError, match="Device with ID .* not found"):
            add_device_to_group(
                db_session,
                sample_group.id,
                fake_device_id
            )


class TestRemoveDeviceFromGroup:
    """Test remove_device_from_group function"""

    def test_remove_device_success(self, db_session, sample_group, sample_devices):
        """Test successfully removing device from group"""
        success = remove_device_from_group(
            db_session,
            sample_group.id,
            sample_devices[0].id
        )

        assert success is True

        # Verify device was removed
        devices = get_group_devices(db_session, sample_group.id)
        assert len(devices) == 1

    def test_remove_device_not_in_group(self, db_session, sample_group, sample_devices):
        """Test removing device that's not in group"""
        # Try to remove device that's not in group
        success = remove_device_from_group(
            db_session,
            sample_group.id,
            sample_devices[2].id
        )

        assert success is False  # Not in group
