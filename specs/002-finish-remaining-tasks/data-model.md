# Phase 1: Data Model Design

**Feature**: Complete DDMS System Polish and Production Readiness
**Branch**: 002-finish-remaining-tasks
**Date**: 2025-10-16

## Overview

This document defines the database schema extensions, new entities, and enhanced relationships for feature 002, building upon the foundation established in feature 001-ddms-web-application. This feature adds production-ready capabilities including system configuration management, automated database operations (retention, compression, backups), and device connection failure notifications.

All entities continue to be implemented as SQLAlchemy models with TimescaleDB hypertable optimization for time-series data. This feature introduces:
- **Enhancement** to existing Configuration entity for backup scheduling and Prometheus settings
- **New** BackupJob entity for tracking database backup history and success/failure states
- **New** ConnectionFailureNotification entity for persisting device connection alerts with acknowledgment workflow

These additions support automated operational workflows (FR-001 through FR-021) while maintaining data reliability, observability, and security principles from the project constitution.

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

┌──────────────────┐                     ┌──────────────────────────┐
│  Configuration   │◀────────────────────│      BackupJob           │
│  (singleton)     │   (one-to-many)     │  (backup history)        │
└──────────────────┘                     └──────────────────────────┘

┌─────────────┐                          ┌───────────────────────────────┐
│   Device    │◀─────────────────────────│ ConnectionFailureNotification │
│             │   (many-to-one)          │   (failure alerts)            │
└─────────────┘                          └─────────┬─────────────────────┘
                                                   │
                                                   │ (acknowledged_by)
                                                   ▼
                                         ┌─────────────┐
                                         │    User     │
                                         └─────────────┘
```

**Key Changes from Feature 001**:
- Configuration entity enhanced with backup and monitoring fields
- BackupJob entity added with one-to-many relationship to Configuration
- ConnectionFailureNotification entity added with many-to-one relationships to Device and User

---

## Entity Definitions

### 1. User
*(Unchanged from feature 001 - included for completeness)*

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
- One-to-many with ConnectionFailureNotification (acknowledged_by) - **NEW in feature 002**

---

### 2. Device
*(Unchanged from feature 001 - included for completeness)*

**Description**: Represents a Modbus monitoring device with connection parameters and configuration settings.

**Table**: `devices`

**Fields**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Auto-generated unique identifier |
| `name` | VARCHAR(100) | UNIQUE, NOT NULL | User-assigned device name (unique across system) |
| `description` | TEXT | NULL | Optional device description |
| `connection_type` | ENUM('modbus_tcp', 'modbus_rtu') | NOT NULL, DEFAULT 'modbus_tcp' | Protocol type (FR-064, FR-065) |
| `ip_address` | VARCHAR(45) | NULL | IPv4/IPv6 address (required for TCP) |
| `port` | INTEGER | NULL, DEFAULT 502 | TCP port (1-65535, required for TCP) |
| `register_address` | INTEGER | NOT NULL | Modbus register address (0-65535) |
| `data_type` | ENUM('INT16', 'UINT16', 'INT32', 'UINT32', 'FLOAT32') | NOT NULL | Register data type (FR-067) |
| `unit` | VARCHAR(20) | NOT NULL | Reading unit (°C, bar, RPM, %, etc. per FR-025) |
| `sampling_interval` | INTEGER | NOT NULL, DEFAULT 10 | Data collection frequency in seconds (default 10s) |
| `retention_days` | INTEGER | NOT NULL, DEFAULT 90 | Data retention period (default 90 days) |
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
- Error count: Triggers ConnectionFailureNotification when >= 3 (FR-017, FR-018) - **ENHANCED in feature 002**

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
             │ (successful connection, reset error_count=0)
             ▼
       ┌────────────┐
       │   online   │
       └─────┬──────┘
             │
             │ (3 consecutive failures, trigger notification)
             ▼
       ┌────────────┐
       │   error    │
       └─────┬──────┘
             │
             │ (successful reconnection, clear notification)
             └──────────▶ (back to online)
```

