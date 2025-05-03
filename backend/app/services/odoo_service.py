"""
Odoo Integration Service for connecting to Odoo instances using XML-RPC or JSON-RPC.
"""
import json
import logging
import random
import ssl
import urllib.request
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.error import URLError, HTTPError

import xmlrpc.client
from app.schemas.integration import OdooAuthMethod, OdooConnectionTestRequest, OdooConfig

logger = logging.getLogger(__name__)


def test_odoo_connection(connection_params: Union[OdooConnectionTestRequest, OdooConfig]) -> Dict[str, Any]:
    """
    Test connection to an Odoo server using the provided parameters.
    
    Args:
        connection_params: Connection parameters for Odoo server
        
    Returns:
        Dictionary with test results
    """
    try:
        # Determine whether to use XML-RPC or JSON-RPC
        if getattr(connection_params, "rpc_path", "/jsonrpc") == "/jsonrpc":
            # Use JSON-RPC (default)
            result = test_odoo_jsonrpc(connection_params)
        else:
            # Use XML-RPC
            result = test_odoo_xmlrpc(connection_params)
        
        return result
        
    except Exception as e:
        logger.exception(f"Error testing Odoo connection: {str(e)}")
        return {
            "success": False,
            "message": f"Error connecting to Odoo server: {str(e)}",
            "details": {"error": str(e), "error_type": type(e).__name__}
        }


def test_odoo_xmlrpc(connection_params: Union[OdooConnectionTestRequest, OdooConfig]) -> Dict[str, Any]:
    """
    Test connection to an Odoo server using XML-RPC.
    
    Args:
        connection_params: Connection parameters for Odoo server
        
    Returns:
        Dictionary with test results
    """
    try:
        url = str(connection_params.url)
        if url.endswith('/'):
            url = url[:-1]
            
        # Connect to the server
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
        
        # Get server version info
        version_info = common.version()
        
        # Try to authenticate
        auth_result = None
        if connection_params.auth_method == OdooAuthMethod.PASSWORD:
            uid = common.authenticate(
                connection_params.database,
                connection_params.username,
                connection_params.password,
                {}
            )
            auth_result = uid
        else:  # API key
            uid = common.authenticate(
                connection_params.database,
                connection_params.username,
                connection_params.api_key,
                {}
            )
            auth_result = uid
            
        if not auth_result:
            return {
                "success": False,
                "message": "Authentication failed. Invalid credentials.",
                "details": {"version_info": version_info}
            }
            
        # Try to list a few partners to verify access
        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
        
        # Test access to res.partner model with a simple search
        partners = models.execute_kw(
            connection_params.database,
            auth_result,
            connection_params.password if connection_params.auth_method == OdooAuthMethod.PASSWORD else connection_params.api_key,
            'res.partner',
            'search_read',
            [[['is_company', '=', True]]],
            {'fields': ['name', 'email'], 'limit': 5}
        )
        
        return {
            "success": True,
            "message": "Successfully connected to Odoo server",
            "details": {
                "version_info": version_info,
                "uid": auth_result,
                "partner_count": len(partners) if partners else 0
            }
        }
        
    except xmlrpc.client.Fault as e:
        logger.error(f"XML-RPC fault: {str(e)}")
        return {
            "success": False,
            "message": f"XML-RPC fault: {str(e)}",
            "details": {"fault_code": getattr(e, "faultCode", None)}
        }
    except (ConnectionRefusedError, URLError) as e:
        logger.error(f"Connection error: {str(e)}")
        return {
            "success": False,
            "message": f"Could not connect to Odoo server: {str(e)}",
            "details": {"error": str(e)}
        }
    except Exception as e:
        logger.exception(f"Error in XML-RPC connection: {str(e)}")
        return {
            "success": False,
            "message": f"Error connecting to Odoo server: {str(e)}",
            "details": {"error": str(e), "error_type": type(e).__name__}
        }


