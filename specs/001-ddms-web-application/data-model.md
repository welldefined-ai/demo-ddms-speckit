# Phase 1: Data Model Design

**Feature**: DDMS Web Application  
**Branch**: 001-ddms-web-application  
**Date**: 2025-10-10

## Overview

This document defines the database schema, entity relationships, validation rules, and state transitions for the DDMS system. All entities are implemented as SQLAlchemy models with TimescaleDB hypertable optimization for time-series data.

---

## Entity Relationship Diagram

```
┌─────────────┐
│    User     │
└──────┬──────┘
       │
       │ (created_by)
       │
       ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Device    │────▶│   Reading    │     │ Threshold   │
│             │     │ (hypertable) │     │ (embedded)  │
└──────┬──────┘     └──────────────┘     └─────────────┘
       │
       │ (many-to-many)
       │
       ▼
┌─────────────┐
│    Group    │
└─────────────┘

┌──────────────────┐
│  Configuration   │
│  (singleton)     │
└──────────────────┘
```

---

## Entity Definitions

### 1. User

**Description**: Represents a system user with authentication credentials and role-based permissions.

**Table**: `users`

**Fields**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Auto-generated unique identifier |
| `username` | VARCHAR(50) | UNIQUE, NOT NULL | Login username (3-50 chars) |
| `password_hash` | VARCHAR(255) | NOT NULL | bcrypt hash with salt |
| `role` | ENUM('owner', 'admin', 'read_only') | NOT NULL, DEFAULT 'read_only' | Access control role |
| `language_preference` | ENUM('en-US', 'zh-CN') | NOT NULL, DEFAULT 'en-US' | UI language (FR-045) |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Account creation time |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Last modification time |

**Validation Rules**:
- Username: 3-50 characters, alphanumeric + underscore/hyphen only, case-insensitive uniqueness
- Password: Minimum 8 characters, must contain uppercase + lowercase + digit (enforced at API layer)
- Role: Exactly one owner account must exist at all times (enforced at service layer)
- Language: Must be one of supported languages (extendable via enum migration)

**Indexes**:
- PRIMARY KEY on `id`
- UNIQUE INDEX on `username` (case-insensitive: `lower(username)`)

**State Transitions**: None (no status field, users are created/deleted atomically)

**Related Entities**:
- One-to-many with Device (created_by)
- One-to-many with Group (created_by)

---

### 2. Device

**Description**: Represents a Modbus monitoring device with connection parameters and configuration settings.

**Table**: `devices`

**Fields**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Auto-generated unique identifier |
| `name` | VARCHAR(100) | UNIQUE, NOT NULL | User-assigned device name (clarification: unique across system) |
| `description` | TEXT | NULL | Optional device description |
| `connection_type` | ENUM('modbus_tcp', 'modbus_rtu') | NOT NULL, DEFAULT 'modbus_tcp' | Protocol type (FR-064, FR-065) |
| `ip_address` | VARCHAR(45) | NULL | IPv4/IPv6 address (required for TCP) |
| `port` | INTEGER | NULL, DEFAULT 502 | TCP port (1-65535, required for TCP) |
| `register_address` | INTEGER | NOT NULL | Modbus register address (0-65535) |
| `data_type` | ENUM('INT16', 'UINT16', 'INT32', 'UINT32', 'FLOAT32') | NOT NULL | Register data type (FR-067) |
| `unit` | VARCHAR(20) | NOT NULL | Reading unit (°C, bar, RPM, %, etc. per FR-025) |
| `sampling_interval` | INTEGER | NOT NULL, DEFAULT 10 | Data collection frequency in seconds (clarification: default 10s) |
| `retention_days` | INTEGER | NOT NULL, DEFAULT 90 | Data retention period (clarification: default 90 days) |
| `warning_lower` | DECIMAL(12,4) | NULL | Lower warning threshold |
| `warning_upper` | DECIMAL(12,4) | NULL | Upper warning threshold |
| `critical_lower` | DECIMAL(12,4) | NULL | Lower critical threshold |
| `critical_upper` | DECIMAL(12,4) | NULL | Upper critical threshold |
| `hysteresis` | DECIMAL(12,4) | NOT NULL, DEFAULT 0.0 | Threshold hysteresis value (FR-030) |
| `status` | ENUM('online', 'offline', 'error') | NOT NULL, DEFAULT 'offline' | Current connection status |
| `last_reading_at` | TIMESTAMP WITH TIME ZONE | NULL | Timestamp of last successful reading (FR-033) |
| `last_error` | TEXT | NULL | Last communication error message |
| `error_count` | INTEGER | NOT NULL, DEFAULT 0 | Consecutive connection failures (resets on success) |
| `created_by` | UUID | NOT NULL, FOREIGN KEY(users.id) | User who created device |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Device creation time |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Last configuration change |

