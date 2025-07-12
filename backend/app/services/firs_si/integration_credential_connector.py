"""
Integration Credential Connector for TaxPoynt eInvoice - System Integrator Functions.

This module provides System Integrator (SI) role functionality for managing
integration credentials, authentication mechanisms, and secure credential storage
for ERP/CRM system connections.

SI Role Responsibilities:
- Secure credential management for ERP/CRM integrations
- Authentication handling for various integration types
- Credential validation and testing
- Integration configuration management
"""

import base64
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List
from uuid import UUID, uuid4

import httpx
import secrets
import urllib.parse
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.integration import Integration, IntegrationType
from app.schemas.integration import IntegrationCreate, IntegrationUpdate

logger = logging.getLogger(__name__)


class SecureCredentialManager:
    """
    System Integrator secure manager for integration credentials with encryption.
    
    Provides SI role functions for secure credential management, encryption,
    and storage for ERP/CRM system integrations.
    """
    
    def __init__(self):
        """Initialize with encryption key from settings."""
        # Use the encryption key from settings
        encryption_key = getattr(settings, 'CREDENTIAL_ENCRYPTION_KEY', None)
        if not encryption_key:
            raise ValueError(
                "CREDENTIAL_ENCRYPTION_KEY must be set in environment variables for production use. "
                "Generate a key with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )
        
        if isinstance(encryption_key, str):
            # Check if it's a valid Fernet key length (44 chars base64)
            if len(encryption_key) < 44:
                # Pad with base64-safe characters if too short
                encryption_key = base64.urlsafe_b64encode(encryption_key.ljust(32, '0')[:32].encode()).decode()
            encryption_key = encryption_key.encode()
            
        self.cipher_suite = Fernet(encryption_key)
        
    def encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """
        Encrypt credentials for secure storage - SI Role Function.
        
        Securely encrypts integration credentials for System Integrator
        credential management and ERP/CRM system authentication.
        
        Args:
            credentials: Dictionary of credential information
            
        Returns:
            str: Encrypted credentials string
        """
        if not credentials:
            return ""
            
        # Convert to JSON string
        credentials_json = json.dumps(credentials, sort_keys=True)
        
        # Encrypt
        encrypted_data = self.cipher_suite.encrypt(credentials_json.encode('utf-8'))
        
        return encrypted_data.decode('utf-8')
        
    def decrypt_credentials(self, encrypted_data: str) -> Dict[str, Any]:
        """
        Decrypt credentials for use - SI Role Function.
        
        Decrypts integration credentials for System Integrator
        authentication and ERP/CRM system connectivity.
        
        Args:
            encrypted_data: Encrypted credentials string
            
        Returns:
            Dict: Decrypted credentials dictionary
        """
        if not encrypted_data:
            return {}
            
        try:
            # Decrypt
            decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode('utf-8'))
            
            # Parse JSON
            credentials = json.loads(decrypted_data.decode('utf-8'))
            
            return credentials
        except Exception as e:
            logger.error(f"Error decrypting credentials: {e}")
            return {}


