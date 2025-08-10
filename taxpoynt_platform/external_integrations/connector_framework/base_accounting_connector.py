"""
Base Accounting Connector
Base class for all accounting software integrations in the TaxPoynt eInvoice platform.
Provides standardized interface for accounting system operations and FIRS compliance.
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

from .base_connector import BaseConnector, ConnectionStatus

logger = logging.getLogger(__name__)


class AccountingTransactionType(Enum):
    """Types of accounting transactions."""
    INVOICE = "invoice"
    BILL = "bill"
    PAYMENT = "payment"
    CREDIT_NOTE = "credit_note"
    DEBIT_NOTE = "debit_note"
    JOURNAL_ENTRY = "journal_entry"
    EXPENSE = "expense"
    PURCHASE_ORDER = "purchase_order"
    SALES_ORDER = "sales_order"
    RECEIPT = "receipt"


class AccountingDocumentStatus(Enum):
    """Status of accounting documents."""
    DRAFT = "draft"
    PENDING = "pending"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    VOID = "void"
    DELETED = "deleted"
    PARTIALLY_PAID = "partially_paid"


@dataclass
class AccountingContact:
    """Represents a contact (customer/vendor) in accounting system."""
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[Dict[str, str]] = None
    tax_number: Optional[str] = None
    contact_type: str = "customer"  # customer, vendor, employee
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class AccountingTransaction:
    """Represents a financial transaction in accounting system."""
    id: str
    transaction_type: AccountingTransactionType
    number: Optional[str] = None
    date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    contact: Optional[AccountingContact] = None
    line_items: List[Dict[str, Any]] = None
    subtotal: float = 0.0
    tax_total: float = 0.0
    total: float = 0.0
    currency: str = "NGN"
    status: Optional[AccountingDocumentStatus] = None
    reference: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    custom_fields: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.line_items is None:
            self.line_items = []


@dataclass
class AccountingAccount:
    """Represents a chart of accounts entry."""
    id: str
    code: Optional[str] = None
    name: str = ""
    account_type: Optional[str] = None
    category: Optional[str] = None
    parent_id: Optional[str] = None
    balance: float = 0.0
    currency: str = "NGN"
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class AccountingWebhookEvent:
    """Represents a webhook event from accounting systems."""
    event_type: str
    resource_type: str
    resource_id: str
    data: Dict[str, Any]
    timestamp: datetime
    signature: Optional[str] = None


class BaseAccountingConnector(BaseConnector):
    """
    Base class for all accounting software connectors.
    
    Provides standardized interface for connecting to accounting systems
    and extracting financial data for FIRS e-invoicing compliance.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize accounting connector.
        
        Args:
            config: Configuration dictionary for the accounting system
        """
        super().__init__(config)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to accounting system.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Disconnect from accounting system.
        
        Returns:
            True if disconnection successful
        """
        pass
    
    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to accounting system.
        
        Returns:
            Dictionary containing connection test results
        """
        pass
    
    # Core Data Retrieval Methods
    
    @abstractmethod
    async def get_invoices(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        invoice_id: Optional[str] = None,
        contact_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[AccountingTransaction]:
        """
        Retrieve invoices from accounting system.
        
        Args:
            date_from: Start date for filtering
            date_to: End date for filtering
            invoice_id: Specific invoice ID
            contact_id: Customer ID filter
            status: Invoice status filter
            limit: Maximum number of invoices to retrieve
            
        Returns:
            List of invoice transactions
        """
        pass
    
    @abstractmethod
    async def get_invoice_by_id(self, invoice_id: str) -> Optional[AccountingTransaction]:
        """
        Retrieve a specific invoice by ID.
        
        Args:
            invoice_id: Invoice ID
            
        Returns:
            Invoice transaction or None if not found
        """
        pass
    
    @abstractmethod
    async def get_bills(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        bill_id: Optional[str] = None,
        vendor_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[AccountingTransaction]:
        """
        Retrieve bills/purchase invoices from accounting system.
        
        Args:
            date_from: Start date for filtering
            date_to: End date for filtering
            bill_id: Specific bill ID
            vendor_id: Vendor ID filter
            status: Bill status filter
            limit: Maximum number of bills to retrieve
            
        Returns:
            List of bill transactions
        """
        pass
    
    @abstractmethod
    async def get_contacts(
        self,
        contact_id: Optional[str] = None,
        contact_type: Optional[str] = None,
        limit: int = 100
    ) -> List[AccountingContact]:
        """
        Retrieve contacts (customers/vendors) from accounting system.
        
        Args:
            contact_id: Specific contact ID
            contact_type: Type of contact ('customer', 'vendor', etc.)
            limit: Maximum number of contacts to retrieve
            
        Returns:
            List of contacts
        """
        pass
    
    @abstractmethod
    async def get_chart_of_accounts(self) -> List[AccountingAccount]:
        """
        Retrieve chart of accounts from accounting system.
        
        Returns:
            List of accounting accounts
        """
        pass
    
    # Transaction Methods
    
    @abstractmethod
    async def create_invoice(self, invoice_data: Dict[str, Any]) -> AccountingTransaction:
        """
        Create a new invoice in the accounting system.
        
        Args:
            invoice_data: Invoice data dictionary
            
        Returns:
            Created invoice transaction
        """
        pass
    
    @abstractmethod
    async def update_invoice(self, invoice_id: str, update_data: Dict[str, Any]) -> AccountingTransaction:
        """
        Update an existing invoice in the accounting system.
        
        Args:
            invoice_id: Invoice ID to update
            update_data: Updated invoice data
            
        Returns:
            Updated invoice transaction
        """
        pass
    
    # UBL/FIRS Transformation Methods
    
    @abstractmethod
    async def transform_invoice_to_ubl(
        self,
        invoice: AccountingTransaction
    ) -> Dict[str, Any]:
        """
        Transform an accounting invoice to FIRS-compliant UBL BIS 3.0 format.
        
        Args:
            invoice: Accounting invoice transaction
            
        Returns:
            UBL BIS 3.0 compliant invoice dictionary
        """
        pass
    
    @abstractmethod
    async def transform_bill_to_ubl(
        self,
        bill: AccountingTransaction
    ) -> Dict[str, Any]:
        """
        Transform an accounting bill to FIRS-compliant UBL BIS 3.0 format.
        
        Args:
            bill: Accounting bill transaction
            
        Returns:
            UBL BIS 3.0 compliant invoice dictionary
        """
        pass
    
    # Webhook Methods
    
    @abstractmethod
    async def process_webhook(
        self,
        event_type: str,
        payload: Dict[str, Any],
        headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Process incoming webhook from accounting system.
        
        Args:
            event_type: Type of webhook event
            payload: Webhook payload data
            headers: HTTP headers from webhook request
            
        Returns:
            Processing result dictionary
        """
        pass
    
    # Analytics and Reporting
    
    async def get_financial_summary(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get financial summary from accounting system.
        
        Args:
            date_from: Start date for summary
            date_to: End date for summary
            
        Returns:
            Financial summary data
        """
        try:
            # Default to current month if no dates provided
            if not date_to:
                date_to = datetime.now()
            if not date_from:
                date_from = date_to.replace(day=1)
            
            # Get invoices and bills for the period
            invoices = await self.get_invoices(date_from=date_from, date_to=date_to, limit=1000)
            bills = await self.get_bills(date_from=date_from, date_to=date_to, limit=1000)
            
            # Calculate totals
            total_sales = sum(inv.total for inv in invoices if inv.status != AccountingDocumentStatus.VOID)
            total_expenses = sum(bill.total for bill in bills if bill.status != AccountingDocumentStatus.VOID)
            net_income = total_sales - total_expenses
            
            # Calculate tax totals
            total_sales_tax = sum(inv.tax_total for inv in invoices if inv.status != AccountingDocumentStatus.VOID)
            total_input_tax = sum(bill.tax_total for bill in bills if bill.status != AccountingDocumentStatus.VOID)
            
            return {
                'period': {
                    'from': date_from.isoformat(),
                    'to': date_to.isoformat()
                },
                'summary': {
                    'total_sales': total_sales,
                    'total_expenses': total_expenses,
                    'net_income': net_income,
                    'total_sales_tax': total_sales_tax,
                    'total_input_tax': total_input_tax,
                    'net_tax_liability': total_sales_tax - total_input_tax
                },
                'transaction_counts': {
                    'invoices': len(invoices),
                    'bills': len(bills)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get financial summary: {e}")
            raise
    
    async def get_tax_report(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate tax report for FIRS compliance.
        
        Args:
            date_from: Start date for tax report
            date_to: End date for tax report
            
        Returns:
            Tax report data
        """
        try:
            # Get financial summary
            summary = await self.get_financial_summary(date_from, date_to)
            
            # Get detailed transactions
            invoices = await self.get_invoices(date_from=date_from, date_to=date_to, limit=1000)
            bills = await self.get_bills(date_from=date_from, date_to=date_to, limit=1000)
            
            # Calculate VAT breakdown
            vat_breakdown = {
                'output_vat': {},  # VAT on sales
                'input_vat': {}    # VAT on purchases
            }
            
            # Process output VAT (from sales)
            for invoice in invoices:
                if invoice.status != AccountingDocumentStatus.VOID and invoice.tax_total > 0:
                    rate = round((invoice.tax_total / invoice.subtotal) * 100, 1) if invoice.subtotal > 0 else 0
                    rate_key = f"{rate}%"
                    
                    if rate_key not in vat_breakdown['output_vat']:
                        vat_breakdown['output_vat'][rate_key] = {
                            'taxable_amount': 0,
                            'tax_amount': 0,
                            'transaction_count': 0
                        }
                    
                    vat_breakdown['output_vat'][rate_key]['taxable_amount'] += invoice.subtotal
                    vat_breakdown['output_vat'][rate_key]['tax_amount'] += invoice.tax_total
                    vat_breakdown['output_vat'][rate_key]['transaction_count'] += 1
            
            # Process input VAT (from purchases)
            for bill in bills:
                if bill.status != AccountingDocumentStatus.VOID and bill.tax_total > 0:
                    rate = round((bill.tax_total / bill.subtotal) * 100, 1) if bill.subtotal > 0 else 0
                    rate_key = f"{rate}%"
                    
                    if rate_key not in vat_breakdown['input_vat']:
                        vat_breakdown['input_vat'][rate_key] = {
                            'taxable_amount': 0,
                            'tax_amount': 0,
                            'transaction_count': 0
                        }
                    
                    vat_breakdown['input_vat'][rate_key]['taxable_amount'] += bill.subtotal
                    vat_breakdown['input_vat'][rate_key]['tax_amount'] += bill.tax_total
                    vat_breakdown['input_vat'][rate_key]['transaction_count'] += 1
            
            return {
                **summary,
                'vat_breakdown': vat_breakdown,
                'compliance_status': {
                    'firs_compliant': True,  # Assume compliant for now
                    'ubl_format_ready': True,
                    'e_invoice_eligible': len(invoices) > 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate tax report: {e}")
            raise
    
    # Health Check
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on accounting system connection.
        
        Returns:
            Health check results
        """
        try:
            start_time = datetime.now()
            
            # Test basic connection
            connection_test = await self.test_connection()
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            return {
                'status': 'healthy' if connection_test.get('success', False) else 'unhealthy',
                'connection_test': connection_test,
                'response_time_ms': response_time,
                'timestamp': start_time.isoformat(),
                'connector_type': 'accounting'
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'connector_type': 'accounting'
            }


# Exception Classes for Accounting Connectors

class AccountingConnectionError(Exception):
    """Raised when accounting system connection fails."""
    pass


class AccountingAuthenticationError(Exception):
    """Raised when accounting system authentication fails."""
    pass


class AccountingDataError(Exception):
    """Raised when accounting system data operations fail."""
    pass


class AccountingValidationError(Exception):
    """Raised when accounting system data validation fails."""
    pass


class AccountingTransformationError(Exception):
    """Raised when UBL transformation fails."""
    pass