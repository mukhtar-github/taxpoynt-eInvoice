from datetime import datetime, timedelta
from typing import Any, Union, Optional, List # type: ignore
import re
from uuid import UUID # type: ignore

from jose import jwt # type: ignore
from passlib.context import CryptContext # type: ignore

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token with longer expiration
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password
    """
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