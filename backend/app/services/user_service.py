from datetime import datetime
from typing import Optional, List, Dict, Any # type: ignore
from uuid import UUID # type: ignore

from sqlalchemy.orm import Session # type: ignore

from app.models.user import User # type: ignore
from app.models.user_role import UserRole # type: ignore
from app.models.organization import Organization, OrganizationUser # type: ignore
from app.schemas.user import UserCreate, UserUpdate, OrganizationCreate, OrganizationUpdate, OrganizationUserCreate # type: ignore
from app.core.security import get_password_hash, verify_password # type: ignore


# User functions
def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Get a user by email
    """
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
    """
    Get a user by ID
    """
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_reset_token(db: Session, token: str) -> Optional[User]:
    """
    Get a user by password reset token
    """
    return db.query(User).filter(User.password_reset_token == token).first()


def get_user_by_verification_token(db: Session, token: str) -> Optional[User]:
    """
    Get a user by email verification token
    """
    return db.query(User).filter(User.email_verification_token == token).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """
    Get a list of users
    """
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user_in: UserCreate, role: UserRole = UserRole.SI_USER) -> User:
    """
    Create a new user
    """
    db_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        is_active=user_in.is_active,
        role=role,
        is_email_verified=False,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: UUID, user_in: UserUpdate) -> Optional[User]:
    """
    Update a user
    """
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    update_data = user_in.dict(exclude_unset=True)
    
    if "password" in update_data:
        hashed_password = get_password_hash(update_data["password"])
        del update_data["password"]
        update_data["hashed_password"] = hashed_password
        
    for field, value in update_data.items():
        setattr(db_user, field, value)
        
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def reset_user_password(db: Session, user: User, new_password: str) -> User:
    """
    Reset user password and clear reset token
    """
    user.hashed_password = get_password_hash(new_password)
    user.password_reset_token = None
    user.password_reset_expires_at = None
    user.updated_at = datetime.now()
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def verify_user_email(db: Session, user: User) -> User:
    """
    Mark user email as verified
    """
    user.is_email_verified = True
    user.email_verification_token = None
    user.updated_at = datetime.now()
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_last_login(db: Session, user: User) -> User:
    """
    Update user's last login timestamp
    """
    user.last_login = datetime.now()
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user by email and password
    """
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    
    # Update last login time
    update_last_login(db, user)
    return user


def is_active(user: User) -> bool:
    """
    Check if a user is active
    """
    return user.is_active


def is_email_verified(user: User) -> bool:
    """
    Check if a user's email is verified
    """
    return user.is_email_verified


# Organization functions
def get_organization_by_id(db: Session, org_id: UUID) -> Optional[Organization]:
    """
    Get organization by ID
    """
    return db.query(Organization).filter(Organization.id == org_id).first()


def get_organization_by_tax_id(db: Session, tax_id: str) -> Optional[Organization]:
    """
    Get organization by tax ID
    """
    return db.query(Organization).filter(Organization.tax_id == tax_id).first()


def get_organizations(db: Session, skip: int = 0, limit: int = 100) -> List[Organization]:
    """
    Get list of organizations
    """
    return db.query(Organization).offset(skip).limit(limit).all()


def create_organization(db: Session, org_in: OrganizationCreate) -> Organization:
    """
    Create a new organization
    """
    db_org = Organization(
        name=org_in.name,
        tax_id=org_in.tax_id,
        address=org_in.address,
        phone=org_in.phone,
        email=org_in.email,
        website=org_in.website,
        status="active",
    )
    db.add(db_org)
    db.commit()
    db.refresh(db_org)
    return db_org


def update_organization(db: Session, org_id: UUID, org_in: OrganizationUpdate) -> Optional[Organization]:
    """
    Update an organization
    """
    db_org = get_organization_by_id(db, org_id)
    if not db_org:
        return None
    
    update_data = org_in.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_org, field, value)
    
    db.add(db_org)
    db.commit()
    db.refresh(db_org)
    return db_org


# Organization User functions
def get_organization_users(db: Session, org_id: UUID) -> List[OrganizationUser]:
    """
    Get all users for an organization
    """
    return (
        db.query(OrganizationUser)
        .filter(OrganizationUser.organization_id == org_id)
        .all()
    )


def get_user_organizations(db: Session, user_id: UUID) -> List[OrganizationUser]:
    """
    Get all organizations for a user
    """
    return (
        db.query(OrganizationUser)
        .filter(OrganizationUser.user_id == user_id)
        .all()
    )


def add_user_to_organization(db: Session, org_user_in: OrganizationUserCreate) -> OrganizationUser:
    """
    Add a user to an organization
    """
    db_org_user = OrganizationUser(
        organization_id=org_user_in.organization_id,
        user_id=org_user_in.user_id,
        role=org_user_in.role,
    )
    db.add(db_org_user)
    db.commit()
    db.refresh(db_org_user)
    return db_org_user


def remove_user_from_organization(db: Session, org_id: UUID, user_id: UUID) -> bool:
    """
    Remove a user from an organization
    """
    db_org_user = (
        db.query(OrganizationUser)
        .filter(
            OrganizationUser.organization_id == org_id,
            OrganizationUser.user_id == user_id
        )
        .first()
    )
    if not db_org_user:
        return False
    
    db.delete(db_org_user)
    db.commit()
    return True


def update_user_role(db: Session, org_id: UUID, user_id: UUID, role: UserRole) -> Optional[OrganizationUser]:
    """
    Update a user's role in an organization
    """
    db_org_user = (
        db.query(OrganizationUser)
        .filter(
            OrganizationUser.organization_id == org_id,
            OrganizationUser.user_id == user_id
        )
        .first()
    )
    if not db_org_user:
        return None
    
    db_org_user.role = role
    db_org_user.updated_at = datetime.now()
    
    db.add(db_org_user)
    db.commit()
    db.refresh(db_org_user)
    return db_org_user


def create_organization_with_owner(db: Session, org_in: OrganizationCreate, owner_id: UUID) -> Dict[str, Any]:
    """
    Create an organization and add the creator as the owner
    """
    # Create organization
    organization = create_organization(db, org_in)
    
    # Add owner to organization
    org_user = OrganizationUserCreate(
        organization_id=organization.id,
        user_id=owner_id,
        role=UserRole.OWNER
    )
    organization_user = add_user_to_organization(db, org_user)
    
    return {
        "organization": organization,
        "organization_user": organization_user
    } 