"""
Identity Verification Service
============================
Comprehensive identity verification service for Nigerian banking
operations. Provides multi-factor identity verification, document
validation, and biometric matching for KYC compliance.

Key Features:
- Multi-factor identity verification
- Document validation and verification
- Biometric matching and verification
- Cross-reference identity databases
- Real-time identity scoring
- Fraud detection and prevention
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
from dataclasses import dataclass, field
import re
import uuid
import hashlib

from ...shared.logging import get_logger
from ...shared.exceptions import IntegrationError


class VerificationMethod(Enum):
    """Identity verification methods."""
    BVN = "bvn"
    NIN = "nin"                    # National Identification Number
    PASSPORT = "passport"
    DRIVERS_LICENSE = "drivers_license"
    VOTERS_CARD = "voters_card"
    BIOMETRIC = "biometric"
    DOCUMENT_UPLOAD = "document_upload"
    VIDEO_CALL = "video_call"
    OTP_VERIFICATION = "otp_verification"
    BANK_STATEMENT = "bank_statement"
    UTILITY_BILL = "utility_bill"


class IdentityMatchLevel(Enum):
    """Levels of identity matching."""
    EXACT = "exact"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NO_MATCH = "no_match"


class DocumentType(Enum):
    """Types of identity documents."""
    NATIONAL_ID = "national_id"
    INTERNATIONAL_PASSPORT = "international_passport"
    DRIVERS_LICENSE = "drivers_license"
    VOTERS_CARD = "voters_card"
    BIRTH_CERTIFICATE = "birth_certificate"
    UTILITY_BILL = "utility_bill"
    BANK_STATEMENT = "bank_statement"
    EMPLOYMENT_LETTER = "employment_letter"
    ACADEMIC_CERTIFICATE = "academic_certificate"


class BiometricType(Enum):
    """Types of biometric verification."""
    FINGERPRINT = "fingerprint"
    FACE_RECOGNITION = "face_recognition"
    VOICE_RECOGNITION = "voice_recognition"
    IRIS_SCAN = "iris_scan"
    SIGNATURE = "signature"


@dataclass
class IdentityDocument:
    """Identity document information."""
    document_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    document_type: DocumentType = DocumentType.NATIONAL_ID
    document_number: str = ""
    issuing_authority: str = ""
    issue_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    
    # Document holder information
    holder_name: str = ""
    holder_dob: Optional[datetime] = None
    holder_address: Optional[str] = None
    holder_photo_url: Optional[str] = None
    
    # Verification status
    is_verified: bool = False
    verification_method: Optional[str] = None
    verification_score: float = 0.0
    verification_date: Optional[datetime] = None
    
    # Document authenticity
    is_authentic: bool = False
    security_features_verified: bool = False
    tampering_detected: bool = False
    
    # Metadata
    uploaded_at: datetime = field(default_factory=datetime.utcnow)
    file_hash: Optional[str] = None
    file_size: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BiometricVerification:
    """Biometric verification data."""
    verification_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    biometric_type: BiometricType = BiometricType.FINGERPRINT
    template_hash: str = ""
    
    # Verification results
    is_verified: bool = False
    confidence_score: float = 0.0
    match_score: float = 0.0
    
    # Quality metrics
    quality_score: float = 0.0
    quality_flags: List[str] = field(default_factory=list)
    
    # Verification metadata
    verified_at: datetime = field(default_factory=datetime.utcnow)
    verification_engine: str = ""
    liveness_check: bool = False
    
    # Security
    encrypted: bool = True
    retention_period_days: int = 2555  # 7 years for compliance


@dataclass
class IdentityMatchResult:
    """Result of identity matching between sources."""
    match_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_1: str = ""
    source_2: str = ""
    match_level: IdentityMatchLevel = IdentityMatchLevel.NO_MATCH
    
    # Field-level matching
    name_match: float = 0.0
    dob_match: float = 0.0
    address_match: float = 0.0
    phone_match: float = 0.0
    email_match: float = 0.0
    
    # Overall scores
    overall_score: float = 0.0
    confidence_level: float = 0.0
    
    # Discrepancies
    discrepancies: List[str] = field(default_factory=list)
    potential_fraud_indicators: List[str] = field(default_factory=list)
    
    # Metadata
    matched_at: datetime = field(default_factory=datetime.utcnow)
    matching_algorithm: str = "fuzzy_matching"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IdentityVerificationResult:
    """Comprehensive identity verification result."""
    verification_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    subject_id: str = ""
    verification_status: str = "pending"  # pending, verified, failed, requires_review
    
    # Verification methods used
    methods_used: List[VerificationMethod] = field(default_factory=list)
    documents_verified: List[IdentityDocument] = field(default_factory=list)
    biometric_verifications: List[BiometricVerification] = field(default_factory=list)
    
    # Matching results
    identity_matches: List[IdentityMatchResult] = field(default_factory=list)
    cross_reference_matches: Dict[str, IdentityMatchResult] = field(default_factory=dict)
    
    # Overall scores
    identity_score: float = 0.0
    fraud_risk_score: float = 0.0
    compliance_score: float = 0.0
    
    # Verification details
    verified_name: Optional[str] = None
    verified_dob: Optional[datetime] = None
    verified_address: Optional[str] = None
    verified_phone: Optional[str] = None
    verified_email: Optional[str] = None
    
    # Risk indicators
    risk_flags: List[str] = field(default_factory=list)
    fraud_indicators: List[str] = field(default_factory=list)
    compliance_flags: List[str] = field(default_factory=list)
    
    # Process metadata
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    processing_time_ms: float = 0.0
    
    # Audit and compliance
    consent_obtained: bool = False
    data_retention_date: Optional[datetime] = None
    audit_trail: List[str] = field(default_factory=list)
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class IdentityVerifier:
    """
    Comprehensive identity verification service.
    
    This service provides multi-factor identity verification capabilities
    including document validation, biometric verification, and cross-reference
    matching for comprehensive KYC compliance.
    """
    
    def __init__(self):
        """Initialize identity verifier."""
        self.logger = get_logger(__name__)
        
        # Verification configuration
        self.enable_biometric_verification = True
        self.enable_document_verification = True
        self.enable_cross_reference_checks = True
        
        # Scoring thresholds
        self.identity_score_threshold = 0.7
        self.fraud_risk_threshold = 0.3
        self.compliance_score_threshold = 0.8
        
        # Document validation patterns
        self.nin_pattern = re.compile(r'^\d{11}$')  # NIN format
        self.passport_pattern = re.compile(r'^[A-Z]\d{8}$')  # Nigerian passport
        self.drivers_license_pattern = re.compile(r'^[A-Z]{3}-\d{6}-[A-Z]{2}-\d{2}$')
        
        # Performance metrics
        self.verification_count = 0
        self.success_rate = 0.0
        
        self.logger.info("Initialized identity verification service")
    
    async def verify_identity(
        self,
        subject_id: str,
        verification_methods: List[VerificationMethod],
        documents: Optional[List[IdentityDocument]] = None,
        biometric_data: Optional[List[BiometricVerification]] = None,
        reference_data: Optional[Dict[str, Any]] = None,
        consent_obtained: bool = False
    ) -> IdentityVerificationResult:
        """
        Perform comprehensive identity verification.
        
        Args:
            subject_id: Subject identifier
            verification_methods: Methods to use for verification
            documents: Identity documents to verify
            biometric_data: Biometric data for verification
            reference_data: Reference data for matching
            consent_obtained: Whether user consent was obtained
            
        Returns:
            Comprehensive verification result
        """
        start_time = datetime.utcnow()
        
        try:
            self.logger.info(f"Starting identity verification for subject: {subject_id}")
            
            # Initialize result
            result = IdentityVerificationResult(
                subject_id=subject_id,
                methods_used=verification_methods,
                consent_obtained=consent_obtained
            )
            
            # Step 1: Document verification
            if VerificationMethod.DOCUMENT_UPLOAD in verification_methods and documents:
                await self._verify_documents(documents, result)
            
            # Step 2: Biometric verification
            if (VerificationMethod.BIOMETRIC in verification_methods and 
                biometric_data and self.enable_biometric_verification):
                await self._verify_biometrics(biometric_data, result)
            
            # Step 3: BVN verification
            if VerificationMethod.BVN in verification_methods:
                await self._verify_bvn_identity(subject_id, result, reference_data)
            
            # Step 4: NIN verification
            if VerificationMethod.NIN in verification_methods:
                await self._verify_nin_identity(subject_id, result, reference_data)
            
            # Step 5: Cross-reference checks
            if self.enable_cross_reference_checks:
                await self._perform_cross_reference_checks(result, reference_data)
            
            # Step 6: Calculate overall scores
            await self._calculate_verification_scores(result)
            
            # Step 7: Determine final status
            result.verification_status = self._determine_verification_status(result)
            
            # Calculate processing time
            end_time = datetime.utcnow()
            result.completed_at = end_time
            result.processing_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # Set data retention date (7 years for compliance)
            result.data_retention_date = end_time + timedelta(days=2555)
            
            # Create audit trail
            await self._create_verification_audit_trail(result)
            
            # Update metrics
            self.verification_count += 1
            self._update_success_rate(result)
            
            self.logger.info(
                f"Identity verification completed for {subject_id}: {result.verification_status}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Identity verification failed: {str(e)}")
            raise IntegrationError(f"Identity verification failed: {str(e)}")
    
    async def match_identities(
        self,
        identity_1: Dict[str, Any],
        identity_2: Dict[str, Any],
        matching_fields: Optional[List[str]] = None
    ) -> IdentityMatchResult:
        """
        Match two identity records and calculate similarity.
        
        Args:
            identity_1: First identity record
            identity_2: Second identity record
            matching_fields: Specific fields to match
            
        Returns:
            Identity matching result
        """
        try:
            self.logger.info("Performing identity matching")
            
            result = IdentityMatchResult(
                source_1=identity_1.get('source', 'unknown'),
                source_2=identity_2.get('source', 'unknown')
            )
            
            # Default matching fields
            if not matching_fields:
                matching_fields = ['name', 'date_of_birth', 'phone', 'address', 'email']
            
            # Perform field-level matching
            if 'name' in matching_fields:
                result.name_match = self._match_names(
                    identity_1.get('name', ''),
                    identity_2.get('name', '')
                )
            
            if 'date_of_birth' in matching_fields:
                result.dob_match = self._match_dates(
                    identity_1.get('date_of_birth'),
                    identity_2.get('date_of_birth')
                )
            
            if 'phone' in matching_fields:
                result.phone_match = self._match_phones(
                    identity_1.get('phone', ''),
                    identity_2.get('phone', '')
                )
            
            if 'address' in matching_fields:
                result.address_match = self._match_addresses(
                    identity_1.get('address', ''),
                    identity_2.get('address', '')
                )
            
            if 'email' in matching_fields:
                result.email_match = self._match_emails(
                    identity_1.get('email', ''),
                    identity_2.get('email', '')
                )
            
            # Calculate overall score
            scores = [result.name_match, result.dob_match, result.phone_match, 
                     result.address_match, result.email_match]
            valid_scores = [s for s in scores if s > 0]
            
            if valid_scores:
                result.overall_score = sum(valid_scores) / len(valid_scores)
            
            # Determine match level
            result.match_level = self._determine_match_level(result.overall_score)
            
            # Calculate confidence
            result.confidence_level = self._calculate_match_confidence(result)
            
            # Detect discrepancies
            result.discrepancies = self._detect_discrepancies(identity_1, identity_2)
            
            # Check for fraud indicators
            result.potential_fraud_indicators = self._detect_fraud_indicators(
                identity_1, identity_2, result
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Identity matching failed: {str(e)}")
            raise IntegrationError(f"Identity matching failed: {str(e)}")
    
    async def validate_document(
        self,
        document: IdentityDocument
    ) -> IdentityDocument:
        """
        Validate identity document authenticity and extract data.
        
        Args:
            document: Document to validate
            
        Returns:
            Updated document with validation results
        """
        try:
            self.logger.info(f"Validating document: {document.document_type.value}")
            
            # Format validation
            is_format_valid = self._validate_document_format(document)
            
            # Security features check
            if is_format_valid:
                document.security_features_verified = await self._check_security_features(document)
            
            # Tampering detection
            document.tampering_detected = await self._detect_tampering(document)
            
            # OCR and data extraction
            if document.security_features_verified and not document.tampering_detected:
                await self._extract_document_data(document)
            
            # Cross-reference with issuing authority
            if document.document_number:
                document.is_authentic = await self._verify_with_issuing_authority(document)
            
            # Calculate verification score
            document.verification_score = self._calculate_document_score(document)
            
            # Set verification status
            document.is_verified = (
                document.verification_score >= 0.7 and
                not document.tampering_detected and
                document.is_authentic
            )
            
            document.verification_date = datetime.utcnow()
            document.verification_method = "automated_validation"
            
            return document
            
        except Exception as e:
            self.logger.error(f"Document validation failed: {str(e)}")
            document.is_verified = False
            document.metadata['validation_error'] = str(e)
            return document
    
    async def _verify_documents(
        self,
        documents: List[IdentityDocument],
        result: IdentityVerificationResult
    ) -> None:
        """Verify all provided documents."""
        for document in documents:
            validated_document = await self.validate_document(document)
            result.documents_verified.append(validated_document)
            
            if validated_document.is_verified:
                # Extract verified information
                if validated_document.holder_name and not result.verified_name:
                    result.verified_name = validated_document.holder_name
                
                if validated_document.holder_dob and not result.verified_dob:
                    result.verified_dob = validated_document.holder_dob
                
                if validated_document.holder_address and not result.verified_address:
                    result.verified_address = validated_document.holder_address
    
    async def _verify_biometrics(
        self,
        biometric_data: List[BiometricVerification],
        result: IdentityVerificationResult
    ) -> None:
        """Verify biometric data."""
        for biometric in biometric_data:
            # Perform biometric verification
            biometric.is_verified = await self._perform_biometric_matching(biometric)
            biometric.verified_at = datetime.utcnow()
            
            result.biometric_verifications.append(biometric)
    
    async def _verify_bvn_identity(
        self,
        subject_id: str,
        result: IdentityVerificationResult,
        reference_data: Optional[Dict[str, Any]]
    ) -> None:
        """Verify identity against BVN data."""
        # This would integrate with the BVN validator
        self.logger.info("Verifying identity against BVN")
        
        # Mock BVN verification
        bvn_match = IdentityMatchResult(
            source_1="provided_data",
            source_2="bvn_database",
            match_level=IdentityMatchLevel.HIGH,
            overall_score=0.85
        )
        
        result.cross_reference_matches["bvn"] = bvn_match
    
    async def _verify_nin_identity(
        self,
        subject_id: str,
        result: IdentityVerificationResult,
        reference_data: Optional[Dict[str, Any]]
    ) -> None:
        """Verify identity against NIN data."""
        self.logger.info("Verifying identity against NIN")
        
        # Mock NIN verification
        nin_match = IdentityMatchResult(
            source_1="provided_data",
            source_2="nin_database",
            match_level=IdentityMatchLevel.HIGH,
            overall_score=0.82
        )
        
        result.cross_reference_matches["nin"] = nin_match
    
    async def _perform_cross_reference_checks(
        self,
        result: IdentityVerificationResult,
        reference_data: Optional[Dict[str, Any]]
    ) -> None:
        """Perform cross-reference checks against multiple databases."""
        # Check against watch lists
        if await self._check_watch_lists(result.subject_id):
            result.risk_flags.append("WATCH_LIST_MATCH")
        
        # Check against sanctions lists
        if await self._check_sanctions_lists(result.subject_id):
            result.risk_flags.append("SANCTIONS_LIST_MATCH")
        
        # Check for duplicate identities
        duplicates = await self._check_duplicate_identities(result)
        if duplicates:
            result.fraud_indicators.append("POTENTIAL_DUPLICATE_IDENTITY")
    
    async def _calculate_verification_scores(
        self,
        result: IdentityVerificationResult
    ) -> None:
        """Calculate overall verification scores."""
        # Identity score based on verification success
        identity_components = []
        
        # Document verification score
        if result.documents_verified:
            doc_scores = [doc.verification_score for doc in result.documents_verified if doc.is_verified]
            if doc_scores:
                identity_components.append(sum(doc_scores) / len(doc_scores))
        
        # Biometric verification score
        if result.biometric_verifications:
            bio_scores = [bio.confidence_score for bio in result.biometric_verifications if bio.is_verified]
            if bio_scores:
                identity_components.append(sum(bio_scores) / len(bio_scores))
        
        # Cross-reference score
        if result.cross_reference_matches:
            ref_scores = [match.overall_score for match in result.cross_reference_matches.values()]
            if ref_scores:
                identity_components.append(sum(ref_scores) / len(ref_scores))
        
        # Calculate overall identity score
        if identity_components:
            result.identity_score = sum(identity_components) / len(identity_components)
        
        # Fraud risk score (inverse of positive indicators)
        fraud_indicators_count = len(result.fraud_indicators) + len(result.risk_flags)
        result.fraud_risk_score = min(fraud_indicators_count * 0.2, 1.0)
        
        # Compliance score
        compliance_components = [
            1.0 if result.consent_obtained else 0.0,
            1.0 if len(result.methods_used) >= 2 else 0.5,  # Multi-factor verification
            1.0 if result.documents_verified else 0.0
        ]
        result.compliance_score = sum(compliance_components) / len(compliance_components)
    
    def _determine_verification_status(self, result: IdentityVerificationResult) -> str:
        """Determine final verification status."""
        if (result.identity_score >= self.identity_score_threshold and
            result.fraud_risk_score <= self.fraud_risk_threshold and
            result.compliance_score >= self.compliance_score_threshold):
            return "verified"
        elif result.fraud_risk_score > 0.7 or "SANCTIONS_LIST_MATCH" in result.risk_flags:
            return "failed"
        elif result.identity_score >= 0.5:
            return "requires_review"
        else:
            return "failed"
    
    # String matching and comparison methods
    
    def _match_names(self, name1: str, name2: str) -> float:
        """Calculate name matching score using fuzzy matching."""
        if not name1 or not name2:
            return 0.0
        
        # Normalize names
        name1_clean = re.sub(r'[^a-zA-Z\s]', '', name1.lower().strip())
        name2_clean = re.sub(r'[^a-zA-Z\s]', '', name2.lower().strip())
        
        # Exact match
        if name1_clean == name2_clean:
            return 1.0
        
        # Simple fuzzy matching (would use more sophisticated algorithms in reality)
        name1_parts = set(name1_clean.split())
        name2_parts = set(name2_clean.split())
        
        if not name1_parts or not name2_parts:
            return 0.0
        
        intersection = name1_parts.intersection(name2_parts)
        union = name1_parts.union(name2_parts)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _match_dates(self, date1: Optional[datetime], date2: Optional[datetime]) -> float:
        """Calculate date matching score."""
        if not date1 or not date2:
            return 0.0
        
        if date1.date() == date2.date():
            return 1.0
        
        # Allow small differences (typos in year, day/month swaps)
        diff_days = abs((date1 - date2).days)
        
        if diff_days <= 1:
            return 0.9
        elif diff_days <= 365:  # Year difference
            return 0.3
        else:
            return 0.0
    
    def _match_phones(self, phone1: str, phone2: str) -> float:
        """Calculate phone number matching score."""
        if not phone1 or not phone2:
            return 0.0
        
        # Normalize phone numbers
        phone1_clean = re.sub(r'[^\d]', '', phone1)
        phone2_clean = re.sub(r'[^\d]', '', phone2)
        
        # Handle Nigerian country code
        if phone1_clean.startswith('234'):
            phone1_clean = phone1_clean[3:]
        if phone2_clean.startswith('234'):
            phone2_clean = phone2_clean[3:]
        
        if phone1_clean == phone2_clean:
            return 1.0
        
        # Check if one is substring of other (different formatting)
        if phone1_clean in phone2_clean or phone2_clean in phone1_clean:
            return 0.8
        
        return 0.0
    
    def _match_addresses(self, addr1: str, addr2: str) -> float:
        """Calculate address matching score."""
        if not addr1 or not addr2:
            return 0.0
        
        # Normalize addresses
        addr1_clean = re.sub(r'[^\w\s]', '', addr1.lower())
        addr2_clean = re.sub(r'[^\w\s]', '', addr2.lower())
        
        if addr1_clean == addr2_clean:
            return 1.0
        
        # Split into components and match
        addr1_parts = set(addr1_clean.split())
        addr2_parts = set(addr2_clean.split())
        
        if not addr1_parts or not addr2_parts:
            return 0.0
        
        intersection = addr1_parts.intersection(addr2_parts)
        union = addr1_parts.union(addr2_parts)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _match_emails(self, email1: str, email2: str) -> float:
        """Calculate email matching score."""
        if not email1 or not email2:
            return 0.0
        
        if email1.lower().strip() == email2.lower().strip():
            return 1.0
        
        return 0.0
    
    # Mock implementation methods
    
    def _validate_document_format(self, document: IdentityDocument) -> bool:
        """Validate document format based on type."""
        if document.document_type == DocumentType.NATIONAL_ID:
            return bool(self.nin_pattern.match(document.document_number))
        elif document.document_type == DocumentType.INTERNATIONAL_PASSPORT:
            return bool(self.passport_pattern.match(document.document_number))
        elif document.document_type == DocumentType.DRIVERS_LICENSE:
            return bool(self.drivers_license_pattern.match(document.document_number))
        
        return True  # Default to valid for other types
    
    async def _check_security_features(self, document: IdentityDocument) -> bool:
        """Check document security features."""
        # Mock implementation
        return True
    
    async def _detect_tampering(self, document: IdentityDocument) -> bool:
        """Detect document tampering."""
        # Mock implementation
        return False
    
    async def _extract_document_data(self, document: IdentityDocument) -> None:
        """Extract data from document using OCR."""
        # Mock implementation
        pass
    
    async def _verify_with_issuing_authority(self, document: IdentityDocument) -> bool:
        """Verify document with issuing authority."""
        # Mock implementation
        return True
    
    def _calculate_document_score(self, document: IdentityDocument) -> float:
        """Calculate document verification score."""
        score = 0.0
        
        if document.security_features_verified:
            score += 0.4
        if not document.tampering_detected:
            score += 0.3
        if document.is_authentic:
            score += 0.3
        
        return score