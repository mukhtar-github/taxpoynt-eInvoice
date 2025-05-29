import pytest
from fastapi.testclient import TestClient
import uuid
from unittest.mock import patch, MagicMock
import json

from app.models.integration import Integration


@pytest.fixture
def client():
    """Create a test client for the API with mocked database connection."""
    # Patch the database connection before importing the app
    with patch("app.db.session.engine"):
        with patch("app.db.session.get_db"):
            # Now import the app after patching the database connection
            from app.main import app
            return TestClient(app)


@pytest.fixture
def mock_authentication():
    """Mock authentication to bypass token verification."""
    with patch("app.api.dependencies.verify_token", return_value={"sub": str(uuid.uuid4())}):
        with patch("app.api.dependencies.get_current_user") as mock_user:
            # Create a mock user with required attributes
            mock_user.return_value = MagicMock()
            mock_user.return_value.id = uuid.uuid4()
            mock_user.return_value.is_active = True
            yield mock_user


@pytest.fixture
def mock_integration():
    """Create a mock integration object."""
    integration = MagicMock(spec=Integration)
    integration.id = uuid.uuid4()
    integration.organization_id = uuid.uuid4()
    integration.name = "Odoo Integration"
    integration.description = "Integration with Odoo ERP"
    integration.type = "odoo"
    integration.config = {
        "url": "https://example.odoo.com",
        "database": "test_db",
        "auth_method": "password",
        "username": "test_user",
        "password": "encrypted_password"
    }
    integration.status = "connected"
    # Make sure __dict__ is properly mocked
    integration.__dict__ = {
        "id": integration.id,
        "organization_id": integration.organization_id,
        "name": integration.name,
        "description": integration.description,
        "type": integration.type,
        "config": integration.config,
        "status": integration.status
    }
    return integration


def test_create_integration(client, mock_authentication, mock_integration):
    """Test creating an integration for an organization."""
    # Mock the integration service
    with patch("app.services.integration_service.create_integration") as mock_create:
        mock_create.return_value = mock_integration
        
        # Test data
        integration_data = {
            "name": "Odoo Integration",
            "description": "Integration with Odoo ERP",
            "type": "odoo",
            "config": {
                "url": "https://example.odoo.com",
                "database": "test_db",
                "auth_method": "password",
                "username": "test_user",
                "password": "test_password"
            }
        }
        
        # Mock the get_db dependency
        with patch("app.api.dependencies.get_db"):
            response = client.post(
                f"/api/organizations/{mock_integration.organization_id}/integrations",
                json=integration_data,
                headers={"Authorization": "Bearer test_token"}
            )
        
        # Check that the response is successful
        assert response.status_code == 201
        
        # Verify the response contains the expected data
        response_data = response.json()
        assert response_data["name"] == "Odoo Integration"
        assert response_data["type"] == "odoo"
        
        # Verify our service was called with the right data
        mock_create.assert_called_once()


def test_get_integration(client, mock_authentication, mock_integration):
    """Test retrieving an integration."""
    # Mock the integration service
    with patch("app.services.integration_service.get_integration") as mock_get:
        mock_get.return_value = mock_integration
        
        # Mock the get_db dependency
        with patch("app.api.dependencies.get_db"):
            response = client.get(
                f"/api/organizations/{mock_integration.organization_id}/integrations/{mock_integration.id}",
                headers={"Authorization": "Bearer test_token"}
            )
        
        # Check that the response is successful
        assert response.status_code == 200
        
        # Verify the response contains the expected data
        response_data = response.json()
        assert response_data["name"] == "Odoo Integration"
        assert response_data["type"] == "odoo"
        
        # Verify our service was called with the right data
        mock_get.assert_called_once()


def test_list_integrations(client, mock_authentication, mock_integration):
    """Test listing all integrations for an organization."""
    # Mock the integration service
    with patch("app.services.integration_service.list_integrations") as mock_list:
        mock_list.return_value = [mock_integration]
        
        # Mock the get_db dependency
        with patch("app.api.dependencies.get_db"):
            response = client.get(
                f"/api/organizations/{mock_integration.organization_id}/integrations",
                headers={"Authorization": "Bearer test_token"}
            )
        
        # Check that the response is successful
        assert response.status_code == 200
        
        # Verify the response contains the expected data
        response_data = response.json()
        assert len(response_data) == 1
        assert response_data[0]["name"] == "Odoo Integration"
        
        # Verify our service was called with the right data
        mock_list.assert_called_once()


def test_update_integration(client, mock_authentication, mock_integration):
    """Test updating an integration."""
    # Mock the integration service
    with patch("app.services.integration_service.update_integration") as mock_update:
        mock_update.return_value = mock_integration
        
        # Test data
        update_data = {
            "name": "Updated Odoo Integration",
            "config": {
                "url": "https://updated.odoo.com",
                "database": "updated_db"
            }
        }
        
        # Mock the get_db dependency
        with patch("app.api.dependencies.get_db"):
            response = client.put(
                f"/api/organizations/{mock_integration.organization_id}/integrations/{mock_integration.id}",
                json=update_data,
                headers={"Authorization": "Bearer test_token"}
            )
        
        # Check that the response is successful
        assert response.status_code == 200
        
        # Verify our service was called with the right data
        mock_update.assert_called_once()


def test_delete_integration(client, mock_authentication, mock_integration):
    """Test deleting an integration."""
    # Mock the integration service
    with patch("app.services.integration_service.delete_integration") as mock_delete:
        mock_delete.return_value = True
        
        # Mock the get_db dependency
        with patch("app.api.dependencies.get_db"):
            response = client.delete(
                f"/api/organizations/{mock_integration.organization_id}/integrations/{mock_integration.id}",
                headers={"Authorization": "Bearer test_token"}
            )
        
        # Check that the response is successful
        assert response.status_code == 204
        
        # Verify our service was called with the right data
        mock_delete.assert_called_once()


