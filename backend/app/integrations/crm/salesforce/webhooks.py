"""
Salesforce Webhook Handler for Platform Events and Change Data Capture.

This module handles incoming webhooks from Salesforce Platform Events and 
Change Data Capture (CDC) to process real-time opportunity updates.
"""

import logging
import json
import hmac
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List

from fastapi import HTTPException, Request
from pydantic import BaseModel, ValidationError

from app.integrations.crm.salesforce.models import (
    SalesforceWebhookEvent,
    OpportunityToInvoiceTransformer,
    SalesforceDataValidator
)

logger = logging.getLogger(__name__)


class SalesforceChangeEvent(BaseModel):
    """Model for Salesforce Change Data Capture events."""
    
    ChangeEventHeader: Dict[str, Any]
    Id: Optional[str] = None
    Name: Optional[str] = None
    Amount: Optional[float] = None
    StageName: Optional[str] = None
    CloseDate: Optional[str] = None
    AccountId: Optional[str] = None
    OwnerId: Optional[str] = None


class SalesforcePlatformEvent(BaseModel):
    """Model for Salesforce Platform Events."""
    
    CreatedDate: str
    CreatedById: str
    EventUuid: str
    ReplayId: int
    OpportunityId__c: Optional[str] = None
    ChangeType__c: Optional[str] = None
    EventData__c: Optional[str] = None


