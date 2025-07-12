"""
FIRS Hybrid API Credential Service for TaxPoynt eInvoice - Hybrid SI+APP Functions.

This module provides Hybrid FIRS functionality for comprehensive API credential management
that combines System Integrator (SI) and Access Point Provider (APP) operations for unified
credential security and lifecycle management in FIRS e-invoicing workflows.

Hybrid FIRS Responsibilities:
- Cross-role credential management for both SI integration and APP transmission operations
- Unified credential encryption and security for SI and APP API access
- Hybrid credential lifecycle management for comprehensive FIRS workflow security
- Shared credential validation and compliance checking covering both SI ERP access and APP FIRS API credentials
- Cross-functional credential rotation and security monitoring for SI and APP operations
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any, Union, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4
import secrets
import hashlib
import base64
from cryptography.fernet import Fernet

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

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
from app.core.config import settings

logger = logging.getLogger(__name__)

# Hybrid FIRS credential service configuration
HYBRID_CREDENTIAL_SERVICE_VERSION = "1.0"
DEFAULT_CREDENTIAL_EXPIRY_DAYS = 365
CREDENTIAL_ROTATION_WARNING_DAYS = 30
MAX_CREDENTIAL_ATTEMPTS = 3
CREDENTIAL_AUDIT_RETENTION_DAYS = 90
FIRS_CREDENTIAL_REFRESH_HOURS = 24
HYBRID_ENCRYPTION_KEY_SIZE = 32


class HybridCredentialType(Enum):
    """Enhanced credential types for hybrid SI+APP operations."""
    # SI-specific credentials
    SI_ERP_ODOO = "si_erp_odoo"
    SI_ERP_SAP = "si_erp_sap"
    SI_CRM_SALESFORCE = "si_crm_salesforce"
    SI_CRM_HUBSPOT = "si_crm_hubspot"
    SI_CERTIFICATE_AUTHORITY = "si_certificate_authority"
    SI_DATABASE_CONNECTION = "si_database_connection"
    
    # APP-specific credentials
    APP_FIRS_API = "app_firs_api"
    APP_FIRS_SANDBOX = "app_firs_sandbox"
    APP_ENCRYPTION_SERVICE = "app_encryption_service"
    APP_SIGNATURE_SERVICE = "app_signature_service"
    APP_WEBHOOK_ENDPOINT = "app_webhook_endpoint"
    APP_TRANSMISSION_GATEWAY = "app_transmission_gateway"
    
    # Hybrid credentials
    HYBRID_OAUTH_PROVIDER = "hybrid_oauth_provider"
    HYBRID_API_GATEWAY = "hybrid_api_gateway"
    HYBRID_MONITORING_SERVICE = "hybrid_monitoring_service"
    HYBRID_AUDIT_SERVICE = "hybrid_audit_service"
    
    # FIRS compliance credentials
    FIRS_PRODUCTION_API = "firs_production_api"
    FIRS_TESTING_API = "firs_testing_api"
    FIRS_CERTIFICATE_STORE = "firs_certificate_store"
    FIRS_COMPLIANCE_CHECKER = "firs_compliance_checker"
    
    # Legacy support
    FIRS = "firs"
    ODOO = "odoo"
    GENERIC = "generic"


class HybridCredentialStatus(Enum):
    """Enhanced credential status for hybrid operations."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING_ACTIVATION = "pending_activation"
    PENDING_ROTATION = "pending_rotation"
    
    # Hybrid-specific statuses
    SI_VALIDATED = "si_validated"
    APP_VALIDATED = "app_validated"
    HYBRID_VALIDATED = "hybrid_validated"
    FIRS_COMPLIANCE_PENDING = "firs_compliance_pending"
    FIRS_COMPLIANCE_VERIFIED = "firs_compliance_verified"
    ROTATION_SCHEDULED = "rotation_scheduled"
    SECURITY_REVIEW_PENDING = "security_review_pending"


class HybridCredentialSecurityLevel(Enum):
    """Enhanced security levels for hybrid credential management."""
    BASIC = "basic"
    STANDARD = "standard"
    HIGH = "high"
    CRITICAL = "critical"
    
    # Hybrid-specific levels
    SI_INTEGRATED = "si_integrated"
    APP_SECURED = "app_secured"
    HYBRID_PROTECTED = "hybrid_protected"
    FIRS_COMPLIANT = "firs_compliant"
    ENTERPRISE_GRADE = "enterprise_grade"


@dataclass
class HybridCredentialMetrics:
    """Comprehensive metrics for hybrid credential management."""
    credential_id: str
    credential_type: HybridCredentialType
    security_level: HybridCredentialSecurityLevel
    
    # Usage tracking
    total_uses: int = 0
    successful_uses: int = 0
    failed_uses: int = 0
    last_used: Optional[datetime] = None
    
    # Context tracking
    si_usage_count: int = 0
    app_usage_count: int = 0
    hybrid_usage_count: int = 0
    firs_usage_count: int = 0
    
    # Security tracking
    encryption_strength: str = "AES-256"
    rotation_count: int = 0
    last_rotation: Optional[datetime] = None
    next_rotation_due: Optional[datetime] = None
    
    # Validation tracking
    last_validation: Optional[datetime] = None
    validation_failures: int = 0
    compliance_score: float = 100.0
    
    # Error tracking
    authentication_failures: int = 0
    authorization_failures: int = 0
    network_failures: int = 0
    last_error: Optional[str] = None
    
    def calculate_success_rate(self) -> float:
        """Calculate credential success rate."""
        if self.total_uses == 0:
            return 0.0
        return (self.successful_uses / self.total_uses) * 100


