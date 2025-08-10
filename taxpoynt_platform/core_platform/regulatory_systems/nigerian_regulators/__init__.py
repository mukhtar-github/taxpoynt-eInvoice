"""
Nigerian Regulatory Compliance Frameworks
=========================================

Nigerian-specific compliance validation systems for FIRS APP certification.

Components:
- firs_compliance/: FIRS compliance rules and UBL validation
- cac_compliance/: Corporate Affairs Commission validation  
- nitda_compliance/: NDPR data protection compliance
- cbn_compliance/: Central Bank of Nigeria banking compliance validation

Integration:
- Provides comprehensive Nigerian regulatory compliance coverage
- Integrates with Universal Compliance Validation Engine
- Supports real-time compliance monitoring and alerting
- Generates regulatory submission reports for Nigerian authorities
"""

# FIRS Compliance
from .firs_compliance import (
    FIRSValidator, FIRSComplianceRequest, FIRSValidationResult,
    TaxCalculationEngine, EInvoiceSubmissionHandler
)

# CAC Compliance  
from .cac_compliance import (
    CACValidator, EntityValidator, BankingLicense,
    RCNumberValidator, CorporateGovernanceValidator
)

# NITDA Compliance
from .nitda_compliance import (
    NDPAComplianceEngine, DataProtectionValidator,
    PrivacyImpactAssessment, ConsentManagementValidator
)

# CBN Compliance
from .cbn_compliance import (
    CBNValidator, BankingRegulationsValidator, KYCAMLValidator,
    CBNComplianceRequest, CBNValidationResult, BankingLicense,
    KYCProfile, AMLTransaction, CBNComplianceStatus, CBNRiskLevel
)

__all__ = [
    # FIRS Compliance
    'FIRSValidator',
    'FIRSComplianceRequest', 
    'FIRSValidationResult',
    'TaxCalculationEngine',
    'EInvoiceSubmissionHandler',
    
    # CAC Compliance
    'CACValidator',
    'EntityValidator',
    'RCNumberValidator',
    'CorporateGovernanceValidator',
    
    # NITDA Compliance
    'NDPAComplianceEngine',
    'DataProtectionValidator',
    'PrivacyImpactAssessment',
    'ConsentManagementValidator',
    
    # CBN Compliance
    'CBNValidator',
    'BankingRegulationsValidator',
    'KYCAMLValidator',
    'CBNComplianceRequest',
    'CBNValidationResult',
    'BankingLicense',
    'KYCProfile',
    'AMLTransaction',
    'CBNComplianceStatus',
    'CBNRiskLevel'
]