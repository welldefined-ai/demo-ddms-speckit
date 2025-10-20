# Configuration

## Purpose

Stores system-wide configuration settings as a singleton record, including default data retention, backup settings, and system identification.

## Schema

### Entity: Configuration

Represents global system configuration (single row only).

**Table**: `configuration`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique configuration identifier (single row) |
| `system_name` | VARCHAR(100) | NOT NULL, DEFAULT 'DDMS - Device Data Monitoring System' | System display name |
| `data_retention_days_default` | INTEGER | NOT NULL, DEFAULT 90, CHECK > 0 | Default retention period for new devices |
| `backup_enabled` | BOOLEAN | NOT NULL, DEFAULT TRUE | Enable/disable automatic backups |
| `backup_schedule` | VARCHAR(100) | NOT NULL, DEFAULT '0 2 * * *' | Cron expression for backup schedule |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Configuration creation timestamp |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Last modification timestamp |

**Check Constraints**:
- `data_retention_days_default > 0` (retention must be positive)

**Relationships**:
```typescript
Configuration {
  hasMany: []
  belongsTo: []
}
```

## Validation Rules

### Rule: Singleton Pattern

- **MUST** contain exactly one row (enforced by application logic)
- Application creates single configuration record on first initialization
- Updates modify existing row rather than creating new rows
- ID typically hardcoded or well-known value

### Rule: System Name

- **MUST NOT** exceed 100 characters
- Defaults to "DDMS - Device Data Monitoring System"
- Used in UI headers, notifications, emails

### Rule: Default Data Retention

- **MUST** be positive integer (CHECK constraint)
- **MUST NOT** be zero or negative
- Defaults to 90 days
- Applied to new devices if device-specific retention not specified

### Rule: Backup Configuration

- `backup_enabled` boolean flag to toggle backups
- `backup_schedule` uses cron expression syntax
- Default schedule: "0 2 * * *" (daily at 2:00 AM)
- Application reads schedule to trigger backup jobs

### Rule: Timestamp Management

- `created_at` set once on initial configuration creation
- `updated_at` automatically updated on any field modification

## Default Values

**Initial Configuration Row**:
```json
{
  "id": "<generated-uuid>",
  "system_name": "DDMS - Device Data Monitoring System",
  "data_retention_days_default": 90,
  "backup_enabled": true,
  "backup_schedule": "0 2 * * *",
  "created_at": "<current-timestamp>",
  "updated_at": "<current-timestamp>"
}
```

## Usage Patterns

### Get System Configuration

```python
# Application retrieves single configuration row
config = session.query(Configuration).first()
```

### Update Configuration

```python
# Update existing configuration
config = session.query(Configuration).first()
config.data_retention_days_default = 60
config.backup_enabled = False
session.commit()
# updated_at automatically set
```

### Use in Device Creation

```python
# Apply default retention when creating device
config = session.query(Configuration).first()
new_device = Device(
    name="...",
    retention_days=config.data_retention_days_default
)
```

## Related Specs

- **Capabilities**: `capabilities/device-monitoring/spec.md`
- **Architecture**: `architecture/ddms-system/spec.md`