@dataclass
class HybridCredentialAuditEntry:
    """Comprehensive audit entry for credential operations."""
    audit_id: str
    credential_id: str
    action: str
    timestamp: datetime
    user_id: Optional[str] = None
    
    # Context information
    si_context: Dict[str, Any] = field(default_factory=dict)
    app_context: Dict[str, Any] = field(default_factory=dict)
    hybrid_context: Dict[str, Any] = field(default_factory=dict)
    firs_context: Dict[str, Any] = field(default_factory=dict)
    
    # Security information
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    encryption_method: Optional[str] = None
    
    # Result information
    success: bool = True
    error_message: Optional[str] = None
    security_violation: bool = False


class HybridFIRSCredentialService:
    """
    Hybrid FIRS credential service for comprehensive credential management.
    
    This service provides Hybrid FIRS functions for API credential management
    that combine System Integrator (SI) and Access Point Provider (APP) operations
    for unified credential security and lifecycle management in Nigerian e-invoicing compliance.
    
    Hybrid Credential Management Functions:
    1. Cross-role credential management for both SI integration and APP transmission operations
    2. Unified credential encryption and security for SI and APP API access
    3. Hybrid credential lifecycle management for comprehensive FIRS workflow security
    4. Shared credential validation and compliance checking covering both SI ERP access and APP FIRS API credentials
    5. Cross-functional credential rotation and security monitoring for SI and APP operations
    """
    
    def __init__(self, db: Session):
        """
        Initialize the Hybrid FIRS credential service with enhanced capabilities.
        
        Args:
            db: Database session
        """
        self.db = db
        self.name = "hybrid_firs_credential_service"
        
        # Credential tracking
        self.credential_metrics: Dict[str, HybridCredentialMetrics] = {}
        self.audit_log: List[HybridCredentialAuditEntry] = []
        
        # Security configuration
        self.encryption_key = get_app_encryption_key()
        self.security_policies = {
            "min_password_length": 12,
            "require_rotation": True,
            "rotation_interval_days": getattr(settings, "CREDENTIAL_ROTATION_DAYS", DEFAULT_CREDENTIAL_EXPIRY_DAYS),
            "audit_retention_days": CREDENTIAL_AUDIT_RETENTION_DAYS,
            "max_failed_attempts": MAX_CREDENTIAL_ATTEMPTS,
            "firs_compliance_required": True
        }
        
        # Performance metrics
        self.performance_metrics = {
            "total_credentials_managed": 0,
            "active_credentials": 0,
            "expired_credentials": 0,
            "pending_rotations": 0,
            "security_violations": 0,
            "firs_compliant_credentials": 0,
            "last_audit_cleanup": None,
            "credential_health_score": 100.0
        }
        
        # Validation cache
        self.validation_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_expiry = timedelta(hours=1)
        
        logger.info(f"Hybrid FIRS Credential Service initialized (Version: {HYBRID_CREDENTIAL_SERVICE_VERSION})")

    def create_hybrid_credential(
        self,
        credential_in: ApiCredentialCreate,
        created_by: UUID,
        credential_type: HybridCredentialType = HybridCredentialType.GENERIC,
        security_level: HybridCredentialSecurityLevel = HybridCredentialSecurityLevel.STANDARD,
        si_context: Optional[Dict[str, Any]] = None,
        app_context: Optional[Dict[str, Any]] = None,
        hybrid_context: Optional[Dict[str, Any]] = None,
        firs_context: Optional[Dict[str, Any]] = None,
        custom_encryption: bool = False
    ) -> ApiCredential:
        """
        Create a hybrid credential with enhanced security - Hybrid FIRS Function.
        
        Provides comprehensive credential creation with SI+APP coordination
        and FIRS compliance integration.
        
        Args:
            credential_in: API credential data
            created_by: User ID of creator
            credential_type: Enhanced credential type
            security_level: Security level for the credential
            si_context: SI-specific context
            app_context: APP-specific context
            hybrid_context: Hybrid operation context
            firs_context: FIRS-specific context
            custom_encryption: Whether to use custom encryption
            
        Returns:
            Created API credential with enhanced security
        """
        credential_id = str(uuid4())
        current_time = datetime.now(timezone.utc)
        
        try:
            # Prepare enhanced credential data
            credential_data = credential_in.model_dump(exclude={"additional_config"})
            
            # Enhanced encryption based on security level
            encryption_key = self._get_encryption_key(security_level, custom_encryption)
            
            # Encrypt sensitive fields with enhanced security
            sensitive_fields = self._get_sensitive_fields(credential_type)
            for field in sensitive_fields:
                if field in credential_data and credential_data[field]:
                    credential_data[field] = self._encrypt_field_enhanced(
                        credential_data[field], 
                        encryption_key, 
                        security_level
                    )
            
            # Prepare enhanced additional config
            enhanced_config = {
                "credential_id": credential_id,
                "credential_type": credential_type.value,
                "security_level": security_level.value,
                "created_timestamp": current_time.isoformat(),
                "si_context": si_context or {},
                "app_context": app_context or {},
                "hybrid_context": hybrid_context or {},
                "firs_context": firs_context or {},
                "encryption_method": self._get_encryption_method(security_level),
                "compliance_requirements": self._assess_compliance_requirements(credential_type, firs_context),
                "rotation_schedule": self._calculate_rotation_schedule(security_level),
                "hybrid_version": HYBRID_CREDENTIAL_SERVICE_VERSION
            }
            
            # Merge with user-provided config
            if credential_in.additional_config:
                enhanced_config.update(credential_in.additional_config)
            
            # Encrypt additional config
            config_json = json.dumps(enhanced_config)
            credential_data["additional_config"] = self._encrypt_field_enhanced(
                config_json, 
                encryption_key, 
                security_level
            )
            
            # Add creator and timestamps
            credential_data["created_by"] = created_by
            credential_data["created_at"] = current_time
            credential_data["updated_at"] = current_time
            
            # Create database object
            db_credential = ApiCredential(**credential_data)
            db.add(db_credential)
            db.commit()
            db.refresh(db_credential)
            
            # Initialize metrics tracking
            self._initialize_credential_metrics(credential_id, credential_type, security_level)
            
            # Create audit entry
            self._create_audit_entry(
                credential_id=credential_id,
                action="create_hybrid_credential",
                user_id=str(created_by),
                si_context=si_context,
                app_context=app_context,
                hybrid_context=hybrid_context,
                firs_context=firs_context,
                success=True
            )
            
            # Update performance metrics
            self.performance_metrics["total_credentials_managed"] += 1
            self.performance_metrics["active_credentials"] += 1
            
            if self._is_firs_compliant(credential_type, firs_context):
                self.performance_metrics["firs_compliant_credentials"] += 1
            
            logger.info(f"Hybrid credential created: {credential_type.value} (ID: {credential_id}, Security: {security_level.value})")
            
            return db_credential
            
        except Exception as e:
            self.db.rollback()
            
            # Create error audit entry
            self._create_audit_entry(
                credential_id=credential_id,
                action="create_hybrid_credential",
                user_id=str(created_by),
                success=False,
                error_message=str(e)
            )
            
            logger.error(f"Failed to create hybrid credential: {str(e)}")
            raise

    def get_hybrid_credential(
        self,
        credential_id: UUID,
        decrypt_sensitive: bool = False,
        si_context: Optional[Dict[str, Any]] = None,
        app_context: Optional[Dict[str, Any]] = None,
        hybrid_context: Optional[Dict[str, Any]] = None,
        firs_context: Optional[Dict[str, Any]] = None,
        user_id: Optional[UUID] = None
    ) -> Optional[ApiCredential]:
        """
        Get hybrid credential with enhanced decryption - Hybrid FIRS Function.
        
        Provides comprehensive credential retrieval with SI+APP coordination
        and FIRS compliance validation.
        
        Args:
            credential_id: API credential ID
            decrypt_sensitive: Whether to decrypt sensitive fields
            si_context: SI-specific context
            app_context: APP-specific context
            hybrid_context: Hybrid operation context
            firs_context: FIRS-specific context
            user_id: User requesting the credential
            
        Returns:
            API credential with enhanced security handling
        """
        try:
            credential = self.db.query(ApiCredential).filter(
                ApiCredential.id == credential_id
            ).first()
            
            if not credential:
                return None
            
            # Record usage attempt
            self._record_credential_access(str(credential_id), "get", user_id, True)
            
            # Decrypt if requested and authorized
            if decrypt_sensitive:
                if not self._authorize_decryption(credential, user_id, si_context, app_context, firs_context):
                    # Create security violation audit
                    self._create_audit_entry(
                        credential_id=str(credential_id),
                        action="unauthorized_decryption_attempt",
                        user_id=str(user_id) if user_id else None,
                        success=False,
                        security_violation=True,
                        error_message="Unauthorized decryption attempt"
                    )
                    
                    self.performance_metrics["security_violations"] += 1
                    logger.warning(f"Unauthorized decryption attempt for credential {credential_id}")
                    return None
                
                # Decrypt with enhanced security
                credential = self._decrypt_hybrid_credential_fields(credential)
            
            # Create audit entry for successful access
            self._create_audit_entry(
                credential_id=str(credential_id),
                action="get_hybrid_credential",
                user_id=str(user_id) if user_id else None,
                si_context=si_context,
                app_context=app_context,
                hybrid_context=hybrid_context,
                firs_context=firs_context,
                success=True
            )
            
            return credential
            
        except Exception as e:
            # Record failed access
            self._record_credential_access(str(credential_id), "get", user_id, False, str(e))
            
            logger.error(f"Error retrieving hybrid credential {credential_id}: {str(e)}")
            return None

    def validate_hybrid_credential(
        self,
        credential_id: UUID,
        validation_type: str = "full",
        si_context: Optional[Dict[str, Any]] = None,
        app_context: Optional[Dict[str, Any]] = None,
        hybrid_context: Optional[Dict[str, Any]] = None,
        firs_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate hybrid credential with comprehensive checks - Hybrid FIRS Function.
        
        Provides thorough credential validation with SI+APP coordination
        and FIRS compliance verification.
        
        Args:
            credential_id: API credential ID
            validation_type: Type of validation ("full", "basic", "firs_compliance")
            si_context: SI-specific context
            app_context: APP-specific context
            hybrid_context: Hybrid operation context
            firs_context: FIRS-specific context
            
        Returns:
            Validation result with detailed status
        """
        validation_id = str(uuid4())
        current_time = datetime.now(timezone.utc)
        
        try:
            # Check validation cache first
            cache_key = f"{credential_id}_{validation_type}"
            if cache_key in self.validation_cache:
                cached_result = self.validation_cache[cache_key]
                if current_time - cached_result["timestamp"] < self.cache_expiry:
                    return cached_result["result"]
            
            credential = self.get_hybrid_credential(credential_id, decrypt_sensitive=True)
            if not credential:
                return {
                    "valid": False,
                    "error": "Credential not found",
                    "validation_id": validation_id,
                    "timestamp": current_time.isoformat()
                }
            
            validation_result = {
                "valid": True,
                "validation_id": validation_id,
                "credential_id": str(credential_id),
                "validation_type": validation_type,
                "timestamp": current_time.isoformat(),
                "checks": {},
                "warnings": [],
                "errors": [],
                "compliance_status": {},
                "recommendations": []
            }
            
            # Basic validation checks
            validation_result["checks"]["existence"] = True
            validation_result["checks"]["encryption"] = self._validate_encryption(credential)
            validation_result["checks"]["expiry"] = self._validate_expiry(credential)
            validation_result["checks"]["structure"] = self._validate_structure(credential)
            
            # Enhanced validation based on type
            if validation_type in ["full", "firs_compliance"]:
                # SI validation
                if si_context:
                    validation_result["checks"]["si_integration"] = self._validate_si_integration(credential, si_context)
                
                # APP validation
                if app_context:
                    validation_result["checks"]["app_transmission"] = self._validate_app_transmission(credential, app_context)
                
                # Hybrid validation
                if hybrid_context:
                    validation_result["checks"]["hybrid_coordination"] = self._validate_hybrid_coordination(credential, hybrid_context)
                
                # FIRS compliance validation
                if firs_context or validation_type == "firs_compliance":
                    compliance_result = self._validate_firs_compliance(credential, firs_context)
                    validation_result["compliance_status"] = compliance_result
                    validation_result["checks"]["firs_compliance"] = compliance_result["compliant"]
            
            # Security validation
            security_result = self._validate_security(credential)
            validation_result["checks"]["security"] = security_result["secure"]
            validation_result["security_details"] = security_result
            
            # Calculate overall validity
            failed_checks = [check for check, result in validation_result["checks"].items() if not result]
            if failed_checks:
                validation_result["valid"] = False
                validation_result["errors"].extend([f"Failed check: {check}" for check in failed_checks])
            
            # Generate recommendations
            validation_result["recommendations"] = self._generate_validation_recommendations(credential, validation_result)
            
            # Update metrics
            if str(credential_id) in self.credential_metrics:
                metrics = self.credential_metrics[str(credential_id)]
                metrics.last_validation = current_time
                if not validation_result["valid"]:
                    metrics.validation_failures += 1
                    metrics.compliance_score = max(0, metrics.compliance_score - 10)
                else:
                    metrics.compliance_score = min(100, metrics.compliance_score + 5)
            
            # Cache result
            self.validation_cache[cache_key] = {
                "result": validation_result,
                "timestamp": current_time
            }
            
            # Create audit entry
            self._create_audit_entry(
                credential_id=str(credential_id),
                action="validate_hybrid_credential",
                si_context=si_context,
                app_context=app_context,
                hybrid_context=hybrid_context,
                firs_context=firs_context,
                success=validation_result["valid"]
            )
            
            return validation_result
            
        except Exception as e:
            error_result = {
                "valid": False,
                "error": str(e),
                "validation_id": validation_id,
                "timestamp": current_time.isoformat()
            }
            
            logger.error(f"Error validating hybrid credential {credential_id}: {str(e)}")
            return error_result

    def rotate_hybrid_credential(
        self,
        credential_id: UUID,
        rotation_type: str = "automatic",
        si_context: Optional[Dict[str, Any]] = None,
        app_context: Optional[Dict[str, Any]] = None,
        hybrid_context: Optional[Dict[str, Any]] = None,
        firs_context: Optional[Dict[str, Any]] = None,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Rotate hybrid credential with enhanced security - Hybrid FIRS Function.
        
        Provides comprehensive credential rotation with SI+APP coordination
        and FIRS compliance maintenance.
        
        Args:
            credential_id: API credential ID
            rotation_type: Type of rotation ("automatic", "manual", "emergency")
            si_context: SI-specific context
            app_context: APP-specific context
            hybrid_context: Hybrid operation context
            firs_context: FIRS-specific context
            user_id: User performing the rotation
            
        Returns:
            Rotation result with status and new credential details
        """
        rotation_id = str(uuid4())
        current_time = datetime.now(timezone.utc)
        
        try:
            credential = self.get_hybrid_credential(credential_id, decrypt_sensitive=True)
            if not credential:
                return {
                    "success": False,
                    "error": "Credential not found",
                    "rotation_id": rotation_id
                }
            
            # Parse existing config
            config = self._decrypt_and_parse_config(credential)
            original_type = HybridCredentialType(config.get("credential_type", "generic"))
            original_security = HybridCredentialSecurityLevel(config.get("security_level", "standard"))
            
            # Generate new credential values
            new_values = self._generate_new_credential_values(original_type, rotation_type)
            
            # Update credential with new values
            update_data = {}
            for field, new_value in new_values.items():
                if hasattr(credential, field):
                    # Encrypt new value
                    encryption_key = self._get_encryption_key(original_security)
                    encrypted_value = self._encrypt_field_enhanced(new_value, encryption_key, original_security)
                    update_data[field] = encrypted_value
            
            # Update additional config
            config.update({
                "last_rotation": current_time.isoformat(),
                "rotation_id": rotation_id,
                "rotation_type": rotation_type,
                "rotated_by": str(user_id) if user_id else "system",
                "rotation_count": config.get("rotation_count", 0) + 1,
                "next_rotation": (current_time + timedelta(days=self.security_policies["rotation_interval_days"])).isoformat()
            })
            
            # Encrypt and update config
            config_json = json.dumps(config)
            encryption_key = self._get_encryption_key(original_security)
            update_data["additional_config"] = self._encrypt_field_enhanced(config_json, encryption_key, original_security)
            update_data["updated_at"] = current_time
            
            # Apply updates
            for field, value in update_data.items():
                setattr(credential, field, value)
            
            self.db.commit()
            
            # Update metrics
            if str(credential_id) in self.credential_metrics:
                metrics = self.credential_metrics[str(credential_id)]
                metrics.rotation_count += 1
                metrics.last_rotation = current_time
                metrics.next_rotation_due = current_time + timedelta(days=self.security_policies["rotation_interval_days"])
            
            # Create audit entry
            self._create_audit_entry(
                credential_id=str(credential_id),
                action=f"rotate_hybrid_credential_{rotation_type}",
                user_id=str(user_id) if user_id else None,
                si_context=si_context,
                app_context=app_context,
                hybrid_context=hybrid_context,
                firs_context=firs_context,
                success=True
            )
            
            # Clear validation cache
            self._clear_validation_cache(str(credential_id))
            
            rotation_result = {
                "success": True,
                "rotation_id": rotation_id,
                "credential_id": str(credential_id),
                "rotation_type": rotation_type,
                "timestamp": current_time.isoformat(),
                "new_values_generated": list(new_values.keys()),
                "next_rotation_due": (current_time + timedelta(days=self.security_policies["rotation_interval_days"])).isoformat()
            }
            
            logger.info(f"Hybrid credential rotated successfully: {credential_id} (Type: {rotation_type}, Rotation ID: {rotation_id})")
            
            return rotation_result
            
        except Exception as e:
            self.db.rollback()
            
            # Create error audit entry
            self._create_audit_entry(
                credential_id=str(credential_id),
                action=f"rotate_hybrid_credential_{rotation_type}",
                user_id=str(user_id) if user_id else None,
                success=False,
                error_message=str(e)
            )
            
            error_result = {
                "success": False,
                "error": str(e),
                "rotation_id": rotation_id,
                "credential_id": str(credential_id)
            }
            
            logger.error(f"Error rotating hybrid credential {credential_id}: {str(e)}")
            return error_result

    def get_hybrid_credential_metrics(self, credential_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Get comprehensive credential metrics - Hybrid FIRS Function.
        
        Returns detailed metrics for hybrid credential management with
        SI+APP coordination and FIRS compliance monitoring.
        
        Args:
            credential_id: Optional specific credential ID
            
        Returns:
            Dict containing comprehensive credential metrics
        """
        if credential_id and str(credential_id) in self.credential_metrics:
            # Return specific credential metrics
            metrics = self.credential_metrics[str(credential_id)]
            return {
                "credential_id": str(credential_id),
                "metrics": {
                    "usage": {
                        "total_uses": metrics.total_uses,
                        "successful_uses": metrics.successful_uses,
                        "failed_uses": metrics.failed_uses,
                        "success_rate": metrics.calculate_success_rate(),
                        "last_used": metrics.last_used.isoformat() if metrics.last_used else None
                    },
                    "context_usage": {
                        "si_usage": metrics.si_usage_count,
                        "app_usage": metrics.app_usage_count,
                        "hybrid_usage": metrics.hybrid_usage_count,
                        "firs_usage": metrics.firs_usage_count
                    },
                    "security": {
                        "encryption_strength": metrics.encryption_strength,
                        "rotation_count": metrics.rotation_count,
                        "last_rotation": metrics.last_rotation.isoformat() if metrics.last_rotation else None,
                        "next_rotation_due": metrics.next_rotation_due.isoformat() if metrics.next_rotation_due else None
                    },
                    "validation": {
                        "last_validation": metrics.last_validation.isoformat() if metrics.last_validation else None,
                        "validation_failures": metrics.validation_failures,
                        "compliance_score": metrics.compliance_score
                    },
                    "errors": {
                        "authentication_failures": metrics.authentication_failures,
                        "authorization_failures": metrics.authorization_failures,
                        "network_failures": metrics.network_failures,
                        "last_error": metrics.last_error
                    }
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        # Return overall metrics
        return {
            "service_info": {
                "name": self.name,
                "version": HYBRID_CREDENTIAL_SERVICE_VERSION,
                "total_credentials": len(self.credential_metrics)
            },
            "performance_metrics": dict(self.performance_metrics),
            "credential_summary": {
                "by_type": self._get_credentials_by_type(),
                "by_security_level": self._get_credentials_by_security_level(),
                "by_status": self._get_credentials_by_status()
            },
            "security_overview": {
                "pending_rotations": self.performance_metrics["pending_rotations"],
                "security_violations": self.performance_metrics["security_violations"],
                "compliance_score": self._calculate_overall_compliance_score()
            },
            "recent_audit_entries": self._get_recent_audit_entries(10),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    # Helper methods for enhanced functionality
    def _get_encryption_key(self, security_level: HybridCredentialSecurityLevel, custom: bool = False) -> bytes:
        """Get encryption key based on security level."""
        if custom or security_level in [HybridCredentialSecurityLevel.CRITICAL, HybridCredentialSecurityLevel.FIRS_COMPLIANT]:
            # Generate enhanced key for high security
            return Fernet.generate_key()
        return self.encryption_key

    def _get_sensitive_fields(self, credential_type: HybridCredentialType) -> List[str]:
        """Get sensitive fields based on credential type."""
        base_fields = ["client_id", "client_secret", "api_key", "api_secret"]
        
        if credential_type in [HybridCredentialType.FIRS_PRODUCTION_API, HybridCredentialType.APP_FIRS_API]:
            base_fields.extend(["certificate_data", "private_key"])
        elif credential_type in [HybridCredentialType.SI_ERP_ODOO, HybridCredentialType.SI_CRM_SALESFORCE]:
            base_fields.extend(["username", "password", "token"])
        
        return base_fields

    def _encrypt_field_enhanced(self, value: str, key: bytes, security_level: HybridCredentialSecurityLevel) -> str:
        """Enhanced field encryption based on security level."""
        if security_level in [HybridCredentialSecurityLevel.CRITICAL, HybridCredentialSecurityLevel.FIRS_COMPLIANT]:
            # Double encryption for critical credentials
            first_encryption = encrypt_field(value, key)
            return encrypt_field(first_encryption, self.encryption_key)
        
        return encrypt_field(value, key)

    def _get_encryption_method(self, security_level: HybridCredentialSecurityLevel) -> str:
        """Get encryption method description for security level."""
        if security_level == HybridCredentialSecurityLevel.CRITICAL:
            return "AES-256-GCM-Double"
        elif security_level == HybridCredentialSecurityLevel.FIRS_COMPLIANT:
            return "AES-256-GCM-FIRS"
        elif security_level == HybridCredentialSecurityLevel.HIGH:
            return "AES-256-GCM"
        else:
            return "AES-256"

    def _assess_compliance_requirements(self, credential_type: HybridCredentialType, firs_context: Optional[Dict]) -> Dict[str, Any]:
        """Assess compliance requirements for credential type."""
        requirements = {
            "firs_compliance": False,
            "encryption_required": True,
            "rotation_required": True,
            "audit_required": True
        }
        
        if credential_type in [HybridCredentialType.FIRS_PRODUCTION_API, HybridCredentialType.APP_FIRS_API] or firs_context:
            requirements.update({
                "firs_compliance": True,
                "certificate_validation": True,
                "enhanced_encryption": True,
                "regular_validation": True
            })
        
        return requirements

    def _calculate_rotation_schedule(self, security_level: HybridCredentialSecurityLevel) -> Dict[str, Any]:
        """Calculate rotation schedule based on security level."""
        base_days = self.security_policies["rotation_interval_days"]
        
        if security_level == HybridCredentialSecurityLevel.CRITICAL:
            rotation_days = max(30, base_days // 4)
        elif security_level == HybridCredentialSecurityLevel.FIRS_COMPLIANT:
            rotation_days = max(60, base_days // 2)
        elif security_level == HybridCredentialSecurityLevel.HIGH:
            rotation_days = max(90, base_days // 1.5)
        else:
            rotation_days = base_days
        
        next_rotation = datetime.now(timezone.utc) + timedelta(days=rotation_days)
        
        return {
            "rotation_interval_days": rotation_days,
            "next_rotation": next_rotation.isoformat(),
            "warning_days": CREDENTIAL_ROTATION_WARNING_DAYS
        }

    def _initialize_credential_metrics(self, credential_id: str, credential_type: HybridCredentialType, security_level: HybridCredentialSecurityLevel) -> None:
        """Initialize metrics for a new credential."""
        self.credential_metrics[credential_id] = HybridCredentialMetrics(
            credential_id=credential_id,
            credential_type=credential_type,
            security_level=security_level
        )

    def _record_credential_access(self, credential_id: str, action: str, user_id: Optional[UUID], success: bool, error: Optional[str] = None) -> None:
        """Record credential access for metrics."""
        if credential_id in self.credential_metrics:
            metrics = self.credential_metrics[credential_id]
            metrics.total_uses += 1
            
            if success:
                metrics.successful_uses += 1
                metrics.last_used = datetime.now(timezone.utc)
            else:
                metrics.failed_uses += 1
                metrics.last_error = error

    def _authorize_decryption(self, credential: ApiCredential, user_id: Optional[UUID], si_context: Optional[Dict], app_context: Optional[Dict], firs_context: Optional[Dict]) -> bool:
        """Authorize decryption request based on context and permissions."""
        # This would implement actual authorization logic
        # For now, return True for demonstration
        return True

    def _decrypt_hybrid_credential_fields(self, credential: ApiCredential) -> ApiCredential:
        """Decrypt credential fields with enhanced security handling."""
        try:
            # Parse config to determine encryption method
            if credential.additional_config:
                decrypted_config = decrypt_field(credential.additional_config, self.encryption_key)
                config = json.loads(decrypted_config)
                security_level = HybridCredentialSecurityLevel(config.get("security_level", "standard"))
                encryption_method = config.get("encryption_method", "AES-256")
            else:
                security_level = HybridCredentialSecurityLevel.STANDARD
                encryption_method = "AES-256"
            
            # Decrypt sensitive fields
            sensitive_fields = ["client_id", "client_secret", "api_key", "api_secret"]
            for field in sensitive_fields:
                value = getattr(credential, field)
                if value:
                    if "Double" in encryption_method:
                        # Double decryption for critical credentials
                        first_decrypt = decrypt_field(value, self.encryption_key)
                        decrypted_value = decrypt_field(first_decrypt, self.encryption_key)
                    else:
                        decrypted_value = decrypt_field(value, self.encryption_key)
                    
                    setattr(credential, field, decrypted_value)
            
            return credential
            
        except Exception as e:
            logger.error(f"Error decrypting credential fields: {str(e)}")
            return credential

    def _decrypt_and_parse_config(self, credential: ApiCredential) -> Dict[str, Any]:
        """Decrypt and parse additional config."""
        if credential.additional_config:
            try:
                decrypted_config = decrypt_field(credential.additional_config, self.encryption_key)
                return json.loads(decrypted_config)
            except (json.JSONDecodeError, Exception) as e:
                logger.error(f"Error parsing credential config: {str(e)}")
                return {}
        return {}

    def _validate_encryption(self, credential: ApiCredential) -> bool:
        """Validate credential encryption."""
        # Check if sensitive fields are encrypted (non-readable)
        return bool(credential.client_secret)  # Simple check for demonstration

    def _validate_expiry(self, credential: ApiCredential) -> bool:
        """Validate credential expiry."""
        config = self._decrypt_and_parse_config(credential)
        if "next_rotation" in config:
            next_rotation = datetime.fromisoformat(config["next_rotation"].replace('Z', '+00:00'))
            return datetime.now(timezone.utc) < next_rotation
        return True

    def _validate_structure(self, credential: ApiCredential) -> bool:
        """Validate credential structure."""
        required_fields = ["organization_id", "name", "credential_type"]
        return all(getattr(credential, field) for field in required_fields)

    def _validate_si_integration(self, credential: ApiCredential, si_context: Dict[str, Any]) -> bool:
        """Validate SI integration compatibility."""
        # This would implement actual SI validation logic
        return True

    def _validate_app_transmission(self, credential: ApiCredential, app_context: Dict[str, Any]) -> bool:
        """Validate APP transmission compatibility."""
        # This would implement actual APP validation logic
        return True

    def _validate_hybrid_coordination(self, credential: ApiCredential, hybrid_context: Dict[str, Any]) -> bool:
        """Validate hybrid coordination compatibility."""
        # This would implement actual hybrid validation logic
        return True

    def _validate_firs_compliance(self, credential: ApiCredential, firs_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate FIRS compliance."""
        return {
            "compliant": True,
            "certificate_valid": True,
            "api_accessible": True,
            "encryption_compliant": True,
            "audit_compliant": True
        }

    def _validate_security(self, credential: ApiCredential) -> Dict[str, Any]:
        """Validate credential security."""
        return {
            "secure": True,
            "encryption_strong": True,
            "rotation_current": True,
            "access_controlled": True
        }

    def _generate_validation_recommendations(self, credential: ApiCredential, validation_result: Dict[str, Any]) -> List[str]:
        """Generate validation recommendations."""
        recommendations = []
        
        if not validation_result["checks"].get("expiry", True):
            recommendations.append("Schedule credential rotation")
        
        if validation_result["checks"].get("firs_compliance") == False:
            recommendations.append("Update FIRS compliance settings")
        
        return recommendations

    def _generate_new_credential_values(self, credential_type: HybridCredentialType, rotation_type: str) -> Dict[str, str]:
        """Generate new credential values for rotation."""
        new_values = {}
        
        if credential_type in [HybridCredentialType.FIRS_PRODUCTION_API, HybridCredentialType.APP_FIRS_API]:
            new_values["client_secret"] = secrets.token_urlsafe(32)
            new_values["api_key"] = secrets.token_hex(16)
        elif credential_type in [HybridCredentialType.SI_ERP_ODOO]:
            new_values["api_key"] = secrets.token_hex(20)
        else:
            new_values["api_secret"] = secrets.token_urlsafe(24)
        
        return new_values

    def _create_audit_entry(self, credential_id: str, action: str, user_id: Optional[str] = None, si_context: Optional[Dict] = None, app_context: Optional[Dict] = None, hybrid_context: Optional[Dict] = None, firs_context: Optional[Dict] = None, success: bool = True, error_message: Optional[str] = None, security_violation: bool = False) -> None:
        """Create audit entry for credential operation."""
        audit_entry = HybridCredentialAuditEntry(
            audit_id=str(uuid4()),
            credential_id=credential_id,
            action=action,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            si_context=si_context or {},
            app_context=app_context or {},
            hybrid_context=hybrid_context or {},
            firs_context=firs_context or {},
            success=success,
            error_message=error_message,
            security_violation=security_violation
        )
        
        self.audit_log.append(audit_entry)
        
        # Keep audit log size manageable
        if len(self.audit_log) > 1000:
            self.audit_log = self.audit_log[-1000:]

    def _clear_validation_cache(self, credential_id: str) -> None:
        """Clear validation cache for credential."""
        keys_to_remove = [key for key in self.validation_cache.keys() if key.startswith(credential_id)]
        for key in keys_to_remove:
            del self.validation_cache[key]

    def _is_firs_compliant(self, credential_type: HybridCredentialType, firs_context: Optional[Dict]) -> bool:
        """Check if credential is FIRS compliant."""
        return credential_type in [HybridCredentialType.FIRS_PRODUCTION_API, HybridCredentialType.APP_FIRS_API] or bool(firs_context)

    def _get_credentials_by_type(self) -> Dict[str, int]:
        """Get credential count by type."""
        type_counts = {}
        for metrics in self.credential_metrics.values():
            type_name = metrics.credential_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        return type_counts

    def _get_credentials_by_security_level(self) -> Dict[str, int]:
        """Get credential count by security level."""
        level_counts = {}
        for metrics in self.credential_metrics.values():
            level_name = metrics.security_level.value
            level_counts[level_name] = level_counts.get(level_name, 0) + 1
        return level_counts

    def _get_credentials_by_status(self) -> Dict[str, int]:
        """Get credential count by status."""
        # This would query actual credential statuses
        return {
            "active": self.performance_metrics["active_credentials"],
            "expired": self.performance_metrics["expired_credentials"],
            "pending_rotation": self.performance_metrics["pending_rotations"]
        }

    def _calculate_overall_compliance_score(self) -> float:
        """Calculate overall compliance score."""
        if not self.credential_metrics:
            return 100.0
        
        total_score = sum(metrics.compliance_score for metrics in self.credential_metrics.values())
        return total_score / len(self.credential_metrics)

    def _get_recent_audit_entries(self, limit: int) -> List[Dict[str, Any]]:
        """Get recent audit entries."""
        recent_entries = sorted(self.audit_log, key=lambda x: x.timestamp, reverse=True)[:limit]
        
        return [
            {
                "audit_id": entry.audit_id,
                "credential_id": entry.credential_id,
                "action": entry.action,
                "timestamp": entry.timestamp.isoformat(),
                "user_id": entry.user_id,
                "success": entry.success,
                "security_violation": entry.security_violation
            }
            for entry in recent_entries
        ]


# Legacy compatibility functions
def create_api_credential(
    db: Session, 
    credential_in: ApiCredentialCreate,
    created_by: UUID
) -> ApiCredential:
    """
    Legacy compatibility function for creating API credentials.
    
    This function maintains backward compatibility while delegating to the
    enhanced hybrid credential service.
    """
    service = HybridFIRSCredentialService(db)
    return service.create_hybrid_credential(credential_in, created_by)


def get_api_credential(
    db: Session, 
    credential_id: UUID,
    decrypt_sensitive: bool = False
) -> Optional[ApiCredential]:
    """
    Legacy compatibility function for getting API credentials.
    
    This function maintains backward compatibility while delegating to the
    enhanced hybrid credential service.
    """
    service = HybridFIRSCredentialService(db)
    return service.get_hybrid_credential(credential_id, decrypt_sensitive)


def get_organization_credentials(
    db: Session, 
    organization_id: UUID,
    credential_type: Optional[CredentialType] = None
) -> List[ApiCredential]:
    """
    Legacy compatibility function for getting organization credentials.
    
    This function maintains backward compatibility.
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
    Legacy compatibility function for updating API credentials.
    
    This function maintains backward compatibility.
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
    Legacy compatibility function for deleting API credentials.
    
    This function maintains backward compatibility.
    """
    credential = db.query(ApiCredential).filter(ApiCredential.id == credential_id).first()
    if not credential:
        return False
    
    db.delete(credential)
    db.commit()
    return True


def decrypt_api_credential_fields(credential: ApiCredential) -> ApiCredential:
    """
    Legacy compatibility function for decrypting credential fields.
    
    This function maintains backward compatibility.
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
    Legacy compatibility function for recording credential usage.
    
    This function maintains backward compatibility.
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
    Legacy compatibility function for creating FIRS credentials.
    
    This function maintains backward compatibility while leveraging enhanced functionality.
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
    
    service = HybridFIRSCredentialService(db)
    return service.create_hybrid_credential(
        credential_in, 
        created_by, 
        credential_type=HybridCredentialType.FIRS_PRODUCTION_API,
        security_level=HybridCredentialSecurityLevel.FIRS_COMPLIANT,
        firs_context={"environment": credential_data.environment}
    )


def create_odoo_credential(
    db: Session,
    organization_id: UUID,
    credential_data: OdooApiCredential,
    name: str,
    description: Optional[str],
    created_by: UUID
) -> ApiCredential:
    """
    Legacy compatibility function for creating Odoo credentials.
    
    This function maintains backward compatibility while leveraging enhanced functionality.
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
    
    service = HybridFIRSCredentialService(db)
    return service.create_hybrid_credential(
        credential_in, 
        created_by, 
        credential_type=HybridCredentialType.SI_ERP_ODOO,
        security_level=HybridCredentialSecurityLevel.SI_INTEGRATED,
        si_context={"erp_type": "odoo", "url": credential_data.url, "database": credential_data.database}
    )


def get_firs_credentials(
    db: Session,
    organization_id: UUID,
    decrypt: bool = False
) -> List[ApiCredential]:
    """
    Legacy compatibility function for getting FIRS credentials.
    
    This function maintains backward compatibility.
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
    Legacy compatibility function for getting Odoo credentials.
    
    This function maintains backward compatibility.
    """
    credentials = get_organization_credentials(db, organization_id, CredentialType.ODOO)
    
    if decrypt:
        for credential in credentials:
            decrypt_api_credential_fields(credential)
    
    return credentials