"""
Notification management service for in-app alerts and notifications
"""
import uuid
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from src.models.notification import Notification, NotificationType, NotificationSeverity
from src.models.user import User, UserRole

logger = logging.getLogger(__name__)


def create_notification(
    db: Session,
    user_id: uuid.UUID,
    notification_type: NotificationType,
    severity: NotificationSeverity,
    title: str,
    message: str,
    device_id: Optional[uuid.UUID] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Notification:
    """
    Create a new notification

    Args:
        db: Database session
        user_id: UUID of user who should receive notification
        notification_type: Type of notification (NotificationType enum)
        severity: Severity level (NotificationSeverity enum)
        title: Short notification title
        message: Detailed notification message
        device_id: Optional device UUID if notification is device-related
        metadata: Optional additional context data

    Returns:
        Created Notification object

    Raises:
        ValueError: If user not found or invalid parameters
    """
    # Validate user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User with ID {user_id} not found")

    # Check for duplicate notifications (prevent spam)
    # Don't create duplicate device disconnect notifications for the same device within 5 minutes
    if notification_type == NotificationType.DEVICE_DISCONNECT and device_id:
        recent_cutoff = datetime.utcnow() - timedelta(minutes=5)
        duplicate = db.query(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.device_id == device_id,
                Notification.type == NotificationType.DEVICE_DISCONNECT,
                Notification.created_at >= recent_cutoff,
                Notification.dismissed_at.is_(None)
            )
        ).first()

        if duplicate:
            logger.info(f"Skipping duplicate notification for device {device_id} and user {user_id}")
            return duplicate

    # Create notification
    notification = Notification(
        id=uuid.uuid4(),
        type=notification_type,
        severity=severity,
        title=title,
        message=message,
        user_id=user_id,
        device_id=device_id,
        extra_data=metadata or {}
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    logger.info(f"Notification created: {notification_type.value} for user {user_id}")

    return notification


def get_user_notifications(
    db: Session,
    user_id: uuid.UUID,
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0
) -> List[Notification]:
    """
    Get notifications for a user with pagination

    Args:
        db: Database session
        user_id: UUID of user
        unread_only: If True, only return unread notifications
        limit: Maximum number of notifications to return (default 50)
        offset: Number of notifications to skip (default 0)

    Returns:
        List of Notification objects
    """
    query = db.query(Notification).filter(
        and_(
            Notification.user_id == user_id,
            Notification.dismissed_at.is_(None)  # Don't show dismissed notifications
        )
    )

    if unread_only:
        query = query.filter(Notification.read_at.is_(None))

    notifications = query.order_by(
        Notification.created_at.desc()
    ).limit(limit).offset(offset).all()

    return notifications


def get_notification_by_id(
    db: Session,
    notification_id: uuid.UUID,
    user_id: uuid.UUID
) -> Optional[Notification]:
    """
    Get a specific notification if it belongs to the user

    Args:
        db: Database session
        notification_id: Notification UUID
        user_id: User UUID (for authorization)

    Returns:
        Notification object if found and authorized, None otherwise
    """
    return db.query(Notification).filter(
        and_(
            Notification.id == notification_id,
            Notification.user_id == user_id
        )
    ).first()


def mark_as_read(
    db: Session,
    notification_id: uuid.UUID,
    user_id: uuid.UUID
) -> Notification:
    """
    Mark a notification as read

    Args:
        db: Database session
        notification_id: Notification UUID
        user_id: User UUID (for authorization check)

    Returns:
        Updated Notification object

    Raises:
        ValueError: If notification not found or user not authorized
    """
    notification = get_notification_by_id(db, notification_id, user_id)

    if not notification:
        raise ValueError("Notification not found or access denied")

    if notification.read_at is None:
        notification.read_at = datetime.utcnow()
        db.commit()
        db.refresh(notification)
        logger.info(f"Notification {notification_id} marked as read by user {user_id}")

    return notification


def mark_all_as_read(db: Session, user_id: uuid.UUID) -> int:
    """
    Mark all unread notifications for a user as read

    Args:
        db: Database session
        user_id: User UUID

    Returns:
        Number of notifications marked as read
    """
    count = db.query(Notification).filter(
        and_(
            Notification.user_id == user_id,
            Notification.read_at.is_(None),
            Notification.dismissed_at.is_(None)
        )
    ).update(
        {"read_at": datetime.utcnow()},
        synchronize_session=False
    )

    db.commit()
    logger.info(f"Marked {count} notifications as read for user {user_id}")

    return count


def dismiss_notification(
    db: Session,
    notification_id: uuid.UUID,
    user_id: uuid.UUID
) -> bool:
    """
    Dismiss a notification (soft delete)

    Args:
        db: Database session
        notification_id: Notification UUID
        user_id: User UUID (for authorization check)

    Returns:
        True if dismissed successfully

    Raises:
        ValueError: If notification not found or user not authorized
    """
    notification = get_notification_by_id(db, notification_id, user_id)

    if not notification:
        raise ValueError("Notification not found or access denied")

    notification.dismissed_at = datetime.utcnow()
    db.commit()

    logger.info(f"Notification {notification_id} dismissed by user {user_id}")

    return True


def get_unread_count(db: Session, user_id: uuid.UUID) -> int:
    """
    Get count of unread notifications for a user

    Args:
        db: Database session
        user_id: User UUID

    Returns:
        Count of unread, non-dismissed notifications
    """
    count = db.query(func.count(Notification.id)).filter(
        and_(
            Notification.user_id == user_id,
            Notification.read_at.is_(None),
            Notification.dismissed_at.is_(None)
        )
    ).scalar()

    return count or 0


def get_admin_and_owner_user_ids(db: Session) -> List[uuid.UUID]:
    """
    Get list of all admin and owner user IDs for broadcasting notifications

    Args:
        db: Database session

    Returns:
        List of user UUIDs with admin or owner role
    """
    users = db.query(User.id).filter(
        or_(
            User.role == UserRole.ADMIN,
            User.role == UserRole.OWNER
        )
    ).all()

    return [user.id for user in users]


def create_device_disconnect_notification(
    db: Session,
    device_id: uuid.UUID,
    device_name: str,
    device_ip: str,
    last_reading_at: Optional[datetime] = None
) -> List[Notification]:
    """
    Create device disconnect notification for all admin/owner users

    Args:
        db: Database session
        device_id: Device UUID
        device_name: Device name
        device_ip: Device IP address
        last_reading_at: Timestamp of last successful reading

    Returns:
        List of created Notification objects
    """
    # Get all admin and owner users
    admin_owner_ids = get_admin_and_owner_user_ids(db)

    if not admin_owner_ids:
        logger.warning("No admin or owner users found to notify about device disconnect")
        return []

    # Create notification metadata
    metadata = {
        "device_name": device_name,
        "device_ip": device_ip,
        "last_reading_at": last_reading_at.isoformat() if last_reading_at else None
    }

    # Create notification for each admin/owner user
    notifications = []
    for user_id in admin_owner_ids:
        try:
            notification = create_notification(
                db=db,
                user_id=user_id,
                notification_type=NotificationType.DEVICE_DISCONNECT,
                severity=NotificationSeverity.ERROR,
                title=f"Device Disconnected: {device_name}",
                message=f"Device '{device_name}' ({device_ip}) failed to respond after 3 retry attempts (60 seconds). Last successful reading: {last_reading_at.strftime('%Y-%m-%d %H:%M:%S UTC') if last_reading_at else 'Never'}",
                device_id=device_id,
                metadata=metadata
            )
            notifications.append(notification)
        except Exception as e:
            logger.error(f"Failed to create notification for user {user_id}: {e}")
            # Continue creating notifications for other users even if one fails

    logger.info(f"Created {len(notifications)} device disconnect notifications for device {device_name}")

    return notifications
