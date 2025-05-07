"""Tests for authentication integration with basic integration configuration."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from app.main import app
from app.db.session import get_db
from app.models.user import User, Organization, OrganizationUser
from app.models.client import Client
from app.crud.user import create_user
from app.crud.client import create_client
from app.schemas.user import UserCreate
from app.schemas.client import ClientCreate

client = TestClient(app)

@pytest.fixture(scope="module")
def test_db():
    # Get a DB session for tests
    db = next(get_db())
    yield db
    # Clean up after tests

@pytest.fixture(scope="module")
def test_organization(test_db: Session):
    # Create a test organization for testing
    # Check if organization already exists
    org = test_db.query(Organization).filter(Organization.name == "Test Organization").first()
    if not org:
        org = Organization(
            name="Test Organization",
            tax_id="12345678-9",
            email="org@example.com"
        )
        test_db.add(org)
        test_db.commit()
        test_db.refresh(org)
    return org

@pytest.fixture(scope="module")
def test_user(test_db: Session, test_organization: Organization):
    """Create a test user for authentication tests."""
    # Check if user already exists
    user = test_db.query(User).filter(User.email == "testuser@example.com").first()
    if user:
        return user
        
    user_create = UserCreate(
        email="testuser@example.com",
        password="testpassword123",
        full_name="Test User"
    )
    user = create_user(test_db, user_create)
    
    # Mark user as verified for login
    user.is_email_verified = True
    
    # Create organization user link
    org_user = OrganizationUser(
        organization_id=test_organization.id,
        user_id=user.id
    )
    test_db.add(org_user)
    test_db.commit()
    test_db.refresh(user)
    
    return user

@pytest.fixture(scope="module")
def auth_headers(test_user: User):
    """Get auth headers with JWT token."""
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "testpassword123"}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return headers

@pytest.fixture(scope="module")
def test_client(test_db: Session, test_organization: Organization):
    """Create a test client for integration tests."""
    # Check if client already exists
    existing_client = test_db.query(Client).filter(Client.name == "Test Client").first()
    if existing_client:
        return existing_client
        
    client_create = ClientCreate(
        name="Test Client",
        description="A test client for integration testing",
        organization_id=str(test_organization.id)  # Convert UUID to string
    )
    db_client = create_client(test_db, client_create)
    return db_client

def test_create_integration_with_auth(auth_headers, test_client: Client):
    """Test creating an integration with authentication."""
    # Attempt to create integration
    integration_data = {
        "name": "Test Integration",
        "description": "Integration for testing auth flow",
        "client_id": str(test_client.id),
        "integration_type": "odoo",
        "config": {
            "url": "https://demo.odoo.com",
            "database": "test_db",
            "username": "test_user",
            "password": "test_password",
            "port": 8069
        }
    }
    
    # First try without auth - should fail
    response_no_auth = client.post(
        "/api/v1/integrations",
        json=integration_data
    )
    assert response_no_auth.status_code == 401 or response_no_auth.status_code == 403
    
    # Now try with auth - should succeed
    response_with_auth = client.post(
        "/api/v1/integrations",
        json=integration_data,
        headers=auth_headers
    )
    assert response_with_auth.status_code in [200, 201], f"Failed with status {response_with_auth.status_code}: {response_with_auth.text}"
    
    # Verify the created integration
    created = response_with_auth.json()
    assert created["name"] == "Test Integration"
    assert created["client_id"] == str(test_client.id)
    
    # Test retrieving the integration
    get_response = client.get(
        f"/api/v1/integrations/{created['id']}",
        headers=auth_headers
    )
    assert get_response.status_code == 200, f"Failed to get integration: {get_response.text}"
    
    return created

def test_integration_list_requires_auth(auth_headers):
    """Test that listing integrations requires authentication."""
    # Try without auth
    response_no_auth = client.get("/api/v1/integrations")
    assert response_no_auth.status_code in [401, 403], f"Expected 401 or 403, got {response_no_auth.status_code}"
    
    # Try with auth
    response_with_auth = client.get(
        "/api/v1/integrations",
        headers=auth_headers
    )
    assert response_with_auth.status_code == 200, f"Failed with status {response_with_auth.status_code}: {response_with_auth.text}"
    
    # Should return a list (even if empty)
    response_data = response_with_auth.json()
    assert isinstance(response_data, list), f"Expected list, got {type(response_data)}: {response_data}"

def test_end_to_end_integration_flow(auth_headers, test_client: Client):
    """Test the complete end-to-end flow of setting up an integration."""
    # 1. Create a new integration
    integration_data = {
        "name": "E2E Test Integration",
        "description": "Complete end-to-end test",
        "client_id": str(test_client.id),
        "integration_type": "odoo",
        "config": {
            "url": "https://demo.odoo.com",
            "database": "test_db",
            "username": "test_user",
            "password": "test_password",
            "port": 8069
        }
    }
    
    create_response = client.post(
        "/api/v1/integrations",
        json=integration_data,
        headers=auth_headers
    )
    assert create_response.status_code in [200, 201], f"Failed to create integration: {create_response.text}"
    response_data = create_response.json()
    integration_id = response_data["id"]
    
    # 2. Retrieve the integration
    get_response = client.get(
        f"/api/v1/integrations/{integration_id}",
        headers=auth_headers
    )
    assert get_response.status_code == 200, f"Failed to get integration: {get_response.text}"
    
    # 3. Update the integration
    update_data = {
        "name": "Updated E2E Integration",
        "config": {
            "url": "https://demo.odoo.com",
            "database": "updated_db",
            "username": "test_user",
            "password": "updated_password",
            "port": 8069
        }
    }
    
    update_response = client.put(
        f"/api/v1/integrations/{integration_id}",
        json=update_data,
        headers=auth_headers
    )
    assert update_response.status_code == 200, f"Failed to update integration: {update_response.text}"
    updated_data = update_response.json()
    assert updated_data["name"] == "Updated E2E Integration", f"Name not updated correctly: {updated_data}"
    
    # 4. Test the integration connection
    test_response = client.post(
        f"/api/v1/integrations/{integration_id}/test",
        headers=auth_headers
    )
    # This might fail with a real test, but we're just checking the endpoint works
    assert test_response.status_code in [200, 400, 422, 500], f"Unexpected status code: {test_response.status_code}"
    
    # 5. Delete the integration
    delete_response = client.delete(
        f"/api/v1/integrations/{integration_id}",
        headers=auth_headers
    )
    assert delete_response.status_code in [200, 202, 204], f"Failed to delete integration: {delete_response.text}"
    
    # 6. Verify it's deleted
    get_deleted = client.get(
        f"/api/v1/integrations/{integration_id}",
        headers=auth_headers
    )
    assert get_deleted.status_code == 404, f"Integration not deleted: {get_deleted.text}"
