"""
Test suite for Salesforce CRM Connector.

This module contains comprehensive tests for the Salesforce integration,
including authentication, data transformation, and webhook handling.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import json

from app.integrations.crm.salesforce.connector import SalesforceConnector
from app.integrations.crm.salesforce.models import (
    OpportunityToInvoiceTransformer,
    SalesforceDataValidator
)
from app.integrations.crm.salesforce.webhooks import SalesforceWebhookHandler
from app.integrations.base.errors import AuthenticationError, ConnectionError


class TestSalesforceConnector:
    """Test cases for SalesforceConnector."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return {
            "client_id": "test_client_id",
            "private_key": """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC7VJTUt9Us8cKB
wjKeNV+FyQhHfFx0yQiXMeniqNjAiGKtg1U2dJn5MZsQK+s2Zp2jZ1xE1QmZ2b1x
-----END PRIVATE KEY-----""",
            "username": "test@example.com",
            "sandbox": True,
            "connection_id": "test_connection_123"
        }
    
    @pytest.fixture
    def connector(self, mock_config):
        """Create a SalesforceConnector instance for testing."""
        return SalesforceConnector(mock_config)
    
    def test_connector_initialization(self, connector, mock_config):
        """Test connector initialization with valid config."""
        assert connector.client_id == mock_config["client_id"]
        assert connector.username == mock_config["username"]
        assert connector.sandbox is True
        assert connector.login_url == "https://test.salesforce.com"
        assert connector.api_version == "v58.0"
    
    def test_connector_initialization_missing_config(self):
        """Test connector initialization with missing required config."""
        with pytest.raises(ValueError, match="client_id is required"):
            SalesforceConnector({})
    
    @patch('app.integrations.crm.salesforce.connector.httpx.AsyncClient')
    async def test_successful_authentication(self, mock_client, connector):
        """Test successful JWT authentication."""
        # Mock the token response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "instance_url": "https://test.my.salesforce.com",
            "token_type": "Bearer"
        }
        
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        result = await connector.authenticate()
        
        assert result["success"] is True
        assert result["access_token"] == "test_access_token"
        assert result["instance_url"] == "https://test.my.salesforce.com"
        assert connector.access_token == "test_access_token"
        assert connector.instance_url == "https://test.my.salesforce.com"
    
    @patch('app.integrations.crm.salesforce.connector.httpx.AsyncClient')
    async def test_authentication_failure(self, mock_client, connector):
        """Test authentication failure."""
        # Mock the error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": "invalid_grant",
            "error_description": "authentication failure"
        }
        
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        with pytest.raises(AuthenticationError, match="authentication failure"):
            await connector.authenticate()
    
    @patch('app.integrations.crm.salesforce.connector.httpx.AsyncClient')
    async def test_get_opportunities(self, mock_client, connector):
        """Test retrieving opportunities from Salesforce."""
        # Set up authenticated state
        connector.access_token = "test_token"
        connector.instance_url = "https://test.my.salesforce.com"
        
        # Mock the opportunities response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = {
            "totalSize": 2,
            "done": True,
            "records": [
                {
                    "Id": "006XX000004TmiQ",
                    "Name": "Test Opportunity 1",
                    "Amount": 50000.0,
                    "StageName": "Closed Won",
                    "CloseDate": "2024-01-15",
                    "Account": {
                        "Name": "Test Account 1",
                        "Id": "001XX000003DHPj"
                    }
                },
                {
                    "Id": "006XX000004TmiR",
                    "Name": "Test Opportunity 2",
                    "Amount": 75000.0,
                    "StageName": "Proposal/Price Quote",
                    "CloseDate": "2024-02-15",
                    "Account": {
                        "Name": "Test Account 2",
                        "Id": "001XX000003DHPk"
                    }
                }
            ]
        }
        
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        result = await connector.get_opportunities(limit=10)
        
        assert result["total_size"] == 2
        assert len(result["opportunities"]) == 2
        assert result["opportunities"][0]["Name"] == "Test Opportunity 1"
        assert result["opportunities"][1]["Amount"] == 75000.0
    
    @patch('app.integrations.crm.salesforce.connector.httpx.AsyncClient')
    async def test_get_opportunity_by_id(self, mock_client, connector):
        """Test retrieving a specific opportunity by ID."""
        # Set up authenticated state
        connector.access_token = "test_token"
        connector.instance_url = "https://test.my.salesforce.com"
        
        # Mock the opportunity response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = {
            "totalSize": 1,
            "done": True,
            "records": [
                {
                    "Id": "006XX000004TmiQ",
                    "Name": "Test Opportunity",
                    "Amount": 50000.0,
                    "StageName": "Closed Won",
                    "CloseDate": "2024-01-15",
                    "Account": {
                        "Name": "Test Account",
                        "Id": "001XX000003DHPj"
                    }
                }
            ]
        }
        
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        result = await connector.get_opportunity_by_id("006XX000004TmiQ")
        
        assert result["Id"] == "006XX000004TmiQ"
        assert result["Name"] == "Test Opportunity"
        assert result["Amount"] == 50000.0
    
    def test_transform_opportunity_to_deal(self, connector):
        """Test transforming Salesforce opportunity to TaxPoynt deal format."""
        opportunity = {
            "Id": "006XX000004TmiQ",
            "Name": "Test Opportunity",
            "Amount": 50000.0,
            "StageName": "Closed Won",
            "CloseDate": "2024-01-15",
            "Probability": 90,
            "Type": "New Customer",
            "CreatedDate": "2024-01-01T10:00:00Z",
            "LastModifiedDate": "2024-01-10T15:30:00Z",
            "Account": {
                "Id": "001XX000003DHPj",
                "Name": "Test Account",
                "BillingStreet": "123 Test St",
                "BillingCity": "Lagos",
                "BillingState": "Lagos",
                "BillingCountry": "Nigeria",
                "BillingPostalCode": "100001",
                "Phone": "+2341234567890"
            },
            "Owner": {
                "Id": "005XX000001b2fX",
                "Name": "John Sales",
                "Email": "john.sales@company.com"
            }
        }
        
        deal = connector.transform_opportunity_to_deal(opportunity)
        
        assert deal["external_deal_id"] == "006XX000004TmiQ"
        assert deal["deal_title"] == "Test Opportunity"
        assert deal["deal_amount"] == "50000.0"
        assert deal["deal_currency"] == "USD"
        assert deal["deal_stage"] == "Closed Won"
        assert deal["deal_probability"] == 90
        
        # Check customer data
        customer_data = deal["customer_data"]
        assert customer_data["name"] == "Test Account"
        assert customer_data["company"] == "Test Account"
        assert customer_data["phone"] == "+2341234567890"
        assert customer_data["address"]["city"] == "Lagos"
        assert customer_data["address"]["country"] == "Nigeria"
        
        # Check deal data
        deal_data = deal["deal_data"]
        assert deal_data["type"] == "New Customer"
        assert deal_data["probability"] == 90
        assert deal_data["owner"]["name"] == "John Sales"
        assert deal_data["owner"]["email"] == "john.sales@company.com"


