"""
REST Adapter - Protocol Adapter for REST APIs
Specialized connector implementation for RESTful web services.
Supports JSON, XML, and other REST-compatible data formats.
"""

import asyncio
import logging
import json
import aiohttp
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin, urlparse

from ..base_connector import (
    BaseConnector, ConnectorConfig, ConnectorRequest, ConnectorResponse,
    ConnectionStatus, DataFormat, AuthenticationType
)

logger = logging.getLogger(__name__)

class RestConnector(BaseConnector):
    """REST API connector implementation"""
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.session: Optional[aiohttp.ClientSession] = None
        self.connector_timeout = aiohttp.ClientTimeout(total=config.timeout)
    
    async def _initialize_session(self):
        """Initialize HTTP session with proper configuration"""
        try:
            # Configure SSL verification
            ssl_context = None if self.config.ssl_verify else False
            
            # Configure proxy if provided
            connector = None
            if self.config.proxy_config:
                connector = aiohttp.TCPConnector(
                    ssl=ssl_context,
                    limit=100,
                    limit_per_host=10
                )
            else:
                connector = aiohttp.TCPConnector(
                    ssl=ssl_context,
                    limit=100,
                    limit_per_host=10
                )
            
            # Create session
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=self.connector_timeout,
                headers=self.config.headers
            )
            
            logger.debug(f"REST session initialized for {self.config.connector_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize REST session: {e}")
            raise
    
    async def _authenticate(self) -> bool:
        """Authenticate with the REST API"""
        try:
            auth_type = self.config.authentication_type
            auth_config = self.config.authentication_config
            
            if auth_type == AuthenticationType.NONE:
                return True
            
            elif auth_type == AuthenticationType.API_KEY:
                # API key authentication - usually via headers
                api_key = auth_config.get('api_key')
                if not api_key:
                    logger.error("API key not provided")
                    return False
                
                # Add API key to headers
                key_header = auth_config.get('api_key_header', 'X-API-Key')
                self.session.headers[key_header] = api_key
                self.authentication_token = api_key
                return True
            
            elif auth_type == AuthenticationType.BASIC_AUTH:
                # Basic authentication
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
                # OAuth 2.0 authentication
                return await self._oauth2_authenticate()
            
            elif auth_type == AuthenticationType.JWT:
                # JWT token authentication
                jwt_token = auth_config.get('jwt_token')
                if not jwt_token:
                    logger.error("JWT token not provided")
                    return False
                
                self.session.headers['Authorization'] = f"Bearer {jwt_token}"
                self.authentication_token = jwt_token
                return True
            
            elif auth_type == AuthenticationType.CUSTOM_TOKEN:
                # Custom token authentication
                token = auth_config.get('token')
                token_header = auth_config.get('token_header', 'Authorization')
                token_prefix = auth_config.get('token_prefix', 'Bearer')
                
                if not token:
                    logger.error("Custom token not provided")
                    return False
                
                if token_prefix:
                    self.session.headers[token_header] = f"{token_prefix} {token}"
                else:
                    self.session.headers[token_header] = token
                
                self.authentication_token = token
                return True
            
            else:
                logger.error(f"Unsupported authentication type: {auth_type}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    async def _oauth2_authenticate(self) -> bool:
        """Perform OAuth 2.0 authentication"""
        try:
            auth_config = self.config.authentication_config
            
            # OAuth 2.0 configuration
            token_url = auth_config.get('token_url')
            client_id = auth_config.get('client_id')
            client_secret = auth_config.get('client_secret')
            grant_type = auth_config.get('grant_type', 'client_credentials')
            scope = auth_config.get('scope', '')
            
            if not all([token_url, client_id, client_secret]):
                logger.error("OAuth 2.0 configuration incomplete")
                return False
            
            # Prepare token request
            token_data = {
                'grant_type': grant_type,
                'client_id': client_id,
                'client_secret': client_secret
            }
            
            if scope:
                token_data['scope'] = scope
            
            # Add additional OAuth parameters
            for key, value in auth_config.items():
                if key.startswith('oauth_') and key not in token_data:
                    token_data[key.replace('oauth_', '')] = value
            
            # Make token request
            async with self.session.post(token_url, data=token_data) as response:
                if response.status == 200:
                    token_response = await response.json()
                    
                    access_token = token_response.get('access_token')
                    if not access_token:
                        logger.error("No access token in OAuth response")
                        return False
                    
                    # Set authentication header
                    self.session.headers['Authorization'] = f"Bearer {access_token}"
                    self.authentication_token = access_token
                    
                    # Set token expiration
                    expires_in = token_response.get('expires_in')
                    if expires_in:
                        self.token_expires_at = datetime.utcnow().timestamp() + expires_in - 60  # 1 minute buffer
                    
                    logger.info("OAuth 2.0 authentication successful")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"OAuth 2.0 authentication failed: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"OAuth 2.0 authentication error: {e}")
            return False
    
    async def _test_connection(self) -> bool:
        """Test the REST API connection"""
        try:
            # Try health endpoint first
            health_endpoint = self.config.endpoints.get('health', '/health')
            test_url = urljoin(self.config.base_url, health_endpoint)
            
            async with self.session.get(test_url) as response:
                if response.status < 400:
                    logger.debug(f"Health check successful: {response.status}")
                    return True
            
            # Fallback to base URL
            async with self.session.get(self.config.base_url) as response:
                if response.status < 500:  # Accept any non-server error as connection success
                    logger.debug(f"Base URL connection successful: {response.status}")
                    return True
                else:
                    logger.warning(f"Connection test failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    async def _execute_protocol_request(self, request: ConnectorRequest) -> ConnectorResponse:
        """Execute REST API request"""
        try:
            # Build request URL
            url = urljoin(self.config.base_url, request.endpoint)
            
            # Prepare request parameters
            method = request.method.upper()
            headers = self.config.headers.copy()
            if request.headers:
                headers.update(request.headers)
            
            params = request.params
            timeout = aiohttp.ClientTimeout(total=request.timeout or self.config.timeout)
            
            # Prepare request data based on format
            data = None
            json_data = None
            
            if request.data and method in ['POST', 'PUT', 'PATCH']:
                if self.config.data_format == DataFormat.JSON:
                    json_data = request.data
                    headers['Content-Type'] = 'application/json'
                elif self.config.data_format == DataFormat.XML:
                    data = self._serialize_to_xml(request.data)
                    headers['Content-Type'] = 'application/xml'
                elif self.config.data_format == DataFormat.FORM_DATA:
                    data = aiohttp.FormData()
                    for key, value in request.data.items():
                        data.add_field(key, str(value))
                    # Don't set Content-Type for FormData, aiohttp will set it
                else:
                    data = str(request.data)
            
            # Execute request with retry logic
            last_exception = None
            for attempt in range(self.config.retry_attempts):
                try:
                    async with self.session.request(
                        method=method,
                        url=url,
                        params=params,
                        data=data,
                        json=json_data,
                        headers=headers,
                        timeout=timeout
                    ) as response:
                        
                        # Read response
                        response_headers = dict(response.headers)
                        response_data = await self._parse_response(response)
                        
                        # Create response object
                        connector_response = ConnectorResponse(
                            status_code=response.status,
                            data=response_data,
                            headers=response_headers,
                            success=response.status < 400,
                            request_id=request.metadata.get('request_id')
                        )
                        
                        if response.status >= 400:
                            connector_response.error_message = f"HTTP {response.status}: {response.reason}"
                        
                        return connector_response
                        
                except Exception as e:
                    last_exception = e
                    if attempt < self.config.retry_attempts - 1:
                        await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                        logger.warning(f"Request attempt {attempt + 1} failed, retrying: {e}")
                    else:
                        logger.error(f"All request attempts failed: {e}")
            
            # If we get here, all attempts failed
            raise last_exception or Exception("Request failed after all retry attempts")
            
        except Exception as e:
            return ConnectorResponse(
                status_code=500,
                data=None,
                success=False,
                error_message=str(e),
                request_id=request.metadata.get('request_id')
            )
    
    async def _parse_response(self, response: aiohttp.ClientResponse) -> Any:
        """Parse response based on content type"""
        try:
            content_type = response.headers.get('Content-Type', '').lower()
            
            if 'application/json' in content_type:
                return await response.json()
            elif 'application/xml' in content_type or 'text/xml' in content_type:
                text = await response.text()
                return self._parse_xml(text)
            elif 'text/' in content_type:
                return await response.text()
            else:
                # Binary content
                return await response.read()
                
        except Exception as e:
            logger.warning(f"Failed to parse response: {e}")
            return await response.text()
    
    def _serialize_to_xml(self, data: Any) -> str:
        """Serialize data to XML format"""
        try:
            if isinstance(data, dict):
                # Simple XML serialization
                xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>', '<root>']
                for key, value in data.items():
                    xml_parts.append(f'<{key}>{self._escape_xml(str(value))}</{key}>')
                xml_parts.append('</root>')
                return '\n'.join(xml_parts)
            else:
                return f'<?xml version="1.0" encoding="UTF-8"?><root>{self._escape_xml(str(data))}</root>'
        except Exception as e:
            logger.error(f"XML serialization failed: {e}")
            return str(data)
    
    def _parse_xml(self, xml_text: str) -> Dict[str, Any]:
        """Parse XML response to dictionary"""
        try:
            # Simple XML parsing - in production, use proper XML parser like lxml
            import xml.etree.ElementTree as ET
            
            root = ET.fromstring(xml_text)
            return self._xml_to_dict(root)
        except Exception as e:
            logger.warning(f"XML parsing failed: {e}")
            return {'raw_xml': xml_text}
    
    def _xml_to_dict(self, element) -> Dict[str, Any]:
        """Convert XML element to dictionary"""
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
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        
        return result
    
    def _escape_xml(self, text: str) -> str:
        """Escape XML special characters"""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&apos;'))
    
    async def _cleanup_session(self):
        """Clean up HTTP session"""
        try:
            if self.session:
                await self.session.close()
                self.session = None
                logger.debug(f"REST session cleaned up for {self.config.connector_id}")
        except Exception as e:
            logger.error(f"Failed to cleanup session: {e}")
    
    # REST-specific convenience methods
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, 
                  headers: Optional[Dict[str, str]] = None) -> ConnectorResponse:
        """Convenience method for GET requests"""
        request = ConnectorRequest(
            operation="get",
            endpoint=endpoint,
            method="GET",
            params=params,
            headers=headers
        )
        return await self.execute_request(request)
    
    async def post(self, endpoint: str, data: Optional[Any] = None, 
                   params: Optional[Dict[str, Any]] = None,
                   headers: Optional[Dict[str, str]] = None) -> ConnectorResponse:
        """Convenience method for POST requests"""
        request = ConnectorRequest(
            operation="post",
            endpoint=endpoint,
            method="POST",
            data=data,
            params=params,
            headers=headers
        )
        return await self.execute_request(request)
    
    async def put(self, endpoint: str, data: Optional[Any] = None,
                  params: Optional[Dict[str, Any]] = None,
                  headers: Optional[Dict[str, str]] = None) -> ConnectorResponse:
        """Convenience method for PUT requests"""
        request = ConnectorRequest(
            operation="put",
            endpoint=endpoint,
            method="PUT",
            data=data,
            params=params,
            headers=headers
        )
        return await self.execute_request(request)
    
    async def patch(self, endpoint: str, data: Optional[Any] = None,
                    params: Optional[Dict[str, Any]] = None,
                    headers: Optional[Dict[str, str]] = None) -> ConnectorResponse:
        """Convenience method for PATCH requests"""
        request = ConnectorRequest(
            operation="patch",
            endpoint=endpoint,
            method="PATCH",
            data=data,
            params=params,
            headers=headers
        )
        return await self.execute_request(request)
    
    async def delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None,
                     headers: Optional[Dict[str, str]] = None) -> ConnectorResponse:
        """Convenience method for DELETE requests"""
        request = ConnectorRequest(
            operation="delete",
            endpoint=endpoint,
            method="DELETE",
            params=params,
            headers=headers
        )
        return await self.execute_request(request)
    
    async def upload_file(self, endpoint: str, file_path: str, 
                         field_name: str = 'file',
                         additional_data: Optional[Dict[str, Any]] = None) -> ConnectorResponse:
        """Upload a file via multipart form data"""
        try:
            data = aiohttp.FormData()
            
            # Add file
            with open(file_path, 'rb') as file:
                data.add_field(field_name, file, filename=file_path.split('/')[-1])
            
            # Add additional form data
            if additional_data:
                for key, value in additional_data.items():
                    data.add_field(key, str(value))
            
            request = ConnectorRequest(
                operation="upload",
                endpoint=endpoint,
                method="POST",
                data=data
            )
            
            return await self.execute_request(request)
            
        except Exception as e:
            return ConnectorResponse(
                status_code=500,
                data=None,
                success=False,
                error_message=f"File upload failed: {e}"
            )