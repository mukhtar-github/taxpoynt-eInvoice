"""
Session Manager Service

This service manages user session lifecycle, providing secure session management
with support for multiple devices, session tracking, and security features.
"""

import asyncio
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
import uuid
from ipaddress import ip_address, ip_network

from taxpoynt_platform.core_platform.shared.base_service import BaseService
from taxpoynt_platform.core_platform.shared.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    SecurityError
)


class SessionStatus(Enum):
    """Session status definitions"""
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    SUSPENDED = "suspended"
    LOCKED = "locked"


class SessionType(Enum):
    """Session type definitions"""
    WEB = "web"
    MOBILE = "mobile"
    API = "api"
    DESKTOP = "desktop"
    SERVICE = "service"


class DeviceType(Enum):
    """Device type definitions"""
    WEB_BROWSER = "web_browser"
    MOBILE_APP = "mobile_app"
    DESKTOP_APP = "desktop_app"
    API_CLIENT = "api_client"
    SERVICE_CLIENT = "service_client"
    UNKNOWN = "unknown"


class SecurityLevel(Enum):
    """Security level definitions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DeviceInfo:
    """Device information"""
    device_id: str
    device_type: DeviceType
    device_name: Optional[str] = None
    os_name: Optional[str] = None
    os_version: Optional[str] = None
    browser_name: Optional[str] = None
    browser_version: Optional[str] = None
    app_version: Optional[str] = None
    user_agent: Optional[str] = None
    screen_resolution: Optional[str] = None
    trusted: bool = False
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionActivity:
    """Session activity record"""
    activity_id: str
    session_id: str
    activity_type: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    risk_score: float = 0.0


@dataclass
class Session:
    """User session"""
    session_id: str
    user_id: str
    session_type: SessionType
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(hours=8))
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_info: Optional[DeviceInfo] = None
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    tenant_id: Optional[str] = None
    roles: Set[str] = field(default_factory=set)
    permissions: Set[str] = field(default_factory=set)
    mfa_verified: bool = False
    idle_timeout: timedelta = field(default_factory=lambda: timedelta(minutes=30))
    absolute_timeout: timedelta = field(default_factory=lambda: timedelta(hours=8))
    concurrent_sessions_allowed: int = 5
    location: Optional[str] = None
    risk_score: float = 0.0
    flags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionSecurityPolicy:
    """Session security policy"""
    policy_id: str
    name: str
    description: str
    max_idle_time: timedelta = field(default_factory=lambda: timedelta(minutes=30))
    max_session_time: timedelta = field(default_factory=lambda: timedelta(hours=8))
    max_concurrent_sessions: int = 5
    require_mfa: bool = False
    ip_whitelist: Set[str] = field(default_factory=set)
    allowed_countries: Set[str] = field(default_factory=set)
    risk_threshold: float = 0.7
    device_trust_required: bool = False
    session_fixation_protection: bool = True
    secure_cookie_required: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    active: bool = True


@dataclass
class SessionMetrics:
    """Session metrics"""
    total_sessions: int = 0
    active_sessions: int = 0
    unique_users: int = 0
    average_session_duration: float = 0.0
    sessions_by_type: Dict[SessionType, int] = field(default_factory=dict)
    sessions_by_device: Dict[DeviceType, int] = field(default_factory=dict)
    high_risk_sessions: int = 0
    mfa_verified_sessions: int = 0
    terminated_sessions: int = 0
    expired_sessions: int = 0


class SessionManager(BaseService):
    """
    Session Manager Service
    
    Manages user session lifecycle, providing secure session management
    with support for multiple devices, session tracking, and security features.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        # Session storage
        self.sessions: Dict[str, Session] = {}
        self.user_sessions: Dict[str, List[str]] = {}  # user_id -> session_ids
        
        # Device management
        self.devices: Dict[str, DeviceInfo] = {}
        self.user_devices: Dict[str, Set[str]] = {}  # user_id -> device_ids
        
        # Security policies
        self.security_policies: Dict[str, SessionSecurityPolicy] = {}
        self.default_policy_id: Optional[str] = None
        
        # Activity tracking
        self.session_activities: Dict[str, List[SessionActivity]] = {}
        
        # Security features
        self.suspicious_ips: Set[str] = set()
        self.trusted_networks: Set[str] = set()
        self.blocked_user_agents: Set[str] = set()
        
        # Session tokens (additional layer)
        self.session_tokens: Dict[str, str] = {}  # session_id -> token
        
        # Background tasks
        self.background_tasks: Dict[str, asyncio.Task] = {}
        
        # Performance metrics
        self.metrics = {
            'sessions_created': 0,
            'sessions_terminated': 0,
            'sessions_expired': 0,
            'security_violations': 0,
            'mfa_verifications': 0,
            'device_registrations': 0,
            'high_risk_detections': 0,
            'concurrent_session_limits_hit': 0
        }
    
    async def initialize(self) -> None:
        """Initialize session manager"""
        try:
            self.logger.info("Initializing SessionManager")
            
            # Load default security policies
            await self._load_default_policies()
            
            # Load trusted networks
            await self._load_trusted_networks()
            
            # Start background workers
            await self._start_background_workers()
            
            self.logger.info("SessionManager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize SessionManager: {str(e)}")
            raise AuthenticationError(f"Initialization failed: {str(e)}")
    
    async def create_session(
        self,
        user_id: str,
        session_type: SessionType,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_info: Optional[DeviceInfo] = None,
        tenant_id: Optional[str] = None,
        roles: Optional[Set[str]] = None,
        permissions: Optional[Set[str]] = None,
        security_level: SecurityLevel = SecurityLevel.MEDIUM,
        policy_id: Optional[str] = None
    ) -> Session:
        """Create new user session"""
        try:
            # Generate session ID
            session_id = self._generate_session_id()
            
            # Check concurrent session limits
            await self._check_concurrent_session_limits(user_id)
            
            # Get security policy
            policy = await self._get_security_policy(policy_id or self.default_policy_id)
            
            # Perform security checks
            await self._perform_security_checks(user_id, ip_address, user_agent, device_info)
            
            # Calculate risk score
            risk_score = await self._calculate_risk_score(user_id, ip_address, user_agent, device_info)
            
            # Create session
            now = datetime.utcnow()
            session = Session(
                session_id=session_id,
                user_id=user_id,
                session_type=session_type,
                created_at=now,
                last_activity=now,
                expires_at=now + (policy.max_session_time if policy else timedelta(hours=8)),
                ip_address=ip_address,
                user_agent=user_agent,
                device_info=device_info,
                security_level=security_level,
                tenant_id=tenant_id,
                roles=roles or set(),
                permissions=permissions or set(),
                idle_timeout=policy.max_idle_time if policy else timedelta(minutes=30),
                absolute_timeout=policy.max_session_time if policy else timedelta(hours=8),
                concurrent_sessions_allowed=policy.max_concurrent_sessions if policy else 5,
                risk_score=risk_score
            )
            
            # Apply security policy requirements
            if policy:
                if policy.require_mfa:
                    session.flags.add('mfa_required')
                if policy.device_trust_required and device_info and not device_info.trusted:
                    session.flags.add('device_verification_required')
            
            # Store session
            self.sessions[session_id] = session
            
            # Add to user sessions
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = []
            self.user_sessions[user_id].append(session_id)
            
            # Register device if provided
            if device_info:
                await self._register_device(user_id, device_info)
            
            # Generate session token
            session_token = self._generate_session_token()
            self.session_tokens[session_id] = session_token
            
            # Log session creation
            await self._log_session_activity(
                session_id, "session_created", ip_address, user_agent,
                {'security_level': security_level.value, 'risk_score': risk_score}
            )
            
            self.metrics['sessions_created'] += 1
            self.logger.info(f"Session created: {session_id} for user {user_id}")
            
            return session
            
        except Exception as e:
            self.logger.error(f"Failed to create session for user {user_id}: {str(e)}")
            raise AuthenticationError(f"Session creation failed: {str(e)}")
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        try:
            if session_id not in self.sessions:
                return None
            
            session = self.sessions[session_id]
            
            # Check if session is still valid
            if not await self._is_session_valid(session):
                await self._terminate_session(session_id, "expired_or_invalid")
                return None
            
            return session
            
        except Exception as e:
            self.logger.error(f"Failed to get session {session_id}: {str(e)}")
            return None
    
    async def update_session_activity(
        self,
        session_id: str,
        activity_type: str = "activity",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update session activity"""
        try:
            if session_id not in self.sessions:
                return False
            
            session = self.sessions[session_id]
            
            # Update last activity
            session.last_activity = datetime.utcnow()
            
            # Extend expiration based on idle timeout
            new_expiry = datetime.utcnow() + session.idle_timeout
            absolute_expiry = session.created_at + session.absolute_timeout
            session.expires_at = min(new_expiry, absolute_expiry)
            
            # Security checks for activity
            if ip_address and ip_address != session.ip_address:
                # IP address changed - potential security concern
                risk_increase = await self._assess_ip_change_risk(session, ip_address)
                session.risk_score = min(1.0, session.risk_score + risk_increase)
                
                if session.risk_score > 0.8:
                    session.flags.add('high_risk')
                    await self._log_session_activity(
                        session_id, "ip_change_detected", ip_address, user_agent,
                        {'old_ip': session.ip_address, 'new_ip': ip_address, 'risk_score': session.risk_score}
                    )
            
            # Log activity
            await self._log_session_activity(session_id, activity_type, ip_address, user_agent, details)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update session activity {session_id}: {str(e)}")
            return False
    
    async def terminate_session(
        self,
        session_id: str,
        reason: str = "user_logout",
        terminated_by: str = "user"
    ) -> bool:
        """Terminate session"""
        try:
            return await self._terminate_session(session_id, reason, terminated_by)
            
        except Exception as e:
            self.logger.error(f"Failed to terminate session {session_id}: {str(e)}")
            return False
    
    async def terminate_user_sessions(
        self,
        user_id: str,
        except_session_id: Optional[str] = None,
        reason: str = "admin_termination",
        terminated_by: str = "admin"
    ) -> int:
        """Terminate all sessions for a user"""
        try:
            if user_id not in self.user_sessions:
                return 0
            
            terminated_count = 0
            session_ids = self.user_sessions[user_id].copy()
            
            for session_id in session_ids:
                if except_session_id and session_id == except_session_id:
                    continue
                
                if await self._terminate_session(session_id, reason, terminated_by):
                    terminated_count += 1
            
            self.logger.info(f"Terminated {terminated_count} sessions for user {user_id}")
            return terminated_count
            
        except Exception as e:
            self.logger.error(f"Failed to terminate user sessions for {user_id}: {str(e)}")
            return 0
    
    async def verify_mfa(self, session_id: str, mfa_token: str) -> bool:
        """Verify MFA for session"""
        try:
            if session_id not in self.sessions:
                return False
            
            session = self.sessions[session_id]
            
            # Here you would integrate with your MFA service
            # For now, we'll simulate MFA verification
            mfa_verified = await self._verify_mfa_token(session.user_id, mfa_token)
            
            if mfa_verified:
                session.mfa_verified = True
                session.flags.discard('mfa_required')
                session.risk_score = max(0.0, session.risk_score - 0.3)  # Reduce risk
                
                await self._log_session_activity(
                    session_id, "mfa_verified", session.ip_address, session.user_agent
                )
                
                self.metrics['mfa_verifications'] += 1
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to verify MFA for session {session_id}: {str(e)}")
            return False
    
    async def get_user_sessions(
        self,
        user_id: str,
        active_only: bool = True,
        session_type: Optional[SessionType] = None
    ) -> List[Session]:
        """Get all sessions for a user"""
        try:
            if user_id not in self.user_sessions:
                return []
            
            user_session_list = []
            
            for session_id in self.user_sessions[user_id]:
                if session_id not in self.sessions:
                    continue
                
                session = self.sessions[session_id]
                
                # Filter by active status
                if active_only and session.status != SessionStatus.ACTIVE:
                    continue
                
                # Filter by session type
                if session_type and session.session_type != session_type:
                    continue
                
                # Check if session is still valid
                if active_only and not await self._is_session_valid(session):
                    continue
                
                user_session_list.append(session)
            
            return user_session_list
            
        except Exception as e:
            self.logger.error(f"Failed to get user sessions for {user_id}: {str(e)}")
            return []
    
    async def get_session_activities(
        self,
        session_id: str,
        limit: int = 100
    ) -> List[SessionActivity]:
        """Get session activities"""
        try:
            if session_id not in self.session_activities:
                return []
            
            activities = self.session_activities[session_id]
            return sorted(activities, key=lambda a: a.timestamp, reverse=True)[:limit]
            
        except Exception as e:
            self.logger.error(f"Failed to get session activities for {session_id}: {str(e)}")
            return []
    
    async def create_security_policy(
        self,
        policy_id: str,
        name: str,
        description: str,
        max_idle_time: Optional[timedelta] = None,
        max_session_time: Optional[timedelta] = None,
        max_concurrent_sessions: int = 5,
        require_mfa: bool = False,
        ip_whitelist: Optional[Set[str]] = None,
        risk_threshold: float = 0.7,
        device_trust_required: bool = False
    ) -> SessionSecurityPolicy:
        """Create session security policy"""
        try:
            policy = SessionSecurityPolicy(
                policy_id=policy_id,
                name=name,
                description=description,
                max_idle_time=max_idle_time or timedelta(minutes=30),
                max_session_time=max_session_time or timedelta(hours=8),
                max_concurrent_sessions=max_concurrent_sessions,
                require_mfa=require_mfa,
                ip_whitelist=ip_whitelist or set(),
                risk_threshold=risk_threshold,
                device_trust_required=device_trust_required
            )
            
            self.security_policies[policy_id] = policy
            
            # Set as default if none exists
            if not self.default_policy_id:
                self.default_policy_id = policy_id
            
            self.logger.info(f"Security policy created: {policy_id}")
            return policy
            
        except Exception as e:
            self.logger.error(f"Failed to create security policy {policy_id}: {str(e)}")
            raise ValidationError(f"Policy creation failed: {str(e)}")
    
    async def get_session_metrics(self) -> SessionMetrics:
        """Get session metrics"""
        try:
            now = datetime.utcnow()
            active_sessions = 0
            unique_users = set()
            total_duration = 0
            sessions_by_type = {}
            sessions_by_device = {}
            high_risk_sessions = 0
            mfa_verified_sessions = 0
            
            for session in self.sessions.values():
                if session.status == SessionStatus.ACTIVE and session.expires_at > now:
                    active_sessions += 1
                    unique_users.add(session.user_id)
                    
                    # Calculate duration
                    duration = (session.last_activity - session.created_at).total_seconds()
                    total_duration += duration
                    
                    # Count by type
                    sessions_by_type[session.session_type] = sessions_by_type.get(session.session_type, 0) + 1
                    
                    # Count by device
                    if session.device_info:
                        device_type = session.device_info.device_type
                        sessions_by_device[device_type] = sessions_by_device.get(device_type, 0) + 1
                    
                    # Count high risk
                    if session.risk_score > 0.7:
                        high_risk_sessions += 1
                    
                    # Count MFA verified
                    if session.mfa_verified:
                        mfa_verified_sessions += 1
            
            average_duration = total_duration / active_sessions if active_sessions > 0 else 0
            
            return SessionMetrics(
                total_sessions=len(self.sessions),
                active_sessions=active_sessions,
                unique_users=len(unique_users),
                average_session_duration=average_duration,
                sessions_by_type=sessions_by_type,
                sessions_by_device=sessions_by_device,
                high_risk_sessions=high_risk_sessions,
                mfa_verified_sessions=mfa_verified_sessions
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get session metrics: {str(e)}")
            return SessionMetrics()
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get session manager health status"""
        try:
            metrics = await self.get_session_metrics()
            
            return {
                'service': 'SessionManager',
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'metrics': self.metrics,
                'session_stats': {
                    'total_sessions': metrics.total_sessions,
                    'active_sessions': metrics.active_sessions,
                    'unique_users': metrics.unique_users,
                    'high_risk_sessions': metrics.high_risk_sessions,
                    'mfa_verified_sessions': metrics.mfa_verified_sessions,
                    'average_session_duration_minutes': metrics.average_session_duration / 60
                },
                'devices': {
                    'total_registered': len(self.devices),
                    'users_with_devices': len(self.user_devices)
                },
                'security': {
                    'policies_configured': len(self.security_policies),
                    'suspicious_ips': len(self.suspicious_ips),
                    'trusted_networks': len(self.trusted_networks)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get health status: {str(e)}")
            return {
                'service': 'SessionManager',
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _load_default_policies(self) -> None:
        """Load default security policies"""
        # Standard policy
        await self.create_security_policy(
            policy_id="standard",
            name="Standard Security Policy",
            description="Standard security policy for regular users",
            max_idle_time=timedelta(minutes=30),
            max_session_time=timedelta(hours=8),
            max_concurrent_sessions=5,
            require_mfa=False,
            risk_threshold=0.7
        )
        
        # High security policy
        await self.create_security_policy(
            policy_id="high_security",
            name="High Security Policy",
            description="High security policy for privileged users",
            max_idle_time=timedelta(minutes=15),
            max_session_time=timedelta(hours=4),
            max_concurrent_sessions=2,
            require_mfa=True,
            risk_threshold=0.5,
            device_trust_required=True
        )
    
    async def _load_trusted_networks(self) -> None:
        """Load trusted network ranges"""
        # Add common private network ranges
        private_networks = [
            "10.0.0.0/8",
            "172.16.0.0/12",
            "192.168.0.0/16",
            "127.0.0.0/8"
        ]
        
        self.trusted_networks.update(private_networks)
    
    async def _start_background_workers(self) -> None:
        """Start background worker tasks"""
        # Session cleanup worker
        async def session_cleanup_worker():
            while True:
                try:
                    await asyncio.sleep(300)  # Check every 5 minutes
                    await self._cleanup_expired_sessions()
                except Exception as e:
                    self.logger.error(f"Session cleanup worker error: {str(e)}")
                    await asyncio.sleep(60)
        
        # Security monitoring worker
        async def security_monitoring_worker():
            while True:
                try:
                    await asyncio.sleep(900)  # Check every 15 minutes
                    await self._monitor_security_threats()
                except Exception as e:
                    self.logger.error(f"Security monitoring worker error: {str(e)}")
                    await asyncio.sleep(300)
        
        # Activity cleanup worker
        async def activity_cleanup_worker():
            while True:
                try:
                    await asyncio.sleep(3600)  # Check every hour
                    await self._cleanup_old_activities()
                except Exception as e:
                    self.logger.error(f"Activity cleanup worker error: {str(e)}")
                    await asyncio.sleep(600)
        
        self.background_tasks['session_cleanup'] = asyncio.create_task(session_cleanup_worker())
        self.background_tasks['security_monitoring'] = asyncio.create_task(security_monitoring_worker())
        self.background_tasks['activity_cleanup'] = asyncio.create_task(activity_cleanup_worker())
    
    async def _check_concurrent_session_limits(self, user_id: str) -> None:
        """Check concurrent session limits"""
        if user_id not in self.user_sessions:
            return
        
        active_sessions = await self.get_user_sessions(user_id, active_only=True)
        
        # Get user's session limit (use default policy for now)
        policy = await self._get_security_policy(self.default_policy_id)
        max_sessions = policy.max_concurrent_sessions if policy else 5
        
        if len(active_sessions) >= max_sessions:
            # Terminate oldest session
            oldest_session = min(active_sessions, key=lambda s: s.created_at)
            await self._terminate_session(
                oldest_session.session_id, 
                "concurrent_session_limit",
                "system"
            )
            self.metrics['concurrent_session_limits_hit'] += 1
    
    async def _perform_security_checks(
        self,
        user_id: str,
        ip_address: Optional[str],
        user_agent: Optional[str],
        device_info: Optional[DeviceInfo]
    ) -> None:
        """Perform security checks before session creation"""
        # Check suspicious IP
        if ip_address and ip_address in self.suspicious_ips:
            self.metrics['security_violations'] += 1
            raise SecurityError(f"Access denied from suspicious IP: {ip_address}")
        
        # Check blocked user agents
        if user_agent:
            for blocked_agent in self.blocked_user_agents:
                if blocked_agent.lower() in user_agent.lower():
                    self.metrics['security_violations'] += 1
                    raise SecurityError("Access denied: blocked user agent")
    
    async def _calculate_risk_score(
        self,
        user_id: str,
        ip_address: Optional[str],
        user_agent: Optional[str],
        device_info: Optional[DeviceInfo]
    ) -> float:
        """Calculate session risk score"""
        risk_score = 0.0
        
        # IP-based risk
        if ip_address:
            if ip_address in self.suspicious_ips:
                risk_score += 0.5
            elif not await self._is_ip_in_trusted_networks(ip_address):
                risk_score += 0.2
        
        # Device-based risk
        if device_info:
            if not device_info.trusted:
                risk_score += 0.3
            if device_info.device_type == DeviceType.UNKNOWN:
                risk_score += 0.2
        
        # User agent risk
        if user_agent:
            # Check for automated/bot patterns
            bot_indicators = ['bot', 'crawler', 'spider', 'scraper']
            if any(indicator in user_agent.lower() for indicator in bot_indicators):
                risk_score += 0.4
        
        # Time-based risk (unusual hours)
        current_hour = datetime.utcnow().hour
        if current_hour < 6 or current_hour > 22:  # Outside business hours
            risk_score += 0.1
        
        return min(1.0, risk_score)
    
    async def _register_device(self, user_id: str, device_info: DeviceInfo) -> None:
        """Register device for user"""
        self.devices[device_info.device_id] = device_info
        
        if user_id not in self.user_devices:
            self.user_devices[user_id] = set()
        
        self.user_devices[user_id].add(device_info.device_id)
        self.metrics['device_registrations'] += 1
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return f"sess_{secrets.token_urlsafe(32)}"
    
    def _generate_session_token(self) -> str:
        """Generate session token"""
        return secrets.token_urlsafe(64)
    
    async def _get_security_policy(self, policy_id: Optional[str]) -> Optional[SessionSecurityPolicy]:
        """Get security policy"""
        if policy_id and policy_id in self.security_policies:
            return self.security_policies[policy_id]
        elif self.default_policy_id and self.default_policy_id in self.security_policies:
            return self.security_policies[self.default_policy_id]
        return None
    
    async def _is_session_valid(self, session: Session) -> bool:
        """Check if session is still valid"""
        now = datetime.utcnow()
        
        # Check status
        if session.status != SessionStatus.ACTIVE:
            return False
        
        # Check expiration
        if session.expires_at and session.expires_at <= now:
            return False
        
        # Check idle timeout
        if session.last_activity and (now - session.last_activity) > session.idle_timeout:
            return False
        
        # Check absolute timeout
        if (now - session.created_at) > session.absolute_timeout:
            return False
        
        return True
    
    async def _terminate_session(
        self,
        session_id: str,
        reason: str = "user_logout",
        terminated_by: str = "user"
    ) -> bool:
        """Internal method to terminate session"""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        session.status = SessionStatus.TERMINATED
        
        # Remove from user sessions
        if session.user_id in self.user_sessions:
            self.user_sessions[session.user_id] = [
                sid for sid in self.user_sessions[session.user_id] if sid != session_id
            ]
        
        # Remove session token
        if session_id in self.session_tokens:
            del self.session_tokens[session_id]
        
        # Log termination
        await self._log_session_activity(
            session_id, "session_terminated", session.ip_address, session.user_agent,
            {'reason': reason, 'terminated_by': terminated_by}
        )
        
        self.metrics['sessions_terminated'] += 1
        self.logger.info(f"Session terminated: {session_id} (reason: {reason})")
        
        return True
    
    async def _verify_mfa_token(self, user_id: str, mfa_token: str) -> bool:
        """Verify MFA token (placeholder implementation)"""
        # This would integrate with your actual MFA service
        # For demo purposes, we'll accept tokens that are 6 digits
        return mfa_token.isdigit() and len(mfa_token) == 6
    
    async def _assess_ip_change_risk(self, session: Session, new_ip: str) -> float:
        """Assess risk of IP address change"""
        risk = 0.0
        
        # Different IP addresses increase risk
        risk += 0.3
        
        # Check if new IP is suspicious
        if new_ip in self.suspicious_ips:
            risk += 0.5
        
        # Check geographic distance (simplified)
        # In a real implementation, you'd use IP geolocation services
        
        return risk
    
    async def _is_ip_in_trusted_networks(self, ip_addr: str) -> bool:
        """Check if IP is in trusted networks"""
        try:
            ip = ip_address(ip_addr)
            for network_str in self.trusted_networks:
                network = ip_network(network_str, strict=False)
                if ip in network:
                    return True
            return False
        except Exception:
            return False
    
    async def _log_session_activity(
        self,
        session_id: str,
        activity_type: str,
        ip_address: Optional[str],
        user_agent: Optional[str],
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log session activity"""
        activity = SessionActivity(
            activity_id=str(uuid.uuid4()),
            session_id=session_id,
            activity_type=activity_type,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {}
        )
        
        if session_id not in self.session_activities:
            self.session_activities[session_id] = []
        
        self.session_activities[session_id].append(activity)
        
        # Limit activity history per session
        if len(self.session_activities[session_id]) > 1000:
            self.session_activities[session_id] = self.session_activities[session_id][-500:]
    
    async def _cleanup_expired_sessions(self) -> None:
        """Clean up expired sessions"""
        now = datetime.utcnow()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if not await self._is_session_valid(session):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            await self._terminate_session(session_id, "expired", "system")
            # Remove from sessions dict
            if session_id in self.sessions:
                del self.sessions[session_id]
        
        if expired_sessions:
            self.metrics['sessions_expired'] += len(expired_sessions)
            self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    async def _monitor_security_threats(self) -> None:
        """Monitor for security threats"""
        # Analyze session patterns for anomalies
        now = datetime.utcnow()
        
        for session in self.sessions.values():
            if session.status == SessionStatus.ACTIVE:
                # Check for high-risk sessions
                if session.risk_score > 0.8 and 'high_risk' not in session.flags:
                    session.flags.add('high_risk')
                    self.metrics['high_risk_detections'] += 1
                    
                    await self._log_session_activity(
                        session.session_id, "high_risk_detected", 
                        session.ip_address, session.user_agent,
                        {'risk_score': session.risk_score}
                    )
    
    async def _cleanup_old_activities(self) -> None:
        """Clean up old session activities"""
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        for session_id in list(self.session_activities.keys()):
            activities = self.session_activities[session_id]
            
            # Keep only recent activities
            recent_activities = [
                activity for activity in activities
                if activity.timestamp > cutoff_date
            ]
            
            if recent_activities:
                self.session_activities[session_id] = recent_activities
            else:
                del self.session_activities[session_id]
    
    async def cleanup(self) -> None:
        """Cleanup session manager resources"""
        try:
            # Cancel background tasks
            for task in self.background_tasks.values():
                if not task.done():
                    task.cancel()
            
            # Clear session data
            self.sessions.clear()
            self.user_sessions.clear()
            self.session_activities.clear()
            self.session_tokens.clear()
            
            self.logger.info("SessionManager cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during SessionManager cleanup: {str(e)}")