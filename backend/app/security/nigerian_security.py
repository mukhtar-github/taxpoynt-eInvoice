"""
Enhanced Nigerian Security Framework
Implements multi-factor authentication and security controls for Nigerian compliance
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass
from uuid import UUID, uuid4
import secrets
import hashlib
import hmac
import pyotp
import qrcode
import io
import base64
import logging
from sqlalchemy.orm import Session

from ..core.config import settings
from ..services.comprehensive_audit_service import (
    ComprehensiveAuditService,
    AuditEventType,
    AuditOutcome
)

logger = logging.getLogger(__name__)


class MFAMethod(str, Enum):
    """Multi-factor authentication methods"""
    SMS = "sms"
    EMAIL = "email"
    TOTP = "totp"  # Time-based One-Time Password (Google Authenticator, etc.)
    BIOMETRIC = "biometric"
    BACKUP_CODES = "backup_codes"
    NIGERIAN_USSD = "nigerian_ussd"  # Nigerian USSD-based verification


class BiometricType(str, Enum):
    """Supported biometric authentication types"""
    FINGERPRINT = "fingerprint"
    FACE_RECOGNITION = "face_recognition"
    VOICE_RECOGNITION = "voice_recognition"


class SecurityLevel(str, Enum):
    """Security levels for different operations"""
    BASIC = "basic"           # Single factor
    ENHANCED = "enhanced"     # Two factors
    HIGH = "high"            # Three factors
    CRITICAL = "critical"    # Four factors + biometric


@dataclass
class MFAConfig:
    """Multi-factor authentication configuration"""
    user_id: str
    primary_method: MFAMethod
    secondary_methods: List[MFAMethod]
    sms_verification: bool = False
    email_verification: bool = False
    totp_enabled: bool = False
    biometric_support: bool = False
    backup_codes: List[str] = None
    nigerian_phone_number: Optional[str] = None
    security_level: SecurityLevel = SecurityLevel.BASIC
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.utcnow()


@dataclass
class AuditRecord:
    """Audit record for security events"""
    user_id: UUID
    action: str
    timestamp: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    session_id: Optional[str]
    data_classification: str
    retention_period: timedelta


class NigerianSecurityFramework:
    """Enhanced security framework for Nigerian compliance."""
    
    def __init__(self):
        self.encryption_standard = "AES-256-GCM"
        self.key_management = "HSM-backed"
        self.audit_retention = timedelta(days=2555)  # 7 years
        self.audit_service = ComprehensiveAuditService()
        
        # Nigerian mobile network providers for SMS/USSD
        self.nigerian_networks = {
            "mtn": {"prefix": ["0803", "0806", "0813", "0816", "0903", "0906"], "ussd_code": "*123#"},
            "airtel": {"prefix": ["0802", "0808", "0812", "0901", "0902"], "ussd_code": "*141#"},
            "glo": {"prefix": ["0805", "0807", "0815", "0811", "0905"], "ussd_code": "*777#"},
            "9mobile": {"prefix": ["0809", "0817", "0818", "0908", "0909"], "ussd_code": "*200#"}
        }
    
    async def implement_mfa(
        self, 
        user_id: UUID, 
        nigerian_phone: Optional[str] = None,
        security_level: SecurityLevel = SecurityLevel.ENHANCED,
        db: Optional[Session] = None
    ) -> MFAConfig:
        """Implement multi-factor authentication for Nigerian users."""
        
        user_id_str = str(user_id)
        
        # Determine appropriate MFA methods based on security level
        primary_method, secondary_methods = self._determine_mfa_methods(
            security_level, 
            nigerian_phone
        )
        
        # Generate backup codes
        backup_codes = self._generate_backup_codes()
        
        # Create MFA configuration
        mfa_config = MFAConfig(
            user_id=user_id_str,
            primary_method=primary_method,
            secondary_methods=secondary_methods,
            sms_verification=MFAMethod.SMS in secondary_methods,
            email_verification=MFAMethod.EMAIL in secondary_methods,
            totp_enabled=MFAMethod.TOTP in secondary_methods,
            biometric_support=MFAMethod.BIOMETRIC in secondary_methods,
            backup_codes=backup_codes,
            nigerian_phone_number=nigerian_phone,
            security_level=security_level
        )
        
        # Generate TOTP secret if enabled
        if mfa_config.totp_enabled:
            totp_secret = await self._setup_totp(user_id_str)
            mfa_config.totp_secret = totp_secret
        
        # Store MFA configuration
        await self._store_mfa_config(mfa_config, db)
        
        # Audit MFA setup
        await self.audit_user_activity(
            user_id=user_id,
            action="mfa_enabled",
            additional_data={
                "security_level": security_level.value,
                "methods": [method.value for method in secondary_methods],
                "nigerian_phone": bool(nigerian_phone)
            },
            db=db
        )
        
        logger.info(f"MFA implemented for user {user_id_str} with security level {security_level.value}")
        
        return mfa_config
    
    def _determine_mfa_methods(
        self, 
        security_level: SecurityLevel, 
        nigerian_phone: Optional[str]
    ) -> tuple[MFAMethod, List[MFAMethod]]:
        """Determine appropriate MFA methods based on security level."""
        
        if security_level == SecurityLevel.BASIC:
            primary = MFAMethod.EMAIL
            secondary = [MFAMethod.EMAIL]
        
        elif security_level == SecurityLevel.ENHANCED:
            primary = MFAMethod.SMS if nigerian_phone else MFAMethod.EMAIL
            secondary = [MFAMethod.SMS, MFAMethod.EMAIL, MFAMethod.BACKUP_CODES]
            if nigerian_phone:
                secondary.append(MFAMethod.NIGERIAN_USSD)
        
        elif security_level == SecurityLevel.HIGH:
            primary = MFAMethod.TOTP
            secondary = [
                MFAMethod.TOTP, 
                MFAMethod.SMS, 
                MFAMethod.EMAIL, 
                MFAMethod.BACKUP_CODES
            ]
            if nigerian_phone:
                secondary.append(MFAMethod.NIGERIAN_USSD)
        
        else:  # CRITICAL
            primary = MFAMethod.BIOMETRIC
            secondary = [
                MFAMethod.BIOMETRIC,
                MFAMethod.TOTP,
                MFAMethod.SMS,
                MFAMethod.EMAIL,
                MFAMethod.BACKUP_CODES
            ]
            if nigerian_phone:
                secondary.append(MFAMethod.NIGERIAN_USSD)
        
        return primary, secondary
    
    def _generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate secure backup codes for MFA recovery."""
        
        backup_codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric code
            code = secrets.token_urlsafe(6)[:8].upper()
            backup_codes.append(code)
        
        return backup_codes
    
    async def _setup_totp(self, user_id: str) -> Dict[str, str]:
        """Setup TOTP (Time-based One-Time Password) for user."""
        
        # Generate secret key
        secret = pyotp.random_base32()
        
        # Create TOTP instance
        totp = pyotp.TOTP(secret)
        
        # Generate QR code for authenticator apps
        provisioning_uri = totp.provisioning_uri(
            name=user_id,
            issuer_name="TaxPoynt Nigerian e-Invoice"
        )
        
        # Generate QR code image
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for frontend display
        img_buffer = io.BytesIO()
        qr_image.save(img_buffer, format='PNG')
        qr_code_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        return {
            "secret": secret,
            "qr_code": qr_code_base64,
            "manual_entry_key": secret,
            "backup_url": provisioning_uri
        }
    
    async def verify_mfa_token(
        self,
        user_id: UUID,
        method: MFAMethod,
        token: str,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Verify MFA token for various methods."""
        
        user_id_str = str(user_id)
        verification_result = {
            "success": False,
            "method": method.value,
            "message": "",
            "remaining_attempts": 3
        }
        
        try:
            # Load user's MFA configuration
            mfa_config = await self._load_mfa_config(user_id_str, db)
            
            if not mfa_config:
                verification_result["message"] = "MFA not configured for user"
                return verification_result
            
            # Verify based on method
            if method == MFAMethod.TOTP:
                success = await self._verify_totp(mfa_config, token)
            elif method == MFAMethod.SMS:
                success = await self._verify_sms_token(user_id_str, token)
            elif method == MFAMethod.EMAIL:
                success = await self._verify_email_token(user_id_str, token)
            elif method == MFAMethod.BACKUP_CODES:
                success = await self._verify_backup_code(mfa_config, token, db)
            elif method == MFAMethod.NIGERIAN_USSD:
                success = await self._verify_ussd_token(mfa_config, token)
            else:
                verification_result["message"] = f"Unsupported MFA method: {method.value}"
                return verification_result
            
            verification_result["success"] = success
            verification_result["message"] = "Verification successful" if success else "Invalid token"
            
            # Audit verification attempt
            await self.audit_user_activity(
                user_id=user_id,
                action="mfa_verification",
                additional_data={
                    "method": method.value,
                    "success": success,
                    "token_length": len(token)
                },
                outcome=AuditOutcome.SUCCESS if success else AuditOutcome.FAILURE,
                db=db
            )
            
        except Exception as e:
            logger.error(f"MFA verification failed for user {user_id_str}: {str(e)}")
            verification_result["message"] = "Verification failed due to system error"
            
            # Audit system error
            await self.audit_user_activity(
                user_id=user_id,
                action="mfa_verification_error",
                additional_data={"error": str(e), "method": method.value},
                outcome=AuditOutcome.FAILURE,
                db=db
            )
        
        return verification_result
    
    async def _verify_totp(self, mfa_config: MFAConfig, token: str) -> bool:
        """Verify TOTP token."""
        
        if not hasattr(mfa_config, 'totp_secret'):
            return False
        
        try:
            totp = pyotp.TOTP(mfa_config.totp_secret)
            return totp.verify(token, valid_window=1)  # Allow 30-second window
        except Exception:
            return False
    
    async def _verify_sms_token(self, user_id: str, token: str) -> bool:
        """Verify SMS token (simplified implementation)."""
        
        # In production, this would verify against stored SMS tokens
        # For now, simulate verification
        stored_token = await self._get_stored_token(user_id, "sms")
        return stored_token == token
    
    async def _verify_email_token(self, user_id: str, token: str) -> bool:
        """Verify email token (simplified implementation)."""
        
        # In production, this would verify against stored email tokens
        stored_token = await self._get_stored_token(user_id, "email")
        return stored_token == token
    
    async def _verify_backup_code(
        self, 
        mfa_config: MFAConfig, 
        code: str, 
        db: Optional[Session]
    ) -> bool:
        """Verify and consume backup code."""
        
        if not mfa_config.backup_codes or code not in mfa_config.backup_codes:
            return False
        
        # Remove used backup code
        mfa_config.backup_codes.remove(code)
        await self._store_mfa_config(mfa_config, db)
        
        return True
    
    async def _verify_ussd_token(self, mfa_config: MFAConfig, token: str) -> bool:
        """Verify Nigerian USSD-based token."""
        
        if not mfa_config.nigerian_phone_number:
            return False
        
        # In production, this would integrate with Nigerian mobile networks
        # to verify USSD-generated tokens
        network = self._detect_nigerian_network(mfa_config.nigerian_phone_number)
        
        if not network:
            return False
        
        # Simulate USSD verification
        stored_token = await self._get_stored_token(mfa_config.user_id, "ussd")
        return stored_token == token
    
    def _detect_nigerian_network(self, phone_number: str) -> Optional[str]:
        """Detect Nigerian mobile network from phone number."""
        
        # Remove country code and spaces
        clean_phone = phone_number.replace("+234", "").replace(" ", "").replace("-", "")
        
        if len(clean_phone) >= 4:
            prefix = clean_phone[:4]
            
            for network, data in self.nigerian_networks.items():
                if prefix in data["prefix"]:
                    return network
        
        return None
    
    async def _get_stored_token(self, user_id: str, method: str) -> Optional[str]:
        """Get stored verification token (simplified implementation)."""
        
        # In production, this would retrieve from secure storage/cache
        # For now, return None to simulate no stored token
        return None
    
    async def _store_mfa_config(self, mfa_config: MFAConfig, db: Optional[Session]):
        """Store MFA configuration securely."""
        
        try:
            # In production, this would store in encrypted database table
            logger.info(f"MFA config stored for user {mfa_config.user_id}")
            
            # Simulate secure storage
            config_data = {
                "user_id": mfa_config.user_id,
                "security_level": mfa_config.security_level.value,
                "methods_enabled": len(mfa_config.secondary_methods),
                "backup_codes_remaining": len(mfa_config.backup_codes) if mfa_config.backup_codes else 0
            }
            
            logger.info(f"MFA configuration: {config_data}")
            
        except Exception as e:
            logger.error(f"Failed to store MFA config: {str(e)}")
            raise
    
    async def _load_mfa_config(self, user_id: str, db: Optional[Session]) -> Optional[MFAConfig]:
        """Load MFA configuration for user."""
        
        try:
            # In production, this would load from database
            # For now, return a default configuration
            return MFAConfig(
                user_id=user_id,
                primary_method=MFAMethod.EMAIL,
                secondary_methods=[MFAMethod.EMAIL, MFAMethod.BACKUP_CODES],
                email_verification=True,
                backup_codes=["ABC123", "DEF456", "GHI789"],
                security_level=SecurityLevel.ENHANCED
            )
            
        except Exception as e:
            logger.error(f"Failed to load MFA config for user {user_id}: {str(e)}")
            return None
    
    async def audit_user_activity(
        self, 
        user_id: UUID, 
        action: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None,
        outcome: AuditOutcome = AuditOutcome.SUCCESS,
        db: Optional[Session] = None
    ):
        """Comprehensive audit logging for compliance."""
        
        # Map action to audit event type
        event_type_mapping = {
            "mfa_enabled": AuditEventType.AUTHENTICATION,
            "mfa_disabled": AuditEventType.AUTHENTICATION,
            "mfa_verification": AuditEventType.AUTHENTICATION,
            "login_attempt": AuditEventType.AUTHENTICATION,
            "password_change": AuditEventType.AUTHENTICATION,
            "security_alert": AuditEventType.SECURITY_EVENT,
            "data_access": AuditEventType.DATA_ACCESS,
            "configuration_change": AuditEventType.CONFIGURATION_CHANGE
        }
        
        event_type = event_type_mapping.get(action, AuditEventType.SYSTEM_ACCESS)
        
        # Create comprehensive audit record
        audit_record = await self.audit_service.log_audit_event(
            event_type=event_type,
            event_description=f"User {action} - {additional_data.get('description', '')}",
            outcome=outcome,
            user_id=str(user_id),
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            additional_data=additional_data,
            db=db
        )
        
        logger.info(f"User activity audited: {audit_record.audit_id}")
    
    async def generate_nigerian_security_report(
        self,
        organization_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generate Nigerian-specific security compliance report."""
        
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        report = {
            "report_id": str(uuid4()),
            "generated_at": datetime.utcnow().isoformat(),
            "organization_id": organization_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "mfa_metrics": {
                "users_with_mfa": 0,
                "mfa_adoption_rate": 0.0,
                "nigerian_phone_verification": 0,
                "totp_usage": 0,
                "backup_codes_used": 0
            },
            "security_events": {
                "total_login_attempts": 0,
                "successful_logins": 0,
                "failed_logins": 0,
                "mfa_challenges": 0,
                "mfa_failures": 0,
                "security_alerts": 0
            },
            "nigerian_compliance": {
                "ndpr_events": 0,
                "data_residency_enforcements": 0,
                "cross_border_transfers": 0,
                "firs_integrations": 0
            },
            "recommendations": [
                "Increase MFA adoption rate to 95%+",
                "Enable Nigerian USSD verification for mobile users", 
                "Implement biometric authentication for high-security operations",
                "Regular security awareness training for Nigerian compliance"
            ]
        }
        
        return report
    
    async def check_nigerian_compliance_status(
        self,
        user_id: UUID,
        operation: str,
        data_classification: str = "internal"
    ) -> Dict[str, Any]:
        """Check if current security posture meets Nigerian compliance requirements."""
        
        user_id_str = str(user_id)
        compliance_status = {
            "compliant": False,
            "required_security_level": SecurityLevel.BASIC,
            "current_security_level": SecurityLevel.BASIC,
            "missing_requirements": [],
            "recommendations": []
        }
        
        # Determine required security level based on operation and data
        if operation in ["firs_submission", "tax_data_access"]:
            compliance_status["required_security_level"] = SecurityLevel.HIGH
        elif data_classification in ["nigerian_pii", "tax_data"]:
            compliance_status["required_security_level"] = SecurityLevel.ENHANCED
        elif operation in ["data_export", "admin_action"]:
            compliance_status["required_security_level"] = SecurityLevel.ENHANCED
        
        # Check current MFA configuration
        try:
            mfa_config = await self._load_mfa_config(user_id_str, None)
            if mfa_config:
                compliance_status["current_security_level"] = mfa_config.security_level
                
                # Check if current level meets requirements
                required_level = compliance_status["required_security_level"]
                current_level = compliance_status["current_security_level"]
                
                level_hierarchy = {
                    SecurityLevel.BASIC: 1,
                    SecurityLevel.ENHANCED: 2,
                    SecurityLevel.HIGH: 3,
                    SecurityLevel.CRITICAL: 4
                }
                
                if level_hierarchy[current_level] >= level_hierarchy[required_level]:
                    compliance_status["compliant"] = True
                else:
                    compliance_status["missing_requirements"].append(
                        f"Security level {required_level.value} required for {operation}"
                    )
            else:
                compliance_status["missing_requirements"].append("MFA not configured")
                
        except Exception as e:
            logger.error(f"Failed to check compliance status: {str(e)}")
            compliance_status["missing_requirements"].append("Unable to verify security configuration")
        
        # Generate recommendations
        if not compliance_status["compliant"]:
            if "MFA not configured" in compliance_status["missing_requirements"]:
                compliance_status["recommendations"].append("Configure multi-factor authentication")
            
            required_level = compliance_status["required_security_level"]
            if required_level == SecurityLevel.HIGH:
                compliance_status["recommendations"].extend([
                    "Enable TOTP authentication",
                    "Configure Nigerian phone verification",
                    "Generate backup codes"
                ])
            elif required_level == SecurityLevel.CRITICAL:
                compliance_status["recommendations"].extend([
                    "Enable biometric authentication",
                    "Configure all available MFA methods",
                    "Implement hardware security keys"
                ])
        
        return compliance_status