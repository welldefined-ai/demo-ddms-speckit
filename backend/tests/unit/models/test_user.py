"""
Unit tests for User model
"""
import pytest
import uuid
from sqlalchemy.exc import IntegrityError
from src.models.user import User, UserRole


class TestUserModel:
    """Test User model functionality"""

    def test_create_user(self, db_session):
        """Test creating a user"""
        user = User(
            id=uuid.uuid4(),
            username="testuser",
            password_hash="hashed_password",
            role=UserRole.ADMIN,
            language_preference="en"
        )

        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.username == "testuser"
        assert user.role == UserRole.ADMIN
        assert user.language_preference == "en"
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_unique_username(self, db_session):
        """Test that username must be unique"""
        user1 = User(
            id=uuid.uuid4(),
            username="testuser",
            password_hash="hashed_password",
            role=UserRole.ADMIN
        )
        db_session.add(user1)
        db_session.commit()

        # Attempt to create second user with same username
        user2 = User(
            id=uuid.uuid4(),
            username="testuser",
            password_hash="another_hash",
            role=UserRole.READ_ONLY
        )
        db_session.add(user2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_user_default_language(self, db_session):
        """Test default language preference"""
        user = User(
            id=uuid.uuid4(),
            username="testuser",
            password_hash="hashed_password",
            role=UserRole.ADMIN
        )

        db_session.add(user)
        db_session.commit()

        assert user.language_preference == "en"

    def test_user_role_enum(self, db_session):
        """Test that user roles use enum"""
        owner = User(
            id=uuid.uuid4(),
            username="owner",
            password_hash="hash",
            role=UserRole.OWNER
        )

        admin = User(
            id=uuid.uuid4(),
            username="admin",
            password_hash="hash",
            role=UserRole.ADMIN
        )

        readonly = User(
            id=uuid.uuid4(),
            username="readonly",
            password_hash="hash",
            role=UserRole.READ_ONLY
        )

        db_session.add_all([owner, admin, readonly])
        db_session.commit()

        assert owner.role == UserRole.OWNER
        assert admin.role == UserRole.ADMIN
        assert readonly.role == UserRole.READ_ONLY

    def test_user_repr(self, db_session):
        """Test user string representation"""
        user = User(
            id=uuid.uuid4(),
            username="testuser",
            password_hash="hashed_password",
            role=UserRole.ADMIN
        )

        db_session.add(user)
        db_session.commit()

        repr_str = repr(user)
        assert "User" in repr_str
        assert "testuser" in repr_str
        assert "admin" in repr_str
