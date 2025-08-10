"""
Sage Business Cloud Accounting Data Extractor
Extracts and processes financial data from Sage Business Cloud Accounting API.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from decimal import Decimal

from .rest_client import SageRestClient
from .exceptions import SageDataError, SageValidationError
from ....connector_framework.base_accounting_connector import (
    AccountingTransaction,
    AccountingContact,
    AccountingAccount,
    AccountingTransactionType,
    AccountingDocumentStatus
)


class SageDataExtractor:
    """
    Extracts financial data from Sage Business Cloud Accounting API.
    
    Handles:
    - Sales invoice and transaction data extraction
    - Contact (customer/supplier) information
    - Ledger accounts (chart of accounts)
    - Data validation and normalization
    - Sage-specific data structures and pagination
    """
    
    def __init__(self, rest_client: SageRestClient):
        """
        Initialize data extractor.
        
        Args:
            rest_client: Sage REST client
        """
        self.client = rest_client
        self.logger = logging.getLogger(__name__)
        
        # Cache for frequently accessed data
        self._contacts_cache: Optional[Dict[str, Dict[str, Any]]] = None
        self._accounts_cache: Optional[Dict[str, Dict[str, Any]]] = None
        self._tax_rates_cache: Optional[Dict[str, Dict[str, Any]]] = None
        self._products_cache: Optional[Dict[str, Dict[str, Any]]] = None
        self._cache_ttl = timedelta(minutes=15)
        self._cache_timestamp: Optional[datetime] = None
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if not self._cache_timestamp:
            return False
        return datetime.now() - self._cache_timestamp < self._cache_ttl
    
    async def _refresh_cache(self) -> None:
        """Refresh data cache."""
        self.logger.info("Refreshing Sage data cache")
        
        # Fetch core data in parallel
        contacts_task = asyncio.create_task(self.client.get_all_pages(self.client.get_contacts))
        accounts_task = asyncio.create_task(self.client.get_all_pages(self.client.get_ledger_accounts))
        tax_rates_task = asyncio.create_task(self.client.get_all_pages(self.client.get_tax_rates))
        products_task = asyncio.create_task(self.client.get_all_pages(self.client.get_products))
        
        contacts_list, accounts_list, tax_rates_list, products_list = await asyncio.gather(
            contacts_task, accounts_task, tax_rates_task, products_task,
            return_exceptions=True
        )
        
        # Process contacts
        if not isinstance(contacts_list, Exception):
            self._contacts_cache = {
                contact['id']: contact for contact in contacts_list
            }
        else:
            self._contacts_cache = {}
            self.logger.warning(f"Failed to cache contacts: {contacts_list}")
        
        # Process accounts
        if not isinstance(accounts_list, Exception):
            self._accounts_cache = {
                account['id']: account for account in accounts_list
            }
        else:
            self._accounts_cache = {}
            self.logger.warning(f"Failed to cache accounts: {accounts_list}")
        
        # Process tax rates
        if not isinstance(tax_rates_list, Exception):
            self._tax_rates_cache = {
                tax_rate['id']: tax_rate for tax_rate in tax_rates_list
            }
        else:
            self._tax_rates_cache = {}
            self.logger.warning(f"Failed to cache tax rates: {tax_rates_list}")
        
        # Process products
        if not isinstance(products_list, Exception):
            self._products_cache = {
                product['id']: product for product in products_list
            }
        else:
            self._products_cache = {}
            self.logger.warning(f"Failed to cache products: {products_list}")
        
        self._cache_timestamp = datetime.now()
        self.logger.info(f"Cache refreshed: {len(self._contacts_cache)} contacts, "
                        f"{len(self._accounts_cache)} accounts, {len(self._tax_rates_cache)} tax rates, "
                        f"{len(self._products_cache)} products")
    
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
        """Parse Sage date string."""
        if not date_str:
            return None
        try:
            # Sage uses ISO 8601 format
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            try:
                # Try alternative format
                return datetime.strptime(date_str[:10], '%Y-%m-%d')
            except:
                return None
    
    def _map_transaction_type(self, sage_type: str) -> AccountingTransactionType:
        """Map Sage transaction type to standard type."""
        # Sage uses different document types
        type_mapping = {
            'SALES_INVOICE': AccountingTransactionType.INVOICE,
            'SALES_CREDIT_NOTE': AccountingTransactionType.CREDIT_NOTE,
            'PURCHASE_INVOICE': AccountingTransactionType.BILL,
            'PURCHASE_CREDIT_NOTE': AccountingTransactionType.CREDIT_NOTE,
        }
        return type_mapping.get(sage_type.upper(), AccountingTransactionType.OTHER)
    
    def _map_document_status(self, sage_status: Optional[str]) -> AccountingDocumentStatus:
        """Map Sage document status to standard status."""
        if not sage_status:
            return AccountingDocumentStatus.DRAFT
        
        status_mapping = {
            'DRAFT': AccountingDocumentStatus.DRAFT,
            'SENT': AccountingDocumentStatus.SENT,
            'PAID': AccountingDocumentStatus.PAID,
            'PART_PAID': AccountingDocumentStatus.PARTIALLY_PAID,
            'OVERDUE': AccountingDocumentStatus.OVERDUE,
            'VOID': AccountingDocumentStatus.VOID,
            'DELETED': AccountingDocumentStatus.DELETED
        }
        return status_mapping.get(sage_status.upper(), AccountingDocumentStatus.DRAFT)
    
    async def extract_invoices(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        contact_ids: Optional[Set[str]] = None,
        invoice_type: str = "sales"
    ) -> List[AccountingTransaction]:
        """
        Extract invoices from Sage.
        
        Args:
            start_date: Filter invoices from this date
            end_date: Filter invoices until this date
            contact_ids: Filter by specific contact IDs
            invoice_type: Type of invoices (sales, purchase)
            
        Returns:
            List of normalized invoice transactions
        """
        await self._ensure_cache()
        
        try:
            # Determine which endpoint to use
            if invoice_type.lower() == "purchase":
                invoice_method = self.client.get_purchase_invoices
                doc_type = "PURCHASE_INVOICE"
            else:
                invoice_method = self.client.get_sales_invoices
                doc_type = "SALES_INVOICE"
            
            # Fetch all invoices with date filtering
            all_invoices = await self.client.get_all_pages(
                invoice_method,
                from_date=start_date,
                to_date=end_date,
                items_per_page=200
            )
            
            # Filter by contact IDs if specified
            if contact_ids:
                all_invoices = [
                    inv for inv in all_invoices
                    if inv.get('contact', {}).get('id') in contact_ids
                ]
            
            # Convert to normalized format
            transactions = []
            for invoice_data in all_invoices:
                try:
                    transaction = await self._convert_invoice_to_transaction(invoice_data, doc_type)
                    transactions.append(transaction)
                except Exception as e:
                    self.logger.warning(f"Failed to convert invoice {invoice_data.get('id')}: {str(e)}")
                    continue
            
            self.logger.info(f"Extracted {len(transactions)} {invoice_type} invoices from Sage")
            return transactions
            
        except Exception as e:
            raise SageDataError(f"Failed to extract {invoice_type} invoices: {str(e)}")
    
    async def _convert_invoice_to_transaction(self, invoice_data: Dict[str, Any], doc_type: str) -> AccountingTransaction:
        """Convert Sage invoice to normalized transaction."""
        # Basic invoice information
        invoice_id = invoice_data.get('id')
        invoice_number = invoice_data.get('invoice_number', invoice_id)
        
        # Contact information
        contact_data = invoice_data.get('contact', {})
        contact_id = contact_data.get('id')
        contact_name = contact_data.get('name', '')
        
        # Get detailed contact info from cache
        detailed_contact = self._contacts_cache.get(contact_id, {}) if contact_id else {}
        
        # Dates
        date = self._parse_date(invoice_data.get('date'))
        due_date = self._parse_date(invoice_data.get('due_date'))
        
        # Financial amounts
        total_amount = self._normalize_decimal(invoice_data.get('total_amount', 0))
        net_amount = self._normalize_decimal(invoice_data.get('net_amount', 0))
        tax_amount = self._normalize_decimal(invoice_data.get('tax_amount', 0))
        outstanding_amount = self._normalize_decimal(invoice_data.get('outstanding_amount', 0))
        
        # Calculate paid amount
        paid_amount = total_amount - outstanding_amount
        
        # Status determination
        status = self._map_document_status(invoice_data.get('status'))
        
        # Currency
        currency_code = invoice_data.get('currency', {}).get('currency_code', 'GBP')  # Sage defaults to GBP
        
        # Line items
        line_items = []
        for line in invoice_data.get('invoice_lines', []):
            # Get product information if available
            product_id = line.get('product', {}).get('id') if line.get('product') else None
            product_data = self._products_cache.get(product_id, {}) if product_id else {}
            
            # Get tax rate information
            tax_rate_id = line.get('tax_rate', {}).get('id') if line.get('tax_rate') else None
            tax_rate_data = self._tax_rates_cache.get(tax_rate_id, {}) if tax_rate_id else {}
            
            line_item = {
                'id': line.get('id'),
                'product_id': product_id,
                'product_code': product_data.get('item_code', ''),
                'description': line.get('description', product_data.get('description', '')),
                'quantity': self._normalize_decimal(line.get('quantity', 1)),
                'unit_price': self._normalize_decimal(line.get('unit_price', 0)),
                'net_amount': self._normalize_decimal(line.get('net_amount', 0)),
                'tax_amount': self._normalize_decimal(line.get('tax_amount', 0)),
                'total_amount': self._normalize_decimal(line.get('total_amount', 0)),
                'discount_percentage': self._normalize_decimal(line.get('discount_percentage', 0)),
                'tax_rate_percentage': self._normalize_decimal(tax_rate_data.get('percentage', 0)),
                'tax_rate_name': tax_rate_data.get('name', ''),
                'ledger_account_id': line.get('ledger_account', {}).get('id') if line.get('ledger_account') else None
            }
            line_items.append(line_item)
        
        # Create contact object
        contact = AccountingContact(
            id=contact_id or '',
            name=contact_name,
            email=detailed_contact.get('email', ''),
            phone=detailed_contact.get('telephone', ''),
            address=self._extract_address(detailed_contact.get('main_address', {})),
            tax_number=detailed_contact.get('tax_number', ''),
            is_customer=detailed_contact.get('contact_type_ids', []) and 'CUSTOMER' in [ct.get('id') for ct in detailed_contact.get('contact_type_ids', [])],
            is_supplier=detailed_contact.get('contact_type_ids', []) and 'VENDOR' in [ct.get('id') for ct in detailed_contact.get('contact_type_ids', [])]
        )
        
        # Create normalized transaction
        return AccountingTransaction(
            id=invoice_id,
            document_number=invoice_number,
            transaction_type=self._map_transaction_type(doc_type),
            status=status,
            date=date or datetime.now(),
            due_date=due_date,
            contact=contact,
            currency_code=currency_code,
            subtotal_amount=net_amount,
            tax_amount=tax_amount,
            total_amount=total_amount,
            paid_amount=paid_amount,
            balance_amount=outstanding_amount,
            line_items=line_items,
            notes=invoice_data.get('notes', ''),
            reference=invoice_data.get('reference', ''),
            metadata={
                'sage_id': invoice_id,
                'sage_type': doc_type,
                'created_at': invoice_data.get('created_at'),
                'updated_at': invoice_data.get('updated_at'),
                'exchange_rate': invoice_data.get('exchange_rate'),
                'inverse_exchange_rate': invoice_data.get('inverse_exchange_rate'),
                'base_currency_total_amount': invoice_data.get('base_currency_total_amount'),
                'base_currency_net_amount': invoice_data.get('base_currency_net_amount'),
                'base_currency_tax_amount': invoice_data.get('base_currency_tax_amount'),
                'sage_status_code': invoice_data.get('status'),
                'tax_analysis': invoice_data.get('tax_analysis', []),
                'payments': invoice_data.get('payments', [])
            }
        )
    
    def _extract_address(self, address_data: Dict[str, Any]) -> Dict[str, str]:
        """Extract address information from Sage contact address."""
        if not address_data:
            return {
                'line1': '',
                'line2': '',
                'city': '',
                'region': '',
                'postal_code': '',
                'country': 'NG'
            }
        
        return {
            'line1': address_data.get('address_line_1', ''),
            'line2': address_data.get('address_line_2', ''),
            'city': address_data.get('city', ''),
            'region': address_data.get('region', ''),
            'postal_code': address_data.get('postal_code', ''),
            'country': address_data.get('country', {}).get('id', 'NG') if address_data.get('country') else 'NG'
        }
    
    async def extract_contacts(
        self,
        active_only: bool = True,
        contact_type: Optional[str] = None
    ) -> List[AccountingContact]:
        """
        Extract contacts from Sage.
        
        Args:
            active_only: Only return active contacts (Sage doesn't have inactive status)
            contact_type: Filter by contact type (Customer, Vendor)
            
        Returns:
            List of normalized contact records
        """
        await self._ensure_cache()
        
        try:
            # Fetch all contacts
            all_contacts = await self.client.get_all_pages(
                self.client.get_contacts,
                contact_type=contact_type,
                items_per_page=200
            )
            
            # Convert to normalized format
            contacts = []
            for contact_data in all_contacts:
                try:
                    contact = self._convert_contact(contact_data)
                    contacts.append(contact)
                except Exception as e:
                    self.logger.warning(f"Failed to convert contact {contact_data.get('id')}: {str(e)}")
                    continue
            
            self.logger.info(f"Extracted {len(contacts)} contacts from Sage")
            return contacts
            
        except Exception as e:
            raise SageDataError(f"Failed to extract contacts: {str(e)}")
    
    def _convert_contact(self, contact_data: Dict[str, Any]) -> AccountingContact:
        """Convert Sage contact to normalized contact."""
        # Get primary email and phone
        email = contact_data.get('email', '')
        telephone = contact_data.get('telephone', '')
        
        # Get address
        main_address = contact_data.get('main_address', {})
        address = self._extract_address(main_address)
        
        # Determine contact types
        contact_type_ids = [ct.get('id') for ct in contact_data.get('contact_type_ids', [])]
        is_customer = 'CUSTOMER' in contact_type_ids
        is_supplier = 'VENDOR' in contact_type_ids
        
        return AccountingContact(
            id=contact_data.get('id', ''),
            name=contact_data.get('name', ''),
            email=email,
            phone=telephone,
            address=address,
            tax_number=contact_data.get('tax_number', ''),
            is_active=True,  # Sage doesn't have inactive status
            is_customer=is_customer,
            is_supplier=is_supplier,
            metadata={
                'sage_id': contact_data.get('id'),
                'created_at': contact_data.get('created_at'),
                'updated_at': contact_data.get('updated_at'),
                'contact_type_ids': contact_type_ids,
                'credit_limit': contact_data.get('credit_limit'),
                'credit_days': contact_data.get('credit_days'),
                'account_number': contact_data.get('account_number'),
                'mobile': contact_data.get('mobile'),
                'website': contact_data.get('website'),
                'notes': contact_data.get('notes', ''),
                'delivery_address': contact_data.get('delivery_address', {}),
                'bank_account_details': contact_data.get('bank_account_details', {}),
                'tax_treatment': contact_data.get('tax_treatment', {}),
                'currency': contact_data.get('currency', {})
            }
        )
    
    async def extract_chart_of_accounts(self) -> List[AccountingAccount]:
        """Extract chart of accounts from Sage."""
        await self._ensure_cache()
        
        try:
            accounts = []
            for account_data in self._accounts_cache.values():
                try:
                    account = self._convert_account(account_data)
                    accounts.append(account)
                except Exception as e:
                    self.logger.warning(f"Failed to convert account {account_data.get('id')}: {str(e)}")
                    continue
            
            self.logger.info(f"Extracted {len(accounts)} accounts from Sage")
            return accounts
            
        except Exception as e:
            raise SageDataError(f"Failed to extract chart of accounts: {str(e)}")
    
    def _convert_account(self, account_data: Dict[str, Any]) -> AccountingAccount:
        """Convert Sage ledger account to normalized account."""
        return AccountingAccount(
            id=account_data.get('id', ''),
            name=account_data.get('name', ''),
            code=account_data.get('nominal_code', ''),
            account_type=account_data.get('ledger_account_type', {}).get('id', ''),
            account_sub_type=account_data.get('ledger_account_classification', {}).get('id', ''),
            description=account_data.get('description', ''),
            balance=self._normalize_decimal(0),  # Sage doesn't include balance in accounts endpoint
            is_active=True,  # Sage accounts are generally active
            metadata={
                'sage_id': account_data.get('id'),
                'created_at': account_data.get('created_at'),
                'updated_at': account_data.get('updated_at'),
                'nominal_code': account_data.get('nominal_code'),
                'ledger_account_type': account_data.get('ledger_account_type', {}),
                'ledger_account_classification': account_data.get('ledger_account_classification', {}),
                'control_name': account_data.get('control_name'),
                'is_control_account': account_data.get('is_control_account', False),
                'tax_rate': account_data.get('tax_rate', {}),
                'included_in_chart': account_data.get('included_in_chart', True),
                'balance_details': account_data.get('balance_details', {})
            }
        )
    
    async def extract_credit_notes(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AccountingTransaction]:
        """
        Extract credit notes from Sage.
        
        Args:
            start_date: Filter credit notes from this date
            end_date: Filter credit notes until this date
            
        Returns:
            List of normalized credit note transactions
        """
        await self._ensure_cache()
        
        try:
            # Fetch all credit notes with date filtering
            all_credit_notes = await self.client.get_all_pages(
                self.client.get_credit_notes,
                from_date=start_date,
                to_date=end_date,
                items_per_page=200
            )
            
            # Convert to normalized format
            transactions = []
            for credit_note_data in all_credit_notes:
                try:
                    transaction = await self._convert_invoice_to_transaction(credit_note_data, "SALES_CREDIT_NOTE")
                    transactions.append(transaction)
                except Exception as e:
                    self.logger.warning(f"Failed to convert credit note {credit_note_data.get('id')}: {str(e)}")
                    continue
            
            self.logger.info(f"Extracted {len(transactions)} credit notes from Sage")
            return transactions
            
        except Exception as e:
            raise SageDataError(f"Failed to extract credit notes: {str(e)}")
    
    async def get_transaction_by_id(self, transaction_id: str, transaction_type: str = "sales_invoice") -> Optional[AccountingTransaction]:
        """
        Get specific transaction by ID.
        
        Args:
            transaction_id: Sage transaction ID
            transaction_type: Transaction type (sales_invoice, purchase_invoice, etc.)
            
        Returns:
            Normalized transaction or None if not found
        """
        try:
            if transaction_type.lower() == "sales_invoice":
                result = await self.client.get_sales_invoice(transaction_id)
                if result:
                    return await self._convert_invoice_to_transaction(result, "SALES_INVOICE")
            
            # Add support for other transaction types as needed
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get transaction {transaction_id}: {str(e)}")
            return None
    
    def get_cached_contact(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """Get contact from cache by ID."""
        if self._contacts_cache:
            return self._contacts_cache.get(contact_id)
        return None
    
    def get_cached_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get account from cache by ID."""
        if self._accounts_cache:
            return self._accounts_cache.get(account_id)
        return None
    
    def get_cached_tax_rate(self, tax_rate_id: str) -> Optional[Dict[str, Any]]:
        """Get tax rate from cache by ID."""
        if self._tax_rates_cache:
            return self._tax_rates_cache.get(tax_rate_id)
        return None
    
    def get_cached_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product from cache by ID."""
        if self._products_cache:
            return self._products_cache.get(product_id)
        return None
    
    async def extract_tax_rates(self) -> List[Dict[str, Any]]:
        """Extract tax rates from Sage."""
        await self._ensure_cache()
        
        try:
            tax_rates = list(self._tax_rates_cache.values())
            self.logger.info(f"Extracted {len(tax_rates)} tax rates from Sage")
            return tax_rates
        except Exception as e:
            raise SageDataError(f"Failed to extract tax rates: {str(e)}")
    
    async def extract_products(self) -> List[Dict[str, Any]]:
        """Extract products/services from Sage."""
        await self._ensure_cache()
        
        try:
            products = list(self._products_cache.values())
            self.logger.info(f"Extracted {len(products)} products from Sage")
            return products
        except Exception as e:
            raise SageDataError(f"Failed to extract products: {str(e)}")