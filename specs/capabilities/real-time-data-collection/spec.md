# Real-Time Data Collection

## Purpose

Provides automatic Modbus TCP data collection from registered devices with configurable sampling intervals and real-time streaming via Server-Sent Events (SSE).

## Requirements

### Requirement: Automatic Data Polling

The system SHALL continuously poll enabled Modbus devices according to their configured sampling intervals.

#### Scenario: Successful data collection

- **WHEN** device manager polls device at configured interval
- **THEN** system connects to Modbus TCP endpoint (IP:port)
- **AND** system reads specified register(s) using slave ID
- **AND** system converts register values to float
- **AND** system stores reading with timestamp in readings table
- **AND** system updates device status to ONLINE
- **AND** system updates device last_reading_at timestamp

#### Scenario: Connection failure during polling

- **WHEN** device manager cannot connect to device within timeout (default 10 seconds)
- **THEN** system updates device status to OFFLINE
- **AND** system does not create reading record
- **AND** system logs connection error
- **AND** system retries according to configured retry attempts (default 3)

#### Scenario: Modbus protocol error

- **WHEN** device responds with Modbus exception code
- **THEN** system updates device status to ERROR
- **AND** system logs exception details
- **AND** system does not create reading record

### Requirement: Configurable Sampling Interval

The system SHALL respect per-device sampling interval configuration ranging from 1 to 3600 seconds.

#### Scenario: High-frequency sampling

- **WHEN** device configured with sampling_interval = 1 second
- **THEN** device manager polls device every 1 second
- **AND** system creates up to 1 reading per second

#### Scenario: Low-frequency sampling

- **WHEN** device configured with sampling_interval = 3600 seconds (1 hour)
- **THEN** device manager polls device every hour
- **AND** system creates 1 reading per hour

#### Scenario: Dynamic interval changes

- **WHEN** user updates device sampling_interval
- **THEN** device manager applies new interval on next polling cycle
- **AND** no restart required for interval change to take effect

### Requirement: Latest Reading Retrieval

The system SHALL provide access to the most recent reading for each device with calculated status.

#### Scenario: Get latest reading for active device

- **WHEN** user requests latest reading for device with recent data
- **THEN** system queries most recent reading by timestamp
- **AND** system calculates alert status based on thresholds
- **AND** system returns reading value, timestamp, and status (normal/warning/critical)

#### Scenario: Get latest reading for device with no data

- **WHEN** user requests latest reading for device never polled
- **THEN** system returns 404 Not Found or null reading
- **AND** system indicates no data available

### Requirement: Real-Time Data Streaming via SSE

The system SHALL provide Server-Sent Events stream for real-time monitoring of all devices.

#### Scenario: Client subscribes to SSE stream

- **WHEN** client connects to /api/devices/stream endpoint
- **THEN** system establishes SSE connection
- **AND** system sends initial device readings for all devices
- **AND** system maintains persistent connection

#### Scenario: Periodic data broadcast

- **WHEN** SSE connection is active
- **THEN** system broadcasts device readings every 5 seconds
- **AND** each event includes device_id, device_name, value, status, timestamp
- **AND** system sends all devices in single event batch

#### Scenario: Client disconnects from stream

- **WHEN** client closes SSE connection
- **THEN** system cleanly terminates server-side stream
- **AND** system releases associated resources

#### Scenario: No authentication required for SSE

- **WHEN** client connects to /api/devices/stream
- **THEN** system allows connection without Bearer token
- **AND** public endpoint accessible for monitoring displays

### Requirement: Modbus TCP Protocol Support

The system SHALL implement Modbus TCP/IP protocol using pymodbus library.

#### Scenario: Read holding registers

- **WHEN** collecting data from device
- **THEN** system uses Modbus function code 0x03 (Read Holding Registers)
- **AND** system reads from configured starting register address
- **AND** system reads configured number of registers (default 1)

#### Scenario: Multi-register reading

- **WHEN** device configured with modbus_register_count > 1
- **THEN** system reads multiple consecutive registers
- **AND** system interprets multi-register values according to data type
- **AND** system stores combined value as single reading

#### Scenario: Slave ID addressing

- **WHEN** connecting to Modbus device
- **THEN** system uses configured modbus_slave_id (1-247)
- **AND** system includes slave ID in Modbus request frame

### Requirement: Connection Retry Logic

The system SHALL implement configurable retry mechanism for failed connections.

#### Scenario: Retry on timeout

- **WHEN** initial connection attempt times out
- **THEN** system retries up to configured attempts (default 3)
- **AND** system waits between retry attempts
- **AND** system marks device OFFLINE only after all retries exhausted

#### Scenario: Successful retry

- **WHEN** first attempt fails but retry succeeds
- **THEN** system marks device ONLINE
- **AND** system stores reading from successful attempt
- **AND** system logs recovery in application logs

### Requirement: Device Manager Orchestration

The system SHALL coordinate data collection across all registered devices concurrently.

#### Scenario: Concurrent device polling

- **WHEN** multiple devices registered with same sampling interval
- **THEN** device manager polls devices concurrently (async)
- **AND** system does not block on individual device timeouts
- **AND** system maintains separate polling schedule per device

#### Scenario: New device registration

- **WHEN** new device created via API
- **THEN** device manager automatically includes device in polling schedule
- **AND** system begins polling according to sampling_interval
- **AND** no manual intervention or restart required

#### Scenario: Device deletion

- **WHEN** device deleted via API
- **THEN** device manager removes device from polling schedule
- **AND** system stops polling deleted device immediately

## Related Specs

- **Data Models**: `data-models/device/schema.md`, `data-models/reading/schema.md`
- **APIs**: `api/device/spec.md`
- **Capabilities**: `capabilities/device-monitoring/spec.md`
- **Architecture**: `architecture/ddms-system/spec.md`
