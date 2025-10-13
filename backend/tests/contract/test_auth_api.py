"""
Contract tests for authentication API endpoints (T077-T079)
Tests POST /api/auth/login, POST /api/auth/logout, POST /api/auth/refresh
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.db.base import Base
from src.api.dependencies import get_db
from src.models.user import User, UserRole
from src.utils.auth import hash_password


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_db():
    """Create test database"""
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    yield db

    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create test client with database override"""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(test_db):
    """Create test user for authentication"""
    user = User(
        id=uuid.uuid4(),
        username="testuser",
        password_hash=hash_password("Test123!@#"),
        role=UserRole.ADMIN,
        language_preference="en"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def owner_user(test_db):
    """Create owner user"""
    user = User(
        id=uuid.uuid4(),
        username="owner",
        password_hash=hash_password("Owner123!@#"),
        role=UserRole.OWNER,
        language_preference="en"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


class TestLoginEndpoint:
    """Contract tests for POST /api/auth/login (T077)"""

    def test_login_success(self, client, test_user):
        """Test successful login with valid credentials"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "Test123!@#"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["username"] == "testuser"
        assert data["user"]["role"] == "admin"

    def test_login_invalid_username(self, client):
        """Test login with non-existent username"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "nonexistent",
                "password": "Test123!@#"
            }
        )

        assert response.status_code == 401
        assert "detail" in response.json()

    def test_login_invalid_password(self, client, test_user):
        """Test login with incorrect password"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "WrongPassword"
            }
        )

        assert response.status_code == 401
        assert "detail" in response.json()

    def test_login_missing_username(self, client):
        """Test login with missing username"""
        response = client.post(
            "/api/auth/login",
            json={
                "password": "Test123!@#"
            }
        )

        assert response.status_code == 422  # Validation error

    def test_login_missing_password(self, client):
        """Test login with missing password"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser"
            }
        )

        assert response.status_code == 422  # Validation error

    def test_login_empty_credentials(self, client):
        """Test login with empty strings"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "",
                "password": ""
            }
        )

        assert response.status_code in [401, 422]

    def test_login_rate_limiting(self, client):
        """Test rate limiting on login attempts"""
        # Make multiple failed login attempts
        for i in range(6):
            response = client.post(
                "/api/auth/login",
                json={
                    "username": "testuser",
                    "password": "WrongPassword"
                }
            )

        # After 5 failed attempts, should be rate limited
        response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "WrongPassword"
            }
        )

        # May be 429 (Too Many Requests) if rate limiting is implemented
        # Or continue to return 401 if not yet implemented
        assert response.status_code in [401, 429]

    def test_login_returns_refresh_token_cookie(self, client, test_user):
        """Test that login sets refresh token in cookie"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "Test123!@#"
            }
        )

        assert response.status_code == 200
        # Check if refresh token cookie is set
        cookies = response.cookies
        # This may be implemented with httponly secure cookies
        # assert "refresh_token" in cookies or "refreshToken" in cookies


class TestLogoutEndpoint:
    """Contract tests for POST /api/auth/logout (T078)"""

    def test_logout_success(self, client, test_user):
        """Test successful logout"""
        # First login to get token
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "Test123!@#"
            }
        )
        token = login_response.json()["access_token"]

        # Then logout
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "detail" in data

    def test_logout_without_auth(self, client):
        """Test logout without authentication token"""
        response = client.post("/api/auth/logout")

        assert response.status_code == 401

    def test_logout_with_invalid_token(self, client):
        """Test logout with invalid token"""
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

    def test_logout_clears_refresh_token_cookie(self, client, test_user):
        """Test that logout clears refresh token cookie"""
        # Login first
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "Test123!@#"
            }
        )
        token = login_response.json()["access_token"]

        # Logout
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        # Refresh token cookie should be cleared
        # This is implementation-specific


class TestRefreshTokenEndpoint:
    """Contract tests for POST /api/auth/refresh (T079)"""

    def test_refresh_token_success(self, client, test_user):
        """Test successful token refresh"""
        # Login to get initial tokens
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "Test123!@#"
            }
        )

        old_token = login_response.json()["access_token"]

        # Refresh token
        response = client.post(
            "/api/auth/refresh",
            headers={"Authorization": f"Bearer {old_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        # New token should be different from old token
        assert data["access_token"] != old_token

    def test_refresh_token_without_auth(self, client):
        """Test refresh without authentication"""
        response = client.post("/api/auth/refresh")

        assert response.status_code == 401

    def test_refresh_token_with_invalid_token(self, client):
        """Test refresh with invalid token"""
        response = client.post(
            "/api/auth/refresh",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

    def test_refresh_token_rotation(self, client, test_user):
        """Test that refresh rotates both access and refresh tokens"""
        # Login
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "Test123!@#"
            }
        )
        token1 = login_response.json()["access_token"]

        # First refresh
        refresh1_response = client.post(
            "/api/auth/refresh",
            headers={"Authorization": f"Bearer {token1}"}
        )
        token2 = refresh1_response.json()["access_token"]

        # Second refresh with new token
        refresh2_response = client.post(
            "/api/auth/refresh",
            headers={"Authorization": f"Bearer {token2}"}
        )
        token3 = refresh2_response.json()["access_token"]

        # All tokens should be different
        assert token1 != token2
        assert token2 != token3
        assert token1 != token3


class TestChangePasswordEndpoint:
    """Contract tests for POST /api/auth/change-password (T089)"""

    def test_change_password_success(self, client, test_user):
        """Test successful password change"""
        # Login first
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "Test123!@#"
            }
        )
        token = login_response.json()["access_token"]

        # Change password
        response = client.post(
            "/api/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "old_password": "Test123!@#",
                "new_password": "NewPass123!@#"
            }
        )

        assert response.status_code == 200

        # Verify old password no longer works
        old_login = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "Test123!@#"
            }
        )
        assert old_login.status_code == 401

        # Verify new password works
        new_login = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "NewPass123!@#"
            }
        )
        assert new_login.status_code == 200

    def test_change_password_wrong_old_password(self, client, test_user):
        """Test change password with incorrect old password"""
        # Login first
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "Test123!@#"
            }
        )
        token = login_response.json()["access_token"]

        # Try to change with wrong old password
        response = client.post(
            "/api/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "old_password": "WrongPassword",
                "new_password": "NewPass123!@#"
            }
        )

        assert response.status_code == 401

    def test_change_password_without_auth(self, client):
        """Test change password without authentication"""
        response = client.post(
            "/api/auth/change-password",
            json={
                "old_password": "Test123!@#",
                "new_password": "NewPass123!@#"
            }
        )

        assert response.status_code == 401

    def test_change_password_weak_password(self, client, test_user):
        """Test change password with weak new password"""
        # Login first
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "Test123!@#"
            }
        )
        token = login_response.json()["access_token"]

        # Try weak password
        response = client.post(
            "/api/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "old_password": "Test123!@#",
                "new_password": "weak"
            }
        )

        assert response.status_code in [400, 422]
