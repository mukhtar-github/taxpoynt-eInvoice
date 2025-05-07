"""Service for secure API credential management."""
import json
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.api_credential import ApiCredential, CredentialType
from app.schemas.api_credential import (
    ApiCredentialCreate, ApiCredentialUpdate, 
    FirsApiCredential, OdooApiCredential
)
from app.utils.encryption import (
    encrypt_field, decrypt_field, 
    encrypt_dict_fields, decrypt_dict_fields,
    get_app_encryption_key
)


def create_api_credential(
    db: Session, 
    credential_in: ApiCredentialCreate,
    created_by: UUID
) -> ApiCredential:
    """
    Create a new API credential with encryption.
    
    Args:
        db: Database session
        credential_in: API credential data
        created_by: User ID of creator
    
    Returns:
        Created API credential
    """
    # Prepare data for storage
    credential_data = credential_in.model_dump(exclude={"additional_config"})
    
    # Encrypt sensitive fields
    encryption_key = get_app_encryption_key()
    
    sensitive_fields = [
        "client_id", "client_secret", "api_key", "api_secret"
    ]
    
    for field in sensitive_fields:
        if field in credential_data and credential_data[field]:
            credential_data[field] = encrypt_field(credential_data[field], encryption_key)
    
    # Encrypt additional config if provided
    if credential_in.additional_config:
        config_json = json.dumps(credential_in.additional_config)
        credential_data["additional_config"] = encrypt_field(config_json, encryption_key)
    
    # Add creator
    credential_data["created_by"] = created_by
    
    # Create database object
    db_credential = ApiCredential(**credential_data)
    db.add(db_credential)
    db.commit()
    db.refresh(db_credential)
    
    return db_credential


def get_api_credential(
    db: Session, 
    credential_id: UUID,
    decrypt_sensitive: bool = False
) -> Optional[ApiCredential]:
    """
    Get API credential by ID with optional decryption.
    
    Args:
        db: Database session
        credential_id: API credential ID
        decrypt_sensitive: Whether to decrypt sensitive fields
        
    Returns:
        API credential if found
    """
    credential = db.query(ApiCredential).filter(ApiCredential.id == credential_id).first()
    
    if credential and decrypt_sensitive:
        decrypt_api_credential_fields(credential)
    
    return credential


def get_organization_credentials(
    db: Session, 
    organization_id: UUID,
    credential_type: Optional[CredentialType] = None
) -> List[ApiCredential]:
    """
    Get all API credentials for an organization.
    
    Args:
        db: Database session
        organization_id: Organization ID
        credential_type: Optional filter by credential type
        
    Returns:
        List of API credentials
    """
    query = db.query(ApiCredential).filter(ApiCredential.organization_id == organization_id)
    
    if credential_type:
        query = query.filter(ApiCredential.credential_type == credential_type)
    
    return query.all()


def update_api_credential(
    db: Session,
    credential_id: UUID,
    credential_in: ApiCredentialUpdate,
    updated_by: UUID
) -> Optional[ApiCredential]:
    """
    Update an API credential with encryption for changed fields.
    
    Args:
        db: Database session
        credential_id: API credential ID
        credential_in: Updated credential data
        updated_by: User ID of updater
        
    Returns:
        Updated API credential if found
    """
    db_credential = get_api_credential(db, credential_id)
    if not db_credential:
        return None
    
    # Get data to update, excluding None values
    update_data = credential_in.model_dump(exclude_unset=True)
    
    # Encrypt sensitive fields that are being updated
    encryption_key = get_app_encryption_key()
    sensitive_fields = ["client_id", "client_secret", "api_key", "api_secret"]
    
    for field in sensitive_fields:
        if field in update_data and update_data[field]:
            update_data[field] = encrypt_field(update_data[field], encryption_key)
    
    # Handle additional config update
    if "additional_config" in update_data and update_data["additional_config"]:
        config_json = json.dumps(update_data["additional_config"])
        update_data["additional_config"] = encrypt_field(config_json, encryption_key)
    
    # Update fields
    for field, value in update_data.items():
        setattr(db_credential, field, value)
    
    # Update timestamp
    db_credential.updated_at = datetime.now()
    
    db.add(db_credential)
    db.commit()
    db.refresh(db_credential)
    
    return db_credential


def delete_api_credential(db: Session, credential_id: UUID) -> bool:
    """
    Delete an API credential.
    
    Args:
        db: Database session
        credential_id: API credential ID
        
    Returns:
        True if deleted
    """
    credential = db.query(ApiCredential).filter(ApiCredential.id == credential_id).first()
    if not credential:
        return False
    
    db.delete(credential)
    db.commit()
    return True


