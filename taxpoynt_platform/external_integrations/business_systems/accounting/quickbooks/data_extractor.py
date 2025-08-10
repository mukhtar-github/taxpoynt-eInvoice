"""
QuickBooks Accounting Data Extractor
Extracts and processes financial data from QuickBooks Online API.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from decimal import Decimal

from .rest_client import QuickBooksRestClient
from .exceptions import QuickBooksDataError, QuickBooksValidationError
from ....connector_framework.base_accounting_connector import (
    AccountingTransaction,
    AccountingContact,
    AccountingAccount,
    AccountingTransactionType,
    AccountingDocumentStatus
)


class QuickBooksDataExtractor:
    """
    Extracts financial data from QuickBooks Online.
    
    Handles:
    - Invoice and transaction data extraction
    - Customer and vendor information
    - Chart of accounts
    - Data validation and normalization
    """
    
    def __init__(self, rest_client: QuickBooksRestClient):
        """
        Initialize data extractor.
        
        Args:
            rest_client: QuickBooks REST client
        """
        self.client = rest_client
        self.logger = logging.getLogger(__name__)
        
        # Cache for frequently accessed data
        self._customers_cache: Optional[Dict[str, Dict[str, Any]]] = None
        self._items_cache: Optional[Dict[str, Dict[str, Any]]] = None
        self._accounts_cache: Optional[Dict[str, Dict[str, Any]]] = None
        self._cache_ttl = timedelta(minutes=15)
        self._cache_timestamp: Optional[datetime] = None
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if not self._cache_timestamp:
            return False
        return datetime.now() - self._cache_timestamp < self._cache_ttl
    
    async def _refresh_cache(self) -> None:
        """Refresh data cache."""
        self.logger.info("Refreshing QuickBooks data cache")
        
        # Fetch core data in parallel
        customers_task = asyncio.create_task(self.client.get_customers())
        items_task = asyncio.create_task(self.client.get_items())
        accounts_task = asyncio.create_task(self._get_accounts())
        
        customers, items, accounts = await asyncio.gather(
            customers_task, items_task, accounts_task,
            return_exceptions=True
        )
        
        # Handle results
        self._customers_cache = {
            cust['Id']: cust for cust in customers
        } if not isinstance(customers, Exception) else {}
        
        self._items_cache = {
            item['Id']: item for item in items
        } if not isinstance(items, Exception) else {}
        
        self._accounts_cache = {
            acc['Id']: acc for acc in accounts
        } if not isinstance(accounts, Exception) else {}
        
        self._cache_timestamp = datetime.now()
        self.logger.info(f"Cache refreshed: {len(self._customers_cache)} customers, "
                        f"{len(self._items_cache)} items, {len(self._accounts_cache)} accounts")
    
    async def _get_accounts(self) -> List[Dict[str, Any]]:
        """Get chart of accounts."""
        result = await self.client.query("SELECT * FROM Account WHERE Active = true")
        return result.get('QueryResponse', {}).get('Account', [])
    
    async def _ensure_cache(self) -> None:
        """Ensure cache is available and valid."""
        if not self._is_cache_valid():
            await self._refresh_cache()
    
    def _normalize_decimal(self, value: Any) -> Decimal:
        """Convert value to Decimal, handling various input types."""
        if value is None:
            return Decimal('0')
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        if isinstance(value, str):
            try:
                return Decimal(value)
            except:
                return Decimal('0')
        return Decimal('0')
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse QuickBooks date string."""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            try:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                return None
    
    def _map_transaction_type(self, qb_type: str) -> AccountingTransactionType:
        """Map QuickBooks transaction type to standard type."""
        type_mapping = {
            'Invoice': AccountingTransactionType.INVOICE,
            'CreditMemo': AccountingTransactionType.CREDIT_NOTE,
            'Payment': AccountingTransactionType.PAYMENT,
            'Bill': AccountingTransactionType.BILL,
            'BillPayment': AccountingTransactionType.BILL_PAYMENT,
            'Estimate': AccountingTransactionType.QUOTE,
            'SalesReceipt': AccountingTransactionType.RECEIPT,
            'Purchase': AccountingTransactionType.EXPENSE,
            'JournalEntry': AccountingTransactionType.JOURNAL_ENTRY
        }
        return type_mapping.get(qb_type, AccountingTransactionType.OTHER)
    
    def _map_document_status(self, qb_status: Optional[str]) -> AccountingDocumentStatus:
        """Map QuickBooks document status to standard status."""
        if not qb_status:
            return AccountingDocumentStatus.DRAFT
        
        status_mapping = {
            'Draft': AccountingDocumentStatus.DRAFT,
            'Pending': AccountingDocumentStatus.PENDING,
            'Sent': AccountingDocumentStatus.SENT,
            'Paid': AccountingDocumentStatus.PAID,
            'Partial': AccountingDocumentStatus.PARTIALLY_PAID,
            'Overdue': AccountingDocumentStatus.OVERDUE,
            'Void': AccountingDocumentStatus.VOID,
            'Deleted': AccountingDocumentStatus.DELETED
        }
        return status_mapping.get(qb_status, AccountingDocumentStatus.DRAFT)
    
    async def extract_invoices(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        customer_ids: Optional[Set[str]] = None
    ) -> List[AccountingTransaction]:
        """
        Extract invoices from QuickBooks.
        
        Args:
            start_date: Filter invoices from this date
            end_date: Filter invoices until this date
            customer_ids: Filter by specific customer IDs
            
        Returns:
            List of normalized invoice transactions
        """
        await self._ensure_cache()
        
        # Build query
        query = "SELECT * FROM Invoice"
        conditions = []
        
        if start_date:
            conditions.append(f"TxnDate >= '{start_date.strftime('%Y-%m-%d')}'")
        if end_date:
            conditions.append(f"TxnDate <= '{end_date.strftime('%Y-%m-%d')}'")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY TxnDate DESC"
        
        try:
            result = await self.client.query(query)
            invoices_data = result.get('QueryResponse', {}).get('Invoice', [])
            
            # Filter by customer IDs if specified
            if customer_ids:
                invoices_data = [
                    inv for inv in invoices_data
                    if inv.get('CustomerRef', {}).get('value') in customer_ids
                ]
            
            # Convert to normalized format
            transactions = []
            for invoice_data in invoices_data:
                try:
                    transaction = await self._convert_invoice_to_transaction(invoice_data)
                    transactions.append(transaction)
                except Exception as e:
                    self.logger.warning(f"Failed to convert invoice {invoice_data.get('Id')}: {str(e)}")
                    continue
            
            self.logger.info(f"Extracted {len(transactions)} invoices from QuickBooks")
            return transactions
            
        except Exception as e:
            raise QuickBooksDataError(f"Failed to extract invoices: {str(e)}")
    
    async def _convert_invoice_to_transaction(self, invoice_data: Dict[str, Any]) -> AccountingTransaction:
        """Convert QuickBooks invoice to normalized transaction."""
        # Basic invoice information
        invoice_id = invoice_data.get('Id')
        doc_number = invoice_data.get('DocNumber', invoice_id)
        
        # Customer information
        customer_ref = invoice_data.get('CustomerRef', {})
        customer_id = customer_ref.get('value')
        customer_name = customer_ref.get('name', '')
        
        # Get detailed customer info from cache
        customer_data = self._customers_cache.get(customer_id, {}) if customer_id else {}
        
        # Dates
        txn_date = self._parse_date(invoice_data.get('TxnDate'))
        due_date = self._parse_date(invoice_data.get('DueDate'))
        
        # Financial amounts
        total_amount = self._normalize_decimal(invoice_data.get('TotalAmt', 0))
        balance = self._normalize_decimal(invoice_data.get('Balance', 0))
        
        # Status determination
        status = AccountingDocumentStatus.DRAFT
        if balance == 0 and total_amount > 0:
            status = AccountingDocumentStatus.PAID
        elif balance > 0 and balance < total_amount:
            status = AccountingDocumentStatus.PARTIALLY_PAID
        elif due_date and due_date < datetime.now() and balance > 0:
            status = AccountingDocumentStatus.OVERDUE
        elif invoice_data.get('EmailStatus') == 'EmailSent':
            status = AccountingDocumentStatus.SENT
        
        # Line items
        line_items = []
        for line in invoice_data.get('Line', []):
            if line.get('DetailType') == 'SalesItemLineDetail':
                detail = line.get('SalesItemLineDetail', {})
                item_ref = detail.get('ItemRef', {})
                item_id = item_ref.get('value')
                item_data = self._items_cache.get(item_id, {}) if item_id else {}
                
                line_item = {
                    'id': line.get('Id'),
                    'item_id': item_id,
                    'item_name': item_ref.get('name', item_data.get('Name', '')),
                    'description': line.get('Description', ''),
                    'quantity': self._normalize_decimal(detail.get('Qty', 1)),
                    'unit_price': self._normalize_decimal(detail.get('UnitPrice', 0)),
                    'amount': self._normalize_decimal(line.get('Amount', 0)),
                    'tax_amount': Decimal('0')  # Tax handled separately in QuickBooks
                }
                line_items.append(line_item)
        
        # Tax information
        tax_amount = Decimal('0')
        tax_lines = [line for line in invoice_data.get('Line', []) if line.get('DetailType') == 'TaxLineDetail']
        for tax_line in tax_lines:
            tax_amount += self._normalize_decimal(tax_line.get('Amount', 0))
        
        # Create normalized transaction
        return AccountingTransaction(
            id=invoice_id,
            document_number=doc_number,
            transaction_type=AccountingTransactionType.INVOICE,
            status=status,
            date=txn_date or datetime.now(),
            due_date=due_date,
            contact=AccountingContact(
                id=customer_id or '',
                name=customer_name,
                email=customer_data.get('PrimaryEmailAddr', {}).get('Address', ''),
                phone=customer_data.get('PrimaryPhone', {}).get('FreeFormNumber', ''),
                address={
                    'line1': customer_data.get('BillAddr', {}).get('Line1', ''),
                    'city': customer_data.get('BillAddr', {}).get('City', ''),
                    'state': customer_data.get('BillAddr', {}).get('CountrySubDivisionCode', ''),
                    'postal_code': customer_data.get('BillAddr', {}).get('PostalCode', ''),
                    'country': customer_data.get('BillAddr', {}).get('Country', '')
                },
                tax_number=customer_data.get('ResaleNum', '')
            ),
            currency_code=invoice_data.get('CurrencyRef', {}).get('value', 'USD'),
            subtotal_amount=total_amount - tax_amount,
            tax_amount=tax_amount,
            total_amount=total_amount,
            paid_amount=total_amount - balance,
            balance_amount=balance,
            line_items=line_items,
            notes=invoice_data.get('PrivateNote', ''),
            reference=invoice_data.get('CustomerMemo', {}).get('value', ''),
            metadata={
                'quickbooks_id': invoice_id,
                'sync_token': invoice_data.get('SyncToken'),
                'created_time': invoice_data.get('MetaData', {}).get('CreateTime'),
                'last_updated_time': invoice_data.get('MetaData', {}).get('LastUpdatedTime'),
                'custom_fields': invoice_data.get('CustomField', [])
            }
        )
    
    async def extract_customers(
        self,
        active_only: bool = True,
        modified_since: Optional[datetime] = None
    ) -> List[AccountingContact]:
        """
        Extract customers from QuickBooks.
        
        Args:
            active_only: Only return active customers
            modified_since: Only return customers modified since this date
            
        Returns:
            List of normalized customer contacts
        """
        await self._ensure_cache()
        
        try:
            # Build query
            query = "SELECT * FROM Customer"
            conditions = []
            
            if active_only:
                conditions.append("Active = true")
            if modified_since:
                conditions.append(f"LastUpdatedTime >= '{modified_since.isoformat()}'")
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            result = await self.client.query(query)
            customers_data = result.get('QueryResponse', {}).get('Customer', [])
            
            # Convert to normalized format
            contacts = []
            for customer_data in customers_data:
                try:
                    contact = self._convert_customer_to_contact(customer_data)
                    contacts.append(contact)
                except Exception as e:
                    self.logger.warning(f"Failed to convert customer {customer_data.get('Id')}: {str(e)}")
                    continue
            
            self.logger.info(f"Extracted {len(contacts)} customers from QuickBooks")
            return contacts
            
        except Exception as e:
            raise QuickBooksDataError(f"Failed to extract customers: {str(e)}")
    
    def _convert_customer_to_contact(self, customer_data: Dict[str, Any]) -> AccountingContact:
        """Convert QuickBooks customer to normalized contact."""
        return AccountingContact(
            id=customer_data.get('Id', ''),
            name=customer_data.get('Name', ''),
            email=customer_data.get('PrimaryEmailAddr', {}).get('Address', ''),
            phone=customer_data.get('PrimaryPhone', {}).get('FreeFormNumber', ''),
            address={
                'line1': customer_data.get('BillAddr', {}).get('Line1', ''),
                'line2': customer_data.get('BillAddr', {}).get('Line2', ''),
                'city': customer_data.get('BillAddr', {}).get('City', ''),
                'state': customer_data.get('BillAddr', {}).get('CountrySubDivisionCode', ''),
                'postal_code': customer_data.get('BillAddr', {}).get('PostalCode', ''),
                'country': customer_data.get('BillAddr', {}).get('Country', 'NG')
            },
            tax_number=customer_data.get('ResaleNum', ''),
            is_active=customer_data.get('Active', True),
            metadata={
                'quickbooks_id': customer_data.get('Id'),
                'sync_token': customer_data.get('SyncToken'),
                'company_name': customer_data.get('CompanyName', ''),
                'balance': customer_data.get('Balance', 0),
                'created_time': customer_data.get('MetaData', {}).get('CreateTime'),
                'last_updated_time': customer_data.get('MetaData', {}).get('LastUpdatedTime')
            }
        )
    
    async def extract_chart_of_accounts(self) -> List[AccountingAccount]:
        """Extract chart of accounts from QuickBooks."""
        await self._ensure_cache()
        
        try:
            accounts = []
            for account_data in self._accounts_cache.values():
                try:
                    account = self._convert_account(account_data)
                    accounts.append(account)
                except Exception as e:
                    self.logger.warning(f"Failed to convert account {account_data.get('Id')}: {str(e)}")
                    continue
            
            self.logger.info(f"Extracted {len(accounts)} accounts from QuickBooks")
            return accounts
            
        except Exception as e:
            raise QuickBooksDataError(f"Failed to extract chart of accounts: {str(e)}")
    
    def _convert_account(self, account_data: Dict[str, Any]) -> AccountingAccount:
        """Convert QuickBooks account to normalized account."""
        return AccountingAccount(
            id=account_data.get('Id', ''),
            name=account_data.get('Name', ''),
            code=account_data.get('AcctNum', ''),
            account_type=account_data.get('AccountType', ''),
            account_sub_type=account_data.get('AccountSubType', ''),
            description=account_data.get('Description', ''),
            balance=self._normalize_decimal(account_data.get('CurrentBalance', 0)),
            parent_id=account_data.get('ParentRef', {}).get('value'),
            is_active=account_data.get('Active', True),
            metadata={
                'quickbooks_id': account_data.get('Id'),
                'sync_token': account_data.get('SyncToken'),
                'classification': account_data.get('Classification'),
                'created_time': account_data.get('MetaData', {}).get('CreateTime'),
                'last_updated_time': account_data.get('MetaData', {}).get('LastUpdatedTime')
            }
        )
    
    async def get_transaction_by_id(self, transaction_id: str, transaction_type: str) -> Optional[AccountingTransaction]:
        """
        Get specific transaction by ID.
        
        Args:
            transaction_id: Transaction ID
            transaction_type: Transaction type (Invoice, Bill, etc.)
            
        Returns:
            Normalized transaction or None if not found
        """
        try:
            result = await self.client.get_entity(transaction_type.lower(), transaction_id)
            transaction_data = result.get('QueryResponse', {}).get(transaction_type, [])
            
            if transaction_data:
                if transaction_type == 'Invoice':
                    return await self._convert_invoice_to_transaction(transaction_data[0])
                # Add other transaction type conversions as needed
                
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get transaction {transaction_id}: {str(e)}")
            return None