class TestOpportunityToInvoiceTransformer:
    """Test cases for OpportunityToInvoiceTransformer."""
    
    @pytest.fixture
    def transformer(self):
        """Create a transformer instance for testing."""
        return OpportunityToInvoiceTransformer()
    
    @pytest.fixture
    def sample_opportunity(self):
        """Sample opportunity data for testing."""
        return {
            "Id": "006XX000004TmiQ",
            "Name": "Test Opportunity",
            "Amount": 50000.0,
            "CloseDate": "2024-01-15",
            "StageName": "Closed Won",
            "Account": {
                "Id": "001XX000003DHPj",
                "Name": "Test Account",
                "BillingStreet": "123 Test St",
                "BillingCity": "Lagos",
                "BillingState": "Lagos",
                "BillingCountry": "Nigeria",
                "BillingPostalCode": "100001"
            }
        }
    
    def test_transform_opportunity_to_invoice(self, transformer, sample_opportunity):
        """Test transforming opportunity to invoice format."""
        invoice = transformer.transform_opportunity_to_invoice(sample_opportunity)
        
        assert invoice["invoice_number"] == "SF-004TmiQ"
        assert invoice["description"] == "Invoice for Test Opportunity"
        assert invoice["currency"] == "USD"
        assert invoice["subtotal"] == 50000.0
        assert invoice["tax_rate"] == 7.5
        assert invoice["tax_amount"] == 3750.0
        assert invoice["total"] == 53750.0
        
        # Check customer data
        customer = invoice["customer"]
        assert customer["name"] == "Test Account"
        assert customer["company"] == "Test Account"
        assert customer["address"]["city"] == "Lagos"
        
        # Check line items
        line_items = invoice["line_items"]
        assert len(line_items) == 1
        assert line_items[0]["description"] == "Test Opportunity"
        assert line_items[0]["quantity"] == 1
        assert line_items[0]["unit_price"] == 50000.0
        assert line_items[0]["tax_rate"] == 7.5
        
        # Check metadata
        metadata = invoice["metadata"]
        assert metadata["source"] == "salesforce"
        assert metadata["opportunity_id"] == "006XX000004TmiQ"
        assert metadata["opportunity_stage"] == "Closed Won"
    
    def test_transform_opportunity_to_deal(self, transformer, sample_opportunity):
        """Test transforming opportunity to deal format."""
        deal = transformer.transform_opportunity_to_deal(sample_opportunity)
        
        assert deal["external_deal_id"] == "006XX000004TmiQ"
        assert deal["deal_title"] == "Test Opportunity"
        assert deal["deal_amount"] == "50000.0"
        assert deal["deal_currency"] == "USD"
        assert deal["deal_stage"] == "Closed Won"
        assert deal["invoice_generated"] is False
        assert deal["sync_status"] == "success"
        
        # Check customer data structure
        customer_data = deal["customer_data"]
        assert customer_data["name"] == "Test Account"
        assert customer_data["company"] == "Test Account"
        assert customer_data["address"]["city"] == "Lagos"
        assert customer_data["custom_fields"]["account_id"] == "001XX000003DHPj"


