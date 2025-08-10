"""
Invoice service for TaxPoynt eInvoice - Access Point Provider Functions.

This module provides Access Point Provider (APP) role functionality for creating 
and managing invoices, processing invoice data for FIRS submission, and handling 
secure transmission protocols.

APP Role Responsibilities:
- Invoice processing and validation for FIRS compliance
- Secure invoice data transmission to FIRS
- Invoice status management and tracking
- FIRS submission workflow coordination
"""

import logging
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.invoice import Invoice, InvoiceStatus, InvoiceSource
from app.models.crm_connection import CRMDeal
from app.models.pos_connection import POSTransaction
from app.models.user import User
from app.services.firs_si.irn_generation_service import IRNService

logger = logging.getLogger(__name__)


class InvoiceService:
    """
    Access Point Provider service for managing invoice processing and FIRS submission.
    
    This service provides APP role functions for invoice creation, validation,
    and preparation for secure transmission to FIRS for e-invoicing compliance.
    """
    
    def __init__(self, db: Session):
        self.db = db
        
    def create_invoice_from_crm_deal(
        self,
        deal: CRMDeal,
        invoice_data: Dict[str, Any],
        created_by: User
    ) -> Invoice:
        """
        Create an invoice from a CRM deal for FIRS processing - APP Role Function.
        
        Creates invoices from CRM deal data and prepares them for Access Point Provider
        validation and transmission to FIRS for e-invoicing compliance.
        
        Args:
            deal: CRM deal object
            invoice_data: Transformed invoice data from the connector
            created_by: User creating the invoice
            
        Returns:
            Created Invoice object ready for FIRS processing
        """
        try:
            # Parse invoice data
            invoice_number = invoice_data.get("invoice_number", f"CRM-{deal.external_deal_id}")
            invoice_date = self._parse_date(invoice_data.get("invoice_date"))
            due_date = self._parse_date(invoice_data.get("due_date"))
            
            # Calculate amounts for FIRS compliance
            subtotal = Decimal(str(invoice_data.get("amount", 0)))
            tax_amount = Decimal(str(invoice_data.get("tax_amount", 0)))
            total_amount = subtotal + tax_amount
            
            # Create invoice with FIRS metadata
            invoice = Invoice(
                invoice_number=invoice_number,
                organization_id=created_by.current_organization_id,
                created_by=created_by.id,
                invoice_date=invoice_date,
                due_date=due_date,
                status=InvoiceStatus.DRAFT,
                source=InvoiceSource.CRM,
                subtotal=subtotal,
                tax_amount=tax_amount,
                total_amount=total_amount,
                currency_code=invoice_data.get("currency", "NGN"),
                customer_data=invoice_data.get("customer", {}),
                line_items=invoice_data.get("line_items", []),
                invoice_metadata={
                    "source_deal_id": deal.external_deal_id,
                    "source_platform": "hubspot",  # TODO: Make this dynamic
                    "deal_stage": deal.deal_stage,
                    "original_data": invoice_data.get("metadata", {}),
                    "firs_ready": True,  # Mark as ready for FIRS processing
                    "app_processing": {
                        "validation_required": True,
                        "transmission_pending": True
                    }
                },
                source_connection_id=deal.connection_id,
                source_entity_id=deal.external_deal_id
            )
            
            # Save to database
            self.db.add(invoice)
            self.db.flush()  # Get the ID without committing
            
            # Update the deal with the invoice reference
            deal.invoice_id = invoice.id
            deal.invoice_generated = True
            
            # Commit all changes
            self.db.commit()
            self.db.refresh(invoice)
            
            logger.info(f"Created invoice {invoice.invoice_number} from CRM deal {deal.external_deal_id} for FIRS processing")
            return invoice
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create invoice from CRM deal {deal.external_deal_id}: {str(e)}")
            raise
    
    def create_invoice_from_pos_transaction(
        self,
        transaction: POSTransaction,
        invoice_data: Dict[str, Any],
        created_by: User
    ) -> Invoice:
        """
        Create an invoice from a POS transaction for FIRS transmission - APP Role Function.
        
        Creates invoices from POS transaction data and prepares them for Access Point Provider
        secure transmission to FIRS for e-invoicing compliance.
        
        Args:
            transaction: POS transaction object
            invoice_data: Transformed invoice data from the connector
            created_by: User creating the invoice
            
        Returns:
            Created Invoice object ready for FIRS transmission
        """
        try:
            # Parse invoice data
            invoice_number = invoice_data.get("invoice_number", f"POS-{transaction.external_transaction_id}")
            invoice_date = self._parse_date(invoice_data.get("transaction_date"))
            
            # Calculate amounts for FIRS compliance
            subtotal = Decimal(str(invoice_data.get("amount", 0)))
            tax_amount = Decimal(str(invoice_data.get("tax_amount", 0)))
            total_amount = subtotal + tax_amount
            
            # Create invoice with FIRS transmission metadata
            invoice = Invoice(
                invoice_number=invoice_number,
                organization_id=created_by.current_organization_id,
                created_by=created_by.id,
                invoice_date=invoice_date,
                status=InvoiceStatus.SENT,  # POS transactions are usually completed
                source=InvoiceSource.POS,
                subtotal=subtotal,
                tax_amount=tax_amount,
                total_amount=total_amount,
                currency_code=invoice_data.get("currency", "NGN"),
                customer_data=invoice_data.get("customer", {}),
                line_items=invoice_data.get("line_items", []),
                invoice_metadata={
                    "source_transaction_id": transaction.external_transaction_id,
                    "source_platform": transaction.connection.pos_type.value,
                    "transaction_date": invoice_data.get("transaction_date"),
                    "original_data": invoice_data.get("metadata", {}),
                    "firs_ready": True,  # Mark as ready for FIRS processing
                    "app_processing": {
                        "validation_required": True,
                        "transmission_pending": True,
                        "pos_transaction": True
                    }
                },
                source_connection_id=transaction.connection_id,
                source_entity_id=transaction.external_transaction_id
            )
            
            # Save to database
            self.db.add(invoice)
            self.db.flush()  # Get the ID without committing
            
            # Update the transaction with the invoice reference
            transaction.invoice_id = invoice.id
            transaction.invoice_transmitted = True
            
            # Commit all changes
            self.db.commit()
            self.db.refresh(invoice)
            
            logger.info(f"Created invoice {invoice.invoice_number} from POS transaction {transaction.external_transaction_id} for FIRS transmission")
            return invoice
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create invoice from POS transaction {transaction.external_transaction_id}: {str(e)}")
            raise
    
    def create_manual_invoice(
        self,
        invoice_data: Dict[str, Any],
        created_by: User
    ) -> Invoice:
        """
        Create a manual invoice for FIRS submission - APP Role Function.
        
        Creates manual invoices and prepares them for Access Point Provider
        validation and secure transmission to FIRS.
        
        Args:
            invoice_data: Invoice data
            created_by: User creating the invoice
            
        Returns:
            Created Invoice object ready for FIRS processing
        """
        try:
            # Parse invoice data
            invoice_number = invoice_data.get("invoice_number")
            if not invoice_number:
                # Generate invoice number
                invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{datetime.now().timestamp():.0f}"
            
            invoice_date = self._parse_date(invoice_data.get("invoice_date"))
            due_date = self._parse_date(invoice_data.get("due_date"))
            
            # Calculate amounts for FIRS compliance
            subtotal = Decimal(str(invoice_data.get("subtotal", 0)))
            tax_amount = Decimal(str(invoice_data.get("tax_amount", 0)))
            total_amount = Decimal(str(invoice_data.get("total_amount", subtotal + tax_amount)))
            
            # Create invoice with FIRS processing metadata
            invoice = Invoice(
                invoice_number=invoice_number,
                organization_id=created_by.current_organization_id,
                created_by=created_by.id,
                invoice_date=invoice_date,
                due_date=due_date,
                status=InvoiceStatus(invoice_data.get("status", "draft")),
                source=InvoiceSource.MANUAL,
                subtotal=subtotal,
                tax_amount=tax_amount,
                total_amount=total_amount,
                currency_code=invoice_data.get("currency_code", "NGN"),
                customer_data=invoice_data.get("customer_data", {}),
                line_items=invoice_data.get("line_items", []),
                invoice_metadata={
                    **invoice_data.get("metadata", {}),
                    "firs_ready": True,  # Mark as ready for FIRS processing
                    "app_processing": {
                        "validation_required": True,
                        "transmission_pending": True,
                        "manual_entry": True
                    }
                }
            )
            
            # Save to database
            self.db.add(invoice)
            self.db.commit()
            self.db.refresh(invoice)
            
            logger.info(f"Created manual invoice {invoice.invoice_number} for FIRS processing")
            return invoice
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create manual invoice: {str(e)}")
            raise
    
    def generate_irn_for_invoice(self, invoice: Invoice) -> str:
        """
        Generate IRN for an invoice for FIRS transmission - APP Role Function.
        
        Generates Invoice Reference Numbers for Access Point Provider
        secure transmission and FIRS compliance validation.
        
        Args:
            invoice: Invoice to generate IRN for
            
        Returns:
            Generated IRN value for FIRS transmission
        """
        if invoice.irn_generated:
            logger.warning(f"IRN already generated for invoice {invoice.invoice_number}")
            return invoice.irn_value
        
        try:
            # Prepare IRN data for FIRS compliance
            irn_data = {
                "invoice_number": invoice.invoice_number,
                "invoice_date": invoice.invoice_date.strftime("%Y-%m-%d"),
                "customer_name": invoice.customer_name,
                "total_amount": float(invoice.total_amount),
                "currency_code": invoice.currency_code,
                "line_items": invoice.line_items or []
            }
            
            # Generate IRN using IRN service
            irn_service = IRNService(self.db)
            irn_record = irn_service.generate_invoice_irn(
                invoice_data=irn_data,
                organization_id=invoice.organization_id
            )
            
            # Update invoice with IRN for FIRS transmission
            invoice.mark_irn_generated(irn_record.irn)
            
            # Update APP processing metadata
            if invoice.invoice_metadata:
                invoice.invoice_metadata["app_processing"]["irn_generated"] = True
                invoice.invoice_metadata["app_processing"]["irn_value"] = irn_record.irn
                invoice.invoice_metadata["app_processing"]["ready_for_transmission"] = True
            
            self.db.commit()
            
            logger.info(f"Generated IRN {irn_record.irn} for invoice {invoice.invoice_number} for FIRS transmission")
            return irn_record.irn
            
        except Exception as e:
            logger.error(f"Failed to generate IRN for invoice {invoice.invoice_number}: {str(e)}")
            raise
    
    def validate_invoice_for_firs(self, invoice: Invoice) -> Dict[str, Any]:
        """
        Validate invoice for FIRS transmission - APP Role Function.
        
        Performs Access Point Provider validation checks to ensure invoice
        data meets FIRS requirements before secure transmission.
        
        Args:
            invoice: Invoice to validate
            
        Returns:
            Validation results dictionary
        """
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "firs_ready": False
        }
        
        try:
            # Required field validation
            if not invoice.invoice_number:
                validation_results["errors"].append("Invoice number is required")
            
            if not invoice.invoice_date:
                validation_results["errors"].append("Invoice date is required")
            
            if not invoice.customer_data or not invoice.customer_data.get("name"):
                validation_results["errors"].append("Customer information is required")
            
            if invoice.total_amount <= 0:
                validation_results["errors"].append("Total amount must be greater than zero")
            
            if not invoice.currency_code:
                validation_results["errors"].append("Currency code is required")
            
            # FIRS-specific validation
            if invoice.currency_code != "NGN":
                validation_results["warnings"].append("Non-NGN currency may require additional validation")
            
            if not invoice.line_items:
                validation_results["warnings"].append("No line items found - may affect FIRS processing")
            
            # Check if already has IRN
            if not invoice.irn_generated:
                validation_results["warnings"].append("IRN not generated - required for FIRS transmission")
            
            # Set validation status
            validation_results["valid"] = len(validation_results["errors"]) == 0
            validation_results["firs_ready"] = validation_results["valid"] and invoice.irn_generated
            
            # Update invoice metadata with validation results
            if invoice.invoice_metadata:
                invoice.invoice_metadata["app_processing"]["validation_completed"] = True
                invoice.invoice_metadata["app_processing"]["validation_results"] = validation_results
                invoice.invoice_metadata["app_processing"]["last_validated"] = datetime.utcnow().isoformat()
            
            self.db.commit()
            
            logger.info(f"Validated invoice {invoice.invoice_number} for FIRS transmission: {'VALID' if validation_results['valid'] else 'INVALID'}")
            return validation_results
            
        except Exception as e:
            logger.error(f"Failed to validate invoice {invoice.invoice_number}: {str(e)}")
            validation_results["valid"] = False
            validation_results["errors"].append(f"Validation error: {str(e)}")
            return validation_results
    
    def mark_invoice_transmitted(self, invoice: Invoice, transmission_id: str) -> None:
        """
        Mark invoice as transmitted to FIRS - APP Role Function.
        
        Updates invoice status after successful Access Point Provider
        transmission to FIRS for compliance tracking.
        
        Args:
            invoice: Invoice that was transmitted
            transmission_id: ID of the transmission record
        """
        try:
            # Update invoice metadata
            if invoice.invoice_metadata:
                invoice.invoice_metadata["app_processing"]["transmitted"] = True
                invoice.invoice_metadata["app_processing"]["transmission_id"] = transmission_id
                invoice.invoice_metadata["app_processing"]["transmitted_at"] = datetime.utcnow().isoformat()
            
            # Update invoice status if it was a draft
            if invoice.status == InvoiceStatus.DRAFT:
                invoice.status = InvoiceStatus.SENT
            
            self.db.commit()
            
            logger.info(f"Marked invoice {invoice.invoice_number} as transmitted to FIRS (transmission: {transmission_id})")
            
        except Exception as e:
            logger.error(f"Failed to mark invoice {invoice.invoice_number} as transmitted: {str(e)}")
            raise
    
    def _parse_date(self, date_value: Any) -> Optional[datetime]:
        """Parse date from various formats for FIRS compliance."""
        if not date_value:
            return None
            
        if isinstance(date_value, datetime):
            return date_value
        elif isinstance(date_value, date):
            return datetime.combine(date_value, datetime.min.time())
        elif isinstance(date_value, str):
            try:
                # Try various date formats
                for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%m/%d/%Y"]:
                    try:
                        return datetime.strptime(date_value, fmt)
                    except ValueError:
                        continue
                # If no format works, return None
                return None
            except Exception:
                return None
        
        return None


def get_invoice_service(db: Session) -> InvoiceService:
    """Get Access Point Provider invoice service instance."""
    return InvoiceService(db)