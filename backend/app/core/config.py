from typing import Any, Dict, List, Optional, Union # type: ignore
import os
from pydantic import PostgresDsn, field_validator, EmailStr, AnyHttpUrl, validator # type: ignore
from pydantic_settings import BaseSettings # type: ignore
import secrets

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "TaxPoynt eInvoice API"
    
    # Environment
    APP_ENV: str = os.getenv("APP_ENV", "development")
    
    # SECURITY
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7 days
    ALGORITHM: str = "HS256"
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "development_encryption_key_please_change_in_production")
    
    # Database
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "taxpoynt")
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_URL: Optional[str] = None

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: Optional[str], info: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        
        postgres_dsn = PostgresDsn.build(
            scheme="postgresql",
            username=info.data.get("POSTGRES_USER"),
            password=info.data.get("POSTGRES_PASSWORD"),
            host=info.data.get("POSTGRES_SERVER"),
            path=f"{info.data.get('POSTGRES_DB') or ''}",
        )
        return postgres_dsn

    @field_validator("REDIS_URL", mode="before")
    def assemble_redis_connection(cls, v: Optional[str], info: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        
        redis_url = f"redis://{info.data.get('REDIS_HOST')}:{info.data.get('REDIS_PORT')}"
        if info.data.get("REDIS_PASSWORD"):
            redis_url = f"redis://:{info.data.get('REDIS_PASSWORD')}@{info.data.get('REDIS_HOST')}:{info.data.get('REDIS_PORT')}"
        
        if info.data.get("REDIS_DB"):
            redis_url += f"/{info.data.get('REDIS_DB')}"
        
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
    ]

    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse CORS origins from env variables."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Rate Limiting
    RATE_LIMIT_AUTH_MINUTE: int = 10  # 10 requests per minute for auth endpoints
    RATE_LIMIT_API_MINUTE: int = 60   # 60 requests per minute for regular API endpoints
    RATE_LIMIT_BATCH_MINUTE: int = 10 # 10 requests per minute for batch operations

    # OAuth providers
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    MICROSOFT_CLIENT_ID: str = os.getenv("MICROSOFT_CLIENT_ID", "")
    MICROSOFT_CLIENT_SECRET: str = os.getenv("MICROSOFT_CLIENT_SECRET", "")
    
    # Frontend URLs for redirects
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    VERIFY_EMAIL_URL: str = "{FRONTEND_URL}/auth/verify-email"
    RESET_PASSWORD_URL: str = "{FRONTEND_URL}/auth/reset-password"

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings() 