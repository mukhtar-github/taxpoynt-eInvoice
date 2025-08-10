"""
Microsoft Dynamics Data Extraction Module
Handles data extraction and formatting from Microsoft Dynamics 365 services.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from .exceptions import DynamicsAPIError, DynamicsDataError

logger = logging.getLogger(__name__)


class DynamicsDataExtractor:
    """Handles data extraction and formatting from Microsoft Dynamics 365."""
    
    def __init__(self, rest_client):
        """Initialize with a Dynamics REST client instance."""
        self.rest_client = rest_client
    
    async def get_invoices(
        self,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        customer_number: Optional[str] = None,
        vendor_number: Optional[str] = None,
        status: Optional[str] = None,
        include_attachments: bool = False,
        data_source: str = 'sales_invoices'  # 'sales_invoices' or 'purchase_invoices'
    ) -> List[Dict[str, Any]]:
        """
        Get invoice list from Microsoft Dynamics 365 - SI Role Function.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            start_date: Filter invoices from this date
            end_date: Filter invoices until this date
            customer_number: Filter by customer number
            vendor_number: Filter by vendor number
            status: Filter by invoice status
            include_attachments: Whether to include attachment information
            data_source: Data source ('sales_invoices' or 'purchase_invoices')
            
        Returns:
            List of invoice records
        """
        try:
            if data_source == 'sales_invoices':
                return await self._get_sales_invoices(
                    limit, offset, start_date, end_date, customer_number, status, include_attachments
                )
            elif data_source == 'purchase_invoices':
                return await self._get_purchase_invoices(
                    limit, offset, start_date, end_date, vendor_number, status, include_attachments
                )
            else:
                raise DynamicsDataError(f"Unknown data source: {data_source}")
                
        except Exception as e:
            logger.error(f"Error retrieving Dynamics invoices: {str(e)}")
            raise DynamicsDataError(f"Error retrieving Dynamics invoices: {str(e)}")
    
    async def _get_sales_invoices(
        self,
        limit: int,
        offset: int,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        customer_number: Optional[str],
        status: Optional[str],
        include_attachments: bool
    ) -> List[Dict[str, Any]]:
        """Get sales invoices from Dynamics Business Central."""
        try:
            filters = {}
            
            if start_date:
                filters['start_date'] = start_date.strftime('%Y-%m-%d')
            if end_date:
                filters['end_date'] = end_date.strftime('%Y-%m-%d')
            if customer_number:
                filters['customer_number'] = customer_number
            if status:
                filters['status'] = status
            
            response = await self.rest_client.get_sales_invoices(
                limit=limit,
                offset=offset,
                filters=filters
            )
            
            if not response.get('success'):
                raise DynamicsDataError(f"Failed to retrieve sales invoices: {response.get('error')}")
            
            invoices = []
            for invoice_data in response.get('data', []):
                formatted_invoice = await self._format_sales_invoice_data(invoice_data, include_attachments)
                invoices.append(formatted_invoice)
            
            return invoices
            
        except Exception as e:
            logger.error(f"Error retrieving sales invoices: {str(e)}")
            raise DynamicsDataError(f"Error retrieving sales invoices: {str(e)}")
    
    async def _get_purchase_invoices(
        self,
        limit: int,
        offset: int,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        vendor_number: Optional[str],
        status: Optional[str],
        include_attachments: bool
    ) -> List[Dict[str, Any]]:
        """Get purchase invoices from Dynamics Business Central."""
        try:
            filters = {}
            
            if start_date:
                filters['start_date'] = start_date.strftime('%Y-%m-%d')
            if end_date:
                filters['end_date'] = end_date.strftime('%Y-%m-%d')
            if vendor_number:
                filters['vendor_number'] = vendor_number
            if status:
                filters['status'] = status
            
            response = await self.rest_client.get_purchase_invoices(
                limit=limit,
                offset=offset,
                filters=filters
            )
            
            if not response.get('success'):
                raise DynamicsDataError(f"Failed to retrieve purchase invoices: {response.get('error')}")
            
            invoices = []
            for invoice_data in response.get('data', []):
                formatted_invoice = await self._format_purchase_invoice_data(invoice_data, include_attachments)
                invoices.append(formatted_invoice)
            
            return invoices
            
        except Exception as e:
            logger.error(f"Error retrieving purchase invoices: {str(e)}")
            raise DynamicsDataError(f"Error retrieving purchase invoices: {str(e)}")
    
    async def get_invoice_by_id(self, invoice_id: Union[int, str], invoice_type: str = 'sales') -> Dict[str, Any]:
        """
        Get a specific invoice by ID from Dynamics 365 - SI Role Function.
        
        Args:
            invoice_id: The invoice ID to retrieve
            invoice_type: Type of invoice ('sales' or 'purchase')
            
        Returns:
            Invoice record data
        """
        try:
            if invoice_type == 'sales':
                response = await self.rest_client.get_sales_invoice_by_id(str(invoice_id))
                if not response.get('success'):
                    raise DynamicsDataError(f"Failed to retrieve sales invoice {invoice_id}: {response.get('error')}")
                return await self._format_sales_invoice_data(response.get('data', {}))
            else:
                response = await self.rest_client.get_purchase_invoice_by_id(str(invoice_id))
                if not response.get('success'):
                    raise DynamicsDataError(f"Failed to retrieve purchase invoice {invoice_id}: {response.get('error')}")
                return await self._format_purchase_invoice_data(response.get('data', {}))
            
        except Exception as e:
            logger.error(f"Error retrieving Dynamics invoice {invoice_id}: {str(e)}")
            raise DynamicsDataError(f"Error retrieving Dynamics invoice {invoice_id}: {str(e)}")
    
    async def search_invoices(
        self,
        customer_name: Optional[str] = None,
        vendor_name: Optional[str] = None,
        invoice_number: Optional[str] = None,
        amount_range: Optional[tuple] = None,
        date_range: Optional[tuple] = None,
        status: Optional[str] = None,
        invoice_type: str = 'sales',
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search invoices with specific criteria - SI Role Function.
        
        Args:
            customer_name: Filter by customer name
            vendor_name: Filter by vendor name
            invoice_number: Filter by invoice number
            amount_range: Tuple of (min_amount, max_amount)
            date_range: Tuple of (start_date, end_date)
            status: Filter by invoice status
            invoice_type: Type of invoice ('sales' or 'purchase')
            limit: Maximum number of records to return
            
        Returns:
            List of matching invoice records
        """
        try:
            search_criteria = {}
            
            if customer_name:
                search_criteria['customer_name'] = customer_name
            if vendor_name:
                search_criteria['vendor_name'] = vendor_name
            if invoice_number:
                search_criteria['invoice_number'] = invoice_number
            if amount_range:
                search_criteria['amount_range'] = amount_range
            if date_range:
                search_criteria['date_range'] = date_range
            if status:
                search_criteria['status'] = status
            
            response = await self.rest_client.search_invoices(search_criteria, limit, invoice_type)
            
            if not response.get('success'):
                raise DynamicsDataError(f"Failed to search invoices: {response.get('error')}")
            
            invoices = []
            for invoice_data in response.get('data', []):
                if invoice_type == 'sales':
                    formatted_invoice = await self._format_sales_invoice_data(invoice_data, include_attachments=False)
                else:
                    formatted_invoice = await self._format_purchase_invoice_data(invoice_data, include_attachments=False)
                invoices.append(formatted_invoice)
            
            return invoices
            
        except Exception as e:
            logger.error(f"Error searching Dynamics invoices: {str(e)}")
            raise DynamicsDataError(f"Error searching Dynamics invoices: {str(e)}")
    
    async def get_customers(
        self,
        search_term: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get customers from Dynamics Business Central - SI Role Function.
        
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
                raise DynamicsDataError(f"Failed to retrieve customers: {response.get('error')}")
            
            customers = []
            for customer_data in response.get('data', []):
                customer = {
                    "id": customer_data.get('id', ''),
                    "number": customer_data.get('number', ''),
                    "name": customer_data.get('displayName', ''),
                    "email": customer_data.get('email', ''),
                    "phone": customer_data.get('phoneNumber', ''),
                    "address": customer_data.get('address', {}),
                    "tax_registration_number": customer_data.get('taxRegistrationNumber', ''),
                    "currency_code": customer_data.get('currencyCode', ''),
                    "blocked": customer_data.get('blocked', ''),
                    "source": "dynamics_business_central"
                }
                customers.append(customer)
            
            return customers
            
        except Exception as e:
            logger.error(f"Error retrieving Dynamics customers: {str(e)}")
            raise DynamicsDataError(f"Error retrieving Dynamics customers: {str(e)}")
    
    async def get_vendors(
        self,
        search_term: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get vendors from Dynamics Business Central - SI Role Function.
        
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
                raise DynamicsDataError(f"Failed to retrieve vendors: {response.get('error')}")
            
            vendors = []
            for vendor_data in response.get('data', []):
                vendor = {
                    "id": vendor_data.get('id', ''),
                    "number": vendor_data.get('number', ''),
                    "name": vendor_data.get('displayName', ''),
                    "email": vendor_data.get('email', ''),
                    "phone": vendor_data.get('phoneNumber', ''),
                    "address": vendor_data.get('address', {}),
                    "tax_registration_number": vendor_data.get('taxRegistrationNumber', ''),
                    "currency_code": vendor_data.get('currencyCode', ''),
                    "blocked": vendor_data.get('blocked', ''),
                    "source": "dynamics_business_central"
                }
                vendors.append(vendor)
            
            return vendors
            
        except Exception as e:
            logger.error(f"Error retrieving Dynamics vendors: {str(e)}")
            raise DynamicsDataError(f"Error retrieving Dynamics vendors: {str(e)}")
    
    async def get_items(
        self,
        search_term: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get items from Dynamics Business Central - SI Role Function.
        
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
                raise DynamicsDataError(f"Failed to retrieve items: {response.get('error')}")
            
            items = []
            for item_data in response.get('data', []):
                item = {
                    "id": item_data.get('id', ''),
                    "number": item_data.get('number', ''),
                    "name": item_data.get('displayName', ''),
                    "description": item_data.get('description', ''),
                    "type": item_data.get('type', ''),
                    "base_unit_of_measure": item_data.get('baseUnitOfMeasure', {}),
                    "unit_price": item_data.get('unitPrice', 0),
                    "unit_cost": item_data.get('unitCost', 0),
                    "inventory": item_data.get('inventory', 0),
                    "blocked": item_data.get('blocked', False),
                    "source": "dynamics_business_central"
                }
                items.append(item)
            
            return items
            
        except Exception as e:
            logger.error(f"Error retrieving Dynamics items: {str(e)}")
            raise DynamicsDataError(f"Error retrieving Dynamics items: {str(e)}")
    
    async def _format_sales_invoice_data(self, invoice: Dict[str, Any], include_attachments: bool = False) -> Dict[str, Any]:
        """
        Format sales invoice data for consistent output - SI Role Function.
        
        Args:
            invoice: Dynamics sales invoice record
            include_attachments: Whether to include attachment data
            
        Returns:
            Formatted invoice data
        """
        try:
            invoice_data = {
                "id": invoice.get('id', ''),
                "name": invoice.get('number', ''),
                "invoice_number": invoice.get('number', ''),
                "invoice_date": self._format_dynamics_date(invoice.get('invoiceDate')),
                "posting_date": self._format_dynamics_date(invoice.get('postingDate')),
                "due_date": self._format_dynamics_date(invoice.get('dueDate')),
                "amount_excluding_tax": float(invoice.get('totalAmountExcludingTax', 0)),
                "amount_including_tax": float(invoice.get('totalAmountIncludingTax', 0)),
                "amount_tax": float(invoice.get('totalTaxAmount', 0)),
                "currency": invoice.get('currencyCode', 'USD'),
                "state": self._map_dynamics_status(invoice.get('status', '')),
                "move_type": "out_invoice",  # Sales invoice
                "status": invoice.get('status', ''),
                
                # Customer information
                "partner": {
                    "id": invoice.get('customerId', ''),
                    "name": invoice.get('customerName', ''),
                    "number": invoice.get('customerNumber', ''),
                    "dynamics_customer_id": invoice.get('customerId', '')
                },
                
                # Company information
                "company": {
                    "dynamics_company_id": invoice.get('companyId', ''),
                    "dynamics_environment": self.rest_client.authenticator.environment
                },
                
                # Dynamics-specific fields
                "dynamics_invoice_id": invoice.get('id', ''),
                "dynamics_invoice_number": invoice.get('number', ''),
                "dynamics_status": invoice.get('status', ''),
                "source": "dynamics_sales_invoices",
                
                # Line items would need separate API call
                "invoice_lines": []
            }
            
            # Add attachment information if requested
            if include_attachments:
                # In a real implementation, this would call Dynamics attachment services
                invoice_data["attachments"] = []
            
            return invoice_data
            
        except Exception as e:
            logger.error(f"Error formatting Dynamics sales invoice data: {str(e)}")
            raise DynamicsDataError(f"Error formatting Dynamics sales invoice data: {str(e)}")
    
    async def _format_purchase_invoice_data(self, invoice: Dict[str, Any], include_attachments: bool = False) -> Dict[str, Any]:
        """
        Format purchase invoice data for consistent output - SI Role Function.
        
        Args:
            invoice: Dynamics purchase invoice record
            include_attachments: Whether to include attachment data
            
        Returns:
            Formatted invoice data
        """
        try:
            invoice_data = {
                "id": invoice.get('id', ''),
                "name": invoice.get('number', ''),
                "invoice_number": invoice.get('number', ''),
                "invoice_date": self._format_dynamics_date(invoice.get('invoiceDate')),
                "posting_date": self._format_dynamics_date(invoice.get('postingDate')),
                "due_date": self._format_dynamics_date(invoice.get('dueDate')),
                "amount_excluding_tax": float(invoice.get('totalAmountExcludingTax', 0)),
                "amount_including_tax": float(invoice.get('totalAmountIncludingTax', 0)),
                "amount_tax": float(invoice.get('totalTaxAmount', 0)),
                "currency": invoice.get('currencyCode', 'USD'),
                "state": self._map_dynamics_status(invoice.get('status', '')),
                "move_type": "in_invoice",  # Purchase invoice
                "status": invoice.get('status', ''),
                
                # Vendor information
                "partner": {
                    "id": invoice.get('vendorId', ''),
                    "name": invoice.get('vendorName', ''),
                    "number": invoice.get('vendorNumber', ''),
                    "dynamics_vendor_id": invoice.get('vendorId', '')
                },
                
                # Company information
                "company": {
                    "dynamics_company_id": invoice.get('companyId', ''),
                    "dynamics_environment": self.rest_client.authenticator.environment
                },
                
                # Dynamics-specific fields
                "dynamics_invoice_id": invoice.get('id', ''),
                "dynamics_invoice_number": invoice.get('number', ''),
                "dynamics_status": invoice.get('status', ''),
                "source": "dynamics_purchase_invoices",
                
                # Line items would need separate API call
                "invoice_lines": []
            }
            
            # Add attachment information if requested
            if include_attachments:
                # In a real implementation, this would call Dynamics attachment services
                invoice_data["attachments"] = []
            
            return invoice_data
            
        except Exception as e:
            logger.error(f"Error formatting Dynamics purchase invoice data: {str(e)}")
            raise DynamicsDataError(f"Error formatting Dynamics purchase invoice data: {str(e)}")
    
    def _format_dynamics_date(self, dynamics_date) -> Optional[str]:
        """Format Dynamics date to ISO format."""
        if not dynamics_date:
            return None
        
        try:
            # Dynamics API dates are typically in ISO format already
            if isinstance(dynamics_date, str):
                # Handle different Dynamics date formats
                if 'T' in dynamics_date:
                    # ISO format with time
                    return dynamics_date
                else:
                    # Date only, add time
                    return f"{dynamics_date}T00:00:00"
            
            # If it's a datetime object, convert to ISO
            if hasattr(dynamics_date, 'isoformat'):
                return dynamics_date.isoformat()
            
            return str(dynamics_date)
            
        except Exception as e:
            logger.warning(f"Error formatting Dynamics date {dynamics_date}: {str(e)}")
            return str(dynamics_date) if dynamics_date else None
    
    def _map_dynamics_status(self, dynamics_status: str) -> str:
        """Map Dynamics invoice status to standard status."""
        status_mapping = {
            'Draft': 'draft',
            'In Review': 'draft',
            'Open': 'posted',
            'Paid': 'paid',
            'Canceled': 'cancelled',
            'Corrective': 'corrective',
            'Partially Paid': 'partial'
        }
        
        return status_mapping.get(dynamics_status, 'unknown')