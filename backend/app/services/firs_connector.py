"""
FIRS API Connector Service for Odoo Integration.

This module provides a connector between the Odoo UBL transformer
and the FIRS API service for seamless invoice submissions.
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Union
import json
from datetime import datetime

from app.services.firs_service import firs_service, InvoiceSubmissionResponse, SubmissionStatus
from app.services.odoo_ubl_transformer import odoo_ubl_transformer
from app.schemas.invoice_validation import InvoiceValidationRequest
from app.core.config import settings

logger = logging.getLogger(__name__)


class FIRSConnector:
    """
    Connector between Odoo UBL transformer and FIRS API service.
    
    This class:
    1. Handles the end-to-end process of transforming Odoo data to UBL
    2. Submits the transformed data to FIRS API
    3. Provides status tracking and error handling
    """
    
    def __init__(self, use_sandbox: Optional[bool] = None):
        """
        Initialize the FIRS connector.
        
        Args:
            use_sandbox: Override the default sandbox setting from config
        """
        self.service = firs_service
        
        # Override sandbox setting if specified
        if use_sandbox is not None and use_sandbox != firs_service.use_sandbox:
            # Create a new service instance with the specified sandbox mode
            from app.core.config import settings
            self.service = type(firs_service)(
                use_sandbox=use_sandbox,
                base_url=settings.FIRS_SANDBOX_API_URL if use_sandbox else settings.FIRS_API_URL,
                api_key=settings.FIRS_SANDBOX_API_KEY if use_sandbox else settings.FIRS_API_KEY,
                api_secret=settings.FIRS_SANDBOX_API_SECRET if use_sandbox else settings.FIRS_API_SECRET
            )
        
        self.transformer = odoo_ubl_transformer
        self.environment = "sandbox" if self.service.use_sandbox else "production"
        logger.info(f"FIRSConnector initialized in {self.environment} environment")
    
    async def process_odoo_invoice(
        self, 
        odoo_invoice: Dict[str, Any], 
        company_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process an Odoo invoice for FIRS submission.
        
        This is the main method for processing Odoo invoices, handling:
        1. Transformation to UBL format
        2. Validation
        3. Submission to FIRS
        4. Response processing
        
        Args:
            odoo_invoice: Odoo invoice data dictionary
            company_info: Company information for the supplier
            
        Returns:
            Dictionary with submission details
        """
        start_time = datetime.now()
        logger.info(f"Processing Odoo invoice {odoo_invoice.get('name', 'Unknown')} for FIRS submission")
        
        try:
            # Step 1: Transform to UBL
            ubl_invoice, validation_issues = self.transformer.odoo_to_ubl_object(
                odoo_invoice, 
                company_info
            )
            
            transformation_time = (datetime.now() - start_time).total_seconds()
            logger.debug(f"UBL transformation completed in {transformation_time:.2f} seconds")
            
            # Handle validation failures
            if not ubl_invoice:
                return {
                    "success": False,
                    "message": "Failed to transform invoice to UBL format",
                    "validation_issues": validation_issues,
                    "processing_time": transformation_time
                }
            
            # Step 2: Submit to FIRS API
            submission_start = datetime.now()
            submission_response = await self.service.submit_invoice(ubl_invoice.dict())
            
            submission_time = (datetime.now() - submission_start).total_seconds()
            total_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"FIRS submission completed in {submission_time:.2f} seconds. "
                f"Total processing time: {total_time:.2f} seconds. "
                f"Result: {'Success' if submission_response.success else 'Failed'}"
            )
            
            # Step 3: Return combined result
            return {
                "success": submission_response.success,
                "message": submission_response.message,
                "submission_id": submission_response.submission_id,
                "validation_issues": validation_issues,
                "firs_response": submission_response.details,
                "processing_time": total_time,
                "environment": self.environment,
                "odoo_invoice_id": odoo_invoice.get("id"),
                "odoo_invoice_name": odoo_invoice.get("name"),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            elapsed_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error processing Odoo invoice for FIRS: {str(e)}", exc_info=True)
            
            return {
                "success": False,
                "message": f"Processing error: {str(e)}",
                "error_details": str(e),
                "processing_time": elapsed_time,
                "environment": self.environment,
                "odoo_invoice_id": odoo_invoice.get("id"),
                "odoo_invoice_name": odoo_invoice.get("name"),
                "timestamp": datetime.now().isoformat()
            }
    
    async def process_batch(
        self, 
        odoo_invoices: List[Dict[str, Any]], 
        company_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a batch of Odoo invoices for FIRS submission.
        
        Args:
            odoo_invoices: List of Odoo invoice data dictionaries
            company_info: Company information for the supplier
            
        Returns:
            Dictionary with batch submission details
        """
        start_time = datetime.now()
        logger.info(f"Processing batch of {len(odoo_invoices)} Odoo invoices for FIRS submission")
        
        try:
            ubl_invoices = []
            all_validation_issues = []
            invoice_mapping = {}  # Maps UBL invoice to original Odoo invoice ID
            
            # Step 1: Transform all invoices
            for idx, odoo_invoice in enumerate(odoo_invoices):
                # Transform to UBL
                ubl_invoice, validation_issues = self.transformer.odoo_to_ubl_object(
                    odoo_invoice, 
                    company_info
                )
                
                # Track validation issues with invoice index and ID
                if validation_issues:
                    for issue in validation_issues:
                        issue["invoice_index"] = idx
                        issue["odoo_invoice_id"] = odoo_invoice.get("id")
                        issue["odoo_invoice_name"] = odoo_invoice.get("name")
                    all_validation_issues.extend(validation_issues)
                
                # Add valid invoices to batch
                if ubl_invoice:
                    ubl_dict = ubl_invoice.dict()
                    ubl_invoices.append(ubl_dict)
                    # Map UBL invoice to Odoo invoice for tracking
                    invoice_mapping[ubl_dict["irn"]] = {
                        "odoo_id": odoo_invoice.get("id"),
                        "odoo_name": odoo_invoice.get("name")
                    }
            
            transformation_time = (datetime.now() - start_time).total_seconds()
            logger.debug(f"Batch UBL transformation completed in {transformation_time:.2f} seconds")
            
            # If no valid invoices, return only validation issues
            if not ubl_invoices:
                return {
                    "success": False,
                    "message": "Failed to transform any invoices to UBL format",
                    "validation_issues": all_validation_issues,
                    "processing_time": transformation_time,
                    "environment": self.environment
                }
            
            # Step 2: Submit batch to FIRS API
            submission_start = datetime.now()
            batch_response = await self.service.submit_invoices_batch(ubl_invoices)
            
            submission_time = (datetime.now() - submission_start).total_seconds()
            total_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"FIRS batch submission completed in {submission_time:.2f} seconds. "
                f"Total processing time: {total_time:.2f} seconds. "
                f"Result: {'Success' if batch_response.success else 'Failed'} "
                f"for {len(ubl_invoices)} invoices"
            )
            
            # Step 3: Return combined result
            return {
                "success": batch_response.success,
                "message": batch_response.message,
                "batch_id": batch_response.submission_id,
                "invoice_count": len(odoo_invoices),
                "success_count": len(ubl_invoices),
                "failed_count": len(odoo_invoices) - len(ubl_invoices),
                "validation_issues": all_validation_issues,
                "invoice_mapping": invoice_mapping,
                "firs_response": batch_response.details,
                "processing_time": total_time,
                "environment": self.environment,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            elapsed_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error processing batch for FIRS: {str(e)}", exc_info=True)
            
            return {
                "success": False,
                "message": f"Batch processing error: {str(e)}",
                "error_details": str(e),
                "processing_time": elapsed_time,
                "environment": self.environment,
                "invoice_count": len(odoo_invoices),
                "timestamp": datetime.now().isoformat()
            }
    
    async def track_submission(self, submission_id: str, max_retries: int = 10, retry_interval: int = 5) -> Dict[str, Any]:
        """
        Track a submission until completion or max retries.
        
        Args:
            submission_id: ID of the submission to track
            max_retries: Maximum number of status check attempts
            retry_interval: Seconds to wait between retries
            
        Returns:
            Final submission status details
        """
        logger.info(f"Tracking submission {submission_id} (max {max_retries} attempts, {retry_interval}s interval)")
        
        for attempt in range(1, max_retries + 1):
            try:
                status_result = await self.service.check_submission_status(submission_id)
                
                logger.debug(f"Attempt {attempt}/{max_retries}: Status = {status_result.status}")
                
                # If status indicates completion, return results
                if status_result.status in ["COMPLETED", "REJECTED", "FAILED", "ERROR"]:
                    logger.info(f"Submission {submission_id} reached final status: {status_result.status}")
                    return {
                        "submission_id": status_result.submission_id,
                        "status": status_result.status,
                        "final": True,
                        "attempts": attempt,
                        "timestamp": status_result.timestamp,
                        "message": status_result.message,
                        "details": status_result.details,
                        "environment": self.environment
                    }
                
                # If still processing, wait and retry
                if attempt < max_retries:
                    await asyncio.sleep(retry_interval)
            
            except Exception as e:
                logger.warning(f"Error checking submission status (attempt {attempt}/{max_retries}): {str(e)}")
                if attempt < max_retries:
                    await asyncio.sleep(retry_interval)
        
        # If we reached max retries without completion
        logger.warning(f"Max retries ({max_retries}) reached for submission {submission_id} without completion")
        return {
            "submission_id": submission_id,
            "status": "UNKNOWN",
            "final": False,
            "attempts": max_retries,
            "message": f"Status tracking exceeded {max_retries} attempts without reaching a final status",
            "environment": self.environment,
            "timestamp": datetime.now().isoformat()
        }


# Create default instances for singleton use
firs_connector = FIRSConnector()
firs_sandbox_connector = FIRSConnector(use_sandbox=True)
