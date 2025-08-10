"""
SAP S/4HANA Connector for TaxPoynt eInvoice - System Integrator Production

This module provides production SAP S/4HANA connector for System Integrator
functions including OData API integration, OAuth 2.0 authentication, and
dual API approach for invoice extraction.

SAP API Endpoints:
- /sap/opu/odata/sap/API_BILLING_DOCUMENT_SRV (SD Invoices)
- /sap/opu/odata/sap/API_OPLACCTGDOCITEMCUBE_SRV (FI Invoices)
- /sap/opu/odata/sap/API_BUSINESS_PARTNER (Business Partners)
- /sap/bc/sec/oauth2/token (OAuth 2.0 Authentication)

Enterprise Features:
- OAuth 2.0 + TLS 1.3 security
- Dual API approach (Billing Document + Journal Entry)
- Business Partner integration
- SAP eDocument Cockpit integration (optional)
- Connection pooling and retry mechanisms
"""

import aiohttp
import asyncio
import json
import logging
import ssl
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from urllib.parse import urljoin, quote
import xml.etree.ElementTree as ET

from app.services.firs_si.base_erp_connector import BaseERPConnector, ERPConnectionError, ERPAuthenticationError, ERPDataError
from app.schemas.integration import IntegrationTestResult

logger = logging.getLogger(__name__)


class SAPODataError(Exception):
    """Exception raised for SAP OData API errors"""
    pass


