"""
Test cases for HubSpot CRM integration connector.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from app.integrations.crm.hubspot.connector import HubSpotConnector, get_hubspot_connector
from app.integrations.crm.hubspot.webhooks import HubSpotWebhookProcessor, HubSpotWebhookEvent
from app.integrations.base.errors import IntegrationError, AuthenticationError


class TestHubSpotConnector:
    """Test cases for HubSpotConnector."""

    def test_init(self):
        """Test HubSpotConnector initialization."""
        config = {
            "connection_id": "test-123",
            "auth": {
                "auth_type": "oauth2",
                "token_url": "https://api.hubapi.com/oauth/v1/token",
                "credentials": {
                    "client_id": "test_client",
                    "client_secret": "test_secret",
                    "refresh_token": "test_refresh"
                }
            }
        }
        
        connector = HubSpotConnector(config)
        assert connector.config == config
        assert connector.api_base_url == "https://api.hubapi.com"
        assert connector._connection_id == "test-123"
    
    @pytest.mark.asyncio
    @patch('app.integrations.crm.hubspot.connector.OAuth2Auth')
    async def test_authenticate_success(self, mock_oauth2_auth):
        """Test successful authentication."""
        # Mock OAuth2Auth instance
        mock_auth_instance = Mock()
        mock_auth_instance.get_access_token = AsyncMock(
            return_value=("test_token", datetime.now())
        )
        mock_oauth2_auth.return_value = mock_auth_instance
        
        config = {
            "auth": {
                "auth_type": "oauth2",
                "credentials": {
                    "client_id": "test_client",
                    "client_secret": "test_secret"
                }
            }
        }
        
        connector = HubSpotConnector(config)
        connector.auth_handler = mock_auth_instance
        
        result = await connector.authenticate()
        
        assert "access_token" in result
        assert result["access_token"] == "test_token"
        assert "expires_at" in result
    
    @pytest.mark.asyncio
    async def test_authenticate_unsupported_method(self):
        """Test authentication with unsupported method."""
        config = {
            "auth": {
                "auth_type": "basic",
                "credentials": {
                    "username": "test",
                    "password": "test"
                }
            }
        }
        
        connector = HubSpotConnector(config)
        
        with pytest.raises(AuthenticationError, match="Unsupported authentication method"):
            await connector.authenticate()
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_get_deals_success(self, mock_client):
        """Test successful deal retrieval."""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "results": [
                {
                    "id": "123",
                    "properties": {
                        "dealname": "Test Deal",
                        "amount": "50000",
                        "dealstage": "closedwon",
                        "closedate": "2025-06-20",
                        "createdate": "2025-06-18"
                    }
                }
            ],
            "paging": {
                "next": {"after": "456"}
            }
        }
        
        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        # Mock authentication
        config = {
            "auth": {
                "auth_type": "oauth2",
                "credentials": {"client_id": "test", "client_secret": "test"}
            }
        }
        
        connector = HubSpotConnector(config)
        connector._authenticated = True
        
        # Mock auth handler
        mock_auth_handler = Mock()
        mock_auth_handler.prepare_headers = AsyncMock(
            return_value={"Authorization": "Bearer test_token"}
        )
        connector.auth_handler = mock_auth_handler
        
        result = await connector.get_deals(limit=10, offset=0)
        
        assert "results" in result
        assert len(result["results"]) == 1
        assert result["results"][0]["id"] == "123"
        assert result["results"][0]["properties"]["dealname"] == "Test Deal"
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_get_deal_by_id_success(self, mock_client):
        """Test successful single deal retrieval."""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "id": "123",
            "properties": {
                "dealname": "Test Deal",
                "amount": "50000",
                "dealstage": "closedwon",
                "closedate": "2025-06-20"
            }
        }
        
        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        config = {
            "auth": {
                "auth_type": "oauth2",
                "credentials": {"client_id": "test", "client_secret": "test"}
            }
        }
        
        connector = HubSpotConnector(config)
        connector._authenticated = True
        
        # Mock auth handler
        mock_auth_handler = Mock()
        mock_auth_handler.prepare_headers = AsyncMock(
            return_value={"Authorization": "Bearer test_token"}
        )
        connector.auth_handler = mock_auth_handler
        
        result = await connector.get_deal_by_id("123")
        
        assert result["id"] == "123"
        assert result["properties"]["dealname"] == "Test Deal"
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_transform_deal_to_invoice(self, mock_client):
        """Test deal to invoice transformation."""
        # Mock customer data response
        mock_associations_response = Mock()
        mock_associations_response.raise_for_status = Mock()
        mock_associations_response.json.return_value = {
            "results": [{"id": "456"}]
        }
        
        mock_contact_response = Mock()
        mock_contact_response.raise_for_status = Mock()
        mock_contact_response.json.return_value = {
            "properties": {
                "firstname": "John",
                "lastname": "Doe",
                "email": "john.doe@example.com",
                "phone": "+2341234567890"
            }
        }
        
        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(side_effect=[
            mock_associations_response,
            mock_contact_response
        ])
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        config = {
            "auth": {
                "auth_type": "oauth2",
                "credentials": {"client_id": "test", "client_secret": "test"}
            }
        }
        
        connector = HubSpotConnector(config)
        connector._authenticated = True
        
        # Mock auth handler
        mock_auth_handler = Mock()
        mock_auth_handler.prepare_headers = AsyncMock(
            return_value={"Authorization": "Bearer test_token"}
        )
        connector.auth_handler = mock_auth_handler
        
        deal_data = {
            "id": "123",
            "properties": {
                "dealname": "Test Deal",
                "amount": "50000",
                "dealstage": "closedwon",
                "closedate": "2025-06-20"
            }
        }
        
        result = await connector.transform_deal_to_invoice(deal_data)
        
        assert result["invoice_number"] == "HUB-123"
        assert result["amount"] == "50000"
        assert result["description"] == "Test Deal"
        assert result["customer"]["name"] == "John Doe"
        assert result["customer"]["email"] == "john.doe@example.com"
        assert result["metadata"]["source"] == "hubspot"
        assert result["metadata"]["deal_id"] == "123"


class TestHubSpotWebhookProcessor:
    """Test cases for HubSpotWebhookProcessor."""

    def test_init(self):
        """Test webhook processor initialization."""
        config = {
            "connection_id": "test-123",
            "webhook_secret": "test_secret",
            "auth": {"auth_type": "oauth2"}
        }
        
        processor = HubSpotWebhookProcessor(config)
        assert processor.config == config
        assert processor.webhook_secret == "test_secret"
    
    def test_verify_webhook_signature_valid(self):
        """Test webhook signature verification with valid signature."""
        config = {"webhook_secret": "test_secret"}
        processor = HubSpotWebhookProcessor(config)
        
        body = b'{"test": "data"}'
        
        import hmac
        import hashlib
        expected_signature = hmac.new(
            "test_secret".encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()
        
        result = processor.verify_webhook_signature(body, expected_signature)
        assert result is True
    
    def test_verify_webhook_signature_invalid(self):
        """Test webhook signature verification with invalid signature."""
        config = {"webhook_secret": "test_secret"}
        processor = HubSpotWebhookProcessor(config)
        
        body = b'{"test": "data"}'
        invalid_signature = "invalid_signature"
        
        result = processor.verify_webhook_signature(body, invalid_signature)
        assert result is False
    
    def test_verify_webhook_signature_no_secret(self):
        """Test webhook signature verification with no secret configured."""
        config = {}
        processor = HubSpotWebhookProcessor(config)
        
        body = b'{"test": "data"}'
        signature = "any_signature"
        
        result = processor.verify_webhook_signature(body, signature)
        assert result is True  # Returns True when no secret configured
    
    @pytest.mark.asyncio
    async def test_process_webhook_events_success(self):
        """Test successful webhook event processing."""
        config = {
            "connection_id": "test-123",
            "settings": {
                "deal_stage_mapping": {
                    "closedwon": "generate_invoice"
                }
            }
        }
        
        processor = HubSpotWebhookProcessor(config)
        
        # Mock the connector
        mock_connector = Mock()
        mock_connector.get_deal_by_id = AsyncMock(return_value={
            "id": "123",
            "properties": {
                "dealname": "Test Deal",
                "amount": "50000",
                "dealstage": "closedwon"
            }
        })
        mock_connector.transform_deal_to_invoice = AsyncMock(return_value={
            "invoice_number": "HUB-123",
            "amount": 50000
        })
        processor.connector = mock_connector
        
        # Create test event
        event = HubSpotWebhookEvent(
            eventId="event-123",
            subscriptionId="sub-123",
            portalId=12345,
            appId=67890,
            occurredAt=datetime.now(),
            subscriptionType="deal.propertyChange",
            attemptNumber=1,
            objectId="123",
            changeSource="CRM_UI",
            changeFlag="UPDATED",
            propertyName="dealstage",
            propertyValue="closedwon"
        )
        
        result = await processor.process_webhook_events([event])
        
        assert result["processed"] == 1
        assert result["errors"] == 0
        assert len(result["events"]) == 1
        assert result["events"][0]["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_handle_deal_stage_change_with_invoice_generation(self):
        """Test deal stage change that triggers invoice generation."""
        config = {
            "settings": {
                "deal_stage_mapping": {
                    "closedwon": "generate_invoice"
                }
            }
        }
        
        processor = HubSpotWebhookProcessor(config)
        
        # Mock the connector
        mock_connector = Mock()
        mock_connector.transform_deal_to_invoice = AsyncMock(return_value={
            "invoice_number": "HUB-123",
            "amount": 50000
        })
        processor.connector = mock_connector
        
        event = HubSpotWebhookEvent(
            eventId="event-123",
            subscriptionId="sub-123",
            portalId=12345,
            appId=67890,
            occurredAt=datetime.now(),
            subscriptionType="deal.propertyChange",
            attemptNumber=1,
            objectId="123",
            changeSource="CRM_UI",
            changeFlag="UPDATED",
            propertyName="dealstage",
            propertyValue="closedwon"
        )
        
        deal_data = {
            "id": "123",
            "properties": {
                "dealname": "Test Deal",
                "amount": "50000",
                "dealstage": "closedwon"
            }
        }
        
        result = await processor.handle_deal_stage_change(event, deal_data)
        
        assert result["status"] == "processed"
        assert result["action"] == "invoice_generated"
        assert result["invoice_number"] == "HUB-123"
        assert result["deal_stage"] == "closedwon"
    
    @pytest.mark.asyncio
    async def test_handle_deal_creation_with_auto_invoice(self):
        """Test deal creation with auto invoice generation enabled."""
        config = {
            "settings": {
                "auto_generate_invoice_on_creation": True
            }
        }
        
        processor = HubSpotWebhookProcessor(config)
        
        # Mock the connector
        mock_connector = Mock()
        mock_connector.get_deal_by_id = AsyncMock(return_value={
            "id": "123",
            "properties": {"dealname": "New Deal", "amount": "25000"}
        })
        mock_connector.transform_deal_to_invoice = AsyncMock(return_value={
            "invoice_number": "HUB-123",
            "amount": 25000
        })
        processor.connector = mock_connector
        
        event = HubSpotWebhookEvent(
            eventId="event-123",
            subscriptionId="sub-123",
            portalId=12345,
            appId=67890,
            occurredAt=datetime.now(),
            subscriptionType="deal.creation",
            attemptNumber=1,
            objectId="123",
            changeSource="CRM_UI",
            changeFlag="CREATED"
        )
        
        result = await processor.handle_deal_creation(event)
        
        assert result["status"] == "processed"
        assert result["action"] == "deal_created_with_invoice"
        assert result["invoice_number"] == "HUB-123"


class TestGetHubSpotConnector:
    """Test cases for get_hubspot_connector function."""

    def test_get_connector_creates_new_instance(self):
        """Test that get_hubspot_connector creates a new instance."""
        config = {
            "connection_id": "test-123",
            "auth": {"auth_type": "oauth2"}
        }
        
        connector = get_hubspot_connector(config)
        
        assert isinstance(connector, HubSpotConnector)
        assert connector.config == config
    
    def test_get_connector_reuses_instance_for_same_config(self):
        """Test that get_hubspot_connector reuses instance for same config."""
        config = {
            "connection_id": "test-123",
            "auth": {"auth_type": "oauth2"}
        }
        
        connector1 = get_hubspot_connector(config)
        connector2 = get_hubspot_connector(config)
        
        assert connector1 is connector2
    
    def test_get_connector_creates_new_instance_for_different_config(self):
        """Test that get_hubspot_connector creates new instance for different config."""
        config1 = {
            "connection_id": "test-123",
            "auth": {"auth_type": "oauth2"}
        }
        
        config2 = {
            "connection_id": "test-456",
            "auth": {"auth_type": "oauth2"}
        }
        
        connector1 = get_hubspot_connector(config1)
        connector2 = get_hubspot_connector(config2)
        
        assert connector1 is not connector2
        assert connector1.config == config1
        assert connector2.config == config2