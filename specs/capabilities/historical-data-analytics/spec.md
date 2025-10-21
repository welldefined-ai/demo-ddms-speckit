# Historical Data Analytics

## Purpose

Provides time-series data retrieval, aggregation, and statistical analysis for device readings with support for flexible time ranges and automatic data retention management.

## Requirements

### Requirement: Time-Range Data Retrieval

The system SHALL allow querying historical readings for specific devices within user-defined time ranges.

#### Scenario: Query readings with start and end time

- **WHEN** user requests readings with start_time and end_time (ISO 8601 format)
- **THEN** system queries readings table WHERE timestamp BETWEEN start_time AND end_time
- **AND** system filters by device_id
- **AND** system orders results by timestamp ascending
- **AND** system returns array of {timestamp, value} objects

#### Scenario: Query with only start time

- **WHEN** user provides start_time without end_time
- **THEN** system queries readings from start_time to current time
- **AND** system applies same filtering and ordering

#### Scenario: Query with only end time

- **WHEN** user provides end_time without start_time
- **THEN** system queries all readings up to end_time
- **AND** system applies same filtering and ordering

#### Scenario: Query without time constraints

- **WHEN** user requests readings without start_time or end_time
- **THEN** system returns all available readings for device
- **AND** system applies pagination limits to prevent excessive results

### Requirement: Pagination Support

The system SHALL support pagination for large result sets using limit and offset parameters.

#### Scenario: Paginated results with default limit

- **WHEN** user queries readings without limit parameter
- **THEN** system returns maximum 100 readings (default limit)
- **AND** response includes returned count

#### Scenario: Custom page size

- **WHEN** user specifies limit parameter (1-1000)
- **THEN** system returns specified number of readings
- **AND** system validates limit is within allowed range

#### Scenario: Offset pagination

- **WHEN** user specifies offset parameter
- **THEN** system skips specified number of readings
- **AND** system returns next page of results
- **AND** offset + limit allows iterating through large datasets

#### Scenario: Exceeding maximum limit

- **WHEN** user requests limit > 1000
- **THEN** system returns 400 Bad Request with validation error
- **AND** system indicates maximum allowed limit

### Requirement: Data Aggregation

The system SHALL provide time-based aggregation with statistical functions for analysis over longer periods.

#### Scenario: 1-minute aggregation

- **WHEN** user requests readings with aggregate="1min"
- **THEN** system uses TimescaleDB time_bucket('1 minute', timestamp)
- **AND** system calculates avg(value), min(value), max(value), count(*)
- **AND** system groups readings into 1-minute intervals
- **AND** response includes {time_bucket, avg, min, max, count} for each interval

#### Scenario: 1-hour aggregation

- **WHEN** user requests readings with aggregate="1hour"
- **THEN** system uses time_bucket('1 hour', timestamp)
- **AND** system calculates same statistics over hourly intervals
- **AND** system returns aggregated hourly data points

#### Scenario: 1-day aggregation

- **WHEN** user requests readings with aggregate="1day"
- **THEN** system uses time_bucket('1 day', timestamp)
- **AND** system calculates daily statistics
- **AND** useful for long-term trend analysis (weeks, months)

#### Scenario: No aggregation specified

- **WHEN** user omits aggregate parameter
- **THEN** system returns raw reading values without aggregation
- **AND** each reading is individual data point with original timestamp and value

### Requirement: Reading Count Queries

The system SHALL provide count of readings within specified time range without returning full data.

#### Scenario: Count readings in time range

- **WHEN** user requests reading count with start_time and end_time
- **THEN** system executes SELECT COUNT(*) query
- **AND** system returns integer count of matching readings
- **AND** more efficient than retrieving full dataset for count

### Requirement: Latest Reading Query

The system SHALL provide optimized access to most recent reading for a device.

#### Scenario: Get latest single reading

- **WHEN** user requests latest reading for device
- **THEN** system queries readings ORDER BY timestamp DESC LIMIT 1
- **AND** system uses index on (device_id, timestamp) for fast retrieval
- **AND** system returns most recent {timestamp, value}

#### Scenario: Latest reading for device with no data

- **WHEN** user requests latest reading for device with no readings
- **THEN** system returns null or empty result
- **AND** system returns 404 Not Found status

### Requirement: Automatic Data Retention

The system SHALL automatically delete readings older than configured retention period per device.

#### Scenario: Default retention period

- **WHEN** device created without explicit retention_days
- **THEN** system sets retention_days = 90 (default from configuration)
- **AND** automatic cleanup process deletes readings older than 90 days

#### Scenario: Custom retention period

- **WHEN** device configured with specific retention_days value
- **THEN** system applies custom retention to that device only
- **AND** cleanup process deletes readings older than custom retention period

#### Scenario: Retention cleanup execution

- **WHEN** scheduled cleanup job runs (background task)
- **THEN** system deletes readings WHERE timestamp < NOW() - retention_days
- **AND** system performs deletion per device according to device.retention_days
- **AND** system uses TimescaleDB retention policies for efficient deletion

### Requirement: TimescaleDB Hypertable Optimization

The system SHALL leverage TimescaleDB hypertable for efficient time-series queries.

#### Scenario: Efficient time-range queries

- **WHEN** querying readings by time range
- **THEN** system uses TimescaleDB chunk-based storage
- **AND** system prunes irrelevant chunks based on time range
- **AND** query performance scales with queried time range, not total data size

#### Scenario: Composite index usage

- **WHEN** filtering readings by device_id and timestamp
- **THEN** system uses composite index (device_id, timestamp)
- **AND** system achieves fast lookups for device-specific time ranges

### Requirement: Group Historical Data Retrieval

The system SHALL support querying historical data for all devices within a group.

#### Scenario: Query group readings

- **WHEN** user requests readings for group with time range
- **THEN** system joins device_groups to get all devices in group
- **AND** system queries readings for all associated devices
- **AND** system returns readings grouped by device or flattened
- **AND** response includes device_id and device_name for each reading

### Requirement: Statistical Aggregates

The system SHALL calculate statistical measures during aggregation queries.

#### Scenario: Average value calculation

- **WHEN** user requests aggregated data
- **THEN** system calculates AVG(value) for each time bucket
- **AND** system returns average as representative value for interval

#### Scenario: Min/Max value calculation

- **WHEN** user requests aggregated data
- **THEN** system calculates MIN(value) and MAX(value) for each bucket
- **AND** useful for identifying peaks and troughs in time period

#### Scenario: Count of readings

- **WHEN** user requests aggregated data
- **THEN** system calculates COUNT(*) for each time bucket
- **AND** indicates data density and potential gaps in collection

## Related Specs

- **Data Models**: `data-models/reading/schema.md`, `data-models/device/schema.md`
- **APIs**: `api/reading/spec.md`
- **Capabilities**: `capabilities/data-export/spec.md`
- **Architecture**: `architecture/ddms-system/spec.md`
