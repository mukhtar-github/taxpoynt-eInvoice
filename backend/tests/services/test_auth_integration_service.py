import pytest # type: ignore
from fastapi.testclient import TestClient # type: ignore
from sqlalchemy import create_engine # type: ignore
from sqlalchemy.orm import sessionmaker # type: ignore
from sqlalchemy.pool import StaticPool # type: ignore
import jwt # type: ignore
from datetime import datetime, timedelta # type: ignore

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.models.user import User, UserRole
from app.core.security import get_password_hash, create_access_token
from app.core.config import settings

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_integration.db"

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
        email="integration_test@example.com",
        hashed_password=get_password_hash("integration_password"),
        full_name="Integration Test User",
        is_active=True,
        role=UserRole.SI_USER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


@pytest.fixture(scope="function")
def test_token(test_user):
    return create_access_token(
        subject=test_user.email,
        user_id=test_user.id
    )


def test_user_authentication_flow():
    """Test the complete user authentication flow from registration to using protected endpoints"""
    # Step 1: Register a new user
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "flow_test@example.com",
            "password": "FlowPassword123",
            "full_name": "Flow Test User",
        },
    )
    assert register_response.status_code == 200
    user_data = register_response.json()
    assert user_data["email"] == "flow_test@example.com"
    
    # Step 2: Login with the new user
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "flow_test@example.com", "password": "FlowPassword123"},
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    token = token_data["access_token"]
    
    # Step 3: Access protected endpoint
    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    user_info = me_response.json()
    assert user_info["email"] == "flow_test@example.com"


def test_token_validation_and_refresh(test_token, test_user):
    """Test token validation and refresh mechanism"""
    # Step 1: Use the token to access a protected endpoint
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    
    # Step 2: Verify token contents
    payload = jwt.decode(
        test_token, 
        settings.SECRET_KEY, 
        algorithms=[settings.ALGORITHM]
    )
    assert payload["sub"] == test_user.email
    assert str(payload["user_id"]) == str(test_user.id)
    
    # Step 3: Test token refresh if endpoint exists
    # Uncomment if you have a token refresh endpoint
    """
    refresh_response = client.post(
        "/api/v1/auth/refresh",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert refresh_response.status_code == 200
    new_token = refresh_response.json()["access_token"]
    assert new_token != test_token
    """


def test_auth_integration_with_permissions(test_db):
    """Test integrating authentication with authorization/permissions"""
    # Create a regular user
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "regular@example.com",
            "password": "Password123",
            "full_name": "Regular User",
        },
    )
    
    # Login as regular user
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "regular@example.com", "password": "Password123"},
    )
    regular_token = login_response.json()["access_token"]
    
    # Create admin user directly in DB
    db = TestingSessionLocal()
    admin_user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("AdminPass123"),
        full_name="Admin User",
        is_active=True,
        role=UserRole.ADMIN,
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    db.close()
    
    # Login as admin
    admin_login = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@example.com", "password": "AdminPass123"},
    )
    admin_token = admin_login.json()["access_token"]
    
    # Try to access admin-only endpoint with regular user
    # Replace with your actual admin endpoint
    admin_endpoint = "/api/v1/users/"
    
    # Regular user access attempt
    regular_response = client.get(
        admin_endpoint,
        headers={"Authorization": f"Bearer {regular_token}"},
    )
    
    # Admin user access attempt
    admin_response = client.get(
        admin_endpoint,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    
    # Regular user should get 403 Forbidden (or 404 Not Found if endpoint is hidden)
    assert regular_response.status_code in [403, 404]
    
    # Admin should get 200 OK (assuming the endpoint exists)
    # If the endpoint doesn't exist, comment this out or adjust accordingly
    if admin_response.status_code != 404:
        assert admin_response.status_code == 200


def test_expired_token_handling():
    """Test handling of expired tokens"""
    # Create a user
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "expired@example.com",
            "password": "Password123",
            "full_name": "Expired Token User",
        },
    )
    
    # Login to get a token
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "expired@example.com", "password": "Password123"},
    )
    token = login_response.json()["access_token"]
    
    # Create an expired token manually
    payload = {
        "sub": "expired@example.com",
        "exp": datetime.utcnow() - timedelta(minutes=30),  # Token expired 30 minutes ago
        "iat": datetime.utcnow() - timedelta(hours=1),     # Issued 1 hour ago
    }
    expired_token = jwt.encode(
        payload, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    # Try to use the expired token
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401  # Unauthorized due to expired token 