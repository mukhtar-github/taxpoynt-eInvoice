"""
Integration Credential Connector Service

This service connects integrations with securely stored API credentials,
enabling integrations to use credentials without directly storing sensitive information.
"""
from typing import Dict, Any, Optional, List, Union
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.integration import Integration, IntegrationType
from app.models.api_credential import ApiCredential, CredentialType
from app.schemas.api_credential import ApiCredentialCreate, OdooApiCredential
from app.services.api_credential_service import (
    create_api_credential, get_api_credential, 
    create_odoo_credential, get_organization_credentials
)


def associate_credentials_with_integration(
    db: Session,
    integration_id: UUID,
    credentials_id: UUID
) -> bool:
    """
    Associate API credentials with an integration.
    
    Args:
        db: Database session
        integration_id: ID of the integration
        credentials_id: ID of the API credentials to associate
        
    Returns:
        True if association was successful, False otherwise
    """
    integration = db.query(Integration).filter(Integration.id == integration_id).first()
    if not integration:
        raise ValueError(f"Integration not found: {integration_id}")
    
    credential = db.query(ApiCredential).filter(ApiCredential.id == credentials_id).first()
    if not credential:
        raise ValueError(f"API credential not found: {credentials_id}")
    
    # Update the integration config to reference the credential
    config = integration.config.copy() if integration.config else {}
    
    # Store just the credential ID, not the sensitive details
    config["api_credential_id"] = str(credentials_id)
    integration.config = config
    
    # Set the config as encrypted since it now contains credential references
    integration.config_encrypted = True
    
    db.commit()
    return True


def create_credentials_from_integration_config(
    db: Session,
    integration_id: UUID,
    created_by: UUID
) -> ApiCredential:
    """
    Create API credentials from integration configuration.
    
    This extracts sensitive data from the integration config and
    creates a proper API credential entry for it.
    
    Args:
        db: Database session
        integration_id: ID of the integration
        created_by: ID of the user creating the credential
        
    Returns:
        Created API credential
    """
    integration = db.query(Integration).filter(Integration.id == integration_id).first()
    if not integration:
        raise ValueError(f"Integration not found: {integration_id}")
    
    # Get client organization_id through the integration's client relationship
    organization_id = integration.client.organization_id
    
    # Determine credential type based on integration type
    credential_type = None
    if integration.integration_type == IntegrationType.ODOO:
        credential_type = CredentialType.ODOO
    else:
        credential_type = CredentialType.OTHER
    
    # Extract sensitive data from integration config
    config = integration.config or {}
    
    if credential_type == CredentialType.ODOO:
        # Extract Odoo-specific credentials
        odoo_credential = OdooApiCredential(
            url=config.get("url", ""),
            database=config.get("database", ""),
            username=config.get("username", ""),
            auth_method=config.get("auth_method", "api_key"),
            password=config.get("password") if config.get("auth_method") == "password" else None,
            api_key=config.get("api_key") if config.get("auth_method") == "api_key" else None
        )
        
        # Create Odoo credential
        credential = create_odoo_credential(
            db=db,
            organization_id=organization_id,
            credential_data=odoo_credential,
            name=f"Odoo Credential for {integration.name}",
            description=f"Automatically created from integration {integration.name}",
            created_by=created_by
        )
        
    else:
        # Create generic credential for other integration types
        credential_create = ApiCredentialCreate(
            organization_id=organization_id,
            name=f"Credential for {integration.name}",
            description=f"Automatically created from integration {integration.name}",
            credential_type=credential_type,
            client_id=config.get("client_id"),
            client_secret=config.get("client_secret"),
            api_key=config.get("api_key"),
            api_secret=config.get("api_secret")
        )
        
        credential = create_api_credential(
            db=db,
            credential_in=credential_create,
            created_by=created_by
        )
    
    # Associate the new credential with the integration
    associate_credentials_with_integration(db, integration_id, credential.id)
    
    return credential


def get_credentials_for_integration(
    db: Session,
    integration_id: UUID
) -> Optional[ApiCredential]:
    """
    Get API credentials associated with an integration.
    
    Args:
        db: Database session
        integration_id: ID of the integration
        
    Returns:
        Associated API credential or None if not found
    """
    integration = db.query(Integration).filter(Integration.id == integration_id).first()
    if not integration:
        raise ValueError(f"Integration not found: {integration_id}")
    
    # Check if there's a credential ID in the config
    config = integration.config or {}
    credential_id = config.get("api_credential_id")
    
    if not credential_id:
        return None
    
    # Get the credential
    try:
        credential = get_api_credential(db, UUID(credential_id))
        return credential
    except (ValueError, TypeError):
        # Invalid UUID format
        return None


def migrate_integration_credentials_to_secure_storage(
    db: Session,
    integration_id: UUID,
    created_by: UUID
) -> ApiCredential:
    """
    Migrate sensitive credentials from an integration to secure storage.
    
    This is useful for legacy integrations that have sensitive data
    stored directly in their config.
    
    Args:
        db: Database session
        integration_id: ID of the integration
        created_by: ID of the user performing the migration
        
    Returns:
        Created API credential
    """
    integration = db.query(Integration).filter(Integration.id == integration_id).first()
    if not integration:
        raise ValueError(f"Integration not found: {integration_id}")
    
    # Check if the integration already uses secure credentials
    config = integration.config or {}
    if config.get("api_credential_id"):
        credential = get_credentials_for_integration(db, integration_id)
        if credential:
            return credential
    
    # Create new credentials from the integration config
    credential = create_credentials_from_integration_config(db, integration_id, created_by)
    
    # Remove sensitive data from the integration config
    new_config = config.copy()
    sensitive_fields = [
        "password", "api_key", "api_secret", "client_secret", 
        "auth_token", "access_token", "refresh_token"
    ]
    
    for field in sensitive_fields:
        if field in new_config:
            del new_config[field]
    
    # Update the integration with the cleaned config
    integration.config = new_config
    db.commit()
    
    return credential