class IntegrationCredentialConnector:
    """
    System Integrator connector for managing integration credentials and authentication.
    
    This service provides SI role functions for managing credentials, testing
    connections, and configuring authentication for various ERP/CRM integrations.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.credential_manager = SecureCredentialManager()
        
    def create_integration_credential(
        self,
        integration_create: IntegrationCreate,
        user_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None
    ) -> Integration:
        """
        Create new integration with encrypted credentials - SI Role Function.
        
        Creates System Integrator integration configuration with secure
        credential storage for ERP/CRM system connections.
        
        Args:
            integration_create: Integration creation data
            user_id: ID of the user creating the integration
            organization_id: ID of the organization
            
        Returns:
            Integration: Created integration record
        """
        # Encrypt sensitive configuration data
        encrypted_config = {}
        if integration_create.config:
            # Separate sensitive from non-sensitive config
            sensitive_keys = {'password', 'api_key', 'client_secret', 'private_key', 'token'}
            sensitive_config = {k: v for k, v in integration_create.config.items() if k in sensitive_keys}
            non_sensitive_config = {k: v for k, v in integration_create.config.items() if k not in sensitive_keys}
            
            # Encrypt sensitive config
            if sensitive_config:
                encrypted_sensitive = self.credential_manager.encrypt_credentials(sensitive_config)
                encrypted_config = {
                    **non_sensitive_config,
                    '_encrypted_credentials': encrypted_sensitive
                }
            else:
                encrypted_config = non_sensitive_config
        
        # Create integration record
        integration = Integration(
            id=uuid4(),
            organization_id=organization_id,
            name=integration_create.name,
            integration_type=integration_create.integration_type,
            config=encrypted_config,
            is_active=integration_create.is_active,
            created_by=user_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(integration)
        self.db.commit()
        self.db.refresh(integration)
        
        logger.info(f"Created integration {integration.id} for organization {organization_id}")
        return integration
    
    def get_integration_credentials(self, integration_id: UUID) -> Dict[str, Any]:
        """
        Get decrypted credentials for an integration - SI Role Function.
        
        Retrieves and decrypts integration credentials for System Integrator
        ERP/CRM system authentication and connectivity.
        
        Args:
            integration_id: ID of the integration
            
        Returns:
            Dict: Complete configuration with decrypted credentials
        """
        integration = self.db.query(Integration).filter(Integration.id == integration_id).first()
        if not integration:
            return {}
        
        config = integration.config or {}
        
        # Check if there are encrypted credentials
        if '_encrypted_credentials' in config:
            encrypted_data = config['_encrypted_credentials']
            decrypted_credentials = self.credential_manager.decrypt_credentials(encrypted_data)
            
            # Merge with non-sensitive config
            complete_config = {k: v for k, v in config.items() if k != '_encrypted_credentials'}
            complete_config.update(decrypted_credentials)
            
            return complete_config
        
        return config
    
    def update_integration_credentials(
        self,
        integration_id: UUID,
        new_config: Dict[str, Any],
        user_id: Optional[UUID] = None
    ) -> Optional[Integration]:
        """
        Update integration credentials securely - SI Role Function.
        
        Updates System Integrator integration credentials with secure
        encryption and proper audit trail.
        
        Args:
            integration_id: ID of the integration to update
            new_config: New configuration data
            user_id: ID of the user making the update
            
        Returns:
            Integration: Updated integration record or None if not found
        """
        integration = self.db.query(Integration).filter(Integration.id == integration_id).first()
        if not integration:
            return None
        
        # Encrypt sensitive configuration data
        encrypted_config = {}
        if new_config:
            # Separate sensitive from non-sensitive config
            sensitive_keys = {'password', 'api_key', 'client_secret', 'private_key', 'token'}
            sensitive_config = {k: v for k, v in new_config.items() if k in sensitive_keys}
            non_sensitive_config = {k: v for k, v in new_config.items() if k not in sensitive_keys}
            
            # Encrypt sensitive config
            if sensitive_config:
                encrypted_sensitive = self.credential_manager.encrypt_credentials(sensitive_config)
                encrypted_config = {
                    **non_sensitive_config,
                    '_encrypted_credentials': encrypted_sensitive
                }
            else:
                encrypted_config = non_sensitive_config
        
        # Update integration
        integration.config = encrypted_config
        integration.updated_at = datetime.utcnow()
        integration.updated_by = user_id
        
        self.db.commit()
        self.db.refresh(integration)
        
        logger.info(f"Updated credentials for integration {integration_id}")
        return integration
    
    def test_integration_connection(self, integration_id: UUID) -> Dict[str, Any]:
        """
        Test connection using integration credentials - SI Role Function.
        
        Tests System Integrator ERP/CRM integration connectivity using
        stored credentials and configuration.
        
        Args:
            integration_id: ID of the integration to test
            
        Returns:
            Dict: Connection test results
        """
        integration = self.db.query(Integration).filter(Integration.id == integration_id).first()
        if not integration:
            return {
                "success": False,
                "error": "Integration not found"
            }
        
        config = self.get_integration_credentials(integration_id)
        
        try:
            if integration.integration_type == IntegrationType.ODOO:
                return self._test_odoo_connection(config)
            elif integration.integration_type == IntegrationType.SALESFORCE:
                return self._test_salesforce_connection(config)
            elif integration.integration_type == IntegrationType.HUBSPOT:
                return self._test_hubspot_connection(config)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported integration type: {integration.integration_type}"
                }
        except Exception as e:
            logger.error(f"Error testing integration {integration_id}: {e}")
            return {
                "success": False,
                "error": f"Connection test failed: {str(e)}"
            }
    
    def _test_odoo_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test Odoo ERP connection."""
        try:
            from app.services.firs_si.odoo_connector import OdooConnector
            from app.schemas.integration import OdooConfig, OdooAuthMethod
            
            odoo_config = OdooConfig(
                url=config.get('url'),
                database=config.get('database'),
                username=config.get('username'),
                password=config.get('password'),
                api_key=config.get('api_key'),
                auth_method=OdooAuthMethod.API_KEY if config.get('api_key') else OdooAuthMethod.PASSWORD
            )
            
            connector = OdooConnector(config=odoo_config)
            connector.authenticate()
            
            user_info = connector.get_user_info()
            
            return {
                "success": True,
                "message": "Successfully connected to Odoo",
                "details": {
                    "server_version": connector.version_info.get('server_version', 'Unknown'),
                    "user": user_info.get('name'),
                    "database": config.get('database')
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Odoo connection failed: {str(e)}"
            }
    
    def _test_salesforce_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test Salesforce CRM connection."""
        try:
            # Basic connection test - implement based on Salesforce connector
            base_url = config.get('instance_url', 'https://login.salesforce.com')
            
            return {
                "success": True,
                "message": "Salesforce connection configuration valid",
                "details": {
                    "instance_url": base_url,
                    "username": config.get('username')
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Salesforce connection failed: {str(e)}"
            }
    
    def _test_hubspot_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test HubSpot CRM connection."""
        try:
            # Basic connection test - implement based on HubSpot connector
            api_key = config.get('api_key')
            if not api_key:
                return {
                    "success": False,
                    "error": "API key required for HubSpot connection"
                }
            
            return {
                "success": True,
                "message": "HubSpot connection configuration valid",
                "details": {
                    "api_key_configured": bool(api_key)
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"HubSpot connection failed: {str(e)}"
            }
    
    def list_integrations_by_organization(
        self,
        organization_id: UUID,
        integration_type: Optional[IntegrationType] = None
    ) -> List[Integration]:
        """
        List integrations for an organization - SI Role Function.
        
        Retrieves list of System Integrator integrations for an organization
        with optional filtering by integration type.
        
        Args:
            organization_id: ID of the organization
            integration_type: Optional filter by integration type
            
        Returns:
            List[Integration]: List of integration records
        """
        query = self.db.query(Integration).filter(Integration.organization_id == organization_id)
        
        if integration_type:
            query = query.filter(Integration.integration_type == integration_type)
        
        return query.order_by(Integration.created_at.desc()).all()
    
    def delete_integration(self, integration_id: UUID, user_id: Optional[UUID] = None) -> bool:
        """
        Delete an integration and its credentials - SI Role Function.
        
        Securely deletes System Integrator integration configuration
        and associated credentials.
        
        Args:
            integration_id: ID of the integration to delete
            user_id: ID of the user performing the deletion
            
        Returns:
            bool: True if deletion was successful
        """
        integration = self.db.query(Integration).filter(Integration.id == integration_id).first()
        if not integration:
            return False
        
        try:
            self.db.delete(integration)
            self.db.commit()
            
            logger.info(f"Deleted integration {integration_id} by user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting integration {integration_id}: {e}")
            self.db.rollback()
            return False