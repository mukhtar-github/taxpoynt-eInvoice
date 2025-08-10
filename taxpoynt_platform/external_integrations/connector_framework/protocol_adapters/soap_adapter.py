"""
SOAP Adapter - Protocol Adapter for SOAP/XML Web Services
Specialized connector implementation for SOAP-based web services.
Supports WSDL parsing, SOAP envelope creation, and XML processing.
"""

import asyncio
import logging
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

class SoapConnector(BaseConnector):
    """SOAP web service connector implementation"""
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.session: Optional[aiohttp.ClientSession] = None
        self.wsdl_content: Optional[str] = None
        self.soap_operations: Dict[str, Dict[str, Any]] = {}
        self.namespace_map: Dict[str, str] = {}
        self.target_namespace: Optional[str] = None
        self.service_url: Optional[str] = None
    
    async def _initialize_session(self):
        """Initialize HTTP session for SOAP requests"""
        try:
            connector = aiohttp.TCPConnector(
                ssl=None if self.config.ssl_verify else False,
                limit=100,
                limit_per_host=10
            )
            
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=self.config.headers
            )
            
            # Load WSDL if configured
            wsdl_url = self.config.custom_settings.get('wsdl_url')
            if wsdl_url:
                await self._load_wsdl(wsdl_url)
            
            logger.debug(f"SOAP session initialized for {self.config.connector_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize SOAP session: {e}")
            raise
    
    async def _load_wsdl(self, wsdl_url: str):
        """Load and parse WSDL definition"""
        try:
            async with self.session.get(wsdl_url) as response:
                if response.status == 200:
                    self.wsdl_content = await response.text()
                    await self._parse_wsdl()
                    logger.info(f"WSDL loaded successfully from {wsdl_url}")
                else:
                    logger.error(f"Failed to load WSDL: HTTP {response.status}")
                    
        except Exception as e:
            logger.error(f"WSDL loading failed: {e}")
    
    async def _parse_wsdl(self):
        """Parse WSDL content to extract operations and types"""
        try:
            if not self.wsdl_content:
                return
            
            root = ET.fromstring(self.wsdl_content)
            
            # Extract namespaces
            for prefix, uri in root.attrib.items():
                if prefix.startswith('xmlns:'):
                    self.namespace_map[prefix[6:]] = uri
                elif prefix == 'xmlns':
                    self.namespace_map[''] = uri
            
            # Find target namespace
            self.target_namespace = root.get('targetNamespace')
            
            # Extract service endpoint
            service_elements = root.findall('.//{http://schemas.xmlsoap.org/wsdl/}service')
            for service in service_elements:
                ports = service.findall('.//{http://schemas.xmlsoap.org/wsdl/}port')
                for port in ports:
                    address = port.find('.//{http://schemas.xmlsoap.org/wsdl/soap/}address')
                    if address is not None:
                        self.service_url = address.get('location')
                        break
                if self.service_url:
                    break
            
            # Extract operations
            port_types = root.findall('.//{http://schemas.xmlsoap.org/wsdl/}portType')
            for port_type in port_types:
                operations = port_type.findall('.//{http://schemas.xmlsoap.org/wsdl/}operation')
                for operation in operations:
                    op_name = operation.get('name')
                    if op_name:
                        self.soap_operations[op_name] = {
                            'name': op_name,
                            'input': None,
                            'output': None
                        }
                        
                        # Extract input/output messages
                        input_elem = operation.find('.//{http://schemas.xmlsoap.org/wsdl/}input')
                        if input_elem is not None:
                            self.soap_operations[op_name]['input'] = input_elem.get('message')
                        
                        output_elem = operation.find('.//{http://schemas.xmlsoap.org/wsdl/}output')
                        if output_elem is not None:
                            self.soap_operations[op_name]['output'] = output_elem.get('message')
            
            logger.debug(f"Parsed WSDL: found {len(self.soap_operations)} operations")
            
        except Exception as e:
            logger.error(f"WSDL parsing failed: {e}")
    
    async def _authenticate(self) -> bool:
        """Authenticate with the SOAP service"""
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
            
            elif auth_type == AuthenticationType.CUSTOM_TOKEN:
                # WS-Security or custom token authentication
                token = auth_config.get('token')
                if token:
                    self.authentication_token = token
                    return True
                else:
                    logger.error("Custom token not provided")
                    return False
            
            else:
                logger.error(f"Unsupported authentication type for SOAP: {auth_type}")
                return False
                
        except Exception as e:
            logger.error(f"SOAP authentication failed: {e}")
            return False
    
    async def _test_connection(self) -> bool:
        """Test the SOAP service connection"""
        try:
            # Try to access WSDL first
            wsdl_url = self.config.custom_settings.get('wsdl_url')
            if wsdl_url:
                async with self.session.get(wsdl_url) as response:
                    if response.status == 200:
                        logger.debug("WSDL access successful")
                        return True
            
            # Fallback to service URL
            test_url = self.service_url or self.config.base_url
            async with self.session.get(test_url) as response:
                # SOAP services often return 405 for GET requests, which is okay
                if response.status < 500 or response.status == 405:
                    logger.debug(f"SOAP service connection test: {response.status}")
                    return True
                else:
                    logger.warning(f"SOAP connection test failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"SOAP connection test failed: {e}")
            return False
    
    async def _execute_protocol_request(self, request: ConnectorRequest) -> ConnectorResponse:
        """Execute SOAP request"""
        try:
            # Determine service URL
            service_url = self.service_url or urljoin(self.config.base_url, request.endpoint)
            
            # Create SOAP envelope
            soap_envelope = self._create_soap_envelope(request)
            
            # Prepare headers
            headers = self.config.headers.copy()
            headers.update({
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': request.metadata.get('soap_action', '""')
            })
            
            if request.headers:
                headers.update(request.headers)
            
            # Execute request with retry logic
            last_exception = None
            for attempt in range(self.config.retry_attempts):
                try:
                    timeout = aiohttp.ClientTimeout(total=request.timeout or self.config.timeout)
                    
                    async with self.session.post(
                        service_url,
                        data=soap_envelope,
                        headers=headers,
                        timeout=timeout
                    ) as response:
                        
                        response_headers = dict(response.headers)
                        response_text = await response.text()
                        
                        # Parse SOAP response
                        response_data = await self._parse_soap_response(response_text)
                        
                        # Check for SOAP faults
                        soap_fault = self._extract_soap_fault(response_data)
                        if soap_fault:
                            return ConnectorResponse(
                                status_code=500,
                                data=soap_fault,
                                headers=response_headers,
                                success=False,
                                error_message=soap_fault.get('faultstring', 'SOAP Fault'),
                                request_id=request.metadata.get('request_id')
                            )
                        
                        return ConnectorResponse(
                            status_code=response.status,
                            data=response_data,
                            headers=response_headers,
                            success=response.status < 400,
                            request_id=request.metadata.get('request_id')
                        )
                        
                except Exception as e:
                    last_exception = e
                    if attempt < self.config.retry_attempts - 1:
                        await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                        logger.warning(f"SOAP request attempt {attempt + 1} failed, retrying: {e}")
                    else:
                        logger.error(f"All SOAP request attempts failed: {e}")
            
            raise last_exception or Exception("SOAP request failed after all retry attempts")
            
        except Exception as e:
            return ConnectorResponse(
                status_code=500,
                data=None,
                success=False,
                error_message=str(e),
                request_id=request.metadata.get('request_id')
            )
    
    def _create_soap_envelope(self, request: ConnectorRequest) -> str:
        """Create SOAP envelope for the request"""
        try:
            # Get namespace configuration
            target_ns = self.target_namespace or self.config.custom_settings.get('target_namespace', 'http://tempuri.org/')
            soap_ns = "http://schemas.xmlsoap.org/soap/envelope/"
            
            # Create SOAP envelope
            envelope_parts = [
                '<?xml version="1.0" encoding="utf-8"?>',
                f'<soap:Envelope xmlns:soap="{soap_ns}" xmlns:tns="{target_ns}">',
                '  <soap:Header>'
            ]
            
            # Add WS-Security header if authentication token is present
            if self.authentication_token and self.config.authentication_type == AuthenticationType.CUSTOM_TOKEN:
                envelope_parts.extend([
                    '    <wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">',
                    f'      <wsse:UsernameToken>',
                    f'        <wsse:Username>{self.config.authentication_config.get("username", "")}</wsse:Username>',
                    f'        <wsse:Password>{self.authentication_token}</wsse:Password>',
                    f'      </wsse:UsernameToken>',
                    '    </wsse:Security>'
                ])
            
            envelope_parts.extend([
                '  </soap:Header>',
                '  <soap:Body>'
            ])
            
            # Add operation call
            operation_name = request.operation
            if operation_name in self.soap_operations:
                envelope_parts.append(f'    <tns:{operation_name}>')
                
                # Add parameters
                if request.data:
                    if isinstance(request.data, dict):
                        for key, value in request.data.items():
                            envelope_parts.append(f'      <tns:{key}>{self._escape_xml(str(value))}</tns:{key}>')
                    else:
                        envelope_parts.append(f'      <tns:value>{self._escape_xml(str(request.data))}</tns:value>')
                
                envelope_parts.append(f'    </tns:{operation_name}>')
            else:
                # Generic operation
                envelope_parts.append(f'    <tns:{operation_name}>')
                if request.data:
                    envelope_parts.append(f'      {self._serialize_data_to_xml(request.data)}')
                envelope_parts.append(f'    </tns:{operation_name}>')
            
            envelope_parts.extend([
                '  </soap:Body>',
                '</soap:Envelope>'
            ])
            
            return '\n'.join(envelope_parts)
            
        except Exception as e:
            logger.error(f"SOAP envelope creation failed: {e}")
            # Return minimal envelope
            return f'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <{request.operation}>
      <value>{self._escape_xml(str(request.data or ""))}</value>
    </{request.operation}>
  </soap:Body>
</soap:Envelope>'''
    
    async def _parse_soap_response(self, response_text: str) -> Dict[str, Any]:
        """Parse SOAP response XML"""
        try:
            root = ET.fromstring(response_text)
            
            # Remove namespace prefixes for easier parsing
            self._strip_namespace_prefixes(root)
            
            # Find SOAP Body
            body = root.find('.//Body')
            if body is not None:
                # Extract body content
                body_content = {}
                for child in body:
                    body_content[child.tag] = self._xml_element_to_dict(child)
                
                return {
                    'soap_body': body_content,
                    'raw_xml': response_text
                }
            else:
                return {
                    'raw_xml': response_text,
                    'parsed': self._xml_element_to_dict(root)
                }
                
        except Exception as e:
            logger.error(f"SOAP response parsing failed: {e}")
            return {
                'raw_xml': response_text,
                'parse_error': str(e)
            }
    
    def _extract_soap_fault(self, response_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract SOAP fault information"""
        try:
            soap_body = response_data.get('soap_body', {})
            
            # Look for SOAP fault
            fault = soap_body.get('Fault')
            if fault:
                return {
                    'faultcode': fault.get('faultcode', 'Unknown'),
                    'faultstring': fault.get('faultstring', 'SOAP Fault occurred'),
                    'detail': fault.get('detail')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"SOAP fault extraction failed: {e}")
            return None
    
    def _strip_namespace_prefixes(self, element):
        """Remove namespace prefixes from XML element tags"""
        try:
            # Remove namespace from tag
            if '}' in element.tag:
                element.tag = element.tag.split('}')[1]
            
            # Process children recursively
            for child in element:
                self._strip_namespace_prefixes(child)
                
        except Exception as e:
            logger.error(f"Namespace stripping failed: {e}")
    
    def _xml_element_to_dict(self, element) -> Any:
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
                child_data = self._xml_element_to_dict(child)
                if child.tag in result:
                    if not isinstance(result[child.tag], list):
                        result[child.tag] = [result[child.tag]]
                    result[child.tag].append(child_data)
                else:
                    result[child.tag] = child_data
            
            return result if result else None
            
        except Exception as e:
            logger.error(f"XML to dict conversion failed: {e}")
            return str(element.text) if element.text else None
    
    def _serialize_data_to_xml(self, data: Any) -> str:
        """Serialize data to XML format"""
        try:
            if isinstance(data, dict):
                xml_parts = []
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        xml_parts.append(f'<{key}>{self._serialize_data_to_xml(value)}</{key}>')
                    else:
                        xml_parts.append(f'<{key}>{self._escape_xml(str(value))}</{key}>')
                return '\n'.join(xml_parts)
            elif isinstance(data, list):
                xml_parts = []
                for item in data:
                    xml_parts.append(f'<item>{self._serialize_data_to_xml(item)}</item>')
                return '\n'.join(xml_parts)
            else:
                return self._escape_xml(str(data))
                
        except Exception as e:
            logger.error(f"Data serialization failed: {e}")
            return self._escape_xml(str(data))
    
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
                logger.debug(f"SOAP session cleaned up for {self.config.connector_id}")
        except Exception as e:
            logger.error(f"Failed to cleanup SOAP session: {e}")
    
    # SOAP-specific convenience methods
    async def call_operation(self, operation_name: str, parameters: Optional[Dict[str, Any]] = None,
                           soap_action: Optional[str] = None) -> ConnectorResponse:
        """Call a SOAP operation"""
        request = ConnectorRequest(
            operation=operation_name,
            endpoint="",  # SOAP uses single endpoint
            method="POST",
            data=parameters,
            metadata={
                'soap_action': soap_action or f'"{operation_name}"'
            }
        )
        return await self.execute_request(request)
    
    def get_available_operations(self) -> List[str]:
        """Get list of available SOAP operations"""
        return list(self.soap_operations.keys())
    
    def get_operation_info(self, operation_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific SOAP operation"""
        return self.soap_operations.get(operation_name)