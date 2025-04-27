from typing import Any, Dict, List, Optional # type: ignore
import os
from pydantic import PostgresDsn, field_validator, EmailStr # type: ignore
from pydantic_settings import BaseSettings # type: ignore

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "TaxPoynt eInvoice API"
    
    # SECURITY
    SECRET_KEY: str = os.getenv("SECRET_KEY", "development_secret_key_please_change_in_production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7 days
    ALGORITHM: str = "HS256"
    
    # Database
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "taxpoynt")
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

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
    
    # Email Settings
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_TLS: bool = True
    EMAILS_FROM_EMAIL: str = os.getenv("EMAILS_FROM_EMAIL", "noreply@taxpoynt.com")
    EMAILS_FROM_NAME: str = os.getenv("EMAILS_FROM_NAME", "TaxPoynt eInvoice")
    
    # Verification Settings
    VERIFICATION_TOKEN_EXPIRE_HOURS: int = 48  # 48 hours
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 24  # 24 hours
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Rate Limiting
    RATE_LIMIT_AUTH_MINUTE: int = 10  # 10 requests per minute for auth endpoints
    RATE_LIMIT_API_MINUTE: int = 60   # 60 requests per minute for regular API endpoints
    RATE_LIMIT_BATCH_MINUTE: int = 10 # 10 requests per minute for batch operations

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings() 