# DeviceGroup

## Purpose

Junction table implementing many-to-many relationship between devices and groups, allowing devices to belong to multiple groups and groups to contain multiple devices.

## Schema

### Entity: DeviceGroup

Represents the association between a device and a group.

**Table**: `device_groups`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `device_id` | UUID | PRIMARY KEY, FOREIGN KEY → devices(id) | Associated device |
| `group_id` | UUID | PRIMARY KEY, FOREIGN KEY → groups(id) | Associated group |
| `added_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Timestamp when device added to group |

**Primary Key**: Composite `(device_id, group_id)`

**Unique Constraints**:
- `uq_device_group` ON `(device_id, group_id)` (prevent duplicate associations)

**Foreign Keys**:
- `device_id` REFERENCES `devices(id)` ON DELETE CASCADE
- `group_id` REFERENCES `groups(id)` ON DELETE CASCADE

**Relationships**:
```typescript
DeviceGroup {
  hasMany: []
  belongsTo: [Device, Group]
}
```

## Validation Rules

### Rule: Composite Primary Key

- Combination of (device_id, group_id) **MUST** be unique
- Ensures one device can only be added to same group once
- Prevents duplicate associations

### Rule: Device Reference

- **MUST** reference valid device_id from devices table
- Foreign key constraint ensures referential integrity
- ON DELETE CASCADE: When device deleted, association automatically removed

### Rule: Group Reference

- **MUST** reference valid group_id from groups table
- Foreign key constraint ensures referential integrity
- ON DELETE CASCADE: When group deleted, association automatically removed

### Rule: Added Timestamp

- `added_at` automatically set when association created
- Records when device was added to group
- Useful for auditing and displaying membership history

### Rule: Cascade Behavior

- Deleting device removes all group memberships for that device
- Deleting group removes all device associations for that group
- No orphaned associations possible due to CASCADE constraints

## Query Patterns

### Get All Devices in Group

```sql
SELECT d.*
FROM devices d
JOIN device_groups dg ON d.id = dg.device_id
WHERE dg.group_id = {group_id}
```

### Get All Groups for Device

```sql
SELECT g.*
FROM groups g
JOIN device_groups dg ON g.id = dg.group_id
WHERE dg.device_id = {device_id}
```

### Check Device in Group

```sql
SELECT EXISTS(
  SELECT 1 FROM device_groups
  WHERE device_id = {device_id} AND group_id = {group_id}
)
```

## Related Specs

- **Capabilities**: `capabilities/device-grouping/spec.md`
- **APIs**: `api/group/spec.md`
- **Data Models**: `data-models/device/schema.md`, `data-models/group/schema.md`
