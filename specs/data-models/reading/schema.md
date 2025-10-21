# Reading

## Purpose

Stores time-series sensor readings from Modbus devices using TimescaleDB hypertable for efficient time-based queries and automatic data retention.

## Schema

### Entity: Reading

Represents a single sensor reading at a specific timestamp.

**Table**: `readings` (TimescaleDB hypertable partitioned by timestamp)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `timestamp` | TIMESTAMP WITH TIME ZONE | NOT NULL | Reading collection timestamp (partition key) |
| `device_id` | UUID | NOT NULL, FOREIGN KEY → devices(id) | Associated device |
| `value` | FLOAT | NOT NULL | Measured value from Modbus register |

**Primary Key**: Composite `(timestamp, device_id)` for TimescaleDB

**Indexes**:
- `idx_readings_device_timestamp` ON `(device_id, timestamp)` (composite index for efficient device-specific time queries)

**Foreign Keys**:
- `device_id` REFERENCES `devices(id)` ON DELETE CASCADE

**Relationships**:
```typescript
Reading {
  hasMany: []
  belongsTo: [Device]
}
```

**TimescaleDB Configuration**:
- Converted to hypertable with `create_hypertable('readings', 'timestamp')`
- Time-based partitioning (chunking) for efficient time-range queries
- Automatic chunk management by TimescaleDB
- Continuous aggregates for 1-minute, 1-hour, 1-day aggregations (migration 002)

## Validation Rules

### Rule: Timestamp Requirement

- **MUST** include timestamp for every reading
- **MUST** use timezone-aware timestamp (TIMESTAMP WITH TIME ZONE)
- Typically set to current server time during data collection
- Used as partition key for TimescaleDB hypertable

### Rule: Device Association

- **MUST** reference valid device_id from devices table
- Foreign key constraint ensures referential integrity
- ON DELETE CASCADE: When device deleted, all readings automatically deleted

### Rule: Value Storage

- **MUST** be valid floating-point number
- Represents raw value read from Modbus register
- No built-in range validation (handled by threshold logic)
- Precision depends on database FLOAT type (typically double precision)

### Rule: Composite Primary Key

- Combination of (timestamp, device_id) **MUST** be unique
- Allows one reading per device per timestamp
- Supports TimescaleDB hypertable requirements

### Rule: TimescaleDB Hypertable

- Table automatically partitioned into time-based chunks
- Chunks typically sized for 1-week or 1-month intervals
- Enables efficient time-range queries using chunk pruning
- Older chunks automatically compressed (if compression enabled)

### Rule: Data Retention

- Readings older than device.retention_days automatically deleted
- Retention policy applied per-device based on device configuration
- Cleanup job runs periodically (background task)

## TimescaleDB Features

### Continuous Aggregates

**1-Minute Aggregate** (readings_1min):
```sql
time_bucket('1 minute', timestamp) AS time_bucket,
device_id,
AVG(value) AS avg,
MIN(value) AS min,
MAX(value) AS max,
COUNT(*) AS count
```

**1-Hour Aggregate** (readings_1hour):
```sql
time_bucket('1 hour', timestamp) AS time_bucket,
device_id,
AVG(value) AS avg,
MIN(value) AS min,
MAX(value) AS max,
COUNT(*) AS count
```

**1-Day Aggregate** (readings_1day):
```sql
time_bucket('1 day', timestamp) AS time_bucket,
device_id,
AVG(value) AS avg,
MIN(value) AS min,
MAX(value) AS max,
COUNT(*) AS count
```

### Query Optimization

- Time-range queries use chunk exclusion
- Composite index (device_id, timestamp) accelerates device-specific queries
- Aggregates pre-computed and materialized for fast dashboard rendering

## Related Specs

- **Capabilities**: `capabilities/real-time-data-collection/spec.md`, `capabilities/historical-data-analytics/spec.md`
- **APIs**: `api/reading/spec.md`, `api/device/spec.md`
- **Data Models**: `data-models/device/schema.md`
- **Architecture**: `architecture/ddms-system/spec.md`
