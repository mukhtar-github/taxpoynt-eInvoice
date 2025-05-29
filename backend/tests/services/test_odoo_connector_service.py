import pytest
from unittest.mock import patch, MagicMock
import uuid
import json
from datetime import datetime

from app.services.odoo_connector import OdooConnector


@pytest.fixture
def odoo_connector():
    """Create an OdooConnector instance with mock config."""
    config = {
        "url": "https://example.odoo.com",
        "database": "test_db",
        "username": "test_user",
        "password": "test_password",
        "auth_method": "password"
    }
    return OdooConnector(config)


@pytest.fixture
def mock_xmlrpc_client():
    """Create a mock xmlrpc client."""
    with patch("xmlrpc.client.ServerProxy") as mock_server:
        # Create a mock for common and object endpoints
        mock_common = MagicMock()
        mock_object = MagicMock()
        
        # Set up the authenticate method
        mock_common.authenticate.return_value = 1  # User ID
        
        # Configure the mock ServerProxy to return our mocks
        mock_server.side_effect = lambda url, *args, **kwargs: (
            mock_common if "/xmlrpc/2/common" in url else mock_object
        )
        
        yield {
            "common": mock_common,
            "object": mock_object,
            "server": mock_server
        }


def test_connect_successful(odoo_connector, mock_xmlrpc_client):
    """Test successful connection to Odoo."""
    result = odoo_connector.connect()
    
    # Verify our connection was successful
    assert result == True
    assert odoo_connector.uid == 1
    
    # Verify the authenticate method was called with the right params
    mock_xmlrpc_client["common"].authenticate.assert_called_once_with(
        "test_db", "test_user", "test_password", {}
    )


def test_connect_failed(odoo_connector, mock_xmlrpc_client):
    """Test failed connection to Odoo."""
    # Set up the authenticate method to fail
    mock_xmlrpc_client["common"].authenticate.return_value = False
    
    result = odoo_connector.connect()
    
    # Verify our connection failed
    assert result == False
    assert odoo_connector.uid is None
    
    # Verify the authenticate method was called
    mock_xmlrpc_client["common"].authenticate.assert_called_once()


def test_get_invoices(odoo_connector, mock_xmlrpc_client):
    """Test retrieving invoices from Odoo."""
    # Set up the execute_kw method to return a list of invoices
    mock_invoices = [
        {
            "id": 1,
            "name": "INV/2023/00001",
            "partner_id": [1, "Customer 1"],
            "amount_total": 100.0,
            "date_invoice": "2023-05-15",
            "state": "posted"
        },
        {
            "id": 2,
            "name": "INV/2023/00002",
            "partner_id": [2, "Customer 2"],
            "amount_total": 200.0,
            "date_invoice": "2023-05-16",
            "state": "draft"
        }
    ]
    mock_xmlrpc_client["object"].execute_kw.return_value = mock_invoices
    
    # Connect to Odoo
    odoo_connector.connect()
    
    # Get invoices
    invoices = odoo_connector.get_invoices(limit=10)
    
    # Verify our method returned the expected result
    assert len(invoices) == 2
    assert invoices[0]["name"] == "INV/2023/00001"
    assert invoices[1]["amount_total"] == 200.0
    
    # Verify the execute_kw method was called with the right params
    mock_xmlrpc_client["object"].execute_kw.assert_called_once()


def test_get_customers(odoo_connector, mock_xmlrpc_client):
    """Test retrieving customers from Odoo."""
    # Set up the execute_kw method to return a list of customers
    mock_customers = [
        {
            "id": 1,
            "name": "Customer 1",
            "email": "customer1@example.com",
            "phone": "1234567890",
            "street": "123 Main St"
        },
        {
            "id": 2,
            "name": "Customer 2",
            "email": "customer2@example.com",
            "phone": "0987654321",
            "street": "456 Oak Ave"
        }
    ]
    mock_xmlrpc_client["object"].execute_kw.return_value = mock_customers
    
    # Connect to Odoo
    odoo_connector.connect()
    
    # Get customers
    customers = odoo_connector.get_customers(limit=10)
    
    # Verify our method returned the expected result
    assert len(customers) == 2
    assert customers[0]["name"] == "Customer 1"
    assert customers[1]["email"] == "customer2@example.com"
    
    # Verify the execute_kw method was called with the right params
    mock_xmlrpc_client["object"].execute_kw.assert_called_once()


def test_get_products(odoo_connector, mock_xmlrpc_client):
    """Test retrieving products from Odoo."""
    # Set up the execute_kw method to return a list of products
    mock_products = [
        {
            "id": 1,
            "name": "Product 1",
            "list_price": 50.0,
            "default_code": "P001",
            "type": "product"
        },
        {
            "id": 2,
            "name": "Product 2",
            "list_price": 75.0,
            "default_code": "P002",
            "type": "service"
        }
    ]
    mock_xmlrpc_client["object"].execute_kw.return_value = mock_products
    
    # Connect to Odoo
    odoo_connector.connect()
    
    # Get products
    products = odoo_connector.get_products(limit=10)
    
    # Verify our method returned the expected result
    assert len(products) == 2
    assert products[0]["name"] == "Product 1"
    assert products[1]["list_price"] == 75.0
    
    # Verify the execute_kw method was called with the right params
    mock_xmlrpc_client["object"].execute_kw.assert_called_once()


def test_connection_status(odoo_connector, mock_xmlrpc_client):
    """Test checking connection status."""
    # Set up a successful connection
    odoo_connector.connect()
    
    # Check status
    status = odoo_connector.check_connection_status()
    
    # Verify our method returned the expected result
    assert status["connected"] == True
    assert "last_connected" in status
    assert status["user_id"] == 1


def test_handle_connection_error(odoo_connector, mock_xmlrpc_client):
    """Test handling connection errors gracefully."""
    # Make the server raise an exception
    mock_xmlrpc_client["common"].authenticate.side_effect = Exception("Connection error")
    
    # Try to connect
    result = odoo_connector.connect()
    
    # Verify our connection failed
    assert result == False
    
    # Check the status
    status = odoo_connector.check_connection_status()
    assert status["connected"] == False
    assert "error" in status
