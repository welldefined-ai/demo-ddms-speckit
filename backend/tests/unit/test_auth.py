"""
Unit tests for authentication utilities
"""
import pytest
from datetime import timedelta
from src.utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token,
)


class TestPasswordHashing:
    """Test password hashing and verification"""

    def test_hash_password_creates_hash(self):
        """Test that password hashing creates a non-empty hash"""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        assert hashed is not None
        assert len(hashed) > 0
        assert hashed != password

    def test_hash_password_creates_different_hashes(self):
        """Test that same password creates different hashes (due to salt)"""
        password = "SecurePassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "SecurePassword123!"
        wrong_password = "WrongPassword456!"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_string(self):
        """Test password verification with empty password"""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        assert verify_password("", hashed) is False


class TestJWTTokens:
    """Test JWT token creation and verification"""

    def test_create_access_token_with_data(self):
        """Test creating JWT token with user data"""
        data = {"sub": "testuser", "role": "admin"}
        token = create_access_token(data)

        assert token is not None
        assert len(token) > 0
        assert isinstance(token, str)

    def test_create_access_token_with_custom_expiry(self):
        """Test creating JWT token with custom expiration"""
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=15)
        token = create_access_token(data, expires_delta=expires_delta)

        assert token is not None
        assert len(token) > 0

    def test_verify_token_valid(self):
        """Test verifying a valid JWT token"""
        data = {"sub": "testuser", "role": "admin"}
        token = create_access_token(data)

        payload = verify_token(token)

        assert payload is not None
        assert payload["sub"] == "testuser"
        assert payload["role"] == "admin"
        assert "exp" in payload
        assert "iat" in payload

    def test_verify_token_invalid(self):
        """Test verifying an invalid JWT token"""
        invalid_token = "invalid.jwt.token"

        payload = verify_token(invalid_token)

        assert payload is None

    def test_verify_token_malformed(self):
        """Test verifying a malformed token"""
        malformed_token = "this-is-not-a-valid-token"

        payload = verify_token(malformed_token)

        assert payload is None

    def test_token_contains_expiration(self):
        """Test that token contains expiration claim"""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        payload = verify_token(token)

        assert payload is not None
        assert "exp" in payload
        assert payload["exp"] > 0

    def test_token_contains_issued_at(self):
        """Test that token contains issued-at claim"""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        payload = verify_token(token)

        assert payload is not None
        assert "iat" in payload
        assert payload["iat"] > 0


class TestAuthenticationIntegration:
    """Integration tests for full authentication flow"""

    def test_full_password_flow(self):
        """Test complete password hash and verify flow"""
        original_password = "MySecurePassword123!"

        # Hash password
        hashed = hash_password(original_password)

        # Verify correct password
        assert verify_password(original_password, hashed) is True

        # Verify incorrect password
        assert verify_password("WrongPassword", hashed) is False

    def test_full_token_flow(self):
        """Test complete token creation and verification flow"""
        user_data = {
            "sub": "testuser",
            "role": "admin",
            "user_id": "123e4567-e89b-12d3-a456-426614174000"
        }

        # Create token
        token = create_access_token(user_data)

        # Verify token
        payload = verify_token(token)

        # Validate all data is preserved
        assert payload is not None
        assert payload["sub"] == user_data["sub"]
        assert payload["role"] == user_data["role"]
        assert payload["user_id"] == user_data["user_id"]
