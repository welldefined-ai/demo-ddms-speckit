# Notifications API

## Purpose

Provides REST API endpoints for managing user notifications, including fetching notification lists, marking as read, dismissing notifications, and real-time notification delivery via Server-Sent Events.

## Base Configuration

**Base URL**: `/api/notifications`
**Authentication**: Required for all endpoints (Bearer token)

## Endpoints

## ADDED Endpoints

### GET /api/notifications

Retrieve paginated list of user's notifications.

**Authentication**: Required (Bearer token)

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | integer | No | Number of notifications to return (default: 20, max: 100) |
| `offset` | integer | No | Number of notifications to skip for pagination (default: 0) |
| `unread_only` | boolean | No | If true, return only unread notifications (default: false) |
| `include_dismissed` | boolean | No | If true, include dismissed notifications (default: false) |
| `type` | string | No | Filter by notification type (DEVICE_DISCONNECT, DEVICE_RECONNECTED, etc.) |
| `severity` | string | No | Filter by severity (INFO, WARNING, ERROR) |

**Responses**:

#### 200 OK - Success

Returns paginated notification list.

```json
{
  "notifications": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "type": "DEVICE_DISCONNECT",
      "severity": "ERROR",
      "title": "Device Disconnected: Temperature Sensor 01",
      "message": "Device 'Temperature Sensor 01' failed to respond after 3 connection attempts. Last successful reading was at 2024-01-15T14:30:00Z.",
      "device_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "metadata": {
        "device_name": "Temperature Sensor 01",
        "modbus_ip": "192.168.1.100",
        "modbus_port": 502,
        "last_reading_at": "2024-01-15T14:30:00Z",
        "consecutive_failures": 3
      },
      "read_at": null,
      "dismissed_at": null,
      "created_at": "2024-01-15T14:35:00Z"
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "type": "DEVICE_RECONNECTED",
      "severity": "INFO",
      "title": "Device Reconnected: Temperature Sensor 01",
      "message": "Device 'Temperature Sensor 01' has successfully reconnected after 5 minutes of downtime.",
      "device_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "metadata": {
        "device_name": "Temperature Sensor 01",
        "downtime_duration_seconds": 300,
        "disconnect_notification_id": "550e8400-e29b-41d4-a716-446655440000"
      },
      "read_at": "2024-01-15T14:45:00Z",
      "dismissed_at": null,
      "created_at": "2024-01-15T14:40:00Z"
    }
  ],
  "total": 42,
  "limit": 20,
  "offset": 0,
  "has_more": true
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `notifications` | array | Array of notification objects |
| `notifications[].id` | UUID | Notification unique identifier |
| `notifications[].type` | string | Notification type enum value |
| `notifications[].severity` | string | Severity level (INFO, WARNING, ERROR) |
| `notifications[].title` | string | Short notification title |
| `notifications[].message` | string | Detailed notification message |
| `notifications[].device_id` | UUID | Related device ID (null if not device-related) |
| `notifications[].metadata` | object | Additional structured data (device details, context) |
| `notifications[].read_at` | timestamp | When marked as read (null if unread) |
| `notifications[].dismissed_at` | timestamp | When dismissed (null if active) |
| `notifications[].created_at` | timestamp | Notification creation time |
| `total` | integer | Total count of notifications matching filters |
| `limit` | integer | Applied limit |
| `offset` | integer | Applied offset |
| `has_more` | boolean | True if more notifications available |

#### 400 Bad Request - Invalid Parameters

```json
{
  "error": "VALIDATION_ERROR",
  "message": "Invalid query parameters",
  "details": [
    {
      "field": "limit",
      "message": "Limit must be between 1 and 100"
    }
  ]
}
```

#### 401 Unauthorized

```json
{
  "error": "UNAUTHORIZED",
  "message": "Authentication required"
}
```

---

### GET /api/notifications/unread-count

Get count of unread notifications for authenticated user.

**Authentication**: Required (Bearer token)

**Query Parameters**: None

**Responses**:

#### 200 OK - Success

```json
{
  "unread_count": 5
}
```

#### 401 Unauthorized

```json
{
  "error": "UNAUTHORIZED",
  "message": "Authentication required"
}
```

---

### GET /api/notifications/{notification_id}

Get single notification by ID.

**Authentication**: Required (Bearer token)

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `notification_id` | UUID | Notification unique identifier |

**Responses**:

#### 200 OK - Success

Returns single notification object (same structure as list item).

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "DEVICE_DISCONNECT",
  "severity": "ERROR",
  "title": "Device Disconnected: Temperature Sensor 01",
  "message": "Device 'Temperature Sensor 01' failed to respond after 3 connection attempts.",
  "device_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "metadata": {
    "device_name": "Temperature Sensor 01",
    "modbus_ip": "192.168.1.100",
    "modbus_port": 502,
    "last_reading_at": "2024-01-15T14:30:00Z",
    "consecutive_failures": 3
  },
  "read_at": null,
  "dismissed_at": null,
  "created_at": "2024-01-15T14:35:00Z"
}
```

#### 403 Forbidden - Not User's Notification

```json
{
  "error": "FORBIDDEN",
  "message": "You do not have permission to access this notification"
}
```

#### 404 Not Found

```json
{
  "error": "NOT_FOUND",
  "message": "Notification not found"
}
```

#### 401 Unauthorized

```json
{
  "error": "UNAUTHORIZED",
  "message": "Authentication required"
}
```

