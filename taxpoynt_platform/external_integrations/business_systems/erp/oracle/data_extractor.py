"""
Oracle Data Extraction Module
Handles data extraction and formatting from Oracle ERP Cloud services.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from .exceptions import OracleAPIError, OracleDataError

logger = logging.getLogger(__name__)


class OracleDataExtractor:
    """Handles data extraction and formatting from Oracle ERP Cloud."""
    
    def __init__(self, rest_client):
        """Initialize with an Oracle REST client instance."""
        self.rest_client = rest_client
    
    async def get_invoices(
        self,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        supplier_number: Optional[str] = None,
        invoice_status: Optional[str] = None,
        include_attachments: bool = False,
        data_source: str = 'ap_invoices'  # Accounts Payable invoices
    ) -> List[Dict[str, Any]]:
        """
        Get invoice list from Oracle ERP Cloud - SI Role Function.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            start_date: Filter invoices from this date
            end_date: Filter invoices until this date
            supplier_number: Filter by supplier number
            invoice_status: Filter by invoice status
            include_attachments: Whether to include attachment information
            data_source: Data source ('ap_invoices' or 'ar_receivables')
            
        Returns:
            List of invoice records
        """
        try:
            if data_source == 'ap_invoices':
                return await self._get_ap_invoices(
                    limit, offset, start_date, end_date, supplier_number, invoice_status, include_attachments
                )
            elif data_source == 'ar_receivables':
                return await self._get_ar_receivables(
                    limit, offset, start_date, end_date, supplier_number, invoice_status, include_attachments
                )
            else:
                raise OracleDataError(f"Unknown data source: {data_source}")
                
        except Exception as e:
            logger.error(f"Error retrieving Oracle invoices: {str(e)}")
            raise OracleDataError(f"Error retrieving Oracle invoices: {str(e)}")
    
    async def _get_ap_invoices(
        self,
        limit: int,
        offset: int,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        supplier_number: Optional[str],
        invoice_status: Optional[str],
        include_attachments: bool
    ) -> List[Dict[str, Any]]:
        """Get Accounts Payable invoices from Oracle FSCM API."""
        try:
            filters = {}
            
            if start_date:
                filters['start_date'] = start_date.strftime('%Y-%m-%d')
            if end_date:
                filters['end_date'] = end_date.strftime('%Y-%m-%d')
            if supplier_number:
                filters['supplier_number'] = supplier_number
            if invoice_status:
                filters['invoice_status'] = invoice_status
            
            response = await self.rest_client.get_invoices(
                limit=limit,
                offset=offset,
                filters=filters
            )
            
            if not response.get('success'):
                raise OracleDataError(f"Failed to retrieve AP invoices: {response.get('error')}")
            
            invoices = []
            for invoice_data in response.get('data', []):
                formatted_invoice = await self._format_ap_invoice_data(invoice_data, include_attachments)
                invoices.append(formatted_invoice)
            
            return invoices
            
        except Exception as e:
            logger.error(f"Error retrieving AP invoices: {str(e)}")
            raise OracleDataError(f"Error retrieving AP invoices: {str(e)}")
    
    async def _get_ar_receivables(
        self,
        limit: int,
        offset: int,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        customer_number: Optional[str],
        transaction_status: Optional[str],
        include_attachments: bool
    ) -> List[Dict[str, Any]]:
        """Get Accounts Receivable transactions from Oracle FSCM API."""
        try:
            filters = {}
            
            if start_date:
                filters['start_date'] = start_date.strftime('%Y-%m-%d')
            if end_date:
                filters['end_date'] = end_date.strftime('%Y-%m-%d')
            if customer_number:
                filters['customer_number'] = customer_number
            if transaction_status:
                filters['transaction_type'] = transaction_status
            
            response = await self.rest_client.get_receivables(
                limit=limit,
                offset=offset,
                filters=filters
            )
            
            if not response.get('success'):
                raise OracleDataError(f"Failed to retrieve AR receivables: {response.get('error')}")
            
            invoices = []
            for receivable_data in response.get('data', []):
                formatted_invoice = await self._format_ar_receivable_data(receivable_data, include_attachments)
                invoices.append(formatted_invoice)
            
            return invoices
            
        except Exception as e:
            logger.error(f"Error retrieving AR receivables: {str(e)}")
            raise OracleDataError(f"Error retrieving AR receivables: {str(e)}")
    
    async def get_invoice_by_id(self, invoice_id: Union[int, str]) -> Dict[str, Any]:
        """
        Get a specific invoice by ID from Oracle ERP Cloud - SI Role Function.
        
        Args:
            invoice_id: The invoice ID to retrieve
            
        Returns:
            Invoice record data
        """
        try:
            response = await self.rest_client.get_invoice_by_id(str(invoice_id))
            
            if not response.get('success'):
                raise OracleDataError(f"Failed to retrieve invoice {invoice_id}: {response.get('error')}")
            
            return await self._format_ap_invoice_data(response.get('data', {}))
            
        except Exception as e:
            logger.error(f"Error retrieving Oracle invoice {invoice_id}: {str(e)}")
            raise OracleDataError(f"Error retrieving Oracle invoice {invoice_id}: {str(e)}")
    
    async def search_invoices(
        self,
        supplier_name: Optional[str] = None,
        invoice_number: Optional[str] = None,
        amount_range: Optional[tuple] = None,
        date_range: Optional[tuple] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search invoices with specific criteria - SI Role Function.
        
        Args:
            supplier_name: Filter by supplier name
            invoice_number: Filter by invoice number
            amount_range: Tuple of (min_amount, max_amount)
            date_range: Tuple of (start_date, end_date)
            status: Filter by invoice status
            limit: Maximum number of records to return
            
        Returns:
            List of matching invoice records
        """
        try:
            search_criteria = {}
            
            if supplier_name:
                search_criteria['supplier_name'] = supplier_name
            if invoice_number:
                search_criteria['invoice_number'] = invoice_number
            if amount_range:
                search_criteria['amount_range'] = amount_range
            if date_range:
                search_criteria['date_range'] = date_range
            if status:
                search_criteria['status'] = status
            
            response = await self.rest_client.search_invoices(search_criteria, limit)
            
            if not response.get('success'):
                raise OracleDataError(f"Failed to search invoices: {response.get('error')}")
            
            invoices = []
            for invoice_data in response.get('data', []):
                formatted_invoice = await self._format_ap_invoice_data(invoice_data, include_attachments=False)
                invoices.append(formatted_invoice)
            
            return invoices
            
        except Exception as e:
            logger.error(f"Error searching Oracle invoices: {str(e)}")
            raise OracleDataError(f"Error searching Oracle invoices: {str(e)}")
    
    async def get_accounts(
        self,
        search_term: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get customer accounts from Oracle CRM - SI Role Function.
        
        Args:
            search_term: Optional search term to filter accounts
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of account records
        """
        try:
            response = await self.rest_client.get_accounts(
                limit=limit,
                offset=offset,
                search_term=search_term
            )
            
            if not response.get('success'):
                raise OracleDataError(f"Failed to retrieve accounts: {response.get('error')}")
            
            accounts = []
            for account_data in response.get('data', []):
                account = {
                    "id": account_data.get('PartyId', ''),
                    "party_number": account_data.get('PartyNumber', ''),
                    "name": account_data.get('PartyName', ''),
                    "party_type": account_data.get('PartyType', ''),
                    "organization_type": account_data.get('OrganizationType', ''),
                    "customer_account_id": account_data.get('CustomerAccountId', ''),
                    "account_number": account_data.get('AccountNumber', ''),
                    "account_name": account_data.get('AccountName', ''),
                    "customer_type": account_data.get('CustomerType', ''),
                    "source": "oracle_crm"
                }
                accounts.append(account)
            
            return accounts
            
        except Exception as e:
            logger.error(f"Error retrieving Oracle accounts: {str(e)}")
            raise OracleDataError(f"Error retrieving Oracle accounts: {str(e)}")
    
    async def get_erp_integrations(
        self,
        integration_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get ERP integrations from Oracle FSCM - SI Role Function.
        
        Args:
            integration_name: Optional integration name filter
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of integration records
        """
        try:
            response = await self.rest_client.get_erp_integrations(
                limit=limit,
                offset=offset,
                integration_name=integration_name
            )
            
            if not response.get('success'):
                raise OracleDataError(f"Failed to retrieve ERP integrations: {response.get('error')}")
            
            integrations = []
            for integration_data in response.get('data', []):
                integration = {
                    "id": integration_data.get('IntegrationId', ''),
                    "name": integration_data.get('IntegrationName', ''),
                    "status": integration_data.get('IntegrationStatus', ''),
                    "last_run_date": self._format_oracle_date(integration_data.get('LastRunDate')),
                    "next_run_date": self._format_oracle_date(integration_data.get('NextRunDate')),
                    "source": "oracle_fscm"
                }
                integrations.append(integration)
            
            return integrations
            
        except Exception as e:
            logger.error(f"Error retrieving Oracle ERP integrations: {str(e)}")
            raise OracleDataError(f"Error retrieving Oracle ERP integrations: {str(e)}")
    
    async def _format_ap_invoice_data(self, invoice: Dict[str, Any], include_attachments: bool = False) -> Dict[str, Any]:
        """
        Format Accounts Payable invoice data for consistent output - SI Role Function.
        
        Args:
            invoice: Oracle AP invoice record
            include_attachments: Whether to include attachment data
            
        Returns:
            Formatted invoice data
        """
        try:
            invoice_data = {
                "id": invoice.get('InvoiceId', ''),
                "name": invoice.get('InvoiceNumber', ''),
                "invoice_number": invoice.get('InvoiceNumber', ''),
                "invoice_date": self._format_oracle_date(invoice.get('InvoiceDate')),
                "invoice_amount": float(invoice.get('InvoiceAmount', 0)),
                "currency": invoice.get('InvoiceCurrencyCode', 'USD'),
                "state": self._map_oracle_status(invoice.get('InvoiceStatusLookupCode', '')),
                "payment_status": invoice.get('PaymentStatusLookupCode', ''),
                "move_type": "in_invoice",  # Accounts Payable invoice
                
                # Supplier information
                "partner": {
                    "id": invoice.get('SupplierNumber', ''),
                    "name": invoice.get('SupplierName', ''),
                    "supplier_number": invoice.get('SupplierNumber', ''),
                    "oracle_supplier_id": invoice.get('SupplierId', '')
                },
                
                # Company information (would need additional API call for full details)
                "company": {
                    "oracle_business_unit": invoice.get('BusinessUnit', ''),
                    "oracle_legal_entity": invoice.get('LegalEntity', '')
                },
                
                # Oracle-specific fields
                "oracle_invoice_id": invoice.get('InvoiceId', ''),
                "oracle_invoice_number": invoice.get('InvoiceNumber', ''),
                "oracle_status_code": invoice.get('InvoiceStatusLookupCode', ''),
                "oracle_payment_status": invoice.get('PaymentStatusLookupCode', ''),
                "source": "oracle_ap_invoices",
                
                # Line items would need separate API call
                "invoice_lines": []
            }
            
            # Add attachment information if requested
            if include_attachments:
                # In a real implementation, this would call Oracle attachment services
                invoice_data["attachments"] = []
            
            return invoice_data
            
        except Exception as e:
            logger.error(f"Error formatting Oracle AP invoice data: {str(e)}")
            raise OracleDataError(f"Error formatting Oracle AP invoice data: {str(e)}")
    
    async def _format_ar_receivable_data(self, receivable: Dict[str, Any], include_attachments: bool = False) -> Dict[str, Any]:
        """
        Format Accounts Receivable transaction data for consistent output - SI Role Function.
        
        Args:
            receivable: Oracle AR receivable record
            include_attachments: Whether to include attachment data
            
        Returns:
            Formatted invoice data
        """
        try:
            invoice_data = {
                "id": receivable.get('CustomerTrxId', ''),
                "name": receivable.get('TrxNumber', ''),
                "transaction_number": receivable.get('TrxNumber', ''),
                "transaction_date": self._format_oracle_date(receivable.get('TrxDate')),
                "transaction_amount": float(receivable.get('TrxLineAmount', 0)),
                "currency": receivable.get('InvoiceCurrencyCode', 'USD'),
                "state": "posted",  # AR transactions are typically posted
                "move_type": "out_invoice",  # Accounts Receivable invoice
                "transaction_type": receivable.get('TransactionTypeName', ''),
                
                # Customer information
                "partner": {
                    "id": receivable.get('BillToCustomerNumber', ''),
                    "name": receivable.get('BillToCustomerName', ''),
                    "customer_number": receivable.get('BillToCustomerNumber', ''),
                    "oracle_customer_id": receivable.get('BillToCustomerId', '')
                },
                
                # Company information
                "company": {
                    "oracle_business_unit": receivable.get('BusinessUnit', ''),
                    "oracle_legal_entity": receivable.get('LegalEntity', '')
                },
                
                # Oracle-specific fields
                "oracle_transaction_id": receivable.get('CustomerTrxId', ''),
                "oracle_transaction_number": receivable.get('TrxNumber', ''),
                "oracle_transaction_type_id": receivable.get('TransactionTypeId', ''),
                "oracle_transaction_type": receivable.get('TransactionTypeName', ''),
                "source": "oracle_ar_receivables",
                
                # Line items would need separate API call
                "invoice_lines": []
            }
            
            # Add attachment information if requested
            if include_attachments:
                # In a real implementation, this would call Oracle attachment services
                invoice_data["attachments"] = []
            
            return invoice_data
            
        except Exception as e:
            logger.error(f"Error formatting Oracle AR receivable data: {str(e)}")
            raise OracleDataError(f"Error formatting Oracle AR receivable data: {str(e)}")
    
    def _format_oracle_date(self, oracle_date) -> Optional[str]:
        """Format Oracle date to ISO format."""
        if not oracle_date:
            return None
        
        try:
            # Oracle REST API dates are typically in ISO format already
            if isinstance(oracle_date, str):
                # Handle different Oracle date formats
                if 'T' in oracle_date:
                    # ISO format with time
                    return oracle_date
                else:
                    # Date only, add time
                    return f"{oracle_date}T00:00:00"
            
            # If it's a datetime object, convert to ISO
            if hasattr(oracle_date, 'isoformat'):
                return oracle_date.isoformat()
            
            return str(oracle_date)
            
        except Exception as e:
            logger.warning(f"Error formatting Oracle date {oracle_date}: {str(e)}")
            return str(oracle_date) if oracle_date else None
    
    def _map_oracle_status(self, oracle_status: str) -> str:
        """Map Oracle invoice status to standard status."""
        status_mapping = {
            'VALIDATED': 'posted',
            'APPROVED': 'approved',
            'NEEDS_REVALIDATION': 'draft',
            'CANCELLED': 'cancelled',
            'PAID': 'paid',
            'UNPAID': 'posted',
            'PARTIALLY_PAID': 'partial',
            'REJECTED': 'rejected'
        }
        
        return status_mapping.get(oracle_status, 'unknown')