def decrypt_api_credential_fields(credential: ApiCredential) -> ApiCredential:
    """
    Decrypt the encrypted fields of an API credential.
    
    Args:
        credential: API credential
        
    Returns:
        API credential with decrypted fields
    """
    encryption_key = get_app_encryption_key()
    
    # Decrypt sensitive string fields
    sensitive_fields = ["client_id", "client_secret", "api_key", "api_secret"]
    for field in sensitive_fields:
        value = getattr(credential, field)
        if value:
            decrypted_value = decrypt_field(value, encryption_key)
            setattr(credential, field, decrypted_value)
    
    # Decrypt and parse additional config
    if credential.additional_config:
        decrypted_config = decrypt_field(credential.additional_config, encryption_key)
        try:
            config_dict = json.loads(decrypted_config)
            setattr(credential, "additional_config", config_dict)
        except json.JSONDecodeError:
            # In case it's not valid JSON
            setattr(credential, "additional_config", decrypted_config)
    
    return credential


def record_credential_usage(db: Session, credential_id: UUID) -> bool:
    """
    Record usage of an API credential.
    
    Args:
        db: Database session
        credential_id: API credential ID
        
    Returns:
        True if updated
    """
    credential = db.query(ApiCredential).filter(ApiCredential.id == credential_id).first()
    if not credential:
        return False
    
    credential.last_used_at = datetime.now()
    db.add(credential)
    db.commit()
    return True


def create_firs_credential(
    db: Session,
    organization_id: UUID,
    credential_data: FirsApiCredential,
    name: str,
    description: Optional[str],
    created_by: UUID
) -> ApiCredential:
    """
    Create a specialized FIRS API credential.
    
    Args:
        db: Database session
        organization_id: Organization ID
        credential_data: FIRS credential data
        name: Credential name
        description: Credential description
        created_by: User ID of creator
        
    Returns:
        Created API credential
    """
    # Create credential with specialized fields for FIRS
    credential_in = ApiCredentialCreate(
        organization_id=organization_id,
        name=name,
        description=description,
        credential_type=CredentialType.FIRS,
        client_id=credential_data.client_id,
        client_secret=credential_data.client_secret,
        additional_config={"environment": credential_data.environment}
    )
    
    return create_api_credential(db, credential_in, created_by)


def create_odoo_credential(
    db: Session,
    organization_id: UUID,
    credential_data: OdooApiCredential,
    name: str,
    description: Optional[str],
    created_by: UUID
) -> ApiCredential:
    """
    Create a specialized Odoo API credential.
    
    Args:
        db: Database session
        organization_id: Organization ID
        credential_data: Odoo credential data
        name: Credential name
        description: Credential description
        created_by: User ID of creator
        
    Returns:
        Created API credential
    """
    # Prepare additional config for Odoo
    additional_config = {
        "url": credential_data.url,
        "database": credential_data.database
    }
    
    # Create credential with specialized fields for Odoo
    credential_in = ApiCredentialCreate(
        organization_id=organization_id,
        name=name,
        description=description,
        credential_type=CredentialType.ODOO,
        client_id=credential_data.username,  # username as client_id
        client_secret=credential_data.password,  # password as client_secret
        api_key=credential_data.api_key,
        additional_config=additional_config
    )
    
    return create_api_credential(db, credential_in, created_by)


def get_firs_credentials(
    db: Session,
    organization_id: UUID,
    decrypt: bool = False
) -> List[ApiCredential]:
    """
    Get all FIRS API credentials for an organization.
    
    Args:
        db: Database session
        organization_id: Organization ID
        decrypt: Whether to decrypt sensitive fields
        
    Returns:
        List of FIRS API credentials
    """
    credentials = get_organization_credentials(db, organization_id, CredentialType.FIRS)
    
    if decrypt:
        for credential in credentials:
            decrypt_api_credential_fields(credential)
    
    return credentials


def get_odoo_credentials(
    db: Session,
    organization_id: UUID,
    decrypt: bool = False
) -> List[ApiCredential]:
    """
    Get all Odoo API credentials for an organization.
    
    Args:
        db: Database session
        organization_id: Organization ID
        decrypt: Whether to decrypt sensitive fields
        
    Returns:
        List of Odoo API credentials
    """
    credentials = get_organization_credentials(db, organization_id, CredentialType.ODOO)
    
    if decrypt:
        for credential in credentials:
            decrypt_api_credential_fields(credential)
    
    return credentials