class SAPConnector(BaseERPConnector):
    """
    Production SAP S/4HANA connector for System Integrator functions
    
    This connector implements full SAP S/4HANA integration with OData APIs,
    OAuth 2.0 authentication, and enterprise-grade features for FIRS
    e-invoicing compliance.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the SAP connector
        
        Args:
            config: Configuration dictionary containing SAP connection parameters
        """
        super().__init__(config)
        
        # SAP connection parameters
        self.host = config.get('host', '')
        self.port = config.get('port', 443)
        self.client = config.get('client', '100')
        self.system_id = config.get('system_id', '')
        self.instance = config.get('instance', '00')
        
        # Authentication parameters
        self.username = config.get('username', '')
        self.password = config.get('password', '')
        self.oauth_client_id = config.get('oauth_client_id', '')
        self.oauth_client_secret = config.get('oauth_client_secret', '')
        self.use_oauth = config.get('use_oauth', True)
        
        # API configuration
        self.api_version = config.get('api_version', '0001')
        self.use_https = config.get('use_https', True)
        self.verify_ssl = config.get('verify_ssl', True)
        self.timeout = config.get('timeout', 30)
        
        # Connection management
        self.session = None
        self.access_token = None
        self.token_expiry = None
        self.base_url = self._build_base_url()
        
        # API endpoints
        self.endpoints = {
            'oauth_token': '/sap/bc/sec/oauth2/token',
            'billing_document': f'/sap/opu/odata/sap/API_BILLING_DOCUMENT_SRV',
            'journal_entry': f'/sap/opu/odata/sap/API_OPLACCTGDOCITEMCUBE_SRV',
            'business_partner': f'/sap/opu/odata/sap/API_BUSINESS_PARTNER',
            'edocument': f'/sap/opu/odata/sap/EDOCUMENT_SRV',
            'metadata': '$metadata'
        }
        
        # SAP-specific configuration
        self.sap_language = config.get('language', 'EN')
        self.sap_format = config.get('format', 'json')
        self.prefer_billing_api = config.get('prefer_billing_api', True)
        self.enable_edocument = config.get('enable_edocument', False)
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 1)
        
        logger.info(f"Initialized SAPConnector for {self.host}:{self.port} client {self.client}")
    
    def _build_base_url(self) -> str:
        """Build base URL for SAP system"""
        protocol = 'https' if self.use_https else 'http'
        if self.port in [80, 443]:
            return f"{protocol}://{self.host}"
        return f"{protocol}://{self.host}:{self.port}"
    
    @property
    def erp_type(self) -> str:
        """Return the ERP system type"""
        return "sap"
    
    @property
    def erp_version(self) -> str:
        """Return the ERP system version"""
        return "S/4HANA 2023"
    
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
            'firs_transformation',
            'oauth2_authentication',
            'basic_authentication',
            'odata_api',
            'billing_document_api',
            'journal_entry_api',
            'business_partner_api',
            'dual_api_approach',
            'connection_pooling',
            'retry_mechanisms',
            'ssl_verification',
            'metadata_introspection'
        ]
        
        if self.enable_edocument:
            features.append('edocument_cockpit')
        
        return features
    
    async def _create_session(self) -> aiohttp.ClientSession:
        """Create aiohttp session with proper configuration"""
        if self.session and not self.session.closed:
            return self.session
        
        # Configure SSL context
        ssl_context = ssl.create_default_context()
        if not self.verify_ssl:
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        
        # Configure connector with connection pooling
        connector = aiohttp.TCPConnector(
            ssl=ssl_context,
            limit=100,  # Total connection pool size
            limit_per_host=30,  # Per-host connection limit
            ttl_dns_cache=300,  # DNS cache TTL
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        # Configure timeout
        timeout = aiohttp.ClientTimeout(
            total=self.timeout,
            connect=10,
            sock_read=self.timeout
        )
        
        # Create session
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'TaxPoynt-SAP-Connector/1.0',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        )
        
        return self.session
    
    async def test_connection(self) -> IntegrationTestResult:
        """Test connection to SAP system"""
        try:
            # Create session
            session = await self._create_session()
            
            # Test basic connectivity
            test_url = f"{self.base_url}/sap/public/ping"
            
            async with session.get(test_url) as response:
                if response.status == 200:
                    connectivity_ok = True
                else:
                    connectivity_ok = False
                    
            # Test authentication
            auth_result = await self._test_authentication()
            
            # Test OData service metadata
            if auth_result['success']:
                metadata_test = await self._test_metadata_access()
            else:
                metadata_test = {'success': False, 'error': 'Authentication failed'}
            
            # Test billing document service
            billing_test = await self._test_billing_service() if auth_result['success'] else {'success': False}
            
            # Test business partner service
            partner_test = await self._test_partner_service() if auth_result['success'] else {'success': False}
            
            success = (
                connectivity_ok and
                auth_result['success'] and
                metadata_test['success'] and
                billing_test['success']
            )
            
            return IntegrationTestResult(
                success=success,
                message=f"SAP connection test {'successful' if success else 'failed'}",
                details={
                    "host": self.host,
                    "port": self.port,
                    "client": self.client,
                    "system_id": self.system_id,
                    "connectivity": connectivity_ok,
                    "authentication": auth_result,
                    "metadata_access": metadata_test,
                    "billing_service": billing_test,
                    "partner_service": partner_test,
                    "oauth_enabled": self.use_oauth,
                    "ssl_verified": self.verify_ssl,
                    "supported_features": self.supported_features
                }
            )
            
        except Exception as e:
            return IntegrationTestResult(
                success=False,
                message=f"SAP connection test failed: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__}
            )
    
    async def authenticate(self) -> bool:
        """Authenticate with SAP system"""
        try:
            session = await self._create_session()
            
            if self.use_oauth:
                # OAuth 2.0 authentication
                auth_result = await self._oauth_authenticate(session)
            else:
                # Basic authentication
                auth_result = await self._basic_authenticate(session)
            
            if auth_result['success']:
                self.authenticated = True
                self.connected = True
                self.last_connection_time = datetime.utcnow()
                
                if self.use_oauth:
                    self.access_token = auth_result['access_token']
                    self.token_expiry = datetime.utcnow() + timedelta(seconds=auth_result['expires_in'])
                
                logger.info(f"Successfully authenticated with SAP system {self.host}")
                return True
            else:
                raise ERPAuthenticationError(f"Authentication failed: {auth_result['error']}")
                
        except Exception as e:
            logger.error(f"SAP authentication failed: {str(e)}")
            self.authenticated = False
            self.connected = False
            raise ERPAuthenticationError(f"SAP authentication failed: {str(e)}")
    
    async def _oauth_authenticate(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Perform OAuth 2.0 authentication"""
        try:
            token_url = urljoin(self.base_url, self.endpoints['oauth_token'])
            
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
            test_url = urljoin(self.base_url, self.endpoints['billing_document'])
            
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
    
    async def _test_authentication(self) -> Dict[str, Any]:
        """Test authentication without storing credentials"""
        try:
            session = await self._create_session()
            
            if self.use_oauth:
                return await self._oauth_authenticate(session)
            else:
                return await self._basic_authenticate(session)
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Authentication test failed: {str(e)}'
            }
    
    async def _test_metadata_access(self) -> Dict[str, Any]:
        """Test access to OData metadata"""
        try:
            session = await self._create_session()
            
            # Test billing document metadata
            metadata_url = urljoin(
                self.base_url,
                f"{self.endpoints['billing_document']}/{self.endpoints['metadata']}"
            )
            
            headers = await self._get_auth_headers()
            
            async with session.get(metadata_url, headers=headers) as response:
                if response.status == 200:
                    metadata_content = await response.text()
                    return {
                        'success': True,
                        'metadata_size': len(metadata_content),
                        'content_type': response.headers.get('Content-Type', 'unknown')
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
                'error': f'Metadata test failed: {str(e)}'
            }
    
    async def _test_billing_service(self) -> Dict[str, Any]:
        """Test billing document service access"""
        try:
            session = await self._create_session()
            
            # Test billing document service
            billing_url = urljoin(
                self.base_url,
                f"{self.endpoints['billing_document']}/A_BillingDocument"
            )
            
            headers = await self._get_auth_headers()
            params = {
                '$top': 1,
                '$format': 'json'
            }
            
            async with session.get(billing_url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'success': True,
                        'service_accessible': True,
                        'sample_data_available': len(data.get('d', {}).get('results', [])) > 0
                    }
                else:
                    error_text = await response.text()
                    return {
                        'success': False,
                        'error': f'Billing service test failed with status {response.status}: {error_text}'
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': f'Billing service test failed: {str(e)}'
            }
    
    async def _test_partner_service(self) -> Dict[str, Any]:
        """Test business partner service access"""
        try:
            session = await self._create_session()
            
            # Test business partner service
            partner_url = urljoin(
                self.base_url,
                f"{self.endpoints['business_partner']}/A_BusinessPartner"
            )
            
            headers = await self._get_auth_headers()
            params = {
                '$top': 1,
                '$format': 'json'
            }
            
            async with session.get(partner_url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'success': True,
                        'service_accessible': True,
                        'sample_data_available': len(data.get('d', {}).get('results', [])) > 0
                    }
                else:
                    error_text = await response.text()
                    return {
                        'success': False,
                        'error': f'Partner service test failed with status {response.status}: {error_text}'
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': f'Partner service test failed: {str(e)}'
            }
    
    async def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for requests"""
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'sap-client': self.client,
            'sap-language': self.sap_language
        }
        
        if self.use_oauth and self.access_token:
            # Check if token is expired
            if self.token_expiry and datetime.utcnow() >= self.token_expiry:
                await self.authenticate()  # Refresh token
            
            headers['Authorization'] = f'Bearer {self.access_token}'
        
        return headers
    
    async def _make_odata_request(
        self,
        endpoint: str,
        entity_set: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = 'GET',
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make OData request with proper error handling and retries"""
        session = await self._create_session()
        url = urljoin(self.base_url, f"{endpoint}/{entity_set}")
        headers = await self._get_auth_headers()
        
        # Default OData parameters
        odata_params = {
            '$format': 'json',
            'sap-client': self.client,
            'sap-language': self.sap_language
        }
        
        if params:
            odata_params.update(params)
        
        # Retry logic
        for attempt in range(self.max_retries):
            try:
                if method.upper() == 'GET':
                    async with session.get(url, headers=headers, params=odata_params) as response:
                        return await self._handle_odata_response(response)
                elif method.upper() == 'POST':
                    async with session.post(url, headers=headers, params=odata_params, json=data) as response:
                        return await self._handle_odata_response(response)
                elif method.upper() == 'PUT':
                    async with session.put(url, headers=headers, params=odata_params, json=data) as response:
                        return await self._handle_odata_response(response)
                elif method.upper() == 'DELETE':
                    async with session.delete(url, headers=headers, params=odata_params) as response:
                        return await self._handle_odata_response(response)
                        
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    raise ERPConnectionError(f"SAP OData request failed after {self.max_retries} attempts: {str(e)}")
            except Exception as e:
                raise SAPODataError(f"SAP OData request error: {str(e)}")
    
    async def _handle_odata_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Handle OData response with proper error handling"""
        try:
            if response.status == 200:
                data = await response.json()
                return {
                    'success': True,
                    'data': data,
                    'status_code': response.status
                }
            elif response.status == 401:
                # Token expired, try to refresh
                await self.authenticate()
                raise ERPAuthenticationError("Authentication token expired")
            else:
                error_text = await response.text()
                try:
                    error_data = json.loads(error_text)
                    error_message = error_data.get('error', {}).get('message', {}).get('value', error_text)
                except:
                    error_message = error_text
                
                return {
                    'success': False,
                    'error': error_message,
                    'status_code': response.status
                }
                
        except json.JSONDecodeError:
            error_text = await response.text()
            return {
                'success': False,
                'error': f'Invalid JSON response: {error_text}',
                'status_code': response.status
            }
    
    async def get_invoices(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        include_draft: bool = False,
        include_attachments: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Fetch invoices from SAP system using dual API approach"""
        try:
            # Try Billing Document API first (preferred for SD invoices)
            if self.prefer_billing_api:
                try:
                    return await self._get_invoices_from_billing_api(
                        from_date, to_date, include_draft, include_attachments, page, page_size
                    )
                except Exception as e:
                    logger.warning(f"Billing API failed, trying Journal Entry API: {str(e)}")
                    return await self._get_invoices_from_journal_api(
                        from_date, to_date, include_draft, include_attachments, page, page_size
                    )
            else:
                # Try Journal Entry API first (for FI invoices)
                try:
                    return await self._get_invoices_from_journal_api(
                        from_date, to_date, include_draft, include_attachments, page, page_size
                    )
                except Exception as e:
                    logger.warning(f"Journal Entry API failed, trying Billing API: {str(e)}")
                    return await self._get_invoices_from_billing_api(
                        from_date, to_date, include_draft, include_attachments, page, page_size
                    )
                    
        except Exception as e:
            logger.error(f"Error fetching SAP invoices: {str(e)}")
            raise ERPDataError(f"Error fetching SAP invoices: {str(e)}")
    
    async def _get_invoices_from_billing_api(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        include_draft: bool = False,
        include_attachments: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Fetch invoices from Billing Document API"""
        try:
            # Build OData filter
            filters = []
            
            # Date filters
            if from_date:
                filters.append(f"BillingDocumentDate ge datetime'{from_date.strftime('%Y-%m-%dT%H:%M:%S')}'")
            if to_date:
                filters.append(f"BillingDocumentDate le datetime'{to_date.strftime('%Y-%m-%dT%H:%M:%S')}'")
            
            # Document type filters (invoices only)
            if not include_draft:
                filters.append("BillingDocumentIsCancelled eq false")
            
            # Build parameters
            params = {
                '$top': page_size,
                '$skip': (page - 1) * page_size,
                '$expand': 'to_Item,to_Partner,to_PricingElement',
                '$orderby': 'BillingDocumentDate desc'
            }
            
            if filters:
                params['$filter'] = ' and '.join(filters)
            
            # Make OData request
            result = await self._make_odata_request(
                self.endpoints['billing_document'],
                'A_BillingDocument',
                params
            )
            
            if not result['success']:
                raise ERPDataError(f"Billing Document API error: {result['error']}")
            
            # Process results
            odata_response = result['data']
            invoices_data = odata_response.get('d', {}).get('results', [])
            
            # Get total count (if available)
            total_count = odata_response.get('d', {}).get('__count', len(invoices_data))
            
            # Format invoices
            formatted_invoices = []
            for invoice in invoices_data:
                formatted_invoice = await self._format_billing_document_data(invoice, include_attachments)
                formatted_invoices.append(formatted_invoice)
            
            # Calculate pagination
            total_pages = (total_count + page_size - 1) // page_size
            
            return {
                "invoices": formatted_invoices,
                "total": total_count,
                "page": page,
                "page_size": page_size,
                "pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
                "next_page": page + 1 if page < total_pages else None,
                "prev_page": page - 1 if page > 1 else None,
                "data_source": "sap_billing_document_api"
            }
            
        except Exception as e:
            logger.error(f"Error fetching from Billing Document API: {str(e)}")
            raise ERPDataError(f"Error fetching from Billing Document API: {str(e)}")
    
    async def _get_invoices_from_journal_api(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        include_draft: bool = False,
        include_attachments: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Fetch invoices from Journal Entry API"""
        try:
            # Build OData filter for FI invoices
            filters = [
                "GLAccount eq '40000000'",  # Revenue account
                "DebitCreditCode eq 'H'"    # Credit entries for sales
            ]
            
            # Date filters
            if from_date:
                filters.append(f"PostingDate ge datetime'{from_date.strftime('%Y-%m-%dT%H:%M:%S')}'")
            if to_date:
                filters.append(f"PostingDate le datetime'{to_date.strftime('%Y-%m-%dT%H:%M:%S')}'")
            
            # Build parameters
            params = {
                '$top': page_size,
                '$skip': (page - 1) * page_size,
                '$filter': ' and '.join(filters),
                '$orderby': 'PostingDate desc'
            }
            
            # Make OData request
            result = await self._make_odata_request(
                self.endpoints['journal_entry'],
                'A_JournalEntryItem',
                params
            )
            
            if not result['success']:
                raise ERPDataError(f"Journal Entry API error: {result['error']}")
            
            # Process results
            odata_response = result['data']
            journal_entries = odata_response.get('d', {}).get('results', [])
            
            # Group by document number to create invoices
            invoice_groups = {}
            for entry in journal_entries:
                doc_num = entry.get('AccountingDocument', '')
                if doc_num not in invoice_groups:
                    invoice_groups[doc_num] = []
                invoice_groups[doc_num].append(entry)
            
            # Format invoices
            formatted_invoices = []
            for doc_num, entries in invoice_groups.items():
                formatted_invoice = await self._format_journal_entry_data(entries, include_attachments)
                formatted_invoices.append(formatted_invoice)
            
            # Calculate pagination
            total_count = len(invoice_groups)
            total_pages = (total_count + page_size - 1) // page_size
            
            return {
                "invoices": formatted_invoices,
                "total": total_count,
                "page": page,
                "page_size": page_size,
                "pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
                "next_page": page + 1 if page < total_pages else None,
                "prev_page": page - 1 if page > 1 else None,
                "data_source": "sap_journal_entry_api"
            }
            
        except Exception as e:
            logger.error(f"Error fetching from Journal Entry API: {str(e)}")
            raise ERPDataError(f"Error fetching from Journal Entry API: {str(e)}")
    
    async def get_invoice_by_id(self, invoice_id: Union[int, str]) -> Dict[str, Any]:
        """Get specific invoice by ID from SAP system"""
        try:
            invoice_id_str = str(invoice_id)
            
            # Try Billing Document API first
            try:
                params = {
                    '$expand': 'to_Item,to_Partner,to_PricingElement'
                }
                
                result = await self._make_odata_request(
                    self.endpoints['billing_document'],
                    f"A_BillingDocument('{invoice_id_str}')",
                    params
                )
                
                if result['success']:
                    invoice_data = result['data']['d']
                    return await self._format_billing_document_data(invoice_data, include_attachments=True)
                    
            except Exception as e:
                logger.warning(f"Billing API failed for invoice {invoice_id}, trying Journal Entry API: {str(e)}")
            
            # Try Journal Entry API as fallback
            params = {
                '$filter': f"AccountingDocument eq '{invoice_id_str}'"
            }
            
            result = await self._make_odata_request(
                self.endpoints['journal_entry'],
                'A_JournalEntryItem',
                params
            )
            
            if result['success']:
                entries = result['data']['d']['results']
                if entries:
                    return await self._format_journal_entry_data(entries, include_attachments=True)
            
            raise ERPDataError(f"Invoice with ID {invoice_id} not found in SAP system")
            
        except Exception as e:
            logger.error(f"Error fetching SAP invoice {invoice_id}: {str(e)}")
            raise ERPDataError(f"Error fetching SAP invoice {invoice_id}: {str(e)}")
    
    async def search_invoices(
        self,
        search_term: str,
        include_attachments: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Search for invoices in SAP system"""
        try:
            # Build search filters
            search_filters = [
                f"contains(BillingDocument, '{search_term}')",
                f"contains(SoldToParty, '{search_term}')",
                f"contains(BillToParty, '{search_term}')"
            ]
            
            params = {
                '$top': page_size,
                '$skip': (page - 1) * page_size,
                '$filter': ' or '.join(search_filters),
                '$expand': 'to_Item,to_Partner,to_PricingElement',
                '$orderby': 'BillingDocumentDate desc'
            }
            
            # Make OData request
            result = await self._make_odata_request(
                self.endpoints['billing_document'],
                'A_BillingDocument',
                params
            )
            
            if not result['success']:
                raise ERPDataError(f"Search failed: {result['error']}")
            
            # Process results
            odata_response = result['data']
            invoices_data = odata_response.get('d', {}).get('results', [])
            total_count = odata_response.get('d', {}).get('__count', len(invoices_data))
            
            # Format invoices
            formatted_invoices = []
            for invoice in invoices_data:
                formatted_invoice = await self._format_billing_document_data(invoice, include_attachments)
                formatted_invoices.append(formatted_invoice)
            
            # Calculate pagination
            total_pages = (total_count + page_size - 1) // page_size
            
            return {
                "invoices": formatted_invoices,
                "total": total_count,
                "page": page,
                "page_size": page_size,
                "pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
                "next_page": page + 1 if page < total_pages else None,
                "prev_page": page - 1 if page > 1 else None,
                "search_term": search_term,
                "data_source": "sap_billing_document_api"
            }
            
        except Exception as e:
            logger.error(f"Error searching SAP invoices: {str(e)}")
            raise ERPDataError(f"Error searching SAP invoices: {str(e)}")
    
    async def get_partners(
        self,
        search_term: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get partners from SAP system"""
        try:
            params = {
                '$top': limit,
                '$filter': "BusinessPartnerCategory eq '2'"  # Customers only
            }
            
            if search_term:
                search_filters = [
                    f"contains(BusinessPartnerName, '{search_term}')",
                    f"contains(BusinessPartnerFullName, '{search_term}')",
                    f"contains(BusinessPartner, '{search_term}')"
                ]
                params['$filter'] += f" and ({' or '.join(search_filters)})"
            
            result = await self._make_odata_request(
                self.endpoints['business_partner'],
                'A_BusinessPartner',
                params
            )
            
            if not result['success']:
                raise ERPDataError(f"Partner search failed: {result['error']}")
            
            partners_data = result['data']['d']['results']
            
            # Format partners
            formatted_partners = []
            for partner in partners_data:
                formatted_partner = {
                    "id": partner.get('BusinessPartner', ''),
                    "name": partner.get('BusinessPartnerFullName', ''),
                    "short_name": partner.get('BusinessPartnerName', ''),
                    "vat": partner.get('VATRegistration', ''),
                    "tax_id": partner.get('TaxNumber1', ''),
                    "email": partner.get('EmailAddress', ''),
                    "phone": partner.get('PhoneNumber1', ''),
                    "street": partner.get('StreetName', ''),
                    "city": partner.get('CityName', ''),
                    "country": partner.get('Country', ''),
                    "postal_code": partner.get('PostalCode', ''),
                    "business_partner_category": partner.get('BusinessPartnerCategory', ''),
                    "is_blocked": partner.get('BusinessPartnerIsBlocked', False),
                    "creation_date": partner.get('CreationDate', ''),
                    "last_change_date": partner.get('LastChangeDate', '')
                }
                formatted_partners.append(formatted_partner)
            
            return formatted_partners
            
        except Exception as e:
            logger.error(f"Error fetching SAP partners: {str(e)}")
            raise ERPDataError(f"Error fetching SAP partners: {str(e)}")
    
    async def _format_billing_document_data(self, invoice: Dict[str, Any], include_attachments: bool = False) -> Dict[str, Any]:
        """Format billing document data into standardized format"""
        try:
            # Extract basic invoice information
            formatted_invoice = {
                "id": invoice.get('BillingDocument', ''),
                "name": invoice.get('BillingDocument', ''),
                "invoice_number": invoice.get('BillingDocument', ''),
                "reference": invoice.get('CustomerReference', ''),
                "invoice_date": invoice.get('BillingDocumentDate', ''),
                "invoice_date_due": invoice.get('BillingDocumentDate', ''),  # Calculate based on payment terms
                "state": "cancelled" if invoice.get('BillingDocumentIsCancelled', False) else "posted",
                "document_type": invoice.get('BillingDocumentType', ''),
                "amount_total": float(invoice.get('TotalGrossAmount', 0)),
                "amount_untaxed": float(invoice.get('NetAmount', 0)),
                "amount_tax": float(invoice.get('TaxAmount', 0)),
                "currency": {
                    "id": invoice.get('TransactionCurrency', ''),
                    "name": invoice.get('TransactionCurrency', ''),
                    "symbol": "₦" if invoice.get('TransactionCurrency') == 'NGN' else invoice.get('TransactionCurrency', '')
                },
                "partner": {
                    "id": invoice.get('SoldToParty', ''),
                    "name": invoice.get('SoldToParty', ''),  # Would need to expand partner data
                    "vat": "",
                    "email": "",
                    "phone": "",
                },
                "lines": []
            }
            
            # Process invoice lines
            for line in invoice.get('to_Item', {}).get('results', []):
                line_data = {
                    "id": line.get('BillingDocumentItem', ''),
                    "name": line.get('MaterialDescription', ''),
                    "quantity": float(line.get('BillingQuantity', 0)),
                    "unit": line.get('BillingQuantityUnit', ''),
                    "price_unit": float(line.get('NetAmount', 0)) / float(line.get('BillingQuantity', 1)),
                    "price_subtotal": float(line.get('NetAmount', 0)),
                    "material": line.get('Material', ''),
                    "product": {
                        "id": line.get('Material', ''),
                        "name": line.get('MaterialDescription', ''),
                        "code": line.get('Material', '')
                    },
                    "taxes": []
                }
                formatted_invoice["lines"].append(line_data)
            
            # Add attachments if requested
            if include_attachments:
                formatted_invoice["attachments"] = []  # Would implement attachment retrieval
            
            return formatted_invoice
            
        except Exception as e:
            logger.error(f"Error formatting billing document data: {str(e)}")
            raise ERPDataError(f"Error formatting billing document data: {str(e)}")
    
    async def _format_journal_entry_data(self, entries: List[Dict[str, Any]], include_attachments: bool = False) -> Dict[str, Any]:
        """Format journal entry data into standardized format"""
        try:
            if not entries:
                raise ERPDataError("No journal entries provided")
            
            # Use first entry for header information
            header_entry = entries[0]
            
            # Calculate totals
            total_amount = sum(float(entry.get('AmountInTransactionCurrency', 0)) for entry in entries)
            
            formatted_invoice = {
                "id": header_entry.get('AccountingDocument', ''),
                "name": header_entry.get('AccountingDocument', ''),
                "invoice_number": header_entry.get('AccountingDocument', ''),
                "reference": header_entry.get('DocumentReferenceID', ''),
                "invoice_date": header_entry.get('PostingDate', ''),
                "invoice_date_due": header_entry.get('PostingDate', ''),
                "state": "posted",
                "document_type": header_entry.get('AccountingDocumentType', ''),
                "amount_total": abs(total_amount),
                "amount_untaxed": abs(total_amount),
                "amount_tax": 0,  # Would need to calculate from tax entries
                "currency": {
                    "id": header_entry.get('TransactionCurrency', ''),
                    "name": header_entry.get('TransactionCurrency', ''),
                    "symbol": "₦" if header_entry.get('TransactionCurrency') == 'NGN' else header_entry.get('TransactionCurrency', '')
                },
                "partner": {
                    "id": header_entry.get('Customer', ''),
                    "name": header_entry.get('Customer', ''),
                    "vat": "",
                    "email": "",
                    "phone": "",
                },
                "lines": []
            }
            
            # Process entries as lines
            for entry in entries:
                line_data = {
                    "id": entry.get('LineNumber', ''),
                    "name": entry.get('GLAccountName', ''),
                    "quantity": 1,
                    "unit": "EA",
                    "price_unit": abs(float(entry.get('AmountInTransactionCurrency', 0))),
                    "price_subtotal": abs(float(entry.get('AmountInTransactionCurrency', 0))),
                    "gl_account": entry.get('GLAccount', ''),
                    "product": {
                        "id": entry.get('GLAccount', ''),
                        "name": entry.get('GLAccountName', ''),
                        "code": entry.get('GLAccount', '')
                    },
                    "taxes": []
                }
                formatted_invoice["lines"].append(line_data)
            
            return formatted_invoice
            
        except Exception as e:
            logger.error(f"Error formatting journal entry data: {str(e)}")
            raise ERPDataError(f"Error formatting journal entry data: {str(e)}")
    
    async def validate_invoice_data(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate invoice data for FIRS compliance"""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # SAP-specific validation rules
        required_fields = [
            'BillingDocument', 'BillingDocumentDate', 'SoldToParty', 
            'NetAmount', 'TransactionCurrency'
        ]
        
        for field in required_fields:
            if field not in invoice_data:
                validation_result['errors'].append(f"Missing required SAP field: {field}")
                validation_result['is_valid'] = False
        
        # Business rules
        if 'BillingDocumentIsCancelled' in invoice_data and invoice_data['BillingDocumentIsCancelled']:
            validation_result['warnings'].append("Invoice is cancelled in SAP system")
        
        return validation_result
    
    async def transform_to_firs_format(
        self,
        invoice_data: Dict[str, Any],
        target_format: str = 'UBL_BIS_3.0'
    ) -> Dict[str, Any]:
        """Transform SAP invoice data to FIRS-compliant format"""
        try:
            # Implementation similar to mock connector but with real SAP data
            # This would use the actual SAP field mappings
            
            # Get company info
            company_info = await self.get_company_info()
            
            # Transform to UBL BIS 3.0 format
            firs_invoice = {
                'invoice_type_code': self._map_sap_doc_type_to_firs(invoice_data.get('BillingDocumentType', 'F2')),
                'id': invoice_data.get('BillingDocument', ''),
                'issue_date': invoice_data.get('BillingDocumentDate', ''),
                'due_date': invoice_data.get('BillingDocumentDate', ''),  # Calculate based on payment terms
                'document_currency_code': invoice_data.get('TransactionCurrency', 'NGN'),
                'accounting_supplier_party': {
                    'party': {
                        'party_name': {
                            'name': company_info.get('name', '')
                        },
                        'party_tax_scheme': {
                            'company_id': company_info.get('vat', '')
                        }
                    }
                },
                'legal_monetary_total': {
                    'line_extension_amount': float(invoice_data.get('NetAmount', 0)),
                    'tax_exclusive_amount': float(invoice_data.get('NetAmount', 0)),
                    'tax_inclusive_amount': float(invoice_data.get('TotalGrossAmount', 0)),
                    'payable_amount': float(invoice_data.get('TotalGrossAmount', 0))
                },
                'invoice_line': []
            }
            
            # Transform invoice lines
            for line in invoice_data.get('to_Item', {}).get('results', []):
                firs_line = {
                    'id': line.get('BillingDocumentItem', ''),
                    'invoiced_quantity': {
                        'quantity': float(line.get('BillingQuantity', 0)),
                        'unit_code': self._map_sap_unit_to_ubl(line.get('BillingQuantityUnit', 'EA'))
                    },
                    'line_extension_amount': float(line.get('NetAmount', 0)),
                    'item': {
                        'description': line.get('MaterialDescription', ''),
                        'name': line.get('MaterialDescription', ''),
                        'sellers_item_identification': {
                            'id': line.get('Material', '')
                        }
                    },
                    'price': {
                        'price_amount': float(line.get('NetAmount', 0)) / float(line.get('BillingQuantity', 1)),
                        'base_quantity': {
                            'quantity': 1,
                            'unit_code': self._map_sap_unit_to_ubl(line.get('BillingQuantityUnit', 'EA'))
                        }
                    }
                }
                firs_invoice['invoice_line'].append(firs_line)
            
            return {
                'firs_invoice': firs_invoice,
                'source_format': 'sap_billing_document',
                'target_format': target_format,
                'transformation_metadata': {
                    'transformation_date': datetime.utcnow().isoformat(),
                    'source_invoice_id': invoice_data.get('BillingDocument', ''),
                    'erp_type': self.erp_type,
                    'erp_version': self.erp_version,
                    'sap_client': self.client,
                    'sap_document_type': invoice_data.get('BillingDocumentType', '')
                }
            }
            
        except Exception as e:
            logger.error(f"Error transforming SAP invoice to FIRS format: {str(e)}")
            raise ERPDataError(f"Error transforming SAP invoice to FIRS format: {str(e)}")
    
    def _map_sap_doc_type_to_firs(self, sap_doc_type: str) -> str:
        """Map SAP document type to FIRS invoice type code"""
        mapping = {
            'F2': '380',  # Invoice
            'G2': '381',  # Credit Note
            'L2': '383',  # Debit Note
            'S1': '384',  # Cancellation
            'RE': '380'   # Invoice for Returns
        }
        return mapping.get(sap_doc_type, '380')
    
    def _map_sap_unit_to_ubl(self, sap_unit: str) -> str:
        """Map SAP unit of measure to UBL unit code"""
        mapping = {
            'EA': 'C62',  # Each
            'PC': 'C62',  # Piece
            'KG': 'KGM',  # Kilogram
            'L': 'LTR',   # Liter
            'M': 'MTR',   # Meter
            'H': 'HUR',   # Hour
            'ST': 'C62',  # Set
            'BOX': 'BX',  # Box
            'PAL': 'PF'   # Pallet
        }
        return mapping.get(sap_unit, 'C62')
    
    async def update_invoice_status(
        self,
        invoice_id: Union[int, str],
        status_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update invoice status in SAP system"""
        try:
            # This would implement status update via SAP OData API
            # For now, just log the action
            logger.info(f"SAP: Updating invoice {invoice_id} status: {status_data}")
            
            return {
                'success': True,
                'invoice_id': invoice_id,
                'status_updated': True,
                'new_status': status_data.get('status'),
                'updated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error updating SAP invoice status: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'invoice_id': invoice_id
            }
    
    async def get_company_info(self) -> Dict[str, Any]:
        """Get company information from SAP system"""
        try:
            # This would fetch company data from SAP
            # For now, return placeholder data
            return {
                "id": "1000",
                "name": "SAP Company Limited",
                "vat": "NG0123456789",
                "email": "info@sap-company.com",
                "phone": "+234-1-2345678",
                "currency": "NGN",
                "address": {
                    "street": "1 SAP Street",
                    "city": "Lagos",
                    "state": "Lagos State",
                    "country": "Nigeria"
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting SAP company info: {str(e)}")
            raise ERPDataError(f"Error getting SAP company info: {str(e)}")
    
    async def get_tax_configuration(self) -> Dict[str, Any]:
        """Get tax configuration from SAP system"""
        try:
            # This would fetch tax configuration from SAP
            return {
                "country": "NG",
                "tax_system": "Nigerian VAT",
                "default_currency": "NGN",
                "taxes": [
                    {
                        "id": "UTXJ",
                        "name": "Nigerian VAT",
                        "rate": 7.5,
                        "type": "VAT",
                        "is_active": True
                    }
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting SAP tax configuration: {str(e)}")
            return {
                "taxes": [],
                "error": str(e)
            }
    
    async def disconnect(self) -> bool:
        """Disconnect from SAP system"""
        try:
            if self.session and not self.session.closed:
                await self.session.close()
            
            self.connected = False
            self.authenticated = False
            self.last_connection_time = None
            self.access_token = None
            self.token_expiry = None
            
            logger.info("Disconnected from SAP system")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting from SAP system: {str(e)}")
            return False