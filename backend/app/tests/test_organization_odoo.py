"""
Tests for organization Odoo data interaction API endpoints.
"""
import uuid
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.organization import Organization
from app.models.integration import Integration, IntegrationType
from app.schemas.integration import OdooConfig, OdooAuthMethod
from app.services.odoo_connector import OdooConnector, OdooDataError


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


@pytest.fixture
def mock_odoo_connector():
    """Fixture to create a mock OdooConnector."""
    mock_connector = MagicMock(spec=OdooConnector)
    
    # Mock authenticate method
    mock_connector.authenticate.return_value = MagicMock()
    
    # Mock get_company_info method
    mock_connector.get_company_info.return_value = {
        "id": 1,
        "name": "MT Garba Global Ventures",
        "vat": "12345678-0001",
        "email": "contact@mtgarba.com",
        "phone": "+234 800 123 4567",
        "website": "https://www.mtgarba.com",
        "currency": "NGN",
        "logo": "base64encodedlogo",
        "address": {
            "street": "123 Business Avenue",
            "city": "Lagos",
            "country": "Nigeria"
        }
    }
    
    # Mock get_invoices method
    mock_connector.get_invoices.return_value = {
        "invoices": [
            {
                "id": 1,
                "name": "INV/2025/0001",
                "partner_id": {"id": 1, "name": "Customer 1"},
                "date": "2025-05-26",
                "amount_total": 1500.00,
                "state": "posted"
            }
        ],
        "total": 1,
        "page": 1,
        "page_size": 20,
        "has_more": False
    }
    
    # Mock get_customers method
    mock_connector.get_customers.return_value = [
        {
            "id": 1,
            "name": "Customer 1",
            "email": "customer1@example.com",
            "phone": "+234 800 111 1111",
            "street": "Customer Street 1",
            "city": "Lagos",
            "country": "Nigeria",
            "vat": "VAT123456"
        }
    ]
    
    # Mock get_products method
    mock_connector.get_products.return_value = [
        {
            "id": 1,
            "name": "Product 1",
            "code": "P001",
            "price": 100.00,
            "currency": "NGN",
            "category": "Services",
            "type": "service",
            "uom": "Unit"
        }
    ]
    
    return mock_connector


@pytest.mark.asyncio
async def test_get_odoo_company_info(monkeypatch, mock_organization, mock_odoo_integration, mock_odoo_connector):
    """Test getting company information from Odoo."""
    # Mock dependencies
    mock_get_org = MagicMock(return_value=mock_organization)
    mock_get_integration = MagicMock(return_value=mock_odoo_integration)
    mock_get_credentials = AsyncMock(return_value={
        "url": "https://mtgarba.odoo.com",
        "database": "mtgarba_prod",
        "username": "admin",
        "password": "secure_password",
        "auth_method": "password"
    })
    mock_record_usage = AsyncMock()
    mock_odoo_connector_class = MagicMock(return_value=mock_odoo_connector)
    
    mock_db = MagicMock()
    mock_current_user = MagicMock(id=uuid.uuid4())
    
    # Apply mocks
    monkeypatch.setattr(
        "app.routes.organization_odoo.OrganizationService.get_organization", 
        mock_get_org
    )
    monkeypatch.setattr(
        "app.routes.organization_odoo.get_integration", 
        mock_get_integration
    )
    monkeypatch.setattr(
        "app.routes.organization_odoo.get_credentials_for_integration", 
        mock_get_credentials
    )
    monkeypatch.setattr(
        "app.routes.organization_odoo.record_credential_usage", 
        mock_record_usage
    )
    monkeypatch.setattr(
        "app.routes.organization_odoo.OdooConnector", 
        mock_odoo_connector_class
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
        f"/api/v1/organizations/{mock_organization.id}/integrations/{mock_odoo_integration.id}/odoo/company-info"
    )
    
    # Assert response
    assert response.status_code == 200
    assert response.json()["name"] == "MT Garba Global Ventures"
    
    # Verify mock calls
    mock_get_org.assert_called_once_with(mock_organization.id)
    mock_get_integration.assert_called_once_with(db=mock_db, integration_id=mock_odoo_integration.id)
    mock_get_credentials.assert_called_once_with(db=mock_db, integration_id=mock_odoo_integration.id)
    mock_record_usage.assert_called_once()
    mock_odoo_connector.authenticate.assert_called_once()
    mock_odoo_connector.get_company_info.assert_called_once()


