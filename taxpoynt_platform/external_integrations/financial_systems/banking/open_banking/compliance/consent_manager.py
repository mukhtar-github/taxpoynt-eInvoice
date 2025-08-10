"""
Consent Manager for NDPR Compliance
===================================
User consent handling for Nigerian Data Protection Regulation (NDPR).
Manages user consent for banking data access, processing, and sharing
in compliance with Nigerian privacy regulations.

Key Features:
- NDPR-compliant consent collection
- Consent lifecycle management
- Data subject rights implementation
- Consent audit trails
- Automated consent renewal
- Granular permission management
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
import uuid

from ....shared.logging import get_logger
from ....shared.exceptions import IntegrationError


class ConsentType(Enum):
    """Types of consent for different operations."""
    ACCOUNT_ACCESS = "account_access"
    TRANSACTION_DATA = "transaction_data"
    BALANCE_INQUIRY = "balance_inquiry"
    PAYMENT_INITIATION = "payment_initiation"
    CREDIT_SCORING = "credit_scoring"
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    THIRD_PARTY_SHARING = "third_party_sharing"
    DATA_RETENTION = "data_retention"


class ConsentStatus(Enum):
    """Status of user consent."""
    PENDING = "pending"
    GRANTED = "granted"
    DENIED = "denied"
    REVOKED = "revoked"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"


class ConsentPurpose(Enum):
    """Purpose of data processing."""
    E_INVOICING = "e_invoicing"
    TAX_COMPLIANCE = "tax_compliance"
    FINANCIAL_REPORTING = "financial_reporting"
    FRAUD_PREVENTION = "fraud_prevention"
    REGULATORY_COMPLIANCE = "regulatory_compliance"
    SERVICE_PROVISION = "service_provision"
    CUSTOMER_SUPPORT = "customer_support"


@dataclass
class ConsentRecord:
    """Record of user consent."""
    consent_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    account_id: Optional[str] = None
    consent_type: ConsentType = ConsentType.ACCOUNT_ACCESS
    purpose: ConsentPurpose = ConsentPurpose.E_INVOICING
    status: ConsentStatus = ConsentStatus.PENDING
    granted_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    consent_text: str = ""
    legal_basis: str = "consent"
    data_categories: List[str] = field(default_factory=list)
    retention_period: Optional[int] = None  # days
    third_parties: List[str] = field(default_factory=list)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConsentAuditEntry:
    """Audit entry for consent changes."""
    audit_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    consent_id: str = ""
    user_id: str = ""
    action: str = ""  # granted, revoked, updated, etc.
    previous_status: Optional[ConsentStatus] = None
    new_status: ConsentStatus = ConsentStatus.PENDING
    timestamp: datetime = field(default_factory=datetime.utcnow)
    reason: Optional[str] = None
    source: str = "system"  # system, user, admin
    ip_address: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


class ConsentManager:
    """
    NDPR-compliant consent management system.
    
    This manager handles all aspects of user consent for banking data
    access and processing, ensuring compliance with Nigerian Data
    Protection Regulation requirements.
    """
    
    def __init__(self):
        """Initialize consent manager."""
        self.logger = get_logger(__name__)
        
        # Consent storage
        self.consent_records: Dict[str, ConsentRecord] = {}
        self.audit_trail: List[ConsentAuditEntry] = []
        
        # Configuration
        self.default_expiry_days = 365  # 1 year
        self.renewal_notice_days = 30
        self.automatic_renewal = False
        
        # NDPR compliance settings
        self.ndpr_compliance_enabled = True
        self.data_retention_limit_days = 2555  # 7 years for FIRS
        self.consent_withdrawal_grace_period = 30  # days
        
        self.logger.info("Initialized NDPR-compliant consent manager")
    
    async def request_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        purpose: ConsentPurpose,
        account_id: Optional[str] = None,
        data_categories: Optional[List[str]] = None,
        retention_period: Optional[int] = None,
        third_parties: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ConsentRecord:
        """
        Request consent from user for data processing.
        
        Args:
            user_id: User identifier
            consent_type: Type of consent being requested
            purpose: Purpose of data processing
            account_id: Optional account identifier
            data_categories: Categories of data to be processed
            retention_period: Data retention period in days
            third_parties: Third parties data may be shared with
            context: Additional context (IP, user agent, etc.)
            
        Returns:
            Consent record
        """
        try:
            # Generate consent text based on type and purpose
            consent_text = self._generate_consent_text(
                consent_type, purpose, data_categories, retention_period, third_parties
            )
            
            # Create consent record
            consent_record = ConsentRecord(
                user_id=user_id,
                account_id=account_id,
                consent_type=consent_type,
                purpose=purpose,
                status=ConsentStatus.PENDING,
                consent_text=consent_text,
                data_categories=data_categories or [],
                retention_period=retention_period or self.data_retention_limit_days,
                third_parties=third_parties or [],
                ip_address=context.get('ip_address') if context else None,
                user_agent=context.get('user_agent') if context else None,
                metadata=context or {}
            )
            
            # Store consent record
            self.consent_records[consent_record.consent_id] = consent_record
            
            # Create audit entry
            await self._create_audit_entry(
                consent_record.consent_id,
                user_id,
                "consent_requested",
                None,
                ConsentStatus.PENDING,
                "Consent requested for data processing",
                context.get('ip_address') if context else None
            )
            
            self.logger.info(f"Consent requested: {consent_record.consent_id} for user {user_id}")
            return consent_record
            
        except Exception as e:
            self.logger.error(f"Failed to request consent: {str(e)}")
            raise IntegrationError(f"Consent request failed: {str(e)}")
    
    async def grant_consent(
        self,
        consent_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ConsentRecord:
        """
        Grant user consent for data processing.
        
        Args:
            consent_id: Consent record identifier
            context: Additional context
            
        Returns:
            Updated consent record
        """
        try:
            consent_record = self.consent_records.get(consent_id)
            if not consent_record:
                raise ValueError(f"Consent record not found: {consent_id}")
            
            if consent_record.status != ConsentStatus.PENDING:
                raise ValueError(f"Consent not in pending state: {consent_record.status}")
            
            # Update consent record
            previous_status = consent_record.status
            consent_record.status = ConsentStatus.GRANTED
            consent_record.granted_at = datetime.utcnow()
            consent_record.expires_at = datetime.utcnow() + timedelta(days=self.default_expiry_days)
            consent_record.updated_at = datetime.utcnow()
            
            if context:
                consent_record.ip_address = context.get('ip_address')
                consent_record.user_agent = context.get('user_agent')
                consent_record.metadata.update(context)
            
            # Create audit entry
            await self._create_audit_entry(
                consent_id,
                consent_record.user_id,
                "consent_granted",
                previous_status,
                ConsentStatus.GRANTED,
                "User granted consent for data processing",
                context.get('ip_address') if context else None
            )
            
            self.logger.info(f"Consent granted: {consent_id}")
            return consent_record
            
        except Exception as e:
            self.logger.error(f"Failed to grant consent: {str(e)}")
            raise IntegrationError(f"Consent grant failed: {str(e)}")
    
    async def revoke_consent(
        self,
        consent_id: str,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ConsentRecord:
        """
        Revoke user consent.
        
        Args:
            consent_id: Consent record identifier
            reason: Reason for revocation
            context: Additional context
            
        Returns:
            Updated consent record
        """
        try:
            consent_record = self.consent_records.get(consent_id)
            if not consent_record:
                raise ValueError(f"Consent record not found: {consent_id}")
            
            if consent_record.status not in [ConsentStatus.GRANTED, ConsentStatus.PENDING]:
                raise ValueError(f"Cannot revoke consent in status: {consent_record.status}")
            
            # Update consent record
            previous_status = consent_record.status
            consent_record.status = ConsentStatus.REVOKED
            consent_record.revoked_at = datetime.utcnow()
            consent_record.updated_at = datetime.utcnow()
            
            # Create audit entry
            await self._create_audit_entry(
                consent_id,
                consent_record.user_id,
                "consent_revoked",
                previous_status,
                ConsentStatus.REVOKED,
                reason or "User revoked consent",
                context.get('ip_address') if context else None
            )
            
            self.logger.info(f"Consent revoked: {consent_id}")
            return consent_record
            
        except Exception as e:
            self.logger.error(f"Failed to revoke consent: {str(e)}")
            raise IntegrationError(f"Consent revocation failed: {str(e)}")
    
    async def check_consent_validity(
        self,
        user_id: str,
        consent_type: ConsentType,
        purpose: ConsentPurpose,
        account_id: Optional[str] = None
    ) -> bool:
        """
        Check if valid consent exists for specified operation.
        
        Args:
            user_id: User identifier
            consent_type: Type of consent required
            purpose: Purpose of data processing
            account_id: Optional account identifier
            
        Returns:
            True if valid consent exists
        """
        try:
            # Find relevant consent records
            relevant_consents = [
                consent for consent in self.consent_records.values()
                if (consent.user_id == user_id and
                    consent.consent_type == consent_type and
                    consent.purpose == purpose and
                    (account_id is None or consent.account_id == account_id))
            ]
            
            # Check for valid (granted and not expired) consent
            now = datetime.utcnow()
            
            for consent in relevant_consents:
                if (consent.status == ConsentStatus.GRANTED and
                    (consent.expires_at is None or consent.expires_at > now)):
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to check consent validity: {str(e)}")
            return False
    
    async def get_user_consents(
        self,
        user_id: str,
        status_filter: Optional[ConsentStatus] = None
    ) -> List[ConsentRecord]:
        """
        Get all consent records for a user.
        
        Args:
            user_id: User identifier
            status_filter: Optional status filter
            
        Returns:
            List of consent records
        """
        try:
            user_consents = [
                consent for consent in self.consent_records.values()
                if consent.user_id == user_id
            ]
            
            if status_filter:
                user_consents = [
                    consent for consent in user_consents
                    if consent.status == status_filter
                ]
            
            # Sort by creation date (newest first)
            user_consents.sort(key=lambda x: x.created_at, reverse=True)
            
            return user_consents
            
        except Exception as e:
            self.logger.error(f"Failed to get user consents: {str(e)}")
            return []
    
    async def check_expiring_consents(
        self,
        days_ahead: int = 30
    ) -> List[ConsentRecord]:
        """
        Check for consents expiring within specified days.
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List of expiring consent records
        """
        try:
            cutoff_date = datetime.utcnow() + timedelta(days=days_ahead)
            
            expiring_consents = [
                consent for consent in self.consent_records.values()
                if (consent.status == ConsentStatus.GRANTED and
                    consent.expires_at and
                    consent.expires_at <= cutoff_date)
            ]
            
            return expiring_consents
            
        except Exception as e:
            self.logger.error(f"Failed to check expiring consents: {str(e)}")
            return []
    
    async def expire_old_consents(self) -> int:
        """
        Expire old consents that have passed their expiry date.
        
        Returns:
            Number of consents expired
        """
        try:
            now = datetime.utcnow()
            expired_count = 0
            
            for consent in self.consent_records.values():
                if (consent.status == ConsentStatus.GRANTED and
                    consent.expires_at and
                    consent.expires_at <= now):
                    
                    # Update status
                    previous_status = consent.status
                    consent.status = ConsentStatus.EXPIRED
                    consent.updated_at = now
                    
                    # Create audit entry
                    await self._create_audit_entry(
                        consent.consent_id,
                        consent.user_id,
                        "consent_expired",
                        previous_status,
                        ConsentStatus.EXPIRED,
                        "Consent expired automatically"
                    )
                    
                    expired_count += 1
            
            if expired_count > 0:
                self.logger.info(f"Expired {expired_count} old consents")
            
            return expired_count
            
        except Exception as e:
            self.logger.error(f"Failed to expire old consents: {str(e)}")
            return 0
    
    def _generate_consent_text(
        self,
        consent_type: ConsentType,
        purpose: ConsentPurpose,
        data_categories: Optional[List[str]],
        retention_period: Optional[int],
        third_parties: Optional[List[str]]
    ) -> str:
        """Generate NDPR-compliant consent text."""
        
        base_text = f"""