def test_test_integration_connection(client, mock_authentication, mock_integration):
    """Test the integration connection test endpoint."""
    # Mock the integration service
    with patch("app.services.integration_service.test_connection") as mock_test:
        mock_test.return_value = {"status": "success", "message": "Connection successful"}
        
        # Mock the get_db dependency
        with patch("app.api.dependencies.get_db"):
            response = client.post(
                f"/api/organizations/{mock_integration.organization_id}/integrations/{mock_integration.id}/test",
                headers={"Authorization": "Bearer test_token"}
            )
        
        # Check that the response is successful
        assert response.status_code == 200
        
        # Verify the response contains the expected data
        response_data = response.json()
        assert response_data["status"] == "success"
        assert response_data["message"] == "Connection successful"
        
        # Verify our service was called with the right data
        mock_test.assert_called_once()


def test_get_integration_status(client, mock_authentication, mock_integration):
    """Test retrieving the integration status."""
    # Mock the integration service
    with patch("app.services.integration_service.get_status") as mock_status:
        mock_status.return_value = {
            "status": "connected",
            "last_connected": "2023-05-28T12:00:00",
            "user_id": 1
        }
        
        # Mock the get_db dependency
        with patch("app.api.dependencies.get_db"):
            response = client.get(
                f"/api/organizations/{mock_integration.organization_id}/integrations/{mock_integration.id}/status",
                headers={"Authorization": "Bearer test_token"}
            )
        
        # Check that the response is successful
        assert response.status_code == 200
        
        # Verify the response contains the expected data
        response_data = response.json()
        assert response_data["status"] == "connected"
        assert "last_connected" in response_data
        
        # Verify our service was called with the right data
        mock_status.assert_called_once()


def test_get_integration_invoices(client, mock_authentication, mock_integration):
    """Test retrieving invoices from the integration."""
    # Mock invoices data
    mock_invoices = [
        {
            "id": 1,
            "name": "INV/2023/00001",
            "partner_name": "Customer 1",
            "amount_total": 100.0,
            "date": "2023-05-15",
            "state": "posted"
        },
        {
            "id": 2,
            "name": "INV/2023/00002",
            "partner_name": "Customer 2",
            "amount_total": 200.0,
            "date": "2023-05-16",
            "state": "draft"
        }
    ]
    
    # Mock the integration service
    with patch("app.services.odoo_connector.get_invoices") as mock_get_invoices:
        mock_get_invoices.return_value = mock_invoices
        
        # Mock the get_db dependency
        with patch("app.api.dependencies.get_db"):
            response = client.get(
                f"/api/organizations/{mock_integration.organization_id}/integrations/{mock_integration.id}/invoices",
                headers={"Authorization": "Bearer test_token"}
            )
        
        # Check that the response is successful
        assert response.status_code == 200
        
        # Verify the response contains the expected data
        response_data = response.json()
        assert len(response_data) == 2
        assert response_data[0]["name"] == "INV/2023/00001"
        assert response_data[1]["amount_total"] == 200.0
        
        # Verify our service was called
        mock_get_invoices.assert_called_once()


def test_get_integration_customers(client, mock_authentication, mock_integration):
    """Test retrieving customers from the integration."""
    # Mock customers data
    mock_customers = [
        {
            "id": 1,
            "name": "Customer 1",
            "email": "customer1@example.com",
            "phone": "1234567890"
        },
        {
            "id": 2,
            "name": "Customer 2",
            "email": "customer2@example.com",
            "phone": "0987654321"
        }
    ]
    
    # Mock the integration service
    with patch("app.services.odoo_connector.get_customers") as mock_get_customers:
        mock_get_customers.return_value = mock_customers
        
        # Mock the get_db dependency
        with patch("app.api.dependencies.get_db"):
            response = client.get(
                f"/api/organizations/{mock_integration.organization_id}/integrations/{mock_integration.id}/customers",
                headers={"Authorization": "Bearer test_token"}
            )
        
        # Check that the response is successful
        assert response.status_code == 200
        
        # Verify the response contains the expected data
        response_data = response.json()
        assert len(response_data) == 2
        assert response_data[0]["name"] == "Customer 1"
        assert response_data[1]["email"] == "customer2@example.com"
        
        # Verify our service was called
        mock_get_customers.assert_called_once()


def test_get_integration_products(client, mock_authentication, mock_integration):
    """Test retrieving products from the integration."""
    # Mock products data
    mock_products = [
        {
            "id": 1,
            "name": "Product 1",
            "list_price": 50.0,
            "default_code": "P001"
        },
        {
            "id": 2,
            "name": "Product 2",
            "list_price": 75.0,
            "default_code": "P002"
        }
    ]
    
    # Mock the integration service
    with patch("app.services.odoo_connector.get_products") as mock_get_products:
        mock_get_products.return_value = mock_products
        
        # Mock the get_db dependency
        with patch("app.api.dependencies.get_db"):
            response = client.get(
                f"/api/organizations/{mock_integration.organization_id}/integrations/{mock_integration.id}/products",
                headers={"Authorization": "Bearer test_token"}
            )
        
        # Check that the response is successful
        assert response.status_code == 200
        
        # Verify the response contains the expected data
        response_data = response.json()
        assert len(response_data) == 2
        assert response_data[0]["name"] == "Product 1"
        assert response_data[1]["list_price"] == 75.0
        
        # Verify our service was called
        mock_get_products.assert_called_once()