@pytest.mark.asyncio
async def test_get_odoo_invoices(monkeypatch, mock_organization, mock_odoo_integration, mock_odoo_connector):
    """Test getting invoices from Odoo."""
    # Mock dependencies
    mock_get_org = MagicMock(return_value=mock_organization)
    mock_get_integration = MagicMock(return_value=mock_odoo_integration)
    mock_get_credentials = AsyncMock(return_value={
        "url": "https://mtgarba.odoo.com",
        "database": "mtgarba_prod",
        "username": "admin",
        "password": "secure_password",
        "auth_method": "password"
    })
    mock_record_usage = AsyncMock()
    mock_odoo_connector_class = MagicMock(return_value=mock_odoo_connector)
    
    mock_db = MagicMock()
    mock_current_user = MagicMock(id=uuid.uuid4())
    
    # Apply mocks
    monkeypatch.setattr(
        "app.routes.organization_odoo.OrganizationService.get_organization", 
        mock_get_org
    )
    monkeypatch.setattr(
        "app.routes.organization_odoo.get_integration", 
        mock_get_integration
    )
    monkeypatch.setattr(
        "app.routes.organization_odoo.get_credentials_for_integration", 
        mock_get_credentials
    )
    monkeypatch.setattr(
        "app.routes.organization_odoo.record_credential_usage", 
        mock_record_usage
    )
    monkeypatch.setattr(
        "app.routes.organization_odoo.OdooConnector", 
        mock_odoo_connector_class
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
        f"/api/v1/organizations/{mock_organization.id}/integrations/{mock_odoo_integration.id}/odoo/invoices"
    )
    
    # Assert response
    assert response.status_code == 200
    assert "invoices" in response.json()
    assert len(response.json()["invoices"]) == 1
    
    # Verify mock calls
    mock_get_org.assert_called_once_with(mock_organization.id)
    mock_get_integration.assert_called_once_with(db=mock_db, integration_id=mock_odoo_integration.id)
    mock_get_credentials.assert_called_once_with(db=mock_db, integration_id=mock_odoo_integration.id)
    mock_record_usage.assert_called_once()
    mock_odoo_connector.authenticate.assert_called_once()
    mock_odoo_connector.get_invoices.assert_called_once()


@pytest.mark.asyncio
async def test_get_odoo_customers(monkeypatch, mock_organization, mock_odoo_integration, mock_odoo_connector):
    """Test getting customers from Odoo."""
    # Mock dependencies
    mock_get_org = MagicMock(return_value=mock_organization)
    mock_get_integration = MagicMock(return_value=mock_odoo_integration)
    mock_get_credentials = AsyncMock(return_value={
        "url": "https://mtgarba.odoo.com",
        "database": "mtgarba_prod",
        "username": "admin",
        "password": "secure_password",
        "auth_method": "password"
    })
    mock_record_usage = AsyncMock()
    mock_odoo_connector_class = MagicMock(return_value=mock_odoo_connector)
    
    mock_db = MagicMock()
    mock_current_user = MagicMock(id=uuid.uuid4())
    
    # Apply mocks
    monkeypatch.setattr(
        "app.routes.organization_odoo.OrganizationService.get_organization", 
        mock_get_org
    )
    monkeypatch.setattr(
        "app.routes.organization_odoo.get_integration", 
        mock_get_integration
    )
    monkeypatch.setattr(
        "app.routes.organization_odoo.get_credentials_for_integration", 
        mock_get_credentials
    )
    monkeypatch.setattr(
        "app.routes.organization_odoo.record_credential_usage", 
        mock_record_usage
    )
    monkeypatch.setattr(
        "app.routes.organization_odoo.OdooConnector", 
        mock_odoo_connector_class
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
        f"/api/v1/organizations/{mock_organization.id}/integrations/{mock_odoo_integration.id}/odoo/customers"
    )
    
    # Assert response
    assert response.status_code == 200
    assert "data" in response.json()
    assert len(response.json()["data"]) == 1
    
    # Verify mock calls
    mock_get_org.assert_called_once_with(mock_organization.id)
    mock_get_integration.assert_called_once_with(db=mock_db, integration_id=mock_odoo_integration.id)
    mock_get_credentials.assert_called_once_with(db=mock_db, integration_id=mock_odoo_integration.id)
    mock_record_usage.assert_called_once()
    mock_odoo_connector.authenticate.assert_called_once()
    mock_odoo_connector.get_customers.assert_called_once()