**Related Entities**:
- Many-to-one with User (created_by)
- One-to-many with Reading (readings)
- Many-to-many with Group (via device_groups association table)
- One-to-many with ConnectionFailureNotification (notifications) - **NEW in feature 002**

---

### 3. Reading
*(Unchanged from feature 001 - included for completeness)*

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
- Compression: Enabled for chunks older than 7 days (90-95% size reduction) - **ENFORCED by migration 004_compression_policy.py in feature 002**
- Continuous aggregates:
  - `readings_1min`: 1-minute averages (MIN, MAX, AVG, COUNT)
  - `readings_1hour`: 1-hour aggregates
  - `readings_1day`: Daily aggregates
- Retention policy: Automatic deletion of data older than `device.retention_days` - **ENFORCED by migration 003_retention_policy.py in feature 002**

**Related Entities**:
- Many-to-one with Device (device_id)

---

### 4. Group
*(Unchanged from feature 001 - included for completeness)*

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
*(Unchanged from feature 001 - included for completeness)*

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

### 6. Configuration (ENHANCED)

**Description**: System-wide configuration settings (singleton entity). Enhanced in feature 002 to support automated backup scheduling and Prometheus metrics control.

**Table**: `configuration`

**Fields**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, CHECK(id = 1) | Always 1 (singleton) |
| `backup_schedule_cron` | VARCHAR(100) | NOT NULL, DEFAULT '0 2 * * *' | Cron expression for automated backups (FR-012, FR-013) - **NEW** |
| `prometheus_enabled` | BOOLEAN | NOT NULL, DEFAULT true | Enable/disable Prometheus metrics endpoint (FR-029) - **NEW** |
| `default_sampling_interval` | INTEGER | NOT NULL, DEFAULT 10 | Default sampling interval in seconds (from feature 001) |
| `default_retention_days` | INTEGER | NOT NULL, DEFAULT 90 | Default retention period (from feature 001) |
| `session_timeout_minutes` | INTEGER | NOT NULL, DEFAULT 480 | Session timeout (8 hours default, from feature 001) |
| `max_login_attempts` | INTEGER | NOT NULL, DEFAULT 5 | Failed login threshold before rate limiting (from feature 001) |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Last configuration change |

**Validation Rules**:
- Only one row allowed (enforced by CHECK constraint on `id = 1`)
- Backup schedule: Valid cron expression (validated via `croniter` Python library) - **NEW**
- Prometheus enabled: Boolean (true/false) - **NEW**
- Sampling interval: 5-3600 seconds
- Retention days: 1-3650 days
- Session timeout: 5-1440 minutes (5 min - 24 hours)
- Max login attempts: 1-20

**Indexes**:
- PRIMARY KEY on `id`

**State Transitions**: None (singleton, only updated, never created/deleted)

**Related Entities**:
- One-to-many with BackupJob (backup_jobs) - **NEW in feature 002**

**Migration Notes**:
- Migration `005_backup_notification_entities.py` adds `backup_schedule_cron` and `prometheus_enabled` columns
- Existing configuration row updated with default values (no data loss)
- Backward compatible: existing code unaffected by new columns

---

### 7. BackupJob (NEW)

**Description**: Tracks database backup execution history including success/failure status, file paths, and error diagnostics. Enables audit trail for automated and manual backup operations, supporting operational visibility and compliance requirements (FR-012 through FR-015).

**Table**: `backup_jobs`

**Fields**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Auto-generated unique identifier |
| `configuration_id` | INTEGER | NOT NULL, FOREIGN KEY(configuration.id) | Reference to Configuration (always 1, singleton) |
| `started_at` | TIMESTAMP WITH TIME ZONE | NOT NULL | Backup job start timestamp |
| `completed_at` | TIMESTAMP WITH TIME ZONE | NULL | Backup job completion timestamp (NULL if running or failed) |
| `status` | ENUM('running', 'success', 'failed') | NOT NULL, DEFAULT 'running' | Current backup job status |
| `backup_file_path` | VARCHAR(500) | NULL | Absolute path to backup file (NULL if failed before file creation) |
| `file_size_bytes` | BIGINT | NULL | Backup file size in bytes (NULL if failed) |
| `error_message` | TEXT | NULL | Error details if status is 'failed' (NULL otherwise) |
| `triggered_by` | ENUM('scheduled', 'manual') | NOT NULL | How backup was initiated (cron vs API call) |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Record creation time (same as started_at typically) |

