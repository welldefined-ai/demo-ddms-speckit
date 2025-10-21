

## Requirements



### Requirement: Device Disconnect Notification Creation

The system SHALL create notifications for admin and owner users when a device fails to respond after 3 consecutive connection retry attempts.

#### Scenario: Device disconnect after 3 failed retries

- **WHEN** device manager attempts to connect to a device and fails 3 times (each with 10-second timeout)
- **THEN** system queries all users with role ADMIN or OWNER
- **AND** system creates one notification record per admin/owner user
- **AND** notification includes device name, device ID, IP address, last successful reading timestamp
- **AND** notification type is "DEVICE_DISCONNECT"
- **AND** notification severity is "ERROR"
- **AND** system logs notification creation event

#### Scenario: Prevent duplicate disconnect notifications

- **WHEN** device has already failed and notification created in last 5 minutes
- **THEN** system does not create duplicate notification for same device
- **AND** existing notification timestamp is more recent than 5 minutes ago
- **AND** system logs duplicate prevention event

#### Scenario: Device reconnects after disconnect notification

- **WHEN** device was OFFLINE/ERROR and successfully responds to connection attempt
- **THEN** system updates device status to ONLINE
- **AND** system creates notification with type "DEVICE_RECONNECTED"
- **AND** notification severity is "INFO"
- **AND** system references original disconnect notification in metadata

### Requirement: Real-Time Notification Delivery

The system SHALL deliver notifications to active users in real-time via WebSocket or Server-Sent Events.

#### Scenario: User connected with active session

- **WHEN** notification is created for user who has active WebSocket/SSE connection
- **THEN** system broadcasts notification to user's connection within 2 seconds
- **AND** frontend receives notification event via WebSocket/SSE
- **AND** frontend displays notification in notification center
- **AND** frontend increments unread badge counter
- **AND** frontend shows browser push notification (if permission granted)

#### Scenario: User not currently connected

- **WHEN** notification is created for user without active connection
- **THEN** system stores notification in database with status DELIVERED
- **AND** notification appears in user's notification center when they next log in
- **AND** unread count includes notification

#### Scenario: Connection interrupted during delivery

- **WHEN** WebSocket/SSE connection drops during notification broadcast
- **THEN** system marks notification as DELIVERED (not SENT_REALTIME)
- **AND** user receives notification when reconnecting
- **AND** system does not lose notification

### Requirement: Notification Display and Management

The system SHALL provide user interface for viewing, marking as read, and dismissing notifications.

#### Scenario: View notification list

- **WHEN** user opens notification center dropdown
- **THEN** system fetches user's most recent notifications (default 20)
- **AND** notifications displayed with icon, title, message, timestamp
- **AND** unread notifications visually distinct from read notifications
- **AND** notifications sorted by created_at descending (newest first)
- **AND** user can scroll to load older notifications (pagination)

#### Scenario: Mark single notification as read

- **WHEN** user clicks mark as read button on notification
- **THEN** system updates notification read_at timestamp to current time
- **AND** notification visual style changes to read state
- **AND** unread badge counter decrements by 1
- **AND** read status persists across sessions

#### Scenario: Mark all notifications as read

- **WHEN** user clicks "Mark all as read" button
- **THEN** system updates read_at timestamp for all unread notifications for user
- **AND** all notifications visual style changes to read state
- **AND** unread badge counter resets to 0

#### Scenario: Dismiss notification

- **WHEN** user clicks dismiss button on notification
- **THEN** system updates notification dismissed_at timestamp to current time
- **AND** notification removes from notification center list
- **AND** dismissed notification still queryable via API (for history)
- **AND** unread counter decrements if notification was unread

### Requirement: Browser Push Notifications

The system SHALL request browser notification permission and display native OS notifications for critical alerts.

#### Scenario: Request notification permission on login

- **WHEN** user logs in and browser notification permission is "default" (not granted/denied)
- **THEN** frontend requests notification permission via Notification API
- **AND** system stores user's permission response
- **AND** if permission denied, system does not show browser notifications (only in-app)

