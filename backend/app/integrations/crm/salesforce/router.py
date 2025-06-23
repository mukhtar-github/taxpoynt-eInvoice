"""
Salesforce CRM Integration Router.

This module provides FastAPI routes for Salesforce CRM integration,
including OAuth flow, webhook endpoints, and testing utilities.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.integrations.crm.salesforce.connector import SalesforceConnector
from app.integrations.crm.salesforce.webhooks import (
    SalesforceWebhookHandler,
    SalesforceWebhookValidator
)
from app.integrations.crm.salesforce.models import (
    SalesforceOpportunity,
    OpportunityToInvoiceTransformer,
    SalesforceDataValidator
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/salesforce", tags=["Salesforce CRM"])


class SalesforceConnectionConfig(BaseModel):
    """Request model for Salesforce connection configuration."""
    
    client_id: str
    private_key: str
    username: str
    sandbox: bool = False
    instance_url: Optional[str] = None
    connection_name: str = "Salesforce Connection"


class SalesforceTestRequest(BaseModel):
    """Request model for testing Salesforce connection."""
    
    config: SalesforceConnectionConfig
    test_type: str = "basic"  # basic, opportunities, full


class SalesforceOpportunitySync(BaseModel):
    """Request model for syncing opportunities."""
    
    limit: int = 100
    offset: int = 0
    modified_since: Optional[datetime] = None
    stage_names: Optional[List[str]] = None


class SalesforceWebhookRequest(BaseModel):
    """Request model for webhook events."""
    
    events: List[Dict[str, Any]]
    signature: Optional[str] = None


# Dependency to get Salesforce connector
async def get_salesforce_connector(config: Dict[str, Any]) -> SalesforceConnector:
    """Create and return a Salesforce connector instance."""
    return SalesforceConnector(config)


@router.post("/test-connection")
async def test_salesforce_connection(request: SalesforceTestRequest):
    """
    Test connection to Salesforce.
    
    This endpoint allows testing Salesforce connectivity without saving credentials.
    """
    try:
        # Create connector with test configuration
        connector = SalesforceConnector(request.config.dict())
        
        if request.test_type == "basic":
            # Basic authentication test
            result = await connector.test_connection()
            
        elif request.test_type == "opportunities":
            # Test opportunities access
            auth_result = await connector.authenticate()
            if not auth_result.get("success"):
                raise HTTPException(status_code=401, detail="Authentication failed")
            
            # Try to fetch a few opportunities
            opportunities = await connector.get_opportunities(limit=5)
            
            result = {
                "success": True,
                "message": "Opportunities access successful",
                "details": {
                    "opportunities_count": len(opportunities.get("opportunities", [])),
                    "total_size": opportunities.get("total_size", 0),
                    "instance_url": connector.instance_url,
                    "api_version": connector.api_version
                }
            }
            
        elif request.test_type == "full":
            # Full integration test
            auth_result = await connector.authenticate()
            if not auth_result.get("success"):
                raise HTTPException(status_code=401, detail="Authentication failed")
            
            # Test opportunities access
            opportunities = await connector.get_opportunities(limit=5)
            
            # Test data transformation
            transformer = OpportunityToInvoiceTransformer()
            transformed_count = 0
            
            for opp in opportunities.get("opportunities", []):
                try:
                    transformer.transform_opportunity_to_deal(opp)
                    transformed_count += 1
                except Exception as e:
                    logger.warning(f"Failed to transform opportunity {opp.get('Id')}: {str(e)}")
            
            result = {
                "success": True,
                "message": "Full integration test successful",
                "details": {
                    "authentication": "success",
                    "opportunities_accessible": True,
                    "opportunities_count": len(opportunities.get("opportunities", [])),
                    "transformation_success_rate": f"{transformed_count}/{len(opportunities.get('opportunities', []))}",
                    "instance_url": connector.instance_url,
                    "api_version": connector.api_version,
                    "sandbox": connector.sandbox
                }
            }
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown test type: {request.test_type}")
        
        return {
            "success": result.get("success", False),
            "message": result.get("message", "Test completed"),
            "details": result.get("details", {}),
            "test_type": request.test_type,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Salesforce connection test failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Connection test failed: {str(e)}"
        )


@router.post("/sync-opportunities")
async def sync_salesforce_opportunities(
    connection_id: str,
    sync_request: SalesforceOpportunitySync,
    background_tasks: BackgroundTasks
):
    """
    Sync opportunities from Salesforce.
    
    This endpoint initiates a sync of opportunities from Salesforce.
    The actual sync process runs in the background.
    """
    try:
        # In a real implementation, you would:
        # 1. Get connection config from database using connection_id
        # 2. Create connector with stored credentials
        # 3. Add sync task to background queue
        
        # For now, return a mock response
        sync_job_id = f"sf_sync_{connection_id}_{int(datetime.now().timestamp())}"
        
        # Add background task (placeholder)
        background_tasks.add_task(
            _sync_opportunities_background,
            connection_id,
            sync_request.dict(),
            sync_job_id
        )
        
        return {
            "success": True,
            "message": "Opportunity sync job started",
            "sync_job_id": sync_job_id,
            "estimated_duration": "5-10 minutes",
            "status": "queued",
            "parameters": {
                "limit": sync_request.limit,
                "offset": sync_request.offset,
                "modified_since": sync_request.modified_since.isoformat() if sync_request.modified_since else None,
                "stage_names": sync_request.stage_names
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to start opportunity sync: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start sync: {str(e)}"
        )


@router.post("/webhook/{connection_id}")
async def handle_salesforce_webhook(
    connection_id: str,
    request: Request,
    webhook_request: SalesforceWebhookRequest
):
    """
    Handle incoming Salesforce webhook events.
    
    This endpoint processes Change Data Capture and Platform Events from Salesforce.
    """
    try:
        # Get request body for signature verification
        body = await request.body()
        signature = request.headers.get("X-Salesforce-Signature", "")
        
        # In a real implementation, get connection config from database
        # For now, create a mock configuration
        connection_config = {
            "connection_id": connection_id,
            "webhook_secret": "your_webhook_secret",  # Should come from database
            "connection_settings": {
                "deal_stage_mapping": {
                    "Closed Won": "generate_invoice",
                    "Proposal/Price Quote": "create_draft"
                },
                "auto_generate_invoice_on_creation": False
            }
        }
        
        # Create webhook handler
        webhook_handler = SalesforceWebhookHandler(connection_config)
        
        # Verify signature if provided
        if signature and not webhook_handler.verify_webhook_signature(body, signature):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        # Process webhook events
        result = await webhook_handler.process_webhook_batch(webhook_request.events)
        
        return {
            "success": result.get("success", False),
            "message": f"Processed {result.get('successful_events', 0)} events successfully",
            "details": {
                "total_events": result.get("total_events", 0),
                "successful_events": result.get("successful_events", 0),
                "failed_events": result.get("failed_events", 0),
                "connection_id": connection_id,
                "processed_at": result.get("processed_at")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Webhook processing failed: {str(e)}"
        )


@router.get("/opportunity/{opportunity_id}")
async def get_salesforce_opportunity(
    opportunity_id: str,
    connection_id: str
):
    """
    Get a specific Salesforce opportunity.
    
    This endpoint retrieves and returns a specific opportunity by ID.
    """
    try:
        # In a real implementation, get connection config from database
        # For now, return a mock response
        
        return {
            "success": True,
            "message": f"Opportunity {opportunity_id} retrieved successfully",
            "opportunity": {
                "id": opportunity_id,
                "name": "Sample Opportunity",
                "amount": 50000.0,
                "stage": "Proposal/Price Quote",
                "close_date": "2024-01-15",
                "account": {
                    "name": "Sample Account",
                    "id": "001XX000003DHPj"
                }
            },
            "connection_id": connection_id
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve opportunity: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve opportunity: {str(e)}"
        )


@router.post("/transform-opportunity")
async def transform_opportunity_to_deal(
    opportunity_data: Dict[str, Any],
    connection_settings: Optional[Dict[str, Any]] = None
):
    """
    Transform a Salesforce opportunity to TaxPoynt deal format.
    
    This endpoint is useful for testing the transformation logic.
    """
    try:
        transformer = OpportunityToInvoiceTransformer()
        
        # Transform to deal format
        deal = transformer.transform_opportunity_to_deal(
            opportunity_data,
            connection_settings
        )
        
        # Validate the result
        validator = SalesforceDataValidator()
        validation_result = validator.validate_opportunity(opportunity_data)
        customer_validation = validator.validate_customer_data(deal.get("customer_data", {}))
        
        return {
            "success": True,
            "message": "Opportunity transformed successfully",
            "deal": deal,
            "validation": {
                "opportunity_valid": validation_result.get("valid", False),
                "customer_valid": customer_validation.get("valid", False),
                "issues": validation_result.get("issues", []) + customer_validation.get("issues", []),
                "warnings": validation_result.get("warnings", []) + customer_validation.get("warnings", [])
            }
        }
        
    except Exception as e:
        logger.error(f"Opportunity transformation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Transformation failed: {str(e)}"
        )


@router.get("/connection/{connection_id}/status")
async def get_salesforce_connection_status(connection_id: str):
    """
    Get the status of a Salesforce connection.
    
    This endpoint returns the current status and health of a Salesforce connection.
    """
    try:
        # In a real implementation, get connection from database and test it
        
        return {
            "success": True,
            "connection_id": connection_id,
            "status": "connected",
            "last_sync": "2024-01-01T12:00:00Z",
            "last_test": "2024-01-01T11:55:00Z",
            "health": "healthy",
            "statistics": {
                "total_opportunities": 150,
                "synced_opportunities": 145,
                "generated_invoices": 25,
                "last_webhook_received": "2024-01-01T11:50:00Z"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get connection status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get connection status: {str(e)}"
        )


async def _sync_opportunities_background(
    connection_id: str,
    sync_params: Dict[str, Any],
    sync_job_id: str
):
    """
    Background task for syncing opportunities.
    
    This function would contain the actual sync logic in a real implementation.
    """
    try:
        logger.info(f"Starting background sync for connection {connection_id}, job {sync_job_id}")
        
        # Placeholder for actual sync logic:
        # 1. Get connection config from database
        # 2. Create Salesforce connector
        # 3. Sync opportunities
        # 4. Transform to deals
        # 5. Save to database
        # 6. Update sync job status
        
        logger.info(f"Completed background sync for job {sync_job_id}")
        
    except Exception as e:
        logger.error(f"Background sync failed for job {sync_job_id}: {str(e)}")


# Health check endpoint for Salesforce integration
@router.get("/health")
async def salesforce_health_check():
    """Health check endpoint for Salesforce integration."""
    return {
        "status": "healthy",
        "service": "salesforce-crm-integration",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "capabilities": [
            "jwt_authentication",
            "opportunity_sync",
            "webhook_handling",
            "change_data_capture",
            "platform_events"
        ]
    }