**Validation Rules**:
- Configuration ID: Must always be 1 (references singleton Configuration)
- Started at: Cannot be in future
- Completed at: Must be >= started_at if not NULL
- Status: 'running' → 'success' or 'failed' (no reverse transitions)
- Backup file path: Must be absolute path if status is 'success' (validated at service layer)
- File size: Must be > 0 if status is 'success'
- Error message: Required if status is 'failed', NULL otherwise
- Triggered by: Immutable after creation (audit trail integrity)

**Indexes**:
- PRIMARY KEY on `id`
- INDEX on `configuration_id` (always 1, but supports foreign key integrity)
- INDEX on `status` (for filtering running/failed backups)
- INDEX on `started_at DESC` (for backup history queries ordered by time)
- INDEX on `(status, started_at DESC)` (composite for filtered history queries)

**State Transitions**:
```
       ┌────────────┐
       │  running   │ (initial state)
       └─────┬──────┘
             │
             ├─────────────────────┐
             │ (backup succeeds)   │ (backup fails)
             ▼                     ▼
       ┌────────────┐        ┌────────────┐
       │  success   │        │   failed   │ (terminal states)
       └────────────┘        └────────────┘
```

**Related Entities**:
- Many-to-one with Configuration (configuration_id, always references singleton)

**Business Logic**:
- After 3 consecutive failures, owner users receive in-app notification banner (FR-014)
- Backup retention: Keep 30 most recent backups, delete older files (implemented at service layer)
- Manual backups via API create records with `triggered_by='manual'`
- Scheduled backups via cron create records with `triggered_by='scheduled'`

**Performance Considerations**:
- Backup history queries typically filter by status and sort by started_at (composite index optimizes this)
- Retention cleanup queries scan by started_at (indexed for efficient old record deletion)
- Expected insert rate: 1-7 records per day (negligible storage/performance impact)

---

### 8. ConnectionFailureNotification (NEW)

**Description**: Persists device connection failure alerts with acknowledgment workflow. Enables admin and owner users to track, acknowledge, and clear device offline notifications through in-app banner interface (FR-018 through FR-021).

**Table**: `connection_failure_notifications`

**Fields**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Auto-generated unique identifier |
| `device_id` | UUID | NOT NULL, FOREIGN KEY(devices.id) ON DELETE CASCADE | Device experiencing connection failures |
| `failure_count` | INTEGER | NOT NULL, DEFAULT 3 | Number of consecutive connection failures (min 3 to create notification) |
| `first_failure_at` | TIMESTAMP WITH TIME ZONE | NOT NULL | Timestamp of first failure in sequence |
| `last_failure_at` | TIMESTAMP WITH TIME ZONE | NOT NULL | Timestamp of most recent failure (updated on each retry) |
| `acknowledged` | BOOLEAN | NOT NULL, DEFAULT false | Whether admin has acknowledged alert |
| `acknowledged_by` | UUID | NULL, FOREIGN KEY(users.id) | User who acknowledged notification (NULL if not acknowledged) |
| `acknowledged_at` | TIMESTAMP WITH TIME ZONE | NULL | Timestamp when notification was acknowledged (NULL if not acknowledged) |
| `cleared_at` | TIMESTAMP WITH TIME ZONE | NULL | Timestamp when device reconnected successfully (notification auto-clears) |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Notification creation time |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Last modification time |

**Validation Rules**:
- Device ID: Must reference existing device (cascades on device deletion)
- Failure count: Must be >= 3 (notifications only created after threshold reached per FR-017)
- First failure at: Cannot be in future
- Last failure at: Must be >= first_failure_at
- Acknowledged by: Required if acknowledged is true, NULL otherwise
- Acknowledged at: Required if acknowledged is true, NULL otherwise
- Cleared at: Must be >= first_failure_at if not NULL
- Uniqueness: Only one active (cleared_at IS NULL) notification per device (enforced at service layer)

