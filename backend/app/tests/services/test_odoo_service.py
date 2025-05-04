import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

import odoorpc
from app.services.odoo_service import test_odoo_connection, fetch_odoo_invoices
from app.schemas.integration import OdooConnectionTestRequest, OdooConfig, OdooAuthMethod


class TestOdooService:
    """Test suite for Odoo service functions using OdooRPC"""
    
    @patch('odoorpc.ODOO')
    def test_connection_success(self, mock_odoo):
        """Test successful connection to Odoo using OdooRPC"""
        # Setup mock
        mock_instance = MagicMock()
        mock_odoo.return_value = mock_instance
        
        # Mock user and version information
        mock_user = MagicMock()
        mock_user.name = "Test User"
        mock_env = {'res.users': MagicMock()}
        mock_env['res.users'].browse.return_value = mock_user
        mock_instance.env = mock_env
        mock_instance.env.uid = 1
        mock_instance.version = {
            'server_version': '14.0',
            'server_version_info': [14, 0, 0, 'final', 0, '']
        }
        
        # Mock partners search to verify permissions
        mock_partner = MagicMock()
        mock_env['res.partner'] = mock_partner
        mock_partner.search.return_value = [1, 2, 3]
        
        # Create test request
        connection_params = OdooConnectionTestRequest(
            url="https://test.odoo.com",
            database="test_db",
            username="test_user",
            auth_method=OdooAuthMethod.API_KEY,
            api_key="test_api_key"
        )
        
        # Call function
        result = test_odoo_connection(connection_params)
        
        # Assertions
        assert result["success"] is True
        assert "Successfully connected" in result["message"]
        assert result["details"]["uid"] == 1
        assert result["details"]["user_name"] == "Test User"
        assert result["details"]["version_info"] == mock_instance.version
        assert result["details"]["partner_count"] == 3
    
    @patch('odoorpc.ODOO')
    def test_connection_error(self, mock_odoo):
        """Test failed connection to Odoo"""
        # Setup mock to raise exception
        mock_odoo.side_effect = odoorpc.error.RPCError("Invalid credentials")
        
        # Create test request
        connection_params = OdooConnectionTestRequest(
            url="https://test.odoo.com",
            database="test_db",
            username="test_user",
            auth_method=OdooAuthMethod.API_KEY,
            api_key="invalid_key"
        )
        
        # Call function
        result = test_odoo_connection(connection_params)
        
        # Assertions
        assert result["success"] is False
        assert "OdooRPC error" in result["message"]
        assert "Invalid credentials" in result["message"]
    
    @patch('odoorpc.ODOO')
    def test_fetch_invoices(self, mock_odoo):
        """Test fetching invoices from Odoo"""
        # Setup mock
        mock_instance = MagicMock()
        mock_odoo.return_value = mock_instance
        
        # Mock invoice model and search
        mock_invoice_model = MagicMock()
        mock_instance.env = {'account.move': mock_invoice_model}
        
        # Mock invoice IDs found
        mock_invoice_model.search.return_value = [1, 2]
        
        # Mock invoice records
        mock_invoice1 = self._create_mock_invoice(1, "INV/2024/0001", "posted", 100.0)
        mock_invoice2 = self._create_mock_invoice(2, "INV/2024/0002", "posted", 200.0)
        
        # Make browse method return mock invoices
        def mock_browse(ids):
            invoice_map = {1: mock_invoice1, 2: mock_invoice2}
            return [invoice_map[id] for id in ids]
        
        mock_invoice_model.browse = mock_browse
        
        # Create config
        config = OdooConfig(
            url="https://test.odoo.com",
            database="test_db",
            username="test_user",
            auth_method=OdooAuthMethod.API_KEY,
            api_key="test_api_key"
        )
        
        # Call function
        invoices = fetch_odoo_invoices(config, from_date=None, limit=10)
        
        # Assertions
        assert len(invoices) == 2
        assert invoices[0]["name"] == "INV/2024/0001"
        assert invoices[0]["amount_total"] == 100.0
        assert invoices[1]["name"] == "INV/2024/0002"
        assert invoices[1]["amount_total"] == 200.0
        
        # Verify search was called with correct parameters
        mock_invoice_model.search.assert_called_once()
        args, kwargs = mock_invoice_model.search.call_args
        assert ('move_type', '=', 'out_invoice') in args[0]
        assert ('state', '=', 'posted') in args[0]
        assert kwargs == {'limit': 10, 'offset': 0}
    
    def _create_mock_invoice(self, id, name, state, amount):
        """Helper method to create a mock invoice object"""
        mock_invoice = MagicMock()
        mock_invoice.id = id
        mock_invoice.name = name
        mock_invoice.state = state
        mock_invoice.amount_total = amount
        mock_invoice.amount_untaxed = amount * 0.9
        mock_invoice.amount_tax = amount * 0.1
        mock_invoice.invoice_date = "2024-06-01"
        mock_invoice.invoice_date_due = "2024-07-01"
        
        # Mock partner
        mock_partner = MagicMock()
        mock_partner.id = 42
        mock_partner.name = "Test Partner"
        mock_partner.vat = "VAT123456"
        mock_partner.email = "partner@example.com"
        mock_partner.phone = "123456789"
        mock_invoice.partner_id = mock_partner
        
        # Mock currency
        mock_currency = MagicMock()
        mock_currency.id = 1
        mock_currency.name = "EUR"
        mock_currency.symbol = "€"
        mock_invoice.currency_id = mock_currency
        
        # Mock invoice lines
        mock_line1 = self._create_mock_invoice_line(101, "Product 1", 2, 45.0)
        mock_line2 = self._create_mock_invoice_line(102, "Product 2", 1, 10.0)
        mock_invoice.invoice_line_ids = [mock_line1, mock_line2]
        
        return mock_invoice
    
    def _create_mock_invoice_line(self, id, name, quantity, price_unit):
        """Helper method to create a mock invoice line object"""
        mock_line = MagicMock()
        mock_line.id = id
        mock_line.name = name
        mock_line.quantity = quantity
        mock_line.price_unit = price_unit
        mock_line.price_subtotal = quantity * price_unit
        
        # Mock product
        mock_product = MagicMock()
        mock_product.id = 200 + id
        mock_product.name = name
        mock_product.default_code = f"P{id}"
        mock_line.product_id = mock_product
        
        # Mock taxes
        mock_tax = MagicMock()
        mock_tax.id = 1
        mock_tax.name = "VAT 10%"
        mock_tax.amount = 10.0
        mock_line.tax_ids = [mock_tax]
        
        return mock_line
