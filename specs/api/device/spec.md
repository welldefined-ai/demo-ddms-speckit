# Device API

## Purpose

The Device API provides comprehensive device management capabilities including CRUD operations, real-time device monitoring through Server-Sent Events (SSE), connection testing, and status tracking. It manages Modbus TCP device configurations, sampling intervals, alert thresholds, and data retention policies.

## Base Configuration

**Base URL**: `/api/devices`
**Authentication**: Required for all endpoints (Bearer token). Admin/owner role required for create, update, delete, and test-connection operations.

## Endpoints

### POST /api/devices

Create a new device configuration.

**Authentication**: Required (Admin/Owner only)

**Request**:

```json
{
  "name": "Temperature Sensor 1",
  "modbus_ip": "192.168.1.100",
  "modbus_port": 502,
  "modbus_slave_id": 1,
  "modbus_register": 0,
  "modbus_register_count": 1,
  "unit": "°C",
  "sampling_interval": 10,
  "threshold_warning_lower": 15.0,
  "threshold_warning_upper": 30.0,
  "threshold_critical_lower": 10.0,
  "threshold_critical_upper": 35.0,
  "retention_days": 90
}
```

**Request Fields**:

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `name` | string | Yes | 1-100 chars, unique | Device name |
| `modbus_ip` | string | Yes | Valid IP | Modbus device IP address |
| `modbus_port` | integer | No | 1-65535 | Modbus port (default: 502) |
| `modbus_slave_id` | integer | Yes | 1-255 | Modbus slave ID |
| `modbus_register` | integer | Yes | >= 0 | Starting register address |
| `modbus_register_count` | integer | No | 1-100 | Number of registers (default: 1) |
| `unit` | string | Yes | 1-20 chars | Measurement unit |
| `sampling_interval` | integer | No | 1-3600 | Sampling interval in seconds (default: 10) |
| `threshold_warning_lower` | float | No | - | Lower warning threshold |
| `threshold_warning_upper` | float | No | - | Upper warning threshold |
| `threshold_critical_lower` | float | No | - | Lower critical threshold |
| `threshold_critical_upper` | float | No | - | Upper critical threshold |
| `retention_days` | integer | No | 1-3650 | Data retention in days (default: 90) |

**Responses**:

#### 201 Created

Device created successfully.

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Temperature Sensor 1",
  "modbus_ip": "192.168.1.100",
  "modbus_port": 502,
  "modbus_slave_id": 1,
  "modbus_register": 0,
  "modbus_register_count": 1,
  "unit": "°C",
  "sampling_interval": 10,
  "threshold_warning_lower": 15.0,
  "threshold_warning_upper": 30.0,
  "threshold_critical_lower": 10.0,
  "threshold_critical_upper": 35.0,
  "retention_days": 90,
  "status": "disconnected",
  "last_reading_at": null,
  "created_at": "2025-10-20T10:30:00Z",
  "updated_at": "2025-10-20T10:30:00Z"
}
```

#### 400 Bad Request

Validation error (duplicate name, invalid thresholds, etc.).

```json
{
  "detail": "Device with name 'Temperature Sensor 1' already exists"
}
```

#### 403 Forbidden

Insufficient permissions (not admin/owner).

```json
{
  "detail": "Access forbidden. Required roles: admin, owner"
}
```

---

### GET /api/devices

List all devices with optional status filtering.

**Authentication**: Required

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter by status: `connected`, `disconnected`, or `error` |

**Responses**:

#### 200 OK

Returns array of device objects.

```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Temperature Sensor 1",
    "modbus_ip": "192.168.1.100",
    "modbus_port": 502,
    "modbus_slave_id": 1,
    "modbus_register": 0,
    "modbus_register_count": 1,
    "unit": "°C",
    "sampling_interval": 10,
    "threshold_warning_lower": 15.0,
    "threshold_warning_upper": 30.0,
    "threshold_critical_lower": 10.0,
    "threshold_critical_upper": 35.0,
    "retention_days": 90,
    "status": "connected",
    "last_reading_at": "2025-10-20T10:30:00Z",
    "created_at": "2025-10-20T10:00:00Z",
    "updated_at": "2025-10-20T10:00:00Z"
  }
]
```

#### 400 Bad Request

Invalid status filter value.

```json
{
  "detail": "Invalid status filter: invalid. Must be one of: connected, disconnected, error"
}
```

---

### GET /api/devices/{device_id}

Get a specific device by ID.

**Authentication**: Required

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `device_id` | UUID | Device UUID |

**Responses**:

#### 200 OK

Returns device object.

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Temperature Sensor 1",
  "modbus_ip": "192.168.1.100",
  "modbus_port": 502,
  "modbus_slave_id": 1,
  "modbus_register": 0,
  "modbus_register_count": 1,
  "unit": "°C",
  "sampling_interval": 10,
  "threshold_warning_lower": 15.0,
  "threshold_warning_upper": 30.0,
  "threshold_critical_lower": 10.0,
  "threshold_critical_upper": 35.0,
  "retention_days": 90,
  "status": "connected",
  "last_reading_at": "2025-10-20T10:30:00Z",
  "created_at": "2025-10-20T10:00:00Z",
  "updated_at": "2025-10-20T10:00:00Z"
}
```

