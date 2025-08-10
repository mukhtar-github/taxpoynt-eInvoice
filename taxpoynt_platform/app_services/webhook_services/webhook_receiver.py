"""
APP Service: Webhook Receiver
Receives and validates incoming webhooks from FIRS system
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import hmac
import ipaddress
from urllib.parse import urlparse

import aiohttp
from fastapi import Request, HTTPException, status
from pydantic import BaseModel, Field, validator


class WebhookEventType(str, Enum):
    """FIRS webhook event types"""
    SUBMISSION_STATUS = "submission.status"
    INVOICE_APPROVED = "invoice.approved"
    INVOICE_REJECTED = "invoice.rejected"
    CERTIFICATE_EXPIRY = "certificate.expiry"
    SYSTEM_MAINTENANCE = "system.maintenance"
    IRN_CANCELLED = "irn.cancelled"
    VALIDATION_ERROR = "validation.error"
    AUTHENTICATION_FAILURE = "authentication.failure"


class WebhookStatus(str, Enum):
    """Webhook processing status"""
    RECEIVED = "received"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    IGNORED = "ignored"


@dataclass
class WebhookMetadata:
    """Webhook metadata for tracking"""
    webhook_id: str
    received_at: datetime
    source_ip: str
    user_agent: Optional[str]
    content_type: str
    content_length: int
    headers: Dict[str, str]
    signature: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['received_at'] = self.received_at.isoformat()
        return data


class WebhookPayload(BaseModel):
    """Standardized webhook payload structure"""
    event_type: WebhookEventType
    event_id: str = Field(..., description="Unique event identifier")
    timestamp: datetime = Field(..., description="Event timestamp")
    source: str = Field(..., description="Event source system")
    data: Dict[str, Any] = Field(..., description="Event data payload")
    version: str = Field(default="1.0", description="Payload version")
    retry_count: int = Field(default=0, description="Retry attempt count")
    
    @validator('timestamp', pre=True)
    def parse_timestamp(cls, v):
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                return datetime.now(timezone.utc)
        return v


class WebhookReceiver:
    """
    Receives and validates incoming webhooks from FIRS
    Handles webhook authentication, rate limiting, and initial processing
    """
    
    def __init__(self, 
                 webhook_secret: str,
                 allowed_ips: Optional[List[str]] = None,
                 max_payload_size: int = 1024 * 1024):  # 1MB default
        self.webhook_secret = webhook_secret
        self.allowed_ips = allowed_ips or []
        self.max_payload_size = max_payload_size
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting storage (in production, use Redis)
        self._rate_limit_storage: Dict[str, List[float]] = {}
        self._rate_limit_window = 300  # 5 minutes
        self._max_requests_per_window = 100
        
        # Webhook processing statistics
        self.stats = {
            'total_received': 0,
            'total_processed': 0,
            'total_failed': 0,
            'total_ignored': 0,
            'last_received_at': None,
            'event_type_counts': {}
        }
    
    async def receive_webhook(self, request: Request) -> Tuple[WebhookPayload, WebhookMetadata]:
        """
        Main entry point for receiving webhooks
        
        Args:
            request: FastAPI request object
            
        Returns:
            Tuple of (webhook_payload, webhook_metadata)
            
        Raises:
            HTTPException: For validation or security errors
        """
        try:
            # Extract metadata
            metadata = await self._extract_metadata(request)
            
            # Security validations
            await self._validate_security(request, metadata)
            
            # Rate limiting
            await self._check_rate_limit(metadata.source_ip)
            
            # Parse and validate payload
            raw_body = await request.body()
            payload = await self._parse_payload(raw_body, metadata)
            
            # Update statistics
            self._update_stats(payload)
            
            self.logger.info(
                f"Webhook received successfully: {payload.event_type} "
                f"from {metadata.source_ip}"
            )
            
            return payload, metadata
            
        except HTTPException:
            self.stats['total_failed'] += 1
            raise
        except Exception as e:
            self.stats['total_failed'] += 1
            self.logger.error(f"Unexpected error receiving webhook: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error processing webhook"
            )
    
    async def _extract_metadata(self, request: Request) -> WebhookMetadata:
        """Extract webhook metadata from request"""
        headers = dict(request.headers)
        client_ip = self._get_client_ip(request)
        
        return WebhookMetadata(
            webhook_id=headers.get('x-webhook-id', self._generate_webhook_id()),
            received_at=datetime.now(timezone.utc),
            source_ip=client_ip,
            user_agent=headers.get('user-agent'),
            content_type=headers.get('content-type', ''),
            content_length=int(headers.get('content-length', 0)),
            headers=headers,
            signature=headers.get('x-firs-signature')
        )
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip
        
        # Fallback to client host
        return getattr(request.client, 'host', 'unknown')
    
    def _generate_webhook_id(self) -> str:
        """Generate unique webhook ID"""
        timestamp = datetime.now(timezone.utc).timestamp()
        content = f"webhook_{timestamp}_{id(self)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    async def _validate_security(self, request: Request, metadata: WebhookMetadata):
        """Validate webhook security requirements"""
        # IP allowlist validation
        if self.allowed_ips and not self._is_ip_allowed(metadata.source_ip):
            self.logger.warning(f"Webhook from unauthorized IP: {metadata.source_ip}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="IP address not authorized"
            )
        
        # Content length validation
        if metadata.content_length > self.max_payload_size:
            self.logger.warning(
                f"Webhook payload too large: {metadata.content_length} bytes "
                f"from {metadata.source_ip}"
            )
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Payload too large"
            )
        
        # Content type validation
        if not metadata.content_type.startswith('application/json'):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Content-Type must be application/json"
            )
    
    def _is_ip_allowed(self, ip_address: str) -> bool:
        """Check if IP address is in allowlist"""
        try:
            client_ip = ipaddress.ip_address(ip_address)
            for allowed_ip in self.allowed_ips:
                if '/' in allowed_ip:  # CIDR notation
                    if client_ip in ipaddress.ip_network(allowed_ip):
                        return True
                else:  # Single IP
                    if client_ip == ipaddress.ip_address(allowed_ip):
                        return True
            return False
        except ValueError:
            return False
    
    async def _check_rate_limit(self, ip_address: str):
        """Check rate limiting for IP address"""
        current_time = datetime.now(timezone.utc).timestamp()
        
        # Clean old entries
        if ip_address in self._rate_limit_storage:
            self._rate_limit_storage[ip_address] = [
                timestamp for timestamp in self._rate_limit_storage[ip_address]
                if current_time - timestamp < self._rate_limit_window
            ]
        else:
            self._rate_limit_storage[ip_address] = []
        
        # Check rate limit
        if len(self._rate_limit_storage[ip_address]) >= self._max_requests_per_window:
            self.logger.warning(f"Rate limit exceeded for IP: {ip_address}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        # Record this request
        self._rate_limit_storage[ip_address].append(current_time)
    
    async def _parse_payload(self, raw_body: bytes, metadata: WebhookMetadata) -> WebhookPayload:
        """Parse and validate webhook payload"""
        try:
            # Parse JSON
            if not raw_body:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Empty payload"
                )
            
            payload_data = json.loads(raw_body.decode('utf-8'))
            
            # Validate signature if present
            if metadata.signature and self.webhook_secret:
                await self._validate_signature(raw_body, metadata.signature)
            
            # Create and validate payload
            payload = WebhookPayload(**payload_data)
            
            return payload
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON payload: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload"
            )
        except ValueError as e:
            self.logger.error(f"Invalid payload structure: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid payload structure: {str(e)}"
            )
    
    async def _validate_signature(self, payload: bytes, signature: str):
        """Validate webhook signature using HMAC"""
        try:
            # Expected format: "sha256=<hash>"
            if not signature.startswith('sha256='):
                raise ValueError("Invalid signature format")
            
            expected_signature = signature[7:]  # Remove 'sha256=' prefix
            
            # Compute HMAC
            computed_hash = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures (constant time comparison)
            if not hmac.compare_digest(expected_signature, computed_hash):
                self.logger.warning("Webhook signature validation failed")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook signature"
                )
                
        except ValueError as e:
            self.logger.error(f"Signature validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signature format"
            )
    
    def _update_stats(self, payload: WebhookPayload):
        """Update webhook processing statistics"""
        self.stats['total_received'] += 1
        self.stats['last_received_at'] = datetime.now(timezone.utc).isoformat()
        
        # Update event type counts
        event_type = payload.event_type.value
        self.stats['event_type_counts'][event_type] = (
            self.stats['event_type_counts'].get(event_type, 0) + 1
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Get webhook receiver health status"""
        return {
            'status': 'healthy',
            'service': 'webhook_receiver',
            'stats': self.stats.copy(),
            'rate_limit_info': {
                'window_seconds': self._rate_limit_window,
                'max_requests': self._max_requests_per_window,
                'current_tracked_ips': len(self._rate_limit_storage)
            },
            'config': {
                'max_payload_size': self.max_payload_size,
                'allowed_ips_count': len(self.allowed_ips),
                'signature_validation_enabled': bool(self.webhook_secret)
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def get_supported_events(self) -> List[Dict[str, str]]:
        """Get list of supported webhook events"""
        return [
            {
                'event_type': event.value,
                'description': self._get_event_description(event)
            }
            for event in WebhookEventType
        ]
    
    def _get_event_description(self, event_type: WebhookEventType) -> str:
        """Get description for webhook event type"""
        descriptions = {
            WebhookEventType.SUBMISSION_STATUS: "Invoice submission status updates",
            WebhookEventType.INVOICE_APPROVED: "Invoice approval notifications",
            WebhookEventType.INVOICE_REJECTED: "Invoice rejection notifications",
            WebhookEventType.CERTIFICATE_EXPIRY: "Certificate expiry warnings",
            WebhookEventType.SYSTEM_MAINTENANCE: "FIRS system maintenance notices",
            WebhookEventType.IRN_CANCELLED: "IRN cancellation notifications",
            WebhookEventType.VALIDATION_ERROR: "Validation error reports",
            WebhookEventType.AUTHENTICATION_FAILURE: "Authentication failure alerts"
        }
        return descriptions.get(event_type, "Unknown event type")
    
    async def cleanup(self):
        """Cleanup resources and save final statistics"""
        self.logger.info("Webhook receiver cleanup initiated")
        
        # Log final statistics
        self.logger.info(f"Final webhook statistics: {self.stats}")
        
        # Clear rate limiting storage
        self._rate_limit_storage.clear()
        
        self.logger.info("Webhook receiver cleanup completed")


# Utility functions for webhook receiver configuration
def create_webhook_receiver(
    webhook_secret: str,
    allowed_ips: Optional[List[str]] = None,
    max_payload_size: int = 1024 * 1024
) -> WebhookReceiver:
    """Factory function to create webhook receiver with standard configuration"""
    return WebhookReceiver(
        webhook_secret=webhook_secret,
        allowed_ips=allowed_ips,
        max_payload_size=max_payload_size
    )


def get_firs_webhook_config() -> Dict[str, Any]:
    """Get standard FIRS webhook configuration"""
    return {
        'signature_header': 'x-firs-signature',
        'webhook_id_header': 'x-webhook-id',
        'timestamp_header': 'x-webhook-timestamp',
        'supported_content_types': ['application/json'],
        'max_payload_size': 1024 * 1024,  # 1MB
        'timeout_seconds': 30,
        'supported_events': [event.value for event in WebhookEventType]
    }