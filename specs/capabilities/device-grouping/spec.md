# Device Grouping

## Purpose

Provides logical organization of devices into groups for collective monitoring, dashboard aggregation, and group-level alert summaries.

## Requirements

### Requirement: Group Creation and Management

The system SHALL allow authorized users to create and manage logical device groups.

#### Scenario: Create new group

- **WHEN** admin or owner creates group with name and optional description
- **THEN** system validates name is unique
- **AND** system creates group with generated UUID
- **AND** system returns group details with created_at timestamp
- **AND** group initially contains no devices

#### Scenario: Duplicate group name validation

- **WHEN** user attempts to create group with existing name
- **THEN** system returns 400 Bad Request
- **AND** system provides validation error indicating duplicate name

#### Scenario: Update group metadata

- **WHEN** user updates group name or description
- **THEN** system validates new name uniqueness (if changed)
- **AND** system updates group record
- **AND** system updates updated_at timestamp
- **AND** device memberships remain unchanged

#### Scenario: Delete group

- **WHEN** admin deletes group
- **THEN** system removes group record from groups table
- **AND** system removes all device-group associations (cascade)
- **AND** devices remain in system and continue monitoring
- **AND** no device or reading data is deleted

### Requirement: Device-Group Association

The system SHALL support many-to-many relationships between devices and groups.

#### Scenario: Add device to group

- **WHEN** user adds device to group
- **THEN** system creates record in device_groups table
- **AND** system validates both device and group exist
- **AND** system records added_at timestamp
- **AND** system enforces unique constraint (device_id, group_id)

#### Scenario: Add device to multiple groups

- **WHEN** user adds same device to multiple groups
- **THEN** system allows device membership in multiple groups
- **AND** device appears in all associated group dashboards

#### Scenario: Prevent duplicate association

- **WHEN** user attempts to add device already in group
- **THEN** system returns 400 Bad Request or ignores duplicate
- **AND** unique constraint prevents duplicate entries

#### Scenario: Remove device from group

- **WHEN** user removes device from group
- **THEN** system deletes device_groups record
- **AND** device remains in system and other groups
- **AND** group continues to exist with remaining devices

### Requirement: Group Device Listing

The system SHALL provide list of all devices belonging to a group with current status.

#### Scenario: Get group with devices

- **WHEN** user requests group details by group_id
- **THEN** system returns group metadata (name, description)
- **AND** system includes array of associated devices
- **AND** each device includes id, name, status, last_reading_at
- **AND** device list ordered by name or added_at

#### Scenario: Empty group

- **WHEN** user requests group with no devices
- **THEN** system returns group metadata
- **AND** devices array is empty
- **AND** group is valid but contains no members

### Requirement: Group Alert Summary

The system SHALL calculate aggregated alert status across all devices in a group.

#### Scenario: Calculate group alert counts

- **WHEN** user requests group alerts
- **THEN** system queries latest reading for each device in group
- **AND** system calculates status for each device (normal/warning/critical)
- **AND** system counts devices in each status category
- **AND** system returns {normal_count, warning_count, critical_count}

#### Scenario: Group with mixed device statuses

- **WHEN** group contains devices in different alert states
- **THEN** system accurately counts each category
- **AND** total count equals number of devices in group

#### Scenario: Group with offline devices

- **WHEN** group contains devices with status OFFLINE
- **THEN** system includes offline devices in counts
- **AND** offline devices may have null or stale readings

### Requirement: Group Historical Data Retrieval

The system SHALL aggregate historical readings from all devices within a group.

#### Scenario: Query group readings with time range

- **WHEN** user requests group readings with start_time and end_time
- **THEN** system queries readings for all devices in group
- **AND** system filters by time range across all devices
- **AND** system returns readings with device_id and device_name
- **AND** response allows correlation of readings to devices

#### Scenario: Aggregated group data

- **WHEN** user requests group readings with aggregation (1min, 1hour, 1day)
- **THEN** system calculates aggregates per device
- **AND** system returns aggregated data grouped by device
- **AND** allows comparison of devices within group over time

### Requirement: Group Listing

The system SHALL provide list of all groups with metadata.

#### Scenario: List all groups

- **WHEN** user requests groups list
- **THEN** system returns all groups with id, name, description
- **AND** system includes created_at and updated_at timestamps
- **AND** response may include device count per group

### Requirement: Group Dashboard Support

The system SHALL support group-level monitoring dashboards showing all group devices.

#### Scenario: Group dashboard data

- **WHEN** frontend requests group dashboard data
- **THEN** system provides group metadata
- **AND** system provides list of devices with latest readings
- **AND** system provides alert summary (normal/warning/critical counts)
- **AND** frontend displays unified view of group health

### Requirement: Cascade Deletion Behavior

The system SHALL handle cascade deletions appropriately to maintain data integrity.

#### Scenario: Delete device in groups

- **WHEN** device is deleted from system
- **THEN** system automatically removes device from all groups (foreign key cascade)
- **AND** groups continue to exist with remaining devices
- **AND** no manual cleanup required

#### Scenario: Delete group

- **WHEN** group is deleted
- **THEN** system removes all device-group associations for that group
- **AND** devices remain in system and other groups
- **AND** device readings and configuration unaffected

## Related Specs

- **Data Models**: `data-models/group/schema.md`, `data-models/device-group/schema.md`, `data-models/device/schema.md`
- **APIs**: `api/group/spec.md`
- **Capabilities**: `capabilities/device-monitoring/spec.md`, `capabilities/historical-data-analytics/spec.md`
- **Architecture**: `architecture/ddms-system/spec.md`
