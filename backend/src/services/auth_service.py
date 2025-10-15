"""
Authentication service for user login, logout, and token management (T084)
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
import logging

from src.models.user import User
from src.utils.auth import verify_password, create_access_token, hash_password

logger = logging.getLogger(__name__)

# Rate limiting storage (in-memory for now, should use Redis in production)
login_attempts: dict[str, list[datetime]] = {}
RATE_LIMIT_ATTEMPTS = 5
RATE_LIMIT_WINDOW_MINUTES = 15


def check_rate_limit(username: str) -> Tuple[bool, Optional[int]]:
    """
    Check if user has exceeded rate limit for login attempts

    Args:
        username: Username to check

    Returns:
        Tuple of (is_allowed, seconds_until_reset)
    """
    now = datetime.utcnow()
    cutoff_time = now - timedelta(minutes=RATE_LIMIT_WINDOW_MINUTES)

    # Clean old attempts
    if username in login_attempts:
        login_attempts[username] = [
            attempt for attempt in login_attempts[username]
            if attempt > cutoff_time
        ]

    # Check if rate limited
    attempts = login_attempts.get(username, [])
    if len(attempts) >= RATE_LIMIT_ATTEMPTS:
        # Calculate time until oldest attempt expires
        oldest_attempt = min(attempts)
        reset_time = oldest_attempt + timedelta(minutes=RATE_LIMIT_WINDOW_MINUTES)
        seconds_until_reset = int((reset_time - now).total_seconds())
        return False, seconds_until_reset

    return True, None


def record_login_attempt(username: str):
    """
    Record a failed login attempt for rate limiting

    Args:
        username: Username that failed login
    """
    if username not in login_attempts:
        login_attempts[username] = []

    login_attempts[username].append(datetime.utcnow())


def clear_login_attempts(username: str):
    """
    Clear login attempts after successful login

    Args:
        username: Username to clear
    """
    if username in login_attempts:
        del login_attempts[username]


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Authenticate a user with username and password

    Args:
        db: Database session
        username: Username
        password: Plain text password

    Returns:
        User object if authentication successful, None otherwise
    """
    # Check rate limit
    is_allowed, seconds_until_reset = check_rate_limit(username)
    if not is_allowed:
        logger.warning(f"Rate limit exceeded for user: {username}")
        raise ValueError(f"Too many failed login attempts. Try again in {seconds_until_reset} seconds.")

    # Find user
    user = db.query(User).filter(User.username == username).first()

    if not user:
        logger.info(f"Login attempt for non-existent user: {username}")
        record_login_attempt(username)
        return None

    # Verify password
    if not verify_password(password, user.password_hash):
        logger.info(f"Failed login attempt for user: {username}")
        record_login_attempt(username)
        return None

    # Successful login - clear rate limit
    clear_login_attempts(username)
    logger.info(f"Successful login for user: {username}")

    return user


def login(db: Session, username: str, password: str) -> Tuple[Optional[str], Optional[dict], Optional[str]]:
    """
    Login user and generate access token

    Args:
        db: Database session
        username: Username
        password: Password

    Returns:
        Tuple of (access_token, user_data, refresh_token) if successful, (None, None, None) otherwise
    """
    user = authenticate_user(db, username, password)

    if not user:
        return None, None, None

    # Generate access token
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": str(user.id),
            "role": user.role.value
        }
    )

    # Generate refresh token (longer expiration)
    refresh_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": str(user.id),
            "role": user.role.value,
            "type": "refresh"
        },
        expires_delta=timedelta(days=7)
    )

    # User data to return
    user_data = {
        "id": str(user.id),
        "username": user.username,
        "role": user.role.value,
        "language_preference": user.language_preference
    }

    return access_token, user_data, refresh_token


def logout(username: str) -> bool:
    """
    Logout user (clear any session data)

    Args:
        username: Username to logout

    Returns:
        True if successful
    """
    # In a stateless JWT system, logout is primarily client-side
    # (clearing tokens). Server-side we just log the event.
    logger.info(f"User logged out: {username}")
    return True


def refresh_access_token(username: str, user_id: str, role: str) -> Tuple[str, str]:
    """
    Refresh access token and rotate refresh token

    Args:
        username: Username
        user_id: User ID
        role: User role

    Returns:
        Tuple of (new_access_token, new_refresh_token)
    """
    # Generate new access token
    access_token = create_access_token(
        data={
            "sub": username,
            "user_id": user_id,
            "role": role
        }
    )

    # Rotate refresh token
    refresh_token = create_access_token(
        data={
            "sub": username,
            "user_id": user_id,
            "role": role,
            "type": "refresh"
        },
        expires_delta=timedelta(days=7)
    )

    logger.info(f"Token refreshed for user: {username}")

    return access_token, refresh_token


def change_password(db: Session, user_id: str, old_password: str, new_password: str) -> bool:
    """
    Change user password

    Args:
        db: Database session
        user_id: User ID
        old_password: Current password
        new_password: New password

    Returns:
        True if password changed successfully

    Raises:
        ValueError: If old password is incorrect or new password is weak
    """
    import uuid

    # Find user
    user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()

    if not user:
        raise ValueError("User not found")

    # Verify old password
    if not verify_password(old_password, user.password_hash):
        raise ValueError("Current password is incorrect")

    # Validate new password strength
    if len(new_password) < 8:
        raise ValueError("New password must be at least 8 characters long")

    # Check for complexity (at least one uppercase, one lowercase, one digit, one special char)
    has_upper = any(c.isupper() for c in new_password)
    has_lower = any(c.islower() for c in new_password)
    has_digit = any(c.isdigit() for c in new_password)
    has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in new_password)

    if not (has_upper and has_lower and has_digit and has_special):
        raise ValueError("New password must contain uppercase, lowercase, digit, and special character")

    # Hash and update password
    user.password_hash = hash_password(new_password)
    db.commit()

    logger.info(f"Password changed for user: {user.username}")

    return True


def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
    """
    Validate password meets strength requirements

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)

    if not has_upper:
        return False, "Password must contain at least one uppercase letter"
    if not has_lower:
        return False, "Password must contain at least one lowercase letter"
    if not has_digit:
        return False, "Password must contain at least one digit"
    if not has_special:
        return False, "Password must contain at least one special character"

    return True, None
