"""
Role-Based Access Control (RBAC) decorators
"""
from functools import wraps
from typing import Callable, List
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.utils.auth import verify_token
from src.models.user import UserRole

# HTTP Bearer token security scheme
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Extract and verify current user from JWT token

    Args:
        credentials: HTTP Authorization header with Bearer token

    Returns:
        Decoded token payload containing user information

    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    token = credentials.credentials
    payload = verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


def require_auth(user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency to require authentication for an endpoint

    Usage:
        @app.get("/protected")
        def protected_route(user: dict = Depends(require_auth)):
            return {"user": user}

    Args:
        user: Current user from JWT token

    Returns:
        User payload dictionary
    """
    return user


def require_roles(allowed_roles: List[UserRole]) -> Callable:
    """
    Decorator factory to require specific roles for an endpoint

    Usage:
        @app.get("/admin-only")
        def admin_route(user: dict = Depends(require_roles([UserRole.OWNER, UserRole.ADMIN]))):
            return {"message": "Admin access granted"}

    Args:
        allowed_roles: List of UserRole enums that are allowed access

    Returns:
        Dependency function that validates user role

    Raises:
        HTTPException: 403 if user doesn't have required role
    """
    def role_checker(user: dict = Depends(get_current_user)) -> dict:
        user_role_str = user.get("role")

        # Convert string to UserRole enum for comparison
        try:
            user_role = UserRole(user_role_str)
        except (ValueError, KeyError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid user role"
            )

        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {[r.value for r in allowed_roles]}"
            )

        return user

    return role_checker


def require_owner(user: dict = Depends(require_roles([UserRole.OWNER]))) -> dict:
    """
    Dependency to require OWNER role

    Usage:
        @app.delete("/users/{user_id}")
        def delete_user(user_id: str, user: dict = Depends(require_owner)):
            ...
    """
    return user


def require_admin(user: dict = Depends(require_roles([UserRole.OWNER, UserRole.ADMIN]))) -> dict:
    """
    Dependency to require OWNER or ADMIN role

    Usage:
        @app.post("/devices")
        def create_device(device: DeviceCreate, user: dict = Depends(require_admin)):
            ...
    """
    return user
