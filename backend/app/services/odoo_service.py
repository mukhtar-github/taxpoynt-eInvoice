"""
Odoo Integration Service for connecting to Odoo instances using OdooRPC.

This module provides service functions for connecting to Odoo, testing
connectivity, and fetching data from Odoo instances.
"""
import json
import logging
import ssl
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union, cast
from urllib.parse import urlparse
import odoorpc

from app.schemas.integration import OdooAuthMethod, OdooConnectionTestRequest, OdooConfig, IntegrationTestResult

logger = logging.getLogger(__name__)


def test_odoo_connection(connection_params: Union[OdooConnectionTestRequest, OdooConfig]) -> Dict[str, Any]:
    """
    Test connection to an Odoo server using OdooRPC.
    
    Args:
        connection_params: Connection parameters for Odoo server
        
    Returns:
        Dictionary with test results
    """
    try:
        # Parse URL to get host, protocol, and port
        parsed_url = urlparse(str(connection_params.url))
        host = parsed_url.netloc.split(':')[0]
        protocol = parsed_url.scheme or 'jsonrpc'
        
        # Determine port (default is 8069 unless specified)
        port = 443 if protocol == 'jsonrpc+ssl' else 8069
        if ':' in parsed_url.netloc:
            try:
                port = int(parsed_url.netloc.split(':')[1])
            except (IndexError, ValueError):
                pass
        
        # Initialize OdooRPC connection
        odoo = odoorpc.ODOO(host, protocol=protocol, port=port)
        
        # Authenticate with the server
        password_or_key = (
            connection_params.password 
            if connection_params.auth_method == OdooAuthMethod.PASSWORD 
            else connection_params.api_key
        )
        
        # Login to Odoo
        odoo.login(connection_params.database, connection_params.username, password_or_key)
        
        # Get user info to verify connection
        user = odoo.env['res.users'].browse(odoo.env.uid)
        
        # Get server version
        version_info = odoo.version

        # Test access to partners to verify permissions
        partner_count = 0
        try:
            partners = odoo.env['res.partner'].search([('is_company', '=', True)], limit=5)
            partner_count = len(partners) if partners else 0
        except Exception as e:
            logger.warning(f"Access to partners limited: {str(e)}")
        
        return {
            "success": True,
            "message": f"Successfully connected to Odoo server as {user.name}",
            "details": {
                "version_info": version_info,
                "uid": odoo.env.uid,
                "user_name": user.name,
                "partner_count": partner_count
            }
        }
        
    except odoorpc.error.RPCError as e:
        logger.error(f"OdooRPC error: {str(e)}")
        return {
            "success": False,
            "message": f"OdooRPC error: {str(e)}",
            "details": {"error": str(e), "error_type": "RPCError"}
        }
    except odoorpc.error.InternalError as e:
        logger.error(f"OdooRPC internal error: {str(e)}")
        return {
            "success": False,
            "message": f"OdooRPC internal error: {str(e)}",
            "details": {"error": str(e), "error_type": "InternalError"}
        }
    except Exception as e:
        logger.exception(f"Error testing Odoo connection: {str(e)}")
        return {
            "success": False,
            "message": f"Error connecting to Odoo server: {str(e)}",
            "details": {"error": str(e), "error_type": type(e).__name__}
        }


def fetch_odoo_invoices(
    config: OdooConfig,
    from_date: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Fetch invoices from Odoo server using OdooRPC.
    
    Args:
        config: Odoo configuration
        from_date: Fetch invoices from this date (default: None)
        limit: Maximum number of invoices to fetch (default: 100)
        offset: Offset for pagination (default: 0)
        
    Returns:
        List of invoice dictionaries
    """
    try:
        # Parse URL to get host, protocol, and port
        parsed_url = urlparse(str(config.url))
        host = parsed_url.netloc.split(':')[0]
        protocol = parsed_url.scheme or 'jsonrpc'
        
        # Determine port (default is 8069 unless specified)
        port = 443 if protocol == 'jsonrpc+ssl' else 8069
        if ':' in parsed_url.netloc:
            try:
                port = int(parsed_url.netloc.split(':')[1])
            except (IndexError, ValueError):
                pass
        
        # Initialize OdooRPC connection
        odoo = odoorpc.ODOO(host, protocol=protocol, port=port)
        
        # Authenticate with the server
        password_or_key = (
            config.password 
            if config.auth_method == OdooAuthMethod.PASSWORD 
            else config.api_key
        )
        
        # Login to Odoo
        odoo.login(config.database, config.username, password_or_key)
        
        # Get the invoice model (account.move in Odoo 13+)
        Invoice = odoo.env['account.move']
        
        # Build search domain
        domain = [
            ('move_type', '=', 'out_invoice'),  # Only customer invoices
            ('state', '=', 'posted')  # Only posted invoices
        ]
        
        # Add date filter if provided
        if from_date:
            domain.append(('write_date', '>=', from_date.strftime('%Y-%m-%d %H:%M:%S')))
        
        # Search for invoices matching the criteria
        invoice_ids = Invoice.search(domain, limit=limit, offset=offset)
        
        # If no invoices found
        if not invoice_ids:
            return []
        
        # Prepare results list
        invoices = []
        
        # Browse invoice records
        for invoice in Invoice.browse(invoice_ids):
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
                    "email": partner.email,
                    "phone": partner.phone,
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
            
            invoices.append(invoice_data)
        
        return invoices
        
    except odoorpc.error.RPCError as e:
        logger.error(f"OdooRPC error fetching invoices: {str(e)}")
        raise ValueError(f"OdooRPC error: {str(e)}")
    except odoorpc.error.InternalError as e:
        logger.error(f"OdooRPC internal error fetching invoices: {str(e)}")
        raise ValueError(f"OdooRPC internal error: {str(e)}")
    except Exception as e:
        logger.exception(f"Error fetching invoices from Odoo: {str(e)}")
        raise ValueError(f"Error fetching invoices: {str(e)}")
