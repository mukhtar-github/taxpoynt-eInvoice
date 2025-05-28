"""
Tests for organization integration API endpoints.
"""
import uuid
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.organization import Organization
from app.models.integration import Integration, IntegrationType
from app.schemas.integration import OdooConfig, OdooAuthMethod


@pytest.fixture
def mock_organization():
    """Fixture to create a mock organization."""
    return Organization(
        id=uuid.uuid4(),
        name="MT Garba Global Ventures",
        tax_id="12345678-0001",
        address="123 Business Avenue, Lagos, Nigeria",
        phone="+234 800 123 4567",
        email="contact@mtgarba.com",
        website="https://www.mtgarba.com",
        status="active",
        created_at=datetime.utcnow()
    )


@pytest.fixture
def mock_odoo_integration(mock_organization):
    """Fixture to create a mock Odoo integration."""
    return Integration(
        id=uuid.uuid4(),
        client_id=mock_organization.id,
        name="Odoo Integration",
        description="MT Garba Odoo Integration",
        integration_type=IntegrationType.ODOO,
        config={
            "url": "https://mtgarba.odoo.com",
            "database": "mtgarba_prod",
            "username": "admin",
            "auth_method": "password"
        },
        config_encrypted=True,
        created_at=datetime.utcnow(),
        status="configured",
        sync_frequency="hourly"
    )


@pytest.mark.asyncio
async def test_list_organization_integrations(monkeypatch, mock_organization, mock_odoo_integration):
    """Test listing integrations for an organization."""
    # Mock get_organization and get_integrations
    mock_get_org = MagicMock(return_value=mock_organization)
    mock_get_integrations = MagicMock(return_value=[mock_odoo_integration])
    mock_db = MagicMock()
    mock_current_user = MagicMock(id=uuid.uuid4())
    
    # Apply mocks
    monkeypatch.setattr(
        "app.routes.organization_integrations.OrganizationService.get_organization", 
        mock_get_org
    )
    monkeypatch.setattr(
        "app.routes.organization_integrations.get_integrations", 
        mock_get_integrations
    )
    
    # Create a test client
    client = TestClient(app)
    
    # Mock the dependencies for authentication
    def mock_get_db():
        return mock_db
    
    def mock_get_current_user():
        return mock_current_user
    
    app.dependency_overrides[Session] = mock_get_db
    app.dependency_overrides["app.dependencies.auth.get_current_user"] = mock_get_current_user
    
    # Make the request
    response = client.get(f"/api/v1/organizations/{mock_organization.id}/integrations")
    
    # Assert response
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == mock_odoo_integration.name
    
    # Verify mock calls
    mock_get_org.assert_called_once_with(mock_organization.id)
    mock_get_integrations.assert_called_once()


@pytest.mark.asyncio
async def test_get_organization_integration(monkeypatch, mock_organization, mock_odoo_integration):
    """Test getting a specific integration for an organization."""
    # Mock get_organization and get_integration
    mock_get_org = MagicMock(return_value=mock_organization)
    mock_get_integration = MagicMock(return_value=mock_odoo_integration)
    mock_db = MagicMock()
    mock_current_user = MagicMock(id=uuid.uuid4())
    
    # Apply mocks
    monkeypatch.setattr(
        "app.routes.organization_integrations.OrganizationService.get_organization", 
        mock_get_org
    )
    monkeypatch.setattr(
        "app.routes.organization_integrations.get_integration", 
        mock_get_integration
    )
    
    # Create a test client
    client = TestClient(app)
    
    # Mock the dependencies for authentication
    def mock_get_db():
        return mock_db
    
    def mock_get_current_user():
        return mock_current_user
    
    app.dependency_overrides[Session] = mock_get_db
    app.dependency_overrides["app.dependencies.auth.get_current_user"] = mock_get_current_user
    
    # Make the request
    response = client.get(
        f"/api/v1/organizations/{mock_organization.id}/integrations/{mock_odoo_integration.id}"
    )
    
    # Assert response
    assert response.status_code == 200
    assert response.json()["name"] == mock_odoo_integration.name
    
    # Verify mock calls
    mock_get_org.assert_called_once_with(mock_organization.id)
    mock_get_integration.assert_called_once_with(db=mock_db, integration_id=mock_odoo_integration.id)


