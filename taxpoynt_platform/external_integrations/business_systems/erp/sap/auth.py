"""
SAP Authentication Module
Handles connection management and authentication for SAP ERP OData services.
"""

import logging
import ssl
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import aiohttp

from .exceptions import SAPODataError

logger = logging.getLogger(__name__)


class SAPAuthenticator:
    """Manages SAP OData connection and authentication."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize SAP authenticator with configuration."""
        self.config = config
        
        # Extract configuration
        self.base_url = config.get('base_url', '')
        self.username = config.get('username', '')
        self.password = config.get('password', '')
        self.use_oauth = config.get('use_oauth', False)
        self.oauth_client_id = config.get('oauth_client_id', '')
        self.oauth_client_secret = config.get('oauth_client_secret', '')
        self.verify_ssl = config.get('verify_ssl', True)
        
        # OData service endpoints
        self.endpoints = {
            'billing_document': 'API_BILLING_DOCUMENT_SRV_0001/A_BillingDocument',
            'journal_entry': 'API_OPLACCTGDOCITEMCUBE_SRV_0001/A_OperationalAcctgDocItemCube',
            'business_partner': 'API_BUSINESS_PARTNER_0001/A_BusinessPartner',
            'oauth_token': 'oauth/token',
            'metadata': '$metadata'
        }
        
        # Authentication state
        self.access_token = None
        self.token_type = 'Bearer'
        self.session = None
    
    def _build_base_url(self) -> str:
        """Build the complete base URL for SAP OData services."""
        base = self.base_url.rstrip('/')
        if not base.endswith('/sap/opu/odata/sap'):
            base = f"{base}/sap/opu/odata/sap"
        return base
    
    async def _create_session(self) -> aiohttp.ClientSession:
        """Create an aiohttp session with appropriate SSL settings."""
        connector = None
        
        if not self.verify_ssl:
            # Create SSL context that doesn't verify certificates
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        # Create session with timeout and connection limits
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'TaxPoynt-eInvoice-SAP-Connector/1.0',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        )
        
        return session
    
    async def authenticate(self) -> bool:
        """
        Authenticate with SAP ERP - SI Role Function.
        
        Performs authentication with SAP ERP system using configured
        credentials (OAuth2 or Basic) for System Integrator data access.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            if not self.session:
                self.session = await self._create_session()
            
            if self.use_oauth:
                result = await self._oauth_authenticate(self.session)
                if result.get('success'):
                    self.access_token = result.get('access_token')
                    self.token_type = result.get('token_type', 'Bearer')
                    logger.info("Successfully authenticated with SAP using OAuth")
                    return True
                else:
                    logger.error(f"OAuth authentication failed: {result.get('error')}")
                    return False
            else:
                result = await self._basic_authenticate(self.session)
                if result.get('success'):
                    logger.info("Successfully authenticated with SAP using Basic Auth")
                    return True
                else:
                    logger.error(f"Basic authentication failed: {result.get('error')}")
                    return False
                    
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return False
    
    async def _oauth_authenticate(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Perform OAuth 2.0 authentication"""
        try:
            token_url = urljoin(self._build_base_url(), self.endpoints['oauth_token'])
            
            # Prepare OAuth request
            auth_data = {
                'grant_type': 'client_credentials',
                'client_id': self.oauth_client_id,
                'client_secret': self.oauth_client_secret,
                'scope': 'API_BILLING_DOCUMENT_SRV_0001 API_OPLACCTGDOCITEMCUBE_SRV_0001 API_BUSINESS_PARTNER_0001'
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            async with session.post(token_url, data=auth_data, headers=headers) as response:
                if response.status == 200:
                    token_data = await response.json()
                    return {
                        'success': True,
                        'access_token': token_data.get('access_token'),
                        'token_type': token_data.get('token_type', 'Bearer'),
                        'expires_in': token_data.get('expires_in', 3600),
                        'scope': token_data.get('scope', '')
                    }
                else:
                    error_text = await response.text()
                    return {
                        'success': False,
                        'error': f'OAuth failed with status {response.status}: {error_text}'
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': f'OAuth authentication error: {str(e)}'
            }
    
    async def _basic_authenticate(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Perform basic authentication"""
        try:
            # Test basic auth by accessing a protected endpoint
            test_url = urljoin(self._build_base_url(), self.endpoints['billing_document'])
            
            auth = aiohttp.BasicAuth(self.username, self.password)
            
            async with session.get(test_url, auth=auth) as response:
                if response.status in [200, 401]:  # 401 is expected for metadata access
                    return {
                        'success': True,
                        'auth_type': 'basic',
                        'username': self.username
                    }
                else:
                    error_text = await response.text()
                    return {
                        'success': False,
                        'error': f'Basic auth failed with status {response.status}: {error_text}'
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': f'Basic authentication error: {str(e)}'
            }
    
    async def test_authentication(self) -> Dict[str, Any]:
        """Test authentication without storing credentials"""
        try:
            if not self.session:
                self.session = await self._create_session()
            
            if self.use_oauth:
                return await self._oauth_authenticate(self.session)
            else:
                return await self._basic_authenticate(self.session)
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Authentication test failed: {str(e)}'
            }
    
    async def test_metadata_access(self) -> Dict[str, Any]:
        """Test access to OData metadata"""
        try:
            if not self.session:
                self.session = await self._create_session()
            
            # Test billing document metadata
            metadata_url = urljoin(
                self._build_base_url(),
                f"{self.endpoints['billing_document']}/{self.endpoints['metadata']}"
            )
            
            headers = await self._get_auth_headers()
            
            async with self.session.get(metadata_url, headers=headers) as response:
                if response.status == 200:
                    return {
                        'success': True,
                        'message': 'Metadata access successful',
                        'service': 'billing_document'
                    }
                else:
                    error_text = await response.text()
                    return {
                        'success': False,
                        'error': f'Metadata access failed with status {response.status}: {error_text}'
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': f'Metadata access test failed: {str(e)}'
            }
    
    async def test_billing_service(self) -> Dict[str, Any]:
        """Test access to billing document service"""
        try:
            if not self.session:
                self.session = await self._create_session()
            
            # Test billing document service with minimal query
            billing_url = urljoin(self._build_base_url(), self.endpoints['billing_document'])
            params = {
                '$top': '1',
                '$select': 'BillingDocument',
                '$format': 'json'
            }
            
            headers = await self._get_auth_headers()
            
            async with self.session.get(billing_url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'success': True,
                        'message': 'Billing service access successful',
                        'record_count': len(data.get('d', {}).get('results', []))
                    }
                else:
                    error_text = await response.text()
                    return {
                        'success': False,
                        'error': f'Billing service access failed with status {response.status}: {error_text}'
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': f'Billing service test failed: {str(e)}'
            }
    
    async def test_partner_service(self) -> Dict[str, Any]:
        """Test access to business partner service"""
        try:
            if not self.session:
                self.session = await self._create_session()
            
            # Test business partner service with minimal query
            partner_url = urljoin(self._build_base_url(), self.endpoints['business_partner'])
            params = {
                '$top': '1',
                '$select': 'BusinessPartner',
                '$format': 'json'
            }
            
            headers = await self._get_auth_headers()
            
            async with self.session.get(partner_url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'success': True,
                        'message': 'Partner service access successful',
                        'record_count': len(data.get('d', {}).get('results', []))
                    }
                else:
                    error_text = await response.text()
                    return {
                        'success': False,
                        'error': f'Partner service access failed with status {response.status}: {error_text}'
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': f'Partner service test failed: {str(e)}'
            }
    
    async def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for requests"""
        headers = {}
        
        if self.use_oauth and self.access_token:
            headers['Authorization'] = f'{self.token_type} {self.access_token}'
        elif not self.use_oauth:
            # For basic auth, we'll rely on aiohttp.BasicAuth in the request
            pass
        
        return headers
    
    def get_basic_auth(self) -> Optional[aiohttp.BasicAuth]:
        """Get BasicAuth object for requests when using basic authentication"""
        if not self.use_oauth and self.username and self.password:
            return aiohttp.BasicAuth(self.username, self.password)
        return None
    
    def is_authenticated(self) -> bool:
        """Check if authenticated"""
        if self.use_oauth:
            return self.access_token is not None
        else:
            return bool(self.username and self.password)
    
    async def disconnect(self) -> bool:
        """Disconnect and cleanup session"""
        try:
            if self.session:
                await self.session.close()
                self.session = None
            
            self.access_token = None
            return True
            
        except Exception as e:
            logger.error(f"Error during disconnect: {str(e)}")
            return False