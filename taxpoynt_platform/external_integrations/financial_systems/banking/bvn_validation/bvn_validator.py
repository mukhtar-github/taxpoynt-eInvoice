"""
BVN (Bank Verification Number) Validator
========================================
Comprehensive BVN validation service for Nigerian banking compliance.
Validates BVN format, verifies against CBN database, and provides
detailed validation results for KYC and compliance purposes.

Key Features:
- BVN format validation
- CBN database verification
- Real-time BVN status checking
- Biometric verification support
- Compliance audit trails
- Multiple service provider support
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, field
import hashlib
import uuid

from ...shared.logging import get_logger
from ...shared.exceptions import IntegrationError


class BVNStatus(Enum):
    """BVN validation status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"
    SUSPENDED = "suspended"
    RESTRICTED = "restricted"
    UNKNOWN = "unknown"


class BVNServiceProvider(Enum):
    """BVN service providers."""
    CBN_DIRECT = "cbn_direct"           # Direct CBN integration
    NIBSS = "nibss"                     # Nigeria Inter-Bank Settlement System
    REMITA = "remita"                   # Remita BVN services
    FLUTTERWAVE = "flutterwave"         # Flutterwave BVN API
    PAYSTACK = "paystack"               # Paystack BVN verification
    MONO = "mono"                       # Mono BVN services
    PREMBLY = "prembly"                 # Prembly verification


class VerificationLevel(Enum):
    """Levels of BVN verification."""
    BASIC = "basic"                     # Format validation only
    STANDARD = "standard"               # Format + existence check
    ENHANCED = "enhanced"               # Standard + biometric check
    COMPREHENSIVE = "comprehensive"     # All checks + compliance verification


@dataclass
class BVNData:
    """BVN holder data structure."""
    bvn: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    gender: Optional[str] = None
    
    # Address information
    residential_address: Optional[str] = None
    state_of_residence: Optional[str] = None
    lga_of_residence: Optional[str] = None
    state_of_origin: Optional[str] = None
    lga_of_origin: Optional[str] = None
    
    # Identification
    nationality: Optional[str] = None
    title: Optional[str] = None
    marital_status: Optional[str] = None
    
    # Banking information
    registration_date: Optional[datetime] = None
    enrollment_bank: Optional[str] = None
    enrollment_branch: Optional[str] = None
    
    # Biometric flags
    has_fingerprint: bool = False
    has_photo: bool = False
    
    # Metadata
    last_updated: Optional[datetime] = None
    watch_listed: bool = False


@dataclass
class BVNValidationResult:
    """Result of BVN validation."""
    validation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    bvn: str = ""
    status: BVNStatus = BVNStatus.UNKNOWN
    is_valid: bool = False
    
    # Validation details
    format_valid: bool = False
    exists_in_database: bool = False
    biometric_verified: bool = False
    compliance_checked: bool = False
    
    # BVN holder data (if available and consented)
    bvn_data: Optional[BVNData] = None
    
    # Verification metadata
    verification_level: VerificationLevel = VerificationLevel.BASIC
    service_provider: BVNServiceProvider = BVNServiceProvider.CBN_DIRECT
    verified_at: datetime = field(default_factory=datetime.utcnow)
    response_time_ms: float = 0.0
    
    # Compliance and audit
    consent_obtained: bool = False
    audit_trail_id: Optional[str] = None
    compliance_flags: List[str] = field(default_factory=list)
    
    # Error information
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class BVNValidationError(IntegrationError):
    """BVN validation specific error."""
    
    def __init__(
        self,
        message: str,
        bvn: Optional[str] = None,
        error_code: Optional[str] = None,
        service_provider: Optional[BVNServiceProvider] = None
    ):
        super().__init__(message)
        self.bvn = bvn
        self.error_code = error_code
        self.service_provider = service_provider