#### 404 Not Found

Device not found.

```json
{
  "detail": "Device 123e4567-e89b-12d3-a456-426614174000 not found"
}
```

---

### PUT /api/devices/{device_id}

Update an existing device configuration.

**Authentication**: Required (Admin/Owner only)

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `device_id` | UUID | Device UUID |

**Request**:

All fields are optional. Only provided fields will be updated.

```json
{
  "name": "Temperature Sensor 1 - Updated",
  "sampling_interval": 15,
  "threshold_warning_upper": 32.0
}
```

**Request Fields**: Same as POST / endpoint, but all fields are optional.

**Responses**:

#### 200 OK

Device updated successfully.

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Temperature Sensor 1 - Updated",
  "modbus_ip": "192.168.1.100",
  "modbus_port": 502,
  "modbus_slave_id": 1,
  "modbus_register": 0,
  "modbus_register_count": 1,
  "unit": "°C",
  "sampling_interval": 15,
  "threshold_warning_lower": 15.0,
  "threshold_warning_upper": 32.0,
  "threshold_critical_lower": 10.0,
  "threshold_critical_upper": 35.0,
  "retention_days": 90,
  "status": "connected",
  "last_reading_at": "2025-10-20T10:30:00Z",
  "created_at": "2025-10-20T10:00:00Z",
  "updated_at": "2025-10-20T10:35:00Z"
}
```

#### 400 Bad Request

Validation error.

```json
{
  "detail": "Device with name 'Temperature Sensor 1 - Updated' already exists"
}
```

#### 403 Forbidden

Insufficient permissions.

```json
{
  "detail": "Access forbidden. Required roles: admin, owner"
}
```

#### 404 Not Found

Device not found.

```json
{
  "detail": "Device 123e4567-e89b-12d3-a456-426614174000 not found"
}
```

---

### DELETE /api/devices/{device_id}

Delete a device.

**Authentication**: Required (Admin/Owner only)

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `device_id` | UUID | Device UUID |

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `keep_data` | boolean | No | If true, keep historical readings; if false, delete them (default: false) |

**Responses**:

#### 204 No Content

Device deleted successfully.

#### 403 Forbidden

Insufficient permissions.

```json
{
  "detail": "Access forbidden. Required roles: admin, owner"
}
```

#### 404 Not Found

Device not found.

```json
{
  "detail": "Device 123e4567-e89b-12d3-a456-426614174000 not found"
}
```

---

### GET /api/devices/{device_id}/latest

Get the latest reading for a device with calculated status.

**Authentication**: Required

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `device_id` | UUID | Device UUID |

**Responses**:

#### 200 OK

Returns latest reading with status.

```json
{
  "device_id": "123e4567-e89b-12d3-a456-426614174000",
  "device_name": "Temperature Sensor 1",
  "unit": "°C",
  "timestamp": "2025-10-20T10:30:00Z",
  "value": 25.5,
  "status": "normal"
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `device_id` | string | Device UUID |
| `device_name` | string | Device name |
| `unit` | string | Measurement unit |
| `timestamp` | string | Reading timestamp (ISO 8601) |
| `value` | float | Measured value |
| `status` | string | Calculated status: `normal`, `warning`, or `critical` |

#### 404 Not Found

Device not found or has no readings.

```json
{
  "detail": "Device not found or has no readings"
}
```

---

### POST /api/devices/{device_id}/test-connection

Test connection to a device.

**Authentication**: Required (Admin/Owner only)

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `device_id` | UUID | Device UUID |

**Request**: None (empty body)

**Responses**:

#### 200 OK

Connection test completed (may succeed or fail).

```json
{
  "success": true,
  "error": null,
  "device_id": "123e4567-e89b-12d3-a456-426614174000",
  "device_name": "Temperature Sensor 1"
}
```

Or on failure:

```json
{
  "success": false,
  "error": "Connection timeout",
  "device_id": "123e4567-e89b-12d3-a456-426614174000",
  "device_name": "Temperature Sensor 1"
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether connection test succeeded |
| `error` | string or null | Error message if connection failed, null otherwise |
| `device_id` | string | Device UUID |
| `device_name` | string | Device name |

#### 403 Forbidden

Insufficient permissions.

```json
{
  "detail": "Access forbidden. Required roles: admin, owner"
}
```

#### 404 Not Found

Device not found.

```json
{
  "detail": "Device 123e4567-e89b-12d3-a456-426614174000 not found"
}
```

---

### GET /api/devices/stream

Server-Sent Events (SSE) stream of real-time device readings.

**Authentication**: Required

**Protocol**: Server-Sent Events (SSE)

**Description**:
This endpoint streams device readings to clients using the SSE protocol. It sends updates every 5 seconds with the latest readings from all devices. Clients should use the EventSource API to consume this stream.

**Response**: Continuous stream with `Content-Type: text/event-stream`

**Headers**:
- `Cache-Control: no-cache`
- `Connection: keep-alive`
- `X-Accel-Buffering: no`

**Event Format**:

Each event contains an array of device readings in JSON format:

```
data: [{"device_id":"123e4567-e89b-12d3-a456-426614174000","device_name":"Temperature Sensor 1","unit":"°C","timestamp":"2025-10-20T10:30:00Z","value":25.5,"status":"normal"}]

```

**Event Data Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `device_id` | string | Device UUID |
| `device_name` | string | Device name |
| `unit` | string | Measurement unit |
| `timestamp` | string | Reading timestamp (ISO 8601) |
| `value` | float | Measured value |
| `status` | string | Calculated status: normal, warning, or critical |

**Error Events**:

If an error occurs during streaming:

```
event: error
data: {"error":"Error message"}

```

**Client Usage Example** (JavaScript):

```javascript
const eventSource = new EventSource('/api/devices/stream', {
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN_HERE'
  }
});

