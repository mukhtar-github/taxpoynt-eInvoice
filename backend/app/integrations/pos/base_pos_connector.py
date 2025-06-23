"""
Base POS connector class for real-time transaction processing.

This module extends the base connector with POS-specific functionality including
webhook signature verification, real-time transaction handling, and location management.
"""

import asyncio
import hashlib
import hmac
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List

from app.integrations.base.connector import BaseConnector, IntegrationTestResult
from pydantic import BaseModel


class POSTransaction(BaseModel):
    """Model representing a POS transaction."""
    transaction_id: str
    location_id: Optional[str] = None
    amount: float
    currency: str
    payment_method: str
    timestamp: datetime
    items: List[Dict[str, Any]] = []
    customer_info: Optional[Dict[str, Any]] = None
    tax_info: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class POSWebhookEvent(BaseModel):
    """Model representing a POS webhook event."""
    event_type: str
    event_id: str
    timestamp: datetime
    data: Dict[str, Any]
    source: str
    signature: Optional[str] = None


class POSLocation(BaseModel):
    """Model representing a POS location/store."""
    location_id: str
    name: str
    address: Optional[Dict[str, Any]] = None
    timezone: Optional[str] = None
    currency: str
    tax_settings: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class BasePOSConnector(BaseConnector, ABC):
    """Base connector for POS integrations with real-time capabilities."""
    
    def __init__(self, connection_config: Dict[str, Any]):
        """
        Initialize the POS connector.
        
        Args:
            connection_config: Dictionary containing POS connection parameters
        """
        super().__init__(connection_config)
        self.webhook_secret = connection_config.get("webhook_secret")
        self.webhook_url = connection_config.get("webhook_url")
        self.location_id = connection_config.get("location_id")
        
    @abstractmethod
    async def verify_webhook_signature(
        self, 
        payload: bytes, 
        signature: str, 
        timestamp: Optional[str] = None
    ) -> bool:
        """
        Verify webhook signature from POS platform.
        
        Args:
            payload: Raw webhook payload
            signature: Signature from webhook headers
            timestamp: Optional timestamp for replay protection
            
        Returns:
            bool: True if signature is valid
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        pass
    
    @abstractmethod
    async def process_transaction(self, transaction_data: Dict[str, Any]) -> POSTransaction:
        """
        Process a transaction from the POS system.
        
        Args:
            transaction_data: Raw transaction data from POS
            
        Returns:
            POSTransaction: Normalized transaction object
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        pass
    
    @abstractmethod
    async def get_transaction_by_id(self, transaction_id: str) -> Optional[POSTransaction]:
        """
        Retrieve transaction details by ID.
        
        Args:
            transaction_id: Unique transaction identifier
            
        Returns:
            POSTransaction or None if not found
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        pass
    
    @abstractmethod
    async def get_location_details(self) -> POSLocation:
        """
        Get details about POS location/store.
        
        Returns:
            POSLocation: Location/store information
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        pass
    
    async def handle_webhook_event(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming webhook event from POS platform.
        
        Args:
            webhook_data: Raw webhook data
            
        Returns:
            Dict with processing results
        """
        try:
            # Create webhook event model
            event = POSWebhookEvent(**webhook_data)
            
            # Verify signature if provided
            if event.signature and self.webhook_secret:
                payload = str(webhook_data).encode('utf-8')
                if not await self.verify_webhook_signature(payload, event.signature):
                    self.logger.warning(f"Invalid webhook signature for event {event.event_id}")
                    return {"success": False, "error": "Invalid signature"}
            
            # Process based on event type
            if event.event_type in ["payment.created", "transaction.completed"]:
                transaction = await self.process_transaction(event.data)
                
                # Here you would typically:
                # 1. Store transaction in database
                # 2. Generate invoice/receipt
                # 3. Send to FIRS if applicable
                # 4. Trigger any business logic
                
                self.logger.info(f"Processed transaction {transaction.transaction_id}")
                return {
                    "success": True,
                    "transaction_id": transaction.transaction_id,
                    "processed_at": datetime.now().isoformat()
                }
            
            elif event.event_type == "location.updated":
                location = await self.get_location_details()
                self.logger.info(f"Location updated: {location.name}")
                return {
                    "success": True,
                    "location_id": location.location_id,
                    "updated_at": datetime.now().isoformat()
                }
            
            else:
                self.logger.info(f"Unhandled event type: {event.event_type}")
                return {
                    "success": True,
                    "message": f"Event {event.event_type} received but not processed"
                }
                
        except Exception as e:
            self.logger.error(f"Error processing webhook event: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_type": e.__class__.__name__
            }
    
    async def get_transactions_in_range(
        self, 
        start_date: datetime, 
        end_date: datetime,
        limit: int = 100
    ) -> List[POSTransaction]:
        """
        Get transactions within a date range.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            limit: Maximum number of transactions to return
            
        Returns:
            List of POSTransaction objects
        """
        # Default implementation - should be overridden by specific connectors
        self.logger.warning("get_transactions_in_range not implemented for this connector")
        return []
    
    async def test_webhook_connectivity(self) -> IntegrationTestResult:
        """
        Test webhook connectivity and configuration.
        
        Returns:
            IntegrationTestResult with webhook test status
        """
        try:
            if not self.webhook_url:
                return IntegrationTestResult(
                    success=False,
                    message="Webhook URL not configured",
                    details={"webhook_url": None}
                )
            
            if not self.webhook_secret:
                return IntegrationTestResult(
                    success=False,
                    message="Webhook secret not configured",
                    details={"webhook_secret_configured": False}
                )
            
            # Test webhook endpoint registration
            # This would be platform-specific implementation
            
            return IntegrationTestResult(
                success=True,
                message="Webhook configuration valid",
                details={
                    "webhook_url": self.webhook_url,
                    "webhook_secret_configured": bool(self.webhook_secret),
                    "location_id": self.location_id
                }
            )
            
        except Exception as e:
            return IntegrationTestResult(
                success=False,
                message=f"Webhook test failed: {str(e)}",
                details={"error": str(e)}
            )
    
    def _generate_hmac_signature(self, payload: bytes, secret: str) -> str:
        """
        Generate HMAC signature for webhook verification.
        
        Args:
            payload: Raw payload bytes
            secret: Webhook secret
            
        Returns:
            str: HMAC signature
        """
        return hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
    
    def _verify_timestamp(self, timestamp: str, tolerance_seconds: int = 300) -> bool:
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
    
    async def health_check(self) -> IntegrationTestResult:
        """
        Comprehensive health check including webhook connectivity.
        
        Returns:
            IntegrationTestResult with overall health status
        """
        # Base connection test
        base_result = await super().health_check()
        
        if not base_result.success:
            return base_result
        
        # Additional POS-specific checks
        webhook_result = await self.test_webhook_connectivity()
        
        return IntegrationTestResult(
            success=base_result.success and webhook_result.success,
            message="POS connector health check complete",
            details={
                "base_connection": base_result.details,
                "webhook_connectivity": webhook_result.details,
                "pos_features": {
                    "real_time_transactions": True,
                    "webhook_processing": True,
                    "location_management": True
                }
            }
        )