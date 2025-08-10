"""
RPC Adapter - Protocol Adapter for RPC-based Services
Specialized connector implementation for RPC (Remote Procedure Call) services.
Supports JSON-RPC, XML-RPC, and custom RPC protocols.
"""

import asyncio
import logging
import json
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin
import xml.etree.ElementTree as ET

from ..base_connector import (
    BaseConnector, ConnectorConfig, ConnectorRequest, ConnectorResponse,
    ConnectionStatus, DataFormat, AuthenticationType
)

logger = logging.getLogger(__name__)

class RpcConnector(BaseConnector):
    """RPC service connector implementation"""
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.session: Optional[aiohttp.ClientSession] = None
        self.rpc_protocol = config.custom_settings.get('rpc_protocol', 'json-rpc')
        self.rpc_version = config.custom_settings.get('rpc_version', '2.0')
        self.request_id_counter = 0
    
    async def _initialize_session(self):
        """Initialize HTTP session for RPC requests"""
        try:
            connector = aiohttp.TCPConnector(
                ssl=None if self.config.ssl_verify else False,
                limit=100,
                limit_per_host=10
            )
            
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            
            # Set default headers based on RPC protocol
            headers = {}
            if self.rpc_protocol == 'json-rpc':
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            elif self.rpc_protocol == 'xml-rpc':
                headers = {
                    'Content-Type': 'text/xml',
                    'Accept': 'text/xml'
                }
            
            headers.update(self.config.headers)
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=headers
            )
            
            logger.debug(f"RPC session initialized for {self.config.connector_id} ({self.rpc_protocol})")
            
        except Exception as e:
            logger.error(f"Failed to initialize RPC session: {e}")
            raise
    
    async def _authenticate(self) -> bool:
        """Authenticate with the RPC service"""
        try:
            auth_type = self.config.authentication_type
            auth_config = self.config.authentication_config
            
            if auth_type == AuthenticationType.NONE:
                return True
            
            elif auth_type == AuthenticationType.API_KEY:
                api_key = auth_config.get('api_key')
                if not api_key:
                    logger.error("API key not provided")
                    return False
                
                key_header = auth_config.get('api_key_header', 'X-API-Key')
                self.session.headers[key_header] = api_key
                self.authentication_token = api_key
                return True
            
            elif auth_type == AuthenticationType.BASIC_AUTH:
                username = auth_config.get('username')
                password = auth_config.get('password')
                
                if not username or not password:
                    logger.error("Username or password not provided for basic auth")
                    return False
                
                auth = aiohttp.BasicAuth(username, password)
                self.session._default_auth = auth
                self.authentication_token = f"{username}:***"
                return True
            
            elif auth_type == AuthenticationType.JWT:
                jwt_token = auth_config.get('jwt_token')
                if not jwt_token:
                    logger.error("JWT token not provided")
                    return False
                
                self.session.headers['Authorization'] = f"Bearer {jwt_token}"
                self.authentication_token = jwt_token
                return True
            
            elif auth_type == AuthenticationType.CUSTOM_TOKEN:
                token = auth_config.get('token')
                token_header = auth_config.get('token_header', 'Authorization')
                
                if not token:
                    logger.error("Custom token not provided")
                    return False
                
                self.session.headers[token_header] = token
                self.authentication_token = token
                return True
            
            else:
                logger.error(f"Unsupported authentication type for RPC: {auth_type}")
                return False
                
        except Exception as e:
            logger.error(f"RPC authentication failed: {e}")
            return False
    
    async def _test_connection(self) -> bool:
        """Test the RPC service connection"""
        try:
            # Try a system method or simple test call
            if self.rpc_protocol == 'json-rpc':
                # Try system.listMethods or a simple ping
                test_methods = ['system.listMethods', 'ping', 'test']
                
                for method in test_methods:
                    try:
                        response = await self.call_method(method)
                        if response.success or response.status_code != 404:
                            logger.debug(f"RPC connection test successful with {method}")
                            return True
                    except:
                        continue
                
                # If specific methods fail, try basic connection
                async with self.session.post(self.config.base_url, json={}) as response:
                    if response.status < 500:
                        logger.debug(f"RPC basic connection test: {response.status}")
                        return True
            
            else:
                # For other RPC protocols, try basic connection
                async with self.session.get(self.config.base_url) as response:
                    if response.status < 500:
                        logger.debug(f"RPC connection test: {response.status}")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"RPC connection test failed: {e}")
            return False
    
    async def _execute_protocol_request(self, request: ConnectorRequest) -> ConnectorResponse:
        """Execute RPC request"""
        try:
            if self.rpc_protocol == 'json-rpc':
                return await self._execute_json_rpc_request(request)
            elif self.rpc_protocol == 'xml-rpc':
                return await self._execute_xml_rpc_request(request)
            else:
                return await self._execute_custom_rpc_request(request)
                
        except Exception as e:
            return ConnectorResponse(
                status_code=500,
                data=None,
                success=False,
                error_message=str(e),
                request_id=request.metadata.get('request_id')
            )
    
    async def _execute_json_rpc_request(self, request: ConnectorRequest) -> ConnectorResponse:
        """Execute JSON-RPC request"""
        try:
            # Generate request ID
            self.request_id_counter += 1
            rpc_request_id = request.metadata.get('rpc_id', self.request_id_counter)
            
            # Build JSON-RPC payload
            payload = {
                'jsonrpc': self.rpc_version,
                'method': request.operation,
                'id': rpc_request_id
            }
            
            # Add parameters
            if request.data:
                if isinstance(request.data, list):
                    payload['params'] = request.data
                elif isinstance(request.data, dict):
                    payload['params'] = request.data
                else:
                    payload['params'] = [request.data]
            
            # Prepare headers
            headers = self.config.headers.copy()
            if request.headers:
                headers.update(request.headers)
            
            # Execute request with retry logic
            last_exception = None
            for attempt in range(self.config.retry_attempts):
                try:
                    endpoint_url = urljoin(self.config.base_url, request.endpoint or '')
                    timeout = aiohttp.ClientTimeout(total=request.timeout or self.config.timeout)
                    
                    async with self.session.post(
                        endpoint_url,
                        json=payload,
                        headers=headers,
                        timeout=timeout
                    ) as response:
                        
                        response_headers = dict(response.headers)
                        
                        if response.status == 200:
                            response_data = await response.json()
                            
                            # Check for JSON-RPC error
                            if 'error' in response_data:
                                error = response_data['error']
                                error_message = error.get('message', 'RPC Error')
                                error_code = error.get('code', -1)
                                
                                return ConnectorResponse(
                                    status_code=400,
                                    data=response_data,
                                    headers=response_headers,
                                    success=False,
                                    error_message=f"JSON-RPC Error {error_code}: {error_message}",
                                    request_id=str(rpc_request_id)
                                )
                            
                            # Return successful response
                            return ConnectorResponse(
                                status_code=response.status,
                                data=response_data.get('result'),
                                headers=response_headers,
                                success=True,
                                metadata={'full_response': response_data},
                                request_id=str(rpc_request_id)
                            )
                        else:
                            error_text = await response.text()
                            return ConnectorResponse(
                                status_code=response.status,
                                data=None,
                                headers=response_headers,
                                success=False,
                                error_message=f"HTTP {response.status}: {error_text}",
                                request_id=str(rpc_request_id)
                            )
                        
                except Exception as e:
                    last_exception = e
                    if attempt < self.config.retry_attempts - 1:
                        await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                        logger.warning(f"JSON-RPC request attempt {attempt + 1} failed, retrying: {e}")
                    else:
                        logger.error(f"All JSON-RPC request attempts failed: {e}")
            
            raise last_exception or Exception("JSON-RPC request failed after all retry attempts")
            
        except Exception as e:
            return ConnectorResponse(
                status_code=500,
                data=None,
                success=False,
                error_message=str(e),
                request_id=str(rpc_request_id)
            )
    
    async def _execute_xml_rpc_request(self, request: ConnectorRequest) -> ConnectorResponse:
        """Execute XML-RPC request"""
        try:
            # Build XML-RPC payload
            xml_payload = self._build_xml_rpc_payload(request.operation, request.data)
            
            # Prepare headers
            headers = self.config.headers.copy()
            if request.headers:
                headers.update(request.headers)
            
            # Execute request
            endpoint_url = urljoin(self.config.base_url, request.endpoint or '')
            timeout = aiohttp.ClientTimeout(total=request.timeout or self.config.timeout)
            
            async with self.session.post(
                endpoint_url,
                data=xml_payload,
                headers=headers,
                timeout=timeout
            ) as response:
                
                response_headers = dict(response.headers)
                response_text = await response.text()
                
                if response.status == 200:
                    # Parse XML-RPC response
                    result = self._parse_xml_rpc_response(response_text)
                    
                    if 'fault' in result:
                        fault = result['fault']
                        return ConnectorResponse(
                            status_code=400,
                            data=fault,
                            headers=response_headers,
                            success=False,
                            error_message=f"XML-RPC Fault: {fault.get('faultString', 'Unknown error')}",
                            request_id=request.metadata.get('request_id')
                        )
                    
                    return ConnectorResponse(
                        status_code=response.status,
                        data=result.get('result'),
                        headers=response_headers,
                        success=True,
                        request_id=request.metadata.get('request_id')
                    )
                else:
                    return ConnectorResponse(
                        status_code=response.status,
                        data=None,
                        headers=response_headers,
                        success=False,
                        error_message=f"HTTP {response.status}: {response_text}",
                        request_id=request.metadata.get('request_id')
                    )
                    
        except Exception as e:
            return ConnectorResponse(
                status_code=500,
                data=None,
                success=False,
                error_message=str(e),
                request_id=request.metadata.get('request_id')
            )
    
    async def _execute_custom_rpc_request(self, request: ConnectorRequest) -> ConnectorResponse:
        """Execute custom RPC request"""
        try:
            # For custom RPC, treat as standard HTTP request
            endpoint_url = urljoin(self.config.base_url, request.endpoint or '')
            
            headers = self.config.headers.copy()
            if request.headers:
                headers.update(request.headers)
            
            # Prepare data based on format
            data = None
            json_data = None
            
            if request.data:
                if self.config.data_format == DataFormat.JSON:
                    json_data = {
                        'method': request.operation,
                        'params': request.data
                    }
                else:
                    data = str(request.data)
            
            timeout = aiohttp.ClientTimeout(total=request.timeout or self.config.timeout)
            
            async with self.session.post(
                endpoint_url,
                data=data,
                json=json_data,
                headers=headers,
                timeout=timeout
            ) as response:
                
                response_headers = dict(response.headers)
                
                # Parse response based on content type
                content_type = response.headers.get('Content-Type', '').lower()
                if 'json' in content_type:
                    response_data = await response.json()
                else:
                    response_data = await response.text()
                
                return ConnectorResponse(
                    status_code=response.status,
                    data=response_data,
                    headers=response_headers,
                    success=response.status < 400,
                    request_id=request.metadata.get('request_id')
                )
                
        except Exception as e:
            return ConnectorResponse(
                status_code=500,
                data=None,
                success=False,
                error_message=str(e),
                request_id=request.metadata.get('request_id')
            )
    
    def _build_xml_rpc_payload(self, method: str, params: Any) -> str:
        """Build XML-RPC request payload"""
        try:
            xml_parts = [
                '<?xml version="1.0"?>',
                '<methodCall>',
                f'<methodName>{self._escape_xml(method)}</methodName>',
                '<params>'
            ]
            
            if params:
                if isinstance(params, list):
                    for param in params:
                        xml_parts.append('<param>')
                        xml_parts.append(f'<value>{self._serialize_xml_rpc_value(param)}</value>')
                        xml_parts.append('</param>')
                else:
                    xml_parts.append('<param>')
                    xml_parts.append(f'<value>{self._serialize_xml_rpc_value(params)}</value>')
                    xml_parts.append('</param>')
            
            xml_parts.extend([
                '</params>',
                '</methodCall>'
            ])
            
            return '\n'.join(xml_parts)
            
        except Exception as e:
            logger.error(f"XML-RPC payload building failed: {e}")
            return f'<?xml version="1.0"?><methodCall><methodName>{method}</methodName><params></params></methodCall>'
    
    def _serialize_xml_rpc_value(self, value: Any) -> str:
        """Serialize value for XML-RPC"""
        try:
            if isinstance(value, str):
                return f'<string>{self._escape_xml(value)}</string>'
            elif isinstance(value, int):
                return f'<int>{value}</int>'
            elif isinstance(value, float):
                return f'<double>{value}</double>'
            elif isinstance(value, bool):
                return f'<boolean>{1 if value else 0}</boolean>'
            elif isinstance(value, list):
                array_items = []
                for item in value:
                    array_items.append(f'<value>{self._serialize_xml_rpc_value(item)}</value>')
                return f'<array><data>{"".join(array_items)}</data></array>'
            elif isinstance(value, dict):
                struct_items = []
                for key, val in value.items():
                    struct_items.append(f'<member><name>{self._escape_xml(key)}</name><value>{self._serialize_xml_rpc_value(val)}</value></member>')
                return f'<struct>{"".join(struct_items)}</struct>'
            else:
                return f'<string>{self._escape_xml(str(value))}</string>'
                
        except Exception as e:
            logger.error(f"XML-RPC value serialization failed: {e}")
            return f'<string>{self._escape_xml(str(value))}</string>'
    
    def _parse_xml_rpc_response(self, xml_text: str) -> Dict[str, Any]:
        """Parse XML-RPC response"""
        try:
            root = ET.fromstring(xml_text)
            
            # Check for fault
            fault_elem = root.find('.//fault')
            if fault_elem is not None:
                fault_value = fault_elem.find('.//value')
                if fault_value is not None:
                    fault_data = self._parse_xml_rpc_value(fault_value)
                    return {'fault': fault_data}
            
            # Parse normal response
            params_elem = root.find('.//params')
            if params_elem is not None:
                param_elem = params_elem.find('.//param')
                if param_elem is not None:
                    value_elem = param_elem.find('.//value')
                    if value_elem is not None:
                        result = self._parse_xml_rpc_value(value_elem)
                        return {'result': result}
            
            return {'result': None}
            
        except Exception as e:
            logger.error(f"XML-RPC response parsing failed: {e}")
            return {'fault': {'faultCode': -1, 'faultString': f'Parse error: {e}'}}
    
    def _parse_xml_rpc_value(self, value_elem) -> Any:
        """Parse XML-RPC value element"""
        try:
            # Check for typed values
            for child in value_elem:
                tag = child.tag.lower()
                
                if tag == 'string':
                    return child.text or ''
                elif tag == 'int' or tag == 'i4':
                    return int(child.text) if child.text else 0
                elif tag == 'double':
                    return float(child.text) if child.text else 0.0
                elif tag == 'boolean':
                    return bool(int(child.text)) if child.text else False
                elif tag == 'array':
                    data_elem = child.find('.//data')
                    if data_elem is not None:
                        return [self._parse_xml_rpc_value(val) for val in data_elem.findall('.//value')]
                elif tag == 'struct':
                    result = {}
                    for member in child.findall('.//member'):
                        name_elem = member.find('.//name')
                        value_elem = member.find('.//value')
                        if name_elem is not None and value_elem is not None:
                            result[name_elem.text] = self._parse_xml_rpc_value(value_elem)
                    return result
            
            # Default to string if no type specified
            return value_elem.text or ''
            
        except Exception as e:
            logger.error(f"XML-RPC value parsing failed: {e}")
            return value_elem.text or ''
    
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
                logger.debug(f"RPC session cleaned up for {self.config.connector_id}")
        except Exception as e:
            logger.error(f"Failed to cleanup RPC session: {e}")
    
    # RPC-specific convenience methods
    async def call_method(self, method: str, params: Optional[Union[List[Any], Dict[str, Any], Any]] = None) -> ConnectorResponse:
        """Call an RPC method"""
        request = ConnectorRequest(
            operation=method,
            endpoint="",
            method="POST",
            data=params
        )
        return await self.execute_request(request)
    
    async def batch_call(self, methods: List[Dict[str, Any]]) -> List[ConnectorResponse]:
        """Execute multiple RPC calls in batch"""
        responses = []
        
        for method_call in methods:
            method = method_call.get('method')
            params = method_call.get('params')
            
            if method:
                response = await self.call_method(method, params)
                responses.append(response)
        
        return responses
    
    def get_protocol_info(self) -> Dict[str, Any]:
        """Get RPC protocol information"""
        return {
            'protocol': self.rpc_protocol,
            'version': self.rpc_version,
            'data_format': self.config.data_format.value,
            'supports_batch': self.rpc_protocol == 'json-rpc'
        }