def test_odoo_jsonrpc(connection_params: Union[OdooConnectionTestRequest, OdooConfig]) -> Dict[str, Any]:
    """
    Test connection to an Odoo server using JSON-RPC.
    
    Args:
        connection_params: Connection parameters for Odoo server
        
    Returns:
        Dictionary with test results
    """
    try:
        url = str(connection_params.url)
        if url.endswith('/'):
            url = url[:-1]
            
        jsonrpc_url = f"{url}/jsonrpc"
        
        # First, get version info
        version_info = json_rpc(
            jsonrpc_url,
            "call",
            {
                "service": "common",
                "method": "version",
                "args": []
            }
        )
        
        # Try to authenticate
        auth_args = [
            connection_params.database,
            connection_params.username,
            connection_params.password if connection_params.auth_method == OdooAuthMethod.PASSWORD else connection_params.api_key,
            {}
        ]
        
        uid = json_rpc(
            jsonrpc_url,
            "call",
            {
                "service": "common",
                "method": "authenticate",
                "args": auth_args
            }
        )
        
        if not uid:
            return {
                "success": False,
                "message": "Authentication failed. Invalid credentials.",
                "details": {"version_info": version_info}
            }
            
        # Try to list a few partners to verify access
        partners = json_rpc(
            jsonrpc_url,
            "call",
            {
                "service": "object",
                "method": "execute_kw",
                "args": [
                    connection_params.database,
                    uid,
                    connection_params.password if connection_params.auth_method == OdooAuthMethod.PASSWORD else connection_params.api_key,
                    'res.partner',
                    'search_read',
                    [[['is_company', '=', True]]],
                    {'fields': ['name', 'email'], 'limit': 5}
                ]
            }
        )
        
        return {
            "success": True,
            "message": "Successfully connected to Odoo server",
            "details": {
                "version_info": version_info,
                "uid": uid,
                "partner_count": len(partners) if partners else 0
            }
        }
        
    except HTTPError as e:
        logger.error(f"HTTP error: {str(e)}")
        return {
            "success": False,
            "message": f"HTTP error: {str(e)}",
            "details": {"status_code": e.code}
        }
    except (ConnectionRefusedError, URLError) as e:
        logger.error(f"Connection error: {str(e)}")
        return {
            "success": False,
            "message": f"Could not connect to Odoo server: {str(e)}",
            "details": {"error": str(e)}
        }
    except Exception as e:
        logger.exception(f"Error in JSON-RPC connection: {str(e)}")
        return {
            "success": False,
            "message": f"Error connecting to Odoo server: {str(e)}",
            "details": {"error": str(e), "error_type": type(e).__name__}
        }


def json_rpc(url: str, method: str, params: Dict[str, Any]) -> Any:
    """
    Generic JSON-RPC 2.0 request function.
    
    Args:
        url: The URL to the JSON-RPC endpoint
        method: The JSON-RPC method to call
        params: The parameters to pass to the method
        
    Returns:
        The result of the JSON-RPC call
    
    Raises:
        Exception: If the response contains an error
    """
    data = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": random.randint(0, 1000000000),
    }
    
    req = urllib.request.Request(
        url=url,
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"}
    )
    
    # Create SSL context that doesn't verify the certificate
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    response = urllib.request.urlopen(req, context=ctx)
    response_data = json.loads(response.read().decode('UTF-8'))
    
    if response_data.get("error"):
        raise Exception(response_data["error"])
    
    return response_data["result"]


