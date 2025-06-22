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
from sqlalchemy.orm import Session

from app.integrations.crm.hubspot.connector import HubSpotConnector, get_hubspot_connector
from app.integrations.crm.hubspot.models import HubSpotWebhookEvent, HubSpotWebhookPayload
from app.integrations.base.errors import IntegrationError
from app.models.crm_connection import CRMDeal
from app.models.invoice import Invoice, InvoiceStatus
from app.db.session import SessionLocal

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
        
        # Always trigger deal processing task for stage changes
        # This will handle the invoice generation and database updates
        try:
            # Import here to avoid circular imports
            from app.tasks.hubspot_tasks import process_hubspot_deal
            
            # Trigger background processing of the deal
            connection_id = self.config.get("connection_id")
            if connection_id:
                # Process the deal asynchronously
                import asyncio
                asyncio.create_task(process_hubspot_deal(event.objectId, connection_id))
                
                logger.info(f"Triggered background processing for deal {event.objectId} after stage change to {new_stage}")
                
                return {
                    "status": "processed",
                    "action": "deal_processing_triggered",
                    "deal_stage": new_stage,
                    "background_task_started": True
                }
            else:
                logger.warning(f"No connection_id found in config for deal {event.objectId}")
                return {
                    "status": "error",
                    "action": "missing_connection_id",
                    "deal_stage": new_stage
                }
                
        except Exception as e:
            logger.error(f"Error triggering deal processing for {event.objectId}: {str(e)}")
            return {
                "status": "error",
                "action": "deal_processing_failed",
                "error": str(e),
                "deal_stage": new_stage
            }
    
    async def handle_deal_amount_change(self, event: HubSpotWebhookEvent, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle deal amount change.
        
        This method updates existing invoices when a deal amount changes significantly.
        It creates a new invoice version or updates draft invoices.
        
        Args:
            event: Webhook event
            deal_data: Current deal data
            
        Returns:
            Dict with handling result
        """
        db = SessionLocal()
        
        try:
            # Find the deal in our database
            deal = db.query(CRMDeal).filter(
                CRMDeal.external_deal_id == str(event.objectId)
            ).first()
            
            if not deal:
                logger.warning(f"Deal {event.objectId} not found in database for amount update")
                return {
                    "status": "processed",
                    "action": "amount_updated",
                    "new_amount": event.propertyValue,
                    "invoice_updated": False,
                    "reason": "deal_not_found"
                }
            
            # Update the deal amount
            old_amount = deal.deal_amount
            new_amount = float(event.propertyValue) if event.propertyValue else 0
            deal.deal_amount = new_amount
            deal.updated_at = datetime.utcnow()
            
            # Check if there's an associated invoice
            if not deal.invoice_id:
                logger.info(f"Deal {event.objectId} amount updated but no invoice exists")
                db.commit()
                return {
                    "status": "processed",
                    "action": "amount_updated",
                    "new_amount": new_amount,
                    "old_amount": float(old_amount) if old_amount else 0,
                    "invoice_updated": False,
                    "reason": "no_invoice_exists"
                }
            
            # Get the associated invoice
            invoice = db.query(Invoice).filter(Invoice.id == deal.invoice_id).first()
            if not invoice:
                logger.warning(f"Invoice {deal.invoice_id} not found for deal {event.objectId}")
                db.commit()
                return {
                    "status": "processed",
                    "action": "amount_updated",
                    "new_amount": new_amount,
                    "invoice_updated": False,
                    "reason": "invoice_not_found"
                }
            
            # Only update if the amount change is significant (>5% or >100 currency units)
            old_invoice_amount = float(invoice.total_amount)
            amount_diff = abs(new_amount - old_invoice_amount)
            percentage_change = (amount_diff / old_invoice_amount * 100) if old_invoice_amount > 0 else 100
            
            if amount_diff < 100 and percentage_change < 5:
                logger.info(f"Deal {event.objectId} amount change too small to update invoice ({amount_diff:.2f}, {percentage_change:.1f}%)")
                db.commit()
                return {
                    "status": "processed",
                    "action": "amount_updated",
                    "new_amount": new_amount,
                    "invoice_updated": False,
                    "reason": "change_not_significant",
                    "amount_diff": amount_diff,
                    "percentage_change": percentage_change
                }
            
            # Update the invoice if it's still in draft status
            if invoice.status == InvoiceStatus.DRAFT:
                invoice.total_amount = new_amount
                invoice.subtotal = new_amount  # Simplified - should calculate proper subtotal/tax
                invoice.updated_at = datetime.utcnow()
                
                # Add metadata about the update
                invoice.invoice_metadata = invoice.invoice_metadata or {}
                invoice.invoice_metadata.update({
                    "amount_updated_from_deal": True,
                    "original_amount": old_invoice_amount,
                    "updated_amount": new_amount,
                    "update_timestamp": datetime.utcnow().isoformat(),
                    "deal_event_id": event.eventId
                })
                
                db.commit()
                
                logger.info(f"Updated draft invoice {invoice.invoice_number} amount from {old_invoice_amount} to {new_amount}")
                
                return {
                    "status": "processed",
                    "action": "amount_updated",
                    "new_amount": new_amount,
                    "old_amount": old_invoice_amount,
                    "invoice_updated": True,
                    "invoice_id": str(invoice.id),
                    "invoice_number": invoice.invoice_number,
                    "invoice_status": invoice.status.value
                }
            else:
                # For non-draft invoices, just log the discrepancy
                logger.warning(f"Invoice {invoice.invoice_number} cannot be updated (status: {invoice.status.value}) - deal amount changed from {old_invoice_amount} to {new_amount}")
                
                # Add metadata to track the discrepancy
                invoice.invoice_metadata = invoice.invoice_metadata or {}
                invoice.invoice_metadata.update({
                    "deal_amount_discrepancy": True,
                    "deal_amount": new_amount,
                    "invoice_amount": old_invoice_amount,
                    "discrepancy_noted_at": datetime.utcnow().isoformat()
                })
                
                db.commit()
                
                return {
                    "status": "processed",
                    "action": "amount_updated",
                    "new_amount": new_amount,
                    "old_amount": old_invoice_amount,
                    "invoice_updated": False,
                    "reason": "invoice_not_draft",
                    "invoice_status": invoice.status.value,
                    "discrepancy_logged": True
                }
                
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating deal amount for {event.objectId}: {str(e)}")
            return {
                "status": "error",
                "action": "amount_update_failed",
                "error": str(e),
                "invoice_updated": False
            }
        finally:
            db.close()
    
    async def handle_deal_creation(self, event: HubSpotWebhookEvent) -> Dict[str, Any]:
        """
        Handle deal creation event.
        
        Args:
            event: Deal creation event
            
        Returns:
            Dict with handling result
        """
        try:
            # Always trigger deal processing for new deals
            # This will handle the database creation and potential invoice generation
            from app.tasks.hubspot_tasks import process_hubspot_deal
            
            # Trigger background processing of the deal
            connection_id = self.config.get("connection_id")
            if connection_id:
                # Process the deal asynchronously
                import asyncio
                asyncio.create_task(process_hubspot_deal(event.objectId, connection_id))
                
                logger.info(f"Triggered background processing for new deal {event.objectId}")
                
                return {
                    "status": "processed",
                    "action": "deal_creation_processing_triggered",
                    "background_task_started": True
                }
            else:
                logger.warning(f"No connection_id found in config for new deal {event.objectId}")
                return {
                    "status": "error",
                    "action": "missing_connection_id"
                }
            
        except Exception as e:
            logger.error(f"Error handling deal creation: {str(e)}")
            return {
                "status": "error",
                "action": "deal_creation_processing_failed",
                "error": str(e)
            }
    
    async def handle_deal_deletion(self, event: HubSpotWebhookEvent) -> Dict[str, Any]:
        """
        Handle deal deletion event.
        
        This method performs cleanup when a deal is deleted from HubSpot:
        - Marks associated invoices as cancelled
        - Soft deletes the deal record from our database
        - Logs cleanup actions for audit purposes
        
        Args:
            event: Deal deletion event
            
        Returns:
            Dict with handling result
        """
        db = SessionLocal()
        cleanup_actions = []
        
        try:
            # Find the deal in our database
            deal = db.query(CRMDeal).filter(
                CRMDeal.external_deal_id == str(event.objectId)
            ).first()
            
            if not deal:
                logger.warning(f"Deal {event.objectId} not found in database, no cleanup needed")
                return {
                    "status": "processed",
                    "action": "deal_deleted",
                    "cleanup_performed": False,
                    "reason": "deal_not_found_in_database"
                }
            
            # Handle associated invoice cleanup
            if deal.invoice_id:
                invoice = db.query(Invoice).filter(Invoice.id == deal.invoice_id).first()
                if invoice and invoice.status != InvoiceStatus.CANCELLED:
                    # Mark invoice as cancelled if it's not already
                    old_status = invoice.status
                    invoice.status = InvoiceStatus.CANCELLED
                    invoice.updated_at = datetime.utcnow()
                    
                    cleanup_actions.append({
                        "action": "invoice_cancelled",
                        "invoice_id": str(invoice.id),
                        "invoice_number": invoice.invoice_number,
                        "previous_status": old_status.value,
                        "new_status": InvoiceStatus.CANCELLED.value
                    })
                    
                    logger.info(f"Cancelled invoice {invoice.invoice_number} associated with deleted deal {event.objectId}")
            
            # Soft delete the deal record by marking it as inactive
            # We don't hard delete to maintain audit trail
            deal.deal_metadata = deal.deal_metadata or {}
            deal.deal_metadata.update({
                "deleted_from_hubspot": True,
                "deletion_timestamp": datetime.utcnow().isoformat(),
                "deletion_event_id": event.eventId
            })
            deal.updated_at = datetime.utcnow()
            
            cleanup_actions.append({
                "action": "deal_marked_deleted",
                "deal_id": str(deal.id),
                "external_deal_id": deal.external_deal_id,
                "deal_title": deal.deal_title
            })
            
            # Commit all changes
            db.commit()
            
            logger.info(f"Successfully cleaned up data for deleted deal {event.objectId}")
            
            return {
                "status": "processed",
                "action": "deal_deleted",
                "cleanup_performed": True,
                "cleanup_actions": cleanup_actions,
                "deal_id": str(deal.id)
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error during deal deletion cleanup for {event.objectId}: {str(e)}")
            return {
                "status": "error",
                "action": "deal_deletion_cleanup_failed",
                "error": str(e),
                "cleanup_performed": False
            }
        finally:
            db.close()
    
    async def handle_contact_property_change(self, event: HubSpotWebhookEvent) -> Dict[str, Any]:
        """
        Handle contact property change event.
        
        This method updates customer data in associated deals and invoices
        when important contact properties change (name, email, etc.).
        
        Args:
            event: Contact property change event
            
        Returns:
            Dict with handling result
        """
        # Only update for important customer properties
        important_properties = {
            "firstname", "lastname", "email", "phone", "company", 
            "address", "city", "state", "zip", "country"
        }
        
        if event.propertyName not in important_properties:
            logger.debug(f"Contact {event.objectId} property '{event.propertyName}' changed - not important for deals")
            return {
                "status": "processed",
                "action": "contact_updated",
                "property_updated": False,
                "reason": "property_not_important"
            }
        
        db = SessionLocal()
        updates_made = []
        
        try:
            # Find deals associated with this contact
            # Note: This would require storing contact associations in the deal metadata
            # or fetching from HubSpot API to get the latest contact data
            
            deals = db.query(CRMDeal).filter(
                CRMDeal.customer_data.op('->')('contact_id').astext == str(event.objectId)
            ).all()
            
            if not deals:
                logger.debug(f"No deals found associated with contact {event.objectId}")
                return {
                    "status": "processed",
                    "action": "contact_updated",
                    "property_updated": False,
                    "reason": "no_associated_deals"
                }
            
            # For each associated deal, we would need to fetch updated contact data
            # and update the customer_data field. This is a placeholder implementation
            # that logs the need for update - in production you'd call HubSpot API
            
            for deal in deals:
                # Update the deal's customer data timestamp to indicate it needs refresh
                deal.deal_metadata = deal.deal_metadata or {}
                deal.deal_metadata.update({
                    "contact_data_needs_refresh": True,
                    "contact_last_updated": datetime.utcnow().isoformat(),
                    "contact_property_changed": event.propertyName
                })
                deal.updated_at = datetime.utcnow()
                
                updates_made.append({
                    "deal_id": str(deal.id),
                    "external_deal_id": deal.external_deal_id,
                    "action": "marked_for_contact_refresh"
                })
                
                logger.info(f"Marked deal {deal.external_deal_id} for contact data refresh due to contact {event.objectId} property change")
            
            db.commit()
            
            return {
                "status": "processed",
                "action": "contact_updated",
                "property_updated": True,
                "property_name": event.propertyName,
                "deals_affected": len(deals),
                "updates_made": updates_made
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating deals for contact {event.objectId} property change: {str(e)}")
            return {
                "status": "error",
                "action": "contact_update_failed",
                "error": str(e),
                "property_updated": False
            }
        finally:
            db.close()
    
    async def handle_company_property_change(self, event: HubSpotWebhookEvent) -> Dict[str, Any]:
        """
        Handle company property change event.
        
        This method updates customer data in associated deals and invoices
        when important company properties change (name, address, tax info, etc.).
        
        Args:
            event: Company property change event
            
        Returns:
            Dict with handling result
        """
        # Only update for important company properties
        important_properties = {
            "name", "domain", "phone", "address", "address2", "city", 
            "state", "zip", "country", "industry", "website", "description",
            "tax_number", "registration_number"  # Important for invoicing
        }
        
        if event.propertyName not in important_properties:
            logger.debug(f"Company {event.objectId} property '{event.propertyName}' changed - not important for deals")
            return {
                "status": "processed",
                "action": "company_updated",
                "property_updated": False,
                "reason": "property_not_important"
            }
        
        db = SessionLocal()
        updates_made = []
        
        try:
            # Find deals associated with this company
            # Note: This would require storing company associations in the deal metadata
            # or fetching from HubSpot API to get the latest company data
            
            deals = db.query(CRMDeal).filter(
                CRMDeal.customer_data.op('->')('company_id').astext == str(event.objectId)
            ).all()
            
            if not deals:
                logger.debug(f"No deals found associated with company {event.objectId}")
                return {
                    "status": "processed",
                    "action": "company_updated",
                    "property_updated": False,
                    "reason": "no_associated_deals"
                }
            
            # For each associated deal, mark for company data refresh
            for deal in deals:
                # Update the deal's customer data timestamp to indicate it needs refresh
                deal.deal_metadata = deal.deal_metadata or {}
                deal.deal_metadata.update({
                    "company_data_needs_refresh": True,
                    "company_last_updated": datetime.utcnow().isoformat(),
                    "company_property_changed": event.propertyName
                })
                deal.updated_at = datetime.utcnow()
                
                updates_made.append({
                    "deal_id": str(deal.id),
                    "external_deal_id": deal.external_deal_id,
                    "action": "marked_for_company_refresh"
                })
                
                logger.info(f"Marked deal {deal.external_deal_id} for company data refresh due to company {event.objectId} property change")
            
            db.commit()
            
            return {
                "status": "processed",
                "action": "company_updated",
                "property_updated": True,
                "property_name": event.propertyName,
                "deals_affected": len(deals),
                "updates_made": updates_made
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating deals for company {event.objectId} property change: {str(e)}")
            return {
                "status": "error",
                "action": "company_update_failed",
                "error": str(e),
                "property_updated": False
            }
        finally:
            db.close()


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