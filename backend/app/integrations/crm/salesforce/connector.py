"""
Salesforce CRM Connector Implementation.

This module provides integration with Salesforce CRM system, including:
- OAuth 2.0 JWT Bearer Token authentication
- Opportunity management and synchronization
- Deal to invoice transformation
- Webhook handling for real-time updates
"""

import logging
import json
import time
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from urllib.parse import urlencode, quote

import httpx
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.integrations.base.connector import BaseConnector, IntegrationTestResult
from app.integrations.base.auth import SecureCredentialManager
from app.integrations.base.errors import (
    IntegrationError,
    AuthenticationError,
    ConnectionError,
    RateLimitError
)

logger = logging.getLogger(__name__)


class SalesforceConnector(BaseConnector):
    """Salesforce CRM connector with JWT Bearer authentication."""
    
    def __init__(self, connection_config: Dict[str, Any]):
        """
        Initialize Salesforce connector.
        
        Args:
            connection_config: Connection configuration containing:
                - client_id: Salesforce Connected App Consumer Key
                - private_key: Private key for JWT signing (PEM format)
                - username: Salesforce username
                - instance_url: Salesforce instance URL (optional)
                - sandbox: Whether to use sandbox environment (default: False)
        """
        super().__init__(connection_config)
        
        # Salesforce-specific configuration
        self.client_id = connection_config.get("client_id")
        self.private_key = connection_config.get("private_key")
        self.username = connection_config.get("username")
        self.sandbox = connection_config.get("sandbox", False)
        
        # API endpoints
        self.login_url = "https://test.salesforce.com" if self.sandbox else "https://login.salesforce.com"
        self.token_url = f"{self.login_url}/services/oauth2/token"
        self.instance_url = connection_config.get("instance_url")
        
        # Authentication state
        self.access_token = None
        self.token_expiry = None
        
        # Credential manager for secure storage
        self.credential_manager = SecureCredentialManager()
        
        # API version
        self.api_version = "v58.0"
        
        # Validate required configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate required configuration parameters."""
        if not self.client_id:
            raise ValueError("client_id is required for Salesforce integration")
        if not self.private_key:
            raise ValueError("private_key is required for JWT authentication")
        if not self.username:
            raise ValueError("username is required for Salesforce integration")
    
    def _create_jwt_assertion(self) -> str:
        """
        Create JWT assertion for JWT Bearer authentication.
        
        Returns:
            str: JWT assertion token
        """
        try:
            # Load private key
            if isinstance(self.private_key, str):
                if self.private_key.startswith("-----BEGIN"):
                    # PEM format
                    private_key_obj = serialization.load_pem_private_key(
                        self.private_key.encode(),
                        password=None
                    )
                else:
                    # Base64 encoded
                    private_key_bytes = base64.b64decode(self.private_key)
                    private_key_obj = serialization.load_pem_private_key(
                        private_key_bytes,
                        password=None
                    )
            else:
                private_key_obj = self.private_key
            
            # JWT payload
            now = int(time.time())
            payload = {
                "iss": self.client_id,  # Issuer (Consumer Key)
                "sub": self.username,   # Subject (Username)
                "aud": self.login_url,  # Audience (Login URL)
                "exp": now + 300,       # Expiration (5 minutes)
                "iat": now,             # Issued at
                "jti": f"{self.client_id}_{now}"  # Unique identifier
            }
            
            # Create JWT token
            token = jwt.encode(
                payload,
                private_key_obj,
                algorithm="RS256"
            )
            
            return token
            
        except Exception as e:
            logger.error(f"Failed to create JWT assertion: {str(e)}")
            raise AuthenticationError(f"JWT creation failed: {str(e)}")
    
    async def authenticate(self) -> Dict[str, Any]:
        """
        Authenticate with Salesforce using JWT Bearer token flow.
        
        Returns:
            Dict containing authentication results
        """
        try:
            # Create JWT assertion
            jwt_assertion = self._create_jwt_assertion()
            
            # Token request data
            data = {
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": jwt_assertion
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            }
            
            # Make token request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_url,
                    data=data,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    error_data = {}
                    try:
                        error_data = response.json()
                    except:
                        pass
                    
                    error_msg = error_data.get("error_description", response.text)
                    logger.error(f"Salesforce authentication failed: {error_msg}")
                    raise AuthenticationError(f"Authentication failed: {error_msg}")
                
                token_data = response.json()
            
            # Store authentication data
            self.access_token = token_data["access_token"]
            self.instance_url = token_data["instance_url"]
            
            # Calculate token expiry (Salesforce tokens typically last 1-2 hours)
            # We'll assume 1 hour and refresh proactively
            self.token_expiry = datetime.now() + timedelta(hours=1)
            
            self._authenticated = True
            self._last_auth_time = datetime.now()
            
            logger.info(f"Successfully authenticated with Salesforce: {self.instance_url}")
            
            return {
                "success": True,
                "access_token": self.access_token,
                "instance_url": self.instance_url,
                "token_type": token_data.get("token_type", "Bearer"),
                "expires_at": self.token_expiry.isoformat()
            }
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Salesforce authentication error: {str(e)}")
            raise AuthenticationError(f"Authentication failed: {str(e)}")
    
    async def _ensure_authenticated(self):
        """Ensure we have a valid authentication token."""
        if not self.access_token or not self.token_expiry:
            await self.authenticate()
        elif datetime.now() >= self.token_expiry - timedelta(minutes=5):
            # Refresh token if expiring within 5 minutes
            logger.info("Token expiring soon, re-authenticating")
            await self.authenticate()
    
    async def _make_api_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated API request to Salesforce.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (relative to instance URL)
            data: Request body data
            params: Query parameters
            
        Returns:
            Dict containing API response
        """
        await self._ensure_authenticated()
        
        url = f"{self.instance_url}/services/data/{self.api_version}/{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                if method.upper() == "GET":
                    response = await client.get(url, params=params, headers=headers, timeout=30.0)
                elif method.upper() == "POST":
                    response = await client.post(url, json=data, params=params, headers=headers, timeout=30.0)
                elif method.upper() == "PATCH":
                    response = await client.patch(url, json=data, params=params, headers=headers, timeout=30.0)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, params=params, headers=headers, timeout=30.0)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                # Handle rate limiting
                if response.status_code == 429:
                    raise RateLimitError("Salesforce API rate limit exceeded")
                
                # Handle authentication errors
                if response.status_code == 401:
                    # Token might be expired, try to re-authenticate
                    await self.authenticate()
                    # Retry the request once
                    headers["Authorization"] = f"Bearer {self.access_token}"
                    if method.upper() == "GET":
                        response = await client.get(url, params=params, headers=headers, timeout=30.0)
                    elif method.upper() == "POST":
                        response = await client.post(url, json=data, params=params, headers=headers, timeout=30.0)
                    elif method.upper() == "PATCH":
                        response = await client.patch(url, json=data, params=params, headers=headers, timeout=30.0)
                    elif method.upper() == "DELETE":
                        response = await client.delete(url, params=params, headers=headers, timeout=30.0)
                
                if not response.is_success:
                    error_msg = f"API request failed: {response.status_code}"
                    try:
                        error_data = response.json()
                        if isinstance(error_data, list) and len(error_data) > 0:
                            error_msg = error_data[0].get("message", error_msg)
                        elif isinstance(error_data, dict):
                            error_msg = error_data.get("message", error_msg)
                    except:
                        error_msg = response.text
                    
                    logger.error(f"Salesforce API error: {error_msg}")
                    raise ConnectionError(f"API request failed: {error_msg}")
                
                # Handle empty responses
                if not response.content:
                    return {}
                
                return response.json()
                
        except httpx.RequestError as e:
            logger.error(f"HTTP request error: {str(e)}")
            raise ConnectionError(f"Request failed: {str(e)}")
    
    async def test_connection(self) -> IntegrationTestResult:
        """
        Test connection to Salesforce.
        
        Returns:
            IntegrationTestResult with test results
        """
        try:
            # Authenticate
            auth_result = await self.authenticate()
            
            # Test basic API access by getting organization info
            org_info = await self._make_api_request("GET", "sobjects/Organization/describe")
            
            # Test opportunities access
            opportunities_info = await self._make_api_request("GET", "sobjects/Opportunity/describe")
            
            return IntegrationTestResult(
                success=True,
                message="Salesforce connection successful",
                details={
                    "instance_url": self.instance_url,
                    "api_version": self.api_version,
                    "organization_accessible": bool(org_info),
                    "opportunities_accessible": bool(opportunities_info),
                    "sandbox": self.sandbox,
                    "authenticated_at": self._last_auth_time.isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Salesforce connection test failed: {str(e)}")
            return IntegrationTestResult(
                success=False,
                message=f"Connection test failed: {str(e)}",
                details={
                    "error_type": e.__class__.__name__,
                    "sandbox": self.sandbox,
                    "login_url": self.login_url
                }
            )
    
    async def get_opportunities(
        self,
        limit: int = 100,
        offset: int = 0,
        modified_since: Optional[datetime] = None,
        stage_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Retrieve opportunities from Salesforce.
        
        Args:
            limit: Maximum number of opportunities to retrieve
            offset: Number of records to skip
            modified_since: Only return opportunities modified since this date
            stage_names: Filter by specific stage names
            
        Returns:
            Dict containing opportunities data
        """
        try:
            # Build SOQL query
            select_fields = [
                "Id", "Name", "Amount", "CloseDate", "StageName", "Probability",
                "Type", "LeadSource", "Description", "CreatedDate", "LastModifiedDate",
                "Account.Name", "Account.Id", "Account.BillingStreet", "Account.BillingCity",
                "Account.BillingState", "Account.BillingCountry", "Account.BillingPostalCode",
                "Account.Phone", "Account.Website", "Owner.Name", "Owner.Email"
            ]
            
            query = f"SELECT {', '.join(select_fields)} FROM Opportunity"
            
            where_conditions = []
            
            # Add date filter
            if modified_since:
                date_str = modified_since.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                where_conditions.append(f"LastModifiedDate >= {date_str}")
            
            # Add stage filter
            if stage_names:
                quoted_stages = [f"'{stage}'" for stage in stage_names]
                where_conditions.append(f"StageName IN ({', '.join(quoted_stages)})")
            
            if where_conditions:
                query += f" WHERE {' AND '.join(where_conditions)}"
            
            query += f" ORDER BY LastModifiedDate DESC LIMIT {limit}"
            
            if offset > 0:
                query += f" OFFSET {offset}"
            
            # Execute query
            params = {"q": query}
            result = await self._make_api_request("GET", "query", params=params)
            
            return {
                "opportunities": result.get("records", []),
                "total_size": result.get("totalSize", 0),
                "done": result.get("done", True),
                "next_records_url": result.get("nextRecordsUrl")
            }
            
        except Exception as e:
            logger.error(f"Failed to retrieve opportunities: {str(e)}")
            raise IntegrationError(f"Failed to retrieve opportunities: {str(e)}")
    
    async def get_opportunity_by_id(self, opportunity_id: str) -> Dict[str, Any]:
        """
        Get a specific opportunity by ID.
        
        Args:
            opportunity_id: Salesforce opportunity ID
            
        Returns:
            Dict containing opportunity data
        """
        try:
            # Build SOQL query for single opportunity
            select_fields = [
                "Id", "Name", "Amount", "CloseDate", "StageName", "Probability",
                "Type", "LeadSource", "Description", "CreatedDate", "LastModifiedDate",
                "Account.Name", "Account.Id", "Account.BillingStreet", "Account.BillingCity",
                "Account.BillingState", "Account.BillingCountry", "Account.BillingPostalCode",
                "Account.Phone", "Account.Website", "Owner.Name", "Owner.Email"
            ]
            
            query = f"SELECT {', '.join(select_fields)} FROM Opportunity WHERE Id = '{opportunity_id}'"
            
            params = {"q": query}
            result = await self._make_api_request("GET", "query", params=params)
            
            records = result.get("records", [])
            if not records:
                raise IntegrationError(f"Opportunity {opportunity_id} not found")
            
            return records[0]
            
        except Exception as e:
            logger.error(f"Failed to retrieve opportunity {opportunity_id}: {str(e)}")
            raise IntegrationError(f"Failed to retrieve opportunity: {str(e)}")
    
    def transform_opportunity_to_deal(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Salesforce opportunity to TaxPoynt deal format.
        
        Args:
            opportunity: Salesforce opportunity data
            
        Returns:
            Dict in TaxPoynt deal format
        """
        try:
            account = opportunity.get("Account", {}) or {}
            owner = opportunity.get("Owner", {}) or {}
            
            # Extract customer data
            customer_data = {
                "name": account.get("Name", ""),
                "email": "",  # Salesforce doesn't store email on Account by default
                "phone": account.get("Phone", ""),
                "company": account.get("Name", ""),
                "address": {
                    "street": account.get("BillingStreet", ""),
                    "city": account.get("BillingCity", ""),
                    "state": account.get("BillingState", ""),
                    "country": account.get("BillingCountry", ""),
                    "postal_code": account.get("BillingPostalCode", "")
                }
            }
            
            # Extract deal data
            deal_data = {
                "source": opportunity.get("LeadSource", ""),
                "owner": {
                    "name": owner.get("Name", ""),
                    "email": owner.get("Email", "")
                },
                "type": opportunity.get("Type", ""),
                "probability": opportunity.get("Probability", 0),
                "expected_close_date": opportunity.get("CloseDate"),
                "description": opportunity.get("Description", ""),
                "salesforce_id": opportunity.get("Id", "")
            }
            
            # Format amount
            amount = opportunity.get("Amount", 0)
            if amount is None:
                amount = 0
            
            # Create deal object
            deal = {
                "external_deal_id": opportunity.get("Id", ""),
                "deal_title": opportunity.get("Name", ""),
                "deal_amount": str(amount),
                "deal_currency": "USD",  # Default currency, can be configured
                "deal_stage": opportunity.get("StageName", ""),
                "deal_probability": opportunity.get("Probability", 0),
                "customer_data": customer_data,
                "deal_data": deal_data,
                "created_at_source": opportunity.get("CreatedDate"),
                "updated_at_source": opportunity.get("LastModifiedDate"),
                "invoice_generated": False
            }
            
            return deal
            
        except Exception as e:
            logger.error(f"Failed to transform opportunity to deal: {str(e)}")
            raise IntegrationError(f"Deal transformation failed: {str(e)}")
    
    async def sync_opportunities(
        self,
        limit: int = 100,
        modified_since: Optional[datetime] = None,
        stage_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Sync opportunities from Salesforce.
        
        Args:
            limit: Maximum number of opportunities to sync
            modified_since: Only sync opportunities modified since this date
            stage_names: Filter by specific stage names
            
        Returns:
            Dict containing sync results
        """
        try:
            # Get opportunities from Salesforce
            opportunities_result = await self.get_opportunities(
                limit=limit,
                modified_since=modified_since,
                stage_names=stage_names
            )
            
            opportunities = opportunities_result.get("opportunities", [])
            
            # Transform opportunities to deals
            deals = []
            for opportunity in opportunities:
                try:
                    deal = self.transform_opportunity_to_deal(opportunity)
                    deals.append(deal)
                except Exception as e:
                    logger.warning(f"Failed to transform opportunity {opportunity.get('Id')}: {str(e)}")
            
            return {
                "success": True,
                "deals_synced": len(deals),
                "deals": deals,
                "total_opportunities": opportunities_result.get("total_size", 0),
                "has_more": not opportunities_result.get("done", True),
                "sync_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Opportunity sync failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "deals_synced": 0,
                "deals": [],
                "sync_timestamp": datetime.now().isoformat()
            }
    
    async def create_webhook_subscription(self, webhook_url: str, events: List[str]) -> Dict[str, Any]:
        """
        Create webhook subscription for Salesforce Platform Events.
        
        Note: This requires Salesforce Platform Events or Change Data Capture setup.
        
        Args:
            webhook_url: URL to receive webhook notifications
            events: List of events to subscribe to
            
        Returns:
            Dict containing subscription details
        """
        # Salesforce uses Platform Events and Change Data Capture for real-time updates
        # This would require additional setup in Salesforce org
        
        logger.info("Salesforce webhook subscription requires Platform Events setup in Salesforce org")
        
        return {
            "success": False,
            "message": "Salesforce webhook subscription requires Platform Events configuration in Salesforce org",
            "webhook_url": webhook_url,
            "events": events
        }
    
    def get_connector_info(self) -> Dict[str, Any]:
        """
        Get connector information.
        
        Returns:
            Dict with connector details
        """
        base_info = super().get_connector_info()
        base_info.update({
            "platform": "salesforce",
            "api_version": self.api_version,
            "sandbox": self.sandbox,
            "instance_url": self.instance_url,
            "login_url": self.login_url,
            "capabilities": [
                "opportunities",
                "accounts",
                "jwt_authentication",
                "soql_queries"
            ]
        })
        return base_info