**Validation Rules**:
- Name: 3-100 characters, must be unique (case-insensitive), no leading/trailing whitespace
- IP address: Valid IPv4 or IPv6 format (validated via `ipaddress` module)
- Port: 1-65535 for TCP, NULL for RTU
- Sampling interval: 5-3600 seconds (5s min to avoid overwhelming devices, 1h max for "real-time" monitoring)
- Retention days: 1-3650 days (max ~10 years)
- Thresholds: `warning_lower <= warning_upper`, `critical_lower <= critical_upper`, `critical_lower <= warning_lower`, `warning_upper <= critical_upper`
- Hysteresis: >= 0, typically 1-10% of threshold range

**Indexes**:
- PRIMARY KEY on `id`
- UNIQUE INDEX on `name` (case-insensitive: `lower(name)`)
- INDEX on `status` (for dashboard queries filtering online devices)
- INDEX on `created_by` (for audit queries)

**State Transitions**:
```
       ┌────────────┐
       │  offline   │ (initial state)
       └─────┬──────┘
             │
             │ (successful connection)
             ▼
       ┌────────────┐
       │   online   │
       └─────┬──────┘
             │
             │ (3 consecutive failures)
             ▼
       ┌────────────┐
       │   error    │
       └─────┬──────┘
             │
             │ (successful reconnection)
             └──────────▶ (back to online)
```

**Related Entities**:
- Many-to-one with User (created_by)
- One-to-many with Reading (readings)
- Many-to-many with Group (via device_groups association table)

---

### 3. Reading

**Description**: Time-series data point from a device. Stored in TimescaleDB hypertable for efficient time-based queries.

**Table**: `readings` (TimescaleDB hypertable partitioned by `timestamp`)

**Fields**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGSERIAL | PRIMARY KEY | Auto-incrementing identifier (partitioned) |
| `device_id` | UUID | NOT NULL, FOREIGN KEY(devices.id) | Device that produced this reading |
| `timestamp` | TIMESTAMP WITH TIME ZONE | NOT NULL | Reading timestamp (UTC, partition key) |
| `value` | DECIMAL(12,4) | NOT NULL | Measured value |
| `quality` | ENUM('good', 'bad', 'uncertain') | NOT NULL, DEFAULT 'good' | Data quality indicator (FR-253) |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Insert time (for debugging) |

**Validation Rules**:
- Timestamp: Cannot be in future (allow max 60s clock skew), cannot be older than device retention period
- Value: Must be finite number (no NaN, Infinity)
- Quality: 'good' for successful reads, 'bad' for error states, 'uncertain' for questionable values

**Indexes**:
- PRIMARY KEY on `(timestamp, id)` (composite for TimescaleDB)
- INDEX on `(device_id, timestamp DESC)` (for device-specific time-range queries)
- INDEX on `timestamp DESC` (for global recent readings queries)

**TimescaleDB Configuration**:
- Hypertable chunk interval: 1 day (balances query performance and partition management)
- Compression: Enabled for chunks older than 7 days (90-95% size reduction)
- Continuous aggregates:
  - `readings_1min`: 1-minute averages (MIN, MAX, AVG, COUNT)
  - `readings_1hour`: 1-hour aggregates
  - `readings_1day`: Daily aggregates
- Retention policy: Automatic deletion of data older than `device.retention_days`

**Related Entities**:
- Many-to-one with Device (device_id)

---

### 4. Group

**Description**: Logical collection of devices for organized monitoring and reporting.

**Table**: `groups`

**Fields**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Auto-generated unique identifier |
| `name` | VARCHAR(100) | UNIQUE, NOT NULL | Group name (user-assigned) |
| `description` | TEXT | NULL | Optional group description |
| `created_by` | UUID | NOT NULL, FOREIGN KEY(users.id) | User who created group |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Group creation time |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Last modification time |

**Validation Rules**:
- Name: 3-100 characters, unique (case-insensitive), no leading/trailing whitespace
- Must contain at least one device to be valid (enforced at service layer for display, but allowed to be empty briefly during creation)

**Indexes**:
- PRIMARY KEY on `id`
- UNIQUE INDEX on `name` (case-insensitive: `lower(name)`)
- INDEX on `created_by`

**Related Entities**:
- Many-to-one with User (created_by)
- Many-to-many with Device (via device_groups)

---

### 5. DeviceGroup (Association Table)

**Description**: Many-to-many relationship between devices and groups.

**Table**: `device_groups`

