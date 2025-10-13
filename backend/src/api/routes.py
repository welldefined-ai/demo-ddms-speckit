"""
Base API router structure
"""
from fastapi import APIRouter
from src.api.devices import router as devices_router

# Create main API router
api_router = APIRouter(prefix="/api")

# Include device routes (User Story 1)
api_router.include_router(devices_router)

# Placeholder for sub-routers to be added later:
# - auth_router (POST /api/auth/login, /api/auth/logout, etc.)
# - users_router (GET/POST /api/users, etc.)
# - readings_router (GET /api/readings/{device_id}, etc.)
# - groups_router (GET/POST/PUT/DELETE /api/groups, etc.)
# - export_router (GET /api/export/device/{device_id}, etc.)
# - system_router (GET /api/system/health, /api/system/config, etc.)


def include_routers():
    """
    Include all sub-routers into the main API router

    This function will be called during app initialization
    to register all API routes
    """
    # Routers are already included above
    pass
