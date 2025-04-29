import pytest # type: ignore
from fastapi.testclient import TestClient # type: ignore
from sqlalchemy import create_engine # type: ignore
from sqlalchemy.orm import sessionmaker # type: ignore
from sqlalchemy.pool import StaticPool # type: ignore

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.models.user import User, UserRole
from app.core.security import get_password_hash

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_user(test_db):
    db = TestingSessionLocal()
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("password"),
        full_name="Test User",
        is_active=True,
        role=UserRole.SI_USER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


def test_create_user(test_db):
    """Test user registration endpoint"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "new_user@example.com",
            "password": "Password123",
            "full_name": "New User",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "new_user@example.com"
    assert data["full_name"] == "New User"
    assert data["role"] == "si_user"
    assert "id" in data


def test_login_user(test_user):
    """Test user login with correct credentials"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_user_wrong_password(test_user):
    """Test user login with incorrect password"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "wrong_password"},
    )
    assert response.status_code == 401


def test_get_user_me(test_user):
    """Test retrieving current user profile"""
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password"},
    )
    token = login_response.json()["access_token"]
    
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    

def test_update_user_me(test_user):
    """Test updating current user profile"""
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password"},
    )
    token = login_response.json()["access_token"]
    
    response = client.put(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"full_name": "Updated Name"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["email"] == "test@example.com"


def test_create_admin_user(test_db):
    """Test admin user creation (should be restricted)"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@example.com",
            "password": "Password123",
            "full_name": "Admin User",
            "role": "admin"
        },
    )
    
    # Depending on your implementation, this might be forbidden or allowed
    # Adjust the assertion accordingly
    if response.status_code == 200:
        data = response.json()
        assert data["role"] != "admin", "Regular registration should not create admin users"
    else:
        assert response.status_code == 403, "Creating admin users should be forbidden"


def test_password_reset_request(test_user):
    """Test password reset request flow"""
    response = client.post(
        "/api/v1/auth/password-reset",
        json={"email": "test@example.com"},
    )
    assert response.status_code == 200


def test_invalid_token_access(test_db):
    """Test access with invalid token"""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401 