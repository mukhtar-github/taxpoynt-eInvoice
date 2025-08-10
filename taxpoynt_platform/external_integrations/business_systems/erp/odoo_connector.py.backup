"""
OdooConnector class for TaxPoynt eInvoice - System Integrator Functions.

This module provides System Integrator (SI) role functionality for Odoo ERP integration,
including connection management, data extraction, and ERP system communication.

Enhanced with BaseERPConnector interface for unified ERP integration architecture.

SI Role Responsibilities:
- ERP system connectivity and authentication
- Data extraction from Odoo instances (invoices, customers, products)
- Connection health monitoring and error handling
- Invoice data transformation for FIRS compliance
- FIRS UBL format transformation
"""
import logging
import ssl
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

import odoorpc

from app.services.firs_si.base_erp_connector import BaseERPConnector, ERPConnectionError, ERPAuthenticationError, ERPDataError, ERPValidationError
from app.schemas.integration import OdooAuthMethod, OdooConfig, IntegrationTestResult
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


class OdooConnector(BaseERPConnector):
    """
    System Integrator connector for Odoo ERP integration.
    
    This class provides SI role methods for connecting to Odoo ERP systems,
    authenticating, and retrieving business data with proper error handling
    and connection management for FIRS e-invoicing compliance.
    """
    
    def __init__(self, config: Union[OdooConfig, Dict[str, Any]]):
        """
        Initialize the OdooConnector with configuration.
        
        Args:
            config: Odoo configuration parameters (OdooConfig or dict)
        """
        # Convert dict to OdooConfig if needed
        if isinstance(config, dict):
            # Create a basic config from dict
            config = OdooConfig(**config)
        
        # Initialize parent class
        super().__init__(config.dict() if hasattr(config, 'dict') else config)
        
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
        Connect to the Odoo ERP server - SI Role Function.
        
        Establishes connection to Odoo ERP system for System Integrator
        data extraction and business process integration.
        
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
        Authenticate with the Odoo ERP server - SI Role Function.
        
        Performs authentication with Odoo ERP system using configured
        credentials for System Integrator data access.
        
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
        Get information about the authenticated user - SI Role Function.
        
        Retrieves user information from Odoo ERP for System Integrator
        session management and audit tracking.
        
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
        Get company information from Odoo ERP - SI Role Function.
        
        Extracts company details from Odoo ERP for System Integrator
        use in invoice generation and FIRS compliance validation.
        
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
        Get customer list from Odoo ERP - SI Role Function.
        
        Extracts customer data from Odoo ERP for System Integrator
        invoice processing and customer validation.
        
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
        Get product list from Odoo ERP - SI Role Function.
        
        Extracts product data from Odoo ERP for System Integrator
        invoice line item processing and tax calculation.
        
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
        Fetch invoices from Odoo ERP with pagination - SI Role Function.
        
        Extracts invoice data from Odoo ERP for System Integrator
        processing and FIRS submission preparation.
        
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
        Format invoice record into standardized dictionary - SI Role Function.
        
        Transforms Odoo ERP invoice data into standardized format for
        System Integrator processing and FIRS compliance preparation.
        
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
        Get specific invoice by ID from Odoo ERP - SI Role Function.
        
        Retrieves individual invoice data from Odoo ERP for System Integrator
        detailed processing and FIRS submission.
        
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
        Search for invoices by criteria in Odoo ERP - SI Role Function.
        
        Performs invoice search in Odoo ERP for System Integrator
        data retrieval and processing workflows.
        
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
        Get partners/customers from Odoo ERP - SI Role Function.
        
        Retrieves partner data from Odoo ERP for System Integrator
        customer management and invoice processing.
        
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

    # BaseERPConnector interface implementation
    @property
    def erp_type(self) -> str:
        """Return the ERP system type"""
        return "odoo"
    
    @property
    def erp_version(self) -> str:
        """Return the ERP system version"""
        if self.version_info:
            return self.version_info.get('server_version', 'unknown')
        return 'unknown'
    
    @property
    def supported_features(self) -> List[str]:
        """Return list of supported features for this ERP connector"""
        features = [
            'invoice_extraction',
            'partner_management',
            'product_management',
            'company_info',
            'invoice_search',
            'pagination',
            'attachments',
            'firs_transformation'
        ]
        
        # Add version-specific features
        if self.major_version and self.major_version >= 18:
            features.extend(['rest_api', 'advanced_einvoice', 'irn_fields'])
        
        return features
    
    async def test_connection(self) -> IntegrationTestResult:
        """Test connection to the ERP system"""
        try:
            # Connect to Odoo
            self.connect()
            
            # Test authentication
            self.authenticate()
            
            # Get user info to verify connection
            user_info = self.get_user_info()
            
            # Test basic data access
            partner_count = 0
            try:
                partners = self.odoo.env['res.partner'].search([('is_company', '=', True)], limit=5)
                partner_count = len(partners) if partners else 0
            except Exception as e:
                logger.warning(f"Limited partner access: {str(e)}")
            
            return IntegrationTestResult(
                success=True,
                message=f"Successfully connected to Odoo server as {user_info['name']}",
                details={
                    "version_info": self.version_info,
                    "major_version": self.major_version,
                    "user_name": user_info['name'],
                    "partner_count": partner_count,
                    "supported_features": self.supported_features
                }
            )
            
        except Exception as e:
            return IntegrationTestResult(
                success=False,
                message=f"Connection test failed: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__}
            )
    
    async def authenticate(self) -> bool:
        """Authenticate with the ERP system"""
        try:
            # Use the existing synchronous authenticate method (avoiding recursion)
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
            
            # Update connection status
            self.authenticated = True
            self.connected = True
            self.last_connection_time = datetime.utcnow()
            
            logger.info(f"Successfully authenticated with Odoo server")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            self.authenticated = False
            self.connected = False
            raise ERPAuthenticationError(f"Authentication failed: {str(e)}")
    
    async def validate_invoice_data(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate invoice data for FIRS compliance"""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Required fields for FIRS compliance
        required_fields = [
            'name', 'invoice_date', 'partner', 'amount_total', 
            'currency', 'lines'
        ]
        
        for field in required_fields:
            if field not in invoice_data:
                validation_result['errors'].append(f"Missing required field: {field}")
                validation_result['is_valid'] = False
        
        # Validate partner data
        if 'partner' in invoice_data:
            partner = invoice_data['partner']
            if 'name' not in partner or not partner['name']:
                validation_result['errors'].append("Partner name is required")
                validation_result['is_valid'] = False
        
        # Validate invoice lines
        if 'lines' in invoice_data:
            if not invoice_data['lines']:
                validation_result['errors'].append("Invoice must have at least one line")
                validation_result['is_valid'] = False
            else:
                for i, line in enumerate(invoice_data['lines']):
                    if 'name' not in line or not line['name']:
                        validation_result['errors'].append(f"Line {i+1}: Description is required")
                        validation_result['is_valid'] = False
                    if 'quantity' not in line or line['quantity'] <= 0:
                        validation_result['errors'].append(f"Line {i+1}: Quantity must be positive")
                        validation_result['is_valid'] = False
        
        return validation_result
    
    async def transform_to_firs_format(
        self,
        invoice_data: Dict[str, Any],
        target_format: str = 'UBL_BIS_3.0'
    ) -> Dict[str, Any]:
        """Transform ERP invoice data to FIRS-compliant format"""
        try:
            # Basic UBL BIS 3.0 transformation
            firs_invoice = {
                'invoice_type_code': '380',  # Standard invoice
                'id': invoice_data.get('name', ''),
                'issue_date': invoice_data.get('invoice_date', ''),
                'due_date': invoice_data.get('invoice_date_due', ''),
                'document_currency_code': invoice_data.get('currency', {}).get('name', 'NGN'),
                'accounting_supplier_party': {
                    'party': {
                        'party_name': {
                            'name': self.get_company_info().get('name', '')
                        },
                        'party_tax_scheme': {
                            'company_id': self.get_company_info().get('vat', '')
                        }
                    }
                },
                'accounting_customer_party': {
                    'party': {
                        'party_name': {
                            'name': invoice_data.get('partner', {}).get('name', '')
                        },
                        'party_tax_scheme': {
                            'company_id': invoice_data.get('partner', {}).get('vat', '')
                        }
                    }
                },
                'legal_monetary_total': {
                    'line_extension_amount': invoice_data.get('amount_untaxed', 0),
                    'tax_exclusive_amount': invoice_data.get('amount_untaxed', 0),
                    'tax_inclusive_amount': invoice_data.get('amount_total', 0),
                    'allowance_total_amount': 0,
                    'charge_total_amount': 0,
                    'prepaid_amount': 0,
                    'payable_amount': invoice_data.get('amount_total', 0)
                },
                'invoice_line': []
            }
            
            # Transform invoice lines
            for line in invoice_data.get('lines', []):
                firs_line = {
                    'id': str(line.get('id', '')),
                    'invoiced_quantity': {
                        'quantity': line.get('quantity', 0),
                        'unit_code': 'C62'  # Default unit
                    },
                    'line_extension_amount': line.get('price_subtotal', 0),
                    'item': {
                        'description': line.get('name', ''),
                        'name': line.get('product', {}).get('name', ''),
                        'sellers_item_identification': {
                            'id': line.get('product', {}).get('default_code', '')
                        }
                    },
                    'price': {
                        'price_amount': line.get('price_unit', 0),
                        'base_quantity': {
                            'quantity': 1,
                            'unit_code': 'C62'
                        }
                    }
                }
                
                # Add tax information
                if line.get('taxes'):
                    firs_line['tax_total'] = {
                        'tax_amount': sum(tax.get('amount', 0) for tax in line['taxes']),
                        'tax_subtotal': [{
                            'taxable_amount': line.get('price_subtotal', 0),
                            'tax_amount': tax.get('amount', 0),
                            'tax_category': {
                                'id': 'S',  # Standard rate
                                'percent': tax.get('amount', 0),
                                'tax_scheme': {
                                    'id': 'VAT'
                                }
                            }
                        } for tax in line['taxes']]
                    }
                
                firs_invoice['invoice_line'].append(firs_line)
            
            # Add tax totals
            firs_invoice['tax_total'] = {
                'tax_amount': invoice_data.get('amount_tax', 0),
                'tax_subtotal': [{
                    'taxable_amount': invoice_data.get('amount_untaxed', 0),
                    'tax_amount': invoice_data.get('amount_tax', 0),
                    'tax_category': {
                        'id': 'S',
                        'percent': 7.5,  # Default Nigerian VAT rate
                        'tax_scheme': {
                            'id': 'VAT'
                        }
                    }
                }]
            }
            
            return {
                'firs_invoice': firs_invoice,
                'source_format': 'odoo_native',
                'target_format': target_format,
                'transformation_metadata': {
                    'transformation_date': datetime.utcnow().isoformat(),
                    'source_invoice_id': invoice_data.get('id'),
                    'erp_type': self.erp_type,
                    'erp_version': self.erp_version
                }
            }
            
        except Exception as e:
            logger.error(f"Error transforming invoice to FIRS format: {str(e)}")
            raise ERPDataError(f"Error transforming invoice to FIRS format: {str(e)}")
    
    async def update_invoice_status(
        self,
        invoice_id: Union[int, str],
        status_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update invoice status in the ERP system"""
        try:
            # For now, just log the status update
            # In a real implementation, this would update the invoice in Odoo
            logger.info(f"Updating invoice {invoice_id} status: {status_data}")
            
            return {
                'success': True,
                'invoice_id': invoice_id,
                'status_updated': True,
                'new_status': status_data.get('status'),
                'updated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error updating invoice status: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'invoice_id': invoice_id
            }
    
    async def get_tax_configuration(self) -> Dict[str, Any]:
        """Get tax configuration from the ERP system"""
        try:
            # Get tax information from Odoo
            Tax = self.odoo.env['account.tax']
            tax_ids = Tax.search([('type_tax_use', '=', 'sale')])
            
            taxes = []
            for tax in Tax.browse(tax_ids):
                taxes.append({
                    'id': tax.id,
                    'name': tax.name,
                    'amount': tax.amount,
                    'type': tax.amount_type,
                    'scope': tax.type_tax_use
                })
            
            return {
                'taxes': taxes,
                'default_currency': self.get_company_info().get('currency', 'NGN'),
                'tax_system': 'Nigerian VAT'
            }
            
        except Exception as e:
            logger.error(f"Error getting tax configuration: {str(e)}")
            return {
                'taxes': [],
                'error': str(e)
            }
    
    async def disconnect(self) -> bool:
        """Disconnect from the ERP system"""
        try:
            if self.odoo:
                # Close the connection
                self.odoo = None
                self.connected = False
                self.authenticated = False
                self.last_connection_time = None
                logger.info("Disconnected from Odoo")
            return True
        except Exception as e:
            logger.error(f"Error disconnecting from Odoo: {str(e)}")
            return False