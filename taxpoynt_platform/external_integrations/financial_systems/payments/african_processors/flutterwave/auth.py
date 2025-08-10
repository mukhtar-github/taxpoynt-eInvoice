"""
Flutterwave Authentication Manager
=================================

Secure authentication handling for Flutterwave API integration with
comprehensive African multi-country support.

Features:
- Bearer token authentication for Flutterwave API
- Environment-specific configuration (sandbox/production)
- Multi-country API endpoint management
- Rate limiting and request throttling
- Comprehensive error handling and retry logic
- NDPR-compliant credential management
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from dataclasses import dataclass
import aiohttp
import hashlib
import hmac

from .models import FlutterwaveEnvironment, FlutterwaveCountry


@dataclass 
class FlutterwaveCredentials:
    """Flutterwave API credentials"""
    
    public_key: str
    secret_key: str
    environment: FlutterwaveEnvironment
    
    # Optional webhook credentials
    webhook_secret: Optional[str] = None
    
    # Optional encryption key for sensitive data
    encryption_key: Optional[str] = None


@dataclass
class FlutterwaveAPIEndpoints:
    """Flutterwave API endpoints by environment"""
    
    # Base URLs
    SANDBOX_BASE = "https://api.flutterwave.com/v3"
    PRODUCTION_BASE = "https://api.flutterwave.com/v3"
    
    # Payment endpoints
    CHARGE = "/payments"
    VERIFY = "/transactions/{id}/verify"
    TRANSACTIONS = "/transactions"
    
    # Customer endpoints
    CUSTOMERS = "/customers"
    
    # Bank endpoints
    BANKS = "/banks/{country}"
    
    # Mobile money endpoints
    MOBILE_MONEY_PROVIDERS = "/mobile-money/{country}"
    
    # Webhook endpoints
    WEBHOOKS = "/webhooks"
    
    # Utility endpoints
    EXCHANGE_RATES = "/exchange-rates"
    COUNTRIES = "/countries"


class FlutterwaveAuthManager:
    """
    Flutterwave authentication and API management
    
    Handles secure authentication, request signing, and API communication
    with comprehensive error handling and rate limiting.
    """
    
    def __init__(self, credentials: FlutterwaveCredentials):
        """
        Initialize Flutterwave authentication manager
        
        Args:
            credentials: FlutterwaveCredentials with API keys and settings
        """
        self.credentials = credentials
        self.logger = logging.getLogger(__name__)
        
        # API configuration
        self.base_url = (
            FlutterwaveAPIEndpoints.PRODUCTION_BASE 
            if credentials.environment == FlutterwaveEnvironment.PRODUCTION 
            else FlutterwaveAPIEndpoints.SANDBOX_BASE
        )
        
        # Rate limiting
        self.rate_limit_window = timedelta(minutes=1)
        self.max_requests_per_window = 120  # Flutterwave allows 120 req/min
        self.request_timestamps = []
        
        # Session management
        self.session: Optional[aiohttp.ClientSession] = None
        self.session_timeout = aiohttp.ClientTimeout(total=30)
        
        # Request retry configuration
        self.max_retries = 3
        self.retry_delay = 1.0
        self.backoff_multiplier = 2.0
        
        self.logger.info(f"Flutterwave auth manager initialized for {credentials.environment}")
    
    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure we have an active HTTP session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=self.session_timeout,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'TaxPoynt-Flutterwave-Connector/1.0.0'
                }
            )
        return self.session
    
    async def close_session(self):
        """Close the HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        return {
            'Authorization': f'Bearer {self.credentials.secret_key}',
            'Content-Type': 'application/json'
        }
    
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
        if len(self.request_timestamps) >= self.max_requests_per_window:
            wait_time = (self.request_timestamps[0] + self.rate_limit_window - now).total_seconds()
            self.logger.warning(f"Rate limit exceeded, waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)
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
        country: Optional[FlutterwaveCountry] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated request to Flutterwave API
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: Request payload for POST/PUT requests
            params: Query parameters
            country: Country code for country-specific endpoints
            
        Returns:
            API response data
            
        Raises:
            Exception: If request fails after retries
        """
        # Check rate limits
        await self._check_rate_limit()
        
        # Prepare URL
        if country and '{country}' in endpoint:
            endpoint = endpoint.replace('{country}', country.value)
        
        url = f"{self.base_url}{endpoint}"
        
        # Prepare headers
        headers = self._get_auth_headers()
        
        # Get session
        session = await self._ensure_session()
        
        # Retry logic
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"Making {method} request to {endpoint} (attempt {attempt + 1})")
                
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params
                ) as response:
                    
                    response_data = await response.json()
                    
                    # Log request details
                    self.logger.debug(f"Flutterwave API response: {response.status}", extra={
                        'method': method,
                        'endpoint': endpoint,
                        'status_code': response.status,
                        'response_time': response.headers.get('x-response-time'),
                        'rate_limit_remaining': response.headers.get('x-ratelimit-remaining')
                    })
                    
                    # Handle HTTP errors
                    if response.status >= 400:
                        error_msg = response_data.get('message', 'Unknown error')
                        error_code = response_data.get('code')
                        
                        if response.status == 429:  # Rate limited
                            retry_after = int(response.headers.get('retry-after', 60))
                            self.logger.warning(f"Rate limited, waiting {retry_after} seconds")
                            await asyncio.sleep(retry_after)
                            continue
                        
                        elif response.status in [500, 502, 503, 504]:  # Server errors
                            if attempt < self.max_retries - 1:
                                delay = self.retry_delay * (self.backoff_multiplier ** attempt)
                                self.logger.warning(f"Server error {response.status}, retrying in {delay} seconds")
                                await asyncio.sleep(delay)
                                continue
                        
                        # Client errors or final attempt
                        raise Exception(f"Flutterwave API error {response.status}: {error_msg} (code: {error_code})")
                    
                    # Check API response status
                    if response_data.get('status') == 'error':
                        raise Exception(f"Flutterwave API error: {response_data.get('message', 'Unknown error')}")
                    
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
                endpoint='/transactions',
                params={'limit': 1}
            )
            
            # Check if we got a valid response structure
            if 'status' in response and response['status'] == 'success':
                self.logger.info("Flutterwave credentials verified successfully")
                return True
            else:
                self.logger.error("Invalid credential verification response")
                return False
                
        except Exception as e:
            self.logger.error(f"Credential verification failed: {str(e)}")
            return False
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Verify Flutterwave webhook signature
        
        Args:
            payload: Raw webhook payload
            signature: Webhook signature from headers
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not self.credentials.webhook_secret:
            self.logger.warning("No webhook secret configured for signature verification")
            return False
        
        try:
            # Flutterwave uses SHA256 HMAC for webhook signatures
            expected_signature = hmac.new(
                self.credentials.webhook_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures securely
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            self.logger.error(f"Webhook signature verification failed: {str(e)}")
            return False
    
    async def get_supported_countries(self) -> List[Dict[str, Any]]:
        """
        Get list of countries supported by Flutterwave
        
        Returns:
            List of supported countries with their details
        """
        try:
            response = await self.make_authenticated_request(
                method='GET',
                endpoint='/countries'
            )
            
            return response.get('data', [])
            
        except Exception as e:
            self.logger.error(f"Failed to get supported countries: {str(e)}")
            return []
    
    async def get_exchange_rates(
        self,
        from_currency: str,
        to_currency: str,
        amount: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get exchange rates between currencies
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code 
            amount: Optional amount to convert
            
        Returns:
            Exchange rate data or None if failed
        """
        try:
            params = {
                'from': from_currency,
                'to': to_currency
            }
            
            if amount:
                params['amount'] = amount
            
            response = await self.make_authenticated_request(
                method='GET',
                endpoint='/exchange-rates',
                params=params
            )
            
            return response.get('data')
            
        except Exception as e:
            self.logger.error(f"Failed to get exchange rates: {str(e)}")
            return None
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get environment and configuration information"""
        return {
            'environment': self.credentials.environment.value,
            'base_url': self.base_url,
            'rate_limit_per_minute': self.max_requests_per_window,
            'webhook_configured': self.credentials.webhook_secret is not None,
            'encryption_enabled': self.credentials.encryption_key is not None
        }


__all__ = [
    'FlutterwaveCredentials',
    'FlutterwaveAPIEndpoints',
    'FlutterwaveAuthManager'
]