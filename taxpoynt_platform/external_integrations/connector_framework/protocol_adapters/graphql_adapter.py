"""
GraphQL Adapter - Protocol Adapter for GraphQL APIs
Specialized connector implementation for GraphQL endpoints.
Supports queries, mutations, subscriptions, and schema introspection.
"""

import asyncio
import logging
import json
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin

from ..base_connector import (
    BaseConnector, ConnectorConfig, ConnectorRequest, ConnectorResponse,
    ConnectionStatus, DataFormat, AuthenticationType
)

logger = logging.getLogger(__name__)

class GraphQLConnector(BaseConnector):
    """GraphQL API connector implementation"""
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.session: Optional[aiohttp.ClientSession] = None
        self.schema: Optional[Dict[str, Any]] = None
        self.introspection_query = """
        query IntrospectionQuery {
          __schema {
            queryType { name }
            mutationType { name }
            subscriptionType { name }
            types {
              ...FullType
            }
            directives {
              name
              description
              locations
              args {
                ...InputValue
              }
            }
          }
        }
        
        fragment FullType on __Type {
          kind
          name
          description
          fields(includeDeprecated: true) {
            name
            description
            args {
              ...InputValue
            }
            type {
              ...TypeRef
            }
            isDeprecated
            deprecationReason
          }
          inputFields {
            ...InputValue
          }
          interfaces {
            ...TypeRef
          }
          enumValues(includeDeprecated: true) {
            name
            description
            isDeprecated
            deprecationReason
          }
          possibleTypes {
            ...TypeRef
          }
        }
        
        fragment InputValue on __InputValue {
          name
          description
          type { ...TypeRef }
          defaultValue
        }
        
        fragment TypeRef on __Type {
          kind
          name
          ofType {
            kind
            name
            ofType {
              kind
              name
              ofType {
                kind
                name
                ofType {
                  kind
                  name
                  ofType {
                    kind
                    name
                    ofType {
                      kind
                      name
                      ofType {
                        kind
                        name
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """
    
    async def _initialize_session(self):
        """Initialize HTTP session for GraphQL requests"""
        try:
            connector = aiohttp.TCPConnector(
                ssl=None if self.config.ssl_verify else False,
                limit=100,
                limit_per_host=10
            )
            
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            
            # Set default headers for GraphQL
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            headers.update(self.config.headers)
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=headers
            )
            
            # Load schema if introspection is enabled
            if self.config.custom_settings.get('introspection_enabled', True):
                await self._load_schema()
            
            logger.debug(f"GraphQL session initialized for {self.config.connector_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize GraphQL session: {e}")
            raise
    
    async def _load_schema(self):
        """Load GraphQL schema via introspection"""
        try:
            introspection_url = self.config.endpoints.get('introspection') or self.config.endpoints.get('graphql')
            if not introspection_url:
                introspection_url = urljoin(self.config.base_url, '/graphql')
            else:
                introspection_url = urljoin(self.config.base_url, introspection_url)
            
            payload = {
                'query': self.introspection_query
            }
            
            async with self.session.post(introspection_url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    if 'data' in result and '__schema' in result['data']:
                        self.schema = result['data']['__schema']
                        logger.info("GraphQL schema loaded successfully")
                    else:
                        logger.warning("Invalid introspection response")
                else:
                    logger.warning(f"Schema introspection failed: HTTP {response.status}")
                    
        except Exception as e:
            logger.warning(f"Schema loading failed: {e}")
    
    async def _authenticate(self) -> bool:
        """Authenticate with the GraphQL API"""
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
            
            elif auth_type == AuthenticationType.JWT:
                jwt_token = auth_config.get('jwt_token')
                if not jwt_token:
                    logger.error("JWT token not provided")
                    return False
                
                self.session.headers['Authorization'] = f"Bearer {jwt_token}"
                self.authentication_token = jwt_token
                return True
            
            elif auth_type == AuthenticationType.OAUTH2:
                # OAuth 2.0 authentication (similar to REST adapter)
                return await self._oauth2_authenticate()
            
            elif auth_type == AuthenticationType.CUSTOM_TOKEN:
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
                logger.error(f"Unsupported authentication type for GraphQL: {auth_type}")
                return False
                
        except Exception as e:
            logger.error(f"GraphQL authentication failed: {e}")
            return False
    
    async def _oauth2_authenticate(self) -> bool:
        """Perform OAuth 2.0 authentication"""
        try:
            auth_config = self.config.authentication_config
            
            token_url = auth_config.get('token_url')
            client_id = auth_config.get('client_id')
            client_secret = auth_config.get('client_secret')
            grant_type = auth_config.get('grant_type', 'client_credentials')
            scope = auth_config.get('scope', '')
            
            if not all([token_url, client_id, client_secret]):
                logger.error("OAuth 2.0 configuration incomplete")
                return False
            
            token_data = {
                'grant_type': grant_type,
                'client_id': client_id,
                'client_secret': client_secret
            }
            
            if scope:
                token_data['scope'] = scope
            
            async with self.session.post(token_url, data=token_data) as response:
                if response.status == 200:
                    token_response = await response.json()
                    access_token = token_response.get('access_token')
                    
                    if access_token:
                        self.session.headers['Authorization'] = f"Bearer {access_token}"
                        self.authentication_token = access_token
                        
                        expires_in = token_response.get('expires_in')
                        if expires_in:
                            self.token_expires_at = datetime.utcnow().timestamp() + expires_in - 60
                        
                        logger.info("OAuth 2.0 authentication successful")
                        return True
                    else:
                        logger.error("No access token in OAuth response")
                        return False
                else:
                    error_text = await response.text()
                    logger.error(f"OAuth 2.0 authentication failed: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"OAuth 2.0 authentication error: {e}")
            return False
    
    async def _test_connection(self) -> bool:
        """Test the GraphQL endpoint connection"""
        try:
            # Try a simple introspection query
            test_query = "{ __typename }"
            graphql_url = self.config.endpoints.get('graphql', '/graphql')
            test_url = urljoin(self.config.base_url, graphql_url)
            
            payload = {'query': test_query}
            
            async with self.session.post(test_url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    if 'data' in result:
                        logger.debug("GraphQL connection test successful")
                        return True
                    elif 'errors' in result:
                        # GraphQL endpoint is working but query may be invalid
                        logger.debug("GraphQL endpoint responding with errors (but accessible)")
                        return True
                
                logger.warning(f"GraphQL connection test failed: {response.status}")
                return False
                
        except Exception as e:
            logger.error(f"GraphQL connection test failed: {e}")
            return False
    
    async def _execute_protocol_request(self, request: ConnectorRequest) -> ConnectorResponse:
        """Execute GraphQL request"""
        try:
            graphql_url = urljoin(self.config.base_url, request.endpoint or self.config.endpoints.get('graphql', '/graphql'))
            
            # Prepare GraphQL payload
            payload = self._prepare_graphql_payload(request)
            
            # Prepare headers
            headers = self.config.headers.copy()
            if request.headers:
                headers.update(request.headers)
            
            # Execute request with retry logic
            last_exception = None
            for attempt in range(self.config.retry_attempts):
                try:
                    timeout = aiohttp.ClientTimeout(total=request.timeout or self.config.timeout)
                    
                    async with self.session.post(
                        graphql_url,
                        json=payload,
                        headers=headers,
                        timeout=timeout
                    ) as response:
                        
                        response_headers = dict(response.headers)
                        
                        if response.status == 200:
                            response_data = await response.json()
                            
                            # Check for GraphQL errors
                            if 'errors' in response_data:
                                error_messages = [error.get('message', 'GraphQL Error') for error in response_data['errors']]
                                return ConnectorResponse(
                                    status_code=400,
                                    data=response_data,
                                    headers=response_headers,
                                    success=False,
                                    error_message='; '.join(error_messages),
                                    request_id=request.metadata.get('request_id')
                                )
                            
                            return ConnectorResponse(
                                status_code=response.status,
                                data=response_data.get('data'),
                                headers=response_headers,
                                success=True,
                                metadata={'full_response': response_data},
                                request_id=request.metadata.get('request_id')
                            )
                        else:
                            error_text = await response.text()
                            return ConnectorResponse(
                                status_code=response.status,
                                data=None,
                                headers=response_headers,
                                success=False,
                                error_message=f"HTTP {response.status}: {error_text}",
                                request_id=request.metadata.get('request_id')
                            )
                        
                except Exception as e:
                    last_exception = e
                    if attempt < self.config.retry_attempts - 1:
                        await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                        logger.warning(f"GraphQL request attempt {attempt + 1} failed, retrying: {e}")
                    else:
                        logger.error(f"All GraphQL request attempts failed: {e}")
            
            raise last_exception or Exception("GraphQL request failed after all retry attempts")
            
        except Exception as e:
            return ConnectorResponse(
                status_code=500,
                data=None,
                success=False,
                error_message=str(e),
                request_id=request.metadata.get('request_id')
            )
    
    def _prepare_graphql_payload(self, request: ConnectorRequest) -> Dict[str, Any]:
        """Prepare GraphQL request payload"""
        try:
            payload = {}
            
            # Handle different request formats
            if isinstance(request.data, str):
                # Raw GraphQL query string
                payload['query'] = request.data
            elif isinstance(request.data, dict):
                if 'query' in request.data:
                    # GraphQL payload format
                    payload = request.data.copy()
                else:
                    # Convert operation to GraphQL query
                    payload['query'] = self._build_query_from_operation(request)
                    if request.data:
                        payload['variables'] = request.data
            else:
                # Build query from operation name
                payload['query'] = self._build_query_from_operation(request)
            
            # Add operation name if specified
            operation_name = request.metadata.get('operation_name')
            if operation_name:
                payload['operationName'] = operation_name
            
            return payload
            
        except Exception as e:
            logger.error(f"GraphQL payload preparation failed: {e}")
            return {'query': str(request.data) if request.data else '{ __typename }'}
    
    def _build_query_from_operation(self, request: ConnectorRequest) -> str:
        """Build GraphQL query from operation name"""
        try:
            operation = request.operation
            operation_type = request.metadata.get('operation_type', 'query')
            
            if operation_type.lower() == 'mutation':
                return f"mutation {{ {operation} }}"
            elif operation_type.lower() == 'subscription':
                return f"subscription {{ {operation} }}"
            else:
                return f"query {{ {operation} }}"
                
        except Exception as e:
            logger.error(f"Query building failed: {e}")
            return '{ __typename }'
    
    async def _cleanup_session(self):
        """Clean up HTTP session"""
        try:
            if self.session:
                await self.session.close()
                self.session = None
                logger.debug(f"GraphQL session cleaned up for {self.config.connector_id}")
        except Exception as e:
            logger.error(f"Failed to cleanup GraphQL session: {e}")
    
    # GraphQL-specific convenience methods
    async def query(self, query: str, variables: Optional[Dict[str, Any]] = None,
                   operation_name: Optional[str] = None) -> ConnectorResponse:
        """Execute a GraphQL query"""
        payload = {'query': query}
        if variables:
            payload['variables'] = variables
        if operation_name:
            payload['operationName'] = operation_name
        
        request = ConnectorRequest(
            operation="query",
            endpoint="",
            method="POST",
            data=payload,
            metadata={'operation_type': 'query'}
        )
        return await self.execute_request(request)
    
    async def mutation(self, mutation: str, variables: Optional[Dict[str, Any]] = None,
                      operation_name: Optional[str] = None) -> ConnectorResponse:
        """Execute a GraphQL mutation"""
        payload = {'query': mutation}
        if variables:
            payload['variables'] = variables
        if operation_name:
            payload['operationName'] = operation_name
        
        request = ConnectorRequest(
            operation="mutation",
            endpoint="",
            method="POST",
            data=payload,
            metadata={'operation_type': 'mutation'}
        )
        return await self.execute_request(request)
    
    async def subscription(self, subscription: str, variables: Optional[Dict[str, Any]] = None,
                          operation_name: Optional[str] = None) -> ConnectorResponse:
        """Execute a GraphQL subscription (note: requires WebSocket support for real subscriptions)"""
        payload = {'query': subscription}
        if variables:
            payload['variables'] = variables
        if operation_name:
            payload['operationName'] = operation_name
        
        request = ConnectorRequest(
            operation="subscription",
            endpoint="",
            method="POST",
            data=payload,
            metadata={'operation_type': 'subscription'}
        )
        return await self.execute_request(request)
    
    async def introspect(self) -> ConnectorResponse:
        """Get schema introspection"""
        if self.schema:
            return ConnectorResponse(
                status_code=200,
                data={'__schema': self.schema},
                success=True
            )
        else:
            return await self.query(self.introspection_query)
    
    def get_schema_types(self) -> List[str]:
        """Get list of available types from schema"""
        if not self.schema or 'types' not in self.schema:
            return []
        
        return [type_def['name'] for type_def in self.schema['types'] if type_def.get('name')]
    
    def get_query_fields(self) -> List[str]:
        """Get list of available query fields"""
        if not self.schema:
            return []
        
        query_type_name = self.schema.get('queryType', {}).get('name')
        if not query_type_name:
            return []
        
        # Find query type in types
        for type_def in self.schema.get('types', []):
            if type_def.get('name') == query_type_name:
                fields = type_def.get('fields', [])
                return [field['name'] for field in fields if field.get('name')]
        
        return []
    
    def get_mutation_fields(self) -> List[str]:
        """Get list of available mutation fields"""
        if not self.schema:
            return []
        
        mutation_type_name = self.schema.get('mutationType', {}).get('name')
        if not mutation_type_name:
            return []
        
        # Find mutation type in types
        for type_def in self.schema.get('types', []):
            if type_def.get('name') == mutation_type_name:
                fields = type_def.get('fields', [])
                return [field['name'] for field in fields if field.get('name')]
        
        return []
    
    def validate_query(self, query: str) -> Dict[str, Any]:
        """Basic query validation (simplified)"""
        try:
            # Basic syntax checks
            if not query.strip():
                return {'valid': False, 'error': 'Empty query'}
            
            if not any(keyword in query.lower() for keyword in ['query', 'mutation', 'subscription']):
                # Might be a field selection, wrap in query
                query = f"query {{ {query} }}"
            
            # Check for balanced braces
            open_braces = query.count('{')
            close_braces = query.count('}')
            
            if open_braces != close_braces:
                return {'valid': False, 'error': 'Unbalanced braces'}
            
            return {'valid': True, 'normalized_query': query}
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    async def batch_requests(self, requests: List[Dict[str, Any]]) -> ConnectorResponse:
        """Execute multiple GraphQL requests in a batch"""
        try:
            graphql_url = urljoin(self.config.base_url, self.config.endpoints.get('graphql', '/graphql'))
            
            # Prepare batch payload
            batch_payload = []
            for req in requests:
                if isinstance(req, dict) and 'query' in req:
                    batch_payload.append(req)
                else:
                    batch_payload.append({'query': str(req)})
            
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            
            async with self.session.post(
                graphql_url,
                json=batch_payload,
                timeout=timeout
            ) as response:
                
                response_headers = dict(response.headers)
                
                if response.status == 200:
                    response_data = await response.json()
                    return ConnectorResponse(
                        status_code=response.status,
                        data=response_data,
                        headers=response_headers,
                        success=True
                    )
                else:
                    error_text = await response.text()
                    return ConnectorResponse(
                        status_code=response.status,
                        data=None,
                        headers=response_headers,
                        success=False,
                        error_message=f"Batch request failed: {error_text}"
                    )
                    
        except Exception as e:
            return ConnectorResponse(
                status_code=500,
                data=None,
                success=False,
                error_message=f"Batch request error: {e}"
            )