#### Scenario: Display browser push notification

- **WHEN** device disconnect notification received via WebSocket and user granted browser notification permission
- **THEN** frontend creates native OS notification using Notification API
- **AND** notification shows device name and disconnect message
- **AND** notification includes device icon
- **AND** clicking notification opens app and navigates to device details page

#### Scenario: Browser notification permission denied

- **WHEN** user has denied browser notification permission
- **THEN** system only shows in-app notifications in notification center
- **AND** system does not repeatedly request permission (respect user choice)

### Requirement: Notification Metadata and Context

The system SHALL include relevant device context in notification metadata for troubleshooting.

#### Scenario: Device disconnect notification metadata

- **WHEN** creating device disconnect notification
- **THEN** metadata includes device.name
- **AND** metadata includes device.modbus_ip and device.modbus_port
- **AND** metadata includes device.last_reading_at timestamp
- **AND** metadata includes consecutive_failures count (3)
- **AND** metadata includes device.id for linking to device details page

#### Scenario: Navigate to device from notification

- **WHEN** user clicks on device disconnect notification in notification center
- **THEN** frontend navigates to device details page
- **AND** device details page highlights device ID from notification
- **AND** notification automatically marked as read

### Requirement: Notification Persistence and History

The system SHALL persist all notifications in database for audit trail and historical analysis.

#### Scenario: Query notification history

- **WHEN** user or admin needs to review past notifications
- **THEN** system provides API to query notifications with date range filter
- **AND** query supports filtering by notification type (DEVICE_DISCONNECT, DEVICE_RECONNECTED)
- **AND** query supports filtering by severity (INFO, WARNING, ERROR)
- **AND** query includes dismissed notifications in results
- **AND** query supports pagination (limit/offset)

#### Scenario: Notification retention

- **WHEN** notification is older than 90 days (configurable)
- **THEN** system automatically archives or deletes old notifications
- **AND** retention policy runs as scheduled background job
- **AND** system logs notification cleanup operations

### Requirement: Admin Notification Target Selection

The system SHALL send device disconnect notifications only to users with ADMIN or OWNER roles.

#### Scenario: Admin receives disconnect notification

- **WHEN** device disconnects and user has role ADMIN
- **THEN** system creates notification for admin user
- **AND** admin sees notification in notification center

#### Scenario: Owner receives disconnect notification

- **WHEN** device disconnects and user has role OWNER
- **THEN** system creates notification for owner user
- **AND** owner sees notification in notification center

#### Scenario: Read-only user does not receive disconnect notification

- **WHEN** device disconnects and user has role READ_ONLY
- **THEN** system does not create notification for read-only user
- **AND** read-only user does not see device disconnect in notification center
- **AND** read-only user can still see device status change on dashboard

### Requirement: Notification Authorization and Privacy

The system SHALL ensure users can only access their own notifications via API.

#### Scenario: User queries own notifications

- **WHEN** authenticated user requests GET /api/notifications
- **THEN** system returns only notifications where user_id matches authenticated user
- **AND** response includes read/unread status
- **AND** response includes dismissed status

#### Scenario: User attempts to mark another user's notification as read

- **WHEN** user sends PUT /api/notifications/{notification_id}/read for notification belonging to different user
- **THEN** system returns 403 Forbidden
- **AND** notification read status unchanged
- **AND** system logs authorization violation

#### Scenario: User attempts to dismiss another user's notification

- **WHEN** user sends DELETE /api/notifications/{notification_id} for notification belonging to different user
- **THEN** system returns 403 Forbidden
- **AND** notification remains active
- **AND** system logs authorization violation

## Related Specs

- **Data Models**: `data-models/notification/schema.md`
- **APIs**: `api/notifications/spec.md`
- **Capabilities**: `capabilities/device-monitoring/spec.md` (baseline), `capabilities/real-time-data-collection/spec.md` (baseline)
