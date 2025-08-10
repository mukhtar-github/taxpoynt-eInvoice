"""
Scheduled tasks for HubSpot CRM integration.

This module contains scheduled tasks that automate HubSpot deal processing,
including:
- Processing individual HubSpot deals
- Syncing historical deals from HubSpot
- Handling deal-to-invoice conversion
- Managing batch deal processing
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from uuid import UUID
from celery import current_task

from app.core.celery import celery_app
from app.db.session import SessionLocal
from app.integrations.crm.hubspot.connector import HubSpotConnector, get_hubspot_connector
from app.integrations.crm.hubspot.models import HubSpotDeal, HubSpotDealInvoice
from app.integrations.base.errors import IntegrationError, AuthenticationError
from app.models.crm_connection import CRMConnection, CRMDeal, CRMType
from app.models.user import User
from app.services.invoice_service import get_invoice_service
from app.services.firs_app.secure_communication_service import get_encryption_service
from app.utils.logger import get_logger

logger = get_logger(__name__)


@celery_app.task(bind=True, name="app.tasks.hubspot_tasks.process_hubspot_deal")
def process_hubspot_deal(self, deal_id: str, connection_id: str) -> Dict[str, Any]:
    """
    Process a single HubSpot deal and generate invoice if needed.
    
    Args:
        deal_id: HubSpot deal ID
        connection_id: HubSpot connection ID
        
    Returns:
        Dict with processing results
    """
    start_time = datetime.utcnow()
    db = SessionLocal()
    
    try:
        logger.info(f"Processing HubSpot deal {deal_id} for connection {connection_id}")
        
        # Get connection configuration from database
        connection = db.query(CRMConnection).filter(
            CRMConnection.id == connection_id,
            CRMConnection.is_active == True
        ).first()
        
        if not connection:
            raise ValueError(f"Active CRM connection {connection_id} not found")
        
        # Get connection config and decrypt credentials
        encryption_service = get_encryption_service(db)
        try:
            encrypted_credentials_dict = json.loads(connection.credentials_encrypted)
            decrypted_credentials = encryption_service.decrypt_integration_config(encrypted_credentials_dict)
        except Exception as e:
            logger.error(f"Failed to decrypt credentials for connection {connection_id}: {str(e)}")
            raise ValueError(f"Invalid or corrupted credentials for connection {connection_id}")
        
        connection_config = {
            "connection_id": connection_id,
            "auth": {
                "auth_type": "oauth2",
                "token_url": "https://api.hubapi.com/oauth/v1/token",
                "credentials": decrypted_credentials
            },
            "settings": connection.connection_settings or {}
        }
        
        # Create HubSpot connector
        connector = get_hubspot_connector(connection_config)
        
        # Fetch deal from HubSpot
        deal_data = asyncio.run(connector.get_deal_by_id(deal_id))
        
        # Check if deal already exists in our database
        existing_deal = db.query(CRMDeal).filter(
            CRMDeal.connection_id == connection_id,
            CRMDeal.external_deal_id == deal_id
        ).first()
        
        # Transform deal to invoice format
        invoice_data = asyncio.run(connector.transform_deal_to_invoice(deal_data))
        
        # Determine if invoice should be generated based on deal stage
        deal_properties = deal_data.get("properties", {})
        deal_stage = deal_properties.get("dealstage", "")
        stage_mapping = connection_config.get("settings", {}).get("deal_stage_mapping", {})
        
        should_generate_invoice = False
        if deal_stage in stage_mapping:
            action = stage_mapping[deal_stage]
            should_generate_invoice = action == "generate_invoice"
        
        # Update or create deal record in database
        if existing_deal:
            # Update existing deal
            existing_deal.deal_title = deal_properties.get("dealname", "")
            existing_deal.deal_amount = deal_properties.get("amount", 0)
            existing_deal.customer_data = invoice_data.get("customer", {})
            existing_deal.deal_stage = deal_stage
            existing_deal.expected_close_date = _parse_date(deal_properties.get("closedate"))
            existing_deal.deal_metadata = deal_data
            existing_deal.updated_at = datetime.utcnow()
            
            # Update invoice generation status
            if should_generate_invoice and not existing_deal.invoice_generated:
                # Create actual invoice record in database
                invoice_service = get_invoice_service(db)
                creator = db.query(User).filter(User.id == connection.user_id).first()
                if creator:
                    invoice = invoice_service.create_invoice_from_crm_deal(
                        deal=existing_deal,
                        invoice_data=invoice_data,
                        created_by=creator
                    )
                    logger.info(f"Generated invoice {invoice.invoice_number} for existing deal {deal_id}")
                else:
                    logger.error(f"Could not find user {connection.user_id} to create invoice for deal {deal_id}")
                
        else:
            # Create new deal record
            new_deal = CRMDeal(
                connection_id=connection_id,
                external_deal_id=deal_id,
                deal_title=deal_properties.get("dealname", ""),
                deal_amount=deal_properties.get("amount", 0),
                customer_data=invoice_data.get("customer", {}),
                deal_stage=deal_stage,
                expected_close_date=_parse_date(deal_properties.get("closedate")),
                invoice_generated=should_generate_invoice,
                deal_metadata=deal_data
            )
            
            if should_generate_invoice:
                # Create actual invoice record in database
                invoice_service = get_invoice_service(db)
                creator = db.query(User).filter(User.id == connection.user_id).first()
                if creator:
                    invoice = invoice_service.create_invoice_from_crm_deal(
                        deal=new_deal,
                        invoice_data=invoice_data,
                        created_by=creator
                    )
                    logger.info(f"Generated invoice {invoice.invoice_number} for new deal {deal_id}")
                else:
                    logger.error(f"Could not find user {connection.user_id} to create invoice for deal {deal_id}")
            
            db.add(new_deal)
        
        # Commit changes
        db.commit()
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return {
            "success": True,
            "message": f"Successfully processed HubSpot deal {deal_id}",
            "details": {
                "deal_id": deal_id,
                "connection_id": connection_id,
                "deal_stage": deal_stage,
                "invoice_generated": should_generate_invoice,
                "processing_time_seconds": processing_time,
                "deal_title": deal_properties.get("dealname", ""),
                "deal_amount": deal_properties.get("amount", 0)
            }
        }
        
    except IntegrationError as e:
        db.rollback()
        logger.error(f"Integration error processing deal {deal_id}: {str(e)}")
        return {
            "success": False,
            "message": f"Integration error processing deal {deal_id}: {str(e)}",
            "details": {
                "deal_id": deal_id,
                "connection_id": connection_id,
                "error_type": "IntegrationError",
                "error": str(e)
            }
        }
    except Exception as e:
        db.rollback()
        logger.exception(f"Unexpected error processing deal {deal_id}: {str(e)}")
        return {
            "success": False,
            "message": f"Error processing deal {deal_id}: {str(e)}",
            "details": {
                "deal_id": deal_id,
                "connection_id": connection_id,
                "error_type": e.__class__.__name__,
                "error": str(e)
            }
        }
    finally:
        db.close()


@celery_app.task(bind=True, name="app.tasks.hubspot_tasks.sync_hubspot_deals") 
def sync_hubspot_deals(self, connection_id: str, days_back: int = 30) -> Dict[str, Any]:
    """
    Sync deals from HubSpot for a specific connection.
    
    Args:
        connection_id: HubSpot connection ID
        days_back: Number of days to look back for deals (default 30)
        
    Returns:
        Dict with sync results
    """
    start_time = datetime.utcnow()
    db = SessionLocal()
    
    try:
        logger.info(f"Starting HubSpot deals sync for connection {connection_id}, {days_back} days back")
        
        # Get connection configuration from database
        connection = db.query(CRMConnection).filter(
            CRMConnection.id == connection_id,
            CRMConnection.is_active == True
        ).first()
        
        if not connection:
            raise ValueError(f"Active CRM connection {connection_id} not found")
        
        # Get connection config and decrypt credentials
        encryption_service = get_encryption_service(db)
        try:
            encrypted_credentials_dict = json.loads(connection.credentials_encrypted)
            decrypted_credentials = encryption_service.decrypt_integration_config(encrypted_credentials_dict)
        except Exception as e:
            logger.error(f"Failed to decrypt credentials for connection {connection_id}: {str(e)}")
            raise ValueError(f"Invalid or corrupted credentials for connection {connection_id}")
        
        connection_config = {
            "connection_id": connection_id,
            "auth": {
                "auth_type": "oauth2",
                "token_url": "https://api.hubapi.com/oauth/v1/token",
                "credentials": decrypted_credentials
            },
            "settings": connection.connection_settings or {}
        }
        
        # Create HubSpot connector
        connector = get_hubspot_connector(connection_config)
        
        # Calculate date filter for recent deals
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Fetch deals from HubSpot with pagination
        all_deals = []
        offset = 0
        limit = 100
        total_fetched = 0
        
        while True:
            try:
                # Get deals from HubSpot
                deals_response = asyncio.run(connector.get_deals(
                    limit=limit,
                    offset=offset,
                    properties=[
                        "dealname", "amount", "dealstage", "closedate", 
                        "createdate", "hs_lastmodifieddate", "hubspot_owner_id"
                    ]
                ))
                
                deals = deals_response.get("results", [])
                if not deals:
                    break
                
                # Filter deals by date
                filtered_deals = []
                for deal in deals:
                    properties = deal.get("properties", {})
                    create_date = _parse_date(properties.get("createdate"))
                    modified_date = _parse_date(properties.get("hs_lastmodifieddate"))
                    
                    # Include if created or modified within our date range
                    if (create_date and create_date >= cutoff_date) or \
                       (modified_date and modified_date >= cutoff_date):
                        filtered_deals.append(deal)
                
                all_deals.extend(filtered_deals)
                total_fetched += len(deals)
                offset += limit
                
                # If we got fewer deals than requested, we've reached the end
                if len(deals) < limit:
                    break
                    
                # Prevent infinite loops
                if total_fetched > 10000:  # Safety limit
                    logger.warning(f"Reached safety limit of 10000 deals for connection {connection_id}")
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching deals at offset {offset}: {str(e)}")
                break
        
        # Process each deal
        processed_count = 0
        error_count = 0
        skipped_count = 0
        
        for deal in all_deals:
            deal_id = deal.get("id")
            if not deal_id:
                skipped_count += 1
                continue
            
            try:
                # Process the deal
                result = process_hubspot_deal.apply_async(args=[deal_id, connection_id]).get()
                if result["success"]:
                    processed_count += 1
                else:
                    error_count += 1
                    logger.warning(f"Failed to process deal {deal_id}: {result['message']}")
                    
            except Exception as e:
                error_count += 1
                logger.exception(f"Error processing deal {deal_id} during sync: {str(e)}")
        
        # Update connection's last sync time
        connection.last_sync_at = datetime.utcnow()
        db.commit()
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(
            f"Completed HubSpot deals sync for connection {connection_id}: "
            f"{processed_count} processed, {error_count} errors, {skipped_count} skipped"
        )
        
        return {
            "success": True,
            "message": f"Successfully synced deals for connection {connection_id}",
            "details": {
                "connection_id": connection_id,
                "days_back": days_back,
                "total_deals_fetched": len(all_deals),
                "processed_count": processed_count,
                "error_count": error_count,
                "skipped_count": skipped_count,
                "processing_time_seconds": processing_time
            }
        }
        
    except Exception as e:
        db.rollback()
        logger.exception(f"Error syncing HubSpot deals for connection {connection_id}: {str(e)}")
        return {
            "success": False,
            "message": f"Error syncing deals: {str(e)}",
            "details": {
                "connection_id": connection_id,
                "error_type": e.__class__.__name__,
                "error": str(e)
            }
        }
    finally:
        db.close()


def batch_process_hubspot_deals(connection_ids: List[str], days_back: int = 30) -> Dict[str, Any]:
    """
    Process HubSpot deals for multiple connections in batch.
    
    Args:
        connection_ids: List of HubSpot connection IDs
        days_back: Number of days to look back for deals
        
    Returns:
        Dict with batch processing results
    """
    start_time = datetime.utcnow()
    
    logger.info(f"Starting batch processing for {len(connection_ids)} HubSpot connections")
    
    results = {
        "success": True,
        "message": "Batch processing completed",
        "details": {
            "total_connections": len(connection_ids),
            "successful_connections": 0,
            "failed_connections": 0,
            "connection_results": []
        }
    }
    
    for connection_id in connection_ids:
        try:
            logger.info(f"Processing connection {connection_id}")
            
            # Sync deals for this connection
            sync_result = sync_hubspot_deals.apply_async(args=[connection_id, days_back]).get()
            
            if sync_result["success"]:
                results["details"]["successful_connections"] += 1
            else:
                results["details"]["failed_connections"] += 1
                results["success"] = False
            
            results["details"]["connection_results"].append({
                "connection_id": connection_id,
                "result": sync_result
            })
            
        except Exception as e:
            logger.exception(f"Error processing connection {connection_id}: {str(e)}")
            results["details"]["failed_connections"] += 1
            results["success"] = False
            results["details"]["connection_results"].append({
                "connection_id": connection_id,
                "result": {
                    "success": False,
                    "message": f"Error: {str(e)}",
                    "error": str(e)
                }
            })
    
    # Calculate total processing time
    processing_time = (datetime.utcnow() - start_time).total_seconds()
    results["details"]["total_processing_time_seconds"] = processing_time
    
    logger.info(
        f"Batch processing completed: {results['details']['successful_connections']} successful, "
        f"{results['details']['failed_connections']} failed"
    )
    
    return results


def _parse_date(date_string: Optional[str]) -> Optional[datetime]:
    """
    Parse a date string from HubSpot API.
    
    Args:
        date_string: Date string from HubSpot
        
    Returns:
        Parsed datetime object or None
    """
    if not date_string:
        return None
    
    try:
        # HubSpot typically returns timestamps in milliseconds
        if date_string.isdigit():
            timestamp = int(date_string) / 1000  # Convert from milliseconds
            return datetime.fromtimestamp(timestamp)
        
        # Try ISO format
        return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        logger.warning(f"Could not parse date string: {date_string}")
        return None


# Background task for automatic deal processing
@celery_app.task(bind=True, name="app.tasks.hubspot_tasks.hubspot_deal_processor_task")
def hubspot_deal_processor_task(self):
    """
    Background task that periodically processes HubSpot deals for all active connections.
    
    This task is designed to run periodically (e.g., every hour) to sync deals
    from all active HubSpot connections.
    """
    logger.info("Running HubSpot deal processor task")
    
    db = SessionLocal()
    try:
        # Get all active HubSpot connections
        active_connections = db.query(CRMConnection).filter(
            CRMConnection.crm_type == "hubspot",
            CRMConnection.is_active == True
        ).all()
        
        if not active_connections:
            logger.info("No active HubSpot connections found")
            return
        
        connection_ids = [str(conn.id) for conn in active_connections]
        logger.info(f"Found {len(connection_ids)} active HubSpot connections")
        
        # Process deals for all connections
        result = asyncio.run(batch_process_hubspot_deals(connection_ids, days_back=1))  # Only last day for regular sync
        
        if result["success"]:
            logger.info(f"HubSpot deal processor task completed successfully")
        else:
            logger.warning(f"HubSpot deal processor task completed with errors")
            
    except Exception as e:
        logger.exception(f"Error in HubSpot deal processor task: {str(e)}")
    finally:
        db.close()