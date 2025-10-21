# Notification

## Purpose

Stores in-app notifications for alerting users about device events, system status changes, and other important information requiring user attention.

## Schema

## ADDED Entities

### Entity: Notification

Represents a single notification delivered to a user.

**Table**: `notifications`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique notification identifier |
| `user_id` | UUID | NOT NULL, FOREIGN KEY → users(id) | Recipient user |
| `type` | ENUM('DEVICE_DISCONNECT', 'DEVICE_RECONNECTED', 'DEVICE_CRITICAL', 'SYSTEM_ALERT') | NOT NULL | Notification type/category |
| `severity` | ENUM('INFO', 'WARNING', 'ERROR') | NOT NULL | Severity level for visual styling |
| `title` | VARCHAR(200) | NOT NULL | Notification title (short summary) |
| `message` | TEXT | NOT NULL | Detailed notification message |
| `device_id` | UUID | NULL, FOREIGN KEY → devices(id) | Related device (null for system notifications) |
| `metadata` | JSONB | NULL | Additional structured data (device details, context) |
| `read_at` | TIMESTAMP WITH TIME ZONE | NULL | When user marked notification as read (null = unread) |
| `dismissed_at` | TIMESTAMP WITH TIME ZONE | NULL | When user dismissed notification (null = active) |
| `delivered_at` | TIMESTAMP WITH TIME ZONE | NULL | When notification delivered via real-time channel (null = pending) |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Notification creation timestamp |

**Indexes**:
- `idx_notifications_user_id` ON `user_id` (for user notification queries)
- `idx_notifications_user_created` ON `(user_id, created_at DESC)` (for sorted pagination)
- `idx_notifications_user_read` ON `(user_id, read_at)` (for unread queries)
- `idx_notifications_device_id` ON `device_id` (for device-related notification queries)
- `idx_notifications_created_at` ON `created_at` (for retention cleanup)

**Foreign Keys**:
- `user_id` REFERENCES `users(id)` ON DELETE CASCADE
- `device_id` REFERENCES `devices(id)` ON DELETE SET NULL

**Relationships**:
```typescript
Notification {
  hasMany: []
  belongsTo: [User, Device]
}
```

**Check Constraints**:
- `severity` IN ('INFO', 'WARNING', 'ERROR')
- `type` IN ('DEVICE_DISCONNECT', 'DEVICE_RECONNECTED', 'DEVICE_CRITICAL', 'SYSTEM_ALERT')

## Validation Rules

### Rule: Notification Type

- **MUST** be one of the defined NotificationType enum values
- **DEVICE_DISCONNECT**: Device failed connection after retries
- **DEVICE_RECONNECTED**: Device reconnected after being offline
- **DEVICE_CRITICAL**: Device reading exceeded critical threshold
- **SYSTEM_ALERT**: System-level alerts (maintenance, errors)

### Rule: Notification Severity

- **MUST** be one of: INFO, WARNING, ERROR
- Severity determines visual styling and urgency in UI
- **INFO**: Informational, green/blue styling
- **WARNING**: Attention needed, yellow/orange styling
- **ERROR**: Critical issue requiring action, red styling

### Rule: Title and Message

- Title **MUST NOT** exceed 200 characters
- Title **MUST** be concise summary suitable for notification list
- Message **MUST** be detailed explanation of notification
- Message supports multiline text
- Both fields **MUST** be non-empty

### Rule: User Association

- **MUST** reference valid user_id from users table
- When user deleted, CASCADE deletes all user's notifications
- Cannot create notification for non-existent user

### Rule: Device Association

- Device_id **MAY** be NULL for system-wide notifications
- When device_id provided, **MUST** reference valid device from devices table
- When device deleted, SET NULL on device_id (preserve notification with broken link indicator)

### Rule: Metadata Structure

- Metadata stored as JSONB for flexible structured data
- For DEVICE_DISCONNECT notifications, metadata includes:
  ```json
  {
    "device_name": "string",
    "modbus_ip": "string",
    "modbus_port": number,
    "last_reading_at": "ISO 8601 timestamp",
    "consecutive_failures": number
  }
  ```
- For DEVICE_RECONNECTED notifications, metadata includes:
  ```json
  {
    "device_name": "string",
    "downtime_duration_seconds": number,
    "disconnect_notification_id": "UUID"
  }
  ```

### Rule: Read Status Lifecycle

- Notification created with read_at = NULL (unread)
- User marks as read → read_at set to current timestamp
- read_at timestamp immutable once set (cannot un-read)
- Notifications with read_at NULL counted in unread badge

### Rule: Dismissed Status

- Notification created with dismissed_at = NULL (active)
- User dismisses → dismissed_at set to current timestamp
- Dismissed notifications hidden from default notification center view
- Dismissed notifications still queryable via API with include_dismissed=true
- Dismissing unread notification also marks as read

### Rule: Delivery Tracking

- delivered_at NULL on creation (pending delivery)
- Set to timestamp when successfully sent via WebSocket/SSE to connected client
- Remains NULL if user not connected at creation time (delivered on next fetch)
- Used for debugging real-time delivery issues

### Rule: Timestamp Relationships

- created_at always present and immutable
- read_at >= created_at (if not null)
- dismissed_at >= created_at (if not null)
- delivered_at >= created_at (if not null)

### Rule: Cascade Deletion

- When user deleted, all user's notifications deleted (CASCADE)
- When device deleted, notifications persist but device_id set to NULL (SET NULL)
- Allows preserving notification history even if device removed

### Rule: Duplicate Prevention

- Before creating DEVICE_DISCONNECT notification, check if notification with same device_id and type exists
- If existing notification created within last 5 minutes (300 seconds), skip creation
- Prevents notification spam for flapping devices

## Query Patterns

### Get Unread Notifications Count

```sql
SELECT COUNT(*)
FROM notifications
WHERE user_id = {user_id}
  AND read_at IS NULL
  AND dismissed_at IS NULL
```

### Get Active Notifications (Not Dismissed)

```sql
SELECT *
FROM notifications
WHERE user_id = {user_id}
  AND dismissed_at IS NULL
ORDER BY created_at DESC
LIMIT 20 OFFSET 0
```

### Get Unread Notifications

```sql
SELECT *
FROM notifications
WHERE user_id = {user_id}
  AND read_at IS NULL
  AND dismissed_at IS NULL
ORDER BY created_at DESC
```

### Check for Duplicate Disconnect Notification

```sql
SELECT id
FROM notifications
WHERE device_id = {device_id}
  AND type = 'DEVICE_DISCONNECT'
  AND created_at > NOW() - INTERVAL '5 minutes'
LIMIT 1
```

## Performance Considerations

- Composite index `(user_id, created_at DESC)` enables efficient pagination
- Index on `(user_id, read_at)` for fast unread count queries
- JSONB metadata allows flexible querying without schema changes
- Consider partitioning by created_at for high-volume systems
- Retention cleanup job should use `created_at` index

## Related Specs

- **Capabilities**: `capabilities/device-alerts/spec.md`
- **APIs**: `api/notifications/spec.md`
- **Data Models**: `data-models/user/schema.md` (baseline), `data-models/device/schema.md` (baseline)