**Indexes**:
- PRIMARY KEY on `id`
- INDEX on `device_id` (for device-specific notification queries)
- INDEX on `(acknowledged, cleared_at)` (for filtering active/unacknowledged notifications)
- INDEX on `cleared_at` (for filtering active vs cleared notifications)
- UNIQUE INDEX on `device_id WHERE cleared_at IS NULL` (partial unique index, ensures one active notification per device)

**State Transitions**:
```
       ┌──────────────────┐
       │     active       │ (created after 3 failures, acknowledged=false, cleared_at=NULL)
       │  unacknowledged  │
       └────────┬─────────┘
                │
                ├─────────────────────────┐
                │ (user acknowledges)     │ (device reconnects)
                ▼                         ▼
       ┌──────────────────┐      ┌──────────────────┐
       │     active       │      │     cleared      │ (cleared_at set, terminal state)
       │   acknowledged   │      │  unacknowledged  │
       └────────┬─────────┘      └──────────────────┘
                │
                │ (device reconnects)
                ▼
       ┌──────────────────┐
       │     cleared      │ (cleared_at set, terminal state)
       │   acknowledged   │
       └──────────────────┘
```

**Related Entities**:
- Many-to-one with Device (device_id, cascade delete when device removed)
- Many-to-one with User (acknowledged_by, nullable)

**Business Logic**:
- Notification created automatically when device.error_count reaches 3 (FR-017, FR-018)
- Notification updated (failure_count++, last_failure_at updated) on each subsequent connection failure
- Notification cleared automatically (cleared_at set) when device reconnects successfully (FR-019)
- Admin/owner users can acknowledge notification via API (acknowledged=true, acknowledged_by/acknowledged_at set)
- Only active notifications (cleared_at IS NULL) displayed in UI banner
- Dashboard aggregates count of active notifications per device group
- Partial unique index prevents duplicate active notifications for same device

**Performance Considerations**:
- Notification queries filter by acknowledged and cleared_at (composite index optimizes this)
- Dashboard queries count active notifications (indexed for efficient aggregation)
- Expected volume: 1-10 active notifications concurrently (negligible storage/performance impact)
- Cleared notifications retained for audit trail (no automatic deletion, optional manual cleanup)

**Security Considerations**:
- Only admin and owner roles can view notifications (enforced at API layer via RBAC)
- Only admin and owner roles can acknowledge notifications (enforced at API layer)
- Acknowledged_by tracks user responsibility (audit trail, non-nullable when acknowledged=true)

---

## Schema Migration Strategy

**Tool**: Alembic (SQLAlchemy migration framework)

**Migration Files Location**: `backend/src/db/migrations/versions/`

**Existing Migrations** (from feature 001):
- `001_initial_schema.py`: Create all base tables, TimescaleDB extension, hypertable conversion, indexes, default data
- `002_continuous_aggregates.py`: Create continuous aggregates for readings (1min, 1hour, 1day rollups)

**New Migrations** (feature 002):

### Migration 003: Retention Policy (`003_retention_policy.py`)

**Purpose**: Implement automated data retention enforcement per device configuration (FR-008, FR-009).

**Operations**:
1. Create TimescaleDB retention policy on `readings` hypertable:
   ```sql
   SELECT add_retention_policy('readings', INTERVAL '90 days');
   ```
   Note: Policy uses global 90-day default initially, but service layer dynamically manages per-device retention via `drop_chunks()` API.

2. Create scheduled job for daily retention enforcement:
   ```sql
   -- Job runs daily at 2 AM server time (configurable)
   -- Queries devices.retention_days and deletes expired readings per device
   -- Service layer implementation in backend/src/services/retention_service.py
   ```

3. Add retention policy metadata table for tracking cleanup history:
   ```sql
   CREATE TABLE retention_policy_runs (
     id UUID PRIMARY KEY,
     run_at TIMESTAMP WITH TIME ZONE NOT NULL,
     devices_processed INTEGER NOT NULL,
     readings_deleted BIGINT NOT NULL,
     duration_seconds DECIMAL(10,2),
     status VARCHAR(20) NOT NULL,
     error_message TEXT
   );
   ```