def fetch_odoo_invoices(
    config: OdooConfig,
    from_date: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Fetch invoices from Odoo server.
    
    Args:
        config: Odoo configuration
        from_date: Fetch invoices from this date (default: None)
        limit: Maximum number of invoices to fetch (default: 100)
        offset: Offset for pagination (default: 0)
        
    Returns:
        List of invoice dictionaries
    """
    try:
        url = str(config.url)
        if url.endswith('/'):
            url = url[:-1]
            
        # Use JSON-RPC by default
        if config.rpc_path == "/jsonrpc":
            return fetch_odoo_invoices_jsonrpc(config, from_date, limit, offset)
        else:
            return fetch_odoo_invoices_xmlrpc(config, from_date, limit, offset)
            
    except Exception as e:
        logger.exception(f"Error fetching invoices: {str(e)}")
        return []


def fetch_odoo_invoices_xmlrpc(
    config: OdooConfig,
    from_date: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Fetch invoices from Odoo server using XML-RPC.
    
    Args:
        config: Odoo configuration
        from_date: Fetch invoices from this date (default: None)
        limit: Maximum number of invoices to fetch (default: 100)
        offset: Offset for pagination (default: 0)
        
    Returns:
        List of invoice dictionaries
    """
    url = str(config.url)
    if url.endswith('/'):
        url = url[:-1]
        
    # Connect to the server
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    
    # Authenticate
    password_or_key = config.password if config.auth_method == OdooAuthMethod.PASSWORD else config.api_key
    uid = common.authenticate(config.database, config.username, password_or_key, {})
    
    if not uid:
        logger.error("Authentication failed")
        return []
        
    # Connect to the models endpoint
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
    
    # Prepare the domain filter
    domain = [
        ('move_type', '=', 'out_invoice'),  # Customer invoices
        ('state', '=', 'posted')  # Posted (confirmed) invoices
    ]
    
    # Add date filter if specified
    if from_date:
        domain.append(('invoice_date', '>=', from_date.strftime('%Y-%m-%d')))
    
    # Fields to fetch
    fields = [
        'name', 'invoice_date', 'amount_total', 'amount_tax',
        'currency_id', 'partner_id', 'invoice_line_ids',
        'state', 'invoice_origin', 'ref'
    ]
    
    # Fetch invoices
    invoices = models.execute_kw(
        config.database, uid, password_or_key,
        'account.move', 'search_read',
        [domain],
        {
            'fields': fields,
            'limit': limit,
            'offset': offset,
            'order': 'invoice_date desc'
        }
    )
    
    # For each invoice, fetch its lines
    for invoice in invoices:
        if 'invoice_line_ids' in invoice and invoice['invoice_line_ids']:
            line_ids = invoice['invoice_line_ids']
            invoice_lines = models.execute_kw(
                config.database, uid, password_or_key,
                'account.move.line', 'read',
                [line_ids],
                {
                    'fields': [
                        'name', 'quantity', 'price_unit', 'tax_ids',
                        'price_subtotal', 'price_total', 'product_id'
                    ]
                }
            )
            invoice['lines'] = invoice_lines
    
    return invoices


def fetch_odoo_invoices_jsonrpc(
    config: OdooConfig,
    from_date: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Fetch invoices from Odoo server using JSON-RPC.
    
    Args:
        config: Odoo configuration
        from_date: Fetch invoices from this date (default: None)
        limit: Maximum number of invoices to fetch (default: 100)
        offset: Offset for pagination (default: 0)
        
    Returns:
        List of invoice dictionaries
    """
    url = str(config.url)
    if url.endswith('/'):
        url = url[:-1]
        
    jsonrpc_url = f"{url}/jsonrpc"
    
    # Authenticate
    password_or_key = config.password if config.auth_method == OdooAuthMethod.PASSWORD else config.api_key
    auth_args = [config.database, config.username, password_or_key, {}]
    
    uid = json_rpc(
        jsonrpc_url,
        "call",
        {
            "service": "common",
            "method": "authenticate",
            "args": auth_args
        }
    )
    
    if not uid:
        logger.error("Authentication failed")
        return []
    
    # Prepare the domain filter
    domain = [
        ('move_type', '=', 'out_invoice'),  # Customer invoices
        ('state', '=', 'posted')  # Posted (confirmed) invoices
    ]
    
    # Add date filter if specified
    if from_date:
        domain.append(('invoice_date', '>=', from_date.strftime('%Y-%m-%d')))
    
    # Fields to fetch
    fields = [
        'name', 'invoice_date', 'amount_total', 'amount_tax',
        'currency_id', 'partner_id', 'invoice_line_ids',
        'state', 'invoice_origin', 'ref'
    ]
    
    # Fetch invoices
    invoices = json_rpc(
        jsonrpc_url,
        "call",
        {
            "service": "object",
            "method": "execute_kw",
            "args": [
                config.database, uid, password_or_key,
                'account.move', 'search_read',
                [domain],
                {
                    'fields': fields,
                    'limit': limit,
                    'offset': offset,
                    'order': 'invoice_date desc'
                }
            ]
        }
    )
    
    # For each invoice, fetch its lines
    for invoice in invoices:
        if 'invoice_line_ids' in invoice and invoice['invoice_line_ids']:
            line_ids = invoice['invoice_line_ids']
            invoice_lines = json_rpc(
                jsonrpc_url,
                "call",
                {
                    "service": "object",
                    "method": "execute_kw",
                    "args": [
                        config.database, uid, password_or_key,
                        'account.move.line', 'read',
                        [line_ids],
                        {
                            'fields': [
                                'name', 'quantity', 'price_unit', 'tax_ids',
                                'price_subtotal', 'price_total', 'product_id'
                            ]
                        }
                    ]
                }
            )
            invoice['lines'] = invoice_lines
    
    return invoices