CONSENT FOR DATA PROCESSING - TaxPoynt eInvoice Platform

Purpose: {purpose.value.replace('_', ' ').title()}
Data Processing Type: {consent_type.value.replace('_', ' ').title()}

By providing your consent, you agree to allow TaxPoynt to:
1. Access and process your banking data for e-invoicing and tax compliance purposes
2. Store your data securely for the period specified below
3. Share data with authorized parties as listed below (if applicable)

Data Categories: {', '.join(data_categories) if data_categories else 'Banking transaction data'}
Retention Period: {retention_period or 2555} days (as required by FIRS regulations)
Third Parties: {', '.join(third_parties) if third_parties else 'None'}

Your Rights:
- You can withdraw this consent at any time
- You can request access to your data
- You can request correction of inaccurate data
- You can request deletion of data (subject to regulatory requirements)
- You can file complaints with NITDA if you believe your rights have been violated

Legal Basis: Consent under the Nigeria Data Protection Regulation (NDPR)

Contact: privacy@taxpoynt.com for any data protection inquiries.
        """.strip()
        
        return base_text
    
    async def _create_audit_entry(
        self,
        consent_id: str,
        user_id: str,
        action: str,
        previous_status: Optional[ConsentStatus],
        new_status: ConsentStatus,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> None:
        """Create audit entry for consent action."""
        audit_entry = ConsentAuditEntry(
            consent_id=consent_id,
            user_id=user_id,
            action=action,
            previous_status=previous_status,
            new_status=new_status,
            reason=reason,
            ip_address=ip_address
        )
        
        self.audit_trail.append(audit_entry)
        
        # Keep audit trail manageable
        if len(self.audit_trail) > 100000:
            self.audit_trail = self.audit_trail[-50000:]