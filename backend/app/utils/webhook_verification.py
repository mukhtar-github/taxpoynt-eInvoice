"""Webhook signature verification utilities for POS integrations."""

import hashlib
import hmac
import time
import base64
from typing import Optional, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class WebhookPlatform(str, Enum):
    """Supported webhook platforms with their verification methods."""
    SQUARE = "square"
    TOAST = "toast"
    LIGHTSPEED = "lightspeed"
    STRIPE = "stripe"
    PAYPAL = "paypal"


class WebhookSignatureVerifier:
    """Universal webhook signature verification utility."""
    
    @staticmethod
    def verify_signature(
        platform: WebhookPlatform,
        payload: bytes,
        signature: str,
        secret: str,
        **kwargs
    ) -> bool:
        """
        Verify webhook signature for different platforms.
        
        Args:
            platform: The webhook platform type
            payload: Raw webhook payload bytes
            signature: Signature from webhook headers
            secret: Webhook secret/signing key
            **kwargs: Platform-specific additional parameters
            
        Returns:
            bool: True if signature is valid
        """
        try:
            if platform == WebhookPlatform.SQUARE:
                return WebhookSignatureVerifier._verify_square_signature(
                    payload, signature, secret, kwargs.get("notification_url", "")
                )
            elif platform == WebhookPlatform.TOAST:
                return WebhookSignatureVerifier._verify_toast_signature(
                    payload, signature, secret, kwargs.get("timestamp")
                )
            elif platform == WebhookPlatform.LIGHTSPEED:
                return WebhookSignatureVerifier._verify_lightspeed_signature(
                    payload, signature, secret
                )
            elif platform == WebhookPlatform.STRIPE:
                return WebhookSignatureVerifier._verify_stripe_signature(
                    payload, signature, secret, kwargs.get("timestamp")
                )
            elif platform == WebhookPlatform.PAYPAL:
                return WebhookSignatureVerifier._verify_paypal_signature(
                    payload, signature, secret, kwargs.get("headers", {})
                )
            else:
                logger.warning(f"Unsupported webhook platform: {platform}")
                return False
                
        except Exception as e:
            logger.error(f"Webhook signature verification failed for {platform}: {str(e)}", exc_info=True)
            return False
    
    @staticmethod
    def _verify_square_signature(
        payload: bytes,
        signature: str,
        signature_key: str,
        notification_url: str
    ) -> bool:
        """
        Verify Square webhook signature.
        
        Square uses SHA-1 HMAC with notification URL + body.
        """
        try:
            # Square combines notification URL with request body
            string_to_sign = notification_url + payload.decode('utf-8')
            
            # Generate HMAC using SHA-1
            expected_signature = hmac.new(
                signature_key.encode('utf-8'),
                string_to_sign.encode('utf-8'),
                hashlib.sha1
            ).digest()
            
            # Base64 encode the result
            expected_signature_b64 = base64.b64encode(expected_signature).decode('utf-8')
            
            # Compare signatures
            return hmac.compare_digest(signature, expected_signature_b64)
            
        except Exception as e:
            logger.error(f"Square signature verification error: {str(e)}")
            return False
    
    @staticmethod
    def _verify_toast_signature(
        payload: bytes,
        signature: str,
        secret: str,
        timestamp: Optional[str] = None
    ) -> bool:
        """
        Verify Toast POS webhook signature.
        
        Toast typically uses HMAC-SHA256.
        """
        try:
            # Toast uses standard HMAC-SHA256
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Remove any prefix (like "sha256=")
            signature_clean = signature.replace("sha256=", "")
            
            return hmac.compare_digest(signature_clean, expected_signature)
            
        except Exception as e:
            logger.error(f"Toast signature verification error: {str(e)}")
            return False
    
    @staticmethod
    def _verify_lightspeed_signature(
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        """
        Verify Lightspeed webhook signature.
        
        Lightspeed uses HMAC-SHA256.
        """
        try:
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Lightspeed signature verification error: {str(e)}")
            return False
    
    @staticmethod
    def _verify_stripe_signature(
        payload: bytes,
        signature: str,
        secret: str,
        timestamp: Optional[str] = None
    ) -> bool:
        """
        Verify Stripe webhook signature with timestamp validation.
        
        Stripe uses HMAC-SHA256 with timestamp for replay protection.
        """
        try:
            # Parse Stripe signature header
            # Format: t=timestamp,v1=signature
            sig_parts = {}
            for part in signature.split(','):
                key, value = part.split('=', 1)
                sig_parts[key] = value
            
            timestamp = sig_parts.get('t')
            signature_hash = sig_parts.get('v1')
            
            if not timestamp or not signature_hash:
                return False
            
            # Verify timestamp (prevent replay attacks)
            if not WebhookSignatureVerifier._verify_timestamp(timestamp, tolerance_seconds=300):
                logger.warning("Stripe webhook timestamp outside tolerance")
                return False
            
            # Create payload string
            payload_string = f"{timestamp}.{payload.decode('utf-8')}"
            
            # Generate expected signature
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                payload_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature_hash, expected_signature)
            
        except Exception as e:
            logger.error(f"Stripe signature verification error: {str(e)}")
            return False
    
    @staticmethod
    def _verify_paypal_signature(
        payload: bytes,
        signature: str,
        secret: str,
        headers: Dict[str, str]
    ) -> bool:
        """
        Verify PayPal webhook signature.
        
        PayPal uses a more complex verification process.
        """
        try:
            # PayPal webhook verification would typically involve
            # certificate validation and more complex logic
            # This is a simplified version using HMAC-SHA256
            
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"PayPal signature verification error: {str(e)}")
            return False
    
    @staticmethod
    def _verify_timestamp(timestamp: str, tolerance_seconds: int = 300) -> bool:
        """
        Verify webhook timestamp for replay protection.
        
        Args:
            timestamp: Timestamp from webhook
            tolerance_seconds: Maximum age of webhook in seconds
            
        Returns:
            bool: True if timestamp is within tolerance
        """
        try:
            webhook_time = int(timestamp)
            current_time = int(time.time())
            return abs(current_time - webhook_time) <= tolerance_seconds
        except (ValueError, TypeError):
            return False


