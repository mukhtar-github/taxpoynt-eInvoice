"""
POS Transaction Service for converting transactions to invoices.

This service handles:
- Converting POS transactions to FIRS-compliant invoices
- Background task coordination for invoice generation
- Error handling and retry mechanisms
- Integration with existing invoice service
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.pos_connection import POSTransaction, POSConnection
from app.models.invoice import Invoice
from app.models.user import User
from app.services.invoice_service import InvoiceService
from app.schemas.pos import POSTransactionCreate
from app.utils.logger import get_logger

logger = get_logger(__name__)


class POSTransactionService:
    """Service for handling POS transactions and invoice conversion."""
    
    def __init__(self, db: Session):
        """
        Initialize POS transaction service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.invoice_service = InvoiceService(db)
    
    async def transaction_to_invoice(
        self, 
        transaction: POSTransaction,
        created_by: Optional[User] = None
    ) -> Invoice:
        """
        Convert a POS transaction to an invoice.
        
        Args:
            transaction: POSTransaction object
            created_by: User creating the invoice (optional)
            
        Returns:
            Created Invoice object
            
        Raises:
            ValueError: If transaction data is invalid
            Exception: If invoice creation fails
        """
        try:
            logger.info(f"Converting POS transaction {transaction.external_transaction_id} to invoice")
            
            # Validate transaction has required data
            if not transaction.transaction_amount or transaction.transaction_amount <= 0:
                raise ValueError(f"Invalid transaction amount: {transaction.transaction_amount}")
            
            if not transaction.external_transaction_id:
                raise ValueError("Transaction missing external_transaction_id")
            
            # Get connection details for platform-specific processing
            connection = transaction.connection
            if not connection:
                raise ValueError(f"Transaction {transaction.id} has no associated connection")
            
            # Extract transaction data
            invoice_data = self._transform_transaction_to_invoice_data(transaction, connection)
            
            # Get user context - use connection owner if no user provided
            if not created_by:
                created_by = connection.user
            
            # Create invoice using existing invoice service
            invoice = self.invoice_service.create_invoice_from_pos_transaction(
                transaction=transaction,
                invoice_data=invoice_data,
                created_by=created_by
            )
            
            logger.info(f"Successfully converted transaction {transaction.external_transaction_id} to invoice {invoice.invoice_number}")
            return invoice
            
        except Exception as e:
            # Log error and add to transaction processing errors
            error_data = {
                "error_message": str(e),
                "error_type": e.__class__.__name__,
                "timestamp": datetime.now().isoformat(),
                "function": "transaction_to_invoice"
            }
            
            # Update transaction with error
            if transaction.processing_errors:
                transaction.processing_errors.append(error_data)
            else:
                transaction.processing_errors = [error_data]
            
            transaction.updated_at = datetime.now()
            self.db.commit()
            
            logger.error(f"Failed to convert transaction {transaction.external_transaction_id} to invoice: {str(e)}")
            raise
    
    def _transform_transaction_to_invoice_data(
        self, 
        transaction: POSTransaction, 
        connection: POSConnection
    ) -> Dict[str, Any]:
        """
        Transform POS transaction data to invoice format.
        
        Args:
            transaction: POS transaction object
            connection: POS connection object
            
        Returns:
            Dict containing invoice data
        """
        # Generate invoice number with POS prefix
        invoice_number = f"POS-{transaction.external_transaction_id}"
        
        # Extract transaction date
        transaction_date = transaction.transaction_timestamp or datetime.now()
        
        # Calculate amounts
        subtotal = transaction.transaction_amount or Decimal('0')
        tax_amount = transaction.tax_amount or Decimal('0')
        
        # Transform line items from transaction items
        line_items = self._transform_line_items(transaction.items or [])
        
        # Extract customer data
        customer_data = self._extract_customer_data(transaction.customer_data or {})
        
        # Determine currency from connection settings or transaction
        currency = self._get_transaction_currency(transaction, connection)
        
        # Build invoice data structure
        invoice_data = {
            "invoice_number": invoice_number,
            "transaction_date": transaction_date.isoformat() if isinstance(transaction_date, datetime) else str(transaction_date),
            "amount": float(subtotal),
            "tax_amount": float(tax_amount),
            "currency": currency,
            "customer": customer_data,
            "line_items": line_items,
            "metadata": {
                "pos_platform": connection.pos_type.value,
                "location_name": connection.location_name,
                "external_transaction_id": transaction.external_transaction_id,
                "transaction_timestamp": transaction_date.isoformat() if isinstance(transaction_date, datetime) else str(transaction_date),
                "connection_id": str(connection.id),
                "original_transaction_data": transaction.transaction_metadata
            }
        }
        
        return invoice_data
    
    def _transform_line_items(self, items: list) -> list:
        """
        Transform transaction items to invoice line items.
        
        Args:
            items: List of transaction items
            
        Returns:
            List of invoice line items
        """
        if not items:
            return []
        
        line_items = []
        
        for item in items:
            if not isinstance(item, dict):
                continue
            
            line_item = {
                "description": item.get("name", item.get("description", "Unknown Item")),
                "quantity": item.get("quantity", 1),
                "unit_price": item.get("price", item.get("unit_price", 0)),
                "total_amount": item.get("total", item.get("amount", 0)),
                "tax_amount": item.get("tax", 0),
                "sku": item.get("sku", item.get("id", "")),
                "category": item.get("category", ""),
                "metadata": {
                    "original_item_data": item
                }
            }
            
            # Calculate total if not provided
            if not line_item["total_amount"]:
                line_item["total_amount"] = line_item["quantity"] * line_item["unit_price"]
            
            line_items.append(line_item)
        
        return line_items
    
    def _extract_customer_data(self, customer_data: dict) -> dict:
        """
        Extract and normalize customer data.
        
        Args:
            customer_data: Raw customer data from transaction
            
        Returns:
            Normalized customer data dict
        """
        if not customer_data:
            return {"name": "Walk-in Customer", "type": "individual"}
        
        # Handle different customer data formats
        customer = {
            "name": customer_data.get("name", customer_data.get("customer_name", "Walk-in Customer")),
            "email": customer_data.get("email", customer_data.get("email_address", "")),
            "phone": customer_data.get("phone", customer_data.get("phone_number", "")),
            "type": customer_data.get("type", "individual"),
            "address": self._extract_address_data(customer_data)
        }
        
        # Handle business customers
        if customer_data.get("company_name") or customer_data.get("business_name"):
            customer["name"] = customer_data.get("company_name", customer_data.get("business_name"))
            customer["type"] = "business"
            customer["tax_id"] = customer_data.get("tax_id", customer_data.get("tin", ""))
        
        return customer
    
    def _extract_address_data(self, customer_data: dict) -> dict:
        """
        Extract address data from customer information.
        
        Args:
            customer_data: Customer data containing address information
            
        Returns:
            Normalized address dict
        """
        address_data = customer_data.get("address", {})
        
        if not address_data and any(key in customer_data for key in ["street", "city", "state", "country"]):
            # Address data is in root level
            address_data = {
                "street": customer_data.get("street", ""),
                "city": customer_data.get("city", ""),
                "state": customer_data.get("state", ""),
                "postal_code": customer_data.get("postal_code", customer_data.get("zip", "")),
                "country": customer_data.get("country", "NG")
            }
        
        return address_data or {}
    
    def _get_transaction_currency(self, transaction: POSTransaction, connection: POSConnection) -> str:
        """
        Determine transaction currency.
        
        Args:
            transaction: POS transaction
            connection: POS connection
            
        Returns:
            Currency code (default: NGN)
        """
        # Check transaction metadata first
        if transaction.transaction_metadata:
            currency = transaction.transaction_metadata.get("currency")
            if currency:
                return currency
        
        # Check connection settings
        if connection.connection_settings:
            currency = connection.connection_settings.get("default_currency")
            if currency:
                return currency
        
        # Default to NGN for FIRS compliance
        return "NGN"
    
    async def create_transaction_from_webhook(
        self,
        webhook_data: Dict[str, Any],
        connection: POSConnection
    ) -> POSTransaction:
        """
        Create a POS transaction from webhook data.
        
        Args:
            webhook_data: Webhook payload data
            connection: POS connection
            
        Returns:
            Created POSTransaction object
        """
        try:
            # Extract transaction data from webhook payload
            transaction_data = self._extract_transaction_from_webhook(webhook_data, connection.pos_type.value)
            
            # Check if transaction already exists
            existing = self.db.query(POSTransaction).filter(
                POSTransaction.connection_id == connection.id,
                POSTransaction.external_transaction_id == transaction_data["external_transaction_id"]
            ).first()
            
            if existing:
                logger.info(f"Transaction {transaction_data['external_transaction_id']} already exists")
                return existing
            
            # Create new transaction
            transaction = POSTransaction(
                connection_id=connection.id,
                external_transaction_id=transaction_data["external_transaction_id"],
                transaction_amount=Decimal(str(transaction_data["amount"])),
                tax_amount=Decimal(str(transaction_data.get("tax_amount", 0))),
                items=transaction_data.get("items", []),
                customer_data=transaction_data.get("customer_data", {}),
                transaction_timestamp=transaction_data["timestamp"],
                transaction_metadata=transaction_data.get("metadata", {}),
                invoice_generated=False,
                invoice_transmitted=False
            )
            
            self.db.add(transaction)
            self.db.commit()
            self.db.refresh(transaction)
            
            logger.info(f"Created transaction {transaction.external_transaction_id} from webhook")
            return transaction
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create transaction from webhook: {str(e)}")
            raise
    
    def _extract_transaction_from_webhook(
        self,
        webhook_data: Dict[str, Any],
        platform: str
    ) -> Dict[str, Any]:
        """
        Extract transaction data from platform-specific webhook.
        
        Args:
            webhook_data: Raw webhook data
            platform: POS platform name
            
        Returns:
            Normalized transaction data
        """
        # Platform-specific extraction logic
        if platform.lower() == "square":
            return self._extract_square_transaction(webhook_data)
        elif platform.lower() == "toast":
            return self._extract_toast_transaction(webhook_data)
        else:
            # Generic extraction
            return self._extract_generic_transaction(webhook_data)
    
    def _extract_square_transaction(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract transaction data from Square webhook."""
        data = webhook_data.get("data", {})
        payment = data.get("object", {}).get("payment", {})
        
        return {
            "external_transaction_id": payment.get("id"),
            "amount": payment.get("amount_money", {}).get("amount", 0) / 100,  # Convert from cents
            "tax_amount": payment.get("total_tax_money", {}).get("amount", 0) / 100,
            "timestamp": datetime.fromisoformat(payment.get("created_at", datetime.now().isoformat())),
            "items": payment.get("line_items", []),
            "customer_data": payment.get("buyer_email_address"),
            "metadata": webhook_data
        }
    
    def _extract_toast_transaction(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract transaction data from Toast webhook."""
        # Toast-specific extraction logic would go here
        return self._extract_generic_transaction(webhook_data)
    
    def _extract_generic_transaction(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract transaction data from generic webhook."""
        return {
            "external_transaction_id": webhook_data.get("transaction_id", webhook_data.get("id")),
            "amount": webhook_data.get("amount", 0),
            "tax_amount": webhook_data.get("tax_amount", 0),
            "timestamp": datetime.now(),
            "items": webhook_data.get("items", []),
            "customer_data": webhook_data.get("customer", {}),
            "metadata": webhook_data
        }
    
    async def retry_failed_invoice_generation(self, transaction_id: UUID) -> bool:
        """
        Retry invoice generation for a failed transaction.
        
        Args:
            transaction_id: Transaction UUID to retry
            
        Returns:
            True if retry was successful, False otherwise
        """
        try:
            transaction = self.db.query(POSTransaction).filter(POSTransaction.id == transaction_id).first()
            
            if not transaction:
                logger.error(f"Transaction {transaction_id} not found for retry")
                return False
            
            if transaction.invoice_generated:
                logger.warning(f"Transaction {transaction_id} already has invoice generated")
                return True
            
            # Attempt to generate invoice
            invoice = await self.transaction_to_invoice(transaction)
            
            logger.info(f"Successfully retried invoice generation for transaction {transaction_id}")
            return True
            
        except Exception as e:
            logger.error(f"Retry failed for transaction {transaction_id}: {str(e)}")
            return False


def get_pos_transaction_service(db: Session) -> POSTransactionService:
    """Get POS transaction service instance."""
    return POSTransactionService(db)