"""
Odoo Invoice Service for TaxPoynt eInvoice - System Integrator Functions.

This module provides System Integrator (SI) role functionality for Odoo invoice
processing, UBL transformation, and integration with IRN generation workflow.

SI Role Responsibilities:
- Odoo invoice data extraction and processing
- UBL format transformation and validation
- Invoice data standardization for FIRS compliance
- ERP invoice workflow integration and batch processing
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union
import json
from datetime import datetime

from app.services.firs_si.odoo_connector import OdooConnector
from app.services.firs_si.odoo_ubl_mapper import odoo_ubl_mapper
from app.services.firs_si.odoo_ubl_validator import odoo_ubl_validator
from app.services.firs_si.odoo_ubl_transformer import odoo_ubl_transformer
from app.services.firs_si.odoo_service import generate_irn_for_odoo_invoice, test_odoo_connection

logger = logging.getLogger(__name__)


class OdooInvoiceService:
    """
    System Integrator service for Odoo invoice processing and UBL transformation.
    
    This class provides SI role functions for integrating the Odoo UBL mapping
    system with the existing invoice generation workflow to deliver end-to-end
    ERP invoice processing for FIRS e-invoicing compliance.
    """
    
    def __init__(self, connector: OdooConnector = None):
        """
        Initialize the service with an optional connector.
        
        Args:
            connector: An OdooConnector instance, or None to create on demand
        """
        self.connector = connector
    
    def process_invoice(
        self,
        invoice_id: int,
        connector_params: Dict[str, str],
        save_ubl: bool = True,
        validate_ubl: bool = True
    ) -> Dict[str, Any]:
        """
        Process an Odoo invoice for FIRS compliance - SI Role Function.
        
        Performs complete invoice processing: retrieve from Odoo ERP, map to UBL format,
        validate against FIRS requirements, and generate IRN for System Integrator workflows.
        
        Args:
            invoice_id: The Odoo invoice ID to process
            connector_params: Parameters for creating a connector if needed
                (host, db, user, password/api_key)
            save_ubl: Whether to save the UBL XML to the database
            validate_ubl: Whether to validate the UBL against schema
            
        Returns:
            Dictionary with processing results including status, IRN, and any errors
        """
        result = {
            "success": False,
            "invoice_id": invoice_id,
            "errors": [],
            "warnings": [],
            "irn": None,
            "ubl_validation": None,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Ensure we have a connector
            connector = self._get_connector(connector_params)
            
            # Step 1: Retrieve the invoice from Odoo
            logger.info(f"Retrieving invoice {invoice_id} from Odoo")
            invoice = connector.get_invoice_by_id(invoice_id)
            if not invoice:
                result["errors"].append({
                    "code": "INVOICE_NOT_FOUND",
                    "message": f"Invoice with ID {invoice_id} not found in Odoo"
                })
                return result
            
            company_info = connector.get_company_info()
            logger.info(f"Retrieved invoice {invoice['name']} and company info")
            
            # Step 2: Map to UBL format and validate
            logger.info(f"Mapping invoice {invoice['name']} to UBL format")
            ubl_invoice, validation_issues = odoo_ubl_transformer.odoo_to_ubl_object(
                invoice, company_info
            )
            
            # Handle validation issues
            if validation_issues:
                for issue in validation_issues:
                    if issue["code"].startswith("MISSING_") or issue["code"].endswith("_MISMATCH"):
                        result["errors"].append(issue)
                    else:
                        result["warnings"].append(issue)
                        
                # If there are errors (not just warnings), stop processing
                if any(issue in result["errors"] for issue in validation_issues):
                    logger.error(f"Validation errors in invoice {invoice['name']}")
                    return result
            
            # Step 3: Transform to UBL XML
            logger.info(f"Transforming invoice {invoice['name']} to UBL XML")
            ubl_xml, conversion_issues = odoo_ubl_transformer.ubl_object_to_xml(ubl_invoice)
            
            # Handle conversion issues
            if conversion_issues:
                for issue in conversion_issues:
                    result["errors"].append(issue)
                logger.error(f"UBL XML conversion errors in invoice {invoice['name']}")
                return result
            
            # Step 4: Validate UBL XML against schema if requested
            if validate_ubl:
                from app.services.ubl_validator import UBLValidator
                
                logger.info(f"Validating UBL XML for invoice {invoice['name']}")
                validator = UBLValidator()
                valid, schema_errors = validator.validate_against_schema(ubl_xml)
                
                result["ubl_validation"] = {
                    "valid": valid,
                    "errors": [error.dict() for error in schema_errors] if not valid else []
                }
                
                if not valid:
                    logger.warning(f"UBL schema validation failed for invoice {invoice['name']}")
                    for error in schema_errors:
                        result["warnings"].append({
                            "code": "SCHEMA_VALIDATION_ERROR",
                            "field": error.field,
                            "message": error.error
                        })
            
            # Step 5: Save UBL XML if requested (simplified here, actual implementation would use a database)
            if save_ubl:
                logger.info(f"Saving UBL XML for invoice {invoice['name']}")
                # In a real implementation, this would save to a database
                # Here we just log it as completed
                logger.info(f"UBL XML saved for invoice {invoice['name']}")
            
            # Step 6: Generate IRN using the existing service
            logger.info(f"Generating IRN for invoice {invoice['name']}")
            irn_result = generate_irn_for_odoo_invoice(
                connector_params["host"],
                connector_params["db"],
                connector_params["user"],
                connector_params.get("password", ""),
                connector_params.get("api_key", ""),
                invoice_id
            )
            
            if "irn" in irn_result and irn_result["irn"]:
                result["irn"] = irn_result["irn"]
                result["success"] = True
                logger.info(f"Successfully generated IRN {result['irn']} for invoice {invoice['name']}")
            else:
                result["errors"].append({
                    "code": "IRN_GENERATION_FAILED",
                    "message": "Failed to generate IRN: " + irn_result.get("message", "Unknown error")
                })
                logger.error(f"IRN generation failed for invoice {invoice['name']}")
            
            return result
            
        except Exception as e:
            logger.exception(f"Error processing invoice {invoice_id}: {str(e)}")
            result["errors"].append({
                "code": "PROCESSING_ERROR",
                "message": f"Error processing invoice: {str(e)}"
            })
            return result
    
    def process_invoices(
        self,
        from_date: str = None,
        to_date: str = None,
        connector_params: Dict[str, str] = None,
        include_draft: bool = False,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        Process multiple invoices from Odoo ERP - SI Role Function.
        
        Performs batch processing of Odoo invoices within a date range for
        System Integrator bulk operations and ERP integration workflows.
        
        Args:
            from_date: Start date for invoice search (YYYY-MM-DD)
            to_date: End date for invoice search (YYYY-MM-DD)
            connector_params: Parameters for creating a connector if needed
            include_draft: Whether to include draft invoices
            page: Page number for pagination
            page_size: Number of invoices per page
            
        Returns:
            Dictionary with processing results including per-invoice results
        """
        result = {
            "success": False,
            "total_count": 0,
            "processed_count": 0,
            "success_count": 0,
            "error_count": 0,
            "results": [],
            "errors": [],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_pages": 0
            },
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Ensure we have a connector
            connector = self._get_connector(connector_params)
            
            # Step 1: Retrieve invoices from Odoo
            logger.info(f"Retrieving invoices from Odoo within date range {from_date} to {to_date}")
            invoices_result = connector.get_invoices(
                from_date=datetime.fromisoformat(from_date) if from_date else None,
                to_date=datetime.fromisoformat(to_date) if to_date else None,
                include_draft=include_draft,
                page=page,
                page_size=page_size
            )
            
            # Update pagination info
            result["pagination"] = {
                "page": invoices_result["page"],
                "page_size": invoices_result["page_size"],
                "total_pages": invoices_result["pages"]
            }
            result["total_count"] = invoices_result["total"]
            
            invoices = invoices_result["invoices"]
            if not invoices:
                result["errors"].append({
                    "code": "NO_INVOICES_FOUND",
                    "message": f"No invoices found in the specified date range"
                })
                return result
            
            # Step 2: Process each invoice
            logger.info(f"Processing {len(invoices)} invoices")
            for invoice in invoices:
                invoice_result = self.process_invoice(
                    invoice_id=invoice["id"],
                    connector_params=connector_params,
                    save_ubl=True,
                    validate_ubl=True
                )
                
                result["results"].append(invoice_result)
                result["processed_count"] += 1
                
                if invoice_result["success"]:
                    result["success_count"] += 1
                else:
                    result["error_count"] += 1
            
            # Set overall success flag
            result["success"] = result["error_count"] == 0
            
            logger.info(f"Processed {result['processed_count']} invoices: "
                       f"{result['success_count']} successful, {result['error_count']} failed")
            
            return result
            
        except Exception as e:
            logger.exception(f"Error processing invoices: {str(e)}")
            result["errors"].append({
                "code": "BATCH_PROCESSING_ERROR",
                "message": f"Error processing invoices: {str(e)}"
            })
            return result
    
    def test_connection(self, connector_params: Dict[str, str]) -> Dict[str, Any]:
        """
        Test the connection to Odoo ERP system - SI Role Function.
        
        Validates Odoo ERP connectivity and system information for
        System Integrator configuration and troubleshooting.
        
        Args:
            connector_params: Parameters for creating a connector
            
        Returns:
            Dictionary with connection test results
        """
        try:
            # Use the existing test_odoo_connection function
            test_result = test_odoo_connection(
                connector_params["host"],
                connector_params["db"],
                connector_params["user"],
                connector_params.get("password", ""),
                connector_params.get("api_key", "")
            )
            
            # Add UBL mapping version information
            test_result["ubl_mapping"] = {
                "version": "1.0.0",
                "supported_formats": ["BIS Billing 3.0", "FIRS e-Invoice"]
            }
            
            return test_result
            
        except Exception as e:
            logger.exception(f"Error testing connection: {str(e)}")
            return {
                "success": False,
                "message": f"Connection test failed: {str(e)}"
            }
    
    def _get_connector(self, connector_params: Dict[str, str] = None) -> OdooConnector:
        """
        Get an OdooConnector instance, creating one if necessary.
        
        Args:
            connector_params: Parameters for creating a connector if needed
            
        Returns:
            An OdooConnector instance
        """
        if self.connector is not None:
            return self.connector
        
        if connector_params is None:
            raise ValueError("Connector parameters must be provided if no connector exists")
        
        # Create a new connector using the config approach
        from app.schemas.integration import OdooConfig, OdooAuthMethod
        
        config = OdooConfig(
            url=f"http://{connector_params['host']}",
            database=connector_params["db"],
            username=connector_params["user"],
            password=connector_params.get("password"),
            api_key=connector_params.get("api_key"),
            auth_method=OdooAuthMethod.API_KEY if connector_params.get("api_key") else OdooAuthMethod.PASSWORD
        )
        
        connector = OdooConnector(config=config)
        
        # Authenticate with Odoo
        connector.authenticate()
        
        return connector


# Create a singleton instance for reuse
odoo_invoice_service = OdooInvoiceService()