class TestSalesforceDataValidator:
    """Test cases for SalesforceDataValidator."""
    
    @pytest.fixture
    def validator(self):
        """Create a validator instance for testing."""
        return SalesforceDataValidator()
    
    def test_validate_valid_opportunity(self, validator):
        """Test validating a valid opportunity."""
        opportunity = {
            "Id": "006XX000004TmiQ",
            "Name": "Test Opportunity",
            "Amount": 50000.0,
            "StageName": "Closed Won",
            "CloseDate": "2024-01-15T00:00:00Z",
            "Probability": 90,
            "Account": {
                "Name": "Test Account"
            }
        }
        
        result = validator.validate_opportunity(opportunity)
        
        assert result["valid"] is True
        assert len(result["issues"]) == 0
        assert result["opportunity_id"] == "006XX000004TmiQ"
    
    def test_validate_opportunity_missing_required_fields(self, validator):
        """Test validating an opportunity with missing required fields."""
        opportunity = {
            "Amount": 50000.0
            # Missing Id, Name, StageName
        }
        
        result = validator.validate_opportunity(opportunity)
        
        assert result["valid"] is False
        assert "Missing required field: Id" in result["issues"]
        assert "Missing required field: Name" in result["issues"]
        assert "Missing required field: StageName" in result["issues"]
    
    def test_validate_opportunity_invalid_amount(self, validator):
        """Test validating an opportunity with invalid amount."""
        opportunity = {
            "Id": "006XX000004TmiQ",
            "Name": "Test Opportunity",
            "Amount": -1000.0,  # Negative amount
            "StageName": "Closed Won"
        }
        
        result = validator.validate_opportunity(opportunity)
        
        assert result["valid"] is True  # Negative amounts are warnings, not errors
        assert "Negative amount detected" in result["warnings"]
    
    def test_validate_customer_data(self, validator):
        """Test validating customer data."""
        customer_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+2341234567890",
            "company": "Test Company",
            "address": {
                "street": "123 Test St",
                "city": "Lagos",
                "country": "Nigeria"
            }
        }
        
        result = validator.validate_customer_data(customer_data)
        
        assert result["valid"] is True
        assert len(result["issues"]) == 0
    
    def test_validate_customer_data_missing_name(self, validator):
        """Test validating customer data with missing name and company."""
        customer_data = {
            "email": "john.doe@example.com",
            "phone": "+2341234567890"
            # Missing name and company
        }
        
        result = validator.validate_customer_data(customer_data)
        
        assert result["valid"] is False
        assert "Either customer name or company name is required" in result["issues"]


