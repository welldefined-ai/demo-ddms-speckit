"""
Contract tests for user management API endpoints (T080-T081)
Tests POST /api/users, GET /api/users, DELETE /api/users/{user_id}
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


@pytest.fixture
def admin_user(test_db):
    """Create admin user"""
    user = User(
        id=uuid.uuid4(),
        username="admin",
        password_hash=hash_password("Admin123!@#"),
        role=UserRole.ADMIN,
        language_preference="en"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def readonly_user(test_db):
    """Create read-only user"""
    user = User(
        id=uuid.uuid4(),
        username="readonly",
        password_hash=hash_password("Read123!@#"),
        role=UserRole.READ_ONLY,
        language_preference="en"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def owner_token(client, owner_user):
    """Get auth token for owner user"""
    response = client.post(
        "/api/auth/login",
        json={"username": "owner", "password": "Owner123!@#"}
    )
    return response.json()["access_token"]


@pytest.fixture
def admin_token(client, admin_user):
    """Get auth token for admin user"""
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "Admin123!@#"}
    )
    return response.json()["access_token"]


@pytest.fixture
def readonly_token(client, readonly_user):
    """Get auth token for readonly user"""
    response = client.post(
        "/api/auth/login",
        json={"username": "readonly", "password": "Read123!@#"}
    )
    return response.json()["access_token"]


class TestCreateUserEndpoint:
    """Contract tests for POST /api/users (T080)"""

    def test_create_user_as_owner(self, client, owner_user, owner_token):
        """Test owner can create new users"""
        response = client.post(
            "/api/users",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "username": "newuser",
                "password": "NewUser123!@#",
                "role": "admin",
                "language_preference": "en"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["role"] == "admin"
        assert "id" in data
        assert "password" not in data  # Password should not be returned
        assert "password_hash" not in data

    def test_create_readonly_user_as_owner(self, client, owner_token):
        """Test creating read-only user"""
        response = client.post(
            "/api/users",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "username": "newreadonly",
                "password": "ReadOnly123!@#",
                "role": "read_only",
                "language_preference": "zh"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "read_only"
        assert data["language_preference"] == "zh"

    def test_create_user_cannot_create_owner_role(self, client, owner_token):
        """Test that creating another owner is not allowed"""
        response = client.post(
            "/api/users",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "username": "newowner",
                "password": "Owner123!@#",
                "role": "owner",
                "language_preference": "en"
            }
        )

        assert response.status_code == 403  # Forbidden

    def test_create_user_as_admin_forbidden(self, client, admin_token):
        """Test that admin cannot create users (owner only)"""
        response = client.post(
            "/api/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "username": "newuser",
                "password": "NewUser123!@#",
                "role": "admin",
                "language_preference": "en"
            }
        )

        assert response.status_code == 403

    def test_create_user_as_readonly_forbidden(self, client, readonly_token):
        """Test that read-only user cannot create users"""
        response = client.post(
            "/api/users",
            headers={"Authorization": f"Bearer {readonly_token}"},
            json={
                "username": "newuser",
                "password": "NewUser123!@#",
                "role": "admin",
                "language_preference": "en"
            }
        )

        assert response.status_code == 403

    def test_create_user_without_auth(self, client):
        """Test creating user without authentication"""
        response = client.post(
            "/api/users",
            json={
                "username": "newuser",
                "password": "NewUser123!@#",
                "role": "admin",
                "language_preference": "en"
            }
        )

        assert response.status_code == 401

    def test_create_user_duplicate_username(self, client, owner_token, admin_user):
        """Test creating user with duplicate username"""
        response = client.post(
            "/api/users",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "username": "admin",  # Already exists
                "password": "NewUser123!@#",
                "role": "admin",
                "language_preference": "en"
            }
        )

        assert response.status_code == 400

    def test_create_user_missing_required_fields(self, client, owner_token):
        """Test creating user with missing required fields"""
        response = client.post(
            "/api/users",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "username": "incomplete"
                # Missing password and role
            }
        )

        assert response.status_code == 422

    def test_create_user_invalid_role(self, client, owner_token):
        """Test creating user with invalid role"""
        response = client.post(
            "/api/users",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "username": "baduser",
                "password": "Test123!@#",
                "role": "invalid_role",
                "language_preference": "en"
            }
        )

        assert response.status_code == 422

    def test_create_user_weak_password(self, client, owner_token):
        """Test creating user with weak password"""
        response = client.post(
            "/api/users",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "username": "weakpass",
                "password": "weak",
                "role": "admin",
                "language_preference": "en"
            }
        )

        assert response.status_code in [400, 422]


class TestListUsersEndpoint:
    """Contract tests for GET /api/users (T091)"""

    def test_list_users_as_owner(self, client, owner_user, admin_user, readonly_user, owner_token):
        """Test owner can list all users"""
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {owner_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3  # At least owner, admin, readonly

        # Verify user data structure
        user_data = data[0]
        assert "id" in user_data
        assert "username" in user_data
        assert "role" in user_data
        assert "password" not in user_data
        assert "password_hash" not in user_data

    def test_list_users_as_admin(self, client, owner_user, admin_user, admin_token):
        """Test admin can list users"""
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_users_as_readonly_forbidden(self, client, readonly_token):
        """Test readonly user cannot list users"""
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {readonly_token}"}
        )

        assert response.status_code == 403

    def test_list_users_without_auth(self, client):
        """Test listing users without authentication"""
        response = client.get("/api/users")

        assert response.status_code == 401


class TestDeleteUserEndpoint:
    """Contract tests for DELETE /api/users/{user_id} (T081)"""

    def test_delete_user_as_owner(self, client, owner_user, admin_user, owner_token):
        """Test owner can delete other users"""
        response = client.delete(
            f"/api/users/{admin_user.id}",
            headers={"Authorization": f"Bearer {owner_token}"}
        )

        assert response.status_code == 204

        # Verify user is deleted
        list_response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        users = list_response.json()
        assert not any(u["id"] == str(admin_user.id) for u in users)

    def test_delete_user_cannot_delete_owner(self, client, owner_user, owner_token):
        """Test that owner cannot delete themselves"""
        response = client.delete(
            f"/api/users/{owner_user.id}",
            headers={"Authorization": f"Bearer {owner_token}"}
        )

        assert response.status_code == 403

    def test_delete_user_as_admin_forbidden(self, client, admin_user, readonly_user, admin_token):
        """Test that admin cannot delete users (owner only)"""
        response = client.delete(
            f"/api/users/{readonly_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 403

    def test_delete_user_as_readonly_forbidden(self, client, admin_user, readonly_token):
        """Test that readonly user cannot delete users"""
        response = client.delete(
            f"/api/users/{admin_user.id}",
            headers={"Authorization": f"Bearer {readonly_token}"}
        )

        assert response.status_code == 403

    def test_delete_user_without_auth(self, client, admin_user):
        """Test deleting user without authentication"""
        response = client.delete(f"/api/users/{admin_user.id}")

        assert response.status_code == 401

    def test_delete_nonexistent_user(self, client, owner_token):
        """Test deleting non-existent user"""
        fake_id = str(uuid.uuid4())
        response = client.delete(
            f"/api/users/{fake_id}",
            headers={"Authorization": f"Bearer {owner_token}"}
        )

        assert response.status_code == 404

    def test_delete_user_invalid_uuid(self, client, owner_token):
        """Test deleting user with invalid UUID"""
        response = client.delete(
            "/api/users/not-a-uuid",
            headers={"Authorization": f"Bearer {owner_token}"}
        )

        assert response.status_code == 422
