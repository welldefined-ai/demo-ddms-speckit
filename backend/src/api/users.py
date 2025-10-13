"""
User Management API endpoints (T090-T092)
POST /api/users, GET /api/users, DELETE /api/users/{user_id}
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List
import uuid
import logging

from src.api.dependencies import get_db, get_current_user, require_role
from src.services import user_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


# Request/Response schemas
class CreateUserRequest(BaseModel):
    """Create user request schema"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    role: str = Field(..., pattern="^(admin|read_only)$")
    language_preference: str = Field(default="en", pattern="^(en|zh)$")


class UserResponse(BaseModel):
    """User response schema"""
    id: str
    username: str
    role: str
    language_preference: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    request: CreateUserRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("owner"))
):
    """
    Create a new user (T090)

    Only the system owner can create new users.
    Cannot create additional owner accounts.

    Args:
        request: User creation data
        db: Database session
        current_user: Current authenticated user (must be owner)

    Returns:
        Created user data

    Raises:
        HTTPException: 400 if validation fails, 403 if not owner, 409 if username exists
    """
    try:
        # Validate username format
        is_valid, error_msg = user_service.validate_username(request.username)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        # Create user
        user = user_service.create_user(
            db=db,
            username=request.username,
            password=request.password,
            role=request.role,
            language_preference=request.language_preference
        )

        logger.info(
            f"User {current_user.get('username')} created new user: {user.username}"
        )

        return UserResponse(
            id=str(user.id),
            username=user.username,
            role=user.role.value,
            language_preference=user.language_preference,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat()
        )

    except ValueError as e:
        error_msg = str(e)

        # Username already exists
        if "already exists" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_msg
            )

        # Cannot create owner or invalid role
        if "owner" in error_msg.lower() or "Invalid role" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_msg
            )

        # Password validation error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )


@router.get("", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("owner", "admin"))
):
    """
    List all users (T091)

    Only owner and admin roles can list users.
    Read-only users cannot access this endpoint.

    Args:
        db: Database session
        current_user: Current authenticated user (must be owner or admin)

    Returns:
        List of all users
    """
    users = user_service.list_users(db)

    logger.info(
        f"User {current_user.get('username')} listed {len(users)} users"
    )

    return [
        UserResponse(
            id=str(user.id),
            username=user.username,
            role=user.role.value,
            language_preference=user.language_preference,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat()
        )
        for user in users
    ]


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("owner"))
):
    """
    Delete a user (T092)

    Only the system owner can delete users.
    Cannot delete the owner account.

    Args:
        user_id: User ID to delete
        db: Database session
        current_user: Current authenticated user (must be owner)

    Returns:
        204 No Content on success

    Raises:
        HTTPException: 400 if invalid UUID, 403 if trying to delete owner, 404 if user not found
    """
    try:
        # Validate UUID format
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )

        # Delete user
        user_service.delete_user(
            db=db,
            user_id=user_uuid,
            requesting_user_role=current_user.get("role")
        )

        logger.info(
            f"User {current_user.get('username')} deleted user with ID: {user_id}"
        )

        return None

    except ValueError as e:
        error_msg = str(e)

        # Cannot delete owner
        if "owner" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_msg
            )

        # User not found
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )

        # Other errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
