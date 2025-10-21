# Implementation Tasks

## 1. Database Schema

- [ ] 1.1 Design notifications table schema with fields for type, severity, device reference, user, read/dismissed status
- [ ] 1.2 Write Alembic migration to create notifications table
- [ ] 1.3 Add indexes for user_id, created_at, read status for efficient queries
- [ ] 1.4 Test migration up/down on development database
- [ ] 1.5 Update database documentation

## 2. Backend - Data Models

- [ ] 2.1 Create SQLAlchemy ORM model for Notification (`backend/src/models/notification.py`)
- [ ] 2.2 Add NotificationType and NotificationSeverity enums
- [ ] 2.3 Add foreign key relationships (user, device)
- [ ] 2.4 Add timestamps (created_at, read_at, dismissed_at)

## 3. Backend - Notification Service

- [ ] 3.1 Create notification service (`backend/src/services/notification_service.py`)
- [ ] 3.2 Implement `create_notification(user_id, type, severity, message, device_id, metadata)`
- [ ] 3.3 Implement `get_user_notifications(user_id, unread_only, limit, offset)` with pagination
- [ ] 3.4 Implement `mark_as_read(notification_id, user_id)` with authorization check
- [ ] 3.5 Implement `mark_all_as_read(user_id)`
- [ ] 3.6 Implement `dismiss_notification(notification_id, user_id)` with authorization check
- [ ] 3.7 Implement `get_unread_count(user_id)`
- [ ] 3.8 Add duplicate prevention logic (check if same device alert exists in last 5 minutes)

## 4. Backend - Device Manager Integration

