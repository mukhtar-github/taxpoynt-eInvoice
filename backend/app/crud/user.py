from typing import Any, Dict, Optional, Union, List
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.user import User, UserRole, OrganizationUser, Organization
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash


def get_user(db: Session, user_id: UUID) -> Optional[User]:
    """
    Get a user by ID.
    """
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Get a user by email.
    """
    return db.query(User).filter(User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """
    Get multiple users with pagination.
    """
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user_data: UserCreate) -> User:
    """
    Create a new user.
    """
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        is_active=user_data.is_active,
        role=UserRole.USER,  # Default role
        is_email_verified=False,  # Email verification required
        created_at=datetime.utcnow()
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: UUID, user_data: Union[UserUpdate, Dict[str, Any]]) -> Optional[User]:
    """
    Update user information.
    """
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    update_data = user_data.dict(exclude_unset=True) if hasattr(user_data, "dict") else user_data
    
    # Hash the password if it's being updated
    if update_data.get("password"):
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    for field, value in update_data.items():
        if hasattr(db_user, field):
            setattr(db_user, field, value)
    
    db_user.updated_at = datetime.utcnow()
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: UUID) -> bool:
    """
    Delete a user by ID.
    """
    db_user = get_user(db, user_id)
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    return True


def get_user_organizations(db: Session, user_id: UUID) -> List[Organization]:
    """
    Get all organizations a user belongs to.
    """
    org_users = db.query(OrganizationUser).filter(OrganizationUser.user_id == user_id).all()
    
    organizations = []
    for org_user in org_users:
        org = db.query(Organization).filter(Organization.id == org_user.organization_id).first()
        if org:
            organizations.append(org)
    
    return organizations


def update_last_login(db: Session, user_id: UUID) -> None:
    """
    Update a user's last login timestamp.
    """
    db_user = get_user(db, user_id)
    if db_user:
        db_user.last_login = datetime.utcnow()
        db.add(db_user)
        db.commit()
