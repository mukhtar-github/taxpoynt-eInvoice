"""
OData Adapter - Protocol Adapter for OData Services
Specialized connector implementation for OData (Open Data Protocol) services.
Commonly used with SAP, Microsoft Dynamics, and other enterprise systems.
"""

import asyncio
import logging
import json
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin, urlencode, quote
import xml.etree.ElementTree as ET

from ..base_connector import (
    BaseConnector, ConnectorConfig, ConnectorRequest, ConnectorResponse,
    ConnectionStatus, DataFormat, AuthenticationType
)

logger = logging.getLogger(__name__)

class ODataConnector(BaseConnector):
    """OData service connector implementation"""
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.session: Optional[aiohttp.ClientSession] = None
        self.metadata: Optional[Dict[str, Any]] = None
        self.entity_sets: Dict[str, Dict[str, Any]] = {}
        self.odata_version = config.custom_settings.get('odata_version', 'v2')
        self.csrf_token: Optional[str] = None
    
    async def _initialize_session(self):
        """Initialize HTTP session for OData requests"""
        try:
            connector = aiohttp.TCPConnector(
                ssl=None if self.config.ssl_verify else False,
                limit=100,
                limit_per_host=10
            )
            
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            
            # Set default headers for OData
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            # Add OData version specific headers
            if self.odata_version == 'v4':
                headers['OData-Version'] = '4.0'
                headers['OData-MaxVersion'] = '4.0'
            else:
                headers['DataServiceVersion'] = '2.0'
                headers['MaxDataServiceVersion'] = '2.0'
            
            headers.update(self.config.headers)
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=headers
            )
            
            # Load metadata
            await self._load_metadata()
            
            # Get CSRF token if required (SAP systems)
            if self.config.custom_settings.get('csrf_protection', False):
                await self._get_csrf_token()
            
            logger.debug(f"OData session initialized for {self.config.connector_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize OData session: {e}")
            raise
    
    async def _load_metadata(self):
        """Load OData service metadata"""
        try:
            metadata_url = urljoin(self.config.base_url, self.config.endpoints.get('metadata', '/$metadata'))
            
            async with self.session.get(metadata_url) as response:
                if response.status == 200:
                    content_type = response.headers.get('Content-Type', '').lower()
                    
                    if 'xml' in content_type:
                        metadata_xml = await response.text()
                        self.metadata = await self._parse_metadata_xml(metadata_xml)
                    else:
                        self.metadata = await response.json()
                    
                    # Extract entity sets
                    await self._extract_entity_sets()
                    logger.info("OData metadata loaded successfully")
                else:
                    logger.warning(f"Failed to load OData metadata: HTTP {response.status}")
                    
        except Exception as e:
            logger.warning(f"Metadata loading failed: {e}")
    
    async def _parse_metadata_xml(self, xml_content: str) -> Dict[str, Any]:
        """Parse OData metadata XML"""
        try:
            root = ET.fromstring(xml_content)
            
            # Extract namespaces
            namespaces = {}
            for elem in root.iter():
                if elem.tag.startswith('{'):
                    namespace = elem.tag[1:elem.tag.index('}')]
                    if namespace not in namespaces.values():
                        prefix = f"ns{len(namespaces)}"
                        namespaces[prefix] = namespace
            
            # Parse schema information
            metadata = {
                'namespaces': namespaces,
                'entity_sets': [],
                'entity_types': [],
                'associations': []
            }
            
            # Find entity sets
            for container in root.findall('.//*[@Name]'):
                if 'EntityContainer' in container.tag:
                    for entity_set in container.findall('.//*[@Name]'):
                        if 'EntitySet' in entity_set.tag:
                            metadata['entity_sets'].append({
                                'name': entity_set.get('Name'),
                                'entity_type': entity_set.get('EntityType')
                            })
            
            return metadata
            
        except Exception as e:
            logger.error(f"Metadata XML parsing failed: {e}")
            return {'raw_xml': xml_content}
    
    async def _extract_entity_sets(self):
        """Extract entity sets from metadata"""
        try:
            if not self.metadata:
                return
            
            entity_sets = self.metadata.get('entity_sets', [])
            for entity_set in entity_sets:
                if isinstance(entity_set, dict) and 'name' in entity_set:
                    self.entity_sets[entity_set['name']] = entity_set
                    
        except Exception as e:
            logger.error(f"Entity set extraction failed: {e}")
    
    async def _get_csrf_token(self):
        """Get CSRF token for SAP systems"""
        try:
            # SAP systems require CSRF token for modify operations
            csrf_url = self.config.base_url
            headers = {'X-CSRF-Token': 'Fetch'}
            
            async with self.session.get(csrf_url, headers=headers) as response:
                csrf_token = response.headers.get('X-CSRF-Token')
                if csrf_token:
                    self.csrf_token = csrf_token
                    self.session.headers['X-CSRF-Token'] = csrf_token
                    logger.debug("CSRF token obtained")
                    
        except Exception as e:
            logger.warning(f"CSRF token retrieval failed: {e}")
    
    async def _authenticate(self) -> bool:
        """Authenticate with the OData service"""
        try:
            auth_type = self.config.authentication_type
            auth_config = self.config.authentication_config
            
            if auth_type == AuthenticationType.NONE:
                return True
            
            elif auth_type == AuthenticationType.BASIC_AUTH:
                username = auth_config.get('username')
                password = auth_config.get('password')
                
                if not username or not password:
                    logger.error("Username or password not provided for basic auth")
                    return False
                
                # Set basic auth
                auth = aiohttp.BasicAuth(username, password)
                self.session._default_auth = auth
                self.authentication_token = f"{username}:***"
                return True
            
            elif auth_type == AuthenticationType.OAUTH2:
                return await self._oauth2_authenticate()
            
            elif auth_type == AuthenticationType.CUSTOM_TOKEN:
                # SAP specific authentication
                token = auth_config.get('token')
                if token:
                    self.session.headers['Authorization'] = f"Bearer {token}"
                    self.authentication_token = token
                    return True
                else:
                    logger.error("Custom token not provided")
                    return False
            
            else:
                logger.error(f"Unsupported authentication type for OData: {auth_type}")
                return False
                
        except Exception as e:
            logger.error(f"OData authentication failed: {e}")
            return False
    
    async def _oauth2_authenticate(self) -> bool:
        """Perform OAuth 2.0 authentication"""
        try:
            auth_config = self.config.authentication_config
            
            token_url = auth_config.get('token_url')
            client_id = auth_config.get('client_id')
            client_secret = auth_config.get('client_secret')
            
            if not all([token_url, client_id, client_secret]):
                logger.error("OAuth 2.0 configuration incomplete")
                return False
            
            token_data = {
                'grant_type': 'client_credentials',
                'client_id': client_id,
                'client_secret': client_secret
            }
            
            async with self.session.post(token_url, data=token_data) as response:
                if response.status == 200:
                    token_response = await response.json()
                    access_token = token_response.get('access_token')
                    
                    if access_token:
                        self.session.headers['Authorization'] = f"Bearer {access_token}"
                        self.authentication_token = access_token
                        logger.info("OAuth 2.0 authentication successful")
                        return True
                
                logger.error("OAuth 2.0 authentication failed")
                return False
                
        except Exception as e:
            logger.error(f"OAuth 2.0 authentication error: {e}")
            return False
    
    async def _test_connection(self) -> bool:
        """Test the OData service connection"""
        try:
            # Try to access metadata endpoint
            metadata_url = urljoin(self.config.base_url, '/$metadata')
            
            async with self.session.get(metadata_url) as response:
                if response.status == 200:
                    logger.debug("OData metadata access successful")
                    return True
                elif response.status == 401:
                    logger.debug("OData service requires authentication")
                    return True  # Service is accessible but needs auth
                else:
                    logger.warning(f"OData connection test failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"OData connection test failed: {e}")
            return False
    
    async def _execute_protocol_request(self, request: ConnectorRequest) -> ConnectorResponse:
        """Execute OData request"""
        try:
            # Build OData URL
            url = self._build_odata_url(request)
            
            # Prepare headers
            headers = self.config.headers.copy()
            if request.headers:
                headers.update(request.headers)
            
            # Add CSRF token for modify operations
            if request.method.upper() in ['POST', 'PUT', 'PATCH', 'DELETE'] and self.csrf_token:
                headers['X-CSRF-Token'] = self.csrf_token
            
            # Prepare data
            data = None
            json_data = None
            
            if request.data and request.method.upper() in ['POST', 'PUT', 'PATCH']:
                json_data = request.data
                headers['Content-Type'] = 'application/json'
            
            # Execute request with retry logic
            last_exception = None
            for attempt in range(self.config.retry_attempts):
                try:
                    timeout = aiohttp.ClientTimeout(total=request.timeout or self.config.timeout)
                    
                    async with self.session.request(
                        method=request.method.upper(),
                        url=url,
                        params=request.params,
                        data=data,
                        json=json_data,
                        headers=headers,
                        timeout=timeout
                    ) as response:
                        
                        response_headers = dict(response.headers)
                        response_data = await self._parse_odata_response(response)
                        
                        # Handle OData specific error responses
                        if response.status >= 400:
                            error_message = self._extract_odata_error(response_data)
                            return ConnectorResponse(
                                status_code=response.status,
                                data=response_data,
                                headers=response_headers,
                                success=False,
                                error_message=error_message,
                                request_id=request.metadata.get('request_id')
                            )
                        
                        return ConnectorResponse(
                            status_code=response.status,
                            data=response_data,
                            headers=response_headers,
                            success=True,
                            request_id=request.metadata.get('request_id')
                        )
                        
                except Exception as e:
                    last_exception = e
                    if attempt < self.config.retry_attempts - 1:
                        await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                        logger.warning(f"OData request attempt {attempt + 1} failed, retrying: {e}")
                    else:
                        logger.error(f"All OData request attempts failed: {e}")
            
            raise last_exception or Exception("OData request failed after all retry attempts")
            
        except Exception as e:
            return ConnectorResponse(
                status_code=500,
                data=None,
                success=False,
                error_message=str(e),
                request_id=request.metadata.get('request_id')
            )
    
    def _build_odata_url(self, request: ConnectorRequest) -> str:
        """Build OData specific URL"""
        try:
            base_url = self.config.base_url.rstrip('/')
            endpoint = request.endpoint.lstrip('/')
            
            # Handle entity set operations
            if request.operation in ['read', 'list']:
                # Add OData query options
                query_params = {}
                
                # $filter
                filter_expr = request.metadata.get('filter')
                if filter_expr:
                    query_params['$filter'] = filter_expr
                
                # $select
                select_fields = request.metadata.get('select')
                if select_fields:
                    if isinstance(select_fields, list):
                        query_params['$select'] = ','.join(select_fields)
                    else:
                        query_params['$select'] = select_fields
                
                # $expand
                expand_fields = request.metadata.get('expand')
                if expand_fields:
                    if isinstance(expand_fields, list):
                        query_params['$expand'] = ','.join(expand_fields)
                    else:
                        query_params['$expand'] = expand_fields
                
                # $orderby
                orderby = request.metadata.get('orderby')
                if orderby:
                    query_params['$orderby'] = orderby
                
                # $top and $skip for paging
                top = request.metadata.get('top')
                if top:
                    query_params['$top'] = str(top)
                
                skip = request.metadata.get('skip')
                if skip:
                    query_params['$skip'] = str(skip)
                
                # Build URL with query parameters
                if query_params:
                    query_string = urlencode(query_params)
                    return f"{base_url}/{endpoint}?{query_string}"
            
            return f"{base_url}/{endpoint}"
            
        except Exception as e:
            logger.error(f"OData URL building failed: {e}")
            return urljoin(self.config.base_url, request.endpoint)
    
    async def _parse_odata_response(self, response: aiohttp.ClientResponse) -> Any:
        """Parse OData response"""
        try:
            content_type = response.headers.get('Content-Type', '').lower()
            
            if 'application/json' in content_type:
                data = await response.json()
                
                # Handle OData v2/v4 response format differences
                if self.odata_version == 'v2' and isinstance(data, dict):
                    # OData v2 wraps results in 'd' property
                    if 'd' in data:
                        return data['d']
                elif self.odata_version == 'v4' and isinstance(data, dict):
                    # OData v4 may have @odata.context
                    if 'value' in data:
                        return data['value']
                
                return data
            elif 'application/xml' in content_type or 'text/xml' in content_type:
                xml_text = await response.text()
                return self._parse_odata_xml(xml_text)
            else:
                return await response.text()
                
        except Exception as e:
            logger.warning(f"Failed to parse OData response: {e}")
            return await response.text()
    
    def _parse_odata_xml(self, xml_text: str) -> Dict[str, Any]:
        """Parse OData XML response"""
        try:
            root = ET.fromstring(xml_text)
            return self._xml_to_dict(root)
        except Exception as e:
            logger.warning(f"OData XML parsing failed: {e}")
            return {'raw_xml': xml_text}
    
    def _xml_to_dict(self, element) -> Any:
        """Convert XML element to dictionary"""
        try:
            result = {}
            
            # Add attributes
            if element.attrib:
                result['@attributes'] = element.attrib
            
            # Add text content
            if element.text and element.text.strip():
                if len(element) == 0:
                    return element.text.strip()
                result['#text'] = element.text.strip()
            
            # Add child elements
            for child in element:
                child_data = self._xml_to_dict(child)
                tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                
                if tag in result:
                    if not isinstance(result[tag], list):
                        result[tag] = [result[tag]]
                    result[tag].append(child_data)
                else:
                    result[tag] = child_data
            
            return result if result else None
            
        except Exception as e:
            logger.error(f"XML to dict conversion failed: {e}")
            return str(element.text) if element.text else None
    
    def _extract_odata_error(self, response_data: Any) -> str:
        """Extract error message from OData error response"""
        try:
            if isinstance(response_data, dict):
                # OData v2 error format
                if 'error' in response_data:
                    error = response_data['error']
                    if isinstance(error, dict):
                        message = error.get('message', {})
                        if isinstance(message, dict):
                            return message.get('value', 'OData Error')
                        else:
                            return str(message)
                
                # OData v4 error format
                if 'error' in response_data:
                    error = response_data['error']
                    return error.get('message', 'OData Error')
            
            return 'OData Error'
            
        except Exception as e:
            logger.error(f"Error extraction failed: {e}")
            return 'OData Error'
    
    async def _cleanup_session(self):
        """Clean up HTTP session"""
        try:
            if self.session:
                await self.session.close()
                self.session = None
                logger.debug(f"OData session cleaned up for {self.config.connector_id}")
        except Exception as e:
            logger.error(f"Failed to cleanup OData session: {e}")
    
    # OData-specific convenience methods
    async def get_entity_set(self, entity_set: str, filters: Optional[Dict[str, Any]] = None,
                           select: Optional[List[str]] = None, expand: Optional[List[str]] = None,
                           top: Optional[int] = None, skip: Optional[int] = None) -> ConnectorResponse:
        """Get entities from an entity set"""
        metadata = {}
        
        if filters:
            # Build OData filter expression
            filter_parts = []
            for key, value in filters.items():
                if isinstance(value, str):
                    filter_parts.append(f"{key} eq '{value}'")
                else:
                    filter_parts.append(f"{key} eq {value}")
            if filter_parts:
                metadata['filter'] = ' and '.join(filter_parts)
        
        if select:
            metadata['select'] = select
        if expand:
            metadata['expand'] = expand
        if top:
            metadata['top'] = top
        if skip:
            metadata['skip'] = skip
        
        request = ConnectorRequest(
            operation="list",
            endpoint=entity_set,
            method="GET",
            metadata=metadata
        )
        return await self.execute_request(request)
    
    async def get_entity(self, entity_set: str, key: Union[str, int, Dict[str, Any]],
                        select: Optional[List[str]] = None, expand: Optional[List[str]] = None) -> ConnectorResponse:
        """Get a specific entity by key"""
        # Build entity endpoint
        if isinstance(key, dict):
            key_parts = [f"{k}='{v}'" if isinstance(v, str) else f"{k}={v}" for k, v in key.items()]
            key_string = ','.join(key_parts)
            endpoint = f"{entity_set}({key_string})"
        else:
            if isinstance(key, str):
                endpoint = f"{entity_set}('{key}')"
            else:
                endpoint = f"{entity_set}({key})"
        
        metadata = {}
        if select:
            metadata['select'] = select
        if expand:
            metadata['expand'] = expand
        
        request = ConnectorRequest(
            operation="read",
            endpoint=endpoint,
            method="GET",
            metadata=metadata
        )
        return await self.execute_request(request)
    
    async def create_entity(self, entity_set: str, data: Dict[str, Any]) -> ConnectorResponse:
        """Create a new entity"""
        request = ConnectorRequest(
            operation="create",
            endpoint=entity_set,
            method="POST",
            data=data
        )
        return await self.execute_request(request)
    
    async def update_entity(self, entity_set: str, key: Union[str, int, Dict[str, Any]], 
                           data: Dict[str, Any], method: str = "PATCH") -> ConnectorResponse:
        """Update an existing entity"""
        # Build entity endpoint
        if isinstance(key, dict):
            key_parts = [f"{k}='{v}'" if isinstance(v, str) else f"{k}={v}" for k, v in key.items()]
            key_string = ','.join(key_parts)
            endpoint = f"{entity_set}({key_string})"
        else:
            if isinstance(key, str):
                endpoint = f"{entity_set}('{key}')"
            else:
                endpoint = f"{entity_set}({key})"
        
        request = ConnectorRequest(
            operation="update",
            endpoint=endpoint,
            method=method.upper(),
            data=data
        )
        return await self.execute_request(request)
    
    async def delete_entity(self, entity_set: str, key: Union[str, int, Dict[str, Any]]) -> ConnectorResponse:
        """Delete an entity"""
        # Build entity endpoint
        if isinstance(key, dict):
            key_parts = [f"{k}='{v}'" if isinstance(v, str) else f"{k}={v}" for k, v in key.items()]
            key_string = ','.join(key_parts)
            endpoint = f"{entity_set}({key_string})"
        else:
            if isinstance(key, str):
                endpoint = f"{entity_set}('{key}')"
            else:
                endpoint = f"{entity_set}({key})"
        
        request = ConnectorRequest(
            operation="delete",
            endpoint=endpoint,
            method="DELETE"
        )
        return await self.execute_request(request)
    
    def get_entity_sets(self) -> List[str]:
        """Get list of available entity sets"""
        return list(self.entity_sets.keys())
    
    def build_filter_expression(self, filters: Dict[str, Any]) -> str:
        """Build OData filter expression from dictionary"""
        try:
            filter_parts = []
            
            for key, value in filters.items():
                if isinstance(value, str):
                    filter_parts.append(f"{key} eq '{value}'")
                elif isinstance(value, bool):
                    filter_parts.append(f"{key} eq {str(value).lower()}")
                elif isinstance(value, (int, float)):
                    filter_parts.append(f"{key} eq {value}")
                elif isinstance(value, list):
                    # Handle 'in' operations
                    value_list = [f"'{v}'" if isinstance(v, str) else str(v) for v in value]
                    filter_parts.append(f"{key} in ({','.join(value_list)})")
            
            return ' and '.join(filter_parts)
            
        except Exception as e:
            logger.error(f"Filter expression building failed: {e}")
            return ""