**Rollback**: Drop retention policy, drop scheduled job, drop metadata table.

---

### Migration 004: Compression Policy (`004_compression_policy.py`)

**Purpose**: Enable TimescaleDB compression for storage optimization (FR-011, SC-023).

**Operations**:
1. Enable compression on `readings` hypertable:
   ```sql
   ALTER TABLE readings SET (
     timescaledb.compress,
     timescaledb.compress_segmentby = 'device_id',
     timescaledb.compress_orderby = 'timestamp DESC'
   );
   ```

2. Create compression policy for data older than 7 days:
   ```sql
   SELECT add_compression_policy('readings', INTERVAL '7 days');
   ```

3. Compress existing historical data (one-time operation during migration):
   ```sql
   -- Compress all chunks older than 7 days
   SELECT compress_chunk(i) FROM show_chunks('readings', older_than => INTERVAL '7 days') i;
   ```

**Expected Results**:
- Storage reduction: 70-90% for compressed data (SC-023 target: 70%)
- Query performance: Minimal impact (TimescaleDB handles decompression transparently)
- Compression latency: Background job, no user-visible delays

**Rollback**: Remove compression policy, decompress chunks, disable compression on hypertable.

---

### Migration 005: Backup and Notification Entities (`005_backup_notification_entities.py`)

**Purpose**: Add BackupJob and ConnectionFailureNotification entities, enhance Configuration (FR-012-021).

**Operations**:

1. **Enhance Configuration table**:
   ```sql
   ALTER TABLE configuration
     ADD COLUMN backup_schedule_cron VARCHAR(100) NOT NULL DEFAULT '0 2 * * *',
     ADD COLUMN prometheus_enabled BOOLEAN NOT NULL DEFAULT true;

   -- Update existing singleton row
   UPDATE configuration SET
     backup_schedule_cron = '0 2 * * *',
     prometheus_enabled = true
   WHERE id = 1;
   ```

2. **Create BackupJob table**:
   ```sql
   CREATE TABLE backup_jobs (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     configuration_id INTEGER NOT NULL REFERENCES configuration(id),
     started_at TIMESTAMP WITH TIME ZONE NOT NULL,
     completed_at TIMESTAMP WITH TIME ZONE,
     status VARCHAR(20) NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'success', 'failed')),
     backup_file_path VARCHAR(500),
     file_size_bytes BIGINT,
     error_message TEXT,
     triggered_by VARCHAR(20) NOT NULL CHECK (triggered_by IN ('scheduled', 'manual')),
     created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
   );

   CREATE INDEX idx_backup_jobs_configuration_id ON backup_jobs(configuration_id);
   CREATE INDEX idx_backup_jobs_status ON backup_jobs(status);
   CREATE INDEX idx_backup_jobs_started_at ON backup_jobs(started_at DESC);
   CREATE INDEX idx_backup_jobs_status_started_at ON backup_jobs(status, started_at DESC);
   ```

3. **Create ConnectionFailureNotification table**:
   ```sql
   CREATE TABLE connection_failure_notifications (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     device_id UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
     failure_count INTEGER NOT NULL DEFAULT 3 CHECK (failure_count >= 3),
     first_failure_at TIMESTAMP WITH TIME ZONE NOT NULL,
     last_failure_at TIMESTAMP WITH TIME ZONE NOT NULL,
     acknowledged BOOLEAN NOT NULL DEFAULT false,
     acknowledged_by UUID REFERENCES users(id),
     acknowledged_at TIMESTAMP WITH TIME ZONE,
     cleared_at TIMESTAMP WITH TIME ZONE,
     created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
     updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
     CONSTRAINT chk_last_after_first CHECK (last_failure_at >= first_failure_at),
     CONSTRAINT chk_acknowledged_by_required CHECK (
       (acknowledged = false AND acknowledged_by IS NULL AND acknowledged_at IS NULL) OR
       (acknowledged = true AND acknowledged_by IS NOT NULL AND acknowledged_at IS NOT NULL)
     )
   );

   CREATE INDEX idx_notification_device_id ON connection_failure_notifications(device_id);
   CREATE INDEX idx_notification_acknowledged_cleared ON connection_failure_notifications(acknowledged, cleared_at);
   CREATE INDEX idx_notification_cleared_at ON connection_failure_notifications(cleared_at);
   CREATE UNIQUE INDEX idx_notification_active_per_device ON connection_failure_notifications(device_id)
     WHERE cleared_at IS NULL;
   ```

