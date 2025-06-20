"""
Webhook handlers for HubSpot CRM integration.

This module provides webhook handling functionality for HubSpot deal updates,
contact changes, and other real-time events.
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import HTTPException, Request, status
from pydantic import BaseModel, Field

from app.integrations.crm.hubspot.connector import HubSpotConnector, get_hubspot_connector
from app.integrations.crm.hubspot.models import HubSpotWebhookEvent, HubSpotWebhookPayload
from app.integrations.base.errors import IntegrationError

logger = logging.getLogger(__name__)


# Webhook event models are now imported from models.py


class HubSpotWebhookProcessor:
    """Processor for HubSpot webhook events."""
    
    def __init__(self, connection_config: Dict[str, Any]):
        """
        Initialize webhook processor.
        
        Args:
            connection_config: HubSpot connection configuration
        """
        self.config = connection_config
        self.connector = get_hubspot_connector(connection_config)
        self.webhook_secret = connection_config.get("webhook_secret", "")
        
    def verify_webhook_signature(self, request_body: bytes, signature: str) -> bool:
        """
        Verify HubSpot webhook signature.
        
        Args:
            request_body: Raw request body bytes
            signature: Signature from X-HubSpot-Signature-V3 header
            
        Returns:
            bool: True if signature is valid
        """
        if not self.webhook_secret:
            logger.warning("No webhook secret configured, skipping signature verification")
            return True
            
        try:
            # HubSpot uses SHA256 HMAC with v3 signatures
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                request_body,
                hashlib.sha256
            ).hexdigest()
            
            # Remove 'sha256=' prefix if present
            if signature.startswith('sha256='):
                signature = signature[7:]
                
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {str(e)}")
            return False
    
    async def process_webhook_events(self, events: List[HubSpotWebhookEvent]) -> Dict[str, Any]:
        """
        Process multiple webhook events.
        
        Args:
            events: List of webhook events
            
        Returns:
            Dict with processing results
        """
        results = {
            "processed": 0,
            "errors": 0,
            "events": []
        }
        
        for event in events:
            try:
                result = await self.process_single_event(event)
                results["events"].append({
                    "event_id": event.eventId,
                    "object_id": event.objectId,
                    "status": "success",
                    "result": result
                })
                results["processed"] += 1
            except Exception as e:
                logger.error(f"Error processing event {event.eventId}: {str(e)}")
                results["events"].append({
                    "event_id": event.eventId,
                    "object_id": event.objectId,
                    "status": "error",
                    "error": str(e)
                })
                results["errors"] += 1
                
        return results
    
    async def process_single_event(self, event: HubSpotWebhookEvent) -> Dict[str, Any]:
        """
        Process a single webhook event.
        
        Args:
            event: Webhook event to process
            
        Returns:
            Dict with processing result
        """
        if event.subscriptionType == "deal.propertyChange":
            return await self.handle_deal_property_change(event)
        elif event.subscriptionType == "deal.creation":
            return await self.handle_deal_creation(event)
        elif event.subscriptionType == "deal.deletion":
            return await self.handle_deal_deletion(event)
        elif event.subscriptionType == "contact.propertyChange":
            return await self.handle_contact_property_change(event)
        elif event.subscriptionType == "company.propertyChange":
            return await self.handle_company_property_change(event)
        else:
            logger.info(f"Unhandled webhook event type: {event.subscriptionType}")
            return {"status": "ignored", "reason": "unhandled_event_type"}
    
    async def handle_deal_property_change(self, event: HubSpotWebhookEvent) -> Dict[str, Any]:
        """
        Handle deal property change event.
        
        Args:
            event: Deal property change event
            
        Returns:
            Dict with handling result
        """
        try:
            # Get the updated deal data
            deal_data = await self.connector.get_deal_by_id(event.objectId)
            
            # Check if this is a stage change that requires invoice generation
            if event.propertyName == "dealstage":
                return await self.handle_deal_stage_change(event, deal_data)
            
            # Check if this is an amount change
            elif event.propertyName == "amount":
                return await self.handle_deal_amount_change(event, deal_data)
            
            # For other property changes, just log and continue
            logger.info(f"Deal {event.objectId} property '{event.propertyName}' changed to '{event.propertyValue}'")
            
            return {
                "status": "processed",
                "action": "property_updated",
                "property": event.propertyName,
                "new_value": event.propertyValue
            }
            
        except Exception as e:
            logger.error(f"Error handling deal property change: {str(e)}")
            raise IntegrationError(f"Failed to handle deal property change: {str(e)}")
    
    async def handle_deal_stage_change(self, event: HubSpotWebhookEvent, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle deal stage change specifically.
        
        Args:
            event: Webhook event
            deal_data: Current deal data
            
        Returns:
            Dict with handling result
        """
        stage_mapping = self.config.get("settings", {}).get("deal_stage_mapping", {})
        new_stage = event.propertyValue
        
        # Check if this stage change should trigger invoice generation
        if new_stage in stage_mapping:
            invoice_action = stage_mapping[new_stage]
            
            if invoice_action == "generate_invoice":
                try:
                    # Generate invoice from deal
                    invoice_data = await self.connector.transform_deal_to_invoice(deal_data)
                    
                    # TODO: Save invoice to database via invoice service
                    # For now, just log the invoice generation
                    logger.info(f"Generated invoice for deal {event.objectId}: {invoice_data['invoice_number']}")
                    
                    return {
                        "status": "processed",
                        "action": "invoice_generated",
                        "invoice_number": invoice_data["invoice_number"],
                        "deal_stage": new_stage
                    }
                except Exception as e:
                    logger.error(f"Error generating invoice for deal {event.objectId}: {str(e)}")
                    return {
                        "status": "error",
                        "action": "invoice_generation_failed",
                        "error": str(e)
                    }
        
        return {
            "status": "processed",
            "action": "stage_changed",
            "new_stage": new_stage,
            "mapping_found": new_stage in stage_mapping
        }
    
    async def handle_deal_amount_change(self, event: HubSpotWebhookEvent, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle deal amount change.
        
        Args:
            event: Webhook event
            deal_data: Current deal data
            
        Returns:
            Dict with handling result
        """
        # TODO: Check if there's an existing invoice for this deal
        # and update it if the amount changed significantly
        
        logger.info(f"Deal {event.objectId} amount changed to {event.propertyValue}")
        
        return {
            "status": "processed",
            "action": "amount_updated",
            "new_amount": event.propertyValue
        }
    
    async def handle_deal_creation(self, event: HubSpotWebhookEvent) -> Dict[str, Any]:
        """
        Handle deal creation event.
        
        Args:
            event: Deal creation event
            
        Returns:
            Dict with handling result
        """
        try:
            # Get the new deal data
            deal_data = await self.connector.get_deal_by_id(event.objectId)
            
            # Check if auto-invoice generation is enabled for new deals
            auto_generate = self.config.get("settings", {}).get("auto_generate_invoice_on_creation", False)
            
            if auto_generate:
                # Generate invoice from new deal
                invoice_data = await self.connector.transform_deal_to_invoice(deal_data)
                
                # TODO: Save invoice to database
                logger.info(f"Auto-generated invoice for new deal {event.objectId}: {invoice_data['invoice_number']}")
                
                return {
                    "status": "processed",
                    "action": "deal_created_with_invoice",
                    "invoice_number": invoice_data["invoice_number"]
                }
            
            return {
                "status": "processed",
                "action": "deal_created",
                "auto_invoice": False
            }
            
        except Exception as e:
            logger.error(f"Error handling deal creation: {str(e)}")
            raise IntegrationError(f"Failed to handle deal creation: {str(e)}")
    
    async def handle_deal_deletion(self, event: HubSpotWebhookEvent) -> Dict[str, Any]:
        """
        Handle deal deletion event.
        
        Args:
            event: Deal deletion event
            
        Returns:
            Dict with handling result
        """
        # TODO: Handle deal deletion
        # - Mark associated invoices as cancelled
        # - Clean up any related data
        
        logger.info(f"Deal {event.objectId} was deleted")
        
        return {
            "status": "processed",
            "action": "deal_deleted",
            "cleanup_performed": False  # TODO: Implement cleanup
        }
    
    async def handle_contact_property_change(self, event: HubSpotWebhookEvent) -> Dict[str, Any]:
        """
        Handle contact property change event.
        
        Args:
            event: Contact property change event
            
        Returns:
            Dict with handling result
        """
        # TODO: Update associated deal customer data if needed
        logger.info(f"Contact {event.objectId} property '{event.propertyName}' changed")
        
        return {
            "status": "processed",
            "action": "contact_updated"
        }
    
    async def handle_company_property_change(self, event: HubSpotWebhookEvent) -> Dict[str, Any]:
        """
        Handle company property change event.
        
        Args:
            event: Company property change event
            
        Returns:
            Dict with handling result
        """
        # TODO: Update associated deal customer data if needed
        logger.info(f"Company {event.objectId} property '{event.propertyName}' changed")
        
        return {
            "status": "processed",
            "action": "company_updated"
        }


async def verify_hubspot_webhook(request: Request, webhook_secret: str) -> bool:
    """
    Verify HubSpot webhook signature.
    
    Args:
        request: FastAPI request object
        webhook_secret: Webhook secret for verification
        
    Returns:
        bool: True if signature is valid
    """
    signature = request.headers.get("X-HubSpot-Signature-V3", "")
    
    if not signature:
        logger.warning("No signature found in webhook request")
        return False
    
    body = await request.body()
    
    try:
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()
        
        # Remove 'sha256=' prefix if present
        if signature.startswith('sha256='):
            signature = signature[7:]
            
        return hmac.compare_digest(expected_signature, signature)
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {str(e)}")
        return False


def create_webhook_processor(connection_config: Dict[str, Any]) -> HubSpotWebhookProcessor:
    """
    Create a webhook processor instance.
    
    Args:
        connection_config: HubSpot connection configuration
        
    Returns:
        HubSpotWebhookProcessor instance
    """
    return HubSpotWebhookProcessor(connection_config)