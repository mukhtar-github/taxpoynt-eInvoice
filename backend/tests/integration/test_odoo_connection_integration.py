import pytest
import os
from unittest.mock import patch, MagicMock
import uuid
import json
from datetime import datetime

from app.services.odoo_connector import OdooConnector
from app.models.integration import Integration
from app.services.integration_service import IntegrationService


class TestOdooConnectionIntegration:
    """Integration tests for Odoo connection functionality.
    
    These tests use a mock Odoo server to simulate real-world interactions.
    For full integration testing with a real Odoo instance, set TAXPOYNT_TEST_REAL_ODOO=true
    in your environment and configure the connection details.
    """
    
    @pytest.fixture
    def odoo_config(self):
        """Return Odoo connection configuration for testing."""
        # Check if we should use a real Odoo instance for testing
        use_real_odoo = os.environ.get("TAXPOYNT_TEST_REAL_ODOO", "false").lower() == "true"
        
        if use_real_odoo:
            # Use environment variables for real Odoo connection
            return {
                "url": os.environ.get("TAXPOYNT_TEST_ODOO_URL", "https://example.odoo.com"),
                "database": os.environ.get("TAXPOYNT_TEST_ODOO_DB", "test_db"),
                "auth_method": os.environ.get("TAXPOYNT_TEST_ODOO_AUTH_METHOD", "password"),
                "username": os.environ.get("TAXPOYNT_TEST_ODOO_USERNAME", "admin"),
                "password": os.environ.get("TAXPOYNT_TEST_ODOO_PASSWORD", "admin"),
                "api_key": os.environ.get("TAXPOYNT_TEST_ODOO_API_KEY", "")
            }
        else:
            # Use default test configuration
            return {
                "url": "https://example.odoo.com",
                "database": "test_db",
                "auth_method": "password",
                "username": "test_user",
                "password": "test_password"
            }
    
    @pytest.fixture
    def mock_odoo_server(self):
        """Create a mock Odoo server for testing."""
        if os.environ.get("TAXPOYNT_TEST_REAL_ODOO", "false").lower() == "true":
            # Skip mocking if using real Odoo
            yield None
            return
            
        with patch("xmlrpc.client.ServerProxy") as mock_server:
            # Create mocks for common and object endpoints
            mock_common = MagicMock()
            mock_object = MagicMock()
            
            # Set up the authenticate method
            mock_common.authenticate.return_value = 1  # User ID
            
            # Set up the execute_kw method for invoices
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
            
            # Set up the execute_kw method for customers
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
            
            # Set up the execute_kw method for products
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
            
            # Configure the mock execute_kw to return different data based on model
            def mock_execute_kw(db, uid, password, model, method, args, kwargs=None):
                if model == "account.move":
                    return mock_invoices
                elif model == "res.partner":
                    return mock_customers
                elif model == "product.product":
                    return mock_products
                return []
            
            mock_object.execute_kw.side_effect = mock_execute_kw
            
            # Configure the mock ServerProxy to return our mocks
            mock_server.side_effect = lambda url, *args, **kwargs: (
                mock_common if "/xmlrpc/2/common" in url else mock_object
            )
            
            yield {
                "common": mock_common,
                "object": mock_object,
                "server": mock_server
            }
    
    @pytest.fixture
    def odoo_connector(self, odoo_config, mock_odoo_server):
        """Create an OdooConnector instance for testing."""
        return OdooConnector(odoo_config)
    
    def test_connection_establishment(self, odoo_connector, mock_odoo_server):
        """Test establishing a connection to Odoo."""
        # Skip this test if using real Odoo and no connection details provided
        if os.environ.get("TAXPOYNT_TEST_REAL_ODOO", "false").lower() == "true":
            if not os.environ.get("TAXPOYNT_TEST_ODOO_URL"):
                pytest.skip("No real Odoo connection details provided")
        
        # Connect to Odoo
        result = odoo_connector.connect()
        
        # Verify the connection was successful
        assert result == True
        assert odoo_connector.uid is not None
        
        # If using mock, verify the authenticate method was called
        if mock_odoo_server:
            mock_odoo_server["common"].authenticate.assert_called_once()
    
    def test_retrieve_invoices(self, odoo_connector, mock_odoo_server):
        """Test retrieving invoices from Odoo."""
        # Skip this test if using real Odoo and no connection details provided
        if os.environ.get("TAXPOYNT_TEST_REAL_ODOO", "false").lower() == "true":
            if not os.environ.get("TAXPOYNT_TEST_ODOO_URL"):
                pytest.skip("No real Odoo connection details provided")
        
        # Connect to Odoo
        odoo_connector.connect()
        
        # Get invoices
        invoices = odoo_connector.get_invoices(limit=10)
        
        # Verify we received invoices
        assert isinstance(invoices, list)
        assert len(invoices) > 0
        
        # Verify invoice structure
        if invoices:
            invoice = invoices[0]
            assert "id" in invoice
            assert "name" in invoice
            
            # If using mock, verify expected data
            if mock_odoo_server:
                assert invoice["name"] == "INV/2023/00001"
    
    def test_retrieve_customers(self, odoo_connector, mock_odoo_server):
        """Test retrieving customers from Odoo."""
        # Skip this test if using real Odoo and no connection details provided
        if os.environ.get("TAXPOYNT_TEST_REAL_ODOO", "false").lower() == "true":
            if not os.environ.get("TAXPOYNT_TEST_ODOO_URL"):
                pytest.skip("No real Odoo connection details provided")
        
        # Connect to Odoo
        odoo_connector.connect()
        
        # Get customers
        customers = odoo_connector.get_customers(limit=10)
        
        # Verify we received customers
        assert isinstance(customers, list)
        assert len(customers) > 0
        
        # Verify customer structure
        if customers:
            customer = customers[0]
            assert "id" in customer
            assert "name" in customer
            
            # If using mock, verify expected data
            if mock_odoo_server:
                assert customer["name"] == "Customer 1"
    
    def test_retrieve_products(self, odoo_connector, mock_odoo_server):
        """Test retrieving products from Odoo."""
        # Skip this test if using real Odoo and no connection details provided
        if os.environ.get("TAXPOYNT_TEST_REAL_ODOO", "false").lower() == "true":
            if not os.environ.get("TAXPOYNT_TEST_ODOO_URL"):
                pytest.skip("No real Odoo connection details provided")
        
        # Connect to Odoo
        odoo_connector.connect()
        
        # Get products
        products = odoo_connector.get_products(limit=10)
        
        # Verify we received products
        assert isinstance(products, list)
        assert len(products) > 0
        
        # Verify product structure
        if products:
            product = products[0]
            assert "id" in product
            assert "name" in product
            
            # If using mock, verify expected data
            if mock_odoo_server:
                assert product["name"] == "Product 1"
    
    def test_integration_service_connection(self, odoo_config, mock_odoo_server):
        """Test connecting to Odoo through the integration service."""
        # Skip this test if using real Odoo and no connection details provided
        if os.environ.get("TAXPOYNT_TEST_REAL_ODOO", "false").lower() == "true":
            if not os.environ.get("TAXPOYNT_TEST_ODOO_URL"):
                pytest.skip("No real Odoo connection details provided")
        
        # Create a mock integration
        integration = MagicMock(spec=Integration)
        integration.id = uuid.uuid4()
        integration.type = "odoo"
        integration.config = odoo_config
        
        # Mock the database operations
        with patch("app.crud.integration.get") as mock_get:
            mock_get.return_value = integration
            
            # Create an integration service
            service = IntegrationService()
            
            # Test the connection
            result = service.test_connection(str(integration.id))
            
            # Verify the connection test was successful
            assert result["status"] == "success"
            
            # If using mock, verify the authenticate method was called
            if mock_odoo_server:
                mock_odoo_server["common"].authenticate.assert_called_once()
    
    def test_error_handling(self, odoo_config, mock_odoo_server):
        """Test error handling in Odoo connection."""
        # Skip this test if using real Odoo
        if os.environ.get("TAXPOYNT_TEST_REAL_ODOO", "false").lower() == "true":
            pytest.skip("Cannot test error handling with real Odoo")
        
        # Make the authenticate method raise an exception
        mock_odoo_server["common"].authenticate.side_effect = Exception("Connection error")
        
        # Create an OdooConnector with the modified mock
        odoo_connector = OdooConnector(odoo_config)
        
        # Try to connect
        result = odoo_connector.connect()
        
        # Verify the connection failed
        assert result == False
        
        # Check the status
        status = odoo_connector.check_connection_status()
        assert status["connected"] == False
        assert "error" in status
