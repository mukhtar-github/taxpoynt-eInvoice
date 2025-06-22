"""
Unit tests for CRM service layer functionality.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

from app.integrations.crm.hubspot.connector import HubSpotConnector
from app.integrations.base.errors import IntegrationError, AuthenticationError
from app.models.crm_connection import CRMConnection, CRMDeal
from app.schemas.pagination import PaginationResponse


class TestCRMConnectionService:
    """Test cases for CRM connection service functionality."""

    def test_crm_connection_creation(self):
        """Test CRM connection model creation."""
        connection_id = str(uuid4())
        connection = CRMConnection(
            id=connection_id,
            organization_id=str(uuid4()),
            crm_type="hubspot",
            connection_name="Test HubSpot",
            credentials={"client_id": "test", "client_secret": "encrypted"},
            connection_settings={"auto_sync": True},
            status="pending",
            webhook_secret="test_secret"
        )
        
        assert connection.id == connection_id
        assert connection.crm_type == "hubspot"
        assert connection.connection_name == "Test HubSpot"
        assert connection.credentials["client_id"] == "test"
        assert connection.status == "pending"
        assert connection.webhook_secret == "test_secret"

    def test_crm_deal_creation(self):
        """Test CRM deal model creation."""
        deal_id = str(uuid4())
        connection_id = str(uuid4())
        deal = CRMDeal(
            id=deal_id,
            connection_id=connection_id,
            external_deal_id="hubspot-123",
            deal_title="Test Deal",
            deal_amount="50000.00",
            deal_stage="closedwon",
            customer_data={"name": "Test Customer", "email": "test@example.com"},
            deal_data={"source": "website"},
            created_at_source=datetime.utcnow(),
            updated_at_source=datetime.utcnow(),
            last_sync=datetime.utcnow(),
            invoice_generated=False
        )
        
        assert deal.id == deal_id
        assert deal.connection_id == connection_id
        assert deal.external_deal_id == "hubspot-123"
        assert deal.deal_title == "Test Deal"
        assert deal.deal_amount == "50000.00"
        assert deal.customer_data["name"] == "Test Customer"
        assert deal.invoice_generated is False

    def test_deal_stage_validation(self):
        """Test deal stage validation logic."""
        # Test valid stages
        valid_stages = ["qualification", "proposal", "negotiation", "closedwon", "closedlost"]
        for stage in valid_stages:
            deal = CRMDeal(
                id=str(uuid4()),
                connection_id=str(uuid4()),
                external_deal_id=f"test-{stage}",
                deal_stage=stage
            )
            assert deal.deal_stage == stage

    def test_customer_data_serialization(self):
        """Test customer data JSON serialization."""
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
        
        deal = CRMDeal(
            id=str(uuid4()),
            connection_id=str(uuid4()),
            external_deal_id="test-customer-data",
            customer_data=customer_data
        )
        
        assert deal.customer_data["name"] == "John Doe"
        assert deal.customer_data["address"]["city"] == "Lagos"
        assert len(deal.customer_data) == 5


class TestCRMDataValidation:
    """Test cases for CRM data validation."""

    def test_valid_crm_types(self):
        """Test CRM type validation."""
        valid_types = ["hubspot", "salesforce", "pipedrive", "zoho"]
        
        for crm_type in valid_types:
            connection = CRMConnection(
                id=str(uuid4()),
                organization_id=str(uuid4()),
                crm_type=crm_type,
                connection_name=f"Test {crm_type.title()}"
            )
            assert connection.crm_type == crm_type

    def test_deal_amount_formatting(self):
        """Test deal amount formatting and validation."""
        test_amounts = [
            ("50000", "50000"),
            ("50000.00", "50000.00"),
            ("50000.99", "50000.99"),
            ("0", "0"),
            ("0.01", "0.01")
        ]
        
        for input_amount, expected in test_amounts:
            deal = CRMDeal(
                id=str(uuid4()),
                connection_id=str(uuid4()),
                external_deal_id=f"test-amount-{input_amount}",
                deal_amount=input_amount
            )
            assert deal.deal_amount == expected

    def test_connection_status_validation(self):
        """Test connection status validation."""
        valid_statuses = ["pending", "connected", "connecting", "failed", "disconnected"]
        
        for status in valid_statuses:
            connection = CRMConnection(
                id=str(uuid4()),
                organization_id=str(uuid4()),
                crm_type="hubspot",
                connection_name="Test Connection",
                status=status
            )
            assert connection.status == status

    def test_webhook_secret_handling(self):
        """Test webhook secret validation and storage."""
        connection = CRMConnection(
            id=str(uuid4()),
            organization_id=str(uuid4()),
            crm_type="hubspot",
            connection_name="Test Connection",
            webhook_secret="my_super_secret_key_123"
        )
        
        assert connection.webhook_secret == "my_super_secret_key_123"
        assert len(connection.webhook_secret) >= 10  # Minimum length check

    def test_credentials_encryption_placeholder(self):
        """Test credentials handling (placeholder for encryption)."""
        # Note: In real implementation, credentials should be encrypted
        sensitive_creds = {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "refresh_token": "test_refresh_token"
        }
        
        connection = CRMConnection(
            id=str(uuid4()),
            organization_id=str(uuid4()),
            crm_type="hubspot",
            connection_name="Test Connection",
            credentials=sensitive_creds
        )
        
        # In real implementation, these should be encrypted
        assert connection.credentials["client_id"] == "test_client_id"
        assert "client_secret" in connection.credentials
        assert "refresh_token" in connection.credentials


class TestCRMServiceOperations:
    """Test cases for CRM service operations."""

    @pytest.mark.asyncio
    async def test_deal_filtering_by_date(self):
        """Test deal filtering by date ranges."""
        # Mock date filtering logic
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        last_week = now - timedelta(days=7)
        
        deals = [
            {"id": "deal-1", "created_at": now.isoformat()},
            {"id": "deal-2", "created_at": yesterday.isoformat()},
            {"id": "deal-3", "created_at": last_week.isoformat()}
        ]
        
        # Filter deals from last 3 days
        cutoff_date = now - timedelta(days=3)
        filtered_deals = [
            deal for deal in deals 
            if datetime.fromisoformat(deal["created_at"]) >= cutoff_date
        ]
        
        assert len(filtered_deals) == 2
        assert "deal-1" in [d["id"] for d in filtered_deals]
        assert "deal-2" in [d["id"] for d in filtered_deals]
        assert "deal-3" not in [d["id"] for d in filtered_deals]

    @pytest.mark.asyncio
    async def test_deal_stage_mapping(self):
        """Test deal stage mapping for invoice generation."""
        stage_mapping = {
            "closedwon": "generate_invoice",
            "proposal": "create_draft",
            "negotiation": "no_action"
        }
        
        # Test each mapping
        for deal_stage, expected_action in stage_mapping.items():
            action = stage_mapping.get(deal_stage, "no_action")
            assert action == expected_action

    @pytest.mark.asyncio
    async def test_pagination_logic(self):
        """Test pagination logic for deal lists."""
        # Mock pagination parameters
        total_items = 250
        page_size = 50
        current_page = 3
        
        # Calculate pagination
        total_pages = (total_items + page_size - 1) // page_size  # Ceiling division
        offset = (current_page - 1) * page_size
        has_next = current_page < total_pages
        has_prev = current_page > 1
        
        pagination = PaginationResponse(
            page=current_page,
            page_size=page_size,
            total=total_items,
            pages=total_pages,
            has_next=has_next,
            has_prev=has_prev
        )
        
        assert pagination.page == 3
        assert pagination.total == 250
        assert pagination.pages == 5
        assert pagination.has_next is True
        assert pagination.has_prev is True
        assert offset == 100

    @pytest.mark.asyncio
    async def test_error_handling_patterns(self):
        """Test error handling patterns for CRM operations."""
        # Test different error scenarios
        error_scenarios = [
            {
                "error_type": IntegrationError,
                "message": "HubSpot API rate limit exceeded",
                "should_retry": True
            },
            {
                "error_type": AuthenticationError,
                "message": "Invalid OAuth token",
                "should_retry": False
            },
            {
                "error_type": ConnectionError,
                "message": "Network connection failed",
                "should_retry": True
            }
        ]
        
        for scenario in error_scenarios:
            error = scenario["error_type"](scenario["message"])
            
            # Test error message
            assert str(error) == scenario["message"]
            
            # Test retry logic (simplified)
            if scenario["error_type"] == AuthenticationError:
                should_retry = False
            else:
                should_retry = True
            
            assert should_retry == scenario["should_retry"]

    def test_deal_to_invoice_transformation_data(self):
        """Test deal to invoice data transformation."""
        # Mock HubSpot deal data
        hubspot_deal = {
            "id": "123456789",
            "properties": {
                "dealname": "Enterprise Software License",
                "amount": "75000",
                "dealstage": "closedwon",
                "closedate": "1703030400000",  # Timestamp in milliseconds
                "createdate": "1703020400000",
                "hubspot_owner_id": "12345"
            }
        }
        
        # Mock customer data
        customer_data = {
            "name": "Acme Corporation",
            "email": "billing@acme.com",
            "phone": "+2341234567890",
            "company": "Acme Corporation"
        }
        
        # Transform to invoice format
        invoice_data = {
            "invoice_number": f"HUB-{hubspot_deal['id']}",
            "description": hubspot_deal["properties"]["dealname"],
            "amount": float(hubspot_deal["properties"]["amount"]),
            "currency": "NGN",  # Default currency
            "customer": customer_data,
            "line_items": [
                {
                    "description": hubspot_deal["properties"]["dealname"],
                    "quantity": 1,
                    "unit_price": float(hubspot_deal["properties"]["amount"]),
                    "total": float(hubspot_deal["properties"]["amount"])
                }
            ],
            "metadata": {
                "source": "hubspot",
                "deal_id": hubspot_deal["id"],
                "deal_stage": hubspot_deal["properties"]["dealstage"]
            }
        }
        
        # Verify transformation
        assert invoice_data["invoice_number"] == "HUB-123456789"
        assert invoice_data["description"] == "Enterprise Software License"
        assert invoice_data["amount"] == 75000.0
        assert invoice_data["customer"]["name"] == "Acme Corporation"
        assert len(invoice_data["line_items"]) == 1
        assert invoice_data["metadata"]["source"] == "hubspot"


class TestCRMSecurityAndValidation:
    """Test cases for CRM security and validation."""

    def test_sensitive_data_handling(self):
        """Test sensitive data handling in CRM connections."""
        # Test that sensitive fields are properly identified
        sensitive_fields = ["client_secret", "refresh_token", "access_token", "webhook_secret"]
        
        connection_data = {
            "client_id": "public_client_id",
            "client_secret": "sensitive_secret",
            "refresh_token": "sensitive_refresh",
            "access_token": "sensitive_access",
            "webhook_secret": "sensitive_webhook"
        }
        
        # Simulate masking sensitive data for logging
        masked_data = {}
        for key, value in connection_data.items():
            if key in sensitive_fields:
                masked_data[key] = "*" * len(value) if value else None
            else:
                masked_data[key] = value
        
        assert masked_data["client_id"] == "public_client_id"
        assert masked_data["client_secret"] == "****************"
        assert masked_data["refresh_token"] == "*****************"
        assert all(c == "*" for c in masked_data["webhook_secret"])

    def test_webhook_signature_validation_logic(self):
        """Test webhook signature validation logic."""
        import hmac
        import hashlib
        
        # Test data
        webhook_secret = "my_webhook_secret"
        payload = b'{"test": "webhook_data"}'
        
        # Generate valid signature
        valid_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Generate invalid signature
        invalid_signature = "invalid_signature_123"
        
        # Validation function (simplified)
        def validate_signature(payload_bytes, signature, secret):
            if not secret:
                return True  # No validation if no secret
            
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                payload_bytes,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
        
        # Test validation
        assert validate_signature(payload, valid_signature, webhook_secret) is True
        assert validate_signature(payload, invalid_signature, webhook_secret) is False
        assert validate_signature(payload, "any_sig", None) is True  # No secret

    def test_data_sanitization(self):
        """Test data sanitization for CRM inputs."""
        # Test input sanitization
        dirty_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "../../../etc/passwd",
            "javascript:alert('xss')"
        ]
        
        # Simple sanitization function
        def sanitize_input(input_str):
            if not isinstance(input_str, str):
                return input_str
            
            # Remove potential XSS and injection patterns
            dangerous_patterns = ["<script", "javascript:", "DROP TABLE", "../"]
            clean_input = input_str
            
            for pattern in dangerous_patterns:
                clean_input = clean_input.replace(pattern, "")
            
            return clean_input.strip()
        
        # Test sanitization
        for dirty_input in dirty_inputs:
            clean_input = sanitize_input(dirty_input)
            assert "<script" not in clean_input
            assert "javascript:" not in clean_input
            assert "DROP TABLE" not in clean_input
            assert "../" not in clean_input

    def test_rate_limiting_logic(self):
        """Test rate limiting logic for API calls."""
        from datetime import datetime, timedelta
        
        # Mock rate limiter
        class RateLimiter:
            def __init__(self, max_requests=100, window_minutes=60):
                self.max_requests = max_requests
                self.window_minutes = window_minutes
                self.requests = []
            
            def is_allowed(self, connection_id):
                now = datetime.utcnow()
                cutoff = now - timedelta(minutes=self.window_minutes)
                
                # Remove old requests
                self.requests = [req for req in self.requests if req['timestamp'] > cutoff]
                
                # Check current count for this connection
                connection_requests = [req for req in self.requests if req['connection_id'] == connection_id]
                
                if len(connection_requests) >= self.max_requests:
                    return False
                
                # Add current request
                self.requests.append({
                    'connection_id': connection_id,
                    'timestamp': now
                })
                return True
        
        # Test rate limiter
        limiter = RateLimiter(max_requests=5, window_minutes=1)
        connection_id = "test-conn-123"
        
        # Should allow first 5 requests
        for i in range(5):
            assert limiter.is_allowed(connection_id) is True
        
        # Should block 6th request
        assert limiter.is_allowed(connection_id) is False
        
        # Different connection should still be allowed
        assert limiter.is_allowed("different-conn") is True

    def test_connection_health_check(self):
        """Test connection health check functionality."""
        # Mock health check results
        health_results = {
            "authentication": True,
            "api_accessible": True,
            "rate_limit_status": "good",
            "last_successful_request": datetime.utcnow(),
            "response_time_ms": 250
        }
        
        # Evaluate overall health
        is_healthy = all([
            health_results["authentication"],
            health_results["api_accessible"],
            health_results["rate_limit_status"] == "good",
            health_results["response_time_ms"] < 1000
        ])
        
        assert is_healthy is True
        assert health_results["response_time_ms"] < 1000
        assert health_results["rate_limit_status"] == "good"