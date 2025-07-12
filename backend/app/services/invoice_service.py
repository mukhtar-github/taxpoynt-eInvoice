"""
Invoice service for creating and managing invoices from CRM/POS integrations.

This service handles:
- Creating invoices from CRM deals and POS transactions
- Linking invoices to IRN generation
- Invoice validation and processing
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
    """Service for managing invoice creation and processing."""
    
    def __init__(self, db: Session):
        self.db = db
        
    def create_invoice_from_crm_deal(
        self,
        deal: CRMDeal,
        invoice_data: Dict[str, Any],
        created_by: User
    ) -> Invoice:
        """
        Create an invoice from a CRM deal.
        
        Args:
            deal: CRM deal object
            invoice_data: Transformed invoice data from the connector
            created_by: User creating the invoice
            
        Returns:
            Created Invoice object
        """
        try:
            # Parse invoice data
            invoice_number = invoice_data.get("invoice_number", f"CRM-{deal.external_deal_id}")
            invoice_date = self._parse_date(invoice_data.get("invoice_date"))
            due_date = self._parse_date(invoice_data.get("due_date"))
            
            # Calculate amounts
            subtotal = Decimal(str(invoice_data.get("amount", 0)))
            tax_amount = Decimal(str(invoice_data.get("tax_amount", 0)))
            total_amount = subtotal + tax_amount
            
            # Create invoice
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
                    "original_data": invoice_data.get("metadata", {})
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
            
            logger.info(f"Created invoice {invoice.invoice_number} from CRM deal {deal.external_deal_id}")
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
        Create an invoice from a POS transaction.
        
        Args:
            transaction: POS transaction object
            invoice_data: Transformed invoice data from the connector
            created_by: User creating the invoice
            
        Returns:
            Created Invoice object
        """
        try:
            # Parse invoice data
            invoice_number = invoice_data.get("invoice_number", f"POS-{transaction.external_transaction_id}")
            invoice_date = self._parse_date(invoice_data.get("transaction_date"))
            
            # Calculate amounts
            subtotal = Decimal(str(invoice_data.get("amount", 0)))
            tax_amount = Decimal(str(invoice_data.get("tax_amount", 0)))
            total_amount = subtotal + tax_amount
            
            # Create invoice
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
                    "original_data": invoice_data.get("metadata", {})
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
            
            logger.info(f"Created invoice {invoice.invoice_number} from POS transaction {transaction.external_transaction_id}")
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
        Create a manual invoice.
        
        Args:
            invoice_data: Invoice data
            created_by: User creating the invoice
            
        Returns:
            Created Invoice object
        """
        try:
            # Parse invoice data
            invoice_number = invoice_data.get("invoice_number")
            if not invoice_number:
                # Generate invoice number
                invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{datetime.now().timestamp():.0f}"
            
            invoice_date = self._parse_date(invoice_data.get("invoice_date"))
            due_date = self._parse_date(invoice_data.get("due_date"))
            
            # Calculate amounts
            subtotal = Decimal(str(invoice_data.get("subtotal", 0)))
            tax_amount = Decimal(str(invoice_data.get("tax_amount", 0)))
            total_amount = Decimal(str(invoice_data.get("total_amount", subtotal + tax_amount)))
            
            # Create invoice
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
                invoice_metadata=invoice_data.get("metadata", {})
            )
            
            # Save to database
            self.db.add(invoice)
            self.db.commit()
            self.db.refresh(invoice)
            
            logger.info(f"Created manual invoice {invoice.invoice_number}")
            return invoice
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create manual invoice: {str(e)}")
            raise
    
    def generate_irn_for_invoice(self, invoice: Invoice) -> str:
        """
        Generate IRN for an invoice.
        
        Args:
            invoice: Invoice to generate IRN for
            
        Returns:
            Generated IRN value
        """
        if invoice.irn_generated:
            logger.warning(f"IRN already generated for invoice {invoice.invoice_number}")
            return invoice.irn_value
        
        try:
            # Prepare IRN data
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
            
            # Update invoice with IRN
            invoice.mark_irn_generated(irn_record.irn)
            self.db.commit()
            
            logger.info(f"Generated IRN {irn_record.irn} for invoice {invoice.invoice_number}")
            return irn_record.irn
            
        except Exception as e:
            logger.error(f"Failed to generate IRN for invoice {invoice.invoice_number}: {str(e)}")
            raise
    
    def _parse_date(self, date_value: Any) -> Optional[datetime]:
        """Parse date from various formats."""
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
    """Get invoice service instance."""
    return InvoiceService(db)