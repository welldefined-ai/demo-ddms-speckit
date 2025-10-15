"""
User management service for CRUD operations on users (T085)
"""
import uuid
import logging
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.models.user import User, UserRole
from src.utils.auth import hash_password
from src.services.auth_service import validate_password_strength

logger = logging.getLogger(__name__)


def create_user(
    db: Session,
    username: str,
    password: str,
    role: str,
    language_preference: str = "en"
) -> User:
    """
    Create a new user

    Args:
        db: Database session
        username: Username (must be unique)
        password: Plain text password
        role: User role (owner/admin/read_only)
        language_preference: Language preference (en/zh)

    Returns:
        Created User object

    Raises:
        ValueError: If username exists, password is weak, or role is invalid
    """
    # Validate username doesn't exist
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise ValueError(f"Username '{username}' already exists")

    # Validate password strength
    is_valid, error_message = validate_password_strength(password)
    if not is_valid:
        raise ValueError(error_message)

    # Validate role
    try:
        user_role = UserRole(role)
    except ValueError:
        raise ValueError(f"Invalid role: {role}. Must be one of: owner, admin, read_only")

    # Cannot create owner role (only one owner should exist, created during initialization)
    if user_role == UserRole.OWNER:
        raise ValueError("Cannot create additional owner accounts")

    # Validate language preference
    if language_preference not in ["en", "zh"]:
        raise ValueError("Language preference must be 'en' or 'zh'")

    # Hash password
    password_hash = hash_password(password)

    # Create user
    user = User(
        id=uuid.uuid4(),
        username=username,
        password_hash=password_hash,
        role=user_role,
        language_preference=language_preference
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(f"User created: {username} with role {role}")
        return user

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Failed to create user {username}: {e}")
        raise ValueError("Failed to create user due to database constraint")


def get_user_by_id(db: Session, user_id: uuid.UUID) -> Optional[User]:
    """
    Get user by ID

    Args:
        db: Database session
        user_id: User UUID

    Returns:
        User object if found, None otherwise
    """
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """
    Get user by username

    Args:
        db: Database session
        username: Username

    Returns:
        User object if found, None otherwise
    """
    return db.query(User).filter(User.username == username).first()


def list_users(db: Session) -> List[User]:
    """
    List all users

    Args:
        db: Database session

    Returns:
        List of all User objects
    """
    return db.query(User).order_by(User.created_at).all()


def delete_user(db: Session, user_id: uuid.UUID, requesting_user_role: str) -> bool:
    """
    Delete a user

    Args:
        db: Database session
        user_id: User UUID to delete
        requesting_user_role: Role of user making the request

    Returns:
        True if deleted successfully

    Raises:
        ValueError: If trying to delete owner or user not found
    """
    # Only owner can delete users
    if requesting_user_role != "owner":
        raise ValueError("Only owner can delete users")

    user = get_user_by_id(db, user_id)

    if not user:
        raise ValueError("User not found")

    # Cannot delete owner
    if user.role == UserRole.OWNER:
        raise ValueError("Cannot delete owner account")

    db.delete(user)
    db.commit()

    logger.info(f"User deleted: {user.username}")

    return True


def update_user_language(db: Session, user_id: uuid.UUID, language_preference: str) -> User:
    """
    Update user language preference

    Args:
        db: Database session
        user_id: User UUID
        language_preference: New language preference (en/zh)

    Returns:
        Updated User object

    Raises:
        ValueError: If user not found or invalid language
    """
    if language_preference not in ["en", "zh"]:
        raise ValueError("Language preference must be 'en' or 'zh'")

    user = get_user_by_id(db, user_id)

    if not user:
        raise ValueError("User not found")

    user.language_preference = language_preference
    db.commit()
    db.refresh(user)

    logger.info(f"Language preference updated for user: {user.username}")

    return user


def get_user_count_by_role(db: Session) -> dict:
    """
    Get count of users by role

    Args:
        db: Database session

    Returns:
        Dictionary with role counts
    """
    users = list_users(db)

    counts = {
        "owner": 0,
        "admin": 0,
        "read_only": 0
    }

    for user in users:
        counts[user.role.value] += 1

    return counts


def validate_username(username: str) -> Tuple[bool, Optional[str]]:
    """
    Validate username meets requirements

    Args:
        username: Username to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username:
        return False, "Username is required"

    if len(username) < 3:
        return False, "Username must be at least 3 characters long"

    if len(username) > 50:
        return False, "Username must be at most 50 characters long"

    # Only allow alphanumeric and underscore
    if not username.replace('_', '').isalnum():
        return False, "Username can only contain letters, numbers, and underscores"

    return True, None