eventSource.onmessage = (event) => {
  const devices = JSON.parse(event.data);
  console.log('Received devices:', devices);
};

eventSource.onerror = (error) => {
  console.error('SSE error:', error);
};
```

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| DEVICE_001 | 400 | Device name already exists |
| DEVICE_002 | 400 | Invalid threshold configuration |
| DEVICE_003 | 400 | Invalid Modbus configuration |
| DEVICE_004 | 400 | Invalid status filter value |
| DEVICE_005 | 403 | Insufficient permissions (not admin/owner) |
| DEVICE_006 | 404 | Device not found |
| DEVICE_007 | 404 | Device has no readings |

## Business Rules

1. **Device Names**: Must be unique across the system
2. **Threshold Validation**: Critical thresholds must be more restrictive than warning thresholds
3. **Sampling Interval**: Must be between 1 and 3600 seconds
4. **Data Retention**: Must be between 1 and 3650 days
5. **Status Calculation**: Based on comparing latest reading against thresholds:
   - `normal`: Within all thresholds or no thresholds defined
   - `warning`: Exceeds warning thresholds but not critical
   - `critical`: Exceeds critical thresholds
6. **Connection Status**: Automatically updated based on Modbus communication success/failure

## Related Specs

- **Capabilities**: Device management (CAP-002), Real-time monitoring (CAP-003)
- **Data Models**: Device model, DeviceStatus enum
- **Services**: device_service for business logic, device_manager for monitoring
