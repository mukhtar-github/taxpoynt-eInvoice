"""
Security Monitor for Banking Operations
======================================
Real-time security monitoring and threat detection system for banking
operations. Provides comprehensive security alerting, anomaly detection,
and incident response capabilities.

Key Features:
- Real-time threat detection
- Anomaly detection and behavioral analysis
- Security alerting and incident response
- Attack pattern recognition
- Compliance security monitoring
- Automated security responses
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum
from dataclasses import dataclass, field
import json
import hashlib
import uuid
from collections import defaultdict, deque

from ....shared.logging import get_logger
from ....shared.exceptions import IntegrationError


class ThreatLevel(Enum):
    """Security threat levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class SecurityEventType(Enum):
    """Types of security events."""
    AUTHENTICATION_FAILURE = "authentication_failure"
    AUTHORIZATION_VIOLATION = "authorization_violation"
    SUSPICIOUS_LOGIN = "suspicious_login"
    BRUTE_FORCE_ATTACK = "brute_force_attack"
    ACCOUNT_LOCKOUT = "account_lockout"
    UNUSUAL_ACCESS_PATTERN = "unusual_access_pattern"
    DATA_EXFILTRATION = "data_exfiltration"
    API_ABUSE = "api_abuse"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    MALICIOUS_REQUEST = "malicious_request"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    CONFIGURATION_TAMPERING = "configuration_tampering"
    SYSTEM_INTRUSION = "system_intrusion"
    DDoS_ATTACK = "ddos_attack"
    SQL_INJECTION = "sql_injection"
    XSS_ATTEMPT = "xss_attempt"
    CSRF_ATTACK = "csrf_attack"
    SESSION_HIJACKING = "session_hijacking"


class AlertStatus(Enum):
    """Status of security alerts."""
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    ESCALATED = "escalated"
    SUPPRESSED = "suppressed"


@dataclass
class SecurityAlert:
    """Security alert record."""
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: SecurityEventType = SecurityEventType.SUSPICIOUS_LOGIN
    threat_level: ThreatLevel = ThreatLevel.MEDIUM
    title: str = ""
    description: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    status: AlertStatus = AlertStatus.OPEN
    
    # Source information
    source_ip: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Resource information
    affected_resources: List[str] = field(default_factory=list)
    account_ids: List[str] = field(default_factory=list)
    transaction_ids: List[str] = field(default_factory=list)
    
    # Attack details
    attack_vector: Optional[str] = None
    indicators_of_compromise: List[str] = field(default_factory=list)
    attack_pattern: Optional[str] = None
    
    # Response information
    automated_response: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    assigned_to: Optional[str] = None
    resolution_time: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    
    # Evidence and context
    evidence: Dict[str, Any] = field(default_factory=dict)
    related_events: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ThreatPattern:
    """Threat detection pattern."""
    pattern_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pattern_name: str = ""
    pattern_type: str = ""  # behavioral, signature, statistical
    event_types: List[SecurityEventType] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)
    threshold: float = 0.0
    time_window_minutes: int = 60
    threat_level: ThreatLevel = ThreatLevel.MEDIUM
    enabled: bool = True
    confidence_threshold: float = 0.7
    
    # Pattern matching
    required_fields: List[str] = field(default_factory=list)
    pattern_rules: List[Dict[str, Any]] = field(default_factory=list)
    
    # Response configuration
    auto_response_enabled: bool = False
    response_actions: List[str] = field(default_factory=list)


@dataclass
class SecurityMetrics:
    """Security monitoring metrics."""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    total_events: int = 0
    alerts_generated: int = 0
    threats_detected: int = 0
    false_positives: int = 0
    mean_detection_time: float = 0.0
    mean_response_time: float = 0.0
    
    # Threat level distribution
    critical_alerts: int = 0
    high_alerts: int = 0
    medium_alerts: int = 0
    low_alerts: int = 0
    
    # Top threat types
    top_threat_types: Dict[str, int] = field(default_factory=dict)
    top_source_ips: Dict[str, int] = field(default_factory=dict)
    top_user_agents: Dict[str, int] = field(default_factory=dict)


