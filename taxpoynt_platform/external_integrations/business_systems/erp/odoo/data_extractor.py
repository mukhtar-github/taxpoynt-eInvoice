"""
Odoo Data Extraction Module
Handles data extraction from Odoo ERP including customers, products, invoices, and partners.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import odoorpc

from .exceptions import OdooDataError
from .auth import ensure_connected

logger = logging.getLogger(__name__)


class OdooDataExtractor:
    """Handles data extraction from Odoo ERP."""
    
    def __init__(self, authenticator):
        """Initialize with an OdooAuthenticator instance."""
        self.authenticator = authenticator
    
    @property
    def odoo(self):
        """Get the Odoo connection from authenticator."""
        return self.authenticator.odoo
    
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
                    "default_code": product.default_code if hasattr(product, "default_code") else None,
                    "type": product.type if hasattr(product, "type") else None,
                    "list_price": float(product.list_price) if hasattr(product, "list_price") else 0.0,
                    "standard_price": float(product.standard_price) if hasattr(product, "standard_price") else 0.0,
                    "uom_id": product.uom_id.id if hasattr(product, "uom_id") and product.uom_id else None,
                    "uom_name": product.uom_id.name if hasattr(product, "uom_id") and product.uom_id else None,
                    "categ_id": product.categ_id.id if hasattr(product, "categ_id") and product.categ_id else None,
                    "category_name": product.categ_id.name if hasattr(product, "categ_id") and product.categ_id else None,
                    "taxes_id": [tax.id for tax in product.taxes_id] if hasattr(product, "taxes_id") else []
                })
                
            return products
            
        except Exception as e:
            logger.error(f"Error retrieving products: {str(e)}")
            raise OdooDataError(f"Error retrieving products: {str(e)}")
    
    @ensure_connected
    def get_invoices(self, 
                    limit: int = 100, 
                    offset: int = 0, 
                    start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None,
                    state: Optional[str] = None,
                    include_attachments: bool = False) -> List[Dict[str, Any]]:
        """
        Get invoice list from Odoo ERP - SI Role Function.
        
        Extracts invoice data from Odoo ERP for System Integrator
        FIRS submission and e-invoice processing.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            start_date: Filter invoices from this date
            end_date: Filter invoices until this date
            state: Filter by invoice state (draft, posted, etc.)
            include_attachments: Whether to include attachment information
            
        Returns:
            List of invoice records
        """
        try:
            Invoice = self.odoo.env['account.move']
            
            # Build domain filter for customer invoices
            domain = [
                ('move_type', '=', 'out_invoice')  # Only customer invoices
            ]
            
            # Add date filters
            if start_date:
                domain.append(('invoice_date', '>=', start_date.strftime('%Y-%m-%d')))
            if end_date:
                domain.append(('invoice_date', '<=', end_date.strftime('%Y-%m-%d')))
                
            # Add state filter
            if state:
                domain.append(('state', '=', state))
                
            # Get invoice IDs with pagination
            invoice_ids = Invoice.search(domain, limit=limit, offset=offset, order='invoice_date desc')
            
            if not invoice_ids:
                return []
                
            # Get invoice records
            invoices = []
            for invoice in Invoice.browse(invoice_ids):
                invoice_data = self._format_invoice_data(invoice, include_attachments)
                invoices.append(invoice_data)
                
            return invoices
            
        except Exception as e:
            logger.error(f"Error retrieving invoices: {str(e)}")
            raise OdooDataError(f"Error retrieving invoices: {str(e)}")
    
    @ensure_connected
    def get_invoice_by_id(self, invoice_id: int, include_attachments: bool = False) -> Dict[str, Any]:
        """
        Get a specific invoice by ID from Odoo ERP - SI Role Function.
        
        Args:
            invoice_id: The invoice ID to retrieve
            include_attachments: Whether to include attachment information
            
        Returns:
            Invoice record data
        """
        try:
            Invoice = self.odoo.env['account.move']
            invoice = Invoice.browse(invoice_id)
            
            if not invoice.exists():
                raise OdooDataError(f"Invoice with ID {invoice_id} not found")
                
            return self._format_invoice_data(invoice, include_attachments)
            
        except Exception as e:
            logger.error(f"Error retrieving invoice {invoice_id}: {str(e)}")
            raise OdooDataError(f"Error retrieving invoice {invoice_id}: {str(e)}")
    
    @ensure_connected
    def search_invoices(self,
                       customer_name: Optional[str] = None,
                       invoice_number: Optional[str] = None,
                       amount_range: Optional[tuple] = None,
                       limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search invoices with specific criteria - SI Role Function.
        
        Args:
            customer_name: Filter by customer name
            invoice_number: Filter by invoice number
            amount_range: Tuple of (min_amount, max_amount)
            limit: Maximum number of records to return
            
        Returns:
            List of matching invoice records
        """
        try:
            Invoice = self.odoo.env['account.move']
            
            # Build domain filter
            domain = [('move_type', '=', 'out_invoice')]
            
            # Add customer name filter
            if customer_name:
                domain.append(('partner_id.name', 'ilike', customer_name))
                
            # Add invoice number filter
            if invoice_number:
                domain.append(('name', 'ilike', invoice_number))
                
            # Add amount range filter
            if amount_range:
                min_amount, max_amount = amount_range
                if min_amount is not None:
                    domain.append(('amount_total', '>=', min_amount))
                if max_amount is not None:
                    domain.append(('amount_total', '<=', max_amount))
            
            # Search invoices
            invoice_ids = Invoice.search(domain, limit=limit, order='invoice_date desc')
            
            if not invoice_ids:
                return []
                
            # Get invoice records
            invoices = []
            for invoice in Invoice.browse(invoice_ids):
                invoice_data = self._format_invoice_data(invoice, include_attachments=False)
                invoices.append(invoice_data)
                
            return invoices
            
        except Exception as e:
            logger.error(f"Error searching invoices: {str(e)}")
            raise OdooDataError(f"Error searching invoices: {str(e)}")
    
    @ensure_connected
    def get_partners(self, search_term: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get business partners from Odoo ERP - SI Role Function.
        
        Args:
            search_term: Optional search term to filter partners
            limit: Maximum number of records to return
            
        Returns:
            List of partner records
        """
        try:
            Partner = self.odoo.env['res.partner']
            
            # Build domain filter
            domain = []
            
            # Add search term if provided
            if search_term:
                domain.append('|')
                domain.append(('name', 'ilike', search_term))
                domain.append(('email', 'ilike', search_term))
                
            # Get partner IDs
            partner_ids = Partner.search(domain, limit=limit)
            
            if not partner_ids:
                return []
                
            # Get partner records
            partners = []
            for partner in Partner.browse(partner_ids):
                partners.append({
                    "id": partner.id,
                    "name": partner.name,
                    "email": partner.email if hasattr(partner, "email") else None,
                    "phone": partner.phone if hasattr(partner, "phone") else None,
                    "is_company": partner.is_company if hasattr(partner, "is_company") else False,
                    "customer_rank": partner.customer_rank if hasattr(partner, "customer_rank") else 0,
                    "supplier_rank": partner.supplier_rank if hasattr(partner, "supplier_rank") else 0,
                    "vat": partner.vat if hasattr(partner, "vat") else None
                })
                
            return partners
            
        except Exception as e:
            logger.error(f"Error retrieving partners: {str(e)}")
            raise OdooDataError(f"Error retrieving partners: {str(e)}")
    
    def _format_invoice_data(self, invoice, include_attachments=False) -> Dict[str, Any]:
        """
        Format invoice data for consistent output - SI Role Function.
        
        Args:
            invoice: Odoo invoice record
            include_attachments: Whether to include attachment data
            
        Returns:
            Formatted invoice data
        """
        try:
            # Basic invoice information
            invoice_data = {
                "id": invoice.id,
                "name": invoice.name,
                "invoice_date": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
                "invoice_date_due": invoice.invoice_date_due.isoformat() if hasattr(invoice, "invoice_date_due") and invoice.invoice_date_due else None,
                "state": invoice.state,
                "move_type": invoice.move_type,
                "ref": invoice.ref if hasattr(invoice, "ref") else None,
                "amount_untaxed": float(invoice.amount_untaxed),
                "amount_tax": float(invoice.amount_tax),
                "amount_total": float(invoice.amount_total),
                "currency": invoice.currency_id.name if invoice.currency_id else None,
                
                # Partner information
                "partner": {
                    "id": invoice.partner_id.id if invoice.partner_id else None,
                    "name": invoice.partner_id.name if invoice.partner_id else None,
                    "email": invoice.partner_id.email if invoice.partner_id and hasattr(invoice.partner_id, "email") else None,
                    "vat": invoice.partner_id.vat if invoice.partner_id and hasattr(invoice.partner_id, "vat") else None,
                    "street": invoice.partner_id.street if invoice.partner_id and hasattr(invoice.partner_id, "street") else None,
                    "city": invoice.partner_id.city if invoice.partner_id and hasattr(invoice.partner_id, "city") else None,
                    "country": invoice.partner_id.country_id.name if invoice.partner_id and hasattr(invoice.partner_id, "country_id") and invoice.partner_id.country_id else None
                },
                
                # Company information
                "company": {
                    "id": invoice.company_id.id if invoice.company_id else None,
                    "name": invoice.company_id.name if invoice.company_id else None,
                    "vat": invoice.company_id.vat if invoice.company_id and hasattr(invoice.company_id, "vat") else None
                },
                
                # Invoice lines
                "invoice_lines": []
            }
            
            # Add invoice lines
            for line in invoice.invoice_line_ids:
                line_data = {
                    "id": line.id,
                    "name": line.name if hasattr(line, "name") else None,
                    "product_id": line.product_id.id if line.product_id else None,
                    "product_name": line.product_id.name if line.product_id else None,
                    "quantity": float(line.quantity) if hasattr(line, "quantity") else 0.0,
                    "price_unit": float(line.price_unit) if hasattr(line, "price_unit") else 0.0,
                    "price_subtotal": float(line.price_subtotal) if hasattr(line, "price_subtotal") else 0.0,
                    "price_total": float(line.price_total) if hasattr(line, "price_total") else 0.0,
                    "discount": float(line.discount) if hasattr(line, "discount") else 0.0,
                    "tax_ids": [tax.id for tax in line.tax_ids] if hasattr(line, "tax_ids") else [],
                    "account_id": line.account_id.id if hasattr(line, "account_id") and line.account_id else None
                }
                invoice_data["invoice_lines"].append(line_data)
            
            # Add attachment information if requested
            if include_attachments:
                attachments = self._get_invoice_attachments(invoice)
                invoice_data["attachments"] = attachments
            
            return invoice_data
            
        except Exception as e:
            logger.error(f"Error formatting invoice data: {str(e)}")
            raise OdooDataError(f"Error formatting invoice data: {str(e)}")
    
    def _get_invoice_attachments(self, invoice) -> List[Dict[str, Any]]:
        """Get attachment information for an invoice."""
        try:
            Attachment = self.odoo.env['ir.attachment']
            
            # Search for attachments related to this invoice
            attachment_ids = Attachment.search([
                ('res_model', '=', 'account.move'),
                ('res_id', '=', invoice.id)
            ])
            
            attachments = []
            for attachment in Attachment.browse(attachment_ids):
                attachments.append({
                    "id": attachment.id,
                    "name": attachment.name,
                    "mimetype": attachment.mimetype if hasattr(attachment, "mimetype") else None,
                    "file_size": attachment.file_size if hasattr(attachment, "file_size") else None,
                    "create_date": attachment.create_date.isoformat() if attachment.create_date else None
                })
                
            return attachments
            
        except Exception as e:
            logger.warning(f"Error retrieving attachments: {str(e)}")
            return []