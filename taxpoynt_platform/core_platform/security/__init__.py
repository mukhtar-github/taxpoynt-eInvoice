"""
Core Platform Security Package
Comprehensive security orchestration and coordination for the TaxPoynt platform.
Provides unified security management across all platform roles and services.
"""

from .security_orchestrator import (
    SecurityOrchestrator,
    SecurityPolicy,
    SecurityEvent,
    SecurityMetrics,
    ThreatLevel,
    security_orchestrator,
    initialize_security_orchestrator
)

from .threat_intelligence import (
    ThreatIntelligence,
    ThreatIndicator,
    ThreatFeed,
    ThreatReport,
    IndicatorType,
    ThreatSeverity,
    threat_intelligence,
    initialize_threat_intelligence
)

from .vulnerability_scanner import (
    VulnerabilityScanner,
    Vulnerability,
    ScanResult,
    ScanTarget,
    VulnerabilitySeverity,
    ScanType,
    vulnerability_scanner,
    initialize_vulnerability_scanner
)

from .compliance_enforcer import (
    ComplianceEnforcer,
    ComplianceRule,
    ComplianceCheck,
    ComplianceViolation,
    ComplianceReport,
    ComplianceLevel,
    ComplianceStatus,
    ComplianceFramework,
    compliance_enforcer,
    initialize_compliance_enforcer
)

from .incident_responder import (
    IncidentResponder,
    SecurityIncident,
    IncidentAction,
    IncidentEvidence,
    ResponsePlaybook,
    IncidentSeverity,
    IncidentStatus,
    IncidentCategory,
    ResponseAction,
    incident_responder,
    initialize_incident_responder
)

__all__ = [
    # Security Orchestrator
    'SecurityOrchestrator',
    'SecurityPolicy',
    'SecurityEvent',
    'SecurityMetrics',
    'ThreatLevel',
    'security_orchestrator',
    'initialize_security_orchestrator',
    
    # Threat Intelligence
    'ThreatIntelligence',
    'ThreatIndicator',
    'ThreatFeed',
    'ThreatReport',
    'IndicatorType',
    'ThreatSeverity',
    'threat_intelligence',
    'initialize_threat_intelligence',
    
    # Vulnerability Scanner
    'VulnerabilityScanner',
    'Vulnerability',
    'ScanResult',
    'ScanTarget',
    'VulnerabilitySeverity',
    'ScanType',
    'vulnerability_scanner',
    'initialize_vulnerability_scanner',
    
    # Compliance Enforcer
    'ComplianceEnforcer',
    'ComplianceRule',
    'ComplianceCheck',
    'ComplianceViolation',
    'ComplianceReport',
    'ComplianceLevel',
    'ComplianceStatus',
    'ComplianceFramework',
    'compliance_enforcer',
    'initialize_compliance_enforcer',
    
    # Incident Responder
    'IncidentResponder',
    'SecurityIncident',
    'IncidentAction',
    'IncidentEvidence',
    'ResponsePlaybook',
    'IncidentSeverity',
    'IncidentStatus',
    'IncidentCategory',
    'ResponseAction',
    'incident_responder',
    'initialize_incident_responder'
]

async def initialize_platform_security():
    """
    Initialize all platform security components.
    This function should be called during platform startup.
    """
    success = True
    
    # Initialize security orchestrator
    if not await initialize_security_orchestrator():
        success = False
    
    # Initialize threat intelligence
    if not await initialize_threat_intelligence():
        success = False
    
    # Initialize vulnerability scanner
    if not await initialize_vulnerability_scanner():
        success = False
    
    # Initialize compliance enforcer
    if not await initialize_compliance_enforcer():
        success = False
    
    # Initialize incident responder
    if not await initialize_incident_responder():
        success = False
    
    return success