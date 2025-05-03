from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List # type: ignore
import re
from uuid import UUID # type: ignore
import uuid
from jose import jwt, JWTError # type: ignore
from passlib.context import CryptContext # type: ignore
from sqlalchemy.orm import Session
from redis import Redis # type: ignore

from app.core.config import settings
from app.db.redis import get_redis_client

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None, token_type: str = "access") -> str:
    """Create a JWT token with payload and expiration."""
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    elif token_type == "access":
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    else:  # refresh token
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Add standard claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": token_type,
        "jti": str(uuid.uuid4()),  # Unique token ID
    })
    
    # Create token with payload, secret, and algorithm
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create access token."""
    return create_token(data, expires_delta, token_type="access")


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create refresh token."""
    return create_token(data, expires_delta, token_type="refresh")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def validate_password_complexity(password: str) -> bool:
    """
    Validate password complexity requirements:
    - At least 8 characters
    - Contains uppercase letter
    - Contains lowercase letter
    - Contains a digit
    """
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    return True


def get_password_strength_message(password: str) -> str:
    """
    Get a message describing password strength requirements
    """
    issues = []
    
    if len(password) < 8:
        issues.append("Password must be at least 8 characters long")
    if not re.search(r'[A-Z]', password):
        issues.append("Password must contain at least one uppercase letter")
    if not re.search(r'[a-z]', password):
        issues.append("Password must contain at least one lowercase letter")
    if not re.search(r'\d', password):
        issues.append("Password must contain at least one digit")
        
    if not issues:
        return "Password meets all requirements"
    else:
        return "\n".join(issues)


def get_permissions_for_role(role: str) -> List[str]:
    """
    Get a list of permissions for a given role
    """
    # Define role-based permissions
    role_permissions = {
        "owner": [
            "manage:organization",
            "manage:users",
            "manage:integrations",
            "view:dashboard",
            "generate:irn",
            "validate:invoice",
        ],
        "admin": [
            "manage:integrations",
            "view:dashboard",
            "generate:irn",
            "validate:invoice",
        ],
        "member": [
            "view:dashboard", 
            "generate:irn",
            "validate:invoice",
        ],
        "si_user": [
            "view:dashboard",
            "generate:irn",
            "validate:invoice",
        ],
    }
    
    return role_permissions.get(role.lower(), [])


# Token blacklist cache (Redis-based)
def get_token_blacklist() -> Redis:
    """Get Redis client for token blacklist."""
    return get_redis_client()


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def verify_access_token(token: str) -> Optional[str]:
    """Verify access token and return user ID if valid."""
    payload = decode_token(token)
    
    if payload is None:
        return None
        
    # Check token type
    if payload.get("type") != "access":
        return None
        
    # Check if token is blacklisted
    token_blacklist = get_token_blacklist()
    token_jti = payload.get("jti")
    if token_jti and token_blacklist.exists(f"blacklist:{token_jti}"):
        return None
        
    # Return user ID
    return payload.get("sub")


def verify_refresh_token(token: str) -> Optional[str]:
    """Verify refresh token and return user ID if valid."""
    payload = decode_token(token)
    
    if payload is None:
        return None
        
    # Check token type
    if payload.get("type") != "refresh":
        return None
        
    # Check if token is blacklisted
    token_blacklist = get_token_blacklist()
    token_jti = payload.get("jti")
    if token_jti and token_blacklist.exists(f"blacklist:{token_jti}"):
        return None
        
    # Return user ID
    return payload.get("sub")


def blacklist_token(token: str) -> bool:
    """Add token to blacklist."""
    try:
        payload = decode_token(token)
        if not payload:
            return False
            
        # Add token to blacklist with expiration
        token_blacklist = get_token_blacklist()
        token_jti = payload.get("jti")
        
        if not token_jti:
            return False
            
        # Calculate remaining time for token
        exp = payload.get("exp")
        if not exp:
            return False
            
        # Convert timestamp to datetime
        exp_datetime = datetime.fromtimestamp(exp)
        current_datetime = datetime.utcnow()
        
        # Calculate time difference in seconds (always at least 1 second)
        ttl = max(1, int((exp_datetime - current_datetime).total_seconds()))
        
        # Add to blacklist with TTL
        token_blacklist.setex(f"blacklist:{token_jti}", ttl, "1")
        return True
    except Exception:
        return False


def authenticate_user(db: Session, email: str, password: str) -> Optional[Any]:
    """Authenticate user with email and password."""
    from app.crud.user import get_user_by_email # type: ignore
    
    user = get_user_by_email(db, email)
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user 