"""
Webhook verification service for TaxPoynt eInvoice APP functionality.

This module provides functionality for:
- Verifying webhook signatures to ensure they come from trusted sources
- Validating webhook payloads against expected schemas
- Preventing replay attacks on webhooks
"""

import hmac
import hashlib
import time
import logging
from typing import Dict, Any, Optional
from uuid import UUID

from app.core.config import settings

logger = logging.getLogger(__name__)

class WebhookVerificationService:
    """Service for verifying incoming webhooks."""
    
    def __init__(self):
        self.webhook_secret = settings.WEBHOOK_SECRET
        # Store nonces to prevent replay attacks, with timestamp cleanup
        self._nonce_registry = {}
        
    def verify_webhook_signature(self, payload: Dict[str, Any], 
                                signature: str,
                                timestamp: str,
                                nonce: str) -> bool:
        """
        Verify the webhook signature to ensure it comes from a trusted source.
        
        Args:
            payload: The webhook payload data
            signature: The signature provided in the request header
            timestamp: The timestamp when the webhook was sent
            nonce: A unique identifier to prevent replay attacks
            
        Returns:
            bool: True if the signature is valid, False otherwise
        """
        # Check if nonce has been seen before (prevent replay attacks)
        if nonce in self._nonce_registry:
            logger.warning(f"Duplicate webhook nonce detected: {nonce}")
            return False
            
        # Clean up old nonces (older than 5 minutes)
        current_time = time.time()
        self._nonce_registry = {n: t for n, t in self._nonce_registry.items() 
                               if current_time - t < 300}
        
        # Add current nonce to registry
        self._nonce_registry[nonce] = current_time
        
        # Create the string to sign
        string_to_sign = f"{timestamp}.{nonce}.{payload}"
        
        # Calculate expected signature
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            string_to_sign.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        return hmac.compare_digest(expected_signature, signature)
        
    def validate_webhook_payload(self, payload: Dict[str, Any], 
                                webhook_type: str) -> Dict[str, Any]:
        """
        Validate webhook payload against expected schema.
        
        Args:
            payload: The webhook payload to validate
            webhook_type: The type of webhook (e.g., 'status_update', 'receipt')
            
        Returns:
            Dict: Validated and normalized payload
            
        Raises:
            ValueError: If payload is invalid
        """
        # Basic validation
        if not payload:
            raise ValueError("Empty webhook payload")
            
        # Specific validation based on webhook type
        if webhook_type == 'status_update':
            required_fields = ['transmission_id', 'status']
            for field in required_fields:
                if field not in payload:
                    raise ValueError(f"Missing required field: {field}")
                    
            # Normalize status values
            status_mapping = {
                'received': 'in_progress',
                'processing': 'in_progress',
                'accepted': 'completed',
                'rejected': 'failed',
                'error': 'failed',
                'successful': 'completed',
                'successful_with_warnings': 'completed',
                'failed': 'failed'
            }
            
            if 'status' in payload:
                status = payload['status'].lower()
                if status in status_mapping:
                    payload['normalized_status'] = status_mapping[status]
                else:
                    logger.warning(f"Unknown status in webhook: {status}")
                    payload['normalized_status'] = 'unknown'
        
        return payload