- [ ] 4.1 Update `device_manager.py` to import notification_service
- [ ] 4.2 In failure handler (after 3 retries), query all admin/owner users
- [ ] 4.3 Create notification for each admin/owner with device disconnect details
- [ ] 4.4 Include device name, IP, last successful reading time in notification metadata
- [ ] 4.5 Log notification creation events
- [ ] 4.6 Add error handling for notification creation failures (don't block device polling)

## 5. Backend - API Endpoints

- [ ] 5.1 Create notifications API router (`backend/src/api/notifications.py`)
- [ ] 5.2 Implement GET `/api/notifications` - list user's notifications (with pagination, filters)
- [ ] 5.3 Implement GET `/api/notifications/unread-count` - get unread count
- [ ] 5.4 Implement PUT `/api/notifications/{notification_id}/read` - mark as read
- [ ] 5.5 Implement PUT `/api/notifications/read-all` - mark all as read
- [ ] 5.6 Implement DELETE `/api/notifications/{notification_id}` - dismiss notification
- [ ] 5.7 Add Pydantic schemas for request/response validation
- [ ] 5.8 Add RBAC checks (users can only access their own notifications)
- [ ] 5.9 Register router in main.py

## 6. Backend - Real-Time Delivery

- [ ] 6.1 Create WebSocket or SSE endpoint for notification streaming (`/api/notifications/stream`)
- [ ] 6.2 Maintain connection registry mapping user_id to active connections
- [ ] 6.3 In notification service, broadcast to connected users when notification created
- [ ] 6.4 Handle connection lifecycle (connect, disconnect, reconnect)
- [ ] 6.5 Add authentication to WebSocket/SSE endpoint
- [ ] 6.6 Test with multiple simultaneous connections

## 7. Backend - Testing

- [ ] 7.1 Unit tests for notification service CRUD operations
- [ ] 7.2 Unit tests for duplicate prevention logic
- [ ] 7.3 Unit tests for authorization checks
- [ ] 7.4 Integration test: device disconnect → notification created
- [ ] 7.5 Integration test: notification API endpoints
- [ ] 7.6 Integration test: real-time delivery via WebSocket/SSE
- [ ] 7.7 Test pagination and filtering
- [ ] 7.8 Test concurrent notification creation

## 8. Frontend - Data Layer

- [ ] 8.1 Create notification TypeScript types/interfaces
- [ ] 8.2 Create notification API client (`frontend/src/services/notifications.ts`)
- [ ] 8.3 Implement API methods (fetchNotifications, markAsRead, markAllAsRead, dismiss, getUnreadCount)
- [ ] 8.4 Implement WebSocket/SSE connection for real-time notifications
- [ ] 8.5 Add reconnection logic with exponential backoff
- [ ] 8.6 Add notification context/state management (React Context or similar)

## 9. Frontend - Notification Center Component

- [ ] 9.1 Create NotificationCenter component (`frontend/src/components/NotificationCenter.tsx`)
- [ ] 9.2 Implement dropdown panel with notification list
- [ ] 9.3 Display notification icon, title, message, timestamp
- [ ] 9.4 Add "Mark as read" button per notification
- [ ] 9.5 Add "Mark all as read" button
- [ ] 9.6 Add "Dismiss" action per notification
- [ ] 9.7 Implement infinite scroll or pagination for notification list
- [ ] 9.8 Add empty state when no notifications
- [ ] 9.9 Add loading states
- [ ] 9.10 Style with appropriate colors for severity (info/warning/error)

## 10. Frontend - Header Integration

- [ ] 10.1 Update Header component to include notification bell icon
- [ ] 10.2 Add unread count badge on notification bell
- [ ] 10.3 Toggle NotificationCenter dropdown on bell click
- [ ] 10.4 Update unread count in real-time via WebSocket/SSE
- [ ] 10.5 Add visual/audio indicator for new notifications (optional)

## 11. Frontend - Browser Push Notifications

- [ ] 11.1 Request notification permission on user login (if not granted)
- [ ] 11.2 Use Web Notifications API to show browser notifications
- [ ] 11.3 Display notification when device disconnect event received via WebSocket
- [ ] 11.4 Handle notification click to open app and focus relevant device
- [ ] 11.5 Respect browser notification settings (don't spam if user denied permission)
- [ ] 11.6 Add user preference to enable/disable browser notifications (future enhancement - skip for now)

## 12. Frontend - Testing

- [ ] 12.1 Unit tests for notification API client
- [ ] 12.2 Unit tests for NotificationCenter component
- [ ] 12.3 Integration test: WebSocket connection and message handling
- [ ] 12.4 E2E test: device disconnect → notification appears in UI
- [ ] 12.5 E2E test: mark as read functionality
- [ ] 12.6 E2E test: dismiss notification
- [ ] 12.7 Visual regression tests for NotificationCenter

## 13. Documentation

- [ ] 13.1 Document notification data model in specs
- [ ] 13.2 Document notification API endpoints
- [ ] 13.3 Update user guide with notification center usage
- [ ] 13.4 Document WebSocket/SSE protocol for real-time delivery
- [ ] 13.5 Add notification examples to API documentation

## 14. Validation & Review

- [ ] 14.1 Run `tigs validate-specs --change add-device-disconnect-notifications`
- [ ] 14.2 Review all delta specs for completeness
- [ ] 14.3 Code review for backend changes
- [ ] 14.4 Code review for frontend changes
- [ ] 14.5 Security review (authorization, input validation)
- [ ] 14.6 Performance review (notification query efficiency, WebSocket scaling)

## 15. Deployment

- [ ] 15.1 Run database migration in staging environment
- [ ] 15.2 Deploy backend to staging
- [ ] 15.3 Deploy frontend to staging
- [ ] 15.4 QA testing in staging (simulate device disconnects)
- [ ] 15.5 Load testing (create 1000+ notifications, test query performance)
- [ ] 15.6 Run database migration in production
- [ ] 15.7 Deploy backend to production
- [ ] 15.8 Deploy frontend to production
- [ ] 15.9 Monitor error rates and notification delivery latency
- [ ] 15.10 Archive change: `tigs archive-change add-device-disconnect-notifications`
