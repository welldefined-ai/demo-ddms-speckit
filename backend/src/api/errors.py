"""
Error response schemas and exception handlers
"""
from typing import Optional, Dict, Any
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError, OperationalError


class ErrorResponse(BaseModel):
    """Standard error response schema"""
    error: str
    detail: Optional[str] = None
    status_code: int


class ValidationErrorResponse(BaseModel):
    """Validation error response schema"""
    error: str
    detail: str
    validation_errors: list
    status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle Pydantic validation errors

    Args:
        request: FastAPI request object
        exc: Validation exception

    Returns:
        JSON response with validation error details
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": "Invalid request data",
            "validation_errors": exc.errors(),
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
        },
    )


async def integrity_exception_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """
    Handle SQLAlchemy integrity errors (unique constraints, foreign keys, etc.)

    Args:
        request: FastAPI request object
        exc: Integrity exception

    Returns:
        JSON response with error details
    """
    # Extract constraint name if available
    detail = str(exc.orig) if hasattr(exc, 'orig') else str(exc)

    # Customize message based on constraint type
    if "unique" in detail.lower():
        error_message = "Duplicate entry"
        detail_message = "A record with this value already exists"
    elif "foreign key" in detail.lower():
        error_message = "Invalid reference"
        detail_message = "Referenced record does not exist"
    else:
        error_message = "Database constraint violation"
        detail_message = detail

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": error_message,
            "detail": detail_message,
            "status_code": status.HTTP_409_CONFLICT,
        },
    )


async def operational_exception_handler(request: Request, exc: OperationalError) -> JSONResponse:
    """
    Handle SQLAlchemy operational errors (connection issues, etc.)

    Args:
        request: FastAPI request object
        exc: Operational exception

    Returns:
        JSON response with error details
    """
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": "Database Unavailable",
            "detail": "Unable to connect to database",
            "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle generic exceptions

    Args:
        request: FastAPI request object
        exc: Exception

    Returns:
        JSON response with error details
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        },
    )


def create_error_response(
    error: str,
    detail: Optional[str] = None,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
) -> Dict[str, Any]:
    """
    Create a standardized error response dictionary

    Args:
        error: Error message
        detail: Additional error details
        status_code: HTTP status code

    Returns:
        Dictionary with error information
    """
    return {
        "error": error,
        "detail": detail,
        "status_code": status_code,
    }
