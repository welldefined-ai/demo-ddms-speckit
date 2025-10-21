"""
Database models package

Import all models here to ensure they are registered with SQLAlchemy
and available for Alembic migrations.
"""
from src.models.user import User, UserRole
from src.models.device import Device, DeviceStatus
from src.models.reading import Reading
from src.models.group import Group
from src.models.device_group import DeviceGroup
from src.models.configuration import Configuration
from src.models.notification import Notification, NotificationType, NotificationSeverity

__all__ = [
    "User",
    "UserRole",
    "Device",
    "DeviceStatus",
    "Reading",
    "Group",
    "DeviceGroup",
    "Configuration",
    "Notification",
    "NotificationType",
    "NotificationSeverity",
]
