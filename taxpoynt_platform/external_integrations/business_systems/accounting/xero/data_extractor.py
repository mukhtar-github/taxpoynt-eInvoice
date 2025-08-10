"""
Xero Accounting Data Extractor
Extracts and processes financial data from Xero Accounting API.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from decimal import Decimal

from .rest_client import XeroRestClient
from .exceptions import XeroDataError, XeroValidationError
from ....connector_framework.base_accounting_connector import (
    AccountingTransaction,
    AccountingContact,
    AccountingAccount,
    AccountingTransactionType,
    AccountingDocumentStatus
)


class XeroDataExtractor:
    """
    Extracts financial data from Xero Accounting API.
    
    Handles:
    - Invoice and transaction data extraction
    - Contact (customer/supplier) information
    - Chart of accounts
    - Data validation and normalization
    - Xero-specific data structures
    """
    
    def __init__(self, rest_client: XeroRestClient):
        """
        Initialize data extractor.
        
        Args:
            rest_client: Xero REST client
        """
        self.client = rest_client
        self.logger = logging.getLogger(__name__)
        
        # Cache for frequently accessed data
        self._contacts_cache: Optional[Dict[str, Dict[str, Any]]] = None
        self._accounts_cache: Optional[Dict[str, Dict[str, Any]]] = None
        self._tax_rates_cache: Optional[Dict[str, Dict[str, Any]]] = None
        self._cache_ttl = timedelta(minutes=15)
        self._cache_timestamp: Optional[datetime] = None
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if not self._cache_timestamp:
            return False
        return datetime.now() - self._cache_timestamp < self._cache_ttl
    
    async def _refresh_cache(self) -> None:
        """Refresh data cache."""
        self.logger.info("Refreshing Xero data cache")
        
        # Fetch core data in parallel
        contacts_task = asyncio.create_task(self.client.get_contacts())
        accounts_task = asyncio.create_task(self.client.get_accounts())
        tax_rates_task = asyncio.create_task(self.client.get_tax_rates())
        
        contacts_resp, accounts_resp, tax_rates_resp = await asyncio.gather(
            contacts_task, accounts_task, tax_rates_task,
            return_exceptions=True
        )
        
        # Process contacts
        if not isinstance(contacts_resp, Exception):
            contacts_list = contacts_resp.get('Contacts', [])
            self._contacts_cache = {
                contact['ContactID']: contact for contact in contacts_list
            }
        else:
            self._contacts_cache = {}
            self.logger.warning(f"Failed to cache contacts: {contacts_resp}")
        
        # Process accounts
        if not isinstance(accounts_resp, Exception):
            accounts_list = accounts_resp.get('Accounts', [])
            self._accounts_cache = {
                account['AccountID']: account for account in accounts_list
            }
        else:
            self._accounts_cache = {}
            self.logger.warning(f"Failed to cache accounts: {accounts_resp}")
        
        # Process tax rates
        if not isinstance(tax_rates_resp, Exception):
            tax_rates_list = tax_rates_resp.get('TaxRates', [])
            self._tax_rates_cache = {
                tax_rate['TaxType']: tax_rate for tax_rate in tax_rates_list
            }
        else:
            self._tax_rates_cache = {}
            self.logger.warning(f"Failed to cache tax rates: {tax_rates_resp}")
        
        self._cache_timestamp = datetime.now()
        self.logger.info(f"Cache refreshed: {len(self._contacts_cache)} contacts, "
                        f"{len(self._accounts_cache)} accounts, {len(self._tax_rates_cache)} tax rates")
    
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
        """Parse Xero date string."""
        if not date_str:
            return None
        try:
            # Xero uses ISO 8601 format
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
    
    def _map_transaction_type(self, xero_type: str) -> AccountingTransactionType:
        """Map Xero transaction type to standard type."""
        type_mapping = {
            'ACCREC': AccountingTransactionType.INVOICE,  # Accounts Receivable (Sales Invoice)
            'ACCPAY': AccountingTransactionType.BILL,     # Accounts Payable (Purchase Invoice)
            'ACCCREDIT': AccountingTransactionType.CREDIT_NOTE,  # Credit Note
        }
        return type_mapping.get(xero_type, AccountingTransactionType.OTHER)
    
    def _map_document_status(self, xero_status: Optional[str]) -> AccountingDocumentStatus:
        """Map Xero document status to standard status."""
        if not xero_status:
            return AccountingDocumentStatus.DRAFT
        
        status_mapping = {
            'DRAFT': AccountingDocumentStatus.DRAFT,
            'SUBMITTED': AccountingDocumentStatus.SENT,
            'AUTHORISED': AccountingDocumentStatus.SENT,
            'PAID': AccountingDocumentStatus.PAID,
            'VOIDED': AccountingDocumentStatus.VOID,
            'DELETED': AccountingDocumentStatus.DELETED
        }
        return status_mapping.get(xero_status, AccountingDocumentStatus.DRAFT)
    
    async def extract_invoices(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        contact_ids: Optional[Set[str]] = None,
        invoice_type: Optional[str] = None
    ) -> List[AccountingTransaction]:
        """
        Extract invoices from Xero.
        
        Args:
            start_date: Filter invoices from this date
            end_date: Filter invoices until this date
            contact_ids: Filter by specific contact IDs
            invoice_type: Filter by invoice type (ACCREC, ACCPAY)
            
        Returns:
            List of normalized invoice transactions
        """
        await self._ensure_cache()
        
        # Build where clause for filtering
        where_conditions = []
        
        if start_date:
            where_conditions.append(f"Date >= DateTime({start_date.year}, {start_date.month}, {start_date.day})")
        if end_date:
            where_conditions.append(f"Date <= DateTime({end_date.year}, {end_date.month}, {end_date.day})")
        if invoice_type:
            where_conditions.append(f"Type == \"{invoice_type}\"")
        if contact_ids:
            contact_filter = " OR ".join([f"Contact.ContactID == Guid(\"{cid}\")" for cid in contact_ids])
            where_conditions.append(f"({contact_filter})")
        
        where_clause = " AND ".join(where_conditions) if where_conditions else None
        
        try:
            # Fetch invoices with pagination
            all_invoices = []
            page = 1
            
            while True:
                result = await self.client.get_invoices(
                    where=where_clause,
                    order="Date DESC",
                    page=page
                )
                
                invoices_data = result.get('Invoices', [])
                if not invoices_data:
                    break
                
                all_invoices.extend(invoices_data)
                
                # Check if there are more pages
                if len(invoices_data) < 100:  # Xero default page size
                    break
                
                page += 1
            
            # Convert to normalized format
            transactions = []
            for invoice_data in all_invoices:
                try:
                    transaction = await self._convert_invoice_to_transaction(invoice_data)
                    transactions.append(transaction)
                except Exception as e:
                    self.logger.warning(f"Failed to convert invoice {invoice_data.get('InvoiceID')}: {str(e)}")
                    continue
            
            self.logger.info(f"Extracted {len(transactions)} invoices from Xero")
            return transactions
            
        except Exception as e:
            raise XeroDataError(f"Failed to extract invoices: {str(e)}")
    
    async def _convert_invoice_to_transaction(self, invoice_data: Dict[str, Any]) -> AccountingTransaction:
        """Convert Xero invoice to normalized transaction."""
        # Basic invoice information
        invoice_id = invoice_data.get('InvoiceID')
        invoice_number = invoice_data.get('InvoiceNumber', invoice_id)
        invoice_type = invoice_data.get('Type', 'ACCREC')
        
        # Contact information
        contact_data = invoice_data.get('Contact', {})
        contact_id = contact_data.get('ContactID')
        contact_name = contact_data.get('Name', '')
        
        # Get detailed contact info from cache
        detailed_contact = self._contacts_cache.get(contact_id, {}) if contact_id else {}
        
        # Dates
        date = self._parse_date(invoice_data.get('Date'))
        due_date = self._parse_date(invoice_data.get('DueDate'))
        
        # Financial amounts
        total_amount = self._normalize_decimal(invoice_data.get('Total', 0))
        subtotal_amount = self._normalize_decimal(invoice_data.get('SubTotal', 0))
        total_tax = self._normalize_decimal(invoice_data.get('TotalTax', 0))
        amount_due = self._normalize_decimal(invoice_data.get('AmountDue', 0))
        amount_paid = self._normalize_decimal(invoice_data.get('AmountPaid', 0))
        
        # Status determination
        status = self._map_document_status(invoice_data.get('Status'))
        
        # Currency
        currency_code = invoice_data.get('CurrencyCode', 'NZD')  # Xero defaults to NZD
        
        # Line items
        line_items = []
        for line in invoice_data.get('LineItems', []):
            line_item = {
                'id': line.get('LineItemID'),
                'item_code': line.get('ItemCode', ''),
                'description': line.get('Description', ''),
                'quantity': self._normalize_decimal(line.get('Quantity', 1)),
                'unit_amount': self._normalize_decimal(line.get('UnitAmount', 0)),
                'line_amount': self._normalize_decimal(line.get('LineAmount', 0)),
                'discount_rate': self._normalize_decimal(line.get('DiscountRate', 0)),
                'discount_amount': self._normalize_decimal(line.get('DiscountAmount', 0)),
                'tax_type': line.get('TaxType', ''),
                'tax_amount': self._normalize_decimal(line.get('TaxAmount', 0)),
                'account_code': line.get('AccountCode', ''),
            }
            
            # Add tracking categories if present
            tracking = line.get('Tracking', [])
            if tracking:
                line_item['tracking'] = tracking
            
            line_items.append(line_item)
        
        # Create contact object
        contact = AccountingContact(
            id=contact_id or '',
            name=contact_name,
            email=detailed_contact.get('EmailAddress', ''),
            phone=detailed_contact.get('Phones', [{}])[0].get('PhoneNumber', '') if detailed_contact.get('Phones') else '',
            address=self._extract_address(detailed_contact.get('Addresses', [])),
            tax_number=detailed_contact.get('TaxNumber', ''),
            is_customer=detailed_contact.get('IsCustomer', True),
            is_supplier=detailed_contact.get('IsSupplier', False)
        )
        
        # Create normalized transaction
        return AccountingTransaction(
            id=invoice_id,
            document_number=invoice_number,
            transaction_type=self._map_transaction_type(invoice_type),
            status=status,
            date=date or datetime.now(),
            due_date=due_date,
            contact=contact,
            currency_code=currency_code,
            subtotal_amount=subtotal_amount,
            tax_amount=total_tax,
            total_amount=total_amount,
            paid_amount=amount_paid,
            balance_amount=amount_due,
            line_items=line_items,
            notes=invoice_data.get('Reference', ''),
            reference=invoice_data.get('Reference', ''),
            metadata={
                'xero_id': invoice_id,
                'xero_type': invoice_type,
                'updated_date_utc': invoice_data.get('UpdatedDateUTC'),
                'currency_rate': invoice_data.get('CurrencyRate'),
                'branding_theme_id': invoice_data.get('BrandingThemeID'),
                'has_attachments': invoice_data.get('HasAttachments', False),
                'line_amount_types': invoice_data.get('LineAmountTypes'),
                'payments': invoice_data.get('Payments', []),
                'credit_notes': invoice_data.get('CreditNotes', []),
                'prepayments': invoice_data.get('Prepayments', []),
                'overpayments': invoice_data.get('Overpayments', [])
            }
        )
    
    def _extract_address(self, addresses: List[Dict[str, Any]]) -> Dict[str, str]:
        """Extract address information from Xero contact addresses."""
        # Prefer POBOX, then STREET
        address_types = ['POBOX', 'STREET']
        
        for addr_type in address_types:
            for addr in addresses:
                if addr.get('AddressType') == addr_type:
                    return {
                        'line1': addr.get('AddressLine1', ''),
                        'line2': addr.get('AddressLine2', ''),
                        'line3': addr.get('AddressLine3', ''),
                        'line4': addr.get('AddressLine4', ''),
                        'city': addr.get('City', ''),
                        'region': addr.get('Region', ''),
                        'postal_code': addr.get('PostalCode', ''),
                        'country': addr.get('Country', 'NG')
                    }
        
        # Return empty address if none found
        return {
            'line1': '',
            'line2': '',
            'city': '',
            'region': '',
            'postal_code': '',
            'country': 'NG'
        }
    
    async def extract_contacts(
        self,
        active_only: bool = True,
        modified_since: Optional[datetime] = None,
        contact_type: Optional[str] = None
    ) -> List[AccountingContact]:
        """
        Extract contacts from Xero.
        
        Args:
            active_only: Only return active contacts
            modified_since: Only return contacts modified since this date
            contact_type: Filter by contact type (Customer, Supplier)
            
        Returns:
            List of normalized contact records
        """
        await self._ensure_cache()
        
        # Build where clause
        where_conditions = []
        
        if modified_since:
            where_conditions.append(f"UpdatedDateUTC >= DateTime({modified_since.year}, {modified_since.month}, {modified_since.day})")
        if contact_type == 'Customer':
            where_conditions.append("IsCustomer == true")
        elif contact_type == 'Supplier':
            where_conditions.append("IsSupplier == true")
        
        where_clause = " AND ".join(where_conditions) if where_conditions else None
        
        try:
            # Fetch contacts with pagination
            all_contacts = []
            page = 1
            
            while True:
                result = await self.client.get_contacts(
                    where=where_clause,
                    order="Name",
                    page=page,
                    include_archived=not active_only
                )
                
                contacts_data = result.get('Contacts', [])
                if not contacts_data:
                    break
                
                all_contacts.extend(contacts_data)
                
                # Check if there are more pages
                if len(contacts_data) < 100:  # Xero default page size
                    break
                
                page += 1
            
            # Convert to normalized format
            contacts = []
            for contact_data in all_contacts:
                try:
                    contact = self._convert_contact(contact_data)
                    contacts.append(contact)
                except Exception as e:
                    self.logger.warning(f"Failed to convert contact {contact_data.get('ContactID')}: {str(e)}")
                    continue
            
            self.logger.info(f"Extracted {len(contacts)} contacts from Xero")
            return contacts
            
        except Exception as e:
            raise XeroDataError(f"Failed to extract contacts: {str(e)}")
    
    def _convert_contact(self, contact_data: Dict[str, Any]) -> AccountingContact:
        """Convert Xero contact to normalized contact."""
        # Get primary email
        email = contact_data.get('EmailAddress', '')
        
        # Get primary phone
        phones = contact_data.get('Phones', [])
        phone = phones[0].get('PhoneNumber', '') if phones else ''
        
        # Get address
        addresses = contact_data.get('Addresses', [])
        address = self._extract_address(addresses)
        
        return AccountingContact(
            id=contact_data.get('ContactID', ''),
            name=contact_data.get('Name', ''),
            email=email,
            phone=phone,
            address=address,
            tax_number=contact_data.get('TaxNumber', ''),
            is_active=contact_data.get('ContactStatus') != 'ARCHIVED',
            is_customer=contact_data.get('IsCustomer', False),
            is_supplier=contact_data.get('IsSupplier', False),
            metadata={
                'xero_id': contact_data.get('ContactID'),
                'updated_date_utc': contact_data.get('UpdatedDateUTC'),
                'contact_status': contact_data.get('ContactStatus'),
                'contact_groups': contact_data.get('ContactGroups', []),
                'sales_tracking_categories': contact_data.get('SalesTrackingCategories', []),
                'purchases_tracking_categories': contact_data.get('PurchasesTrackingCategories', []),
                'payment_terms': contact_data.get('PaymentTerms', {}),
                'contact_persons': contact_data.get('ContactPersons', []),
                'has_attachments': contact_data.get('HasAttachments', False),
                'xero_network_key': contact_data.get('XeroNetworkKey'),
                'bank_account_details': contact_data.get('BankAccountDetails'),
                'batch_payments': contact_data.get('BatchPayments', {}),
                'discount': contact_data.get('Discount'),
                'balances': contact_data.get('Balances', {}),
                'has_validation_errors': contact_data.get('HasValidationErrors', False)
            }
        )
    
    async def extract_chart_of_accounts(self) -> List[AccountingAccount]:
        """Extract chart of accounts from Xero."""
        await self._ensure_cache()
        
        try:
            accounts = []
            for account_data in self._accounts_cache.values():
                try:
                    account = self._convert_account(account_data)
                    accounts.append(account)
                except Exception as e:
                    self.logger.warning(f"Failed to convert account {account_data.get('AccountID')}: {str(e)}")
                    continue
            
            self.logger.info(f"Extracted {len(accounts)} accounts from Xero")
            return accounts
            
        except Exception as e:
            raise XeroDataError(f"Failed to extract chart of accounts: {str(e)}")
    
    def _convert_account(self, account_data: Dict[str, Any]) -> AccountingAccount:
        """Convert Xero account to normalized account."""
        return AccountingAccount(
            id=account_data.get('AccountID', ''),
            name=account_data.get('Name', ''),
            code=account_data.get('Code', ''),
            account_type=account_data.get('Type', ''),
            account_sub_type=account_data.get('Class', ''),
            description=account_data.get('Description', ''),
            balance=self._normalize_decimal(0),  # Xero doesn't include balance in accounts endpoint
            is_active=account_data.get('Status') == 'ACTIVE',
            metadata={
                'xero_id': account_data.get('AccountID'),
                'tax_type': account_data.get('TaxType'),
                'enable_payments_to_account': account_data.get('EnablePaymentsToAccount', False),
                'show_in_expense_claims': account_data.get('ShowInExpenseClaims', False),
                'class': account_data.get('Class'),
                'status': account_data.get('Status'),
                'system_account': account_data.get('SystemAccount'),
                'bank_account_number': account_data.get('BankAccountNumber'),
                'bank_account_type': account_data.get('BankAccountType'),
                'currency_code': account_data.get('CurrencyCode'),
                'reporting_code': account_data.get('ReportingCode'),
                'reporting_code_name': account_data.get('ReportingCodeName'),
                'has_attachments': account_data.get('HasAttachments', False),
                'updated_date_utc': account_data.get('UpdatedDateUTC')
            }
        )
    
    async def get_transaction_by_id(self, transaction_id: str, transaction_type: str = "Invoice") -> Optional[AccountingTransaction]:
        """
        Get specific transaction by ID.
        
        Args:
            transaction_id: Xero transaction ID
            transaction_type: Transaction type (Invoice, CreditNote, etc.)
            
        Returns:
            Normalized transaction or None if not found
        """
        try:
            if transaction_type.lower() == "invoice":
                result = await self.client.get_invoice(transaction_id)
                invoices_data = result.get('Invoices', [])
                
                if invoices_data:
                    return await self._convert_invoice_to_transaction(invoices_data[0])
            
            # Add support for other transaction types as needed
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get transaction {transaction_id}: {str(e)}")
            return None
    
    async def extract_payments(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract payments from Xero.
        
        Args:
            start_date: Filter payments from this date
            end_date: Filter payments until this date
            
        Returns:
            List of payment data
        """
        # Build where clause for date filtering
        where_conditions = []
        
        if start_date:
            where_conditions.append(f"Date >= DateTime({start_date.year}, {start_date.month}, {start_date.day})")
        if end_date:
            where_conditions.append(f"Date <= DateTime({end_date.year}, {end_date.month}, {end_date.day})")
        
        where_clause = " AND ".join(where_conditions) if where_conditions else None
        
        try:
            all_payments = []
            page = 1
            
            while True:
                result = await self.client.get_payments(
                    where=where_clause,
                    order="Date DESC",
                    page=page
                )
                
                payments_data = result.get('Payments', [])
                if not payments_data:
                    break
                
                all_payments.extend(payments_data)
                
                # Check if there are more pages
                if len(payments_data) < 100:
                    break
                
                page += 1
            
            self.logger.info(f"Extracted {len(all_payments)} payments from Xero")
            return all_payments
            
        except Exception as e:
            raise XeroDataError(f"Failed to extract payments: {str(e)}")
    
    async def extract_credit_notes(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AccountingTransaction]:
        """
        Extract credit notes from Xero.
        
        Args:
            start_date: Filter credit notes from this date
            end_date: Filter credit notes until this date
            
        Returns:
            List of normalized credit note transactions
        """
        # Build where clause for date filtering
        where_conditions = []
        
        if start_date:
            where_conditions.append(f"Date >= DateTime({start_date.year}, {start_date.month}, {start_date.day})")
        if end_date:
            where_conditions.append(f"Date <= DateTime({end_date.year}, {end_date.month}, {end_date.day})")
        
        where_clause = " AND ".join(where_conditions) if where_conditions else None
        
        try:
            all_credit_notes = []
            page = 1
            
            while True:
                result = await self.client.get_credit_notes(
                    where=where_clause,
                    order="Date DESC",
                    page=page
                )
                
                credit_notes_data = result.get('CreditNotes', [])
                if not credit_notes_data:
                    break
                
                all_credit_notes.extend(credit_notes_data)
                
                # Check if there are more pages
                if len(credit_notes_data) < 100:
                    break
                
                page += 1
            
            # Convert to normalized format
            transactions = []
            for credit_note_data in all_credit_notes:
                try:
                    # Convert credit note structure to invoice structure for processing
                    credit_note_data['Type'] = 'ACCCREDIT'
                    transaction = await self._convert_invoice_to_transaction(credit_note_data)
                    transactions.append(transaction)
                except Exception as e:
                    self.logger.warning(f"Failed to convert credit note {credit_note_data.get('CreditNoteID')}: {str(e)}")
                    continue
            
            self.logger.info(f"Extracted {len(transactions)} credit notes from Xero")
            return transactions
            
        except Exception as e:
            raise XeroDataError(f"Failed to extract credit notes: {str(e)}")
    
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
    
    def get_cached_tax_rate(self, tax_type: str) -> Optional[Dict[str, Any]]:
        """Get tax rate from cache by type."""
        if self._tax_rates_cache:
            return self._tax_rates_cache.get(tax_type)
        return None