---

### PUT /api/notifications/{notification_id}/read

Mark a notification as read.

**Authentication**: Required (Bearer token)

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `notification_id` | UUID | Notification unique identifier |

**Request**: Empty body or optional timestamp

```json
{
  "read_at": "2024-01-15T15:00:00Z"
}
```

**Request Fields** (all optional):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `read_at` | timestamp | No | Timestamp to set (defaults to current server time if omitted) |

**Responses**:

#### 200 OK - Success

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "read_at": "2024-01-15T15:00:00Z",
  "message": "Notification marked as read"
}
```

#### 403 Forbidden - Not User's Notification

```json
{
  "error": "FORBIDDEN",
  "message": "You do not have permission to modify this notification"
}
```

#### 404 Not Found

```json
{
  "error": "NOT_FOUND",
  "message": "Notification not found"
}
```

#### 409 Conflict - Already Read

```json
{
  "error": "ALREADY_READ",
  "message": "Notification was already marked as read",
  "read_at": "2024-01-15T14:50:00Z"
}
```

#### 401 Unauthorized

```json
{
  "error": "UNAUTHORIZED",
  "message": "Authentication required"
}
```

---

### PUT /api/notifications/read-all

Mark all unread notifications as read for authenticated user.

**Authentication**: Required (Bearer token)

**Request**: Empty body

**Responses**:

#### 200 OK - Success

```json
{
  "marked_as_read": 5,
  "message": "All notifications marked as read"
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `marked_as_read` | integer | Number of notifications marked as read |
| `message` | string | Success message |

#### 401 Unauthorized

```json
{
  "error": "UNAUTHORIZED",
  "message": "Authentication required"
}
```

---

### DELETE /api/notifications/{notification_id}

Dismiss (soft delete) a notification.

**Authentication**: Required (Bearer token)

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `notification_id` | UUID | Notification unique identifier |

**Responses**:

#### 200 OK - Success

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "dismissed_at": "2024-01-15T15:10:00Z",
  "message": "Notification dismissed"
}
```

#### 403 Forbidden - Not User's Notification

```json
{
  "error": "FORBIDDEN",
  "message": "You do not have permission to dismiss this notification"
}
```

#### 404 Not Found

```json
{
  "error": "NOT_FOUND",
  "message": "Notification not found"
}
```

#### 401 Unauthorized

```json
{
  "error": "UNAUTHORIZED",
  "message": "Authentication required"
}
```

---

### GET /api/notifications/stream

Server-Sent Events stream for real-time notification delivery.

**Authentication**: Required (Bearer token via query parameter or header)

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `token` | string | No | Bearer token (alternative to Authorization header) |

**Connection**:

Client establishes SSE connection:
```javascript
const eventSource = new EventSource('/api/notifications/stream?token=<bearer_token>');
```

**Event Format**:

When notification created for user:

```
event: notification
data: {"id":"550e8400-e29b-41d4-a716-446655440000","type":"DEVICE_DISCONNECT","severity":"ERROR","title":"Device Disconnected: Temperature Sensor 01","message":"Device 'Temperature Sensor 01' failed to respond after 3 connection attempts.","device_id":"7c9e6679-7425-40de-944b-e07fc1f90ae7","metadata":{"device_name":"Temperature Sensor 01","modbus_ip":"192.168.1.100","modbus_port":502,"last_reading_at":"2024-01-15T14:30:00Z","consecutive_failures":3},"read_at":null,"dismissed_at":null,"created_at":"2024-01-15T14:35:00Z"}
```

Heartbeat (keep-alive) every 30 seconds:

```
event: heartbeat
data: {"timestamp":"2024-01-15T15:00:00Z"}
```

**Responses**:

#### 200 OK - Connection Established

Content-Type: `text/event-stream`

Stream remains open, sending events as they occur.

#### 401 Unauthorized

If token invalid or missing:

```json
{
  "error": "UNAUTHORIZED",
  "message": "Authentication required for notification stream"
}
```

**Connection Lifecycle**:

- Client connects with token
- Server authenticates and registers connection for user_id
- Server sends heartbeat every 30 seconds
- When notification created for user, server sends notification event
- Client can reconnect with last-event-id header to resume
- Server removes connection on client disconnect

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed (invalid parameters) |
| `UNAUTHORIZED` | 401 | Missing or invalid authentication token |
| `FORBIDDEN` | 403 | User attempting to access another user's notification |
| `NOT_FOUND` | 404 | Notification ID does not exist |
| `ALREADY_READ` | 409 | Notification already marked as read (idempotent warning) |

## Authorization Rules

- Users can only access their own notifications
- Notification user_id must match authenticated user ID
- Admin/Owner roles have no special privileges for notifications (each user sees only their own)
- Authorization checked on all GET/PUT/DELETE operations

## Rate Limiting

- `/api/notifications`: 100 requests per minute per user
- `/api/notifications/unread-count`: 300 requests per minute per user (higher limit for real-time polling)
- `/api/notifications/stream`: 1 concurrent connection per user

## Performance Considerations

- List endpoint uses composite index (user_id, created_at) for efficient pagination
- Unread count query optimized with index on (user_id, read_at)
- SSE stream maintains connection registry (in-memory map) for fast broadcast
- Notification metadata stored as JSONB for flexible queries without schema changes

## Related Specs

- **Capabilities**: `capabilities/device-alerts/spec.md`
- **Data Models**: `data-models/notification/schema.md`
