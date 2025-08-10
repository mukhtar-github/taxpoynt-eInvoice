"""
FIRS Core Services Package

This package contains shared FIRS services that are used by both SI and APP components:

- Core FIRS API client and integration
- Audit logging and compliance tracking
- Common utilities and helper functions
- Configuration management for FIRS services
- Base classes and interfaces for FIRS operations

Core Responsibilities:
- Provide unified FIRS API access
- Maintain audit trails for compliance
- Offer common utilities for FIRS operations
- Manage FIRS-specific configuration
- Define base interfaces for extensibility
"""

# Core FIRS service imports
from .firs_api_client import FIRSService
from .audit_service import AuditService

__all__ = [
    "FIRSService",
    "AuditService",
]