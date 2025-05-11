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


def test_odoo_connection(connection_params: Union[OdooConnectionTestRequest, OdooConfig]) -> IntegrationTestResult:
    """
    Test connection to an Odoo server using OdooRPC with enhanced Odoo 18+ support.
    Also checks for FIRS integration capabilities based on environment setting.
    
    Args:
        connection_params: Connection parameters for Odoo server
        
    Returns:
        IntegrationTestResult with success status, message, and details
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
        major_version = int(version_info.get('server_version_info', [0])[0])
        
        # Test access to partners to verify permissions
        partner_count = 0
        try:
            partners = odoo.env['res.partner'].search([('is_company', '=', True)], limit=5)
            partner_count = len(partners) if partners else 0
        except Exception as e:
            logger.warning(f"Access to partners limited: {str(e)}")
        
        # Test invoice access and capabilities
        invoice_features = {}
        try:
            # Check for account.move model (used for invoices in recent Odoo versions)
            if 'account.move' in odoo.env:
                invoice_model = 'account.move'
                invoice_count = odoo.env[invoice_model].search_count([('move_type', 'in', ['out_invoice', 'out_refund'])])
                invoice_features['model'] = invoice_model
                invoice_features['count'] = invoice_count
                
                # Test Odoo 18+ specific features if available
                if major_version >= 18:
                    # Check for e-invoicing capabilities
                    module_list = odoo.env['ir.module.module'].search_read(
                        [('name', 'in', ['account_edi', 'l10n_ng_einvoice']), ('state', '=', 'installed')],
                        ['name', 'state']
                    )
                    invoice_features['e_invoice_modules'] = {mod['name']: mod['state'] for mod in module_list}
                    
                    # Check for IRN field support
                    has_irn_field = False
                    try:
                        fields_data = odoo.env[invoice_model].fields_get(['irn_number', 'l10n_ng_irn'])
                        has_irn_field = any(f in fields_data for f in ['irn_number', 'l10n_ng_irn'])
                    except:
                        pass
                    invoice_features['irn_field_support'] = has_irn_field
        except Exception as e:
            logger.warning(f"Cannot test invoice access: {str(e)}")
            invoice_features['error'] = str(e)
        
        # Test for API endpoints - specific to Odoo 18+
        api_endpoints = {}
        if major_version >= 18:
            try:
                # Check if REST API module is installed
                rest_api_installed = odoo.env['ir.module.module'].search_count(
                    [('name', 'in', ['restful', 'rest_api']), ('state', '=', 'installed')]
                ) > 0
                api_endpoints['rest_api_available'] = rest_api_installed
            except Exception as e:
                logger.warning(f"Cannot check REST API availability: {str(e)}")
                api_endpoints['error'] = str(e)
        
        # Check FIRS integration capabilities based on environment setting
        firs_env = getattr(connection_params, 'firs_environment', 'sandbox')
        firs_features = {}
        try:
            # Check for FIRS-related fields and modules
            firs_modules = odoo.env['ir.module.module'].search_read(
                [('name', 'like', 'firs'), ('state', '=', 'installed')],
                ['name', 'state']
            )
            firs_features['modules'] = {mod['name']: mod['state'] for mod in firs_modules}
            
            # Check for FIRS sandbox configuration
            if firs_env == 'sandbox':
                # For sandbox environment, validate the test endpoint availability
                firs_features['sandbox_ready'] = True
                firs_features['environment'] = 'sandbox'
            else:
                # For production environment
                firs_features['production_ready'] = True
                firs_features['environment'] = 'production'
        except Exception as e:
            logger.warning(f"Cannot check FIRS integration capabilities: {str(e)}")
            firs_features['error'] = str(e)
        
        return IntegrationTestResult(
            success=True,
            message=f"Successfully connected to Odoo server as {user.name}",
            details={
                "version_info": version_info,
                "major_version": major_version,
                "uid": odoo.env.uid,
                "user_name": user.name,
                "partner_count": partner_count,
                "invoice_features": invoice_features,
                "api_endpoints": api_endpoints,
                "is_odoo18_plus": major_version >= 18,
                "firs_features": firs_features
            }
        )
        
    except odoorpc.error.RPCError as e:
        logger.error(f"OdooRPC error: {str(e)}")
        return IntegrationTestResult(
            success=False,
            message=f"OdooRPC error: {str(e)}",
            details={
                "error": str(e), 
                "error_type": "RPCError",
                "error_code": getattr(e, 'code', None),
                "error_data": getattr(e, 'data', None)
            }
        )
    except odoorpc.error.InternalError as e:
        logger.error(f"OdooRPC internal error: {str(e)}")
        return IntegrationTestResult(
            success=False,
            message=f"OdooRPC internal error: {str(e)}",
            details={
                "error": str(e), 
                "error_type": "InternalError"
            }
        )
    except Exception as e:
        logger.exception(f"Error testing Odoo connection: {str(e)}")
        return IntegrationTestResult(
            success=False,
            message=f"Error connecting to Odoo server: {str(e)}",
            details={
                "error": str(e), 
                "error_type": type(e).__name__
            }
        )


def fetch_odoo_invoices(
    config: OdooConfig,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    include_draft: bool = False,
    include_attachments: bool = False,
    page: int = 1,
    page_size: int = 20
) -> Dict[str, Any]:
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
            
            # Fetch PDF attachments if requested
            if include_attachments:
                try:
                    Attachment = odoo.env['ir.attachment']
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
                                "url": f"{config.url}/web/content/{attachment.id}?download=true"
                            })
                        invoice_data["attachments"] = attachments
                except Exception as e:
                    logger.warning(f"Error fetching attachments for invoice {invoice.id}: {str(e)}")
                    invoice_data["attachments_error"] = str(e)
            
            invoices.append(invoice_data)
        
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
        error_data = {
            "error": str(e),
            "error_type": "RPCError",
            "error_code": getattr(e, 'code', None),
            "error_data": getattr(e, 'data', None)
        }
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
            "error": error_data
        }
    except odoorpc.error.InternalError as e:
        logger.error(f"OdooRPC internal error fetching invoices: {str(e)}")
        error_data = {
            "error": str(e),
            "error_type": "InternalError"
        }
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
            "error": error_data
        }
    except Exception as e:
        logger.exception(f"Error fetching invoices from Odoo: {str(e)}")
        error_data = {
            "error": str(e),
            "error_type": type(e).__name__
        }
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
            "error": error_data
        }


def generate_irn_for_odoo_invoice(
    config: OdooConfig,
    invoice_id: int,
    integration_id: str,
    service_id: str,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate an IRN (Invoice Reference Number) for an Odoo invoice.
    
    Args:
        config: Odoo configuration
        invoice_id: ID of the Odoo invoice
        integration_id: ID of the integration
        service_id: Service ID for the IRN
        user_id: ID of the user generating the IRN (optional)
        
    Returns:
        Dictionary with IRN details
    """
    from app.models.irn import IRNRecord, InvoiceData, IRNStatus
    from app.db.session import SessionLocal
    import hashlib
    import secrets
    from datetime import datetime, timedelta
    
    try:
        # Connect to Odoo
        parsed_url = urlparse(str(config.url))
        host = parsed_url.netloc.split(':')[0]
        protocol = parsed_url.scheme or 'jsonrpc'
        
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
        
        # Fetch the invoice data
        Invoice = odoo.env['account.move']
        
        # Use search_read to avoid frozendict issues
        invoice_data = Invoice.search_read(
            [('id', '=', invoice_id)],
            [
                'name', 'ref', 'invoice_date', 'amount_total', 'amount_untaxed', 'amount_tax',
                'partner_id', 'invoice_line_ids', 'state', 'currency_id'
            ]
        )
        
        if not invoice_data:
            return {
                "success": False,
                "message": f"Invoice with ID {invoice_id} not found",
                "details": {"error_type": "NotFound"}
            }
        
        invoice = invoice_data[0]
        
        # Get partner info
        partner_id = invoice['partner_id'][0] if invoice.get('partner_id') else None
        partner_name = invoice['partner_id'][1] if invoice.get('partner_id') else "Unknown"
        
        # Get partner details including VAT if available
        partner_vat = None
        if partner_id:
            try:
                partner_data = odoo.env['res.partner'].search_read(
                    [('id', '=', partner_id)],
                    ['vat']
                )
                if partner_data and partner_data[0].get('vat'):
                    partner_vat = partner_data[0]['vat']
            except Exception as e:
                logger.warning(f"Could not fetch partner VAT: {str(e)}")
        
        # Get currency info
        currency_id = invoice['currency_id'][0] if invoice.get('currency_id') else None
        currency_code = invoice['currency_id'][1] if invoice.get('currency_id') else "NGN"
        
        # Get invoice lines
        line_ids = invoice.get('invoice_line_ids', [])
        line_items = []
        
        if line_ids:
            try:
                line_data = odoo.env['account.move.line'].search_read(
                    [('id', 'in', line_ids), ('display_type', 'in', (None, 'product'))],
                    ['name', 'quantity', 'price_unit', 'price_subtotal', 'product_id']
                )
                
                for line in line_data:
                    product_name = line['product_id'][1] if line.get('product_id') else line.get('name', 'Unknown')
                    line_items.append({
                        "name": product_name,
                        "quantity": float(line.get('quantity', 0)),
                        "price_unit": float(line.get('price_unit', 0)),
                        "price_subtotal": float(line.get('price_subtotal', 0))
                    })
            except Exception as e:
                logger.warning(f"Error fetching invoice lines: {str(e)}")
        
        # Generate line items hash for verification
        line_items_json = json.dumps(line_items, sort_keys=True)
        line_items_hash = hashlib.sha256(line_items_json.encode()).hexdigest()
        
        # Generate hash of invoice data for verification
        invoice_hash_data = {
            "invoice_id": invoice_id,
            "invoice_number": invoice.get('name', ''),
            "invoice_date": str(invoice.get('invoice_date', '')),
            "partner_id": partner_id,
            "partner_name": partner_name,
            "amount_total": float(invoice.get('amount_total', 0)),
            "currency_code": currency_code,
            "line_items_hash": line_items_hash,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        invoice_hash_json = json.dumps(invoice_hash_data, sort_keys=True)
        hash_value = hashlib.sha256(invoice_hash_json.encode()).hexdigest()
        
        # Generate verification code
        verification_code = secrets.token_hex(16)
        
        # Generate timestamp (YYYYMMDD)
        timestamp = datetime.utcnow().strftime('%Y%m%d')
        
        # Create IRN value: service_id + timestamp + 8 chars of hash
        irn_value = f"{service_id}-{timestamp}-{hash_value[:8]}"
        
        # Calculate valid until date (30 days by default)
        valid_until = datetime.utcnow() + timedelta(days=30)
        
        # Create database session
        db = SessionLocal()
        
        try:
            # Create IRN record
            irn_record = IRNRecord(
                irn=irn_value,
                integration_id=integration_id,
                invoice_number=invoice.get('name', '') or f"ODO-{invoice_id}",
                service_id=service_id,
                timestamp=timestamp,
                valid_until=valid_until,
                status=IRNStatus.UNUSED,
                hash_value=hash_value,
                verification_code=verification_code,
                issued_by=user_id,
                odoo_invoice_id=invoice_id,
                meta_data={"source": "odoo", "odoo_id": invoice_id}
            )
            
            db.add(irn_record)
            db.flush()
            
            # Create invoice data record
            invoice_data = InvoiceData(
                irn=irn_value,
                invoice_number=invoice.get('name', '') or f"ODO-{invoice_id}",
                invoice_date=datetime.strptime(invoice.get('invoice_date', datetime.utcnow().strftime('%Y-%m-%d')), '%Y-%m-%d') if invoice.get('invoice_date') else datetime.utcnow(),
                customer_name=partner_name,
                customer_tax_id=partner_vat,
                total_amount=float(invoice.get('amount_total', 0)),
                currency_code=currency_code,
                line_items_hash=line_items_hash,
                line_items_data=line_items,
                odoo_partner_id=partner_id,
                odoo_currency_id=currency_id
            )
            
            db.add(invoice_data)
            db.commit()
            
            return {
                "success": True,
                "message": f"Successfully generated IRN for invoice {invoice.get('name', '')}",
                "details": {
                    "irn": irn_value,
                    "invoice_id": invoice_id,
                    "invoice_number": invoice.get('name', ''),
                    "valid_until": valid_until.isoformat(),
                    "verification_code": verification_code
                }
            }
            
        except Exception as e:
            db.rollback()
            logger.exception(f"Error creating IRN record: {str(e)}")
            return {
                "success": False,
                "message": f"Error creating IRN record: {str(e)}",
                "details": {"error_type": "DatabaseError"}
            }
        finally:
            db.close()
        
    except odoorpc.error.RPCError as e:
        logger.error(f"OdooRPC error: {str(e)}")
        return {
            "success": False,
            "message": f"OdooRPC error: {str(e)}",
            "details": {"error_type": "RPCError"}
        }
    except Exception as e:
        logger.exception(f"Error generating IRN: {str(e)}")
        return {
            "success": False,
            "message": f"Error generating IRN: {str(e)}",
            "details": {"error_type": type(e).__name__}
        }


def validate_irn(irn_value: str) -> Dict[str, Any]:
    """
    Validate an IRN.
    
    Args:
        irn_value: The IRN to validate
        
    Returns:
        Dictionary with validation result
    """
    from app.models.irn import IRNRecord, IRNValidationRecord, IRNStatus
    from app.db.session import SessionLocal
    from sqlalchemy.orm import joinedload
    
    db = SessionLocal()
    
    try:
        # Fetch IRN record with related invoice data
        irn_record = db.query(IRNRecord).options(
            joinedload(IRNRecord.invoice_data)
        ).filter(IRNRecord.irn == irn_value).first()
        
        if not irn_record:
            result = {
                "success": False,
                "message": "IRN not found",
                "details": {"error_type": "NotFound"}
            }
            return result
        
        # Check if IRN is active
        now = datetime.utcnow()
        
        if irn_record.status == IRNStatus.EXPIRED or irn_record.valid_until < now:
            # Update status to expired if necessary
            if irn_record.status != IRNStatus.EXPIRED:
                irn_record.status = IRNStatus.EXPIRED
                db.commit()
            
            result = {
                "success": False,
                "message": "IRN has expired",
                "details": {
                    "error_type": "Expired",
                    "valid_until": irn_record.valid_until.isoformat() if irn_record.valid_until else None
                }
            }
        elif irn_record.status == IRNStatus.REVOKED:
            result = {
                "success": False,
                "message": "IRN has been revoked",
                "details": {"error_type": "Revoked"}
            }
        elif irn_record.status == IRNStatus.INVALID:
            result = {
                "success": False,
                "message": "IRN is invalid",
                "details": {"error_type": "Invalid"}
            }
        else:
            # IRN is valid (unused or active)
            invoice_data = irn_record.invoice_data if irn_record.invoice_data else None
            
            result = {
                "success": True,
                "message": "IRN is valid",
                "details": {
                    "status": irn_record.status,
                    "invoice_number": irn_record.invoice_number,
                    "valid_until": irn_record.valid_until.isoformat() if irn_record.valid_until else None,
                    "invoice_data": {
                        "customer_name": invoice_data.customer_name if invoice_data else None,
                        "invoice_date": invoice_data.invoice_date.isoformat() if invoice_data and invoice_data.invoice_date else None,
                        "total_amount": invoice_data.total_amount if invoice_data else None,
                        "currency_code": invoice_data.currency_code if invoice_data else None
                    } if invoice_data else None
                }
            }
            
            # If the IRN was unused, mark it as active now
            if irn_record.status == IRNStatus.UNUSED:
                irn_record.status = IRNStatus.ACTIVE
                irn_record.used_at = now
                db.commit()
        
        # Record this validation event
        validation_record = IRNValidationRecord(
            irn=irn_value,
            validation_status=result["success"],
            validation_message=result["message"],
            validation_source="api",
            request_data={"validation_type": "standard"},
            response_data=result
        )
        
        db.add(validation_record)
        db.commit()
        
        return result
    
    except Exception as e:
        db.rollback()
        logger.exception(f"Error validating IRN: {str(e)}")
        return {
            "success": False,
            "message": f"Error validating IRN: {str(e)}",
            "details": {"error_type": "ValidationError"}
        }
    finally:
        db.close()


def get_irn_for_odoo_invoice(odoo_invoice_id: int) -> Dict[str, Any]:
    """
    Get IRN records for an Odoo invoice.
    
    Args:
        odoo_invoice_id: The Odoo invoice ID
        
    Returns:
        Dictionary with IRN details
    """
    from app.models.irn import IRNRecord
    from app.db.session import SessionLocal
    from sqlalchemy.orm import joinedload
    
    db = SessionLocal()
    
    try:
        # Fetch IRN records for the invoice
        irn_records = db.query(IRNRecord).options(
            joinedload(IRNRecord.invoice_data)
        ).filter(IRNRecord.odoo_invoice_id == odoo_invoice_id).all()
        
        if not irn_records:
            return {
                "success": False,
                "message": f"No IRN records found for Odoo invoice ID {odoo_invoice_id}",
                "details": {"error_type": "NotFound"}
            }
        
        # Format result
        irns = []
        for record in irn_records:
            irns.append({
                "irn": record.irn,
                "status": record.status,
                "generated_at": record.generated_at.isoformat() if record.generated_at else None,
                "valid_until": record.valid_until.isoformat() if record.valid_until else None,
                "used_at": record.used_at.isoformat() if record.used_at else None,
                "invoice_number": record.invoice_number
            })
        
        return {
            "success": True,
            "message": f"Found {len(irns)} IRN records for Odoo invoice ID {odoo_invoice_id}",
            "details": {
                "irn_records": irns
            }
        }
    
    except Exception as e:
        logger.exception(f"Error getting IRN for Odoo invoice: {str(e)}")
        return {
            "success": False,
            "message": f"Error getting IRN for Odoo invoice: {str(e)}",
            "details": {"error_type": "QueryError"}
        }
    finally:
        db.close()
