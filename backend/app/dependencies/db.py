"""
Database dependency for FastAPI route functions.
Provides a database session for each request.
"""

from typing import Generator
from sqlalchemy.orm import Session

from app.db.session import SessionLocal

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a SQLAlchemy database session.
    The session is automatically closed when the request is complete.
    
    Returns:
        Generator yielding a SQLAlchemy Session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