**Fields**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `device_id` | UUID | NOT NULL, FOREIGN KEY(devices.id) ON DELETE CASCADE | Device in group |
| `group_id` | UUID | NOT NULL, FOREIGN KEY(groups.id) ON DELETE CASCADE | Group containing device |
| `added_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | When device was added to group |

**Validation Rules**:
- Composite uniqueness: (device_id, group_id) pair must be unique

**Indexes**:
- PRIMARY KEY on `(device_id, group_id)`
- INDEX on `group_id` (for queries fetching all devices in a group)

---

### 6. Configuration

**Description**: System-wide configuration settings (singleton entity).

**Table**: `configuration`

**Fields**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, CHECK(id = 1) | Always 1 (singleton) |
| `backup_schedule_cron` | VARCHAR(50) | NOT NULL, DEFAULT '0 2 * * *' | Cron expression for automated backups (FR-058) |
| `default_sampling_interval` | INTEGER | NOT NULL, DEFAULT 10 | Default sampling interval in seconds (clarification) |
| `default_retention_days` | INTEGER | NOT NULL, DEFAULT 90 | Default retention period (clarification) |
| `session_timeout_minutes` | INTEGER | NOT NULL, DEFAULT 480 | Session timeout (8 hours default) |
| `max_login_attempts` | INTEGER | NOT NULL, DEFAULT 5 | Failed login threshold before rate limiting |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Last configuration change |

**Validation Rules**:
- Only one row allowed (enforced by CHECK constraint on `id = 1`)
- Backup schedule: Valid cron expression
- Sampling interval: 5-3600 seconds
- Retention days: 1-3650 days
- Session timeout: 5-1440 minutes (5 min - 24 hours)
- Max login attempts: 1-20

**Indexes**:
- PRIMARY KEY on `id`

**State Transitions**: None (singleton, only updated, never created/deleted)

---

## Schema Migration Strategy

**Tool**: Alembic (SQLAlchemy migration framework)

**Migration Files Location**: `backend/src/db/migrations/versions/`

**Initial Migration** (`001_initial_schema.py`):
- Create all tables
- Create TimescaleDB extension: `CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE`
- Convert `readings` table to hypertable: `SELECT create_hypertable('readings', 'timestamp', chunk_time_interval => INTERVAL '1 day')`
- Create all indexes
- Insert default owner user (username: `admin`, password: `changeme`, role: `owner`)
- Insert default configuration row

**Future Migrations**:
- Backward-compatible changes preferred (add columns with defaults, never drop columns)
- Data migrations must preserve existing readings (never delete historical data)
- Schema changes must maintain TimescaleDB hypertable integrity

---

## Data Validation Summary

All validation enforced at three layers:
1. **Database**: Constraints (NOT NULL, UNIQUE, CHECK, FOREIGN KEY)
2. **ORM**: SQLAlchemy model validators (`@validates` decorators)
3. **API**: Pydantic request schemas (FastAPI automatic validation)

Critical validations:
- Device name uniqueness (FR-025a: clarification)
- Threshold ordering (warning ≤ critical, lower ≤ upper)
- Sampling interval bounds (5-3600s)
- Retention period bounds (1-3650 days)
- Data quality on all readings
- Role enforcement (exactly one owner)

---

## Performance Optimizations

1. **TimescaleDB Hypertables**: Automatic time-based partitioning for `readings` table
2. **Compression**: 90-95% size reduction for data older than 7 days
3. **Continuous Aggregates**: Pre-computed rollups for fast dashboard queries
4. **Indexes**: Strategic indexes on query patterns (device_id + timestamp, status)
5. **Connection Pooling**: SQLAlchemy pooling (10-20 connections) for concurrent API requests
6. **Retention Automation**: TimescaleDB retention policy for automatic old data deletion

**Expected Performance** (per constitution Principle V):
- Single device query (24h): < 100ms (uses continuous aggregate + compression)
- Dashboard query (100 devices, current values): < 500ms (indexed on device status)
- Insert 1000 readings (10s batch): < 200ms (TimescaleDB optimized inserts)
- Historical export (1 week, 1 device): < 2s (60,480 readings, compressed chunks)

---

## Testing Strategy

**Unit Tests** (target: >=80% coverage per constitution):
- Model validators (test invalid data rejection)
- Threshold logic (warning/critical ordering)
- State transitions (device status changes)
- Constraint violations (unique names, singleton configuration)

**Integration Tests**:
- Database operations (CRUD for all entities)
- Foreign key cascades (delete device → delete readings)
- TimescaleDB hypertable queries (time-range filtering)
- Continuous aggregate accuracy (compare to raw data)

**Contract Tests**:
- SQLAlchemy model ↔ database schema alignment
- Alembic migrations (up/down reversibility)

All tests use Docker-based PostgreSQL + TimescaleDB container for isolation.

---

## Next Steps

With data model defined, Phase 1 continues with:
1. **contracts/**: OpenAPI specification for API endpoints
2. **quickstart.md**: Development setup guide
3. **Agent context update**: Add final technology stack to `.claude/` context

Data model aligns with all functional requirements (FR-001 through FR-072) and constitution principles (especially data reliability Principle I and performance Principle V).