class SecurityMonitor:
    """
    Comprehensive security monitoring system for banking operations.
    
    This monitor provides real-time threat detection, anomaly analysis,
    and automated incident response capabilities to protect banking
    systems from security threats and attacks.
    """
    
    def __init__(self):
        """Initialize security monitor."""
        self.logger = get_logger(__name__)
        
        # Alert storage
        self.active_alerts: Dict[str, SecurityAlert] = {}
        self.alert_history: List[SecurityAlert] = []
        self.threat_patterns: Dict[str, ThreatPattern] = {}
        
        # Event tracking
        self.recent_events: deque = deque(maxlen=10000)
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
        self.ip_activity: Dict[str, Dict[str, Any]] = {}
        
        # Behavioral baselines
        self.user_baselines: Dict[str, Dict[str, Any]] = {}
        self.system_baselines: Dict[str, Any] = {}
        
        # Configuration
        self.monitoring_enabled = True
        self.auto_response_enabled = True
        self.alert_threshold_scores = {
            ThreatLevel.LOW: 0.3,
            ThreatLevel.MEDIUM: 0.5,
            ThreatLevel.HIGH: 0.7,
            ThreatLevel.CRITICAL: 0.9
        }
        
        # Response handlers
        self.response_handlers: Dict[str, Callable] = {}
        
        # Metrics
        self.metrics = SecurityMetrics()
        
        self.logger.info("Initialized security monitor")
        
        # Set up default threat patterns
        self._setup_default_threat_patterns()
    
    async def process_security_event(
        self,
        event_data: Dict[str, Any]
    ) -> Optional[SecurityAlert]:
        """
        Process security event and generate alerts if needed.
        
        Args:
            event_data: Security event data
            
        Returns:
            Generated security alert if any
        """
        try:
            if not self.monitoring_enabled:
                return None
            
            # Add event to recent events
            event_data['timestamp'] = datetime.utcnow()
            self.recent_events.append(event_data)
            
            # Update metrics
            self.metrics.total_events += 1
            
            # Update user and IP tracking
            await self._update_activity_tracking(event_data)
            
            # Check against threat patterns
            detected_threats = await self._detect_threats(event_data)
            
            # Generate alerts for detected threats
            alerts = []
            for threat_info in detected_threats:
                alert = await self._generate_security_alert(threat_info, event_data)
                if alert:
                    alerts.append(alert)
            
            # Return the highest priority alert
            if alerts:
                alerts.sort(key=lambda x: self._get_threat_priority(x.threat_level), reverse=True)
                return alerts[0]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Security event processing failed: {str(e)}")
            raise IntegrationError(f"Security event processing failed: {str(e)}")
    
    async def detect_brute_force_attack(
        self,
        user_id: str,
        ip_address: str,
        time_window_minutes: int = 15,
        failure_threshold: int = 5
    ) -> Optional[SecurityAlert]:
        """
        Detect brute force authentication attacks.
        
        Args:
            user_id: User identifier
            ip_address: Source IP address
            time_window_minutes: Time window for analysis
            failure_threshold: Failure count threshold
            
        Returns:
            Security alert if attack detected
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
            
            # Count recent authentication failures
            recent_failures = [
                event for event in self.recent_events
                if (event.get('timestamp', datetime.min) > cutoff_time and
                    event.get('event_type') == 'authentication_failure' and
                    (event.get('user_id') == user_id or event.get('ip_address') == ip_address))
            ]
            
            if len(recent_failures) >= failure_threshold:
                # Generate brute force alert
                alert = SecurityAlert(
                    event_type=SecurityEventType.BRUTE_FORCE_ATTACK,
                    threat_level=ThreatLevel.HIGH,
                    title=f"Brute Force Attack Detected",
                    description=f"Multiple authentication failures ({len(recent_failures)}) detected for user {user_id} from IP {ip_address}",
                    source_ip=ip_address,
                    user_id=user_id,
                    indicators_of_compromise=[
                        f"authentication_failures:{len(recent_failures)}",
                        f"time_window:{time_window_minutes}min",
                        f"source_ip:{ip_address}"
                    ],
                    attack_pattern="brute_force_authentication",
                    automated_response=["account_lockout", "ip_blocking"],
                    recommended_actions=[
                        "Lock user account temporarily",
                        "Block source IP address",
                        "Notify user of suspicious activity",
                        "Review account security"
                    ],
                    confidence_score=0.9,
                    evidence={
                        "failure_count": len(recent_failures),
                        "time_window": time_window_minutes,
                        "threshold": failure_threshold,
                        "recent_failures": [
                            {
                                "timestamp": event.get('timestamp', '').isoformat() if hasattr(event.get('timestamp', ''), 'isoformat') else str(event.get('timestamp', '')),
                                "ip_address": event.get('ip_address'),
                                "user_agent": event.get('user_agent')
                            }
                            for event in recent_failures[-10:]  # Last 10 failures
                        ]
                    }
                )
                
                await self._store_alert(alert)
                
                # Execute automated response
                if self.auto_response_enabled:
                    await self._execute_automated_response(alert)
                
                return alert
            
            return None
            
        except Exception as e:
            self.logger.error(f"Brute force detection failed: {str(e)}")
            return None
    
    async def detect_unusual_access_pattern(
        self,
        user_id: str,
        access_data: Dict[str, Any]
    ) -> Optional[SecurityAlert]:
        """
        Detect unusual access patterns based on user behavior baseline.
        
        Args:
            user_id: User identifier
            access_data: Access event data
            
        Returns:
            Security alert if unusual pattern detected
        """
        try:
            # Get or create user baseline
            baseline = self.user_baselines.get(user_id, {})
            
            if not baseline:
                # Initialize baseline
                await self._initialize_user_baseline(user_id)
                return None
            
            anomaly_score = 0.0
            anomalies = []
            
            # Check access time patterns
            current_hour = datetime.utcnow().hour
            typical_hours = baseline.get('typical_access_hours', [])
            
            if typical_hours and current_hour not in typical_hours:
                anomaly_score += 0.3
                anomalies.append(f"access_time:{current_hour}:00")
            
            # Check location patterns
            current_ip = access_data.get('ip_address')
            if current_ip:
                typical_ips = baseline.get('typical_ip_addresses', [])
                if typical_ips and current_ip not in typical_ips:
                    anomaly_score += 0.4
                    anomalies.append(f"new_ip_address:{current_ip}")
            
            # Check device patterns
            current_user_agent = access_data.get('user_agent')
            if current_user_agent:
                typical_agents = baseline.get('typical_user_agents', [])
                if typical_agents and current_user_agent not in typical_agents:
                    anomaly_score += 0.2
                    anomalies.append(f"new_user_agent")
            
            # Check access frequency
            recent_access_count = len([
                event for event in self.recent_events
                if (event.get('user_id') == user_id and
                    event.get('timestamp', datetime.min) > datetime.utcnow() - timedelta(hours=1))
            ])
            
            typical_frequency = baseline.get('typical_hourly_frequency', 5)
            if recent_access_count > typical_frequency * 3:
                anomaly_score += 0.3
                anomalies.append(f"high_frequency:{recent_access_count}")
            
            # Generate alert if anomaly score is high
            if anomaly_score >= 0.6:
                alert = SecurityAlert(
                    event_type=SecurityEventType.UNUSUAL_ACCESS_PATTERN,
                    threat_level=ThreatLevel.MEDIUM if anomaly_score < 0.8 else ThreatLevel.HIGH,
                    title="Unusual Access Pattern Detected",
                    description=f"Anomalous access behavior detected for user {user_id}",
                    source_ip=current_ip,
                    user_id=user_id,
                    user_agent=current_user_agent,
                    indicators_of_compromise=anomalies,
                    attack_pattern="behavioral_anomaly",
                    recommended_actions=[
                        "Verify user identity",
                        "Check for account compromise",
                        "Review recent activity",
                        "Consider additional authentication"
                    ],
                    confidence_score=anomaly_score,
                    evidence={
                        "anomaly_score": anomaly_score,
                        "detected_anomalies": anomalies,
                        "baseline_data": baseline,
                        "current_access": access_data
                    }
                )
                
                await self._store_alert(alert)
                return alert
            
            # Update baseline with new data
            await self._update_user_baseline(user_id, access_data)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Unusual access pattern detection failed: {str(e)}")
            return None
    
    async def detect_api_abuse(
        self,
        api_endpoint: str,
        ip_address: str,
        time_window_minutes: int = 5,
        request_threshold: int = 100
    ) -> Optional[SecurityAlert]:
        """
        Detect API abuse and potential DDoS attacks.
        
        Args:
            api_endpoint: API endpoint being accessed
            ip_address: Source IP address
            time_window_minutes: Time window for analysis
            request_threshold: Request count threshold
            
        Returns:
            Security alert if abuse detected
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
            
            # Count recent API requests
            recent_requests = [
                event for event in self.recent_events
                if (event.get('timestamp', datetime.min) > cutoff_time and
                    event.get('api_endpoint') == api_endpoint and
                    event.get('ip_address') == ip_address)
            ]
            
            if len(recent_requests) >= request_threshold:
                # Determine threat level based on request volume
                if len(recent_requests) > request_threshold * 5:
                    threat_level = ThreatLevel.CRITICAL
                    event_type = SecurityEventType.DDoS_ATTACK
                elif len(recent_requests) > request_threshold * 2:
                    threat_level = ThreatLevel.HIGH
                    event_type = SecurityEventType.API_ABUSE
                else:
                    threat_level = ThreatLevel.MEDIUM
                    event_type = SecurityEventType.RATE_LIMIT_EXCEEDED
                
                alert = SecurityAlert(
                    event_type=event_type,
                    threat_level=threat_level,
                    title=f"API Abuse Detected - {api_endpoint}",
                    description=f"Excessive API requests ({len(recent_requests)}) from IP {ip_address} to {api_endpoint}",
                    source_ip=ip_address,
                    affected_resources=[api_endpoint],
                    indicators_of_compromise=[
                        f"request_count:{len(recent_requests)}",
                        f"api_endpoint:{api_endpoint}",
                        f"source_ip:{ip_address}"
                    ],
                    attack_pattern="api_abuse" if event_type == SecurityEventType.API_ABUSE else "ddos_attack",
                    automated_response=["rate_limiting", "ip_blocking"],
                    recommended_actions=[
                        "Implement rate limiting",
                        "Block or throttle source IP",
                        "Monitor for continued abuse",
                        "Review API security"
                    ],
                    confidence_score=0.95,
                    evidence={
                        "request_count": len(recent_requests),
                        "threshold": request_threshold,
                        "time_window": time_window_minutes,
                        "api_endpoint": api_endpoint,
                        "request_timestamps": [
                            event.get('timestamp', '').isoformat() if hasattr(event.get('timestamp', ''), 'isoformat') else str(event.get('timestamp', ''))
                            for event in recent_requests[-20:]  # Last 20 requests
                        ]
                    }
                )
                
                await self._store_alert(alert)
                
                # Execute automated response
                if self.auto_response_enabled:
                    await self._execute_automated_response(alert)
                
                return alert
            
            return None
            
        except Exception as e:
            self.logger.error(f"API abuse detection failed: {str(e)}")
            return None
    
    async def get_security_dashboard(self) -> Dict[str, Any]:
        """
        Get comprehensive security dashboard data.
        
        Returns:
            Security dashboard metrics and status
        """
        try:
            now = datetime.utcnow()
            
            # Count alerts by status
            alert_counts = {
                "total": len(self.active_alerts),
                "open": len([a for a in self.active_alerts.values() if a.status == AlertStatus.OPEN]),
                "investigating": len([a for a in self.active_alerts.values() if a.status == AlertStatus.INVESTIGATING]),
                "resolved": len([a for a in self.active_alerts.values() if a.status == AlertStatus.RESOLVED])
            }
            
            # Count alerts by threat level
            threat_level_counts = {
                "critical": len([a for a in self.active_alerts.values() if a.threat_level == ThreatLevel.CRITICAL]),
                "high": len([a for a in self.active_alerts.values() if a.threat_level == ThreatLevel.HIGH]),
                "medium": len([a for a in self.active_alerts.values() if a.threat_level == ThreatLevel.MEDIUM]),
                "low": len([a for a in self.active_alerts.values() if a.threat_level == ThreatLevel.LOW])
            }
            
            # Recent activity (last 24 hours)
            recent_cutoff = now - timedelta(hours=24)
            recent_alerts = [
                a for a in self.alert_history
                if a.timestamp > recent_cutoff
            ]
            
            # Top threat types
            threat_type_counts = defaultdict(int)
            for alert in recent_alerts:
                threat_type_counts[alert.event_type.value] += 1
            
            # Top source IPs
            source_ip_counts = defaultdict(int)
            for alert in recent_alerts:
                if alert.source_ip:
                    source_ip_counts[alert.source_ip] += 1
            
            # Calculate metrics
            total_events_24h = len([
                event for event in self.recent_events
                if event.get('timestamp', datetime.min) > recent_cutoff
            ])
            
            detection_rate = (len(recent_alerts) / total_events_24h * 100) if total_events_24h > 0 else 0
            
            return {
                "timestamp": now.isoformat(),
                "monitoring_status": "active" if self.monitoring_enabled else "disabled",
                "alert_summary": alert_counts,
                "threat_levels": threat_level_counts,
                "recent_activity": {
                    "total_events_24h": total_events_24h,
                    "alerts_24h": len(recent_alerts),
                    "detection_rate": round(detection_rate, 2)
                },
                "top_threats": dict(sorted(threat_type_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
                "top_source_ips": dict(sorted(source_ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
                "system_health": {
                    "patterns_active": len([p for p in self.threat_patterns.values() if p.enabled]),
                    "auto_response_enabled": self.auto_response_enabled,
                    "baseline_users": len(self.user_baselines)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Security dashboard generation failed: {str(e)}")
            raise IntegrationError(f"Dashboard generation failed: {str(e)}")
    
    def _setup_default_threat_patterns(self) -> None:
        """Set up default threat detection patterns."""
        # Brute force pattern
        self.threat_patterns["brute_force"] = ThreatPattern(
            pattern_name="Brute Force Authentication",
            pattern_type="statistical",
            event_types=[SecurityEventType.AUTHENTICATION_FAILURE],
            threshold=5,
            time_window_minutes=15,
            threat_level=ThreatLevel.HIGH,
            auto_response_enabled=True,
            response_actions=["account_lockout", "ip_blocking"]
        )
        
        # API abuse pattern
        self.threat_patterns["api_abuse"] = ThreatPattern(
            pattern_name="API Rate Limit Abuse",
            pattern_type="statistical",
            event_types=[SecurityEventType.RATE_LIMIT_EXCEEDED],
            threshold=100,
            time_window_minutes=5,
            threat_level=ThreatLevel.MEDIUM,
            auto_response_enabled=True,
            response_actions=["rate_limiting", "ip_blocking"]
        )
        
        # Suspicious login pattern
        self.threat_patterns["suspicious_login"] = ThreatPattern(
            pattern_name="Suspicious Login Behavior",
            pattern_type="behavioral",
            event_types=[SecurityEventType.SUSPICIOUS_LOGIN],
            threshold=0.6,
            time_window_minutes=60,
            threat_level=ThreatLevel.MEDIUM,
            confidence_threshold=0.7
        )
    
    async def _detect_threats(self, event_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect threats based on patterns."""
        detected_threats = []
        
        for pattern in self.threat_patterns.values():
            if not pattern.enabled:
                continue
            
            threat_info = await self._check_pattern_match(pattern, event_data)
            if threat_info:
                detected_threats.append(threat_info)
        
        return detected_threats
    
    async def _check_pattern_match(
        self,
        pattern: ThreatPattern,
        event_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check if event matches threat pattern."""
        # This is a simplified pattern matching implementation
        # In a real system, this would be more sophisticated
        
        event_type_str = event_data.get('event_type', '')
        if event_type_str not in [et.value for et in pattern.event_types]:
            return None
        
        # Pattern-specific logic would go here
        confidence = 0.8  # Simplified confidence calculation
        
        if confidence >= pattern.confidence_threshold:
            return {
                "pattern": pattern,
                "confidence": confidence,
                "event_data": event_data
            }
        
        return None
    
    def _get_threat_priority(self, threat_level: ThreatLevel) -> int:
        """Get numeric priority for threat level."""
        priority_map = {
            ThreatLevel.LOW: 1,
            ThreatLevel.MEDIUM: 2,
            ThreatLevel.HIGH: 3,
            ThreatLevel.CRITICAL: 4,
            ThreatLevel.EMERGENCY: 5
        }
        return priority_map.get(threat_level, 0)