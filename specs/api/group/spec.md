# Group API

## Purpose

The Group API enables organizing devices into logical groups for collective monitoring, management, and reporting. It provides CRUD operations for groups, device membership management, alert summaries, and aggregated readings from all devices in a group.

## Base Configuration

**Base URL**: `/api/groups`
**Authentication**: Required for all endpoints (Bearer token). Admin/owner role required for create, update, and delete operations.

## Endpoints

### POST /api/groups

Create a new device group.

**Authentication**: Required (Admin/Owner only)

**Request**:

```json
{
  "name": "Building A Sensors",
  "description": "All temperature sensors in Building A",
  "device_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "223e4567-e89b-12d3-a456-426614174001"
  ]
}
```

**Request Fields**:

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `name` | string | Yes | 1-100 chars, unique | Group name |
| `description` | string | No | Max 500 chars | Group description |
| `device_ids` | array | No | Valid UUIDs | List of device IDs to add to group (default: empty) |

**Responses**:

#### 201 Created

Group created successfully.

```json
{
  "id": "323e4567-e89b-12d3-a456-426614174002",
  "name": "Building A Sensors",
  "description": "All temperature sensors in Building A",
  "devices": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Temperature Sensor 1",
      "unit": "°C",
      "status": "connected"
    },
    {
      "id": "223e4567-e89b-12d3-a456-426614174001",
      "name": "Temperature Sensor 2",
      "unit": "°C",
      "status": "connected"
    }
  ],
  "alert_summary": {
    "normal": 1,
    "warning": 1,
    "critical": 0
  },
  "created_at": "2025-10-20T10:30:00Z",
  "updated_at": "2025-10-20T10:30:00Z"
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Group UUID |
| `name` | string | Group name |
| `description` | string or null | Group description |
| `devices` | array | Array of device objects in the group |
| `devices[].id` | string | Device UUID |
| `devices[].name` | string | Device name |
| `devices[].unit` | string | Measurement unit |
| `devices[].status` | string | Device status (connected/disconnected/error) |
| `alert_summary` | object | Count of devices by alert status |
| `alert_summary.normal` | integer | Number of devices with normal status |
| `alert_summary.warning` | integer | Number of devices with warning status |
| `alert_summary.critical` | integer | Number of devices with critical status |
| `created_at` | string | Creation timestamp (ISO 8601) |
| `updated_at` | string | Last update timestamp (ISO 8601) |

#### 400 Bad Request

Validation error (duplicate name, device not found, etc.).

```json
{
  "detail": "Group with name 'Building A Sensors' already exists"
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

### GET /api/groups

List all device groups.

**Authentication**: Required (accessible to all authenticated users)

**Responses**:

#### 200 OK

Returns array of group objects with device counts.

```json
[
  {
    "id": "323e4567-e89b-12d3-a456-426614174002",
    "name": "Building A Sensors",
    "description": "All temperature sensors in Building A",
    "device_count": 2,
    "created_at": "2025-10-20T10:30:00Z",
    "updated_at": "2025-10-20T10:30:00Z"
  },
  {
    "id": "423e4567-e89b-12d3-a456-426614174003",
    "name": "Building B Sensors",
    "description": null,
    "device_count": 5,
    "created_at": "2025-10-20T09:00:00Z",
    "updated_at": "2025-10-20T09:15:00Z"
  }
]
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Group UUID |
| `name` | string | Group name |
| `description` | string or null | Group description |
| `device_count` | integer | Number of devices in the group |
| `created_at` | string | Creation timestamp (ISO 8601) |
| `updated_at` | string | Last update timestamp (ISO 8601) |

---

### GET /api/groups/{group_id}

Get a specific group by ID with full details including devices and alert summary.

**Authentication**: Required

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `group_id` | UUID | Group UUID |

**Responses**:

#### 200 OK

Returns group object with devices and alert summary.

```json
{
  "id": "323e4567-e89b-12d3-a456-426614174002",
  "name": "Building A Sensors",
  "description": "All temperature sensors in Building A",
  "devices": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Temperature Sensor 1",
      "unit": "°C",
      "status": "connected"
    },
    {
      "id": "223e4567-e89b-12d3-a456-426614174001",
      "name": "Temperature Sensor 2",
      "unit": "°C",
      "status": "connected"
    }
  ],
  "alert_summary": {
    "normal": 1,
    "warning": 1,
    "critical": 0
  },
  "created_at": "2025-10-20T10:30:00Z",
  "updated_at": "2025-10-20T10:30:00Z"
}
```

#### 404 Not Found

Group not found.

```json
{
  "detail": "Group 323e4567-e89b-12d3-a456-426614174002 not found"
}
```

---

### PUT /api/groups/{group_id}

Update an existing group.

**Authentication**: Required (Admin/Owner only)

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `group_id` | UUID | Group UUID |

**Request**:

All fields are optional. Only provided fields will be updated. Note that providing `device_ids` replaces the entire device list (not a merge operation).

```json
{
  "name": "Building A - Updated",
  "description": "Updated description",
  "device_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "223e4567-e89b-12d3-a456-426614174001",
    "323e4567-e89b-12d3-a456-426614174010"
  ]
}
```

**Request Fields**: Same as POST / endpoint, but all fields are optional.

**Responses**:

#### 200 OK

Group updated successfully.

```json
{
  "id": "323e4567-e89b-12d3-a456-426614174002",
  "name": "Building A - Updated",
  "description": "Updated description",
  "devices": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Temperature Sensor 1",
      "unit": "°C",
      "status": "connected"
    },
    {
      "id": "223e4567-e89b-12d3-a456-426614174001",
      "name": "Temperature Sensor 2",
      "unit": "°C",
      "status": "connected"
    },
    {
      "id": "323e4567-e89b-12d3-a456-426614174010",
      "name": "Temperature Sensor 3",
      "unit": "°C",
      "status": "disconnected"
    }
  ],
  "alert_summary": {
    "normal": 2,
    "warning": 1,
    "critical": 0
  },
  "created_at": "2025-10-20T10:30:00Z",
  "updated_at": "2025-10-20T11:00:00Z"
}
```

#### 400 Bad Request

Validation error.

```json
{
  "detail": "Device 323e4567-e89b-12d3-a456-426614174010 not found"
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

Group not found.

```json
{
  "detail": "Group 323e4567-e89b-12d3-a456-426614174002 not found"
}
```

---

### DELETE /api/groups/{group_id}

Delete a group. Devices in the group are preserved and remain in the system.

**Authentication**: Required (Admin/Owner only)

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `group_id` | UUID | Group UUID |

**Responses**:

#### 204 No Content

Group deleted successfully.

#### 403 Forbidden

Insufficient permissions.

```json
{
  "detail": "Access forbidden. Required roles: admin, owner"
}
```

#### 404 Not Found

Group not found.

```json
{
  "detail": "Group 323e4567-e89b-12d3-a456-426614174002 not found"
}
```

---

### GET /api/groups/{group_id}/readings

Get readings from all devices in a group.

**Authentication**: Required

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `group_id` | UUID | Group UUID |

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `hours` | integer | No | 24 | Number of hours to look back |
| `limit` | integer | No | 1000 | Maximum number of readings to return |

**Responses**:

#### 200 OK

Returns readings from all devices in the group.

```json
{
  "group_id": "323e4567-e89b-12d3-a456-426614174002",
  "readings": [
    {
      "device_id": "123e4567-e89b-12d3-a456-426614174000",
      "device_name": "Temperature Sensor 1",
      "timestamp": "2025-10-20T10:30:00Z",
      "value": 25.5,
      "unit": "°C"
    },
    {
      "device_id": "223e4567-e89b-12d3-a456-426614174001",
      "device_name": "Temperature Sensor 2",
      "timestamp": "2025-10-20T10:30:05Z",
      "value": 26.2,
      "unit": "°C"
    }
  ],
  "total": 2400
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `group_id` | string | Group UUID |
| `readings` | array | Array of reading objects from all devices |
| `readings[].device_id` | string | Device UUID |
| `readings[].device_name` | string | Device name |
| `readings[].timestamp` | string | Reading timestamp (ISO 8601) |
| `readings[].value` | float | Measured value |
| `readings[].unit` | string | Measurement unit |
| `total` | integer | Total number of readings returned |

#### 404 Not Found

Group not found.

```json
{
  "detail": "Group 323e4567-e89b-12d3-a456-426614174002 not found"
}
```

---

### GET /api/groups/{group_id}/alerts

Get alert summary for a group (same as alert_summary in group detail).

**Authentication**: Required

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `group_id` | UUID | Group UUID |

**Note**: This endpoint is mentioned in the code but provides the same data as the `alert_summary` field in the GET /{group_id} endpoint. For alert summary data, use GET /{group_id} instead.

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| GROUP_001 | 400 | Group name already exists |
| GROUP_002 | 400 | Device not found in device_ids list |
| GROUP_003 | 400 | Invalid device ID format |
| GROUP_004 | 403 | Insufficient permissions (not admin/owner) |
| GROUP_005 | 404 | Group not found |

## Business Rules

1. **Group Names**: Must be unique across the system
2. **Device Membership**: A device can belong to multiple groups
3. **Device List Updates**: Providing `device_ids` in PUT request replaces the entire device list
4. **Group Deletion**: Deleting a group does not delete the devices in it
5. **Alert Summary**: Calculated based on latest readings and thresholds for each device
6. **Empty Groups**: Groups can exist without any devices

## Alert Status Calculation

The alert summary counts devices based on their current status:

1. **Normal**: Latest reading is within all thresholds (or no thresholds defined)
2. **Warning**: Latest reading exceeds warning thresholds but not critical
3. **Critical**: Latest reading exceeds critical thresholds

The calculation is performed in real-time based on the latest reading for each device in the group.

## Related Specs

- **Capabilities**: Device grouping (CAP-006), Group monitoring (CAP-007)
- **Data Models**: Group model, DeviceGroup association model
- **Services**: group_service for group management and aggregation
