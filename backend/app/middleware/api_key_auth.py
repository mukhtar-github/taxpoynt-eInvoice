"""API Key Authentication Middleware for two-layer authentication."""
from typing import Optional, Callable, Awaitable
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from sqlalchemy.orm import Session
from app.db.session import get_db_session
from app.crud.api_key import authenticate_with_api_key


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware for two-layer API key authentication.
    
    This middleware authenticates requests using both API key and Secret key 
    provided in request headers, as required in the Authentication.md documentation.
    """
    
    def __init__(
        self, 
        app: ASGIApp,
        api_key_header: str = "X-API-KEY",
        secret_key_header: str = "X-SECRET-KEY",
        exclude_paths: list = None
    ):
        super().__init__(app)
        self.api_key_header = api_key_header
        self.secret_key_header = secret_key_header
        self.exclude_paths = exclude_paths or ["/docs", "/redoc", "/openapi.json", "/auth"]
        
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process an incoming request and apply API key authentication if needed."""
        # Skip authentication for excluded paths
        path = request.url.path
        if any(path.startswith(exclude) for exclude in self.exclude_paths):
            return await call_next(request)
            
        # Check if API key authentication headers are present
        api_key = request.headers.get(self.api_key_header)
        secret_key = request.headers.get(self.secret_key_header)
        
        # If no API key headers, fallback to token-based auth (handled by dependencies)
        if not api_key or not secret_key:
            return await call_next(request)
            
        # Validate API key and Secret key
        db = get_db_session()
        try:
            result = authenticate_with_api_key(db, api_key, secret_key)
            
            if not result:
                return Response(
                    content='{"detail":"Invalid API key or Secret key"}',
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    media_type="application/json"
                )
                
            # Authentication successful
            user, organization, api_key_obj = result
            
            # Store authenticated user and organization in request state
            request.state.authenticated_user = user
            request.state.authenticated_organization = organization
            request.state.authenticated_with_api_key = True
            
            # Process the request
            return await call_next(request)
        finally:
            db.close()
