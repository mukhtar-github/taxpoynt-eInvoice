"""
FIRS Core Monitoring Service

Enhanced FIRS API monitoring with comprehensive compliance tracking,
Nigerian regulatory compliance, and ISO 27001 security monitoring.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
import json
import asyncio
from functools import wraps
import statistics
from collections import deque, Counter
from enum import Enum
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# Enhanced monitoring configurations
DEFAULT_HISTORY_SIZE = 1000  # Increased for compliance tracking
DEFAULT_SLOW_THRESHOLD_MS = 2000  # Adjusted for FIRS API expectations
COMPLIANCE_RETENTION_DAYS = 2555  # 7 years for Nigerian tax compliance


class MonitoringLevel(str, Enum):
    """Monitoring severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ComplianceEventType(str, Enum):
    """Compliance event types for Nigerian regulations"""
    FIRS_SUBMISSION = "firs_submission"
    TAX_DATA_ACCESS = "tax_data_access"
    NDPR_DATA_PROCESSING = "ndpr_data_processing"
    INVOICE_VALIDATION = "invoice_validation"
    CERTIFICATE_OPERATION = "certificate_operation"
    SECURITY_EVENT = "security_event"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    API_RATE_LIMIT = "api_rate_limit"
    SYSTEM_ERROR = "system_error"


@dataclass
class ComplianceEvent:
    """Enhanced compliance event structure"""
    event_id: str
    event_type: ComplianceEventType
    timestamp: datetime
    severity: MonitoringLevel
    organization_id: Optional[str] = None
    user_id: Optional[str] = None
    endpoint: Optional[str] = None
    request_id: Optional[str] = None
    duration_ms: Optional[float] = None
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    compliance_flags: Optional[List[str]] = None
    nigerian_data_involved: bool = False
    tax_data_involved: bool = False
    retention_required: bool = True
    metadata: Optional[Dict[str, Any]] = None


