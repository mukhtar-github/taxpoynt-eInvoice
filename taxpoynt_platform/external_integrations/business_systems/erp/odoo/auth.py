"""
Odoo Authentication Module
Handles connection management and authentication for Odoo ERP.
"""

import logging
import ssl
from urllib.parse import urlparse
from typing import Any, Dict
from functools import wraps

import odoorpc

from app.schemas.integration import OdooAuthMethod, OdooConfig
from .exceptions import OdooConnectionError, OdooAuthenticationError

logger = logging.getLogger(__name__)


class OdooAuthenticator:
    """Manages Odoo connection and authentication."""
    
    def __init__(self, config: OdooConfig):
        """Initialize Odoo authenticator with configuration."""
        self.config = config
        self.odoo = None
        self.version_info = None
        self.major_version = None
        self.host = None
        self.protocol = None
        self.port = None
        
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
    
    def get_user_info(self) -> Dict[str, Any]:
        """
        Get information about the authenticated user - SI Role Function.
        
        Retrieves user information from Odoo ERP for System Integrator
        session management and audit tracking.
        
        Returns:
            Dict with user information
        """
        if not self.odoo or not self.odoo.env:
            raise OdooConnectionError("Not connected to Odoo")
            
        user = self.odoo.env.user
        return {
            "id": user.id,
            "name": user.name,
            "login": user.login,
            "email": user.email if hasattr(user, "email") else None,
            "company_id": user.company_id.id if user.company_id else None,
            "company_name": user.company_id.name if user.company_id else None,
            "groups": [group.name for group in user.groups_id] if hasattr(user, 'groups_id') else []
        }
    
    def get_company_info(self) -> Dict[str, Any]:
        """
        Get information about the company - SI Role Function.
        
        Retrieves company information from Odoo ERP for System Integrator
        business context and data extraction scope.
        
        Returns:
            Dict with company information
        """
        if not self.odoo or not self.odoo.env:
            raise OdooConnectionError("Not connected to Odoo")
            
        company = self.odoo.env.user.company_id
        return {
            "id": company.id,
            "name": company.name,
            "vat": company.vat if hasattr(company, 'vat') else None,
            "email": company.email if hasattr(company, 'email') else None,
            "phone": company.phone if hasattr(company, 'phone') else None,
            "website": company.website if hasattr(company, 'website') else None,
            "street": company.street if hasattr(company, 'street') else None,
            "street2": company.street2 if hasattr(company, 'street2') else None,
            "city": company.city if hasattr(company, 'city') else None,
            "state_id": company.state_id.name if hasattr(company, 'state_id') and company.state_id else None,
            "zip": company.zip if hasattr(company, 'zip') else None,
            "country_id": company.country_id.name if hasattr(company, 'country_id') and company.country_id else None,
            "currency": company.currency_id.name if hasattr(company, 'currency_id') else None,
            "logo": bool(company.logo) if hasattr(company, 'logo') else False
        }
    
    def is_connected(self) -> bool:
        """Check if connected and authenticated to Odoo."""
        try:
            return self.odoo is not None and self.odoo.env is not None
        except:
            return False


def ensure_connected(func):
    """
    Decorator to ensure the connector is connected and authenticated.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            if not self.authenticator.is_connected():
                self.authenticator.authenticate()
            return func(self, *args, **kwargs)
        except (odoorpc.error.RPCError, odoorpc.error.InternalError) as e:
            # Handle session timeout by trying to reconnect once
            logger.warning(f"OdooRPC connection error, attempting to reconnect: {str(e)}")
            try:
                self.authenticator.authenticate()
                return func(self, *args, **kwargs)
            except Exception as e2:
                logger.error(f"Failed to reconnect to Odoo: {str(e2)}")
                raise
        except Exception as e:
            logger.error(f"Error in OdooConnector: {str(e)}")
            raise
    return wrapper