@pytest.mark.asyncio
async def test_get_odoo_products(monkeypatch, mock_organization, mock_odoo_integration, mock_odoo_connector):
    """Test getting products from Odoo."""
    # Mock dependencies
    mock_get_org = MagicMock(return_value=mock_organization)
    mock_get_integration = MagicMock(return_value=mock_odoo_integration)
    mock_get_credentials = AsyncMock(return_value={
        "url": "https://mtgarba.odoo.com",
        "database": "mtgarba_prod",
        "username": "admin",
        "password": "secure_password",
        "auth_method": "password"
    })
    mock_record_usage = AsyncMock()
    mock_odoo_connector_class = MagicMock(return_value=mock_odoo_connector)
    
    mock_db = MagicMock()
    mock_current_user = MagicMock(id=uuid.uuid4())
    
    # Apply mocks
    monkeypatch.setattr(
        "app.routes.organization_odoo.OrganizationService.get_organization", 
        mock_get_org
    )
    monkeypatch.setattr(
        "app.routes.organization_odoo.get_integration", 
        mock_get_integration
    )
    monkeypatch.setattr(
        "app.routes.organization_odoo.get_credentials_for_integration", 
        mock_get_credentials
    )
    monkeypatch.setattr(
        "app.routes.organization_odoo.record_credential_usage", 
        mock_record_usage
    )
    monkeypatch.setattr(
        "app.routes.organization_odoo.OdooConnector", 
        mock_odoo_connector_class
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
        f"/api/v1/organizations/{mock_organization.id}/integrations/{mock_odoo_integration.id}/odoo/products"
    )
    
    # Assert response
    assert response.status_code == 200
    assert "data" in response.json()
    assert len(response.json()["data"]) == 1
    
    # Verify mock calls
    mock_get_org.assert_called_once_with(mock_organization.id)
    mock_get_integration.assert_called_once_with(db=mock_db, integration_id=mock_odoo_integration.id)
    mock_get_credentials.assert_called_once_with(db=mock_db, integration_id=mock_odoo_integration.id)
    mock_record_usage.assert_called_once()
    mock_odoo_connector.authenticate.assert_called_once()
    mock_odoo_connector.get_products.assert_called_once()


@pytest.mark.asyncio
async def test_sync_odoo_data(monkeypatch, mock_organization, mock_odoo_integration, mock_odoo_connector):
    """Test syncing data from Odoo."""
    # Mock dependencies
    mock_get_org = MagicMock(return_value=mock_organization)
    mock_get_integration = MagicMock(return_value=mock_odoo_integration)
    mock_get_credentials = AsyncMock(return_value={
        "url": "https://mtgarba.odoo.com",
        "database": "mtgarba_prod",
        "username": "admin",
        "password": "secure_password",
        "auth_method": "password"
    })
    mock_record_usage = AsyncMock()
    mock_odoo_connector_class = MagicMock(return_value=mock_odoo_connector)
    
    mock_db = MagicMock()
    mock_current_user = MagicMock(id=uuid.uuid4())
    
    # Apply mocks
    monkeypatch.setattr(
        "app.routes.organization_odoo.OrganizationService.get_organization", 
        mock_get_org
    )
    monkeypatch.setattr(
        "app.routes.organization_odoo.get_integration", 
        mock_get_integration
    )
    monkeypatch.setattr(
        "app.routes.organization_odoo.get_credentials_for_integration", 
        mock_get_credentials
    )
    monkeypatch.setattr(
        "app.routes.organization_odoo.record_credential_usage", 
        mock_record_usage
    )
    monkeypatch.setattr(
        "app.routes.organization_odoo.OdooConnector", 
        mock_odoo_connector_class
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
        f"/api/v1/organizations/{mock_organization.id}/integrations/{mock_odoo_integration.id}/odoo/sync"
    )
    
    # Assert response
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Verify mock calls
    mock_get_org.assert_called_once_with(mock_organization.id)
    mock_get_integration.assert_called_once_with(db=mock_db, integration_id=mock_odoo_integration.id)
    mock_get_credentials.assert_called_once_with(db=mock_db, integration_id=mock_odoo_integration.id)
    mock_record_usage.assert_called_once()
    mock_odoo_connector.authenticate.assert_called_once()
