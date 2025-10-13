"""
Group model for organizing devices
"""
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.db.base import Base


class Group(Base):
    """
    Group model for device organization

    Fields:
    - id: UUID primary key
    - name: Unique group name
    - description: Optional group description
    - created_at: Group creation timestamp
    - updated_at: Last update timestamp
    """
    __tablename__ = "groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<Group(id={self.id}, name={self.name})>"
