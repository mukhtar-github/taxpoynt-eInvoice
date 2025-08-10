"""
Bank Verification Number (BVN) Validation Services
==================================================
Comprehensive BVN validation and identity verification services for
Nigerian banking compliance. Provides KYC processing, identity
verification, and regulatory compliance for banking operations.

Key Components:
- bvn_validator: Core BVN validation services
- identity_verifier: Identity verification and matching
- kyc_processor: Know Your Customer compliance processing

Nigerian Banking Compliance:
- CBN (Central Bank of Nigeria) BVN requirements
- NDPR (Nigerian Data Protection Regulation) compliance
- Anti-Money Laundering (AML) compliance
- Know Your Customer (KYC) regulations
"""

from .bvn_validator import (
    BVNValidator, BVNValidationResult, BVNStatus,
    BVNValidationError, BVNServiceProvider
)
from .identity_verifier import (
    IdentityVerifier, IdentityVerificationResult, VerificationMethod,
    IdentityMatchResult, BiometricVerification
)
from .kyc_processor import (
    KYCProcessor, KYCLevel, KYCStatus, KYCResult,
    RiskAssessment, ComplianceCheck
)

__all__ = [
    # BVN Validation
    'BVNValidator',
    'BVNValidationResult',
    'BVNStatus',
    'BVNValidationError',
    'BVNServiceProvider',
    
    # Identity Verification
    'IdentityVerifier',
    'IdentityVerificationResult',
    'VerificationMethod',
    'IdentityMatchResult',
    'BiometricVerification',
    
    # KYC Processing
    'KYCProcessor',
    'KYCLevel',
    'KYCStatus',
    'KYCResult',
    'RiskAssessment',
    'ComplianceCheck'
]