class SalesforceWebhookHandler:
    """Handles Salesforce webhook events and processes them for TaxPoynt integration."""
    
    def __init__(self, connection_config: Dict[str, Any]):
        """
        Initialize the webhook handler.
        
        Args:
            connection_config: Connection configuration containing webhook settings
        """
        self.connection_config = connection_config
        self.connection_id = connection_config.get("connection_id")
        self.webhook_secret = connection_config.get("webhook_secret")
        self.transformer = OpportunityToInvoiceTransformer()
        self.validator = SalesforceDataValidator()
        
    def verify_webhook_signature(self, request_body: bytes, signature: str) -> bool:
        """
        Verify webhook signature from Salesforce.
        
        Args:
            request_body: Raw request body
            signature: Signature from Salesforce headers
            
        Returns:
            bool: True if signature is valid
        """
        if not self.webhook_secret:
            logger.warning("No webhook secret configured, skipping signature verification")
            return True
        
        try:
            # Salesforce uses HMAC-SHA256 for webhook signatures
            expected_signature = hmac.new(
                self.webhook_secret.encode(),
                request_body,
                hashlib.sha256
            ).hexdigest()
            
            # Remove any prefix from the signature
            if signature.startswith("sha256="):
                signature = signature[7:]
            
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {str(e)}")
            return False
    
    async def handle_change_data_capture(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle Salesforce Change Data Capture event.
        
        Args:
            event_data: CDC event data
            
        Returns:
            Dict with processing results
        """
        try:
            # Parse the change event
            change_event = SalesforceChangeEvent(**event_data)
            header = change_event.ChangeEventHeader
            
            # Extract change information
            change_type = header.get("changeType")  # CREATE, UPDATE, DELETE, UNDELETE
            changed_fields = header.get("changedFields", [])
            entity_name = header.get("entityName")
            record_ids = header.get("recordIds", [])
            
            logger.info(f"Received CDC event: {change_type} for {entity_name}, records: {record_ids}")
            
            # Only process Opportunity changes
            if entity_name != "Opportunity":
                return {
                    "success": True,
                    "message": f"Ignoring {entity_name} change event",
                    "processed": False
                }
            
            results = []
            
            for record_id in record_ids:
                try:
                    result = await self._process_opportunity_change(
                        record_id,
                        change_type,
                        changed_fields,
                        change_event.dict()
                    )
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to process opportunity {record_id}: {str(e)}")
                    results.append({
                        "opportunity_id": record_id,
                        "success": False,
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "message": f"Processed {len(results)} opportunity changes",
                "results": results,
                "change_type": change_type,
                "entity_name": entity_name
            }
            
        except ValidationError as e:
            logger.error(f"Invalid CDC event format: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid event format: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing CDC event: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Event processing failed: {str(e)}")
    
    async def handle_platform_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle Salesforce Platform Event.
        
        Args:
            event_data: Platform event data
            
        Returns:
            Dict with processing results
        """
        try:
            # Parse the platform event
            platform_event = SalesforcePlatformEvent(**event_data)
            
            # Extract opportunity ID from the event
            opportunity_id = platform_event.OpportunityId__c
            change_type = platform_event.ChangeType__c
            event_data_str = platform_event.EventData__c
            
            if not opportunity_id:
                return {
                    "success": True,
                    "message": "No opportunity ID in platform event",
                    "processed": False
                }
            
            logger.info(f"Received platform event for opportunity {opportunity_id}, change: {change_type}")
            
            # Parse additional event data if available
            additional_data = {}
            if event_data_str:
                try:
                    additional_data = json.loads(event_data_str)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse event data JSON")
            
            # Process the opportunity change
            result = await self._process_opportunity_change(
                opportunity_id,
                change_type,
                [],  # Changed fields not available in platform events
                additional_data
            )
            
            return {
                "success": True,
                "message": f"Processed platform event for opportunity {opportunity_id}",
                "result": result,
                "change_type": change_type,
                "replay_id": platform_event.ReplayId
            }
            
        except ValidationError as e:
            logger.error(f"Invalid platform event format: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid event format: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing platform event: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Event processing failed: {str(e)}")
    
    async def _process_opportunity_change(
        self,
        opportunity_id: str,
        change_type: str,
        changed_fields: List[str],
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process an individual opportunity change.
        
        Args:
            opportunity_id: Salesforce opportunity ID
            change_type: Type of change (CREATE, UPDATE, DELETE, etc.)
            changed_fields: List of changed field names
            event_data: Additional event data
            
        Returns:
            Dict with processing results
        """
        try:
            # Get connection settings
            connection_settings = self.connection_config.get("connection_settings", {})
            deal_stage_mapping = connection_settings.get("deal_stage_mapping", {})
            auto_generate = connection_settings.get("auto_generate_invoice_on_creation", False)
            
            # Determine action based on change type and changed fields
            action_needed = self._determine_action(
                change_type,
                changed_fields,
                event_data,
                deal_stage_mapping,
                auto_generate
            )
            
            if action_needed == "no_action":
                return {
                    "opportunity_id": opportunity_id,
                    "success": True,
                    "action": "no_action",
                    "message": "No action required for this change"
                }
            
            # For now, we'll return a placeholder since we need the full TaxPoynt
            # database integration to actually create/update deals and generate invoices
            return {
                "opportunity_id": opportunity_id,
                "success": True,
                "action": action_needed,
                "message": f"Action {action_needed} queued for opportunity {opportunity_id}",
                "change_type": change_type,
                "changed_fields": changed_fields,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing opportunity change {opportunity_id}: {str(e)}")
            return {
                "opportunity_id": opportunity_id,
                "success": False,
                "error": str(e),
                "change_type": change_type
            }
    
    def _determine_action(
        self,
        change_type: str,
        changed_fields: List[str],
        event_data: Dict[str, Any],
        deal_stage_mapping: Dict[str, str],
        auto_generate: bool
    ) -> str:
        """
        Determine what action to take based on the change.
        
        Args:
            change_type: Type of change
            changed_fields: Changed fields
            event_data: Event data
            deal_stage_mapping: Stage to action mapping
            auto_generate: Whether to auto-generate invoices
            
        Returns:
            str: Action to take (generate_invoice, create_draft, sync_data, no_action)
        """
        # Handle new opportunities
        if change_type == "CREATE":
            if auto_generate:
                return "generate_invoice"
            else:
                return "sync_data"
        
        # Handle opportunity updates
        if change_type == "UPDATE":
            # Check if stage changed
            if "StageName" in changed_fields:
                current_stage = event_data.get("StageName")
                if current_stage and current_stage in deal_stage_mapping:
                    mapped_action = deal_stage_mapping[current_stage]
                    if mapped_action in ["generate_invoice", "create_draft"]:
                        return mapped_action
            
            # Check if amount or other important fields changed
            important_fields = ["Amount", "CloseDate", "Name", "AccountId"]
            if any(field in changed_fields for field in important_fields):
                return "sync_data"
        
        # Handle deletions
        if change_type == "DELETE":
            return "mark_deleted"
        
        # Handle undeletions
        if change_type == "UNDELETE":
            return "sync_data"
        
        return "no_action"
    
    async def process_webhook_batch(self, webhook_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process a batch of webhook events.
        
        Args:
            webhook_events: List of webhook event data
            
        Returns:
            Dict with batch processing results
        """
        results = []
        
        for event in webhook_events:
            try:
                # Determine event type and process accordingly
                if "ChangeEventHeader" in event:
                    # Change Data Capture event
                    result = await self.handle_change_data_capture(event)
                elif "EventUuid" in event:
                    # Platform Event
                    result = await self.handle_platform_event(event)
                else:
                    # Unknown event type
                    result = {
                        "success": False,
                        "error": "Unknown event type",
                        "event_data": event
                    }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing webhook event: {str(e)}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "event_data": event
                })
        
        successful = sum(1 for r in results if r.get("success", False))
        
        return {
            "success": successful > 0,
            "total_events": len(webhook_events),
            "successful_events": successful,
            "failed_events": len(webhook_events) - successful,
            "results": results,
            "processed_at": datetime.now().isoformat()
        }


class SalesforceWebhookValidator:
    """Validates incoming Salesforce webhook requests."""
    
    @staticmethod
    def validate_cdc_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Change Data Capture event structure."""
        issues = []
        
        if "ChangeEventHeader" not in event_data:
            issues.append("Missing ChangeEventHeader")
        else:
            header = event_data["ChangeEventHeader"]
            
            if "changeType" not in header:
                issues.append("Missing changeType in header")
            
            if "entityName" not in header:
                issues.append("Missing entityName in header")
            
            if "recordIds" not in header:
                issues.append("Missing recordIds in header")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    @staticmethod
    def validate_platform_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Platform Event structure."""
        issues = []
        
        required_fields = ["CreatedDate", "CreatedById", "EventUuid", "ReplayId"]
        
        for field in required_fields:
            if field not in event_data:
                issues.append(f"Missing required field: {field}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }


def create_salesforce_webhook_handler(connection_config: Dict[str, Any]) -> SalesforceWebhookHandler:
    """
    Factory function to create a Salesforce webhook handler.
    
    Args:
        connection_config: Connection configuration
        
    Returns:
        SalesforceWebhookHandler instance
    """
    return SalesforceWebhookHandler(connection_config)