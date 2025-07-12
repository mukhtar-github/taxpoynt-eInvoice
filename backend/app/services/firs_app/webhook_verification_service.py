"""
Webhook verification service for TaxPoynt eInvoice - Access Point Provider Functions.

This module provides Access Point Provider (APP) role functionality for verifying
webhooks from FIRS and external systems, ensuring secure communication and
preventing unauthorized access to transmission endpoints.

APP Role Responsibilities:
- Verifying webhook signatures from FIRS to ensure trusted communication
- Validating webhook payloads against FIRS expected schemas
- Preventing replay attacks on FIRS webhook endpoints
- Secure authentication for transmission status updates
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
    """
    Access Point Provider service for verifying incoming webhooks from FIRS and external systems.
    
    This service provides APP role functions for secure webhook verification,
    authentication, and payload validation to ensure trusted communication
    with FIRS and other external e-invoicing services.
    """
    
    def __init__(self):
        self.webhook_secret = settings.WEBHOOK_SECRET
        # Store nonces to prevent replay attacks, with timestamp cleanup
        self._nonce_registry = {}
        
    def verify_webhook_signature(self, payload: Dict[str, Any], 
                                signature: str,
                                timestamp: str,
                                nonce: str) -> bool:
        """
        Verify the webhook signature from FIRS or external systems - APP Role Function.
        
        Provides Access Point Provider secure verification of webhook signatures
        to ensure they come from trusted FIRS sources and prevent unauthorized access.
        
        Args:
            payload: The webhook payload data from FIRS
            signature: The signature provided in the request header
            timestamp: The timestamp when the webhook was sent
            nonce: A unique identifier to prevent replay attacks
            
        Returns:
            bool: True if the signature is valid for APP processing, False otherwise
        """
        # Check if nonce has been seen before (prevent replay attacks)
        if nonce in self._nonce_registry:
            logger.warning(f"Duplicate webhook nonce detected from FIRS: {nonce}")
            return False
            
        # Clean up old nonces (older than 5 minutes)
        current_time = time.time()
        self._nonce_registry = {n: t for n, t in self._nonce_registry.items() 
                               if current_time - t < 300}
        
        # Add current nonce to registry
        self._nonce_registry[nonce] = current_time
        
        # Create the string to sign for FIRS compliance
        string_to_sign = f"{timestamp}.{nonce}.{payload}"
        
        # Calculate expected signature using APP provider credentials
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            string_to_sign.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures with constant-time comparison
        is_valid = hmac.compare_digest(expected_signature, signature)
        
        if is_valid:
            logger.info(f"Successfully verified webhook signature from FIRS (nonce: {nonce})")
        else:
            logger.warning(f"Failed to verify webhook signature from FIRS (nonce: {nonce})")
            
        return is_valid
        
    def validate_webhook_payload(self, payload: Dict[str, Any], 
                                webhook_type: str) -> Dict[str, Any]:
        """
        Validate webhook payload against FIRS expected schemas - APP Role Function.
        
        Provides Access Point Provider validation of webhook payloads from FIRS
        to ensure they conform to expected schemas and contain valid data.
        
        Args:
            payload: The webhook payload to validate from FIRS
            webhook_type: The type of webhook (e.g., 'status_update', 'receipt')
            
        Returns:
            Dict: Validated and normalized payload for APP processing
            
        Raises:
            ValueError: If payload is invalid for FIRS processing
        """
        # Basic validation
        if not payload:
            raise ValueError("Empty webhook payload from FIRS")
            
        # Specific validation based on FIRS webhook type
        if webhook_type == 'status_update':
            required_fields = ['transmission_id', 'status']
            for field in required_fields:
                if field not in payload:
                    raise ValueError(f"Missing required field for FIRS webhook: {field}")
                    
            # Normalize status values for FIRS compliance
            status_mapping = {
                'received': 'in_progress',
                'processing': 'in_progress',
                'accepted': 'completed',
                'rejected': 'failed',
                'error': 'failed',
                'successful': 'completed',
                'successful_with_warnings': 'completed',
                'failed': 'failed',
                # FIRS-specific statuses
                'firs_accepted': 'completed',
                'firs_rejected': 'failed',
                'firs_processing': 'in_progress',
                'validation_failed': 'failed',
                'signature_invalid': 'failed'
            }
            
            if 'status' in payload:
                status = payload['status'].lower()
                if status in status_mapping:
                    payload['normalized_status'] = status_mapping[status]
                    payload['firs_compatible'] = True
                else:
                    logger.warning(f"Unknown FIRS status in webhook: {status}")
                    payload['normalized_status'] = 'unknown'
                    payload['firs_compatible'] = False
        
        elif webhook_type == 'receipt_confirmation':
            required_fields = ['transmission_id', 'receipt_hash', 'timestamp']
            for field in required_fields:
                if field not in payload:
                    raise ValueError(f"Missing required field for FIRS receipt webhook: {field}")
            
            # Add FIRS receipt validation
            payload['firs_receipt'] = True
            payload['validated_by_app'] = True
            
        elif webhook_type == 'validation_result':
            required_fields = ['document_id', 'validation_status', 'errors']
            for field in required_fields:
                if field not in payload:
                    raise ValueError(f"Missing required field for FIRS validation webhook: {field}")
            
            # Normalize validation status
            payload['firs_validation'] = True
            payload['app_processed'] = True
        
        # Add APP processing metadata
        payload['app_verified'] = True
        payload['verification_timestamp'] = time.time()
        payload['webhook_type'] = webhook_type
        
        logger.info(f"Successfully validated FIRS webhook payload: {webhook_type}")
        
        return payload
    
    def verify_firs_webhook(
        self,
        payload: Dict[str, Any],
        signature: str,
        timestamp: str,
        nonce: str,
        webhook_type: str
    ) -> Dict[str, Any]:
        """
        Complete FIRS webhook verification and validation - APP Role Function.
        
        Provides comprehensive Access Point Provider verification of FIRS webhooks,
        including signature verification and payload validation.
        
        Args:
            payload: The webhook payload data from FIRS
            signature: The signature provided in the request header
            timestamp: The timestamp when the webhook was sent
            nonce: A unique identifier to prevent replay attacks
            webhook_type: The type of FIRS webhook
            
        Returns:
            Dict: Verification results and validated payload
        """
        verification_result = {
            "signature_valid": False,
            "payload_valid": False,
            "firs_compliant": False,
            "errors": [],
            "validated_payload": None
        }
        
        try:
            # Verify signature
            verification_result["signature_valid"] = self.verify_webhook_signature(
                payload, signature, timestamp, nonce
            )
            
            if not verification_result["signature_valid"]:
                verification_result["errors"].append("Invalid webhook signature from FIRS")
                return verification_result
            
            # Validate payload
            validated_payload = self.validate_webhook_payload(payload, webhook_type)
            verification_result["payload_valid"] = True
            verification_result["validated_payload"] = validated_payload
            
            # Check FIRS compliance
            verification_result["firs_compliant"] = (
                verification_result["signature_valid"] and
                verification_result["payload_valid"] and
                validated_payload.get("firs_compatible", False)
            )
            
            logger.info(f"FIRS webhook verification complete: {'SUCCESS' if verification_result['firs_compliant'] else 'FAILED'}")
            
        except ValueError as e:
            verification_result["errors"].append(str(e))
            logger.error(f"FIRS webhook validation error: {str(e)}")
        except Exception as e:
            verification_result["errors"].append(f"Unexpected error: {str(e)}")
            logger.error(f"Unexpected error verifying FIRS webhook: {str(e)}")
        
        return verification_result
    
    def create_webhook_response(
        self,
        transmission_id: str,
        status: str,
        message: str = None
    ) -> Dict[str, Any]:
        """
        Create a standardized webhook response for FIRS - APP Role Function.
        
        Provides Access Point Provider standardized response format for
        FIRS webhook acknowledgments and status updates.
        
        Args:
            transmission_id: ID of the transmission being acknowledged
            status: Status of the webhook processing
            message: Optional message for additional details
            
        Returns:
            Dict: Standardized webhook response for FIRS
        """
        response = {
            "transmission_id": transmission_id,
            "status": status,
            "timestamp": time.time(),
            "app_provider": "TaxPoynt",
            "acknowledgment": "received"
        }
        
        if message:
            response["message"] = message
        
        # Add APP signature for response authentication
        response_string = f"{transmission_id}.{status}.{response['timestamp']}"
        response_signature = hmac.new(
            self.webhook_secret.encode(),
            response_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        response["signature"] = response_signature
        response["firs_ready"] = True
        
        logger.info(f"Created webhook response for FIRS transmission {transmission_id}: {status}")
        
        return response