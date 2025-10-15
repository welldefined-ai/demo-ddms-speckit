"""
Unit tests for authentication service (T100)
"""
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.services import auth_service
from src.models.user import User, UserRole
from src.utils.auth import hash_password


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user = User(
        id=uuid.uuid4(),
        username="testuser",
        password_hash=hash_password("Test123!@#"),
        role=UserRole.ADMIN,
        language_preference="en"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(autouse=True)
def clear_rate_limit():
    """Clear rate limit storage before each test"""
    auth_service.login_attempts.clear()
    yield
    auth_service.login_attempts.clear()


class TestCheckRateLimit:
    """Test check_rate_limit function"""

    def test_allows_first_attempt(self):
        """Test that first attempt is allowed"""
        is_allowed, seconds = auth_service.check_rate_limit("testuser")
        assert is_allowed is True
        assert seconds is None

    def test_allows_within_limit(self):
        """Test that attempts within limit are allowed"""
        username = "testuser"

        # Record 4 attempts (under limit of 5)
        for _ in range(4):
            auth_service.record_login_attempt(username)

        is_allowed, seconds = auth_service.check_rate_limit(username)
        assert is_allowed is True
        assert seconds is None

    def test_blocks_at_limit(self):
        """Test that rate limit blocks after max attempts"""
        username = "testuser"

        # Record 5 attempts (at limit)
        for _ in range(5):
            auth_service.record_login_attempt(username)

        is_allowed, seconds = auth_service.check_rate_limit(username)
        assert is_allowed is False
        assert seconds is not None
        assert seconds > 0
        assert seconds <= auth_service.RATE_LIMIT_WINDOW_MINUTES * 60

    def test_cleans_old_attempts(self):
        """Test that old attempts are cleaned up"""
        username = "testuser"

        # Add old attempts (16 minutes ago - outside window)
        old_time = datetime.utcnow() - timedelta(minutes=16)
        auth_service.login_attempts[username] = [old_time] * 5

        # Should be allowed now (old attempts cleaned)
        is_allowed, seconds = auth_service.check_rate_limit(username)
        assert is_allowed is True
        assert seconds is None

    def test_different_users_independent(self):
        """Test that rate limits are per-user"""
        # Max out user1
        for _ in range(5):
            auth_service.record_login_attempt("user1")

        # User2 should still be allowed
        is_allowed, seconds = auth_service.check_rate_limit("user2")
        assert is_allowed is True
        assert seconds is None


class TestRecordLoginAttempt:
    """Test record_login_attempt function"""

    def test_records_attempt(self):
        """Test that attempt is recorded"""
        username = "testuser"
        auth_service.record_login_attempt(username)

        assert username in auth_service.login_attempts
        assert len(auth_service.login_attempts[username]) == 1

    def test_records_multiple_attempts(self):
        """Test recording multiple attempts"""
        username = "testuser"

        for _ in range(3):
            auth_service.record_login_attempt(username)

        assert len(auth_service.login_attempts[username]) == 3


class TestClearLoginAttempts:
    """Test clear_login_attempts function"""

    def test_clears_attempts(self):
        """Test that attempts are cleared"""
        username = "testuser"

        # Record some attempts
        for _ in range(3):
            auth_service.record_login_attempt(username)

        # Clear attempts
        auth_service.clear_login_attempts(username)

        assert username not in auth_service.login_attempts

    def test_clears_only_specified_user(self):
        """Test that only specified user's attempts are cleared"""
        # Record attempts for multiple users
        auth_service.record_login_attempt("user1")
        auth_service.record_login_attempt("user2")

        # Clear user1 only
        auth_service.clear_login_attempts("user1")

        assert "user1" not in auth_service.login_attempts
        assert "user2" in auth_service.login_attempts


class TestAuthenticateUser:
    """Test authenticate_user function"""

    def test_successful_authentication(self, db_session, test_user):
        """Test successful user authentication"""
        user = auth_service.authenticate_user(db_session, "testuser", "Test123!@#")

        assert user is not None
        assert user.username == "testuser"
        assert user.role == UserRole.ADMIN

    def test_wrong_password(self, db_session, test_user):
        """Test authentication with wrong password"""
        user = auth_service.authenticate_user(db_session, "testuser", "WrongPassword")

        assert user is None

    def test_nonexistent_user(self, db_session):
        """Test authentication with non-existent user"""
        user = auth_service.authenticate_user(db_session, "nonexistent", "Password123!")

        assert user is None

    def test_clears_rate_limit_on_success(self, db_session, test_user):
        """Test that rate limit is cleared on successful login"""
        # Record some failed attempts
        auth_service.record_login_attempt("testuser")
        auth_service.record_login_attempt("testuser")

        # Successful login
        user = auth_service.authenticate_user(db_session, "testuser", "Test123!@#")

        assert user is not None
        assert "testuser" not in auth_service.login_attempts

    def test_records_failed_attempt(self, db_session, test_user):
        """Test that failed login is recorded"""
        auth_service.authenticate_user(db_session, "testuser", "WrongPassword")

        assert "testuser" in auth_service.login_attempts
        assert len(auth_service.login_attempts["testuser"]) == 1

    def test_rate_limit_exception(self, db_session, test_user):
        """Test that rate limit raises exception"""
        # Max out rate limit
        for _ in range(5):
            auth_service.record_login_attempt("testuser")

        with pytest.raises(ValueError, match="Too many failed login attempts"):
            auth_service.authenticate_user(db_session, "testuser", "Test123!@#")


class TestLogin:
    """Test login function"""

    def test_successful_login(self, db_session, test_user):
        """Test successful login returns tokens and user data"""
        access_token, user_data, refresh_token = auth_service.login(
            db_session, "testuser", "Test123!@#"
        )

        assert access_token is not None
        assert refresh_token is not None
        assert user_data is not None
        assert user_data["username"] == "testuser"
        assert user_data["role"] == "admin"
        assert "id" in user_data
        assert "language_preference" in user_data

    def test_failed_login_returns_none(self, db_session, test_user):
        """Test failed login returns None values"""
        access_token, user_data, refresh_token = auth_service.login(
            db_session, "testuser", "WrongPassword"
        )

        assert access_token is None
        assert user_data is None
        assert refresh_token is None

    def test_tokens_are_different(self, db_session, test_user):
        """Test that access and refresh tokens are different"""
        access_token, user_data, refresh_token = auth_service.login(
            db_session, "testuser", "Test123!@#"
        )

        assert access_token != refresh_token

    def test_refresh_token_has_type_claim(self, db_session, test_user):
        """Test that refresh token has 'type' claim"""
        from src.utils.auth import verify_token

        access_token, user_data, refresh_token = auth_service.login(
            db_session, "testuser", "Test123!@#"
        )

        refresh_payload = verify_token(refresh_token)
        assert refresh_payload is not None
        assert refresh_payload.get("type") == "refresh"

        # Access token should not have type claim
        access_payload = verify_token(access_token)
        assert access_payload is not None
        assert "type" not in access_payload or access_payload.get("type") is None


class TestLogout:
    """Test logout function"""

    def test_logout_success(self):
        """Test successful logout"""
        result = auth_service.logout("testuser")
        assert result is True

    def test_logout_logs_event(self):
        """Test that logout logs the event"""
        with patch('src.services.auth_service.logger') as mock_logger:
            auth_service.logout("testuser")
            mock_logger.info.assert_called_once()


class TestRefreshAccessToken:
    """Test refresh_access_token function"""

    def test_returns_new_tokens(self):
        """Test that new tokens are returned"""
        new_access, new_refresh = auth_service.refresh_access_token(
            username="testuser",
            user_id=str(uuid.uuid4()),
            role="admin"
        )

        assert new_access is not None
        assert new_refresh is not None
        assert new_access != new_refresh

    def test_tokens_are_valid(self):
        """Test that returned tokens are valid"""
        from src.utils.auth import verify_token

        user_id = str(uuid.uuid4())
        new_access, new_refresh = auth_service.refresh_access_token(
            username="testuser",
            user_id=user_id,
            role="admin"
        )

        # Verify access token
        access_payload = verify_token(new_access)
        assert access_payload is not None
        assert access_payload["sub"] == "testuser"
        assert access_payload["user_id"] == user_id
        assert access_payload["role"] == "admin"

        # Verify refresh token
        refresh_payload = verify_token(new_refresh)
        assert refresh_payload is not None
        assert refresh_payload["sub"] == "testuser"
        assert refresh_payload["type"] == "refresh"


class TestChangePassword:
    """Test change_password function"""

    def test_successful_password_change(self, db_session, test_user):
        """Test successful password change"""
        result = auth_service.change_password(
            db_session,
            str(test_user.id),
            "Test123!@#",
            "NewPass123!@#"
        )

        assert result is True

        # Verify new password works
        from src.utils.auth import verify_password
        db_session.refresh(test_user)
        assert verify_password("NewPass123!@#", test_user.password_hash)

    def test_wrong_old_password(self, db_session, test_user):
        """Test password change with wrong old password"""
        with pytest.raises(ValueError, match="Current password is incorrect"):
            auth_service.change_password(
                db_session,
                str(test_user.id),
                "WrongPassword",
                "NewPass123!@#"
            )

    def test_user_not_found(self, db_session):
        """Test password change for non-existent user"""
        fake_id = str(uuid.uuid4())

        with pytest.raises(ValueError, match="User not found"):
            auth_service.change_password(
                db_session,
                fake_id,
                "OldPass123!",
                "NewPass123!@#"
            )

    def test_weak_password_validation(self, db_session, test_user):
        """Test that weak passwords are rejected"""
        # Too short
        with pytest.raises(ValueError, match="at least 8 characters"):
            auth_service.change_password(
                db_session,
                str(test_user.id),
                "Test123!@#",
                "Short1!"
            )

        # Missing uppercase
        with pytest.raises(ValueError, match="uppercase"):
            auth_service.change_password(
                db_session,
                str(test_user.id),
                "Test123!@#",
                "noupperscase123!"
            )

        # Missing lowercase
        with pytest.raises(ValueError, match="lowercase"):
            auth_service.change_password(
                db_session,
                str(test_user.id),
                "Test123!@#",
                "NOLOWERCASE123!"
            )

        # Missing digit
        with pytest.raises(ValueError, match="digit"):
            auth_service.change_password(
                db_session,
                str(test_user.id),
                "Test123!@#",
                "NoDigits!@#"
            )

        # Missing special character
        with pytest.raises(ValueError, match="special character"):
            auth_service.change_password(
                db_session,
                str(test_user.id),
                "Test123!@#",
                "NoSpecial123"
            )


class TestValidatePasswordStrength:
    """Test validate_password_strength function"""

    def test_valid_password(self):
        """Test validation of valid password"""
        is_valid, error = auth_service.validate_password_strength("ValidPass123!")
        assert is_valid is True
        assert error is None

    def test_too_short(self):
        """Test password too short"""
        is_valid, error = auth_service.validate_password_strength("Short1!")
        assert is_valid is False
        assert "at least 8 characters" in error

    def test_missing_uppercase(self):
        """Test password missing uppercase"""
        is_valid, error = auth_service.validate_password_strength("lowercase123!")
        assert is_valid is False
        assert "uppercase" in error

    def test_missing_lowercase(self):
        """Test password missing lowercase"""
        is_valid, error = auth_service.validate_password_strength("UPPERCASE123!")
        assert is_valid is False
        assert "lowercase" in error

    def test_missing_digit(self):
        """Test password missing digit"""
        is_valid, error = auth_service.validate_password_strength("NoDigits!@#")
        assert is_valid is False
        assert "digit" in error

    def test_missing_special(self):
        """Test password missing special character"""
        is_valid, error = auth_service.validate_password_strength("NoSpecial123")
        assert is_valid is False
        assert "special character" in error

    def test_all_requirements_met(self):
        """Test password meeting all requirements"""
        valid_passwords = [
            "Password1!",
            "Test123!@#",
            "Str0ng&Pass",
            "C0mpl3x#Pwd"
        ]

        for password in valid_passwords:
            is_valid, error = auth_service.validate_password_strength(password)
            assert is_valid is True, f"Password '{password}' should be valid"
            assert error is None
