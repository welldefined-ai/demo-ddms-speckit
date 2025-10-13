"""
FastAPI dependencies for database and authentication
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Generator

from src.db.session import SessionLocal
from src.utils.auth import verify_token
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for database session

    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Dependency for getting current authenticated user from JWT token

    Args:
        credentials: HTTP Bearer token credentials

    Returns:
        Dictionary with user data (username, user_id, role)

    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    token = credentials.credentials

    # Verify token
    payload = verify_token(token)

    if not payload:
        logger.warning("Invalid or expired token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Extract user data from token
    username = payload.get("sub")
    user_id = payload.get("user_id")
    role = payload.get("role")

    if not all([username, user_id, role]):
        logger.warning("Token missing required claims")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return {
        "username": username,
        "user_id": user_id,
        "role": role
    }


def require_role(*allowed_roles: str):
    """
    Dependency factory for role-based access control

    Args:
        *allowed_roles: Allowed role names (e.g., "owner", "admin", "read_only")

    Returns:
        Dependency function that checks user role

    Example:
        @router.post("/users", dependencies=[Depends(require_role("owner"))])
    """
    def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role")

        if user_role not in allowed_roles:
            logger.warning(
                f"User {current_user.get('username')} with role {user_role} "
                f"attempted to access endpoint requiring roles: {allowed_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden. Required roles: {', '.join(allowed_roles)}"
            )

        return current_user

    return role_checker
