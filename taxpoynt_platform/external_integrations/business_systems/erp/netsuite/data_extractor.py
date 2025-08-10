"""
NetSuite Data Extraction Module
Handles data extraction and formatting from NetSuite ERP services.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from .exceptions import NetSuiteAPIError, NetSuiteDataError

logger = logging.getLogger(__name__)


class NetSuiteDataExtractor:
    """Handles data extraction and formatting from NetSuite ERP."""
    
    def __init__(self, rest_client):
        """Initialize with a NetSuite REST client instance."""
        self.rest_client = rest_client
    
    async def get_invoices(
        self,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        include_attachments: bool = False,
        data_source: str = 'invoices'
    ) -> List[Dict[str, Any]]:
        """
        Get invoice list from NetSuite ERP - SI Role Function.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            start_date: Filter invoices from this date
            end_date: Filter invoices until this date
            customer_id: Filter by customer ID
            status: Filter by invoice status
            include_attachments: Whether to include attachment information
            data_source: Data source identifier
            
        Returns:
            List of invoice records
        """
        try:
            filters = {}
            
            if start_date:
                filters['start_date'] = start_date.strftime('%Y-%m-%d')
            if end_date:
                filters['end_date'] = end_date.strftime('%Y-%m-%d')
            if customer_id:
                filters['customer_id'] = customer_id
            if status:
                filters['status'] = status
            
            response = await self.rest_client.get_invoices(
                limit=limit,
                offset=offset,
                filters=filters
            )
            
            if not response.get('success'):
                raise NetSuiteDataError(f"Failed to retrieve invoices: {response.get('error')}")
            
            invoices = []
            for invoice_data in response.get('data', []):
                formatted_invoice = await self._format_invoice_data(invoice_data, include_attachments)
                invoices.append(formatted_invoice)
            
            return invoices
            
        except Exception as e:
            logger.error(f"Error retrieving NetSuite invoices: {str(e)}")
            raise NetSuiteDataError(f"Error retrieving NetSuite invoices: {str(e)}")
    
    async def get_invoice_by_id(self, invoice_id: Union[int, str]) -> Dict[str, Any]:
        """
        Get a specific invoice by ID from NetSuite - SI Role Function.
        
        Args:
            invoice_id: The invoice ID to retrieve
            
        Returns:
            Invoice record data
        """
        try:
            response = await self.rest_client.get_invoice_by_id(str(invoice_id))
            if not response.get('success'):
                raise NetSuiteDataError(f"Failed to retrieve invoice {invoice_id}: {response.get('error')}")
            
            return await self._format_invoice_data(response.get('data', {}))
            
        except Exception as e:
            logger.error(f"Error retrieving NetSuite invoice {invoice_id}: {str(e)}")
            raise NetSuiteDataError(f"Error retrieving NetSuite invoice {invoice_id}: {str(e)}")
    
    async def search_invoices(
        self,
        customer_name: Optional[str] = None,
        invoice_number: Optional[str] = None,
        amount_range: Optional[tuple] = None,
        date_range: Optional[tuple] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search invoices with specific criteria - SI Role Function.
        
        Args:
            customer_name: Filter by customer name
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
            
            if customer_name:
                search_criteria['customer_name'] = customer_name
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
                raise NetSuiteDataError(f"Failed to search invoices: {response.get('error')}")
            
            invoices = []
            for invoice_data in response.get('data', []):
                formatted_invoice = await self._format_suiteql_invoice_data(invoice_data)
                invoices.append(formatted_invoice)
            
            return invoices
            
        except Exception as e:
            logger.error(f"Error searching NetSuite invoices: {str(e)}")
            raise NetSuiteDataError(f"Error searching NetSuite invoices: {str(e)}")
    
    async def get_customers(
        self,
        search_term: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get customers from NetSuite - SI Role Function.
        
        Args:
            search_term: Optional search term to filter customers
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of customer records
        """
        try:
            response = await self.rest_client.get_customers(
                limit=limit,
                offset=offset,
                search_term=search_term
            )
            
            if not response.get('success'):
                raise NetSuiteDataError(f"Failed to retrieve customers: {response.get('error')}")
            
            customers = []
            for customer_data in response.get('data', []):
                customer = {
                    "id": customer_data.get('id', ''),
                    "entity_id": customer_data.get('entityId', ''),
                    "company_name": customer_data.get('companyName', ''),
                    "name": customer_data.get('entityId', ''),
                    "email": customer_data.get('email', ''),
                    "phone": customer_data.get('phone', ''),
                    "address": {
                        "address1": customer_data.get('defaultAddress', {}).get('addr1', ''),
                        "address2": customer_data.get('defaultAddress', {}).get('addr2', ''),
                        "city": customer_data.get('defaultAddress', {}).get('city', ''),
                        "state": customer_data.get('defaultAddress', {}).get('state', ''),
                        "zip": customer_data.get('defaultAddress', {}).get('zip', ''),
                        "country": customer_data.get('defaultAddress', {}).get('country', '')
                    },
                    "tax_registration_number": customer_data.get('taxRegNumber', ''),
                    "currency": customer_data.get('currency', ''),
                    "is_inactive": customer_data.get('isInactive', False),
                    "subsidiary": customer_data.get('subsidiary', ''),
                    "source": "netsuite_customers"
                }
                customers.append(customer)
            
            return customers
            
        except Exception as e:
            logger.error(f"Error retrieving NetSuite customers: {str(e)}")
            raise NetSuiteDataError(f"Error retrieving NetSuite customers: {str(e)}")
    
    async def get_vendors(
        self,
        search_term: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get vendors from NetSuite - SI Role Function.
        
        Args:
            search_term: Optional search term to filter vendors
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of vendor records
        """
        try:
            response = await self.rest_client.get_vendors(
                limit=limit,
                offset=offset,
                search_term=search_term
            )
            
            if not response.get('success'):
                raise NetSuiteDataError(f"Failed to retrieve vendors: {response.get('error')}")
            
            vendors = []
            for vendor_data in response.get('data', []):
                vendor = {
                    "id": vendor_data.get('id', ''),
                    "entity_id": vendor_data.get('entityId', ''),
                    "company_name": vendor_data.get('companyName', ''),
                    "name": vendor_data.get('entityId', ''),
                    "email": vendor_data.get('email', ''),
                    "phone": vendor_data.get('phone', ''),
                    "address": {
                        "address1": vendor_data.get('defaultAddress', {}).get('addr1', ''),
                        "address2": vendor_data.get('defaultAddress', {}).get('addr2', ''),
                        "city": vendor_data.get('defaultAddress', {}).get('city', ''),
                        "state": vendor_data.get('defaultAddress', {}).get('state', ''),
                        "zip": vendor_data.get('defaultAddress', {}).get('zip', ''),
                        "country": vendor_data.get('defaultAddress', {}).get('country', '')
                    },
                    "tax_registration_number": vendor_data.get('taxRegNumber', ''),
                    "currency": vendor_data.get('currency', ''),
                    "is_inactive": vendor_data.get('isInactive', False),
                    "subsidiary": vendor_data.get('subsidiary', ''),
                    "source": "netsuite_vendors"
                }
                vendors.append(vendor)
            
            return vendors
            
        except Exception as e:
            logger.error(f"Error retrieving NetSuite vendors: {str(e)}")
            raise NetSuiteDataError(f"Error retrieving NetSuite vendors: {str(e)}")
    
    async def get_items(
        self,
        search_term: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get items from NetSuite - SI Role Function.
        
        Args:
            search_term: Optional search term to filter items
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of item records
        """
        try:
            response = await self.rest_client.get_items(
                limit=limit,
                offset=offset,
                search_term=search_term
            )
            
            if not response.get('success'):
                raise NetSuiteDataError(f"Failed to retrieve items: {response.get('error')}")
            
            items = []
            for item_data in response.get('data', []):
                item = {
                    "id": item_data.get('id', ''),
                    "item_id": item_data.get('itemId', ''),
                    "name": item_data.get('displayName', ''),
                    "description": item_data.get('description', ''),
                    "type": item_data.get('itemType', ''),
                    "base_price": float(item_data.get('basePrice', 0)),
                    "cost": float(item_data.get('cost', 0)),
                    "unit_type": item_data.get('unitsType', ''),
                    "is_inactive": item_data.get('isInactive', False),
                    "subsidiary": item_data.get('subsidiary', ''),
                    "source": "netsuite_items"
                }
                items.append(item)
            
            return items
            
        except Exception as e:
            logger.error(f"Error retrieving NetSuite items: {str(e)}")
            raise NetSuiteDataError(f"Error retrieving NetSuite items: {str(e)}")
    
    async def _format_invoice_data(self, invoice: Dict[str, Any], include_attachments: bool = False) -> Dict[str, Any]:
        """
        Format invoice data for consistent output - SI Role Function.
        
        Args:
            invoice: NetSuite invoice record
            include_attachments: Whether to include attachment data
            
        Returns:
            Formatted invoice data
        """
        try:
            invoice_data = {
                "id": invoice.get('id', ''),
                "name": invoice.get('tranId', ''),
                "invoice_number": invoice.get('tranId', ''),
                "invoice_date": self._format_netsuite_date(invoice.get('tranDate')),
                "due_date": self._format_netsuite_date(invoice.get('dueDate')),
                "amount_excluding_tax": float(invoice.get('subTotal', 0)),
                "amount_including_tax": float(invoice.get('total', 0)),
                "amount_tax": float(invoice.get('taxTotal', 0)),
                "currency": invoice.get('currency', {}).get('name', 'USD'),
                "state": self._map_netsuite_status(invoice.get('status', '')),
                "move_type": "out_invoice",  # NetSuite invoices are sales invoices
                "status": invoice.get('status', ''),
                
                # Customer information
                "partner": {
                    "id": invoice.get('entity', {}).get('id', ''),
                    "name": invoice.get('entity', {}).get('entityId', ''),
                    "company_name": invoice.get('entity', {}).get('companyName', ''),
                    "netsuite_entity_id": invoice.get('entity', {}).get('id', '')
                },
                
                # Company information
                "company": {
                    "netsuite_subsidiary_id": invoice.get('subsidiary', {}).get('id', ''),
                    "subsidiary_name": invoice.get('subsidiary', {}).get('name', '')
                },
                
                # NetSuite-specific fields
                "netsuite_invoice_id": invoice.get('id', ''),
                "netsuite_tran_id": invoice.get('tranId', ''),
                "netsuite_status": invoice.get('status', ''),
                "source": "netsuite_invoices",
                
                # Line items
                "invoice_lines": self._format_invoice_lines(invoice.get('item', []))
            }
            
            # Add attachment information if requested
            if include_attachments:
                # In a real implementation, this would call NetSuite file cabinet services
                invoice_data["attachments"] = []
            
            return invoice_data
            
        except Exception as e:
            logger.error(f"Error formatting NetSuite invoice data: {str(e)}")
            raise NetSuiteDataError(f"Error formatting NetSuite invoice data: {str(e)}")
    
    async def _format_suiteql_invoice_data(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Format SuiteQL invoice data for consistent output."""
        try:
            invoice_data = {
                "id": invoice.get('id', ''),
                "name": invoice.get('tranid', ''),
                "invoice_number": invoice.get('tranid', ''),
                "invoice_date": self._format_netsuite_date(invoice.get('trandate')),
                "due_date": None,  # Not available in basic SuiteQL query
                "amount_excluding_tax": float(invoice.get('total', 0)) * 0.9,  # Approximate
                "amount_including_tax": float(invoice.get('total', 0)),
                "amount_tax": float(invoice.get('total', 0)) * 0.1,  # Approximate
                "currency": invoice.get('currency', 'USD'),
                "state": self._map_netsuite_status(invoice.get('status', '')),
                "move_type": "out_invoice",
                "status": invoice.get('status', ''),
                
                # Customer information
                "partner": {
                    "id": invoice.get('entity', ''),
                    "name": invoice.get('customer_name', ''),
                    "email": invoice.get('customer_email', ''),
                    "netsuite_entity_id": invoice.get('entity', '')
                },
                
                # NetSuite-specific fields
                "netsuite_invoice_id": invoice.get('id', ''),
                "netsuite_tran_id": invoice.get('tranid', ''),
                "netsuite_status": invoice.get('status', ''),
                "source": "netsuite_suiteql",
                
                # Line items would need separate query
                "invoice_lines": []
            }
            
            return invoice_data
            
        except Exception as e:
            logger.error(f"Error formatting NetSuite SuiteQL invoice data: {str(e)}")
            raise NetSuiteDataError(f"Error formatting NetSuite SuiteQL invoice data: {str(e)}")
    
    def _format_invoice_lines(self, line_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format NetSuite invoice line items."""
        formatted_lines = []
        
        for i, line in enumerate(line_items):
            formatted_line = {
                "id": str(line.get('id', i + 1)),
                "line_number": i + 1,
                "item_id": line.get('item', {}).get('id', ''),
                "item_name": line.get('item', {}).get('itemId', ''),
                "description": line.get('description', ''),
                "quantity": float(line.get('quantity', 1)),
                "unit_price": float(line.get('rate', 0)),
                "line_amount": float(line.get('amount', 0)),
                "tax_amount": float(line.get('taxAmount', 0)),
                "tax_code": line.get('taxCode', {}).get('itemId', ''),
                "source": "netsuite_line_items"
            }
            formatted_lines.append(formatted_line)
        
        return formatted_lines
    
    def _format_netsuite_date(self, netsuite_date) -> Optional[str]:
        """Format NetSuite date to ISO format."""
        if not netsuite_date:
            return None
        
        try:
            # NetSuite API dates are typically in ISO format or date objects
            if isinstance(netsuite_date, str):
                # Handle different NetSuite date formats
                if 'T' in netsuite_date:
                    # ISO format with time
                    return netsuite_date
                else:
                    # Date only, add time
                    return f"{netsuite_date}T00:00:00"
            
            # If it's a datetime object, convert to ISO
            if hasattr(netsuite_date, 'isoformat'):
                return netsuite_date.isoformat()
            
            return str(netsuite_date)
            
        except Exception as e:
            logger.warning(f"Error formatting NetSuite date {netsuite_date}: {str(e)}")
            return str(netsuite_date) if netsuite_date else None
    
    def _map_netsuite_status(self, netsuite_status: str) -> str:
        """Map NetSuite invoice status to standard status."""
        status_mapping = {
            'Open': 'posted',
            'Paid In Full': 'paid',
            'Partially Paid': 'partial',
            'Pending Approval': 'draft',
            'Rejected': 'cancelled',
            'Voided': 'cancelled',
            'Pending Billing': 'draft'
        }
        
        return status_mapping.get(netsuite_status, 'unknown')