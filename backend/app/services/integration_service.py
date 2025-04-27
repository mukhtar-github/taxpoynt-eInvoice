from typing import Dict, Any, List, Optional # type: ignore
from uuid import UUID # type: ignore

from sqlalchemy.orm import Session # type: ignore

from app import crud
from app.schemas.integration import IntegrationCreate, IntegrationUpdate, Integration # type: ignore
from app.utils.encryption import encrypt_sensitive_value, decrypt_sensitive_value, get_app_encryption_key # type: ignore


# List of config fields that should be encrypted
SENSITIVE_CONFIG_FIELDS = [
    "api_key", 
    "client_secret", 
    "secret_key", 
    "password", 
    "token",
    "auth_token",
    "access_token",
    "refresh_token",
    "private_key"
]


def encrypt_sensitive_config_fields(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Encrypt sensitive fields in integration configuration.
    
    Args:
        config: The integration configuration dictionary
        
    Returns:
        Updated configuration with sensitive fields encrypted
    """
    if not config:
        return config
        
    encryption_key = get_app_encryption_key()
    encrypted_config = config.copy()
    
    # Encrypt top-level sensitive fields
    for field in SENSITIVE_CONFIG_FIELDS:
        if field in encrypted_config and encrypted_config[field]:
            encrypted_config[field] = encrypt_sensitive_value(
                str(encrypted_config[field]), 
                encryption_key
            )
    
    # Check for nested objects that might contain sensitive fields
    for key, value in encrypted_config.items():
        if isinstance(value, dict):
            encrypted_config[key] = encrypt_sensitive_config_fields(value)
            
    return encrypted_config


def decrypt_sensitive_config_fields(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decrypt sensitive fields in integration configuration.
    
    Args:
        config: The integration configuration dictionary with encrypted fields
        
    Returns:
        Configuration with sensitive fields decrypted
    """
    if not config:
        return config
        
    encryption_key = get_app_encryption_key()
    decrypted_config = config.copy()
    
    # Decrypt top-level sensitive fields
    for field in SENSITIVE_CONFIG_FIELDS:
        if field in decrypted_config and decrypted_config[field]:
            try:
                decrypted_config[field] = decrypt_sensitive_value(
                    decrypted_config[field], 
                    encryption_key
                )
            except Exception:
                # If decryption fails, it might not be encrypted yet
                pass
    
    # Check for nested objects that might contain sensitive fields
    for key, value in decrypted_config.items():
        if isinstance(value, dict):
            decrypted_config[key] = decrypt_sensitive_config_fields(value)
            
    return decrypted_config


def create_integration(
    db: Session, 
    obj_in: IntegrationCreate, 
    user_id: UUID
) -> Integration:
    """
    Create a new integration with encrypted sensitive config fields.
    
    Args:
        db: Database session
        obj_in: Integration creation schema
        user_id: ID of the user creating the integration
        
    Returns:
        Created integration object
    """
    # Encrypt sensitive fields in config
    if obj_in.config:
        encrypted_config = encrypt_sensitive_config_fields(obj_in.config)
        # Create a new object with the updated config
        obj_in_data = obj_in.dict()
        obj_in_data["config"] = encrypted_config
        obj_in_encrypted = IntegrationCreate(**obj_in_data)
        integration = crud.integration.create(db=db, obj_in=obj_in_encrypted, user_id=user_id)
    else:
        integration = crud.integration.create(db=db, obj_in=obj_in, user_id=user_id)
    
    # Return integration with decrypted config
    return decrypt_integration_config(integration)


def update_integration(
    db: Session,
    db_obj: Any,
    obj_in: IntegrationUpdate,
    user_id: UUID
) -> Integration:
    """
    Update an integration with encrypted sensitive config fields.
    
    Args:
        db: Database session
        db_obj: Existing integration object from database
        obj_in: Integration update schema
        user_id: ID of the user updating the integration
        
    Returns:
        Updated integration object
    """
    # If we're updating the config, encrypt sensitive fields
    update_data = obj_in.dict(exclude_unset=True)
    
    if "config" in update_data and update_data["config"]:
        update_data["config"] = encrypt_sensitive_config_fields(update_data["config"])
        obj_in_encrypted = IntegrationUpdate(**update_data)
        integration = crud.integration.update(db=db, db_obj=db_obj, obj_in=obj_in_encrypted, user_id=user_id)
    else:
        integration = crud.integration.update(db=db, db_obj=db_obj, obj_in=obj_in, user_id=user_id)
    
    # Return integration with decrypted config
    return decrypt_integration_config(integration)


def get_integration(
    db: Session,
    integration_id: UUID
) -> Optional[Integration]:
    """
    Get an integration by ID with decrypted config.
    
    Args:
        db: Database session
        integration_id: ID of the integration to retrieve
        
    Returns:
        Integration object with decrypted sensitive config fields
    """
    integration = crud.integration.get(db=db, integration_id=integration_id)
    if not integration:
        return None
        
    return decrypt_integration_config(integration)


def get_integrations(
    db: Session,
    skip: int = 0,
    limit: int = 100
) -> List[Integration]:
    """
    Get multiple integrations with decrypted configs.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of integration objects with decrypted sensitive config fields
    """
    integrations = crud.integration.get_multi(db=db, skip=skip, limit=limit)
    return [decrypt_integration_config(integration) for integration in integrations]


def decrypt_integration_config(integration: Any) -> Any:
    """
    Decrypt sensitive fields in an integration's config.
    
    Args:
        integration: Integration object from database
        
    Returns:
        Integration with decrypted config
    """
    # Don't modify the original object
    integration_dict = {
        key: getattr(integration, key) 
        for key in integration.__dict__ 
        if not key.startswith('_')
    }
    
    if "config" in integration_dict and integration_dict["config"]:
        integration_dict["config"] = decrypt_sensitive_config_fields(integration_dict["config"])
        
    return Integration(**integration_dict) 