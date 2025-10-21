# Group

## Purpose

Stores logical groupings of devices for collective monitoring, dashboard organization, and group-level alerting and analytics.

## Schema

### Entity: Group

Represents a logical collection of devices.

**Table**: `groups`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique group identifier |
| `name` | VARCHAR(100) | UNIQUE, NOT NULL | Unique group name |
| `description` | VARCHAR(500) | NULL | Optional group description |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Group creation timestamp |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Last modification timestamp |

**Indexes**:
- `ix_groups_name` ON `name` (for group lookups by name)

**Relationships**:
```typescript
Group {
  hasMany: [DeviceGroup]
  belongsTo: []
}
```

## Validation Rules

### Rule: Group Name Uniqueness

- **MUST** be unique across all groups
- **MUST NOT** exceed 100 characters
- **MUST** be provided (NOT NULL)

### Rule: Description

- Optional field (NULL allowed)
- **MUST NOT** exceed 500 characters if provided
- Used for documenting group purpose or membership criteria

### Rule: Timestamp Management

- `created_at` automatically set on record creation
- `updated_at` automatically updated on any field modification

### Rule: Many-to-Many Device Relationship

- Groups associated with devices through device_groups junction table
- One group can contain multiple devices
- One device can belong to multiple groups
- No direct foreign key in this table (see device_groups)

### Rule: Cascade Deletion

- When group deleted, all device_groups associations deleted (foreign key cascade)
- Devices remain in system and continue monitoring
- No device or reading data deleted

## Related Specs

- **Capabilities**: `capabilities/device-grouping/spec.md`
- **APIs**: `api/group/spec.md`
- **Data Models**: `data-models/device-group/schema.md`, `data-models/device/schema.md`
