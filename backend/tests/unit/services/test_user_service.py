"""
Unit tests for user management service (T101)
"""
import pytest
import uuid
from unittest.mock import patch

from src.services import user_service
from src.models.user import User, UserRole
from src.utils.auth import hash_password, verify_password


@pytest.fixture
def owner_user(db_session):
    """Create an owner user"""
    user = User(
        id=uuid.uuid4(),
        username="owner",
        password_hash=hash_password("Owner123!"),
        role=UserRole.OWNER,
        language_preference="en"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session):
    """Create an admin user"""
    user = User(
        id=uuid.uuid4(),
        username="admin",
        password_hash=hash_password("Admin123!"),
        role=UserRole.ADMIN,
        language_preference="en"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def readonly_user(db_session):
    """Create a read-only user"""
    user = User(
        id=uuid.uuid4(),
        username="readonly",
        password_hash=hash_password("Read123!"),
        role=UserRole.READ_ONLY,
        language_preference="zh"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestCreateUser:
    """Test create_user function"""

    def test_create_user_success(self, db_session):
        """Test successful user creation"""
        user = user_service.create_user(
            db_session,
            username="newuser",
            password="NewUser123!",
            role="admin",
            language_preference="en"
        )

        assert user.id is not None
        assert user.username == "newuser"
        assert user.role == UserRole.ADMIN
        assert user.language_preference == "en"
        assert verify_password("NewUser123!", user.password_hash)

    def test_create_user_with_chinese_language(self, db_session):
        """Test creating user with Chinese language preference"""
        user = user_service.create_user(
            db_session,
            username="chinese_user",
            password="ChineseUser123!",
            role="admin",
            language_preference="zh"
        )

        assert user.language_preference == "zh"

    def test_create_read_only_user(self, db_session):
        """Test creating read-only user"""
        user = user_service.create_user(
            db_session,
            username="readonly",
            password="ReadOnly123!",
            role="read_only",
            language_preference="en"
        )

        assert user.role == UserRole.READ_ONLY

    def test_cannot_create_owner_role(self, db_session):
        """Test that creating owner role is not allowed"""
        with pytest.raises(ValueError, match="Cannot create additional owner accounts"):
            user_service.create_user(
                db_session,
                username="newowner",
                password="Owner123!",
                role="owner",
                language_preference="en"
            )

    def test_duplicate_username_fails(self, db_session, admin_user):
        """Test that duplicate username fails"""
        with pytest.raises(ValueError, match="already exists"):
            user_service.create_user(
                db_session,
                username="admin",  # Same as admin_user
                password="NewPass123!",
                role="admin",
                language_preference="en"
            )

    def test_invalid_role_fails(self, db_session):
        """Test that invalid role fails"""
        with pytest.raises(ValueError, match="Invalid role"):
            user_service.create_user(
                db_session,
                username="newuser",
                password="NewUser123!",
                role="invalid_role",
                language_preference="en"
            )

    def test_invalid_language_fails(self, db_session):
        """Test that invalid language preference fails"""
        with pytest.raises(ValueError, match="Language preference must be"):
            user_service.create_user(
                db_session,
                username="newuser",
                password="NewUser123!",
                role="admin",
                language_preference="fr"  # Not supported
            )

    def test_weak_password_fails(self, db_session):
        """Test that weak password fails"""
        # Too short
        with pytest.raises(ValueError, match="at least 8 characters"):
            user_service.create_user(
                db_session,
                username="newuser",
                password="Short1!",
                role="admin",
                language_preference="en"
            )

        # Missing uppercase
        with pytest.raises(ValueError, match="uppercase"):
            user_service.create_user(
                db_session,
                username="newuser",
                password="lowercase123!",
                role="admin",
                language_preference="en"
            )

    def test_default_language_preference(self, db_session):
        """Test default language preference is 'en'"""
        user = user_service.create_user(
            db_session,
            username="newuser",
            password="NewUser123!",
            role="admin"
            # language_preference not specified
        )

        assert user.language_preference == "en"


class TestGetUserById:
    """Test get_user_by_id function"""

    def test_get_existing_user(self, db_session, admin_user):
        """Test getting existing user by ID"""
        user = user_service.get_user_by_id(db_session, admin_user.id)

        assert user is not None
        assert user.id == admin_user.id
        assert user.username == admin_user.username

    def test_get_nonexistent_user(self, db_session):
        """Test getting non-existent user returns None"""
        fake_id = uuid.uuid4()
        user = user_service.get_user_by_id(db_session, fake_id)

        assert user is None


class TestGetUserByUsername:
    """Test get_user_by_username function"""

    def test_get_existing_user(self, db_session, admin_user):
        """Test getting existing user by username"""
        user = user_service.get_user_by_username(db_session, "admin")

        assert user is not None
        assert user.username == "admin"
        assert user.id == admin_user.id

    def test_get_nonexistent_user(self, db_session):
        """Test getting non-existent user returns None"""
        user = user_service.get_user_by_username(db_session, "nonexistent")

        assert user is None

    def test_username_case_sensitive(self, db_session, admin_user):
        """Test that username lookup is case-sensitive"""
        user = user_service.get_user_by_username(db_session, "ADMIN")

        # Should not find user (case-sensitive)
        assert user is None


class TestListUsers:
    """Test list_users function"""

    def test_list_all_users(self, db_session, owner_user, admin_user, readonly_user):
        """Test listing all users"""
        users = user_service.list_users(db_session)

        assert len(users) == 3
        usernames = [u.username for u in users]
        assert "owner" in usernames
        assert "admin" in usernames
        assert "readonly" in usernames

    def test_list_empty(self, db_session):
        """Test listing users when none exist"""
        users = user_service.list_users(db_session)

        assert len(users) == 0

    def test_list_ordered_by_created_at(self, db_session):
        """Test that users are ordered by creation time"""
        # Create users in specific order
        user1 = user_service.create_user(
            db_session, "user1", "User1Pass123!", "admin", "en"
        )
        user2 = user_service.create_user(
            db_session, "user2", "User2Pass123!", "admin", "en"
        )
        user3 = user_service.create_user(
            db_session, "user3", "User3Pass123!", "read_only", "en"
        )

        users = user_service.list_users(db_session)

        # Should be in creation order
        assert users[0].username == "user1"
        assert users[1].username == "user2"
        assert users[2].username == "user3"


class TestDeleteUser:
    """Test delete_user function"""

    def test_owner_can_delete_admin(self, db_session, owner_user, admin_user):
        """Test that owner can delete admin user"""
        result = user_service.delete_user(
            db_session,
            admin_user.id,
            requesting_user_role="owner"
        )

        assert result is True

        # Verify user is deleted
        user = user_service.get_user_by_id(db_session, admin_user.id)
        assert user is None

    def test_owner_can_delete_readonly(self, db_session, owner_user, readonly_user):
        """Test that owner can delete read-only user"""
        result = user_service.delete_user(
            db_session,
            readonly_user.id,
            requesting_user_role="owner"
        )

        assert result is True

    def test_cannot_delete_owner(self, db_session, owner_user):
        """Test that owner cannot be deleted"""
        with pytest.raises(ValueError, match="Cannot delete owner account"):
            user_service.delete_user(
                db_session,
                owner_user.id,
                requesting_user_role="owner"
            )

    def test_non_owner_cannot_delete(self, db_session, admin_user, readonly_user):
        """Test that non-owner cannot delete users"""
        with pytest.raises(ValueError, match="Only owner can delete users"):
            user_service.delete_user(
                db_session,
                readonly_user.id,
                requesting_user_role="admin"
            )

    def test_delete_nonexistent_user(self, db_session, owner_user):
        """Test deleting non-existent user"""
        fake_id = uuid.uuid4()

        with pytest.raises(ValueError, match="User not found"):
            user_service.delete_user(
                db_session,
                fake_id,
                requesting_user_role="owner"
            )


class TestUpdateUserLanguage:
    """Test update_user_language function"""

    def test_update_to_english(self, db_session, readonly_user):
        """Test updating language to English"""
        # readonly_user starts with 'zh'
        assert readonly_user.language_preference == "zh"

        user = user_service.update_user_language(
            db_session,
            readonly_user.id,
            "en"
        )

        assert user.language_preference == "en"

    def test_update_to_chinese(self, db_session, admin_user):
        """Test updating language to Chinese"""
        # admin_user starts with 'en'
        assert admin_user.language_preference == "en"

        user = user_service.update_user_language(
            db_session,
            admin_user.id,
            "zh"
        )

        assert user.language_preference == "zh"

    def test_invalid_language_fails(self, db_session, admin_user):
        """Test that invalid language fails"""
        with pytest.raises(ValueError, match="Language preference must be"):
            user_service.update_user_language(
                db_session,
                admin_user.id,
                "fr"  # Not supported
            )

    def test_user_not_found(self, db_session):
        """Test updating language for non-existent user"""
        fake_id = uuid.uuid4()

        with pytest.raises(ValueError, match="User not found"):
            user_service.update_user_language(
                db_session,
                fake_id,
                "zh"
            )


class TestGetUserCountByRole:
    """Test get_user_count_by_role function"""

    def test_count_all_roles(self, db_session, owner_user, admin_user, readonly_user):
        """Test counting users by role"""
        counts = user_service.get_user_count_by_role(db_session)

        assert counts["owner"] == 1
        assert counts["admin"] == 1
        assert counts["read_only"] == 1

    def test_count_with_multiple_same_role(self, db_session, owner_user):
        """Test counting with multiple users of same role"""
        # Create multiple admin users
        user_service.create_user(db_session, "admin1", "Admin123!", "admin", "en")
        user_service.create_user(db_session, "admin2", "Admin123!", "admin", "en")

        counts = user_service.get_user_count_by_role(db_session)

        assert counts["owner"] == 1
        assert counts["admin"] == 2
        assert counts["read_only"] == 0

    def test_count_empty(self, db_session):
        """Test counting when no users exist"""
        counts = user_service.get_user_count_by_role(db_session)

        assert counts["owner"] == 0
        assert counts["admin"] == 0
        assert counts["read_only"] == 0


class TestValidateUsername:
    """Test validate_username function"""

    def test_valid_usernames(self):
        """Test validation of valid usernames"""
        valid_usernames = [
            "user",
            "user123",
            "user_name",
            "test_user_123",
            "a" * 50  # Max length
        ]

        for username in valid_usernames:
            is_valid, error = user_service.validate_username(username)
            assert is_valid is True, f"Username '{username}' should be valid"
            assert error is None

    def test_empty_username(self):
        """Test empty username fails"""
        is_valid, error = user_service.validate_username("")
        assert is_valid is False
        assert "required" in error

    def test_too_short_username(self):
        """Test username too short"""
        is_valid, error = user_service.validate_username("ab")
        assert is_valid is False
        assert "at least 3 characters" in error

    def test_too_long_username(self):
        """Test username too long"""
        is_valid, error = user_service.validate_username("a" * 51)
        assert is_valid is False
        assert "at most 50 characters" in error

    def test_invalid_characters(self):
        """Test username with invalid characters"""
        invalid_usernames = [
            "user name",  # Space
            "user-name",  # Hyphen
            "user.name",  # Dot
            "user@name",  # Special chars
            "用户名",      # Non-ASCII
        ]

        for username in invalid_usernames:
            is_valid, error = user_service.validate_username(username)
            assert is_valid is False, f"Username '{username}' should be invalid"
            assert "letters, numbers, and underscores" in error

    def test_alphanumeric_with_underscore(self):
        """Test that alphanumeric with underscore is valid"""
        is_valid, error = user_service.validate_username("user_123")
        assert is_valid is True
        assert error is None
