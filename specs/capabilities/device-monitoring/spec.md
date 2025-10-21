# Device Monitoring and Management

## Purpose

Provides comprehensive device lifecycle management including CRUD operations, Modbus TCP connectivity testing, status tracking, and threshold-based alerting for industrial monitoring devices.

## Requirements

### Requirement: Device Registration and Configuration

The system SHALL allow authorized users to register new Modbus TCP devices with complete configuration parameters.

#### Scenario: Create new device with valid Modbus configuration

- **WHEN** an admin or owner creates a device with name, Modbus IP, port, slave ID, register address, and thresholds
- **THEN** system validates all required fields
- **AND** system creates device with status OFFLINE
- **AND** system returns device details with generated UUID
- **AND** system sets default values (port 502, sampling interval, retention days 90)

#### Scenario: Duplicate device name validation

- **WHEN** user attempts to create device with existing name
- **THEN** system returns 400 Bad Request
- **AND** system provides validation error indicating duplicate name

#### Scenario: Invalid Modbus configuration

- **WHEN** user provides invalid Modbus parameters (slave ID outside 1-247, invalid IP format)
- **THEN** system returns 400 Bad Request with validation errors
- **AND** system does not create the device

### Requirement: Device Configuration Updates

The system SHALL allow modification of device configuration parameters while preserving device identity and historical data.

#### Scenario: Update device thresholds

- **WHEN** user updates warning or critical threshold values
- **THEN** system validates new threshold values
- **AND** system updates device configuration
- **AND** system applies new thresholds to future status calculations
- **AND** system preserves all historical readings

#### Scenario: Update sampling interval

- **WHEN** user changes sampling interval (1-3600 seconds)
- **THEN** system validates range
- **AND** system updates device configuration
- **AND** data collector applies new interval on next polling cycle

#### Scenario: Update retention period

- **WHEN** user changes retention_days parameter
- **THEN** system validates value is positive
- **AND** system updates device configuration
- **AND** automatic cleanup applies new retention policy

### Requirement: Device Deletion

The system SHALL support device deletion with options for historical data preservation.

#### Scenario: Delete device with data preservation

- **WHEN** admin deletes device
- **THEN** system removes device record from devices table
- **AND** system preserves historical readings in readings table
- **AND** system removes device from all groups

#### Scenario: Delete device with data purge

- **WHEN** admin deletes device (default behavior with cascade)
- **THEN** system removes device record
- **AND** system deletes all associated readings (foreign key cascade)
- **AND** system removes device-group associations

### Requirement: Device Status Tracking

The system SHALL automatically track and update device connection status based on data collection results.

#### Scenario: Device becomes online

- **WHEN** data collector successfully reads from device
- **THEN** system updates device status to ONLINE
- **AND** system updates last_reading_at timestamp
- **AND** system stores reading value in readings table

#### Scenario: Device goes offline

- **WHEN** data collector fails to connect to device (timeout, network error)
- **THEN** system updates device status to OFFLINE
- **AND** system does not update last_reading_at

#### Scenario: Device enters error state

- **WHEN** data collector encounters protocol error (invalid response, Modbus exception)
- **THEN** system updates device status to ERROR
- **AND** system logs error details

### Requirement: Modbus Connection Testing

The system SHALL provide connectivity testing before enabling device monitoring.

#### Scenario: Successful connection test

- **WHEN** user tests device connection with valid Modbus configuration
- **THEN** system attempts to read from specified register address
- **THEN** system returns success status with sample reading value
- **AND** system does not persist test reading

#### Scenario: Failed connection test due to timeout

- **WHEN** user tests connection but device does not respond within timeout (default 10 seconds)
- **THEN** system returns failure status with timeout error
- **AND** system provides diagnostic message

#### Scenario: Failed connection test due to invalid register

- **WHEN** user tests connection with invalid register address
- **THEN** system returns Modbus exception code
- **AND** system provides error description

### Requirement: Threshold-Based Status Calculation

The system SHALL calculate alert status based on configured thresholds and current reading values.

#### Scenario: Normal status within thresholds

- **WHEN** device reading value is between warning thresholds (or no thresholds configured)
- **THEN** system calculates status as "normal"
- **AND** system includes status in latest reading response

#### Scenario: Warning status exceeded

- **WHEN** reading value exceeds warning upper threshold (but below critical)
- **THEN** system calculates status as "warning"
- **AND** system includes status in latest reading response

- **WHEN** reading value falls below warning lower threshold (but above critical)
- **THEN** system calculates status as "warning"

#### Scenario: Critical status exceeded

- **WHEN** reading value exceeds critical upper threshold
- **THEN** system calculates status as "critical"
- **AND** critical takes precedence over warning

- **WHEN** reading value falls below critical lower threshold
- **THEN** system calculates status as "critical"

### Requirement: Device Listing and Filtering

The system SHALL provide device listing with optional status filtering.

#### Scenario: List all devices

- **WHEN** user requests device list without filters
- **THEN** system returns all devices with complete configuration
- **AND** response includes status, last_reading_at, and timestamps

#### Scenario: Filter devices by status

- **WHEN** user requests devices with status filter (ONLINE, OFFLINE, ERROR)
- **THEN** system returns only devices matching specified status
- **AND** response maintains same structure as unfiltered list

### Requirement: Device Detail Retrieval

The system SHALL provide detailed information for individual devices including latest reading.

#### Scenario: Get device by ID

- **WHEN** user requests device details with valid UUID
- **THEN** system returns complete device configuration
- **AND** response includes all threshold settings
- **AND** response includes current status and last_reading_at

#### Scenario: Get device with non-existent ID

- **WHEN** user requests device with UUID not in database
- **THEN** system returns 404 Not Found
- **AND** system provides appropriate error message

## Related Specs

- **Data Models**: `data-models/device/schema.md`
- **APIs**: `api/device/spec.md`
- **Capabilities**: `capabilities/real-time-data-collection/spec.md`
- **Architecture**: `architecture/ddms-system/spec.md`
