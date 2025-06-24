from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os

from app.core.config import settings

def get_engine_kwargs():
    """Get database engine configuration optimized for Railway deployment."""
    kwargs = {
        "pool_size": 5,
        "max_overflow": 10,
        "pool_timeout": 20,
        "pool_recycle": 300,  # 5 minutes
        "pool_pre_ping": True,  # Test connections before use
        "connect_args": {
            "connect_timeout": 10,
            "server_settings": {
                "application_name": "taxpoynt-einvoice",
            }
        }
    }
    
    # Railway-specific optimizations
    if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_DEPLOYMENT"):
        kwargs.update({
            "pool_size": 3,  # Smaller pool for Railway
            "max_overflow": 5,
            "pool_timeout": 10,  # Faster timeout
            "connect_args": {
                "connect_timeout": 5,
                "server_settings": {
                    "application_name": "taxpoynt-railway",
                }
            }
        })
    
    return kwargs

# Create engine with Railway optimizations
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    **get_engine_kwargs()
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
def get_db_session() -> Session:
    """Get a SQLAlchemy session directly for middleware use.
    NOTE: The caller is responsible for closing this session."""
    return SessionLocal()