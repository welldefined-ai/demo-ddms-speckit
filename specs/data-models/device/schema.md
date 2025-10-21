# Device

## Purpose

Stores Modbus TCP device configuration including connection parameters, threshold settings, and monitoring status for industrial device monitoring.

## Schema

### Entity: Device

Represents a Modbus TCP device with complete configuration.

**Table**: `devices`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique device identifier |
| `name` | VARCHAR(100) | UNIQUE, NOT NULL | Unique device name |
| `modbus_ip` | VARCHAR(45) | NOT NULL | Modbus TCP IP address (IPv4 or IPv6) |
| `modbus_port` | INTEGER | NOT NULL, DEFAULT 502 | Modbus TCP port number |
| `modbus_slave_id` | INTEGER | NOT NULL | Modbus slave ID (1-247) |
| `modbus_register` | INTEGER | NOT NULL | Starting register address to read |
| `modbus_register_count` | INTEGER | NOT NULL, DEFAULT 1 | Number of consecutive registers to read |
| `unit` | VARCHAR(20) | NULL | Measurement unit (e.g., °C, kPa, rpm) |
| `sampling_interval` | INTEGER | NOT NULL | Data collection interval in seconds (1-3600) |
| `threshold_warning_lower` | FLOAT | NULL | Lower warning threshold |
| `threshold_warning_upper` | FLOAT | NULL | Upper warning threshold |
| `threshold_critical_lower` | FLOAT | NULL | Lower critical threshold |
| `threshold_critical_upper` | FLOAT | NULL | Upper critical threshold |
| `retention_days` | INTEGER | NOT NULL, DEFAULT 90 | Data retention period in days |
| `status` | ENUM('ONLINE', 'OFFLINE', 'ERROR') | NOT NULL, DEFAULT 'OFFLINE' | Current connection status |
| `last_reading_at` | TIMESTAMP WITH TIME ZONE | NULL | Timestamp of last successful reading |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Device creation timestamp |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Last modification timestamp |

**Indexes**:
- `ix_devices_name` ON `name` (for device lookups by name)

**Relationships**:
```typescript
Device {
  hasMany: [Reading, DeviceGroup]
  belongsTo: []
}
```

## Validation Rules

### Rule: Device Name Uniqueness

- **MUST** be unique across all devices
- **MUST NOT** exceed 100 characters
- **MUST** be provided (NOT NULL)

### Rule: Modbus TCP Configuration

- `modbus_ip` **MUST** be valid IPv4 or IPv6 address format
- `modbus_port` **MUST** be valid port number (1-65535), defaults to 502
- `modbus_slave_id` **MUST** be in range 1-247 (Modbus protocol limit)
- `modbus_register` **MUST** be valid register address (0-65535)
- `modbus_register_count` **MUST** be positive integer, defaults to 1

### Rule: Sampling Interval

- **MUST** be between 1 and 3600 seconds (1 second to 1 hour)
- **MUST** be positive integer
- Lower intervals generate more data but higher polling load

### Rule: Threshold Configuration

- All threshold fields are optional (NULL allowed)
- When configured, thresholds used for status calculation:
  - Critical thresholds take precedence over warning thresholds
  - `threshold_critical_lower` < `threshold_warning_lower` < normal range < `threshold_warning_upper` < `threshold_critical_upper`

### Rule: Data Retention

- `retention_days` **MUST** be positive integer
- Defaults to 90 days
- Automatic cleanup deletes readings older than retention period
- **MUST** be greater than 0

### Rule: Device Status

- **MUST** be one of: ONLINE, OFFLINE, ERROR
- Defaults to OFFLINE on device creation
- ONLINE: Device responding to Modbus requests
- OFFLINE: Device not responding (timeout, network error)
- ERROR: Device responding with Modbus protocol errors
- Updated automatically by data collector

### Rule: Last Reading Timestamp

- NULL when device never successfully polled
- Updated to current timestamp on successful reading collection
- Used to track device connectivity and data freshness

### Rule: Cascade Deletion

- When device deleted, all associated readings deleted (foreign key cascade)
- When device deleted, all device_groups associations deleted (foreign key cascade)

## Related Specs

- **Capabilities**: `capabilities/device-monitoring/spec.md`, `capabilities/real-time-data-collection/spec.md`
- **APIs**: `api/device/spec.md`
- **Data Models**: `data-models/reading/schema.md`, `data-models/device-group/schema.md`