class BVNValidator:
    """
    Comprehensive BVN validation service.
    
    This validator provides complete BVN validation capabilities including
    format validation, database verification, biometric checks, and
    compliance verification for Nigerian banking operations.
    """
    
    def __init__(
        self,
        primary_provider: BVNServiceProvider = BVNServiceProvider.CBN_DIRECT,
        fallback_providers: Optional[List[BVNServiceProvider]] = None
    ):
        """
        Initialize BVN validator.
        
        Args:
            primary_provider: Primary BVN service provider
            fallback_providers: Fallback providers for redundancy
        """
        self.logger = get_logger(__name__)
        self.primary_provider = primary_provider
        self.fallback_providers = fallback_providers or []
        
        # Validation configuration
        self.enable_biometric_verification = True
        self.enable_compliance_checks = True
        self.cache_results = True
        self.cache_duration_hours = 24
        
        # Rate limiting
        self.rate_limit_per_minute = 100
        self.rate_limit_per_hour = 1000
        
        # Validation cache
        self.validation_cache: Dict[str, BVNValidationResult] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
        
        # Performance metrics
        self.validation_count = 0
        self.success_count = 0
        self.error_count = 0
        
        # Nigerian BVN format pattern (11 digits)
        self.bvn_pattern = re.compile(r'^\d{11}$')
        
        self.logger.info(f"Initialized BVN validator with provider: {primary_provider}")
    
    async def validate_bvn(
        self,
        bvn: str,
        verification_level: VerificationLevel = VerificationLevel.STANDARD,
        consent_obtained: bool = False,
        requester_id: Optional[str] = None,
        purpose: Optional[str] = None
    ) -> BVNValidationResult:
        """
        Validate BVN with specified verification level.
        
        Args:
            bvn: Bank Verification Number to validate
            verification_level: Level of verification to perform
            consent_obtained: Whether user consent was obtained
            requester_id: ID of the entity requesting validation
            purpose: Purpose of the BVN validation
            
        Returns:
            BVN validation result
            
        Raises:
            BVNValidationError: If validation fails
        """
        start_time = datetime.utcnow()
        
        try:
            self.logger.info(f"Validating BVN with level: {verification_level.value}")
            
            # Check cache first
            if self.cache_results:
                cached_result = self._get_cached_result(bvn, verification_level)
                if cached_result:
                    self.logger.info("Returning cached BVN validation result")
                    return cached_result
            
            # Initialize result
            result = BVNValidationResult(
                bvn=self._mask_bvn(bvn),
                verification_level=verification_level,
                service_provider=self.primary_provider,
                consent_obtained=consent_obtained
            )
            
            # Step 1: Format validation
            result.format_valid = self._validate_bvn_format(bvn)
            if not result.format_valid:
                result.error_code = "INVALID_FORMAT"
                result.error_message = "BVN format is invalid"
                return result
            
            # Step 2: Database verification (if level requires)
            if verification_level in [
                VerificationLevel.STANDARD,
                VerificationLevel.ENHANCED,
                VerificationLevel.COMPREHENSIVE
            ]:
                await self._verify_bvn_existence(bvn, result)
            
            # Step 3: Biometric verification (if level requires and available)
            if verification_level in [
                VerificationLevel.ENHANCED,
                VerificationLevel.COMPREHENSIVE
            ] and self.enable_biometric_verification:
                await self._verify_biometric_data(bvn, result)
            
            # Step 4: Compliance checks (if level requires)
            if verification_level == VerificationLevel.COMPREHENSIVE and self.enable_compliance_checks:
                await self._perform_compliance_checks(bvn, result)
            
            # Determine overall validity
            result.is_valid = self._calculate_overall_validity(result, verification_level)
            
            # Calculate response time
            end_time = datetime.utcnow()
            result.response_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # Cache result
            if self.cache_results and result.is_valid:
                self._cache_result(bvn, verification_level, result)
            
            # Update metrics
            self.validation_count += 1
            if result.is_valid:
                self.success_count += 1
            else:
                self.error_count += 1
            
            # Create audit trail
            await self._create_audit_trail(bvn, result, requester_id, purpose)
            
            self.logger.info(f"BVN validation completed: {result.is_valid}")
            return result
            
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"BVN validation failed: {str(e)}")
            raise BVNValidationError(
                f"BVN validation failed: {str(e)}",
                bvn=self._mask_bvn(bvn),
                service_provider=self.primary_provider
            )
    
    async def validate_multiple_bvns(
        self,
        bvns: List[str],
        verification_level: VerificationLevel = VerificationLevel.STANDARD,
        batch_size: int = 10
    ) -> List[BVNValidationResult]:
        """
        Validate multiple BVNs in batch.
        
        Args:
            bvns: List of BVNs to validate
            verification_level: Verification level for all BVNs
            batch_size: Size of each batch
            
        Returns:
            List of validation results
        """
        try:
            self.logger.info(f"Batch validating {len(bvns)} BVNs")
            
            results = []
            
            # Process in batches to respect rate limits
            for i in range(0, len(bvns), batch_size):
                batch = bvns[i:i + batch_size]
                batch_tasks = [
                    self.validate_bvn(bvn, verification_level)
                    for bvn in batch
                ]
                
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, Exception):
                        # Create error result
                        error_result = BVNValidationResult(
                            bvn="***masked***",
                            is_valid=False,
                            error_message=str(result)
                        )
                        results.append(error_result)
                    else:
                        results.append(result)
                
                # Rate limiting delay between batches
                if i + batch_size < len(bvns):
                    await asyncio.sleep(1)  # 1 second delay
            
            self.logger.info(f"Batch validation completed: {len(results)} results")
            return results
            
        except Exception as e:
            self.logger.error(f"Batch BVN validation failed: {str(e)}")
            raise BVNValidationError(f"Batch validation failed: {str(e)}")
    
    async def check_bvn_status(self, bvn: str) -> BVNStatus:
        """
        Check current status of a BVN.
        
        Args:
            bvn: Bank Verification Number
            
        Returns:
            Current BVN status
        """
        try:
            # Validate format first
            if not self._validate_bvn_format(bvn):
                return BVNStatus.UNKNOWN
            
            # Check with primary provider
            status = await self._check_bvn_status_with_provider(
                bvn, self.primary_provider
            )
            
            return status
            
        except Exception as e:
            self.logger.error(f"BVN status check failed: {str(e)}")
            return BVNStatus.UNKNOWN
    
    def _validate_bvn_format(self, bvn: str) -> bool:
        """
        Validate BVN format (11 digits).
        
        Args:
            bvn: BVN to validate
            
        Returns:
            True if format is valid
        """
        if not bvn or not isinstance(bvn, str):
            return False
        
        # Remove any whitespace
        bvn_clean = bvn.strip().replace(' ', '')
        
        # Check if it matches Nigerian BVN format (11 digits)
        return bool(self.bvn_pattern.match(bvn_clean))
    
    async def _verify_bvn_existence(
        self,
        bvn: str,
        result: BVNValidationResult
    ) -> None:
        """
        Verify BVN exists in CBN database.
        
        Args:
            bvn: BVN to verify
            result: Result object to update
        """
        try:
            # Try primary provider first
            exists, bvn_data = await self._check_existence_with_provider(
                bvn, self.primary_provider
            )
            
            if not exists and self.fallback_providers:
                # Try fallback providers
                for provider in self.fallback_providers:
                    exists, bvn_data = await self._check_existence_with_provider(
                        bvn, provider
                    )
                    if exists:
                        result.service_provider = provider
                        break
            
            result.exists_in_database = exists
            if exists and bvn_data:
                result.bvn_data = bvn_data
                result.status = BVNStatus.ACTIVE
            else:
                result.status = BVNStatus.UNKNOWN
                
        except Exception as e:
            self.logger.error(f"BVN existence verification failed: {str(e)}")
            result.warnings.append(f"Database verification failed: {str(e)}")
    
    async def _verify_biometric_data(
        self,
        bvn: str,
        result: BVNValidationResult
    ) -> None:
        """
        Verify biometric data associated with BVN.
        
        Args:
            bvn: BVN to verify
            result: Result object to update
        """
        try:
            # Check if biometric data is available
            has_biometric = await self._check_biometric_availability(bvn)
            
            if has_biometric:
                # Perform biometric verification (simplified)
                verified = await self._perform_biometric_verification(bvn)
                result.biometric_verified = verified
                
                if result.bvn_data:
                    result.bvn_data.has_fingerprint = has_biometric
                    result.bvn_data.has_photo = has_biometric
            else:
                result.warnings.append("No biometric data available for verification")
                
        except Exception as e:
            self.logger.error(f"Biometric verification failed: {str(e)}")
            result.warnings.append(f"Biometric verification failed: {str(e)}")
    
    async def _perform_compliance_checks(
        self,
        bvn: str,
        result: BVNValidationResult
    ) -> None:
        """
        Perform compliance checks on BVN.
        
        Args:
            bvn: BVN to check
            result: Result object to update
        """
        try:
            compliance_flags = []
            
            # Check watch lists
            if await self._check_watch_list(bvn):
                compliance_flags.append("WATCH_LISTED")
            
            # Check sanctions lists
            if await self._check_sanctions_list(bvn):
                compliance_flags.append("SANCTIONS_LISTED")
            
            # Check for restricted status
            if await self._check_restricted_status(bvn):
                compliance_flags.append("RESTRICTED")
            
            result.compliance_flags = compliance_flags
            result.compliance_checked = True
            
            if result.bvn_data and compliance_flags:
                result.bvn_data.watch_listed = "WATCH_LISTED" in compliance_flags
                
        except Exception as e:
            self.logger.error(f"Compliance checks failed: {str(e)}")
            result.warnings.append(f"Compliance checks failed: {str(e)}")
    
    def _calculate_overall_validity(
        self,
        result: BVNValidationResult,
        verification_level: VerificationLevel
    ) -> bool:
        """
        Calculate overall BVN validity based on verification level.
        
        Args:
            result: Validation result
            verification_level: Required verification level
            
        Returns:
            True if BVN is valid for the required level
        """
        # Format must always be valid
        if not result.format_valid:
            return False
        
        # Basic level only requires format
        if verification_level == VerificationLevel.BASIC:
            return True
        
        # Standard level requires existence
        if verification_level == VerificationLevel.STANDARD:
            return result.exists_in_database
        
        # Enhanced level requires existence and biometric (if available)
        if verification_level == VerificationLevel.ENHANCED:
            return result.exists_in_database and (
                result.biometric_verified or 
                not self.enable_biometric_verification
            )
        
        # Comprehensive level requires all checks
        if verification_level == VerificationLevel.COMPREHENSIVE:
            return (
                result.exists_in_database and
                (result.biometric_verified or not self.enable_biometric_verification) and
                result.compliance_checked and
                "WATCH_LISTED" not in result.compliance_flags and
                "SANCTIONS_LISTED" not in result.compliance_flags
            )
        
        return False
    
    def _mask_bvn(self, bvn: str) -> str:
        """
        Mask BVN for logging and security.
        
        Args:
            bvn: BVN to mask
            
        Returns:
            Masked BVN string
        """
        if not bvn or len(bvn) < 4:
            return "***masked***"
        
        return f"{bvn[:3]}***{bvn[-2:]}"
    
    def _get_cached_result(
        self,
        bvn: str,
        verification_level: VerificationLevel
    ) -> Optional[BVNValidationResult]:
        """Get cached validation result if available and not expired."""
        cache_key = f"{hashlib.sha256(bvn.encode()).hexdigest()}_{verification_level.value}"
        
        if cache_key in self.validation_cache:
            cached_time = self.cache_timestamps.get(cache_key)
            if cached_time and datetime.utcnow() - cached_time < timedelta(hours=self.cache_duration_hours):
                return self.validation_cache[cache_key]
            else:
                # Remove expired cache
                del self.validation_cache[cache_key]
                del self.cache_timestamps[cache_key]
        
        return None
    
    def _cache_result(
        self,
        bvn: str,
        verification_level: VerificationLevel,
        result: BVNValidationResult
    ) -> None:
        """Cache validation result."""
        cache_key = f"{hashlib.sha256(bvn.encode()).hexdigest()}_{verification_level.value}"
        self.validation_cache[cache_key] = result
        self.cache_timestamps[cache_key] = datetime.utcnow()
        
        # Clean old cache entries if cache is getting large
        if len(self.validation_cache) > 1000:
            self._clean_old_cache_entries()
    
    def _clean_old_cache_entries(self) -> None:
        """Clean expired cache entries."""
        current_time = datetime.utcnow()
        expired_keys = [
            key for key, timestamp in self.cache_timestamps.items()
            if current_time - timestamp > timedelta(hours=self.cache_duration_hours)
        ]
        
        for key in expired_keys:
            if key in self.validation_cache:
                del self.validation_cache[key]
            if key in self.cache_timestamps:
                del self.cache_timestamps[key]
    
    # Mock service provider integration methods
    # These would be replaced with actual provider API calls
    
    async def _check_existence_with_provider(
        self,
        bvn: str,
        provider: BVNServiceProvider
    ) -> Tuple[bool, Optional[BVNData]]:
        """Check BVN existence with specific provider."""
        # Mock implementation - would integrate with actual provider APIs
        self.logger.info(f"Checking BVN existence with {provider.value}")
        
        # Simulate API call delay
        await asyncio.sleep(0.1)
        
        # Mock response - in reality would parse provider response
        return True, BVNData(
            bvn=bvn,
            first_name="Mock",
            last_name="User",
            date_of_birth=datetime(1990, 1, 1),
            phone_number="08012345678",
            nationality="Nigerian",
            registration_date=datetime(2015, 1, 1)
        )
    
    async def _check_bvn_status_with_provider(
        self,
        bvn: str,
        provider: BVNServiceProvider
    ) -> BVNStatus:
        """Check BVN status with specific provider."""
        self.logger.info(f"Checking BVN status with {provider.value}")
        await asyncio.sleep(0.1)
        return BVNStatus.ACTIVE
    
    async def _check_biometric_availability(self, bvn: str) -> bool:
        """Check if biometric data is available."""
        await asyncio.sleep(0.05)
        return True
    
    async def _perform_biometric_verification(self, bvn: str) -> bool:
        """Perform biometric verification."""
        await asyncio.sleep(0.1)
        return True
    
    async def _check_watch_list(self, bvn: str) -> bool:
        """Check if BVN is on watch list."""
        await asyncio.sleep(0.05)
        return False
    
    async def _check_sanctions_list(self, bvn: str) -> bool:
        """Check if BVN is on sanctions list."""
        await asyncio.sleep(0.05)
        return False
    
    async def _check_restricted_status(self, bvn: str) -> bool:
        """Check if BVN has restricted status."""
        await asyncio.sleep(0.05)
        return False
    
    async def _create_audit_trail(
        self,
        bvn: str,
        result: BVNValidationResult,
        requester_id: Optional[str],
        purpose: Optional[str]
    ) -> None:
        """Create audit trail for BVN validation."""
        audit_data = {
            "validation_id": result.validation_id,
            "bvn_masked": self._mask_bvn(bvn),
            "requester_id": requester_id,
            "purpose": purpose,
            "verification_level": result.verification_level.value,
            "result": result.is_valid,
            "timestamp": result.verified_at.isoformat()
        }
        
        # This would integrate with the audit logger
        self.logger.info(f"BVN validation audit: {audit_data}")
        result.audit_trail_id = str(uuid.uuid4())