class FIRSCoreAPIMonitor:
    """
    Enhanced FIRS API monitoring service with compliance tracking.
    
    Provides comprehensive monitoring for:
    1. FIRS API performance and reliability
    2. Nigerian compliance requirements (NDPR, FIRS)
    3. ISO 27001 security monitoring
    4. Tax data protection and audit trails
    """
    
    def __init__(self, 
                 history_size: int = DEFAULT_HISTORY_SIZE,
                 compliance_retention_days: int = COMPLIANCE_RETENTION_DAYS):
        """Initialize enhanced monitoring service."""
        self.request_history = deque(maxlen=history_size)
        self.error_history = deque(maxlen=history_size)
        self.compliance_events = deque(maxlen=history_size * 2)
        self.endpoint_usage = Counter()
        self.slow_threshold_ms = DEFAULT_SLOW_THRESHOLD_MS
        self.start_time = datetime.now()
        self.compliance_retention_days = compliance_retention_days
        
        # Enhanced stats tracking
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.rate_limited_requests = 0
        self.compliance_violations = 0
        self.security_incidents = 0
        
        # Nigerian compliance tracking
        self.firs_submissions = 0
        self.tax_data_operations = 0
        self.ndpr_relevant_operations = 0
        
        logger.info(f"FIRS Core API monitoring initialized (history: {history_size}, "
                   f"compliance retention: {compliance_retention_days} days)")
    
    def record_enhanced_request(
        self, 
        endpoint: str, 
        method: str, 
        duration_ms: float, 
        status_code: int, 
        environment: str,
        request_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        user_id: Optional[str] = None,
        payload_size: Optional[int] = None,
        response_size: Optional[int] = None,
        error: Optional[str] = None,
        compliance_context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record enhanced API request with compliance tracking.
        
        Args:
            endpoint: The API endpoint that was called
            method: HTTP method used
            duration_ms: Request duration in milliseconds
            status_code: HTTP status code received
            environment: 'sandbox' or 'production'
            request_id: Unique identifier for the request
            organization_id: Organization making the request
            user_id: User making the request
            payload_size: Size of request payload in bytes
            response_size: Size of response in bytes
            error: Error message if request failed
            compliance_context: Additional compliance-related data
        """
        timestamp = datetime.utcnow()
        
        # Determine compliance flags
        compliance_flags = self._analyze_compliance_context(endpoint, compliance_context)
        
        # Create enhanced request record
        request_record = {
            'timestamp': timestamp,
            'endpoint': endpoint,
            'method': method,
            'duration_ms': duration_ms,
            'status_code': status_code,
            'environment': environment,
            'request_id': request_id,
            'organization_id': organization_id,
            'user_id': user_id,
            'payload_size': payload_size,
            'response_size': response_size,
            'is_slow': duration_ms > self.slow_threshold_ms,
            'compliance_flags': compliance_flags,
            'nigerian_data_involved': self._involves_nigerian_data(endpoint, compliance_context),
            'tax_data_involved': self._involves_tax_data(endpoint, compliance_context),
            'security_relevant': self._is_security_relevant(endpoint, status_code)
        }
        
        # Update stats
        self.total_requests += 1
        self.endpoint_usage[endpoint] += 1
        
        # Update compliance counters
        if self._is_firs_submission(endpoint):
            self.firs_submissions += 1
        if request_record['tax_data_involved']:
            self.tax_data_operations += 1
        if request_record['nigerian_data_involved']:
            self.ndpr_relevant_operations += 1
        
        # Categorize response
        if 200 <= status_code < 300:
            self.successful_requests += 1
        elif status_code == 429:
            self.rate_limited_requests += 1
            self.failed_requests += 1
            self._record_compliance_event(
                ComplianceEventType.API_RATE_LIMIT,
                MonitoringLevel.HIGH,
                endpoint=endpoint,
                request_id=request_id,
                organization_id=organization_id,
                metadata={"rate_limit_hit": True}
            )
        else:
            self.failed_requests += 1
        
        # Store in history
        self.request_history.append(request_record)
        
        # Log performance issues
        if request_record['is_slow']:
            severity = MonitoringLevel.HIGH if duration_ms > self.slow_threshold_ms * 2 else MonitoringLevel.MEDIUM
            logger.warning(
                f"Slow FIRS API call: {method} {endpoint} took {duration_ms:.2f} ms "
                f"(threshold: {self.slow_threshold_ms} ms)"
            )
            self._record_compliance_event(
                ComplianceEventType.PERFORMANCE_DEGRADATION,
                severity,
                endpoint=endpoint,
                request_id=request_id,
                organization_id=organization_id,
                duration_ms=duration_ms
            )
        
        # Record error if present
        if error:
            self.record_enhanced_error(
                endpoint, status_code, error, environment, 
                request_id, organization_id, user_id
            )
    
    def record_enhanced_error(
        self, 
        endpoint: str, 
        status_code: int, 
        error_message: str, 
        environment: str,
        request_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> None:
        """Record enhanced API error with compliance tracking."""
        error_record = {
            'timestamp': datetime.utcnow(),
            'endpoint': endpoint,
            'status_code': status_code,
            'error_message': error_message,
            'environment': environment,
            'request_id': request_id,
            'organization_id': organization_id,
            'user_id': user_id,
            'error_category': self._categorize_error(status_code, error_message),
            'compliance_impact': self._assess_compliance_impact(endpoint, status_code)
        }
        
        self.error_history.append(error_record)
        
        # Determine severity and compliance implications
        severity = self._determine_error_severity(status_code, error_message)
        
        # Record compliance event
        self._record_compliance_event(
            ComplianceEventType.SYSTEM_ERROR,
            severity,
            endpoint=endpoint,
            request_id=request_id,
            organization_id=organization_id,
            error_message=error_message,
            metadata={
                "status_code": status_code,
                "error_category": error_record['error_category'],
                "compliance_impact": error_record['compliance_impact']
            }
        )
        
        logger.error(
            f"FIRS API error ({status_code}): {error_message} - {endpoint} "
            f"[Org: {organization_id}, Req: {request_id}]"
        )
    
    def _record_compliance_event(
        self,
        event_type: ComplianceEventType,
        severity: MonitoringLevel,
        endpoint: Optional[str] = None,
        request_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        user_id: Optional[str] = None,
        duration_ms: Optional[float] = None,
        status_code: Optional[int] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record compliance event for audit trail."""
        import uuid
        
        event = ComplianceEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.utcnow(),
            severity=severity,
            organization_id=organization_id,
            user_id=user_id,
            endpoint=endpoint,
            request_id=request_id,
            duration_ms=duration_ms,
            status_code=status_code,
            error_message=error_message,
            compliance_flags=self._get_compliance_flags(event_type, endpoint),
            nigerian_data_involved=self._involves_nigerian_data(endpoint, metadata),
            tax_data_involved=self._involves_tax_data(endpoint, metadata),
            retention_required=self._requires_retention(event_type),
            metadata=metadata or {}
        )
        
        self.compliance_events.append(event)
        
        # Update compliance violation counter
        if severity in [MonitoringLevel.CRITICAL, MonitoringLevel.HIGH]:
            if event_type in [ComplianceEventType.SECURITY_EVENT, ComplianceEventType.SYSTEM_ERROR]:
                self.security_incidents += 1
            else:
                self.compliance_violations += 1
    
    def _analyze_compliance_context(self, endpoint: str, context: Optional[Dict[str, Any]]) -> List[str]:
        """Analyze request for compliance flags."""
        flags = []
        
        if self._is_firs_submission(endpoint):
            flags.extend(["FIRS_SUBMISSION", "TAX_COMPLIANCE"])
        
        if self._involves_nigerian_data(endpoint, context):
            flags.append("NDPR_RELEVANT")
        
        if self._involves_certificates(endpoint):
            flags.append("CERTIFICATE_OPERATION")
        
        if self._involves_validation(endpoint):
            flags.append("DATA_VALIDATION")
        
        return flags
    
    def _involves_nigerian_data(self, endpoint: Optional[str], context: Optional[Dict[str, Any]]) -> bool:
        """Check if operation involves Nigerian-specific data."""
        if not endpoint:
            return False
        
        nigerian_indicators = [
            'tin', 'bvn', 'nin', 'nigeria', 'firs', 'party', 'business'
        ]
        
        endpoint_lower = endpoint.lower()
        if any(indicator in endpoint_lower for indicator in nigerian_indicators):
            return True
        
        if context:
            context_str = str(context).lower()
            return any(indicator in context_str for indicator in nigerian_indicators)
        
        return False
    
    def _involves_tax_data(self, endpoint: Optional[str], context: Optional[Dict[str, Any]]) -> bool:
        """Check if operation involves tax-related data."""
        if not endpoint:
            return False
        
        tax_indicators = ['invoice', 'tax', 'vat', 'submission', 'irn', 'firs']
        
        endpoint_lower = endpoint.lower()
        return any(indicator in endpoint_lower for indicator in tax_indicators)
    
    def _is_security_relevant(self, endpoint: str, status_code: int) -> bool:
        """Check if request is security-relevant."""
        security_endpoints = ['auth', 'login', 'token', 'certificate', 'key']
        
        if any(sec in endpoint.lower() for sec in security_endpoints):
            return True
        
        # Failed authentication attempts
        if status_code in [401, 403]:
            return True
        
        return False
    
    def _is_firs_submission(self, endpoint: str) -> bool:
        """Check if endpoint is a FIRS submission."""
        submission_indicators = ['submit', 'transmit', 'invoice', 'sign']
        return any(indicator in endpoint.lower() for indicator in submission_indicators)
    
    def _involves_certificates(self, endpoint: str) -> bool:
        """Check if endpoint involves certificate operations."""
        return 'certificate' in endpoint.lower() or 'cert' in endpoint.lower()
    
    def _involves_validation(self, endpoint: str) -> bool:
        """Check if endpoint involves validation operations."""
        return 'validate' in endpoint.lower() or 'verify' in endpoint.lower()
    
    def _categorize_error(self, status_code: int, error_message: str) -> str:
        """Categorize error for better analysis."""
        if status_code == 400:
            return "validation_error"
        elif status_code == 401:
            return "authentication_error"
        elif status_code == 403:
            return "authorization_error"
        elif status_code == 404:
            return "resource_not_found"
        elif status_code == 429:
            return "rate_limit_exceeded"
        elif 500 <= status_code < 600:
            return "server_error"
        else:
            return "unknown_error"
    
    def _assess_compliance_impact(self, endpoint: str, status_code: int) -> str:
        """Assess compliance impact of error."""
        if self._is_firs_submission(endpoint) and status_code >= 400:
            return "high_impact"  # Failed FIRS submission
        elif self._involves_tax_data(endpoint, None) and status_code >= 400:
            return "medium_impact"  # Tax data operation failed
        else:
            return "low_impact"
    
    def _determine_error_severity(self, status_code: int, error_message: str) -> MonitoringLevel:
        """Determine error severity for compliance tracking."""
        if status_code >= 500:
            return MonitoringLevel.HIGH
        elif status_code in [401, 403]:
            return MonitoringLevel.HIGH  # Security-related
        elif status_code == 429:
            return MonitoringLevel.MEDIUM
        else:
            return MonitoringLevel.LOW
    
    def _get_compliance_flags(self, event_type: ComplianceEventType, endpoint: Optional[str]) -> List[str]:
        """Get compliance flags for event."""
        flags = []
        
        if event_type == ComplianceEventType.FIRS_SUBMISSION:
            flags.extend(["TAX_COMPLIANCE", "RETENTION_REQUIRED"])
        
        if event_type == ComplianceEventType.NDPR_DATA_PROCESSING:
            flags.extend(["NDPR_COMPLIANCE", "PRIVACY_RELEVANT"])
        
        if event_type == ComplianceEventType.SECURITY_EVENT:
            flags.extend(["ISO27001_RELEVANT", "SECURITY_INCIDENT"])
        
        return flags
    
    def _requires_retention(self, event_type: ComplianceEventType) -> bool:
        """Check if event requires long-term retention."""
        retention_required_events = [
            ComplianceEventType.FIRS_SUBMISSION,
            ComplianceEventType.TAX_DATA_ACCESS,
            ComplianceEventType.SECURITY_EVENT,
            ComplianceEventType.CERTIFICATE_OPERATION
        ]
        return event_type in retention_required_events
    
    def get_enhanced_performance_stats(self, timeframe_minutes: Optional[int] = None) -> Dict[str, Any]:
        """Get enhanced performance statistics with compliance metrics."""
        base_stats = self.get_performance_stats(timeframe_minutes)
        
        # Add compliance-specific metrics
        compliance_stats = {
            "compliance_metrics": {
                "total_firs_submissions": self.firs_submissions,
                "tax_data_operations": self.tax_data_operations,
                "ndpr_relevant_operations": self.ndpr_relevant_operations,
                "compliance_violations": self.compliance_violations,
                "security_incidents": self.security_incidents,
                "compliance_events_count": len(self.compliance_events)
            },
            "nigerian_compliance": {
                "firs_submission_success_rate": self._calculate_firs_success_rate(),
                "ndpr_compliance_score": self._calculate_ndpr_score(),
                "tax_data_protection_level": self._assess_tax_data_protection()
            },
            "iso27001_metrics": {
                "security_incident_rate": self._calculate_security_incident_rate(),
                "availability_score": self._calculate_availability_score(),
                "performance_score": self._calculate_performance_score()
            }
        }
        
        return {**base_stats, **compliance_stats}
    
    def get_performance_stats(self, timeframe_minutes: Optional[int] = None) -> Dict[str, Any]:
        """Calculate performance statistics for API calls."""
        # Filter history based on timeframe if specified
        if timeframe_minutes is not None:
            cutoff_time = datetime.utcnow() - timedelta(minutes=timeframe_minutes)
            filtered_history = [
                req for req in self.request_history 
                if req['timestamp'] >= cutoff_time
            ]
        else:
            filtered_history = list(self.request_history)
        
        # Handle empty history
        if not filtered_history:
            return {
                'request_count': 0,
                'avg_duration_ms': 0,
                'min_duration_ms': 0,
                'max_duration_ms': 0,
                'p95_duration_ms': 0,
                'success_rate': 0.0,
                'error_rate': 0.0,
                'slow_request_count': 0,
                'timeframe_minutes': timeframe_minutes
            }
        
        # Calculate stats
        durations = [req['duration_ms'] for req in filtered_history]
        durations.sort()
        
        success_count = sum(1 for req in filtered_history if 200 <= req['status_code'] < 300)
        error_count = len(filtered_history) - success_count
        slow_count = sum(1 for req in filtered_history if req['is_slow'])
        
        # Calculate p95 (95th percentile)
        p95_index = int(len(durations) * 0.95)
        if p95_index >= len(durations):
            p95_index = len(durations) - 1
        
        return {
            'request_count': len(filtered_history),
            'avg_duration_ms': statistics.mean(durations) if durations else 0,
            'min_duration_ms': min(durations) if durations else 0,
            'max_duration_ms': max(durations) if durations else 0,
            'p95_duration_ms': durations[p95_index] if durations else 0,
            'success_rate': (success_count / len(filtered_history)) * 100 if filtered_history else 0,
            'error_rate': (error_count / len(filtered_history)) * 100 if filtered_history else 0,
            'slow_request_count': slow_count,
            'timeframe_minutes': timeframe_minutes
        }
    
    def _calculate_firs_success_rate(self) -> float:
        """Calculate FIRS submission success rate."""
        firs_requests = [req for req in self.request_history if self._is_firs_submission(req['endpoint'])]
        if not firs_requests:
            return 100.0
        
        successful = sum(1 for req in firs_requests if 200 <= req['status_code'] < 300)
        return (successful / len(firs_requests)) * 100
    
    def _calculate_ndpr_score(self) -> float:
        """Calculate NDPR compliance score."""
        # Simplified scoring based on Nigerian data operations
        if self.ndpr_relevant_operations == 0:
            return 100.0
        
        # Calculate based on successful operations vs violations
        violations = sum(1 for event in self.compliance_events 
                        if event.event_type == ComplianceEventType.NDPR_DATA_PROCESSING 
                        and event.severity in [MonitoringLevel.HIGH, MonitoringLevel.CRITICAL])
        
        score = max(0, 100 - (violations / self.ndpr_relevant_operations * 100))
        return min(100, score)
    
    def _assess_tax_data_protection(self) -> str:
        """Assess tax data protection level."""
        if self.tax_data_operations == 0:
            return "not_applicable"
        
        violations = sum(1 for event in self.compliance_events 
                        if event.tax_data_involved and 
                        event.severity in [MonitoringLevel.HIGH, MonitoringLevel.CRITICAL])
        
        violation_rate = violations / self.tax_data_operations
        
        if violation_rate == 0:
            return "excellent"
        elif violation_rate < 0.01:
            return "good"
        elif violation_rate < 0.05:
            return "acceptable"
        else:
            return "needs_improvement"
    
    def _calculate_security_incident_rate(self) -> float:
        """Calculate security incident rate per 1000 requests."""
        if self.total_requests == 0:
            return 0.0
        
        return (self.security_incidents / self.total_requests) * 1000
    
    def _calculate_availability_score(self) -> float:
        """Calculate service availability score."""
        if self.total_requests == 0:
            return 100.0
        
        return (self.successful_requests / self.total_requests) * 100
    
    def _calculate_performance_score(self) -> float:
        """Calculate performance score based on response times."""
        if not self.request_history:
            return 100.0
        
        slow_requests = sum(1 for req in self.request_history if req['is_slow'])
        total_requests = len(self.request_history)
        
        return max(0, 100 - (slow_requests / total_requests * 100))
    
    def get_compliance_report(self) -> Dict[str, Any]:
        """Generate comprehensive compliance monitoring report."""
        return {
            "report_generated": datetime.utcnow().isoformat(),
            "monitoring_period": {
                "start_time": self.start_time.isoformat(),
                "duration_hours": (datetime.utcnow() - self.start_time).total_seconds() / 3600
            },
            "operational_metrics": self.get_enhanced_performance_stats(),
            "compliance_events": {
                "total_events": len(self.compliance_events),
                "by_type": self._group_events_by_type(),
                "by_severity": self._group_events_by_severity(),
                "retention_summary": self._get_retention_summary()
            },
            "nigerian_compliance": {
                "firs_operations": self.firs_submissions,
                "ndpr_relevant_ops": self.ndpr_relevant_operations,
                "tax_data_ops": self.tax_data_operations,
                "compliance_score": self._calculate_overall_compliance_score()
            },
            "security_summary": {
                "incidents": self.security_incidents,
                "violations": self.compliance_violations,
                "risk_level": self._assess_risk_level()
            },
            "recommendations": self._generate_recommendations()
        }
    
    def _group_events_by_type(self) -> Dict[str, int]:
        """Group compliance events by type."""
        return Counter(event.event_type.value for event in self.compliance_events)
    
    def _group_events_by_severity(self) -> Dict[str, int]:
        """Group compliance events by severity."""
        return Counter(event.severity.value for event in self.compliance_events)
    
    def _get_retention_summary(self) -> Dict[str, Any]:
        """Get retention requirements summary."""
        retention_required = sum(1 for event in self.compliance_events if event.retention_required)
        
        return {
            "events_requiring_retention": retention_required,
            "retention_period_days": self.compliance_retention_days,
            "estimated_storage_gb": retention_required * 0.001  # Rough estimate
        }
    
    def _calculate_overall_compliance_score(self) -> float:
        """Calculate overall compliance score."""
        if self.total_requests == 0:
            return 100.0
        
        # Weight different compliance aspects
        firs_score = self._calculate_firs_success_rate() * 0.4
        ndpr_score = self._calculate_ndpr_score() * 0.3
        security_score = (100 - self._calculate_security_incident_rate()) * 0.3
        
        return min(100, firs_score + ndpr_score + security_score)
    
    def _assess_risk_level(self) -> str:
        """Assess overall risk level."""
        critical_events = sum(1 for event in self.compliance_events 
                            if event.severity == MonitoringLevel.CRITICAL)
        high_events = sum(1 for event in self.compliance_events 
                         if event.severity == MonitoringLevel.HIGH)
        
        if critical_events > 0:
            return "critical"
        elif high_events > 5:
            return "high"
        elif self.compliance_violations > 10:
            return "medium"
        else:
            return "low"
    
    def _generate_recommendations(self) -> List[str]:
        """Generate monitoring recommendations."""
        recommendations = []
        
        # Performance recommendations
        if self._calculate_performance_score() < 90:
            recommendations.append("Review API performance optimization")
        
        # Security recommendations
        if self.security_incidents > 0:
            recommendations.append("Investigate recent security incidents")
        
        # Compliance recommendations
        if self._calculate_firs_success_rate() < 95:
            recommendations.append("Improve FIRS submission reliability")
        
        if self._calculate_ndpr_score() < 90:
            recommendations.append("Review NDPR compliance procedures")
        
        # General recommendations
        recommendations.extend([
            "Maintain 7-year retention for tax-related compliance events",
            "Regular review of Nigerian compliance requirements",
            "Monitor FIRS API changes and updates",
            "Ensure ISO 27001 controls are tested regularly"
        ])
        
        return recommendations
    
    def enhanced_monitoring_decorator(self, 
                                    sandbox: bool = True, 
                                    compliance_tracking: bool = True):
        """
        Create enhanced decorator for FIRS API monitoring with compliance tracking.
        
        Args:
            sandbox: Whether the API is in sandbox mode
            compliance_tracking: Whether to enable compliance event tracking
        
        Returns:
            Enhanced decorator function
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                environment = "sandbox" if sandbox else "production"
                endpoint = func.__name__
                start_time = time.time()
                request_id = kwargs.get('request_id')
                organization_id = kwargs.get('organization_id')
                user_id = kwargs.get('user_id')
                error_message = None
                status_code = 0
                compliance_context = kwargs.get('compliance_context', {})
                
                try:
                    # Call the original function
                    result = await func(*args, **kwargs)
                    
                    # Extract status code if result has it
                    if hasattr(result, 'status_code'):
                        status_code = result.status_code
                    else:
                        status_code = 200
                    
                    return result
                    
                except Exception as e:
                    error_message = str(e)
                    if hasattr(e, 'status_code'):
                        status_code = e.status_code
                    else:
                        status_code = 500
                    
                    raise
                    
                finally:
                    # Calculate duration and record request
                    end_time = time.time()
                    duration_ms = (end_time - start_time) * 1000
                    
                    self.record_enhanced_request(
                        endpoint=endpoint,
                        method='ASYNC',
                        duration_ms=duration_ms,
                        status_code=status_code,
                        environment=environment,
                        request_id=request_id,
                        organization_id=organization_id,
                        user_id=user_id,
                        error=error_message,
                        compliance_context=compliance_context
                    )
                    
                    # Record compliance events if enabled
                    if compliance_tracking:
                        self._record_api_compliance_event(
                            endpoint, status_code, duration_ms, 
                            organization_id, user_id, request_id
                        )
            
            return wrapper
        
        return decorator
    
    def _record_api_compliance_event(self, 
                                   endpoint: str, 
                                   status_code: int, 
                                   duration_ms: float,
                                   organization_id: Optional[str],
                                   user_id: Optional[str],
                                   request_id: Optional[str]):
        """Record compliance event for API call."""
        
        # Determine event type based on endpoint
        if self._is_firs_submission(endpoint):
            event_type = ComplianceEventType.FIRS_SUBMISSION
        elif self._involves_validation(endpoint):
            event_type = ComplianceEventType.INVOICE_VALIDATION
        elif self._involves_certificates(endpoint):
            event_type = ComplianceEventType.CERTIFICATE_OPERATION
        else:
            return  # Don't record compliance event for non-compliance operations
        
        # Determine severity
        if status_code >= 400:
            severity = MonitoringLevel.HIGH if status_code >= 500 else MonitoringLevel.MEDIUM
        elif duration_ms > self.slow_threshold_ms:
            severity = MonitoringLevel.MEDIUM
        else:
            severity = MonitoringLevel.LOW
        
        self._record_compliance_event(
            event_type=event_type,
            severity=severity,
            endpoint=endpoint,
            request_id=request_id,
            organization_id=organization_id,
            user_id=user_id,
            duration_ms=duration_ms,
            status_code=status_code
        )


# Create enhanced global monitoring instance
firs_core_monitor = FIRSCoreAPIMonitor()

# Enhanced decorator instances
monitor_sandbox_api_enhanced = firs_core_monitor.enhanced_monitoring_decorator(sandbox=True)
monitor_production_api_enhanced = firs_core_monitor.enhanced_monitoring_decorator(sandbox=False)

# Backward compatibility decorators
monitor_sandbox_api = firs_core_monitor.enhanced_monitoring_decorator(sandbox=True, compliance_tracking=False)
monitor_production_api = firs_core_monitor.enhanced_monitoring_decorator(sandbox=False, compliance_tracking=False)