**Validation**:
- Verify Configuration table has 1 row with new columns
- Verify BackupJob and ConnectionFailureNotification tables exist with correct indexes
- Verify CHECK constraints enforce business rules
- Verify partial unique index on active notifications

**Rollback**:
- Drop connection_failure_notifications table
- Drop backup_jobs table
- Remove new columns from configuration table
- Restore configuration to original state

---

**Future Migrations**:
- Backward-compatible changes preferred (add columns with defaults, never drop columns)
- Data migrations must preserve existing readings (never delete historical data)
- Schema changes must maintain TimescaleDB hypertable integrity
- All migrations must be reversible (implement downgrade() function)

**Testing Strategy**:
- Test migrations on copy of production database schema before deployment
- Validate migration up/down reversibility
- Verify data integrity after migration (row counts, foreign keys, constraints)
- Test performance impact of new indexes on large datasets

---

## Data Validation Summary

All validation enforced at three layers:
1. **Database**: Constraints (NOT NULL, UNIQUE, CHECK, FOREIGN KEY)
2. **ORM**: SQLAlchemy model validators (`@validates` decorators)
3. **API**: Pydantic request schemas (FastAPI automatic validation)

**Critical Validations (from feature 001)**:
- Device name uniqueness (FR-025a: clarification)
- Threshold ordering (warning ≤ critical, lower ≤ upper)
- Sampling interval bounds (5-3600s)
- Retention period bounds (1-3650 days)
- Data quality on all readings
- Role enforcement (exactly one owner)

**New Validations (feature 002)**:
- Backup schedule: Valid cron expression (validated via `croniter.is_valid()` in service layer)
- Backup job status: State transitions (running → success/failed, no reverse)
- Backup file path: Absolute path format when status is 'success'
- Notification failure count: Minimum 3 (notifications only created at threshold)
- Notification uniqueness: One active notification per device (partial unique index)
- Acknowledged fields: Consistency (acknowledged=true requires acknowledged_by and acknowledged_at)
- Cleared timestamp: Must be >= first_failure_at if not NULL

**Validation Error Handling**:
- Database constraint violations return HTTP 400 with user-friendly error messages
- SQLAlchemy validators raise `ValueError` with detailed field-level errors
- Pydantic schema validation returns HTTP 422 with field-specific error details
- All validation errors logged with structured context for debugging

---

## Performance Optimizations

### Existing Optimizations (from feature 001)
1. **TimescaleDB Hypertables**: Automatic time-based partitioning for `readings` table
2. **Continuous Aggregates**: Pre-computed rollups for fast dashboard queries (1min, 1hour, 1day)
3. **Strategic Indexes**: Query patterns (device_id + timestamp, status)
4. **Connection Pooling**: SQLAlchemy pooling (10-20 connections) for concurrent API requests

### New Optimizations (feature 002)

#### BackupJob Query Optimization
- **Composite Index** on `(status, started_at DESC)`: Optimizes filtered history queries (e.g., "show last 30 successful backups")
- **Index** on `started_at DESC`: Optimizes retention cleanup queries (delete old backup records)
- **Expected Query Patterns**:
  - List recent backups: `SELECT * FROM backup_jobs ORDER BY started_at DESC LIMIT 30` → Uses started_at index
  - Check for failures: `SELECT * FROM backup_jobs WHERE status='failed' ORDER BY started_at DESC LIMIT 10` → Uses composite index
  - Count consecutive failures: `SELECT COUNT(*) FROM backup_jobs WHERE status='failed' AND started_at > NOW() - INTERVAL '7 days'` → Uses composite index