class TestSalesforceWebhookHandler:
    """Test cases for SalesforceWebhookHandler."""
    
    @pytest.fixture
    def webhook_config(self):
        """Mock webhook configuration."""
        return {
            "connection_id": "test_connection_123",
            "webhook_secret": "test_webhook_secret",
            "connection_settings": {
                "deal_stage_mapping": {
                    "Closed Won": "generate_invoice",
                    "Proposal/Price Quote": "create_draft"
                },
                "auto_generate_invoice_on_creation": False
            }
        }
    
    @pytest.fixture
    def webhook_handler(self, webhook_config):
        """Create a webhook handler for testing."""
        return SalesforceWebhookHandler(webhook_config)
    
    def test_verify_webhook_signature(self, webhook_handler):
        """Test webhook signature verification."""
        import hmac
        import hashlib
        
        test_body = b'{"test": "data"}'
        expected_signature = hmac.new(
            b"test_webhook_secret",
            test_body,
            hashlib.sha256
        ).hexdigest()
        
        # Test valid signature
        assert webhook_handler.verify_webhook_signature(test_body, expected_signature) is True
        
        # Test invalid signature
        assert webhook_handler.verify_webhook_signature(test_body, "invalid_signature") is False
    
    async def test_handle_change_data_capture(self, webhook_handler):
        """Test handling Change Data Capture events."""
        cdc_event = {
            "ChangeEventHeader": {
                "changeType": "UPDATE",
                "changedFields": ["StageName", "Amount"],
                "entityName": "Opportunity",
                "recordIds": ["006XX000004TmiQ"]
            },
            "Id": "006XX000004TmiQ",
            "Name": "Test Opportunity",
            "StageName": "Closed Won"
        }
        
        result = await webhook_handler.handle_change_data_capture(cdc_event)
        
        assert result["success"] is True
        assert result["change_type"] == "UPDATE"
        assert result["entity_name"] == "Opportunity"
        assert len(result["results"]) == 1
    
    async def test_handle_platform_event(self, webhook_handler):
        """Test handling Platform Events."""
        platform_event = {
            "CreatedDate": "2024-01-01T12:00:00Z",
            "CreatedById": "005XX000001b2fX",
            "EventUuid": "test-uuid-123",
            "ReplayId": 12345,
            "OpportunityId__c": "006XX000004TmiQ",
            "ChangeType__c": "UPDATE"
        }
        
        result = await webhook_handler.handle_platform_event(platform_event)
        
        assert result["success"] is True
        assert result["change_type"] == "UPDATE"
        assert result["replay_id"] == 12345
        assert "006XX000004TmiQ" in result["message"]
    
    def test_determine_action(self, webhook_handler):
        """Test action determination logic."""
        connection_settings = webhook_handler.connection_config["connection_settings"]
        deal_stage_mapping = connection_settings["deal_stage_mapping"]
        auto_generate = connection_settings["auto_generate_invoice_on_creation"]
        
        # Test CREATE with auto-generate disabled
        action = webhook_handler._determine_action(
            "CREATE", [], {}, deal_stage_mapping, auto_generate
        )
        assert action == "sync_data"
        
        # Test UPDATE with stage change to Closed Won
        action = webhook_handler._determine_action(
            "UPDATE", ["StageName"], {"StageName": "Closed Won"}, deal_stage_mapping, auto_generate
        )
        assert action == "generate_invoice"
        
        # Test UPDATE with stage change to Proposal
        action = webhook_handler._determine_action(
            "UPDATE", ["StageName"], {"StageName": "Proposal/Price Quote"}, deal_stage_mapping, auto_generate
        )
        assert action == "create_draft"
        
        # Test UPDATE with amount change
        action = webhook_handler._determine_action(
            "UPDATE", ["Amount"], {"Amount": 60000}, deal_stage_mapping, auto_generate
        )
        assert action == "sync_data"
        
        # Test DELETE
        action = webhook_handler._determine_action(
            "DELETE", [], {}, deal_stage_mapping, auto_generate
        )
        assert action == "mark_deleted"


if __name__ == "__main__":
    pytest.main([__file__])