"""
FIRS Hybrid Services Package

This package contains cross-cutting services that span both SI and APP functionality:

- Shared models and data structures
- Cross-role validation services
- Unified compliance monitoring
- Shared workflow orchestration
- Common infrastructure services

Hybrid Responsibilities:
- Provide shared models used by both SI and APP
- Implement cross-role validation logic
- Monitor compliance across both SI and APP operations
- Orchestrate workflows that span multiple FIRS roles
- Manage common infrastructure and dependencies
"""

# Hybrid service imports
from .deps import get_certificate_service, get_document_signing_service
from .certificate_manager import CertificateService

__all__ = [
    "get_certificate_service",
    "get_document_signing_service", 
    "CertificateService",
]