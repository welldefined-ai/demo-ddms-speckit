"""
FastAPI application setup with middleware and configuration
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, OperationalError
import time

from src.api.routes import api_router, include_routers
from src.api.errors import (
    validation_exception_handler,
    integrity_exception_handler,
    operational_exception_handler,
    generic_exception_handler,
)
from src.db.session import init_db
from src.utils.logging import get_logger, setup_logging
from src.utils.metrics import get_metrics, record_api_request, set_system_health

# Setup logging
log_level = os.environ.get("LOG_LEVEL", "INFO")
setup_logging(log_level)
logger = get_logger("ddms")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager

    Handles startup and shutdown events
    """
    # Startup
    logger.info("Starting DDMS application")
    try:
        init_db()
        set_system_health(True)
        logger.info("Database connection initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        set_system_health(False)
        raise

    yield

    # Shutdown
    logger.info("Shutting down DDMS application")


# Create FastAPI application
app = FastAPI(
    title="DDMS API",
    description="Device Data Monitoring System - REST API",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware to log all requests and collect metrics

    Args:
        request: FastAPI request
        call_next: Next middleware/route handler

    Returns:
        Response from downstream handlers
    """
    start_time = time.time()

    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time.time() - start_time

    # Record metrics
    record_api_request(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code,
        duration=duration
    )

    # Log response
    logger.info(
        f"Response: {request.method} {request.url.path} - "
        f"Status: {response.status_code} - Duration: {duration:.3f}s"
    )

    return response


# Register exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(IntegrityError, integrity_exception_handler)
app.add_exception_handler(OperationalError, operational_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include API routers
include_routers()
app.include_router(api_router)


# Prometheus metrics endpoint
@app.get("/metrics", include_in_schema=False)
async def metrics():
    """
    Prometheus metrics endpoint

    Returns metrics in Prometheus text format
    """
    return Response(content=get_metrics(), media_type="text/plain")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "DDMS API",
        "version": "1.0.0",
        "status": "online"
    }
