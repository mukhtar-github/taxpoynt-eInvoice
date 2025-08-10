"""
Stripe Authentication Manager
============================

Secure authentication handling for Stripe API integration with
comprehensive global payment support.

Features:
- Bearer token authentication for Stripe API
- Environment-specific configuration (test/live)
- Global API endpoint management
- Rate limiting and request throttling
- Comprehensive error handling and retry logic
- NDPR-compliant credential management
- Idempotency key management for safe retries
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from dataclasses import dataclass
import aiohttp
import hashlib
import hmac
import uuid

from .models import StripeEnvironment, StripeCountry


@dataclass 
class StripeCredentials:
    """Stripe API credentials"""
    
    secret_key: str
    publishable_key: str
    environment: StripeEnvironment
    
    # Optional webhook credentials
    webhook_secret: Optional[str] = None
    
    # Optional restricted API key
    restricted_key: Optional[str] = None
    
    # Account information
    account_id: Optional[str] = None


@dataclass
class StripeAPIEndpoints:
    """Stripe API endpoints"""
    
    # Base URL
    BASE = "https://api.stripe.com/v1"
    
    # Payment endpoints
    PAYMENT_INTENTS = "/payment_intents"
    CHARGES = "/charges"
    PAYMENT_METHODS = "/payment_methods"
    SETUP_INTENTS = "/setup_intents"
    
    # Customer endpoints
    CUSTOMERS = "/customers"
    
    # Subscription endpoints
    SUBSCRIPTIONS = "/subscriptions"
    INVOICES = "/invoices"
    PRODUCTS = "/products"
    PRICES = "/prices"
    
    # Financial endpoints
    TRANSFERS = "/transfers"
    PAYOUTS = "/payouts"
    BALANCE = "/balance"
    
    # Marketplace endpoints
    ACCOUNTS = "/accounts"
    ACCOUNT_LINKS = "/account_links"
    
    # Dispute endpoints
    DISPUTES = "/disputes"
    
    # Webhook endpoints
    WEBHOOK_ENDPOINTS = "/webhook_endpoints"
    
    # Utility endpoints
    COUNTRY_SPECS = "/country_specs"
    EXCHANGE_RATES = "/exchange_rates"


class StripeAuthManager:
    """
    Stripe authentication and API management
    
    Handles secure authentication, request signing, and API communication
    with comprehensive error handling and rate limiting.
    """
    
    def __init__(self, credentials: StripeCredentials):
        """
        Initialize Stripe authentication manager
        
        Args:
            credentials: StripeCredentials with API keys and settings
        """
        self.credentials = credentials
        self.logger = logging.getLogger(__name__)
        
        # API configuration
        self.base_url = StripeAPIEndpoints.BASE
        
        # Rate limiting - Stripe has generous limits but we want to be conservative
        self.rate_limit_window = timedelta(seconds=1)
        self.max_requests_per_second = 25  # Conservative limit
        self.request_timestamps = []
        
        # Session management
        self.session: Optional[aiohttp.ClientSession] = None
        self.session_timeout = aiohttp.ClientTimeout(total=80)  # Stripe recommends 80s
        
        # Request retry configuration
        self.max_retries = 3
        self.retry_delay = 1.0
        self.backoff_multiplier = 2.0
        
        # Idempotency management
        self.idempotency_keys = set()
        
        self.logger.info(f"Stripe auth manager initialized for {credentials.environment}")
    
    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure we have an active HTTP session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=self.session_timeout,
                headers={
                    'User-Agent': 'TaxPoynt-Stripe-Connector/1.0.0'
                }
            )
        return self.session
    
    async def close_session(self):
        """Close the HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
    
    def _get_auth_headers(self, idempotency_key: Optional[str] = None) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        headers = {
            'Authorization': f'Bearer {self.credentials.secret_key}',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Stripe-Version': '2023-10-16'  # Pin to specific API version
        }
        
        if idempotency_key:
            headers['Idempotency-Key'] = idempotency_key
        
        if self.credentials.account_id:
            headers['Stripe-Account'] = self.credentials.account_id
        
        return headers
    
    def _generate_idempotency_key(self, operation: str, data: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate unique idempotency key for safe retries
        
        Args:
            operation: Type of operation (create_payment_intent, etc.)
            data: Request data to include in key generation
            
        Returns:
            Unique idempotency key
        """
        # Create deterministic key based on operation and data
        key_data = f"{operation}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        if data:
            # Include relevant data fields for deterministic key
            relevant_fields = ['amount', 'currency', 'customer', 'payment_method']
            data_str = '_'.join([f"{k}:{v}" for k, v in data.items() if k in relevant_fields])
            if data_str:
                key_data += f"_{data_str}"
        
        # Generate hash
        key = hashlib.sha256(key_data.encode()).hexdigest()[:32]
        
        # Ensure uniqueness
        while key in self.idempotency_keys:
            key = hashlib.sha256(f"{key}_{uuid.uuid4().hex[:4]}".encode()).hexdigest()[:32]
        
        self.idempotency_keys.add(key)
        return key
    
    async def _check_rate_limit(self) -> bool:
        """
        Check if we're within rate limits
        
        Returns:
            True if request can proceed, False if rate limited
        """
        now = datetime.utcnow()
        
        # Remove old timestamps outside the window
        cutoff = now - self.rate_limit_window
        self.request_timestamps = [
            ts for ts in self.request_timestamps if ts > cutoff
        ]
        
        # Check if we can make another request
        if len(self.request_timestamps) >= self.max_requests_per_second:
            wait_time = (self.request_timestamps[0] + self.rate_limit_window - now).total_seconds()
            self.logger.warning(f"Rate limit approached, waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time + 0.1)  # Small buffer
            return False
        
        # Record this request
        self.request_timestamps.append(now)
        return True
    
    async def make_authenticated_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        idempotent: bool = False,
        operation_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated request to Stripe API
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: Request payload for POST/PUT requests
            params: Query parameters
            idempotent: Whether to use idempotency key
            operation_name: Name for idempotency key generation
            
        Returns:
            API response data
            
        Raises:
            Exception: If request fails after retries
        """
        # Check rate limits
        await self._check_rate_limit()
        
        # Prepare URL
        url = f"{self.base_url}{endpoint}"
        
        # Generate idempotency key if requested
        idempotency_key = None
        if idempotent and method.upper() in ['POST', 'PUT']:
            idempotency_key = self._generate_idempotency_key(
                operation_name or endpoint.replace('/', '_'),
                data
            )
        
        # Prepare headers
        headers = self._get_auth_headers(idempotency_key)
        
        # Get session
        session = await self._ensure_session()
        
        # Prepare data - Stripe uses form encoding
        form_data = None
        if data and method.upper() in ['POST', 'PUT']:
            form_data = aiohttp.FormData()
            self._flatten_data(data, form_data)
        
        # Retry logic
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"Making {method} request to {endpoint} (attempt {attempt + 1})")
                
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    data=form_data,
                    params=params
                ) as response:
                    
                    response_text = await response.text()
                    
                    # Log request details
                    self.logger.debug(f"Stripe API response: {response.status}", extra={
                        'method': method,
                        'endpoint': endpoint,
                        'status_code': response.status,
                        'request_id': response.headers.get('request-id')
                    })
                    
                    # Parse response
                    try:
                        response_data = await response.json()
                    except:
                        response_data = {'raw_response': response_text}
                    
                    # Handle HTTP errors
                    if response.status >= 400:
                        error_info = response_data.get('error', {})
                        error_type = error_info.get('type', 'api_error')
                        error_code = error_info.get('code')
                        error_message = error_info.get('message', 'Unknown error')
                        
                        if response.status == 429:  # Rate limited
                            retry_after = int(response.headers.get('retry-after', 1))
                            self.logger.warning(f"Rate limited, waiting {retry_after} seconds")
                            await asyncio.sleep(retry_after)
                            continue
                        
                        elif error_type in ['api_connection_error', 'api_error'] and response.status >= 500:
                            # Server errors - retry
                            if attempt < self.max_retries - 1:
                                delay = self.retry_delay * (self.backoff_multiplier ** attempt)
                                self.logger.warning(f"Server error {response.status}, retrying in {delay} seconds")
                                await asyncio.sleep(delay)
                                continue
                        
                        # Client errors or final attempt
                        raise Exception(f"Stripe API error {response.status}: {error_message} (type: {error_type}, code: {error_code})")
                    
                    return response_data
                    
            except asyncio.TimeoutError as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (self.backoff_multiplier ** attempt)
                    self.logger.warning(f"Request timeout, retrying in {delay} seconds")
                    await asyncio.sleep(delay)
                continue
                
            except aiohttp.ClientError as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (self.backoff_multiplier ** attempt)
                    self.logger.warning(f"Client error {str(e)}, retrying in {delay} seconds")
                    await asyncio.sleep(delay)
                continue
                
            except Exception as e:
                # Don't retry for other exceptions
                self.logger.error(f"Request failed: {str(e)}")
                raise
        
        # All retries exhausted
        raise Exception(f"Request failed after {self.max_retries} attempts: {str(last_exception)}")
    
    def _flatten_data(self, data: Dict[str, Any], form_data: aiohttp.FormData, prefix: str = '') -> None:
        """
        Flatten nested data for Stripe's form encoding format
        
        Args:
            data: Data to flatten
            form_data: FormData object to populate
            prefix: Current prefix for nested keys
        """
        for key, value in data.items():
            full_key = f"{prefix}[{key}]" if prefix else key
            
            if isinstance(value, dict):
                self._flatten_data(value, form_data, full_key)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        self._flatten_data(item, form_data, f"{full_key}[{i}]")
                    else:
                        form_data.add_field(f"{full_key}[{i}]", str(item))
            elif value is not None:
                form_data.add_field(full_key, str(value))
    
    async def verify_credentials(self) -> bool:
        """
        Verify API credentials by making a test request
        
        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            # Test with a simple API call
            response = await self.make_authenticated_request(
                method='GET',
                endpoint='/charges',
                params={'limit': 1}
            )
            
            # Check if we got a valid response structure
            if 'object' in response and response['object'] == 'list':
                self.logger.info("Stripe credentials verified successfully")
                return True
            else:
                self.logger.error("Invalid credential verification response")
                return False
                
        except Exception as e:
            self.logger.error(f"Credential verification failed: {str(e)}")
            return False
    
    def verify_webhook_signature(self, payload: str, signature: str, timestamp: str) -> bool:
        """
        Verify Stripe webhook signature
        
        Args:
            payload: Raw webhook payload
            signature: Webhook signature from headers
            timestamp: Timestamp from headers
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not self.credentials.webhook_secret:
            self.logger.warning("No webhook secret configured for signature verification")
            return False
        
        try:
            # Stripe webhook signature verification
            signed_payload = f"{timestamp}.{payload}"
            expected_signature = hmac.new(
                self.credentials.webhook_secret.encode('utf-8'),
                signed_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Stripe sends signature as "t=timestamp,v1=signature"
            signatures = {}
            for part in signature.split(','):
                key, value = part.split('=', 1)
                signatures[key] = value
            
            if 'v1' not in signatures:
                return False
            
            # Compare signatures securely
            return hmac.compare_digest(expected_signature, signatures['v1'])
            
        except Exception as e:
            self.logger.error(f"Webhook signature verification failed: {str(e)}")
            return False
    
    async def get_account_info(self) -> Optional[Dict[str, Any]]:
        """
        Get account information
        
        Returns:
            Account data or None if failed
        """
        try:
            response = await self.make_authenticated_request(
                method='GET',
                endpoint='/account'
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to get account info: {str(e)}")
            return None
    
    async def get_country_specs(self, country: Optional[StripeCountry] = None) -> List[Dict[str, Any]]:
        """
        Get country specifications
        
        Args:
            country: Specific country to get specs for
            
        Returns:
            List of country specifications
        """
        try:
            endpoint = '/country_specs'
            if country:
                endpoint += f'/{country.value}'
            
            response = await self.make_authenticated_request(
                method='GET',
                endpoint=endpoint
            )
            
            if country:
                return [response]
            else:
                return response.get('data', [])
            
        except Exception as e:
            self.logger.error(f"Failed to get country specs: {str(e)}")
            return []
    
    async def get_exchange_rates(self, currency: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get current exchange rates
        
        Args:
            currency: Base currency for rates
            
        Returns:
            Exchange rate data or None if failed
        """
        try:
            endpoint = '/exchange_rates'
            if currency:
                endpoint += f'/{currency.lower()}'
            
            response = await self.make_authenticated_request(
                method='GET',
                endpoint=endpoint
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to get exchange rates: {str(e)}")
            return None
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get environment and configuration information"""
        return {
            'environment': self.credentials.environment.value,
            'base_url': self.base_url,
            'rate_limit_per_second': self.max_requests_per_second,
            'webhook_configured': self.credentials.webhook_secret is not None,
            'account_id': self.credentials.account_id,
            'restricted_key_used': self.credentials.restricted_key is not None
        }
    
    def cleanup_idempotency_keys(self, older_than_hours: int = 24):
        """Clean up old idempotency keys to prevent memory buildup"""
        # For production, this would be implemented with proper storage
        # For now, we just clear if we have too many
        if len(self.idempotency_keys) > 10000:
            # Keep only recent keys (simplified approach)
            self.idempotency_keys = set(list(self.idempotency_keys)[-5000:])
            self.logger.info("Cleaned up old idempotency keys")


__all__ = [
    'StripeCredentials',
    'StripeAPIEndpoints',
    'StripeAuthManager'
]