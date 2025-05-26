"""
OdooConnector class for TaxPoynt eInvoice.

This module provides a reusable connector class for Odoo integration.
"""
import logging
import ssl
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

import odoorpc

from app.schemas.integration import OdooAuthMethod, OdooConfig
from app.core.config import settings

logger = logging.getLogger(__name__)


class OdooConnectorError(Exception):
    """Base exception for OdooConnector errors."""
    pass


class OdooConnectionError(OdooConnectorError):
    """Exception raised for connection errors."""
    pass


class OdooAuthenticationError(OdooConnectorError):
    """Exception raised for authentication errors."""
    pass


class OdooDataError(OdooConnectorError):
    """Exception raised for data retrieval errors."""
    pass


class OdooConnector:
    """
    Connector class for Odoo integration using OdooRPC.
    
    This class provides methods for connecting to Odoo, authenticating,
    and retrieving data with proper error handling and connection management.
    """
    
    def __init__(self, config: OdooConfig):
        """
        Initialize the OdooConnector with configuration.
        
        Args:
            config: Odoo configuration parameters
        """
        self.config = config
        self.odoo = None
        self.version_info = None
        self.major_version = None
        self._parse_url()
    
    def _parse_url(self):
        """Parse the Odoo URL to extract host, protocol, and port."""
        parsed_url = urlparse(str(self.config.url))
        self.host = parsed_url.netloc.split(':')[0]
        self.protocol = parsed_url.scheme or 'jsonrpc'
        
        # Determine port (default is 8069 unless specified)
        self.port = 443 if self.protocol == 'jsonrpc+ssl' else 8069
        if ':' in parsed_url.netloc:
            try:
                self.port = int(parsed_url.netloc.split(':')[1])
            except (IndexError, ValueError):
                pass
    
    def connect(self) -> odoorpc.ODOO:
        """
        Connect to the Odoo server.
        
        Returns:
            odoorpc.ODOO: Connected OdooRPC instance
            
        Raises:
            OdooConnectionError: If connection fails
        """
        try:
            # Initialize OdooRPC connection
            self.odoo = odoorpc.ODOO(self.host, protocol=self.protocol, port=self.port)
            return self.odoo
        except Exception as e:
            logger.error(f"Failed to connect to Odoo: {str(e)}")
            raise OdooConnectionError(f"Failed to connect to Odoo: {str(e)}")
    
    def authenticate(self) -> odoorpc.ODOO:
        """
        Authenticate with the Odoo server.
        
        Returns:
            odoorpc.ODOO: Authenticated OdooRPC instance
            
        Raises:
            OdooAuthenticationError: If authentication fails
        """
        try:
            if not self.odoo:
                self.connect()
            
            # Determine auth method and credentials
            password_or_key = (
                self.config.password 
                if self.config.auth_method == OdooAuthMethod.PASSWORD 
                else self.config.api_key
            )
            
            # Login to Odoo
            self.odoo.login(self.config.database, self.config.username, password_or_key)
            
            # Get version information
            self.version_info = self.odoo.version
            self.major_version = int(self.version_info.get('server_version_info', [0])[0])
            
            logger.info(f"Successfully authenticated with Odoo server as user {self.odoo.env.user.name}")
            return self.odoo
        
        except odoorpc.error.RPCError as e:
            logger.error(f"Odoo RPC Authentication error: {str(e)}")
            raise OdooAuthenticationError(f"Odoo RPC Authentication error: {str(e)}")
        except odoorpc.error.InternalError as e:
            logger.error(f"Odoo Internal Authentication error: {str(e)}")
            raise OdooAuthenticationError(f"Odoo Internal Authentication error: {str(e)}")
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise OdooAuthenticationError(f"Authentication error: {str(e)}")
    
    def ensure_connected(func):
        """
        Decorator to ensure the connector is connected and authenticated.
        """
        def wrapper(self, *args, **kwargs):
            try:
                if not self.odoo or not self.odoo.env:
                    self.authenticate()
                return func(self, *args, **kwargs)
            except (odoorpc.error.RPCError, odoorpc.error.InternalError) as e:
                # Handle session timeout by trying to reconnect once
                logger.warning(f"OdooRPC connection error, attempting to reconnect: {str(e)}")
                try:
                    self.authenticate()
                    return func(self, *args, **kwargs)
                except Exception as e2:
                    logger.error(f"Failed to reconnect to Odoo: {str(e2)}")
                    raise
            except Exception as e:
                logger.error(f"Error in OdooConnector: {str(e)}")
                raise
        return wrapper
    
    @ensure_connected
    def get_user_info(self) -> Dict[str, Any]:
        """
        Get information about the authenticated user.
        
        Returns:
            Dict with user information
        """
        user = self.odoo.env.user
        return {
            "id": user.id,
            "name": user.name,
            "login": user.login,
            "email": user.email if hasattr(user, "email") else None,
            "company_id": user.company_id.id if hasattr(user, "company_id") else None,
            "company_name": user.company_id.name if hasattr(user, "company_id") else None
        }
        
    @ensure_connected
    def get_company_info(self) -> Dict[str, Any]:
        """
        Get information about the company associated with the authenticated user.
        
        Returns:
            Dict with company information
        """
        try:
            company = self.odoo.env.user.company_id
            # Get company logo if available
            logo_data = None
            if hasattr(company, 'logo') and company.logo:
                logo_data = company.logo
                
            # Get company address if available
            address = {}
            if hasattr(company, 'street'):
                address['street'] = company.street
            if hasattr(company, 'street2'):
                address['street2'] = company.street2
            if hasattr(company, 'city'):
                address['city'] = company.city
            if hasattr(company, 'state_id') and company.state_id:
                address['state'] = company.state_id.name
            if hasattr(company, 'zip'):
                address['zip'] = company.zip
            if hasattr(company, 'country_id') and company.country_id:
                address['country'] = company.country_id.name
                
            return {
                "id": company.id,
                "name": company.name,
                "vat": company.vat if hasattr(company, "vat") else None,
                "email": company.email if hasattr(company, "email") else None,
                "phone": company.phone if hasattr(company, "phone") else None,
                "website": company.website if hasattr(company, "website") else None,
                "currency": company.currency_id.name if hasattr(company, "currency_id") and company.currency_id else None,
                "logo": logo_data,
                "address": address
            }
        except Exception as e:
            logger.error(f"Error retrieving company information: {str(e)}")
            raise OdooDataError(f"Error retrieving company information: {str(e)}")
            
    @ensure_connected
    def get_customers(self, limit: int = 100, offset: int = 0, search_term: str = None) -> List[Dict[str, Any]]:
        """
        Get list of customers (partners with customer=True).
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            search_term: Optional search term to filter customers
            
        Returns:
            List of customer records
        """
        try:
            Partner = self.odoo.env['res.partner']
            
            # Build domain filter
            domain = [('customer_rank', '>', 0)]  # In Odoo 13+, customer_rank > 0 indicates customers
            
            # Add search term if provided
            if search_term:
                domain.append('|')
                domain.append(('name', 'ilike', search_term))
                domain.append(('email', 'ilike', search_term))
                
            # Get customer IDs with pagination
            customer_ids = Partner.search(domain, limit=limit, offset=offset)
            
            if not customer_ids:
                return []
                
            # Get customer records
            customers = []
            for customer in Partner.browse(customer_ids):
                customers.append({
                    "id": customer.id,
                    "name": customer.name,
                    "email": customer.email if hasattr(customer, "email") else None,
                    "phone": customer.phone if hasattr(customer, "phone") else None,
                    "street": customer.street if hasattr(customer, "street") else None,
                    "city": customer.city if hasattr(customer, "city") else None,
                    "country": customer.country_id.name if hasattr(customer, "country_id") and customer.country_id else None,
                    "vat": customer.vat if hasattr(customer, "vat") else None
                })
                
            return customers
            
        except Exception as e:
            logger.error(f"Error retrieving customers: {str(e)}")
            raise OdooDataError(f"Error retrieving customers: {str(e)}")
            
    @ensure_connected
    def get_products(self, limit: int = 100, offset: int = 0, search_term: str = None) -> List[Dict[str, Any]]:
        """
        Get list of products.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            search_term: Optional search term to filter products
            
        Returns:
            List of product records
        """
        try:
            Product = self.odoo.env['product.product']
            
            # Build domain filter
            domain = [('sale_ok', '=', True)]  # Only products that can be sold
            
            # Add search term if provided
            if search_term:
                domain.append('|')
                domain.append(('name', 'ilike', search_term))
                domain.append(('default_code', 'ilike', search_term))
                
            # Get product IDs with pagination
            product_ids = Product.search(domain, limit=limit, offset=offset)
            
            if not product_ids:
                return []
                
            # Get product records
            products = []
            for product in Product.browse(product_ids):
                products.append({
                    "id": product.id,
                    "name": product.name,
                    "code": product.default_code if hasattr(product, "default_code") else None,
                    "price": product.list_price if hasattr(product, "list_price") else 0.0,
                    "currency": product.currency_id.name if hasattr(product, "currency_id") and product.currency_id else None,
                    "category": product.categ_id.name if hasattr(product, "categ_id") and product.categ_id else None,
                    "type": product.type if hasattr(product, "type") else None,
                    "uom": product.uom_id.name if hasattr(product, "uom_id") and product.uom_id else None,
                    "taxes": [
                        {"id": tax.id, "name": tax.name} 
                        for tax in product.taxes_id.browse(product.taxes_id) 
                        if hasattr(product, "taxes_id") and product.taxes_id
                    ] if hasattr(product, "taxes_id") else []
                })
                
            return products
            
        except Exception as e:
            logger.error(f"Error retrieving products: {str(e)}")
            raise OdooDataError(f"Error retrieving products: {str(e)}")
    
    @ensure_connected
    def get_invoices(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        include_draft: bool = False,
        include_attachments: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Fetch invoices from Odoo with pagination.
        
        Args:
            from_date: Start date for filtering invoices
            to_date: End date for filtering invoices
            include_draft: Whether to include draft invoices
            include_attachments: Whether to include document attachments
            page: Page number for pagination
            page_size: Number of records per page
            
        Returns:
            Dict containing invoices and pagination metadata
        """
        try:
            # Get the invoice model (account.move in Odoo 13+)
            Invoice = self.odoo.env['account.move']
            
            # Build search domain
            domain = [
                ('move_type', '=', 'out_invoice'),  # Only customer invoices
            ]
            
            # Filter by state based on include_draft parameter
            if not include_draft:
                domain.append(('state', '=', 'posted'))  # Only posted invoices
            
            # Add date filters if provided
            if from_date:
                domain.append(('write_date', '>=', from_date.strftime('%Y-%m-%d %H:%M:%S')))
            if to_date:
                domain.append(('write_date', '<=', to_date.strftime('%Y-%m-%d %H:%M:%S')))
            
            # Calculate offset based on page and page_size
            offset = (page - 1) * page_size
            
            # Get total count of matching invoices
            total_invoices = Invoice.search_count(domain)
            
            # Search for invoices matching the criteria with pagination
            invoice_ids = Invoice.search(domain, limit=page_size, offset=offset)
            
            # If no invoices found
            if not invoice_ids:
                return {
                    "invoices": [],
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "pages": 0,
                    "has_next": False,
                    "has_prev": page > 1,
                    "next_page": None,
                    "prev_page": page - 1 if page > 1 else None
                }
            
            # Calculate pagination info
            total_pages = (total_invoices + page_size - 1) // page_size
            has_next = page < total_pages
            next_page = page + 1 if has_next else None
            has_prev = page > 1
            prev_page = page - 1 if has_prev else None
            
            # Prepare results list
            invoices = []
            
            # Browse invoice records
            for invoice in Invoice.browse(invoice_ids):
                # Add to results list
                invoices.append(self._format_invoice_data(invoice, include_attachments))
            
            # Return paginated results with metadata
            return {
                "invoices": invoices,
                "total": total_invoices,
                "page": page,
                "page_size": page_size,
                "pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev,
                "next_page": next_page,
                "prev_page": prev_page
            }
            
        except odoorpc.error.RPCError as e:
            logger.error(f"OdooRPC error fetching invoices: {str(e)}")
            raise OdooDataError(f"OdooRPC error fetching invoices: {str(e)}")
        except Exception as e:
            logger.exception(f"Error fetching invoices from Odoo: {str(e)}")
            raise OdooDataError(f"Error fetching invoices from Odoo: {str(e)}")
    
    def _format_invoice_data(self, invoice, include_attachments=False) -> Dict[str, Any]:
        """
        Format an invoice record into a standardized dictionary.
        
        Args:
            invoice: The Odoo invoice record
            include_attachments: Whether to include document attachments
            
        Returns:
            Dict with formatted invoice data
        """
        # Get partner (customer) data
        partner = invoice.partner_id
        
        # Get currency
        currency = invoice.currency_id
        
        # Format invoice data
        invoice_data = {
            "id": invoice.id,
            "name": invoice.name,
            "invoice_number": invoice.name,
            "reference": getattr(invoice, 'ref', '') or '',
            "invoice_date": invoice.invoice_date,
            "invoice_date_due": invoice.invoice_date_due,
            "state": invoice.state,
            "amount_total": invoice.amount_total,
            "amount_untaxed": invoice.amount_untaxed,
            "amount_tax": invoice.amount_tax,
            "currency": {
                "id": currency.id,
                "name": currency.name,
                "symbol": currency.symbol
            },
            "partner": {
                "id": partner.id,
                "name": partner.name,
                "vat": partner.vat if hasattr(partner, 'vat') else '',
                "email": partner.email if hasattr(partner, 'email') else '',
                "phone": partner.phone if hasattr(partner, 'phone') else '',
            },
            "lines": []
        }
        
        # Get invoice lines
        for line in invoice.invoice_line_ids:
            product = line.product_id
            taxes = [{
                "id": tax.id,
                "name": tax.name,
                "amount": tax.amount
            } for tax in line.tax_ids] if hasattr(line, 'tax_ids') else []
            
            line_data = {
                "id": line.id,
                "name": line.name,
                "quantity": line.quantity,
                "price_unit": line.price_unit,
                "price_subtotal": line.price_subtotal,
                "taxes": taxes,
                "product": {
                    "id": product.id,
                    "name": product.name,
                    "default_code": product.default_code if hasattr(product, 'default_code') else '',
                }
            }
            invoice_data["lines"].append(line_data)
        
        # Fetch PDF attachments if requested
        if include_attachments:
            try:
                Attachment = self.odoo.env['ir.attachment']
                attachment_ids = Attachment.search([
                    ('res_model', '=', 'account.move'),
                    ('res_id', '=', invoice.id),
                    ('mimetype', '=', 'application/pdf')
                ], limit=3)  # Limiting to 3 most recent PDFs
                
                if attachment_ids:
                    attachments = []
                    for attachment in Attachment.browse(attachment_ids):
                        attachments.append({
                            "id": attachment.id,
                            "name": attachment.name,
                            "mimetype": attachment.mimetype,
                            "url": f"{self.config.url}/web/content/{attachment.id}?download=true"
                        })
                    invoice_data["attachments"] = attachments
            except Exception as e:
                logger.warning(f"Error fetching attachments for invoice {invoice.id}: {str(e)}")
                invoice_data["attachments_error"] = str(e)
        
        return invoice_data
    
    @ensure_connected
    def get_invoice_by_id(self, invoice_id: int, include_attachments: bool = False) -> Dict[str, Any]:
        """
        Get a specific invoice by ID.
        
        Args:
            invoice_id: ID of the invoice to retrieve
            include_attachments: Whether to include document attachments
            
        Returns:
            Dict with invoice data
        """
        try:
            Invoice = self.odoo.env['account.move']
            invoice = Invoice.browse(invoice_id)
            
            # Check if invoice exists
            if not invoice.exists():
                raise OdooDataError(f"Invoice with ID {invoice_id} not found")
            
            return self._format_invoice_data(invoice, include_attachments)
        
        except odoorpc.error.RPCError as e:
            logger.error(f"OdooRPC error fetching invoice {invoice_id}: {str(e)}")
            raise OdooDataError(f"OdooRPC error fetching invoice {invoice_id}: {str(e)}")
        except Exception as e:
            logger.exception(f"Error fetching invoice {invoice_id} from Odoo: {str(e)}")
            raise OdooDataError(f"Error fetching invoice {invoice_id} from Odoo: {str(e)}")
    
    @ensure_connected
    def search_invoices(
        self, 
        search_term: str, 
        include_attachments: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Search for invoices by various criteria.
        
        Args:
            search_term: Text to search for in invoice number, reference, or partner name
            include_attachments: Whether to include document attachments
            page: Page number for pagination
            page_size: Number of records per page
            
        Returns:
            Dict containing matching invoices and pagination metadata
        """
        try:
            Invoice = self.odoo.env['account.move']
            
            # Build domain for invoice search
            domain = [
                ('move_type', '=', 'out_invoice'),  # Only customer invoices
                '|', '|', '|',
                ('name', 'ilike', search_term),
                ('ref', 'ilike', search_term),
                ('partner_id.name', 'ilike', search_term),
                ('invoice_line_ids.name', 'ilike', search_term)
            ]
            
            # Calculate offset based on page and page_size
            offset = (page - 1) * page_size
            
            # Get total count
            total_invoices = Invoice.search_count(domain)
            
            # Search with pagination
            invoice_ids = Invoice.search(domain, limit=page_size, offset=offset)
            
            # If no invoices found
            if not invoice_ids:
                return {
                    "invoices": [],
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "pages": 0,
                    "has_next": False,
                    "has_prev": page > 1,
                    "next_page": None,
                    "prev_page": page - 1 if page > 1 else None,
                    "search_term": search_term
                }
            
            # Calculate pagination info
            total_pages = (total_invoices + page_size - 1) // page_size
            has_next = page < total_pages
            next_page = page + 1 if has_next else None
            has_prev = page > 1
            prev_page = page - 1 if has_prev else None
            
            # Format results
            invoices = [self._format_invoice_data(invoice, include_attachments) 
                       for invoice in Invoice.browse(invoice_ids)]
            
            return {
                "invoices": invoices,
                "total": total_invoices,
                "page": page,
                "page_size": page_size,
                "pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev,
                "next_page": next_page,
                "prev_page": prev_page,
                "search_term": search_term
            }
            
        except Exception as e:
            logger.exception(f"Error searching invoices in Odoo: {str(e)}")
            raise OdooDataError(f"Error searching invoices in Odoo: {str(e)}")
    
    @ensure_connected
    def get_partners(self, search_term: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get partners/customers from Odoo.
        
        Args:
            search_term: Optional term to search for in partner name or reference
            limit: Maximum number of partners to return
            
        Returns:
            List of partner dictionaries
        """
        try:
            Partner = self.odoo.env['res.partner']
            
            # Build domain
            domain = [('is_company', '=', True)]
            if search_term:
                domain.extend(['|', ('name', 'ilike', search_term), ('ref', 'ilike', search_term)])
            
            # Search for partners
            partner_ids = Partner.search(domain, limit=limit)
            
            # Format results
            partners = []
            for partner in Partner.browse(partner_ids):
                partners.append({
                    "id": partner.id,
                    "name": partner.name,
                    "vat": partner.vat if hasattr(partner, 'vat') else '',
                    "email": partner.email if hasattr(partner, 'email') else '',
                    "phone": partner.phone if hasattr(partner, 'phone') else '',
                    "street": partner.street if hasattr(partner, 'street') else '',
                    "city": partner.city if hasattr(partner, 'city') else '',
                    "zip": partner.zip if hasattr(partner, 'zip') else '',
                    "country": partner.country_id.name if hasattr(partner, 'country_id') and partner.country_id else '',
                })
            
            return partners
            
        except Exception as e:
            logger.exception(f"Error fetching partners from Odoo: {str(e)}")
            raise OdooDataError(f"Error fetching partners from Odoo: {str(e)}")
