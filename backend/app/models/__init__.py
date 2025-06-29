from app.models.user import User
from app.models.user_role import UserRole
from app.models.organization import Organization, OrganizationUser
from app.models.client import Client
from app.models.integration import Integration, IntegrationHistory
from app.models.irn import IRNRecord, InvoiceData, IRNValidationRecord, IRNStatus
from app.models.encryption import EncryptionKey, EncryptionConfig
from app.models.firs_credentials import FIRSCredentials
from app.models.api_keys import APIKey
from app.models.api_credential import ApiCredential, CredentialType
from app.models.crm_connection import CRMConnection, CRMDeal, CRMType
from app.models.pos_connection import POSConnection, POSTransaction, POSType
from app.models.invoice import Invoice, InvoiceStatus, InvoiceSource
from app.models.certificate import Certificate, CertificateRevocation, CertificateType, CertificateStatus
from app.models.certificate_request import CertificateRequest, CertificateRequestType, CertificateRequestStatus
from app.models.submission import SubmissionRecord, SubmissionStatusUpdate, SubmissionNotification, SubmissionStatus, NotificationStatus
from app.models.nigerian_compliance import (
    NITDAAccreditation, 
    NDPRCompliance, 
    NigerianBusinessRegistration,
    FIRSPenaltyTracking,
    ISO27001Compliance,
    AccreditationStatus,
    ComplianceLevel
)
from app.models.user_service_access import (
    UserServiceAccess,
    ServiceAccessAuditLog,
    ServiceType,
    AccessLevel
)
from app.models.nigerian_business import (
    NigerianRelationshipManager,
    NigerianClientAssignment,
    NigerianCulturalPreferences,
    NigerianApprovalLevel,
    NigerianApprovalRequest,
    NigerianConglomerate,
    NigerianSubsidiary,
    NigerianBusinessInteraction,
    LanguagePreference,
    GreetingStyle,
    CommunicationPace,
    ApprovalStatus,
    TaxConsolidationType
)

# Add new models here when created