class WebhookEventValidator:
    """Validates webhook event structure and content."""
    
    @staticmethod
    def validate_event_structure(event_data: Dict[str, Any], platform: WebhookPlatform) -> bool:
        """
        Validate basic webhook event structure for different platforms.
        
        Args:
            event_data: Webhook event data
            platform: Platform type
            
        Returns:
            bool: True if event structure is valid
        """
        try:
            if platform == WebhookPlatform.SQUARE:
                return WebhookEventValidator._validate_square_event(event_data)
            elif platform == WebhookPlatform.TOAST:
                return WebhookEventValidator._validate_toast_event(event_data)
            elif platform == WebhookPlatform.LIGHTSPEED:
                return WebhookEventValidator._validate_lightspeed_event(event_data)
            else:
                # Generic validation
                required_fields = ['event_id', 'event_type', 'data']
                return all(field in event_data for field in required_fields)
                
        except Exception as e:
            logger.error(f"Event structure validation failed: {str(e)}")
            return False
    
    @staticmethod
    def _validate_square_event(event_data: Dict[str, Any]) -> bool:
        """Validate Square webhook event structure."""
        required_fields = ['merchant_id', 'type', 'event_id', 'created_at', 'data']
        return all(field in event_data for field in required_fields)
    
    @staticmethod
    def _validate_toast_event(event_data: Dict[str, Any]) -> bool:
        """Validate Toast webhook event structure."""
        required_fields = ['eventType', 'guid', 'entityId', 'timestamp']
        return all(field in event_data for field in required_fields)
    
    @staticmethod
    def _validate_lightspeed_event(event_data: Dict[str, Any]) -> bool:
        """Validate Lightspeed webhook event structure."""
        required_fields = ['action', 'data', 'timestamp']
        return all(field in event_data for field in required_fields)


class WebhookSecurity:
    """Additional security utilities for webhook processing."""
    
    @staticmethod
    def check_ip_whitelist(client_ip: str, platform: WebhookPlatform) -> bool:
        """
        Check if the client IP is in the platform's webhook IP whitelist.
        
        Args:
            client_ip: Client IP address
            platform: Platform type
            
        Returns:
            bool: True if IP is whitelisted
        """
        # Define platform-specific IP ranges (examples)
        ip_whitelists = {
            WebhookPlatform.SQUARE: [
                "54.240.196.0/24",   # Example Square IP ranges
                "52.19.124.0/24",
            ],
            WebhookPlatform.TOAST: [
                "52.71.0.0/16",      # Example Toast IP ranges
            ],
            WebhookPlatform.LIGHTSPEED: [
                "34.102.0.0/16",     # Example Lightspeed IP ranges
            ]
        }
        
        if platform not in ip_whitelists:
            # If no whitelist defined, allow all IPs
            return True
        
        # Check if client IP is in any of the whitelisted ranges
        import ipaddress
        client_ip_obj = ipaddress.ip_address(client_ip)
        
        for ip_range in ip_whitelists[platform]:
            if client_ip_obj in ipaddress.ip_network(ip_range):
                return True
        
        return False
    
    @staticmethod
    def rate_limit_check(client_ip: str, max_requests: int = 100, window_seconds: int = 60) -> bool:
        """
        Simple rate limiting for webhook endpoints.
        
        Args:
            client_ip: Client IP address
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
            
        Returns:
            bool: True if request is within rate limit
        """
        # This would typically use Redis or another cache
        # For now, return True (no rate limiting)
        return True
    
    @staticmethod
    def sanitize_webhook_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize webhook data to prevent XSS and injection attacks.
        
        Args:
            data: Raw webhook data
            
        Returns:
            Dict: Sanitized data
        """
        import html
        import json
        
        def sanitize_value(value):
            if isinstance(value, str):
                # HTML escape the string
                return html.escape(value)
            elif isinstance(value, dict):
                return {k: sanitize_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [sanitize_value(item) for item in value]
            else:
                return value
        
        return sanitize_value(data)