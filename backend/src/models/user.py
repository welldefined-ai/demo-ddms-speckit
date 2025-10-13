"""
User model for authentication and authorization
"""
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Enum, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.db.base import Base


class UserRole(PyEnum):
    """User role enumeration"""
    OWNER = "owner"
    ADMIN = "admin"
    READ_ONLY = "read_only"


class User(Base):
    """
    User model for authentication and RBAC

    Fields:
    - id: UUID primary key
    - username: Unique username for login
    - password_hash: Bcrypt hashed password
    - role: UserRole enum (owner/admin/read_only)
    - language_preference: Two-letter language code (en/zh)
    - created_at: Timestamp of account creation
    - updated_at: Timestamp of last update
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    language_preference = Column(String(2), default="en", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, role={self.role.value})>"
