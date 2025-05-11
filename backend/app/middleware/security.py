"""Security middleware for enforcing HTTPS and HSTS."""
from typing import Callable, Awaitable
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.core.config import settings


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Security middleware for enforcing HTTPS and setting security headers.
    - Redirects HTTP to HTTPS
    - Adds HSTS headers when HTTPS is enabled
    - Adds security-related headers to all responses
    """
    
    def __init__(
        self, 
        app: ASGIApp,
        https_redirect: bool = True,
        enable_hsts: bool = True,
    ):
        super().__init__(app)
        self.https_redirect = https_redirect and settings.ENFORCE_HTTPS
        self.enable_hsts = enable_hsts and settings.HSTS_ENABLED
        
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process an incoming request and enforce security policies."""
        # Check if we need to redirect to HTTPS
        if self.https_redirect and request.url.scheme == "http":
            https_url = str(request.url).replace("http://", "https://", 1)
            return Response(
                status_code=status.HTTP_301_MOVED_PERMANENTLY,
                headers={"Location": https_url}
            )
            
        # Process the request normally
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Add HSTS header if enabled
        if self.enable_hsts and (request.url.scheme == "https" or settings.APP_ENV != "production"):
            response.headers["Strict-Transport-Security"] = f"max-age={settings.HSTS_MAX_AGE}; includeSubDomains"
            
        # Add Content-Security-Policy
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; connect-src 'self'; img-src 'self' data:; style-src 'self';"
        
        return response
