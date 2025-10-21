# Add Device Disconnect Notifications

## Why

Currently, when a device fails to respond after 3 retry attempts (60 seconds), the system only logs an error message and updates the device status to OFFLINE/ERROR. Administrators have no proactive notification mechanism and must manually monitor the dashboard or check logs to detect device connectivity issues. This can lead to delayed response times for critical equipment failures in industrial monitoring scenarios.

The system needs real-time alerting to notify admins and owners immediately when devices disconnect, enabling faster incident response and reducing downtime.

## What Changes

- Add in-app notification system with real-time delivery to admin/owner users
- Create notification when device disconnects after 3 failed connection attempts
- Store notification history with full tracking (delivery status, read status, timestamps)
- Add notification center UI component showing unread notifications with badge counter
- Add browser push notifications for real-time alerts (when user has granted permission)
- Integrate notification creation in device manager's failure handling logic
- Add API endpoints for fetching, marking as read, and dismissing notifications
- Add WebSocket/SSE channel for real-time notification delivery to connected clients

## Impact

- **Affected specs**:
  - `capabilities/device-alerts` (ADDED - device disconnect alerting)
  - `data-models/notification` (ADDED - notification storage)
  - `api/notifications` (ADDED - notification management endpoints)

- **Affected code**:
  - `backend/src/collectors/device_manager.py` - Add notification creation on device failure
  - `backend/src/models/notification.py` (NEW) - Notification ORM model
  - `backend/src/services/notification_service.py` (NEW) - Notification business logic
  - `backend/src/api/notifications.py` (NEW) - Notification API endpoints
  - `backend/src/db/migrations/` (NEW) - Create notifications table migration
  - `frontend/src/components/NotificationCenter.tsx` (NEW) - Notification UI component
  - `frontend/src/components/Header.tsx` - Add notification bell icon with badge
  - `frontend/src/services/notifications.ts` (NEW) - Notification API client and WebSocket handler

## Success Criteria

- When a device fails 3 connection attempts, a notification is created for all admin/owner users
- Notifications appear in real-time in the notification center (within 2 seconds)
- Browser push notifications work when user has granted permission
- Users can mark notifications as read
- Users can dismiss notifications
- Notification history is queryable with pagination
- Unread notification count displays in header badge
- System logs notification creation and delivery events
- No duplicate notifications for same device disconnect event
