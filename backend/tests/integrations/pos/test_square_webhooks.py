"""
Test cases for Square webhook processing.
"""

import pytest
import json
import hmac
import hashlib
import base64
from unittest.mock import Mock, patch

from app.integrations.pos.square.connector import SquarePOSConnector


class TestSquareWebhooks:
    """Test cases for Square webhook processing."""
    
    def test_webhook_signature_verification_valid(self):
        """Test valid webhook signature verification."""
        config = {
            "webhook_signature_key": "test_signature_key",
            "webhook_url": "https://example.com/webhook"
        }
        
        connector = SquarePOSConnector(config)
        
        # Create test payload and signature
        payload = b'{"event_type": "payment.created"}'
        webhook_url = "https://example.com/webhook"
        
        # Generate valid signature
        string_to_sign = webhook_url + payload.decode('utf-8')
        signature = base64.b64encode(
            hmac.new(
                "test_signature_key".encode('utf-8'),
                string_to_sign.encode('utf-8'),
                hashlib.sha1
            ).digest()
        ).decode('utf-8')
        
        # Test verification
        is_valid = connector.verify_webhook_signature(payload, signature)
        assert is_valid is True