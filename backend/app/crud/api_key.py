"""CRUD operations for API keys."""
import uuid
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.models.api_key import APIKey
from app.schemas.api_key import APIKeyCreate
from app.models.user import User
from app.models.organization import Organization # type: ignore

# Context for hashing API keys
api_key_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate_key(length: int = 32) -> Tuple[str, str]:
    """
    Generate a new key with a prefix.
    Returns a tuple of (prefix, full_key).
    """
    # Generate a prefix for reference (8 characters)
    prefix = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
    
    # Generate a random string for the key
    key_base = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))
    
    # Combine prefix and key with a period
    full_key = f"{prefix}.{key_base}"
    
    return prefix, full_key


def generate_api_key(length: int = 32) -> Tuple[str, str]:
    """
    Generate a new API key with a prefix.
    Returns a tuple of (prefix, full_key).
    """
    return generate_key(length)


def generate_secret_key(length: int = 64) -> Tuple[str, str]:
    """
    Generate a new secret key with a prefix. More secure than API key.
    Returns a tuple of (prefix, full_key).
    """
    return generate_key(length)

def hash_key(key: str) -> str:
    """Hash a key."""
    return api_key_context.hash(key)

def verify_key(plain_key: str, hashed_key: str) -> bool:
    """Verify a key against a hash."""
    return api_key_context.verify(plain_key, hashed_key)

def hash_api_key(api_key: str) -> str:
    """Hash an API key."""
    return hash_key(api_key)

def hash_secret_key(secret_key: str) -> str:
    """Hash a secret key."""
    return hash_key(secret_key)

def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify an API key against a hash."""
    return verify_key(plain_key, hashed_key)

def verify_secret_key(plain_key: str, hashed_key: str) -> bool:
    """Verify a secret key against a hash."""
    return verify_key(plain_key, hashed_key)

def get_api_key_by_prefix(db: Session, prefix: str) -> Optional[APIKey]:
    """Get API key by prefix."""
    return db.query(APIKey).filter(APIKey.prefix == prefix).first()

def create_api_key(
    db: Session, 
    user: User, 
    organization: Organization,
    key_data: APIKeyCreate
) -> Tuple[APIKey, str, str]:
    """
    Create a new API key with both API key and secret key for two-layer authentication.
    Returns a tuple of (api_key_model, full_api_key, full_secret_key).
    """
    # Generate API key
    api_prefix, full_api_key = generate_api_key(32)  # 32 character API key
    
    # Generate Secret key (longer for more security)
    secret_prefix, full_secret_key = generate_secret_key(64)  # 64 character secret key
    
    # Calculate expiry date if needed
    expires_at = None
    if key_data.expires_days:
        expires_at = datetime.utcnow() + timedelta(days=key_data.expires_days)
    
    # Create API key in database
    db_api_key = APIKey(
        id=uuid.uuid4(),
        prefix=api_prefix,
        hashed_key=hash_api_key(full_api_key),
        secret_prefix=secret_prefix,
        hashed_secret=hash_secret_key(full_secret_key),
        name=key_data.name,
        description=key_data.description,
        expires_at=expires_at,
        user_id=user.id,
        organization_id=organization.id,
        rate_limit_per_minute=key_data.rate_limit_per_minute or 60,
        rate_limit_per_day=key_data.rate_limit_per_day or 10000
    )
    
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)
    
    return db_api_key, full_api_key, full_secret_key

def get_api_keys_by_user(db: Session, user_id: uuid.UUID) -> List[APIKey]:
    """Get all API keys for a user."""
    return db.query(APIKey).filter(APIKey.user_id == user_id).all()

def get_api_keys_by_organization(db: Session, organization_id: uuid.UUID) -> List[APIKey]:
    """Get all API keys for an organization."""
    return db.query(APIKey).filter(APIKey.organization_id == organization_id).all()

def update_api_key_last_used(db: Session, api_key: APIKey) -> APIKey:
    """Update the last_used_at timestamp for an API key."""
    api_key.last_used_at = datetime.utcnow()
    db.commit()
    db.refresh(api_key)
    return api_key

def revoke_api_key(db: Session, api_key_id: uuid.UUID) -> bool:
    """Revoke an API key by setting is_active to False."""
    db_api_key = db.query(APIKey).filter(APIKey.id == api_key_id).first()
    if not db_api_key:
        return False
    
    db_api_key.is_active = False
    db.commit()
    return True

def authenticate_with_api_key(db: Session, api_key: str, secret_key: str) -> Optional[Tuple[User, Organization, APIKey]]:
    """
    Authenticate with both API key and secret key (two-layer authentication).
    Returns a tuple of (user, organization, api_key) if successful.
    """
    if not api_key or not secret_key or '.' not in api_key or '.' not in secret_key:
        return None
    
    # Extract prefixes
    try:
        api_prefix = api_key.split('.')[0]
        secret_prefix = secret_key.split('.')[0]
    except:
        return None
    
    # Get API key by prefix
    db_api_key = get_api_key_by_prefix(db, api_prefix)
    if not db_api_key:
        return None
    
    # Check if API key is active
    if not db_api_key.is_active:
        return None
    
    # Check if API key has expired
    if db_api_key.expires_at and db_api_key.expires_at < datetime.utcnow():
        return None
    
    # Verify both API key and secret key match
    if not verify_api_key(api_key, db_api_key.hashed_key):
        return None
        
    if db_api_key.secret_prefix != secret_prefix or not verify_secret_key(secret_key, db_api_key.hashed_secret):
        return None
    
    # Check rate limiting
    current_time = datetime.utcnow()
    
    # Reset counters if needed
    minute_ago = current_time - timedelta(minutes=1)
    day_ago = current_time - timedelta(days=1)
    
    if db_api_key.last_minute_reset < minute_ago:
        db_api_key.current_minute_requests = 0
        db_api_key.last_minute_reset = current_time
    
    if db_api_key.last_day_reset < day_ago:
        db_api_key.current_day_requests = 0
        db_api_key.last_day_reset = current_time
    
    # Check if rate limits exceeded
    if db_api_key.current_minute_requests >= db_api_key.rate_limit_per_minute:
        return None
    
    if db_api_key.current_day_requests >= db_api_key.rate_limit_per_day:
        return None
    
    # Increment request counters
    db_api_key.current_minute_requests += 1
    db_api_key.current_day_requests += 1
    
    # Get user and organization
    user = db.query(User).filter(User.id == db_api_key.user_id).first()
    organization = db.query(Organization).filter(Organization.id == db_api_key.organization_id).first()
    
    if not user or not organization:
        return None
    
    # Update last_used_at timestamp
    update_api_key_last_used(db, db_api_key)
    
    return user, organization, db_api_key 