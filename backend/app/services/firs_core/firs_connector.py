"""
FIRS Core Connector Service for TaxPoynt eInvoice - Core FIRS Functions.

This module provides Core FIRS functionality that serves as the foundation for both
System Integrator (SI) and Access Point Provider (APP) operations, handling base
FIRS API communication, connection management, and shared protocol implementations.

Core FIRS Responsibilities:
- Base FIRS API client functionality for all e-invoicing operations
- Connection management and authentication with FIRS endpoints
- Shared protocol implementations for invoice submission workflows
- Common utilities for FIRS data transformation and validation
- Base error handling and logging for FIRS operations
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Union
import json
from datetime import datetime, timedelta
from uuid import uuid4

from app.services.firs_core.firs_api_client import firs_service, InvoiceSubmissionResponse, SubmissionStatus
from app.services.firs_si.odoo_ubl_transformer import odoo_ubl_transformer
from app.schemas.invoice_validation import InvoiceValidationRequest
from app.core.config import settings

logger = logging.getLogger(__name__)


class FIRSConnector:
    """
    Core FIRS connector service providing base functionality for e-invoicing operations.
    
    This class serves as the foundation for both System Integrator (SI) and Access Point
    Provider (APP) operations, handling base FIRS API communication, connection management,
    and shared protocol implementations for Nigerian e-invoicing compliance.
    
    Core FIRS Functions:
    1. Base FIRS API client functionality for all e-invoicing operations
    2. Connection management and authentication with FIRS endpoints
    3. Shared protocol implementations for invoice submission workflows
    4. Common utilities for FIRS data transformation and validation
    5. Base error handling and logging for FIRS operations
    """
    
    def __init__(self, use_sandbox: Optional[bool] = None):
        """
        Initialize the Core FIRS connector for e-invoicing operations.
        
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
        
        # Core FIRS configuration
        self.connection_pool = {}
        self.last_health_check = None
        self.firs_compliance_version = "1.0"
        self.supported_document_types = ["invoice", "credit_note", "debit_note"]
        
        logger.info(f"Core FIRS Connector initialized in {self.environment} environment for e-invoicing operations")
    
    async def check_firs_health(self) -> Dict[str, Any]:
        """
        Check FIRS API health and connectivity - Core FIRS Function.
        
        Provides core health monitoring for FIRS API endpoints, ensuring
        reliable connection and service availability for e-invoicing operations.
        
        Returns:
            Dict containing FIRS health status and connectivity metrics
        """
        try:
            start_time = datetime.now()
            
            # Perform health check with FIRS API
            health_response = await self.service.health_check()
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            health_result = {
                "healthy": health_response.get("status") == "healthy",
                "response_time_seconds": response_time,
                "firs_version": health_response.get("version", "unknown"),
                "environment": self.environment,
                "timestamp": datetime.now().isoformat(),
                "compliance_version": self.firs_compliance_version,
                "supported_operations": health_response.get("supported_operations", []),
                "firs_core_ready": True
            }
            
            self.last_health_check = datetime.now()
            logger.info(f"FIRS health check completed: {'HEALTHY' if health_result['healthy'] else 'UNHEALTHY'} (Response time: {response_time:.2f}s)")
            
            return health_result
            
        except Exception as e:
            logger.error(f"FIRS health check failed: {str(e)}")
            return {
                "healthy": False,
                "error": str(e),
                "environment": self.environment,
                "timestamp": datetime.now().isoformat(),
                "firs_core_ready": False
            }
    
    async def validate_firs_credentials(self) -> Dict[str, Any]:
        """
        Validate FIRS API credentials and authentication - Core FIRS Function.
        
        Provides core credential validation for FIRS authentication,
        ensuring proper API access for e-invoicing operations.
        
        Returns:
            Dict containing credential validation results
        """
        try:
            validation_result = await self.service.validate_credentials()
            
            return {
                "valid": validation_result.get("valid", False),
                "expires_at": validation_result.get("expires_at"),
                "permissions": validation_result.get("permissions", []),
                "environment": self.environment,
                "firs_compliant": True,
                "core_validated": True,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"FIRS credential validation failed: {str(e)}")
            return {
                "valid": False,
                "error": str(e),
                "environment": self.environment,
                "firs_compliant": False,
                "core_validated": False,
                "timestamp": datetime.now().isoformat()
            }
    
    async def process_odoo_invoice(
        self, 
        odoo_invoice: Dict[str, Any], 
        company_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process an Odoo invoice for FIRS submission - Core FIRS Function.
        
        Provides core processing functionality for Odoo invoice transformation
        and FIRS submission, handling base workflows for e-invoicing compliance.
        
        This is the main method for processing Odoo invoices, handling:
        1. Transformation to UBL format using core utilities
        2. Validation against FIRS schemas
        3. Submission to FIRS using core API client
        4. Response processing and error handling
        
        Args:
            odoo_invoice: Odoo invoice data dictionary
            company_info: Company information for the supplier
            
        Returns:
            Dictionary with submission details and core processing metadata
        """
        start_time = datetime.now()
        processing_id = str(uuid4())
        
        logger.info(f"Core FIRS: Processing Odoo invoice {odoo_invoice.get('name', 'Unknown')} for e-invoicing (ID: {processing_id})")
        
        try:
            # Step 1: Transform to UBL using core transformation utilities
            ubl_invoice, validation_issues = self.transformer.odoo_to_ubl_object(
                odoo_invoice, 
                company_info
            )
            
            transformation_time = (datetime.now() - start_time).total_seconds()
            logger.debug(f"Core FIRS: UBL transformation completed in {transformation_time:.2f} seconds")
            
            # Handle validation failures
            if not ubl_invoice:
                return {
                    "success": False,
                    "message": "Core FIRS: Failed to transform invoice to UBL format",
                    "validation_issues": validation_issues,
                    "processing_time": transformation_time,
                    "processing_id": processing_id,
                    "firs_core_processed": True,
                    "compliance_level": "failed_transformation"
                }
            
            # Step 2: Submit to FIRS API using core client
            submission_start = datetime.now()
            submission_response = await self.service.submit_invoice(ubl_invoice.dict())
            
            submission_time = (datetime.now() - submission_start).total_seconds()
            total_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"Core FIRS: Submission completed in {submission_time:.2f} seconds. "
                f"Total processing time: {total_time:.2f} seconds. "
                f"Result: {'Success' if submission_response.success else 'Failed'} (ID: {processing_id})"
            )
            
            # Step 3: Return enhanced result with core metadata
            return {
                "success": submission_response.success,
                "message": submission_response.message,
                "submission_id": submission_response.submission_id,
                "processing_id": processing_id,
                "validation_issues": validation_issues,
                "firs_response": submission_response.details,
                "processing_time": total_time,
                "environment": self.environment,
                "odoo_invoice_id": odoo_invoice.get("id"),
                "odoo_invoice_name": odoo_invoice.get("name"),
                "firs_core_processed": True,
                "compliance_level": "full_compliance" if submission_response.success else "submission_failed",
                "core_version": self.firs_compliance_version,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            elapsed_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Core FIRS: Error processing Odoo invoice for e-invoicing (ID: {processing_id}): {str(e)}", exc_info=True)
            
            return {
                "success": False,
                "message": f"Core FIRS processing error: {str(e)}",
                "error_details": str(e),
                "processing_id": processing_id,
                "processing_time": elapsed_time,
                "environment": self.environment,
                "odoo_invoice_id": odoo_invoice.get("id"),
                "odoo_invoice_name": odoo_invoice.get("name"),
                "firs_core_processed": False,
                "compliance_level": "processing_error",
                "timestamp": datetime.now().isoformat()
            }
    
    async def process_batch(
        self, 
        odoo_invoices: List[Dict[str, Any]], 
        company_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a batch of Odoo invoices for FIRS submission - Core FIRS Function.
        
        Provides core batch processing functionality for multiple invoice submissions,
        optimizing e-invoicing workflows and ensuring efficient FIRS compliance.
        
        Args:
            odoo_invoices: List of Odoo invoice data dictionaries
            company_info: Company information for the supplier
            
        Returns:
            Dictionary with batch submission details and core processing metadata
        """
        start_time = datetime.now()
        batch_id = str(uuid4())
        
        logger.info(f"Core FIRS: Processing batch of {len(odoo_invoices)} Odoo invoices for e-invoicing (Batch ID: {batch_id})")
        
        try:
            ubl_invoices = []
            all_validation_issues = []
            invoice_mapping = {}  # Maps UBL invoice to original Odoo invoice ID
            
            # Step 1: Transform all invoices using core transformation
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
                        issue["batch_id"] = batch_id
                        issue["firs_core_validation"] = True
                    all_validation_issues.extend(validation_issues)
                
                # Add valid invoices to batch
                if ubl_invoice:
                    ubl_dict = ubl_invoice.dict()
                    ubl_invoices.append(ubl_dict)
                    # Map UBL invoice to Odoo invoice for tracking
                    invoice_mapping[ubl_dict["irn"]] = {
                        "odoo_id": odoo_invoice.get("id"),
                        "odoo_name": odoo_invoice.get("name"),
                        "batch_position": idx
                    }
            
            transformation_time = (datetime.now() - start_time).total_seconds()
            logger.debug(f"Core FIRS: Batch UBL transformation completed in {transformation_time:.2f} seconds")
            
            # If no valid invoices, return only validation issues
            if not ubl_invoices:
                return {
                    "success": False,
                    "message": "Core FIRS: Failed to transform any invoices to UBL format",
                    "validation_issues": all_validation_issues,
                    "processing_time": transformation_time,
                    "batch_id": batch_id,
                    "environment": self.environment,
                    "firs_core_processed": True,
                    "compliance_level": "batch_transformation_failed"
                }
            
            # Step 2: Submit batch to FIRS API using core client
            submission_start = datetime.now()
            batch_response = await self.service.submit_invoices_batch(ubl_invoices)
            
            submission_time = (datetime.now() - submission_start).total_seconds()
            total_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"Core FIRS: Batch submission completed in {submission_time:.2f} seconds. "
                f"Total processing time: {total_time:.2f} seconds. "
                f"Result: {'Success' if batch_response.success else 'Failed'} "
                f"for {len(ubl_invoices)} invoices (Batch ID: {batch_id})"
            )
            
            # Step 3: Return enhanced batch result with core metadata
            return {
                "success": batch_response.success,
                "message": batch_response.message,
                "batch_id": batch_id,
                "firs_batch_id": batch_response.submission_id,
                "invoice_count": len(odoo_invoices),
                "success_count": len(ubl_invoices),
                "failed_count": len(odoo_invoices) - len(ubl_invoices),
                "validation_issues": all_validation_issues,
                "invoice_mapping": invoice_mapping,
                "firs_response": batch_response.details,
                "processing_time": total_time,
                "environment": self.environment,
                "firs_core_processed": True,
                "compliance_level": "full_batch_compliance" if batch_response.success else "batch_submission_failed",
                "core_version": self.firs_compliance_version,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            elapsed_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Core FIRS: Error processing batch for e-invoicing (Batch ID: {batch_id}): {str(e)}", exc_info=True)
            
            return {
                "success": False,
                "message": f"Core FIRS batch processing error: {str(e)}",
                "error_details": str(e),
                "batch_id": batch_id,
                "processing_time": elapsed_time,
                "environment": self.environment,
                "invoice_count": len(odoo_invoices),
                "firs_core_processed": False,
                "compliance_level": "batch_processing_error",
                "timestamp": datetime.now().isoformat()
            }
    
    async def track_submission(self, submission_id: str, max_retries: int = 10, retry_interval: int = 5) -> Dict[str, Any]:
        """
        Track a submission until completion or max retries - Core FIRS Function.
        
        Provides core submission tracking functionality for FIRS e-invoicing operations,
        monitoring submission status and providing comprehensive tracking metadata.
        
        Args:
            submission_id: ID of the submission to track
            max_retries: Maximum number of status check attempts
            retry_interval: Seconds to wait between retries
            
        Returns:
            Final submission status details with core tracking metadata
        """
        tracking_id = str(uuid4())
        logger.info(f"Core FIRS: Tracking submission {submission_id} (max {max_retries} attempts, {retry_interval}s interval, tracking ID: {tracking_id})")
        
        tracking_history = []
        
        for attempt in range(1, max_retries + 1):
            try:
                check_start = datetime.now()
                status_result = await self.service.check_submission_status(submission_id)
                check_time = (datetime.now() - check_start).total_seconds()
                
                # Record tracking history
                tracking_history.append({
                    "attempt": attempt,
                    "status": status_result.status,
                    "timestamp": datetime.now().isoformat(),
                    "response_time": check_time,
                    "firs_core_tracked": True
                })
                
                logger.debug(f"Core FIRS: Attempt {attempt}/{max_retries}: Status = {status_result.status} (Response time: {check_time:.2f}s)")
                
                # If status indicates completion, return results
                if status_result.status in ["COMPLETED", "REJECTED", "FAILED", "ERROR"]:
                    logger.info(f"Core FIRS: Submission {submission_id} reached final status: {status_result.status} (Tracking ID: {tracking_id})")
                    return {
                        "submission_id": status_result.submission_id,
                        "status": status_result.status,
                        "final": True,
                        "attempts": attempt,
                        "tracking_id": tracking_id,
                        "tracking_history": tracking_history,
                        "timestamp": status_result.timestamp,
                        "message": status_result.message,
                        "details": status_result.details,
                        "environment": self.environment,
                        "firs_core_tracked": True,
                        "compliance_status": "tracked_to_completion"
                    }
                
                # If still processing, wait and retry
                if attempt < max_retries:
                    await asyncio.sleep(retry_interval)
            
            except Exception as e:
                logger.warning(f"Core FIRS: Error checking submission status (attempt {attempt}/{max_retries}): {str(e)}")
                tracking_history.append({
                    "attempt": attempt,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                    "firs_core_tracked": False
                })
                
                if attempt < max_retries:
                    await asyncio.sleep(retry_interval)
        
        # If we reached max retries without completion
        logger.warning(f"Core FIRS: Max retries ({max_retries}) reached for submission {submission_id} without completion (Tracking ID: {tracking_id})")
        return {
            "submission_id": submission_id,
            "status": "UNKNOWN",
            "final": False,
            "attempts": max_retries,
            "tracking_id": tracking_id,
            "tracking_history": tracking_history,
            "message": f"Core FIRS: Status tracking exceeded {max_retries} attempts without reaching a final status",
            "environment": self.environment,
            "firs_core_tracked": True,
            "compliance_status": "tracking_timeout",
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_firs_configuration(self) -> Dict[str, Any]:
        """
        Get current FIRS configuration and capabilities - Core FIRS Function.
        
        Provides core configuration information for FIRS e-invoicing operations,
        including supported features, compliance requirements, and API capabilities.
        
        Returns:
            Dict containing FIRS configuration and capabilities
        """
        try:
            config_response = await self.service.get_configuration()
            
            return {
                "environment": self.environment,
                "compliance_version": self.firs_compliance_version,
                "supported_document_types": self.supported_document_types,
                "firs_capabilities": config_response.get("capabilities", []),
                "api_version": config_response.get("api_version", "unknown"),
                "rate_limits": config_response.get("rate_limits", {}),
                "supported_formats": config_response.get("supported_formats", ["UBL2.1"]),
                "validation_rules": config_response.get("validation_rules", []),
                "firs_core_config": True,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Core FIRS: Error retrieving configuration: {str(e)}")
            return {
                "environment": self.environment,
                "compliance_version": self.firs_compliance_version,
                "supported_document_types": self.supported_document_types,
                "error": str(e),
                "firs_core_config": False,
                "timestamp": datetime.now().isoformat()
            }


# Create default instances for singleton use with core FIRS functionality
firs_connector = FIRSConnector()
firs_sandbox_connector = FIRSConnector(use_sandbox=True)
