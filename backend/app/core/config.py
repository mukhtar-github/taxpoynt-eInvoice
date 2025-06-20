from typing import Any, Dict, List, Optional, Union
import os
import pathlib
from pydantic import PostgresDsn, validator, EmailStr, AnyHttpUrl
# Handle both Pydantic V1 and V2 compatibility
try:
    # Try importing from pydantic (V1)
    from pydantic import BaseSettings
except ImportError:
    # Fall back to pydantic-settings (V2)
    from pydantic_settings import BaseSettings
import secrets

class Settings(BaseSettings):
    # Configuration for Pydantic V1
    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"  # Allow extra fields in environment variables
    
    # Configuration for Pydantic V2
    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "extra": "ignore"  # Allow extra fields in environment variables
    }

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "TaxPoynt eInvoice API"
    VERSION: str = "0.1.0"
    
    # Environment
    APP_ENV: str = os.getenv("APP_ENV", "development")
    ENVIRONMENT: str = APP_ENV  # Alias for consistent naming
    
    # SECURITY
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7 days
    ALGORITHM: str = "HS256"
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "development_encryption_key_please_change_in_production")
    
    # Integration Authentication
    CREDENTIAL_ENCRYPTION_KEY: str = os.getenv("CREDENTIAL_ENCRYPTION_KEY", "")
    OAUTH_TOKEN_REFRESH_BUFFER_MINUTES: int = 5  # Refresh tokens 5 minutes before expiry
    OAUTH_MAX_RETRY_ATTEMPTS: int = 3  # Maximum retries for token refresh
    OAUTH_RETRY_DELAY_SECONDS: int = 1  # Initial delay between retries
    
    # HubSpot Integration
    HUBSPOT_SYNC_INTERVAL: int = int(os.getenv("HUBSPOT_SYNC_INTERVAL", "3600"))  # Default: hourly
    
    # FIRS Encryption and Cryptographic Signing
    CRYPTO_KEYS_PATH: str = os.getenv("CRYPTO_KEYS_PATH", "")
    SIGNING_PRIVATE_KEY_PATH: str = os.getenv("SIGNING_PRIVATE_KEY_PATH", "")
    SIGNING_KEY_PASSWORD: str = os.getenv("SIGNING_KEY_PASSWORD", "")
    VERIFICATION_PUBLIC_KEY_PATH: str = os.getenv("VERIFICATION_PUBLIC_KEY_PATH", "")
    FIRS_PUBLIC_KEY_PATH: str = os.getenv("FIRS_PUBLIC_KEY_PATH", "")
    FIRS_CERTIFICATE_PATH: str = os.getenv("FIRS_CERTIFICATE_PATH", "")
    
    # TLS Configuration
    CLIENT_CERT_PATH: str = os.getenv("CLIENT_CERT_PATH", "")
    CLIENT_KEY_PATH: str = os.getenv("CLIENT_KEY_PATH", "")
    ENFORCE_HTTPS: bool = os.getenv("ENFORCE_HTTPS", "True").lower() in ("true", "1", "t")
    MIN_TLS_VERSION: str = os.getenv("MIN_TLS_VERSION", "1.2")
    
    # Database
    SQLALCHEMY_DATABASE_URI: Optional[str] = os.getenv("DATABASE_URL")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "taxpoynt")

    # Redis Configuration
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    
    # Reference Data
    REFERENCE_DATA_DIR: str = os.getenv("REFERENCE_DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "reference_data"))

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        # If DATABASE_URL is already provided via environment, use it directly
        # This is useful for Railway integration where the full URL is provided
        if isinstance(v, str) and v:
            return v
        
        # For testing/development mode, we can use SQLite instead of PostgreSQL
        if os.getenv("APP_ENV") == "development" or os.getenv("TESTING") == "true":
            # Use SQLite for development/testing
            return "sqlite:///./test.db"
        
        try:
            # Otherwise, build connection URL from individual components
            postgres_dsn = PostgresDsn.build(
                scheme="postgresql",
                user=values.get("POSTGRES_USER") or "postgres",
                password=values.get("POSTGRES_PASSWORD") or "postgres",
                host=values.get("POSTGRES_SERVER") or "localhost",
                path=f"{values.get('POSTGRES_DB') or 'taxpoynt'}",
            )
            # Convert PostgresDsn to string to avoid validation errors
            return str(postgres_dsn)
        except Exception as e:
            print(f"Warning: Failed to build PostgreSQL DSN: {e}")
            # Fallback to SQLite
            return "sqlite:///./fallback.db"

    @validator("REDIS_URL", pre=True)
    def assemble_redis_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        
        redis_url = f"redis://{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}"
        if values.get("REDIS_PASSWORD"):
            redis_url = f"redis://:{values.get('REDIS_PASSWORD')}@{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}"
        
        if values.get("REDIS_DB"):
            redis_url += f"/{values.get('REDIS_DB')}"
        
        return redis_url
    
    # Email Settings
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST")
    SMTP_PORT: Optional[int] = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    SMTP_TLS: bool = os.getenv("SMTP_TLS", "True").lower() == "true"
    EMAILS_FROM_EMAIL: Optional[EmailStr] = os.getenv("EMAILS_FROM_EMAIL")
    EMAILS_FROM_NAME: Optional[str] = os.getenv("EMAILS_FROM_NAME")
    
    # Verification Settings
    VERIFICATION_TOKEN_EXPIRE_HOURS: int = 48  # 48 hours
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 24  # 24 hours
    
    # CORS
    CORS_ORIGINS: List[Union[str, AnyHttpUrl]] = [
        "http://localhost:3000",  # Frontend dev server
        "https://localhost:3000",
        "http://localhost:8000",  # Backend dev server
        "https://localhost:8000",
        "https://www.taxpoynt.com",  # Production frontend
        "https://taxpoynt.com",      # Production frontend (apex domain)
        "http://www.taxpoynt.com",   # HTTP version of production frontend
        "http://taxpoynt.com",       # HTTP version of apex domain
        "https://taxpoynte-invoice.vercel.app",  # Vercel deployment
        "*"  # Allow all origins (for testing - remove in production)
    ]
    
    # Frontend/Backend URLs (optional fields)
    FRONTEND_URL: Optional[str] = os.getenv("FRONTEND_URL", "http://localhost:3000")
    BACKEND_URL: Optional[str] = os.getenv("BACKEND_URL", "http://localhost:8000")
    NEXT_PUBLIC_FRONTEND_URL: Optional[str] = os.getenv("NEXT_PUBLIC_FRONTEND_URL", "https://taxpoynte-invoice.vercel.app/")
    NEXT_PUBLIC_BACKEND_URL: Optional[str] = os.getenv("NEXT_PUBLIC_BACKEND_URL", "https://taxpoynt-einvoice-production.up.railway.app/api/v1")
    ALLOWED_ORIGINS: Optional[str] = os.getenv("ALLOWED_ORIGINS", "https://taxpoynte-invoice.vercel.app/")
    

    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse CORS origins from env variables."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Rate Limiting
    RATE_LIMIT_AUTH_MINUTE: int = 10     # 10 requests per minute for auth endpoints
    RATE_LIMIT_API_MINUTE: int = 60      # 60 requests per minute for regular API endpoints
    RATE_LIMIT_BATCH_MINUTE: int = 10    # 10 requests per minute for batch operations
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))  # Default general rate limit per minute
    RATE_LIMIT_PER_DAY: int = int(os.getenv("RATE_LIMIT_PER_DAY", "10000"))     # Default general rate limit per day
    
    # TLS & Security Configuration
    TLS_VERSION: str = os.getenv("TLS_VERSION", "1.2")  # Minimum TLS version to enforce
    TLS_CIPHERS: str = os.getenv("TLS_CIPHERS", "ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384")  # Secure cipher suite
    HSTS_ENABLED: bool = os.getenv("HSTS_ENABLED", "True").lower() in ("true", "1", "t")
    HSTS_MAX_AGE: int = int(os.getenv("HSTS_MAX_AGE", "31536000"))  # 1 year in seconds

    # OAuth providers
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    MICROSOFT_CLIENT_ID: str = os.getenv("MICROSOFT_CLIENT_ID", "")
    MICROSOFT_CLIENT_SECRET: str = os.getenv("MICROSOFT_CLIENT_SECRET", "")
    
    # Frontend URLs for redirects
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    VERIFY_EMAIL_URL: str = "{FRONTEND_URL}/auth/verify-email"
    RESET_PASSWORD_URL: str = "{FRONTEND_URL}/auth/reset-password"
    
    # Odoo Integration Settings
    ODOO_HOST: Optional[str] = os.getenv("ODOO_HOST")
    ODOO_PORT: Optional[int] = int(os.getenv("ODOO_PORT", "443"))
    ODOO_PROTOCOL: str = os.getenv("ODOO_PROTOCOL", "jsonrpc+ssl")
    ODOO_DATABASE: Optional[str] = os.getenv("ODOO_DATABASE")
    ODOO_USERNAME: Optional[str] = os.getenv("ODOO_USERNAME")
    ODOO_PASSWORD: Optional[str] = os.getenv("ODOO_PASSWORD")
    ODOO_API_KEY: Optional[str] = os.getenv("ODOO_API_KEY")
    ODOO_AUTH_METHOD: str = os.getenv("ODOO_AUTH_METHOD", "password")
    
    # FIRS API Configuration
    FIRS_API_URL: str = os.getenv("FIRS_API_URL", "https://api.firs.gov.ng")
    FIRS_API_KEY: str = os.getenv("FIRS_API_KEY", "")
    FIRS_API_SECRET: str = os.getenv("FIRS_API_SECRET", "")
    FIRS_SUBMISSION_TIMEOUT: int = int(os.getenv("FIRS_SUBMISSION_TIMEOUT", "30"))
    FIRS_RETRY_ATTEMPTS: int = int(os.getenv("FIRS_RETRY_ATTEMPTS", "3"))
    FIRS_MAX_BATCH_SIZE: int = int(os.getenv("FIRS_MAX_BATCH_SIZE", "100"))
    
    # FIRS Sandbox Configuration
    FIRS_SANDBOX_API_URL: str = os.getenv("FIRS_SANDBOX_API_URL", "https://eivc-k6z6d.ondigitalocean.app")
    FIRS_SANDBOX_API_KEY: str = os.getenv("FIRS_SANDBOX_API_KEY", "")
    FIRS_SANDBOX_API_SECRET: str = os.getenv("FIRS_SANDBOX_API_SECRET", "")
    FIRS_USE_SANDBOX: bool = os.getenv("FIRS_USE_SANDBOX", "True").lower() in ("true", "1", "t")
    
    # IRN Service Configuration
    FIRS_SERVICE_ID: str = os.getenv("FIRS_SERVICE_ID", "94ND90NR")
    IRN_EXPIRY_DAYS: int = int(os.getenv("IRN_EXPIRY_DAYS", "30"))
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")



settings = Settings() 