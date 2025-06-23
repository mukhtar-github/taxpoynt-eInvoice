"""Square OAuth authentication flow implementation."""

import secrets
import hashlib
import base64
from urllib.parse import urlencode, parse_qs
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from square.client import Client
from square.models import ObtainTokenRequest, RenewTokenRequest
from square.exceptions import ApiException
from fastapi import HTTPException

import logging

logger = logging.getLogger(__name__)


class SquareOAuthFlow:
    """Handles Square OAuth 2.0 authentication flow."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Square OAuth flow.
        
        Args:
            config: Dictionary containing OAuth configuration
                - client_id: Square application ID
                - client_secret: Square application secret
                - redirect_uri: OAuth redirect URI
                - environment: 'sandbox' or 'production'
                - scopes: List of requested scopes
        """
        self.client_id = config.get("client_id")
        self.client_secret = config.get("client_secret")
        self.redirect_uri = config.get("redirect_uri")
        self.environment = config.get("environment", "sandbox")
        self.scopes = config.get("scopes", ["PAYMENTS_READ", "ORDERS_READ"])
        
        # Initialize Square OAuth client
        self.client = Client(environment=self.environment)
        self.oauth_api = self.client.o_auth
        
        # OAuth endpoints
        if self.environment == "production":
            self.authorize_url = "https://connect.squareup.com/oauth2/authorize"
        else:
            self.authorize_url = "https://connect.squareupsandbox.com/oauth2/authorize"
    
    def generate_authorization_url(self, state: Optional[str] = None) -> Dict[str, str]:
        """
        Generate Square OAuth authorization URL.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Dict containing authorization URL and state
        """
        try:
            # Generate state for CSRF protection if not provided
            if not state:
                state = secrets.token_urlsafe(32)
            
            # Prepare authorization parameters
            auth_params = {
                "client_id": self.client_id,
                "scope": " ".join(self.scopes),
                "session": "false",  # For server-to-server flow
                "state": state
            }
            
            # Add redirect URI if provided
            if self.redirect_uri:
                auth_params["redirect_uri"] = self.redirect_uri
            
            # Build authorization URL
            authorization_url = f"{self.authorize_url}?{urlencode(auth_params)}"
            
            logger.info(f"Generated Square OAuth authorization URL for client {self.client_id}")
            
            return {
                "authorization_url": authorization_url,
                "state": state
            }
            
        except Exception as e:
            logger.error(f"Error generating Square OAuth authorization URL: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"OAuth URL generation failed: {str(e)}")
    
    async def exchange_authorization_code(self, authorization_code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.
        
        Args:
            authorization_code: Authorization code from Square OAuth callback
            
        Returns:
            Dict containing access token and token information
        """
        try:
            # Create token request
            token_request = ObtainTokenRequest(
                client_id=self.client_id,
                client_secret=self.client_secret,
                code=authorization_code,
                grant_type="authorization_code"
            )
            
            # Add redirect URI if provided
            if self.redirect_uri:
                token_request.redirect_uri = self.redirect_uri
            
            # Exchange authorization code for token
            result = self.oauth_api.obtain_token(body=token_request)
            
            if result.is_success():
                token_data = result.body
                
                # Calculate token expiration
                expires_in = token_data.get("expires_at")
                if expires_in:
                    expires_at = datetime.fromisoformat(expires_in.replace('Z', '+00:00'))
                else:
                    # Default to 30 days if not provided
                    expires_at = datetime.now() + timedelta(days=30)
                
                token_info = {
                    "access_token": token_data.get("access_token"),
                    "refresh_token": token_data.get("refresh_token"),
                    "token_type": token_data.get("token_type", "Bearer"),
                    "expires_at": expires_at.isoformat(),
                    "merchant_id": token_data.get("merchant_id"),
                    "scopes": self.scopes,
                    "environment": self.environment
                }
                
                logger.info(f"Successfully obtained Square access token for merchant {token_info['merchant_id']}")
                return token_info
                
            else:
                errors = result.errors
                error_msg = f"Token exchange failed: {[error['detail'] for error in errors]}"
                logger.error(error_msg)
                raise HTTPException(status_code=400, detail=error_msg)
                
        except ApiException as e:
            logger.error(f"Square API error during token exchange: {str(e)}", exc_info=True)
            raise HTTPException(status_code=400, detail=f"Square OAuth error: {str(e)}")
        except Exception as e:
            logger.error(f"Error exchanging Square authorization code: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Token exchange failed: {str(e)}")
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh Square access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            Dict containing new access token and token information
        """
        try:
            # Create refresh token request
            refresh_request = RenewTokenRequest(
                access_token=refresh_token
            )
            
            # Refresh the token
            result = self.oauth_api.renew_token(
                client_id=self.client_id,
                body=refresh_request,
                authorization=f"Client {self.client_secret}"
            )
            
            if result.is_success():
                token_data = result.body
                
                # Calculate token expiration
                expires_in = token_data.get("expires_at")
                if expires_in:
                    expires_at = datetime.fromisoformat(expires_in.replace('Z', '+00:00'))
                else:
                    expires_at = datetime.now() + timedelta(days=30)
                
                token_info = {
                    "access_token": token_data.get("access_token"),
                    "token_type": token_data.get("token_type", "Bearer"),
                    "expires_at": expires_at.isoformat(),
                    "merchant_id": token_data.get("merchant_id"),
                    "environment": self.environment
                }
                
                logger.info(f"Successfully refreshed Square access token for merchant {token_info['merchant_id']}")
                return token_info
                
            else:
                errors = result.errors
                error_msg = f"Token refresh failed: {[error['detail'] for error in errors]}"
                logger.error(error_msg)
                raise HTTPException(status_code=400, detail=error_msg)
                
        except ApiException as e:
            logger.error(f"Square API error during token refresh: {str(e)}", exc_info=True)
            raise HTTPException(status_code=400, detail=f"Square OAuth refresh error: {str(e)}")
        except Exception as e:
            logger.error(f"Error refreshing Square access token: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Token refresh failed: {str(e)}")
    
    async def revoke_access_token(self, access_token: str) -> bool:
        """
        Revoke Square access token.
        
        Args:
            access_token: Access token to revoke
            
        Returns:
            bool: True if successful
        """
        try:
            # Square OAuth API doesn't have explicit revoke endpoint
            # Token revocation is handled by expiration or merchant action
            # This is a placeholder for future implementation
            
            logger.info("Square access token marked for revocation")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking Square access token: {str(e)}", exc_info=True)
            return False
    
    def validate_token_expiration(self, expires_at: str) -> bool:
        """
        Check if access token is still valid.
        
        Args:
            expires_at: Token expiration timestamp
            
        Returns:
            bool: True if token is still valid
        """
        try:
            expiration_time = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            current_time = datetime.now()
            
            # Add 5-minute buffer before expiration
            buffer_time = timedelta(minutes=5)
            
            return current_time < (expiration_time - buffer_time)
            
        except Exception as e:
            logger.error(f"Error validating token expiration: {str(e)}")
            return False
    
    def get_required_scopes(self) -> List[str]:
        """
        Get the list of required OAuth scopes for POS integration.
        
        Returns:
            List of required scope strings
        """
        return [
            "PAYMENTS_READ",           # Read payment information
            "PAYMENTS_WRITE",          # Create payments (if needed)
            "ORDERS_READ",             # Read order information
            "ORDERS_WRITE",            # Create/update orders (if needed)
            "CUSTOMERS_READ",          # Read customer information
            "INVENTORY_READ",          # Read inventory information
            "MERCHANT_PROFILE_READ",   # Read merchant profile
            "ITEMS_READ",              # Read catalog items
            "WEBHOOK_SUBSCRIPTION_MANAGEMENT"  # Manage webhook subscriptions
        ]
    
    def validate_webhook_notification_url(self, url: str) -> bool:
        """
        Validate webhook notification URL format.
        
        Args:
            url: Webhook notification URL
            
        Returns:
            bool: True if URL is valid
        """
        try:
            # Square webhook URLs must be HTTPS
            if not url.startswith("https://"):
                return False
            
            # URL should be accessible from Square's servers
            # Additional validation could be added here
            
            return True
            
        except Exception:
            return False


class SquareOAuthManager:
    """Manager class for Square OAuth operations."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize OAuth manager with configuration."""
        self.oauth_flow = SquareOAuthFlow(config)
        self._stored_states = {}  # In production, use Redis or database
    
    async def initiate_oauth_flow(self, user_id: str) -> Dict[str, str]:
        """
        Initiate OAuth flow for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict containing authorization URL and state
        """
        auth_data = self.oauth_flow.generate_authorization_url()
        
        # Store state for validation (use proper storage in production)
        self._stored_states[auth_data["state"]] = {
            "user_id": user_id,
            "created_at": datetime.now(),
            "used": False
        }
        
        return auth_data
    
    async def complete_oauth_flow(
        self, 
        authorization_code: str, 
        state: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """
        Complete OAuth flow with authorization code.
        
        Args:
            authorization_code: Authorization code from callback
            state: State parameter for validation
            user_id: User identifier
            
        Returns:
            Dict containing token information
        """
        # Validate state
        stored_state = self._stored_states.get(state)
        if not stored_state or stored_state["used"] or stored_state["user_id"] != user_id:
            raise HTTPException(status_code=400, detail="Invalid or expired state parameter")
        
        # Mark state as used
        stored_state["used"] = True
        
        # Exchange code for token
        token_info = await self.oauth_flow.exchange_authorization_code(authorization_code)
        
        # Clean up used state
        del self._stored_states[state]
        
        return token_info