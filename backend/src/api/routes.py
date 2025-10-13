"""
Base API router structure
"""
from fastapi import APIRouter
from src.api.devices import router as devices_router
from src.api.auth import router as auth_router
from src.api.users import router as users_router

# Create main API router
api_router = APIRouter(prefix="/api")

# Include device routes (User Story 1)
api_router.include_router(devices_router)

# Include auth and user routes (User Story 3)
api_router.include_router(auth_router)
api_router.include_router(users_router)

# Placeholder for sub-routers to be added later:
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