#### ConnectionFailureNotification Query Optimization
- **Composite Index** on `(acknowledged, cleared_at)`: Optimizes dashboard queries for active unacknowledged notifications
- **Partial Unique Index** on `device_id WHERE cleared_at IS NULL`: Enforces business rule + optimizes active notification lookups
- **Index** on `cleared_at`: Supports filtering active (NULL) vs historical (not NULL) notifications
- **Expected Query Patterns**:
  - Get active notifications: `SELECT * FROM connection_failure_notifications WHERE cleared_at IS NULL` → Uses partial unique index
  - Get unacknowledged active: `SELECT * FROM connection_failure_notifications WHERE acknowledged=false AND cleared_at IS NULL` → Uses composite index
  - Device-specific notifications: `SELECT * FROM connection_failure_notifications WHERE device_id=? ORDER BY created_at DESC` → Uses device_id index

#### Retention Policy Optimization
- **TimescaleDB drop_chunks()**: Native optimized deletion of expired hypertable chunks (orders of magnitude faster than DELETE statements)
- **Target Performance**: Delete 100,000 expired readings in < 5 minutes (SC-022)
- **Scheduled Execution**: Daily at 2 AM (low-traffic period, configurable via Configuration.backup_schedule_cron)

#### Compression Policy Optimization
- **Automatic Compression**: TimescaleDB background job compresses chunks older than 7 days
- **Target Reduction**: 70% storage savings for compressed data (SC-023)
- **Segmentby device_id**: Optimizes queries filtering by device (compression preserves device locality)
- **Orderby timestamp DESC**: Optimizes time-range queries (recent data accessed first)

**Expected Performance** (updated from feature 001):
- Single device query (24h): < 100ms (uses continuous aggregate + compression)
- Dashboard query (100 devices, current values): < 500ms (indexed on device status)
- Insert 1000 readings (10s batch): < 200ms (TimescaleDB optimized inserts)
- Historical export (1 week, 1 device): < 2s (60,480 readings, compressed chunks)
- Backup job history query: < 50ms (indexed on status + started_at)
- Active notifications query: < 30ms (partial unique index on device_id)
- Retention policy execution: < 5 minutes for 100,000 readings (SC-022)

---

## Testing Strategy

### Unit Tests (target: >=80% coverage per constitution)

**Existing Tests (from feature 001)**:
- Model validators (test invalid data rejection)
- Threshold logic (warning/critical ordering)
- State transitions (device status changes)
- Constraint violations (unique names, singleton configuration)

**New Tests (feature 002)**:

#### BackupJob Model Tests
- `test_backup_job_creation`: Verify all fields set correctly
- `test_backup_job_status_transitions`: Validate running → success/failed state changes
- `test_backup_job_validation_error_message_required_on_failure`: Enforce error_message when status='failed'
- `test_backup_job_validation_file_path_required_on_success`: Enforce backup_file_path when status='success'
- `test_backup_job_configuration_reference`: Verify foreign key to Configuration (always id=1)
- `test_backup_job_triggered_by_enum`: Validate scheduled/manual enum values

#### ConnectionFailureNotification Model Tests
- `test_notification_creation_with_minimum_failure_count`: Verify failure_count >= 3 constraint
- `test_notification_unique_active_per_device`: Ensure only one active notification per device
- `test_notification_acknowledged_fields_consistency`: Validate acknowledged_by/acknowledged_at required when acknowledged=true
- `test_notification_cleared_timestamp_ordering`: Verify cleared_at >= first_failure_at
- `test_notification_cascade_delete_on_device_removal`: Confirm ON DELETE CASCADE behavior
- `test_notification_state_transitions`: Validate active → acknowledged → cleared state flow

#### Configuration Enhancement Tests
- `test_configuration_backup_schedule_cron_validation`: Validate cron expression format via croniter
- `test_configuration_prometheus_enabled_boolean`: Verify boolean type constraint
- `test_configuration_singleton_constraint`: Ensure only one row with id=1 exists

### Integration Tests

**Existing Tests (from feature 001)**:
- Database operations (CRUD for all entities)
- Foreign key cascades (delete device → delete readings)
- TimescaleDB hypertable queries (time-range filtering)
- Continuous aggregate accuracy (compare to raw data)

**New Tests (feature 002)**:

#### TimescaleDB Policy Tests (`test_timescale_policies.py`)
- `test_retention_policy_deletes_expired_data`: Verify automatic deletion after retention period
- `test_retention_policy_preserves_recent_data`: Ensure data within retention window not deleted
- `test_compression_policy_reduces_storage`: Measure storage before/after compression (target 70% reduction)
- `test_compression_policy_maintains_query_accuracy`: Verify compressed data returns same results as raw
- `test_retention_policy_performance`: Validate SC-022 (100,000 readings deleted in < 5 minutes)

#### Backup/Restore Tests (`test_backup_restore.py`)
- `test_scheduled_backup_creates_backup_job`: Verify BackupJob record created with triggered_by='scheduled'
- `test_manual_backup_via_api_creates_backup_job`: Verify BackupJob record created with triggered_by='manual'
- `test_backup_success_sets_file_path_and_size`: Validate file metadata populated on success
- `test_backup_failure_sets_error_message`: Verify error details captured on failure
- `test_consecutive_backup_failures_trigger_notification`: Validate FR-014 (3 failures → owner notification)
- `test_backup_restore_data_integrity`: Restore from backup and verify data matches original

#### Reconnection Workflow Tests (`test_reconnection_workflow.py`)
- `test_device_offline_retries_every_60_seconds`: Verify FR-016 retry interval
- `test_third_failure_creates_notification`: Validate FR-018 (error_count=3 → create notification)
- `test_subsequent_failures_update_notification`: Verify failure_count increments, last_failure_at updates
- `test_successful_reconnection_clears_notification`: Validate FR-019 (device online → cleared_at set)
- `test_notification_banner_displays_for_admin_owner_only`: Verify RBAC (read_only users don't see notifications)
- `test_acknowledge_notification_workflow`: Test user acknowledges alert (acknowledged=true, acknowledged_by set)

### Contract Tests

**Existing Tests (from feature 001)**:
- SQLAlchemy model ↔ database schema alignment
- Alembic migrations (up/down reversibility)

**New Tests (feature 002)**:

#### System API Tests (`test_system_api.py`)
- `test_health_endpoint_unauthenticated_access`: Verify FR-007 (health check without auth)
- `test_metrics_endpoint_prometheus_format`: Validate FR-029 (Prometheus-compatible metrics)
- `test_metrics_endpoint_caching`: Verify FR-035 (10-second cache)

#### Config API Tests (`test_config_api.py`)
- `test_get_config_requires_owner_role`: Verify RBAC (only owner can view)
- `test_update_config_requires_owner_role`: Verify RBAC (only owner can modify)
- `test_update_config_validates_cron_expression`: Validate cron format via Pydantic schema
- `test_config_persistence_across_restarts`: Verify SC-002 (config survives server restart)

#### Notification API Tests
- `test_get_notifications_requires_admin_or_owner`: Verify RBAC
- `test_acknowledge_notification_requires_admin_or_owner`: Verify RBAC
- `test_acknowledge_notification_sets_acknowledged_by`: Validate user tracking in audit trail

All tests use Docker-based PostgreSQL + TimescaleDB container for isolation.

---

## Next Steps

With data model defined, Phase 1 continues with:
1. **contracts/**: OpenAPI specification for new API endpoints (system config, health, metrics, backup, notifications)
2. **quickstart.md**: Production deployment guide updates (Docker, Nginx, TLS, backup procedures)
3. **Agent context update**: Add final technology stack (prometheus-client, nginx, backup tools) to `.claude/` context

Data model aligns with all functional requirements (FR-001 through FR-060) and constitution principles:
- **Principle I (Data Reliability)**: Automated retention enforcement, backup history tracking, data integrity constraints
- **Principle II (Observability)**: Connection failure notifications, backup job status tracking, Prometheus metrics control
- **Principle III (Test-First)**: Comprehensive test strategy with >=80% coverage maintained
- **Principle IV (Security)**: RBAC enforcement for config/notifications, audit trails (acknowledged_by, triggered_by)
- **Principle V (Performance)**: Optimized indexes for backup/notification queries, TimescaleDB compression/retention automation

**Ready to proceed with Phase 1 contracts and quickstart guide development.**
