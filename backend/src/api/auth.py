"""
Authentication API endpoints (T086-T089)
POST /api/auth/login, POST /api/auth/logout, POST /api/auth/refresh, POST /api/auth/change-password
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from src.api.dependencies import get_db, get_current_user
from src.services import auth_service
from src.utils.auth import verify_token
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


# Request/Response schemas
class LoginRequest(BaseModel):
    """Login request schema"""
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """Login response schema"""
    access_token: str
    token_type: str = "bearer"
    refresh_token: str
    user: dict


class RefreshResponse(BaseModel):
    """Token refresh response schema"""
    access_token: str
    token_type: str = "bearer"
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Change password request schema"""
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str


@router.post("/login", response_model=LoginResponse)
def login(
    request: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Login endpoint with rate limiting (T086)

    Rate limit: 5 attempts per 15 minutes per username

    Args:
        request: Login credentials
        response: FastAPI response object for setting cookies
        db: Database session

    Returns:
        LoginResponse with access token and user data

    Raises:
        HTTPException: 401 if credentials invalid, 429 if rate limited
    """
    try:
        access_token, user_data, refresh_token = auth_service.login(
            db, request.username, request.password
        )

        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )

        # Set refresh token as httponly secure cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=7 * 24 * 60 * 60  # 7 days
        )

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            refresh_token=refresh_token,
            user=user_data
        )

    except ValueError as e:
        # Rate limit or validation error
        error_msg = str(e)
        if "Too many" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=error_msg
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )


@router.post("/logout", response_model=MessageResponse)
def logout(
    response: Response,
    current_user: dict = Depends(get_current_user)
):
    """
    Logout endpoint (T087)

    Clears refresh token cookie

    Args:
        response: FastAPI response object
        current_user: Current authenticated user

    Returns:
        MessageResponse confirming logout
    """
    username = current_user.get("username")

    # Clear refresh token cookie
    response.delete_cookie(key="refresh_token")

    # Call logout service
    auth_service.logout(username)

    return MessageResponse(message="Successfully logged out")


@router.post("/refresh", response_model=RefreshResponse)
def refresh_token(
    response: Response,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Refresh access token endpoint (T088)

    Rotates both access and refresh tokens

    Args:
        response: FastAPI response object for setting new refresh cookie
        credentials: Current access token

    Returns:
        RefreshResponse with new access and refresh tokens

    Raises:
        HTTPException: 401 if token invalid
    """
    token = credentials.credentials

    # Verify current token
    payload = verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    # Extract user info
    username = payload.get("sub")
    user_id = payload.get("user_id")
    role = payload.get("role")

    if not all([username, user_id, role]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    # Generate new tokens
    new_access_token, new_refresh_token = auth_service.refresh_access_token(
        username, user_id, role
    )

    # Set new refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60
    )

    return RefreshResponse(
        access_token=new_access_token,
        token_type="bearer",
        refresh_token=new_refresh_token
    )


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Change password endpoint (T089)

    Args:
        request: Old and new passwords
        db: Database session
        current_user: Current authenticated user

    Returns:
        MessageResponse confirming password change

    Raises:
        HTTPException: 401 if old password wrong, 400 if new password weak
    """
    user_id = current_user.get("user_id")

    try:
        auth_service.change_password(
            db, user_id, request.old_password, request.new_password
        )

        return MessageResponse(message="Password changed successfully")

    except ValueError as e:
        error_msg = str(e)

        if "incorrect" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_msg
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
