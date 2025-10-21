"""
Notification Management API endpoints
GET /api/notifications, GET /api/notifications/unread-count,
PUT /api/notifications/{id}/read, PUT /api/notifications/read-all,
DELETE /api/notifications/{id}, GET /api/notifications/stream
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import logging
import json
import asyncio

from src.api.dependencies import get_db, get_current_user
from src.utils.auth import verify_token
from src.api.schemas import (
    NotificationResponse,
    NotificationListResponse,
    UnreadCountResponse,
    MessageResponse
)
from src.services import notification_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


def get_current_user_from_token(token: str = Query(..., description="JWT token")) -> dict:
    """
    Get current user from query parameter token (for SSE which doesn't support headers)

    Args:
        token: JWT token from query parameter

    Returns:
        User data dict

    Raises:
        HTTPException: 401 if token is invalid
    """
    payload = verify_token(token)

    if not payload:
        logger.warning("Invalid or expired token provided in query")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    username = payload.get("sub")
    user_id = payload.get("user_id")
    role = payload.get("role")

    if not all([username, user_id, role]):
        logger.warning("Token missing required claims")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    return {
        "username": username,
        "user_id": user_id,
        "role": role
    }


@router.get("", response_model=NotificationListResponse)
def list_notifications(
    unread_only: bool = Query(False, description="Only return unread notifications"),
    limit: int = Query(50, ge=1, le=100, description="Number of notifications to return"),
    offset: int = Query(0, ge=0, description="Number of notifications to skip"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List notifications for the current user with pagination

    Args:
        unread_only: Filter to only unread notifications
        limit: Maximum number of notifications to return (1-100)
        offset: Number of notifications to skip for pagination
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of notifications with total count and unread count
    """
    user_id = uuid.UUID(current_user["user_id"])

    # Get notifications
    notifications = notification_service.get_user_notifications(
        db=db,
        user_id=user_id,
        unread_only=unread_only,
        limit=limit,
        offset=offset
    )

    # Get total unread count
    unread_count = notification_service.get_unread_count(db=db, user_id=user_id)

    # Convert to response schema
    notification_responses = [
        NotificationResponse(
            id=n.id,
            type=n.type.value,
            severity=n.severity.value,
            title=n.title,
            message=n.message,
            device_id=n.device_id,
            metadata=n.extra_data,
            read_at=n.read_at,
            dismissed_at=n.dismissed_at,
            created_at=n.created_at,
            updated_at=n.updated_at
        )
        for n in notifications
    ]

    logger.info(
        f"User {current_user['username']} retrieved {len(notifications)} notifications "
        f"(unread_only={unread_only}, limit={limit}, offset={offset})"
    )

    return NotificationListResponse(
        notifications=notification_responses,
        total=len(notification_responses),
        unread_count=unread_count
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get count of unread notifications for the current user

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        Count of unread notifications
    """
    user_id = uuid.UUID(current_user["user_id"])

    count = notification_service.get_unread_count(db=db, user_id=user_id)

    return UnreadCountResponse(unread_count=count)


@router.put("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Mark a specific notification as read

    Args:
        notification_id: UUID of notification to mark as read
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated notification

    Raises:
        HTTPException: 404 if notification not found or access denied
    """
    user_id = uuid.UUID(current_user["user_id"])

    try:
        notification = notification_service.mark_as_read(
            db=db,
            notification_id=notification_id,
            user_id=user_id
        )

        logger.info(
            f"User {current_user['username']} marked notification {notification_id} as read"
        )

        return NotificationResponse(
            id=notification.id,
            type=notification.type.value,
            severity=notification.severity.value,
            title=notification.title,
            message=notification.message,
            device_id=notification.device_id,
            metadata=notification.extra_data,
            read_at=notification.read_at,
            dismissed_at=notification.dismissed_at,
            created_at=notification.created_at,
            updated_at=notification.updated_at
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/read-all", response_model=MessageResponse)
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Mark all unread notifications as read for the current user

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        Success message with count of notifications marked as read
    """
    user_id = uuid.UUID(current_user["user_id"])

    count = notification_service.mark_all_as_read(db=db, user_id=user_id)

    logger.info(
        f"User {current_user['username']} marked {count} notifications as read"
    )

    return MessageResponse(message=f"Marked {count} notifications as read")


@router.delete("/{notification_id}", response_model=MessageResponse)
def dismiss_notification(
    notification_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Dismiss (soft delete) a notification

    Args:
        notification_id: UUID of notification to dismiss
        db: Database session
        current_user: Current authenticated user

    Returns:
        Success message

    Raises:
        HTTPException: 404 if notification not found or access denied
    """
    user_id = uuid.UUID(current_user["user_id"])

    try:
        notification_service.dismiss_notification(
            db=db,
            notification_id=notification_id,
            user_id=user_id
        )

        logger.info(
            f"User {current_user['username']} dismissed notification {notification_id}"
        )

        return MessageResponse(message="Notification dismissed successfully")

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


async def notification_stream_generator(db: Session, user_id: uuid.UUID):
    """
    Generator function for SSE stream of real-time notifications

    Yields notifications for a specific user in Server-Sent Events format
    Polls database every 2 seconds for new notifications

    Args:
        db: Database session
        user_id: UUID of user to stream notifications for

    Yields:
        SSE formatted notification data
    """
    last_check_time = None

    try:
        while True:
            # Get unread count
            unread_count = notification_service.get_unread_count(db=db, user_id=user_id)

            # Get recent notifications (last 10)
            notifications = notification_service.get_user_notifications(
                db=db,
                user_id=user_id,
                unread_only=False,
                limit=10,
                offset=0
            )

            # Format data for SSE
            data = {
                "unread_count": unread_count,
                "notifications": [
                    {
                        "id": str(n.id),
                        "type": n.type.value,
                        "severity": n.severity.value,
                        "title": n.title,
                        "message": n.message,
                        "device_id": str(n.device_id) if n.device_id else None,
                        "read_at": n.read_at.isoformat() if n.read_at else None,
                        "created_at": n.created_at.isoformat()
                    }
                    for n in notifications
                ]
            }

            # Send as SSE event
            yield f"data: {json.dumps(data)}\n\n"

            # Poll every 2 seconds
            await asyncio.sleep(2)

    except asyncio.CancelledError:
        logger.info(f"SSE stream cancelled for user {user_id}")
        raise
    except Exception as e:
        logger.error(f"Error in notification stream for user {user_id}: {e}", exc_info=True)
        raise


@router.get("/stream")
async def stream_notifications(
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
    Server-Sent Events (SSE) stream of real-time notifications

    This endpoint streams notifications to the authenticated user using the SSE protocol.
    Clients should use EventSource API to consume this stream.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        StreamingResponse with text/event-stream content type

    Example usage in JavaScript:
        const token = localStorage.getItem('access_token');
        const eventSource = new EventSource(`/api/notifications/stream?token=${token}`);
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Unread count:', data.unread_count);
            console.log('Recent notifications:', data.notifications);
        };
    """
    user_id = uuid.UUID(current_user["user_id"])

    logger.info(f"Starting SSE stream for notifications (user: {current_user['username']})")

    return StreamingResponse(
        notification_stream_generator(db, user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
