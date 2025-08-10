"""
FIRS SI ERP Integration Service

This service implements System Integrator (SI) specific functionality for
ERP system integration and data extraction.

SI Role Responsibilities:
- Connect to various ERP systems (Odoo, SAP, Oracle, etc.)
- Extract invoice data from ERP systems
- Transform ERP data to FIRS-compliant format
- Manage ERP system credentials and connections
- Handle ERP-specific data validation and mapping
- Provide ERP system status monitoring

This service is part of the firs_si package and focuses on the SI's core
responsibility of ERP system integration and data extraction.
"""
import json
import logging
import ssl
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union, cast
from urllib.parse import urlparse
import odoorpc

from app.services.firs_si.odoo_connector import OdooConnector, OdooConnectionError, OdooAuthenticationError, OdooDataError
from app.schemas.integration import OdooAuthMethod, OdooConnectionTestRequest, OdooConfig, IntegrationTestResult

logger = logging.getLogger(__name__)


def test_odoo_connection(connection_params: Union[OdooConnectionTestRequest, OdooConfig]) -> IntegrationTestResult:
    """
    Test connection to an Odoo server using the OdooConnector.
    
    Args:
        connection_params: Connection parameters for Odoo server
        
    Returns:
        IntegrationTestResult with success status, message, and details
    """
    try:
        # Create an OdooConnector instance
        connector = OdooConnector(connection_params)
        
        # Authenticate to test the connection
        connector.authenticate()
        
        # Get user info
        user_info = connector.get_user_info()
        
        # Get server version
        version_info = connector.version_info
        major_version = connector.major_version
        
        # Test access to partners to verify permissions
        partner_count = 0
        try:
            partners = connector.odoo.env['res.partner'].search([('is_company', '=', True)], limit=5)
            partner_count = len(partners) if partners else 0
        except Exception as e:
            logger.warning(f"Access to partners limited: {str(e)}")
        
        # Test invoice access and capabilities
        invoice_features = {}
        try:
            # Check for account.move model (used for invoices in recent Odoo versions)
            if 'account.move' in connector.odoo.env:
                invoice_model = 'account.move'
                invoice_count = connector.odoo.env[invoice_model].search_count([('move_type', 'in', ['out_invoice', 'out_refund'])])
                invoice_features['model'] = invoice_model
                invoice_features['count'] = invoice_count
                
                # Test Odoo 18+ specific features if available
                if major_version >= 18:
                    # Check for e-invoicing capabilities
                    module_list = connector.odoo.env['ir.module.module'].search_read(
                        [('name', 'in', ['account_edi', 'l10n_ng_einvoice']), ('state', '=', 'installed')],
                        ['name', 'state']
                    )
                    invoice_features['e_invoice_modules'] = {mod['name']: mod['state'] for mod in module_list}
                    
                    # Check for IRN field support
                    has_irn_field = False
                    try:
                        fields_data = connector.odoo.env[invoice_model].fields_get(['irn_number', 'l10n_ng_irn'])
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
                rest_api_installed = connector.odoo.env['ir.module.module'].search_count(
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
            firs_modules = connector.odoo.env['ir.module.module'].search_read(
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
            message=f"Successfully connected to Odoo server as {user_info['name']}",
            details={
                "version_info": version_info,
                "major_version": major_version,
                "uid": connector.odoo.env.uid,
                "user_name": user_info['name'],
                "partner_count": partner_count,
                "invoice_features": invoice_features,
                "api_endpoints": api_endpoints,
                "is_odoo18_plus": major_version >= 18,
                "firs_features": firs_features
            }
        )
        
    except OdooConnectionError as e:
        logger.error(f"Odoo connection error: {str(e)}")
        return IntegrationTestResult(
            success=False,
            message=f"Connection error: {str(e)}",
            details={"error": str(e), "error_type": "ConnectionError"}
        )
    except OdooAuthenticationError as e:
        logger.error(f"Odoo authentication error: {str(e)}")
        return IntegrationTestResult(
            success=False,
            message=f"Authentication error: {str(e)}",
            details={"error": str(e), "error_type": "AuthenticationError"}
        )
    except Exception as e:
        logger.exception(f"Error testing Odoo connection: {str(e)}")
        return IntegrationTestResult(
            success=False,
            message=f"Error connecting to Odoo server: {str(e)}",
            details={"error": str(e), "error_type": type(e).__name__}
        )


def _create_error_response(page: int, page_size: int, error_data: Dict[str, Any]) -> Dict[str, Any]:
    """Helper function to create a standard error response with pagination metadata."""
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
    Fetch invoices from Odoo server using OdooConnector.
    
    Args:
        config: Odoo configuration
        from_date: Fetch invoices from this date
        to_date: Fetch invoices up to this date
        include_draft: Whether to include draft invoices
        include_attachments: Whether to include document attachments
        page: Page number for pagination
        page_size: Number of records per page
        
    Returns:
        Dictionary with invoices and pagination metadata
    """
    try:
        # Create connector and authenticate
        connector = OdooConnector(config)
        
        # Get invoices with pagination
        return connector.get_invoices(
            from_date=from_date,
            to_date=to_date,
            include_draft=include_draft,
            include_attachments=include_attachments,
            page=page,
            page_size=page_size
        )
        
    except OdooConnectionError as e:
        logger.error(f"Odoo connection error: {str(e)}")
        error_data = {"error": str(e), "error_type": "ConnectionError"}
        return _create_error_response(page, page_size, error_data)
    except OdooAuthenticationError as e:
        logger.error(f"Odoo authentication error: {str(e)}")
        error_data = {"error": str(e), "error_type": "AuthenticationError"}
        return _create_error_response(page, page_size, error_data)
    except OdooDataError as e:
        logger.error(f"Odoo data error: {str(e)}")
        error_data = {"error": str(e), "error_type": "DataError"}
        return _create_error_response(page, page_size, error_data)
    except Exception as e:
        logger.exception(f"Error fetching invoices from Odoo: {str(e)}")
        error_data = {"error": str(e), "error_type": type(e).__name__}
        return _create_error_response(page, page_size, error_data)


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
    from datetime import datetime, timedelta
    import secrets
    import string
    
    db = SessionLocal()
    
    try:
        # Create connector and authenticate
        connector = OdooConnector(config)
        
        # Get the specific invoice data with the connector
        try:
            invoice_data = connector.get_invoice_by_id(invoice_id)
        except Exception as e:
            logger.error(f"Error retrieving invoice from Odoo: {str(e)}")
            return {"success": False, "error": f"Error retrieving invoice data: {str(e)}"}
            
        # Extract data from invoice_data
        invoice_number = invoice_data.get("invoice_number")
        if not invoice_number:
            return {"success": False, "error": "Invoice number not found"}
            
        # Extract partner (customer) data
        partner = invoice_data.get("partner", {})
        customer_name = partner.get("name", "")
        customer_tax_id = partner.get("vat")
        
        # Get invoice date
        invoice_date = invoice_data.get("invoice_date")
        if not invoice_date:
            invoice_date = datetime.utcnow().date()
        
        # Get invoice amount
        amount_total = invoice_data.get("amount_total", 0.0)
        currency = invoice_data.get("currency", {}).get("name", "NGN")
        
        # Extract line items
        line_items = []
        for line in invoice_data.get("lines", []):
            tax_percentage = sum(tax.get("amount", 0) for tax in line.get("taxes", []))
            line_data = {
                "description": line.get("name", ""),
                "quantity": line.get("quantity", 0),
                "unit_price": line.get("price_unit", 0.0),
                "subtotal": line.get("price_subtotal", 0.0),
                "tax_percentage": tax_percentage,
                "product_code": line.get("product", {}).get("default_code", None),
            }
            line_items.append(line_data)
        
        # Generate hash for the line items
        line_items_str = json.dumps(line_items, sort_keys=True)
        line_items_hash = hashlib.sha256(line_items_str.encode()).hexdigest()
        
        # Generate a random component to ensure uniqueness
        random_chars = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        
        # Combine all components to create the IRN
        timestamp = datetime.utcnow().strftime("%H%M%S")
        date_str = datetime.utcnow().strftime("%Y%m%d")
        irn_base = f"{service_id}{date_str}{timestamp}{invoice_id}{random_chars}"
        irn_hash = hashlib.sha256(irn_base.encode()).hexdigest()[:10].upper()
        irn = f"{service_id}-{date_str}-{timestamp}-{irn_hash}"
        
        # Create verification code (for future validation)
        verification_code = secrets.token_hex(16)
        
        # Prepare hash value for verification
        data_to_hash = f"{irn}|{invoice_number}|{amount_total}|{invoice_date}"
        hash_value = hashlib.sha256(data_to_hash.encode()).hexdigest()
        
        # IRN has already been created above
        irn_value = irn
        
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


def search_odoo_invoices(
    config: OdooConfig,
    search_term: str,
    include_attachments: bool = False,
    page: int = 1,
    page_size: int = 20
) -> Dict[str, Any]:
    """
    Search for invoices in Odoo by various criteria.
    
    Args:
        config: Odoo configuration
        search_term: Text to search for in invoice number, reference, or partner name
        include_attachments: Whether to include document attachments
        page: Page number for pagination
        page_size: Number of records per page
        
    Returns:
        Dictionary with matching invoices and pagination metadata
    """
    try:
        connector = OdooConnector(config)
        return connector.search_invoices(
            search_term=search_term,
            include_attachments=include_attachments,
            page=page,
            page_size=page_size
        )
    except OdooConnectionError as e:
        logger.error(f"Odoo connection error: {str(e)}")
        error_data = {"error": str(e), "error_type": "ConnectionError"}
        return _create_error_response(page, page_size, error_data)
    except OdooAuthenticationError as e:
        logger.error(f"Odoo authentication error: {str(e)}")
        error_data = {"error": str(e), "error_type": "AuthenticationError"}
        return _create_error_response(page, page_size, error_data)
    except OdooDataError as e:
        logger.error(f"Odoo data error: {str(e)}")
        error_data = {"error": str(e), "error_type": "DataError"}
        return _create_error_response(page, page_size, error_data)
    except Exception as e:
        logger.exception(f"Error searching Odoo invoices: {str(e)}")
        error_data = {"error": str(e), "error_type": type(e).__name__}
        return _create_error_response(page, page_size, error_data)


def fetch_odoo_partners(
    config: OdooConfig,
    search_term: Optional[str] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """
    Fetch partners/customers from Odoo.
    
    Args:
        config: Odoo configuration
        search_term: Optional term to search for in partner name or reference
        limit: Maximum number of partners to return
        
    Returns:
        Dictionary with partners list
    """
    try:
        connector = OdooConnector(config)
        partners = connector.get_partners(search_term=search_term, limit=limit)
        return {
            "success": True,
            "partners": partners,
            "count": len(partners)
        }
    except OdooConnectionError as e:
        logger.error(f"Odoo connection error: {str(e)}")
        return {
            "success": False,
            "partners": [],
            "count": 0,
            "error": str(e),
            "error_type": "ConnectionError"
        }
    except OdooAuthenticationError as e:
        logger.error(f"Odoo authentication error: {str(e)}")
        return {
            "success": False,
            "partners": [],
            "count": 0,
            "error": str(e),
            "error_type": "AuthenticationError"
        }
    except OdooDataError as e:
        logger.error(f"Odoo data error: {str(e)}")
        return {
            "success": False,
            "partners": [],
            "count": 0,
            "error": str(e),
            "error_type": "DataError"
        }
    except Exception as e:
        logger.exception(f"Error fetching Odoo partners: {str(e)}")
        return {
            "success": False,
            "partners": [],
            "count": 0,
            "error": str(e),
            "error_type": type(e).__name__
        }


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
