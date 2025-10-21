# Data Export

## Purpose

Provides CSV export functionality for device and group historical readings with support for time-range filtering and data aggregation for offline analysis and reporting.

## Requirements

### Requirement: Device Data CSV Export

The system SHALL generate CSV files containing historical readings for individual devices.

#### Scenario: Export device readings with time range

- **WHEN** user requests CSV export for device with start_time and end_time
- **THEN** system queries readings within specified time range
- **AND** system generates CSV with columns: timestamp, value, status
- **AND** system returns CSV file with appropriate content-type header
- **AND** system provides filename: {device_name}_{start}_{end}.csv

#### Scenario: Export with aggregation

- **WHEN** user requests CSV export with aggregate parameter (1min, 1hour, 1day)
- **THEN** system aggregates data using TimescaleDB time_bucket
- **AND** CSV includes columns: time_bucket, avg, min, max, count
- **AND** filename indicates aggregation level

#### Scenario: Export without time constraints

- **WHEN** user requests CSV export without start_time or end_time
- **THEN** system exports all available readings for device
- **AND** system applies pagination or streaming for large datasets
- **AND** filename includes device name and export timestamp

#### Scenario: CSV format and encoding

- **WHEN** system generates CSV file
- **THEN** file uses UTF-8 encoding
- **AND** first row contains column headers
- **AND** timestamps in ISO 8601 format
- **AND** values with appropriate decimal precision
- **AND** status as string (normal/warning/critical)

### Requirement: Group Data CSV Export

The system SHALL generate CSV files containing readings from all devices within a group.

#### Scenario: Export group readings

- **WHEN** user requests CSV export for group with time range
- **THEN** system queries all devices in group
- **AND** system retrieves readings for each device in time range
- **AND** CSV includes columns: device_id, device_name, timestamp, value, status
- **AND** filename: {group_name}_{start}_{end}.csv

#### Scenario: Export group with aggregation

- **WHEN** user requests group CSV with aggregation
- **THEN** system aggregates each device separately
- **AND** CSV includes: device_id, device_name, time_bucket, avg, min, max, count
- **AND** allows comparison across devices in group

#### Scenario: Empty group export

- **WHEN** user requests export for group with no devices
- **THEN** system returns empty CSV with headers only
- **OR** system returns 400 Bad Request indicating empty group

### Requirement: Authentication and Authorization

The system SHALL require authentication for export operations.

#### Scenario: Authenticated user export

- **WHEN** authenticated user requests export
- **THEN** system validates Bearer token
- **AND** system allows export if token valid
- **AND** any authenticated role can export (Owner, Admin, ReadOnly)

#### Scenario: Unauthenticated export attempt

- **WHEN** unauthenticated user requests export
- **THEN** system returns 401 Unauthorized
- **AND** system does not generate CSV file

### Requirement: Export File Naming

The system SHALL generate descriptive filenames for exported CSV files.

#### Scenario: Device export filename

- **WHEN** exporting device data
- **THEN** filename format: {device_name}_{start_time}_{end_time}.csv
- **AND** timestamps formatted as YYYYMMDD_HHMMSS
- **AND** device name sanitized (spaces replaced, special chars removed)

#### Scenario: Group export filename

- **WHEN** exporting group data
- **THEN** filename format: {group_name}_{start_time}_{end_time}.csv
- **AND** same timestamp and sanitization rules apply

#### Scenario: Export without time constraints

- **WHEN** exporting all data
- **THEN** filename: {name}_all_data_{export_timestamp}.csv
- **AND** export_timestamp is current server time

### Requirement: HTTP Response Headers

The system SHALL configure appropriate HTTP headers for CSV downloads.

#### Scenario: Content-Type header

- **WHEN** returning CSV export
- **THEN** response includes Content-Type: text/csv; charset=utf-8
- **AND** ensures proper browser handling

#### Scenario: Content-Disposition header

- **WHEN** returning CSV export
- **THEN** response includes Content-Disposition: attachment; filename="{filename}.csv"
- **AND** triggers browser download dialog
- **AND** suggests filename to user

### Requirement: Export Data Format

The system SHALL format exported data for optimal compatibility with spreadsheet and analysis tools.

#### Scenario: Timestamp formatting

- **WHEN** exporting readings
- **THEN** timestamps formatted as ISO 8601 (YYYY-MM-DDTHH:MM:SS.sssZ)
- **AND** includes timezone information (UTC or configured timezone)
- **AND** compatible with Excel, Google Sheets date parsing

#### Scenario: Numeric value formatting

- **WHEN** exporting reading values
- **THEN** values formatted with appropriate decimal precision
- **AND** uses period (.) as decimal separator
- **AND** no thousands separators
- **AND** scientific notation for very large/small values

#### Scenario: Aggregated data formatting

- **WHEN** exporting aggregated data
- **THEN** time_bucket represents start of interval
- **AND** avg, min, max formatted as numeric values
- **AND** count formatted as integer

### Requirement: Large Dataset Handling

The system SHALL efficiently handle exports of large time ranges with many readings.

#### Scenario: Streaming large exports

- **WHEN** export contains millions of readings
- **THEN** system uses streaming response (not loading all into memory)
- **AND** system generates CSV rows incrementally
- **AND** prevents memory overflow

#### Scenario: Time range validation

- **WHEN** user requests very large time range
- **THEN** system validates request
- **AND** may enforce maximum time range limit (e.g., 1 year)
- **OR** suggests using aggregation for large ranges

### Requirement: Error Handling

The system SHALL provide clear error messages for invalid export requests.

#### Scenario: Invalid device or group ID

- **WHEN** user requests export for non-existent device/group
- **THEN** system returns 404 Not Found
- **AND** provides clear error message

#### Scenario: Invalid time range

- **WHEN** user provides invalid start_time or end_time format
- **THEN** system returns 400 Bad Request
- **AND** indicates expected ISO 8601 format

#### Scenario: Start time after end time

- **WHEN** user provides start_time > end_time
- **THEN** system returns 400 Bad Request
- **AND** indicates invalid time range

## Related Specs

- **Data Models**: `data-models/reading/schema.md`, `data-models/device/schema.md`, `data-models/group/schema.md`
- **APIs**: `api/export/spec.md`
- **Capabilities**: `capabilities/historical-data-analytics/spec.md`
- **Architecture**: `architecture/ddms-system/spec.md`
