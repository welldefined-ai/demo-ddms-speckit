"""
Initialize default data for the database

Creates default owner account and system configuration
"""
import uuid
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from sqlalchemy.orm import Session
from src.db.session import SessionLocal
from src.models.user import User, UserRole
from src.models.configuration import Configuration
from src.utils.auth import hash_password
from src.utils.logging import get_logger

logger = get_logger("ddms.init")


def create_default_owner(db: Session) -> None:
    """
    Create default owner account if it doesn't exist

    Args:
        db: Database session
    """
    # Check if owner already exists
    existing_owner = db.query(User).filter(User.role == UserRole.OWNER).first()

    if existing_owner:
        logger.info("Default owner account already exists")
        return

    # Create default owner account
    default_owner = User(
        id=uuid.uuid4(),
        username="admin",
        password_hash=hash_password("admin123"),  # Default password - MUST be changed
        role=UserRole.OWNER,
        language_preference="en"
    )

    db.add(default_owner)
    db.commit()

    logger.info(
        "Created default owner account - Username: admin, Password: admin123 "
        "(IMPORTANT: Change this password immediately!)"
    )


def create_default_configuration(db: Session) -> None:
    """
    Create default system configuration if it doesn't exist

    Args:
        db: Database session
    """
    # Check if configuration already exists
    existing_config = db.query(Configuration).first()

    if existing_config:
        logger.info("System configuration already exists")
        return

    # Create default configuration
    default_config = Configuration(
        id=uuid.uuid4(),
        system_name="DDMS - Device Data Monitoring System",
        data_retention_days_default=90,
        backup_enabled=True,
        backup_schedule="0 2 * * *"  # Daily at 2 AM
    )

    db.add(default_config)
    db.commit()

    logger.info("Created default system configuration")


def init_default_data() -> None:
    """
    Initialize all default data

    This function should be called after running database migrations
    """
    logger.info("Initializing default data...")

    db = SessionLocal()
    try:
        create_default_owner(db)
        create_default_configuration(db)
        logger.info("Default data initialization complete")
    except Exception as e:
        logger.error(f"Failed to initialize default data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_default_data()
