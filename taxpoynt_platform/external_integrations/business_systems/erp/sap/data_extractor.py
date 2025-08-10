"""
SAP Data Extraction Module
Handles data extraction and formatting from SAP ERP services.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from .exceptions import SAPODataError

logger = logging.getLogger(__name__)


class SAPDataExtractor:
    """Handles data extraction and formatting from SAP ERP."""
    
    def __init__(self, odata_client):
        """Initialize with a SAP OData client instance."""
        self.odata_client = odata_client
    
    async def get_invoices(
        self,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        document_type: Optional[str] = None,
        include_attachments: bool = False,
        data_source: str = 'billing'
    ) -> List[Dict[str, Any]]:
        """
        Get invoice list from SAP ERP - SI Role Function.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            start_date: Filter invoices from this date
            end_date: Filter invoices until this date
            document_type: Filter by document type
            include_attachments: Whether to include attachment information
            data_source: Data source ('billing' or 'journal')
            
        Returns:
            List of invoice records
        """
        try:
            if data_source == 'billing':
                return await self._get_invoices_from_billing_api(
                    limit, offset, start_date, end_date, document_type, include_attachments
                )
            elif data_source == 'journal':
                return await self._get_invoices_from_journal_api(
                    limit, offset, start_date, end_date, document_type, include_attachments
                )
            else:
                raise SAPODataError(f"Unknown data source: {data_source}")
                
        except Exception as e:
            logger.error(f"Error retrieving invoices: {str(e)}")
            raise SAPODataError(f"Error retrieving invoices: {str(e)}")
    
    async def _get_invoices_from_billing_api(
        self,
        limit: int,
        offset: int,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        document_type: Optional[str],
        include_attachments: bool
    ) -> List[Dict[str, Any]]:
        """Get invoices from SAP Billing Document API."""
        try:
            filters = {}
            
            if start_date:
                filters['start_date'] = start_date.isoformat()
            if end_date:
                filters['end_date'] = end_date.isoformat()
            if document_type:
                filters['document_type'] = document_type
            
            response = await self.odata_client.get_billing_documents(
                limit=limit,
                offset=offset,
                filters=filters
            )
            
            if not response.get('success'):
                raise SAPODataError(f"Failed to retrieve billing documents: {response.get('error')}")
            
            invoices = []
            for doc in response.get('data', []):
                invoice_data = await self._format_billing_document_data(doc, include_attachments)
                invoices.append(invoice_data)
            
            return invoices
            
        except Exception as e:
            logger.error(f"Error retrieving invoices from billing API: {str(e)}")
            raise SAPODataError(f"Error retrieving invoices from billing API: {str(e)}")
    
    async def _get_invoices_from_journal_api(
        self,
        limit: int,
        offset: int,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        document_type: Optional[str],
        include_attachments: bool
    ) -> List[Dict[str, Any]]:
        """Get invoices from SAP Journal Entry API."""
        try:
            filters = {}
            
            if start_date:
                filters['start_date'] = start_date.isoformat()
            if end_date:
                filters['end_date'] = end_date.isoformat()
            if document_type:
                filters['document_type'] = document_type
            
            response = await self.odata_client.get_journal_entries(
                limit=limit,
                offset=offset,
                filters=filters
            )
            
            if not response.get('success'):
                raise SAPODataError(f"Failed to retrieve journal entries: {response.get('error')}")
            
            # Group journal entries by document
            grouped_entries = self._group_journal_entries_by_document(response.get('data', []))
            
            invoices = []
            for doc_key, entries in grouped_entries.items():
                invoice_data = await self._format_journal_entry_data(entries, include_attachments)
                invoices.append(invoice_data)
            
            return invoices
            
        except Exception as e:
            logger.error(f"Error retrieving invoices from journal API: {str(e)}")
            raise SAPODataError(f"Error retrieving invoices from journal API: {str(e)}")
    
    async def get_invoice_by_id(self, invoice_id: Union[int, str]) -> Dict[str, Any]:
        """
        Get a specific invoice by ID from SAP ERP - SI Role Function.
        
        Args:
            invoice_id: The invoice ID to retrieve
            
        Returns:
            Invoice record data
        """
        try:
            response = await self.odata_client.get_billing_document_by_id(str(invoice_id))
            
            if not response.get('success'):
                raise SAPODataError(f"Failed to retrieve invoice {invoice_id}: {response.get('error')}")
            
            return await self._format_billing_document_data(response.get('data', {}))
            
        except Exception as e:
            logger.error(f"Error retrieving invoice {invoice_id}: {str(e)}")
            raise SAPODataError(f"Error retrieving invoice {invoice_id}: {str(e)}")
    
    async def search_invoices(
        self,
        customer_name: Optional[str] = None,
        invoice_number: Optional[str] = None,
        amount_range: Optional[tuple] = None,
        date_range: Optional[tuple] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search invoices with specific criteria - SI Role Function.
        
        Args:
            customer_name: Filter by customer name
            invoice_number: Filter by invoice number
            amount_range: Tuple of (min_amount, max_amount)
            date_range: Tuple of (start_date, end_date)
            limit: Maximum number of records to return
            
        Returns:
            List of matching invoice records
        """
        try:
            search_criteria = {}
            
            if customer_name:
                search_criteria['customer_name'] = customer_name
            if invoice_number:
                search_criteria['document_number'] = invoice_number
            if amount_range:
                search_criteria['amount_range'] = amount_range
            if date_range:
                search_criteria['date_range'] = date_range
            
            response = await self.odata_client.search_documents(search_criteria, limit)
            
            if not response.get('success'):
                raise SAPODataError(f"Failed to search invoices: {response.get('error')}")
            
            invoices = []
            for doc in response.get('data', []):
                invoice_data = await self._format_billing_document_data(doc, include_attachments=False)
                invoices.append(invoice_data)
            
            return invoices
            
        except Exception as e:
            logger.error(f"Error searching invoices: {str(e)}")
            raise SAPODataError(f"Error searching invoices: {str(e)}")
    
    async def get_partners(
        self,
        search_term: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get business partners from SAP ERP - SI Role Function.
        
        Args:
            search_term: Optional search term to filter partners
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of partner records
        """
        try:
            response = await self.odata_client.get_business_partners(
                limit=limit,
                offset=offset,
                search_term=search_term
            )
            
            if not response.get('success'):
                raise SAPODataError(f"Failed to retrieve partners: {response.get('error')}")
            
            partners = []
            for partner_data in response.get('data', []):
                partner = {
                    "id": partner_data.get('BusinessPartner', ''),
                    "name": partner_data.get('BusinessPartnerName', ''),
                    "category": partner_data.get('BusinessPartnerCategory', ''),
                    "is_customer": bool(partner_data.get('Customer')),
                    "is_supplier": bool(partner_data.get('Supplier')),
                    "tax_number_1": partner_data.get('TaxNumber1', ''),
                    "tax_number_2": partner_data.get('TaxNumber2', ''),
                    "source": "sap_business_partner"
                }
                partners.append(partner)
            
            return partners
            
        except Exception as e:
            logger.error(f"Error retrieving partners: {str(e)}")
            raise SAPODataError(f"Error retrieving partners: {str(e)}")
    
    async def _format_billing_document_data(self, invoice: Dict[str, Any], include_attachments: bool = False) -> Dict[str, Any]:
        """
        Format billing document data for consistent output - SI Role Function.
        
        Args:
            invoice: SAP billing document record
            include_attachments: Whether to include attachment data
            
        Returns:
            Formatted invoice data
        """
        try:
            invoice_data = {
                "id": invoice.get('BillingDocument', ''),
                "name": invoice.get('BillingDocument', ''),
                "invoice_date": self._format_sap_date(invoice.get('BillingDocumentDate')),
                "document_type": invoice.get('BillingDocumentType', ''),
                "state": "posted",  # SAP billing documents are typically posted
                "move_type": "out_invoice",
                "currency": invoice.get('TransactionCurrency', 'EUR'),
                "amount_untaxed": float(invoice.get('NetAmount', 0)),
                "amount_tax": float(invoice.get('TaxAmount', 0)),
                "amount_total": float(invoice.get('TotalAmount', 0)),
                
                # Partner information
                "partner": {
                    "id": invoice.get('SoldToParty', ''),
                    "name": invoice.get('SoldToPartyName', ''),  # May not be available
                    "sap_customer_number": invoice.get('SoldToParty', '')
                },
                
                # Company information
                "company": {
                    "sap_company_code": invoice.get('CompanyCode', ''),
                    "sales_organization": invoice.get('SalesOrganization', '')
                },
                
                # SAP-specific fields
                "sap_document_type": invoice.get('BillingDocumentType', ''),
                "sap_billing_document": invoice.get('BillingDocument', ''),
                "source": "sap_billing_api",
                
                # Line items would need separate API call
                "invoice_lines": []
            }
            
            # Add attachment information if requested
            if include_attachments:
                # In a real implementation, this would call SAP attachment services
                invoice_data["attachments"] = []
            
            return invoice_data
            
        except Exception as e:
            logger.error(f"Error formatting billing document data: {str(e)}")
            raise SAPODataError(f"Error formatting billing document data: {str(e)}")
    
    async def _format_journal_entry_data(self, entries: List[Dict[str, Any]], include_attachments: bool = False) -> Dict[str, Any]:
        """
        Format journal entry data for consistent output - SI Role Function.
        
        Args:
            entries: List of SAP journal entry records for the same document
            include_attachments: Whether to include attachment data
            
        Returns:
            Formatted invoice data
        """
        try:
            if not entries:
                return {}
            
            # Use the first entry for header information
            first_entry = entries[0]
            
            # Calculate totals from line items
            total_debit = sum(float(entry.get('AmountInCompanyCodeCurrency', 0)) 
                            for entry in entries 
                            if float(entry.get('AmountInCompanyCodeCurrency', 0)) > 0)
            
            total_credit = sum(abs(float(entry.get('AmountInCompanyCodeCurrency', 0))) 
                             for entry in entries 
                             if float(entry.get('AmountInCompanyCodeCurrency', 0)) < 0)
            
            invoice_data = {
                "id": f"{first_entry.get('CompanyCode', '')}-{first_entry.get('AccountingDocument', '')}-{first_entry.get('FiscalYear', '')}",
                "name": first_entry.get('AccountingDocument', ''),
                "invoice_date": self._format_sap_date(first_entry.get('PostingDate')),
                "document_date": self._format_sap_date(first_entry.get('DocumentDate')),
                "document_type": first_entry.get('AccountingDocumentType', ''),
                "state": "posted",
                "move_type": "journal_entry",
                "currency": first_entry.get('CompanyCodeCurrency', 'EUR'),
                "amount_total": total_debit,
                "amount_debit": total_debit,
                "amount_credit": total_credit,
                
                # Partner information (if available)
                "partner": {
                    "id": first_entry.get('BusinessPartner', ''),
                    "sap_business_partner": first_entry.get('BusinessPartner', '')
                },
                
                # Company information
                "company": {
                    "sap_company_code": first_entry.get('CompanyCode', ''),
                    "fiscal_year": first_entry.get('FiscalYear', '')
                },
                
                # SAP-specific fields
                "sap_document_type": first_entry.get('AccountingDocumentType', ''),
                "sap_accounting_document": first_entry.get('AccountingDocument', ''),
                "sap_fiscal_year": first_entry.get('FiscalYear', ''),
                "sap_company_code": first_entry.get('CompanyCode', ''),
                "source": "sap_journal_api",
                
                # Journal entry lines
                "journal_lines": []
            }
            
            # Add journal entry lines
            for entry in entries:
                line_data = {
                    "gl_account": entry.get('GLAccount', ''),
                    "business_partner": entry.get('BusinessPartner', ''),
                    "amount": float(entry.get('AmountInCompanyCodeCurrency', 0)),
                    "currency": entry.get('CompanyCodeCurrency', 'EUR'),
                    "debit_credit_indicator": "D" if float(entry.get('AmountInCompanyCodeCurrency', 0)) > 0 else "C"
                }
                invoice_data["journal_lines"].append(line_data)
            
            # Add attachment information if requested
            if include_attachments:
                # In a real implementation, this would call SAP attachment services
                invoice_data["attachments"] = []
            
            return invoice_data
            
        except Exception as e:
            logger.error(f"Error formatting journal entry data: {str(e)}")
            raise SAPODataError(f"Error formatting journal entry data: {str(e)}")
    
    def _group_journal_entries_by_document(self, entries: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group journal entries by document number."""
        grouped = {}
        
        for entry in entries:
            key = f"{entry.get('CompanyCode', '')}-{entry.get('AccountingDocument', '')}-{entry.get('FiscalYear', '')}"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(entry)
        
        return grouped
    
    def _format_sap_date(self, sap_date) -> Optional[str]:
        """Format SAP date to ISO format."""
        if not sap_date:
            return None
        
        try:
            # SAP OData dates are typically in format "/Date(1234567890000)/"
            if isinstance(sap_date, str) and sap_date.startswith('/Date('):
                timestamp_str = sap_date[6:-2]  # Extract timestamp
                timestamp = int(timestamp_str) / 1000  # Convert to seconds
                return datetime.fromtimestamp(timestamp).isoformat()
            
            # If it's already a datetime string, return as is
            if isinstance(sap_date, str):
                return sap_date
            
            # If it's a datetime object, convert to ISO
            if hasattr(sap_date, 'isoformat'):
                return sap_date.isoformat()
            
            return str(sap_date)
            
        except Exception as e:
            logger.warning(f"Error formatting SAP date {sap_date}: {str(e)}")
            return str(sap_date) if sap_date else None