@pytest.mark.asyncio
async def test_create_organization_odoo_integration(monkeypatch, mock_organization):
    """Test creating an Odoo integration for an organization."""
    # Mock get_organization and create_odoo_integration
    integration_id = uuid.uuid4()
    mock_get_org = MagicMock(return_value=mock_organization)
    mock_create_integration = MagicMock(return_value=MagicMock(id=integration_id))
    mock_create_credentials = MagicMock()
    mock_db = MagicMock()
    mock_current_user = MagicMock(id=uuid.uuid4())
    
    # Apply mocks
    monkeypatch.setattr(
        "app.routes.organization_integrations.OrganizationService.get_organization", 
        mock_get_org
    )
    monkeypatch.setattr(
        "app.routes.organization_integrations.create_odoo_integration", 
        mock_create_integration
    )
    monkeypatch.setattr(
        "app.routes.organization_integrations.create_credentials_from_integration_config", 
        mock_create_credentials
    )
    
    # Create a test client
    client = TestClient(app)
    
    # Mock the dependencies for authentication
    def mock_get_db():
        return mock_db
    
    def mock_get_current_user():
        return mock_current_user
    
    app.dependency_overrides[Session] = mock_get_db
    app.dependency_overrides["app.dependencies.auth.get_current_user"] = mock_get_current_user
    
    # Define test data
    integration_data = {
        "name": "Test Odoo Integration",
        "description": "Test integration for MT Garba",
        "client_id": str(mock_organization.id),
        "config": {
            "url": "https://test.odoo.com",
            "database": "test_db",
            "username": "test_user",
            "password": "test_password",
            "auth_method": "password"
        }
    }
    
    # Make the request
    response = client.post(
        f"/api/v1/organizations/{mock_organization.id}/integrations/odoo",
        json=integration_data
    )
    
    # Assert response
    assert response.status_code == 201
    
    # Verify mock calls
    mock_get_org.assert_called_once_with(mock_organization.id)
    mock_create_integration.assert_called_once()
    mock_create_credentials.assert_called_once()


@pytest.mark.asyncio
async def test_test_organization_integration(monkeypatch, mock_organization, mock_odoo_integration):
    """Test testing an integration for an organization."""
    # Mock get_organization, get_integration, and test_integration
    mock_get_org = MagicMock(return_value=mock_organization)
    mock_get_integration = MagicMock(return_value=mock_odoo_integration)
    mock_record_usage = MagicMock()
    mock_test_integration = MagicMock(return_value={"status": "success"})
    mock_db = MagicMock()
    mock_current_user = MagicMock(id=uuid.uuid4())
    
    # Apply mocks
    monkeypatch.setattr(
        "app.routes.organization_integrations.OrganizationService.get_organization", 
        mock_get_org
    )
    monkeypatch.setattr(
        "app.routes.organization_integrations.get_integration", 
        mock_get_integration
    )
    monkeypatch.setattr(
        "app.routes.organization_integrations.record_credential_usage", 
        mock_record_usage
    )
    monkeypatch.setattr(
        "app.routes.organization_integrations.test_integration", 
        mock_test_integration
    )
    
    # Create a test client
    client = TestClient(app)
    
    # Mock the dependencies for authentication
    def mock_get_db():
        return mock_db
    
    def mock_get_current_user():
        return mock_current_user
    
    app.dependency_overrides[Session] = mock_get_db
    app.dependency_overrides["app.dependencies.auth.get_current_user"] = mock_get_current_user
    
    # Make the request
    response = client.post(
        f"/api/v1/organizations/{mock_organization.id}/integrations/{mock_odoo_integration.id}/test"
    )
    
    # Assert response
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Verify mock calls
    mock_get_org.assert_called_once_with(mock_organization.id)
    mock_get_integration.assert_called_once_with(db=mock_db, integration_id=mock_odoo_integration.id)
    mock_record_usage.assert_called_once()
    mock_test_integration.assert_called_once_with(db=mock_db, integration_id=mock_odoo_integration.id)
