"""
Database models for storing signature settings.

This module defines the models needed for persisting signature settings in the database,
enabling settings to survive server restarts and support versioning.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.models.user import User

class SignatureSettings(Base):
    """Database model for signature settings"""
    __tablename__ = "signature_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Settings versioning
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # User association (null means system-wide default)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    user = relationship("User", back_populates="signature_settings")
    
    # Signature algorithm settings
    algorithm = Column(String, default="RSA-PSS-SHA256")
    csid_version = Column(String, default="2.0")
    
    # Caching settings
    enable_caching = Column(Boolean, default=True)
    cache_size = Column(Integer, default=1000)
    cache_ttl = Column(Integer, default=3600)  # in seconds
    
    # Performance settings
    parallel_processing = Column(Boolean, default=True)
    max_workers = Column(Integer, default=4)
    
    # Additional settings as JSON (for extensibility)
    extra_settings = Column(JSON, default={})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary representation"""
        return {
            "id": self.id,
            "version": self.version,
            "is_active": self.is_active,
            "user_id": self.user_id,
            "algorithm": self.algorithm,
            "csid_version": self.csid_version,
            "enable_caching": self.enable_caching,
            "cache_size": self.cache_size,
            "cache_ttl": self.cache_ttl,
            "parallel_processing": self.parallel_processing,
            "max_workers": self.max_workers,
            "extra_settings": self.extra_settings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

# Add relationship to User model
User.signature_settings = relationship(
    "SignatureSettings", 
    back_populates="user", 
    uselist=True,
    cascade="all, delete-orphan"
)
