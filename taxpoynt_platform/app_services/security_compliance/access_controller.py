"""
Access Controller Service for APP Role

This service controls and monitors access to FIRS including:
- Role-based access control (RBAC)
- API rate limiting and throttling
- Permission validation and enforcement
- Session management and tracking
- Access pattern monitoring and anomaly detection
"""

import time
import asyncio
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict, deque
import jwt
import bcrypt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AccessLevel(Enum):
    """Access levels for FIRS operations"""
    READ_ONLY = "read_only"
    STANDARD = "standard"
    ELEVATED = "elevated"
    ADMIN = "admin"
    SYSTEM = "system"


class PermissionType(Enum):
    """Types of permissions"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    APPROVE = "approve"
    ADMIN = "admin"


class ResourceType(Enum):
    """Types of resources that can be accessed"""
    INVOICE = "invoice"
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    CERTIFICATE = "certificate"
    AUDIT_LOG = "audit_log"
    SYSTEM_CONFIG = "system_config"
    USER_MANAGEMENT = "user_management"
    FIRS_API = "firs_api"


class SessionStatus(Enum):
    """Session status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    SUSPENDED = "suspended"


class AccessDecision(Enum):
    """Access control decisions"""
    ALLOW = "allow"
    DENY = "deny"
    CHALLENGE = "challenge"
    THROTTLE = "throttle"


@dataclass
class Permission:
    """Permission definition"""
    resource_type: ResourceType
    permission_type: PermissionType
    resource_id: Optional[str] = None
    conditions: Dict[str, Any] = field(default_factory=dict)
    granted_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


@dataclass
class Role:
    """Role definition with permissions"""
    role_id: str
    role_name: str
    description: str
    access_level: AccessLevel
    permissions: List[Permission] = field(default_factory=list)
    inherit_from: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True


@dataclass
class User:
    """User definition"""
    user_id: str
    username: str
    email: str
    password_hash: str
    roles: List[str] = field(default_factory=list)
    access_level: AccessLevel = AccessLevel.READ_ONLY
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Session:
    """User session"""
    session_id: str
    user_id: str
    ip_address: str
    user_agent: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    status: SessionStatus = SessionStatus.ACTIVE
    permissions_cache: Dict[str, bool] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccessRequest:
    """Access request structure"""
    request_id: str
    user_id: str
    session_id: Optional[str]
    resource_type: ResourceType
    permission_type: PermissionType
    resource_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class AccessResult:
    """Access control result"""
    decision: AccessDecision
    request_id: str
    user_id: str
    allowed: bool
    reason: str
    additional_data: Dict[str, Any] = field(default_factory=dict)
    expires_at: Optional[datetime] = None
    retry_after: Optional[int] = None


@dataclass
class RateLimitRule:
    """Rate limiting rule"""
    rule_id: str
    resource_pattern: str
    max_requests: int
    time_window: int  # seconds
    per_user: bool = True
    per_ip: bool = False
    burst_allowance: int = 0
    is_active: bool = True


@dataclass
class AccessPattern:
    """Access pattern for anomaly detection"""
    user_id: str
    resource_type: ResourceType
    permission_type: PermissionType
    request_count: int
    time_period: timedelta
    locations: Set[str] = field(default_factory=set)
    user_agents: Set[str] = field(default_factory=set)
    last_seen: datetime = field(default_factory=datetime.utcnow)


class AccessController:
    """
    Access controller service for APP role
    
    Handles:
    - Role-based access control (RBAC)
    - API rate limiting and throttling
    - Permission validation and enforcement
    - Session management and tracking
    - Access pattern monitoring and anomaly detection
    """
    
    def __init__(self,
                 jwt_secret: str = None,
                 session_timeout: int = 3600,  # 1 hour
                 max_failed_attempts: int = 5,
                 lockout_duration: int = 1800):  # 30 minutes
        
        self.jwt_secret = jwt_secret or secrets.token_urlsafe(32)
        self.session_timeout = session_timeout
        self.max_failed_attempts = max_failed_attempts
        self.lockout_duration = lockout_duration
        
        # Storage
        self.users: Dict[str, User] = {}
        self.roles: Dict[str, Role] = {}
        self.sessions: Dict[str, Session] = {}
        self.rate_limit_rules: Dict[str, RateLimitRule] = {}
        
        # Rate limiting tracking
        self.request_counts: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(deque))
        
        # Access patterns for anomaly detection
        self.access_patterns: Dict[str, AccessPattern] = {}
        
        # Access history
        self.access_history: List[AccessResult] = []
        
        # Setup default roles and rules
        self._setup_default_roles()
        self._setup_default_rate_limits()
        
        # Policy functions
        self.custom_policies: List[Callable] = []
        
        # Metrics
        self.metrics = {
            'total_requests': 0,
            'allowed_requests': 0,
            'denied_requests': 0,
            'throttled_requests': 0,
            'challenged_requests': 0,
            'active_sessions': 0,
            'failed_logins': 0,
            'successful_logins': 0,
            'lockouts': 0,
            'anomalies_detected': 0,
            'requests_by_resource': defaultdict(int),
            'requests_by_permission': defaultdict(int),
            'requests_by_user': defaultdict(int)
        }
    
    def _setup_default_roles(self):
        """Setup default roles"""
        # Read-only role
        read_only_permissions = []
        for resource_type in ResourceType:
            if resource_type not in [ResourceType.SYSTEM_CONFIG, ResourceType.USER_MANAGEMENT]:
                read_only_permissions.append(
                    Permission(resource_type, PermissionType.READ)
                )
        
        self.roles['read_only'] = Role(
            role_id='read_only',
            role_name='Read Only',
            description='Read-only access to most resources',
            access_level=AccessLevel.READ_ONLY,
            permissions=read_only_permissions
        )
        
        # Standard user role
        standard_permissions = read_only_permissions + [
            Permission(ResourceType.INVOICE, PermissionType.CREATE),
            Permission(ResourceType.INVOICE, PermissionType.UPDATE),
            Permission(ResourceType.CUSTOMER, PermissionType.CREATE),
            Permission(ResourceType.CUSTOMER, PermissionType.UPDATE),
            Permission(ResourceType.SUPPLIER, PermissionType.CREATE),
            Permission(ResourceType.SUPPLIER, PermissionType.UPDATE)
        ]
        
        self.roles['standard_user'] = Role(
            role_id='standard_user',
            role_name='Standard User',
            description='Standard user with create/update permissions',
            access_level=AccessLevel.STANDARD,
            permissions=standard_permissions
        )
        
        # Administrator role
        admin_permissions = []
        for resource_type in ResourceType:
            for permission_type in PermissionType:
                admin_permissions.append(
                    Permission(resource_type, permission_type)
                )
        
        self.roles['administrator'] = Role(
            role_id='administrator',
            role_name='Administrator',
            description='Full administrative access',
            access_level=AccessLevel.ADMIN,
            permissions=admin_permissions
        )
    
    def _setup_default_rate_limits(self):
        """Setup default rate limiting rules"""
        # General API rate limit
        self.rate_limit_rules['general_api'] = RateLimitRule(
            rule_id='general_api',
            resource_pattern='*',
            max_requests=1000,
            time_window=3600,  # 1 hour
            per_user=True,
            burst_allowance=50
        )
        
        # FIRS API specific limits
        self.rate_limit_rules['firs_api'] = RateLimitRule(
            rule_id='firs_api',
            resource_pattern='firs_api',
            max_requests=100,
            time_window=3600,  # 1 hour
            per_user=True,
            burst_allowance=10
        )
        
        # Authentication attempts
        self.rate_limit_rules['auth'] = RateLimitRule(
            rule_id='auth',
            resource_pattern='auth',
            max_requests=10,
            time_window=900,  # 15 minutes
            per_ip=True,
            burst_allowance=3
        )
    
    async def create_user(self,
                        username: str,
                        email: str,
                        password: str,
                        roles: List[str] = None,
                        access_level: AccessLevel = AccessLevel.READ_ONLY) -> User:
        """Create new user"""
        user_id = f"user_{int(time.time())}_{secrets.token_hex(8)}"
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Validate roles
        valid_roles = []
        for role_id in roles or ['read_only']:
            if role_id in self.roles:
                valid_roles.append(role_id)
        
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
            roles=valid_roles,
            access_level=access_level
        )
        
        self.users[user_id] = user
        
        logger.info(f"User created: {username} ({user_id})")
        return user
    
    async def authenticate_user(self,
                              username: str,
                              password: str,
                              ip_address: str,
                              user_agent: str) -> Optional[Session]:
        """Authenticate user and create session"""
        # Check rate limiting for authentication
        rate_limit_key = f"auth:{ip_address}"
        if not await self._check_rate_limit(rate_limit_key, 'auth'):
            logger.warning(f"Authentication rate limit exceeded for IP: {ip_address}")
            return None
        
        # Find user by username
        user = None
        for u in self.users.values():
            if u.username == username:
                user = u
                break
        
        if not user:
            self.metrics['failed_logins'] += 1
            return None
        
        # Check if user is locked
        if user.locked_until and datetime.utcnow() < user.locked_until:
            logger.warning(f"User {username} is locked until {user.locked_until}")
            return None
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"User {username} is inactive")
            return None
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            user.failed_login_attempts += 1
            
            # Lock user if too many failed attempts
            if user.failed_login_attempts >= self.max_failed_attempts:
                user.locked_until = datetime.utcnow() + timedelta(seconds=self.lockout_duration)
                self.metrics['lockouts'] += 1
                logger.warning(f"User {username} locked due to failed login attempts")
            
            self.metrics['failed_logins'] += 1
            return None
        
        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        
        # Create session
        session = await self._create_session(user, ip_address, user_agent)
        
        self.metrics['successful_logins'] += 1
        self.metrics['active_sessions'] += 1
        
        logger.info(f"User authenticated: {username} ({user.user_id})")
        return session
    
    async def _create_session(self, user: User, ip_address: str, user_agent: str) -> Session:
        """Create user session"""
        session_id = secrets.token_urlsafe(32)
        
        session = Session(
            session_id=session_id,
            user_id=user.user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(seconds=self.session_timeout)
        )
        
        self.sessions[session_id] = session
        return session
    
    async def validate_session(self, session_id: str) -> Optional[Session]:
        """Validate and refresh session"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # Check if session is expired
        if datetime.utcnow() > session.expires_at:
            session.status = SessionStatus.EXPIRED
            self.metrics['active_sessions'] -= 1
            return None
        
        # Check if session is active
        if session.status != SessionStatus.ACTIVE:
            return None
        
        # Update last activity and extend expiration
        session.last_activity = datetime.utcnow()
        session.expires_at = datetime.utcnow() + timedelta(seconds=self.session_timeout)
        
        return session
    
    async def check_permission(self, request: AccessRequest) -> AccessResult:
        """Check if access request should be allowed"""
        request_id = request.request_id
        user_id = request.user_id
        
        self.metrics['total_requests'] += 1
        self.metrics['requests_by_resource'][request.resource_type.value] += 1
        self.metrics['requests_by_permission'][request.permission_type.value] += 1
        self.metrics['requests_by_user'][user_id] += 1
        
        try:
            # Validate session if provided
            if request.session_id:
                session = await self.validate_session(request.session_id)
                if not session:
                    result = AccessResult(
                        decision=AccessDecision.DENY,
                        request_id=request_id,
                        user_id=user_id,
                        allowed=False,
                        reason="Invalid or expired session"
                    )
                    self.metrics['denied_requests'] += 1
                    self._record_access_result(result)
                    return result
            
            # Get user
            if user_id not in self.users:
                result = AccessResult(
                    decision=AccessDecision.DENY,
                    request_id=request_id,
                    user_id=user_id,
                    allowed=False,
                    reason="User not found"
                )
                self.metrics['denied_requests'] += 1
                self._record_access_result(result)
                return result
            
            user = self.users[user_id]
            
            # Check if user is active
            if not user.is_active:
                result = AccessResult(
                    decision=AccessDecision.DENY,
                    request_id=request_id,
                    user_id=user_id,
                    allowed=False,
                    reason="User is inactive"
                )
                self.metrics['denied_requests'] += 1
                self._record_access_result(result)
                return result
            
            # Check rate limiting
            rate_limit_key = f"{user_id}:{request.resource_type.value}"
            if not await self._check_rate_limit(rate_limit_key, request.resource_type.value):
                result = AccessResult(
                    decision=AccessDecision.THROTTLE,
                    request_id=request_id,
                    user_id=user_id,
                    allowed=False,
                    reason="Rate limit exceeded",
                    retry_after=300  # 5 minutes
                )
                self.metrics['throttled_requests'] += 1
                self._record_access_result(result)
                return result
            
            # Check permissions
            permission_granted = await self._check_user_permissions(
                user, request.resource_type, request.permission_type, request.resource_id
            )
            
            if not permission_granted:
                result = AccessResult(
                    decision=AccessDecision.DENY,
                    request_id=request_id,
                    user_id=user_id,
                    allowed=False,
                    reason="Insufficient permissions"
                )
                self.metrics['denied_requests'] += 1
                self._record_access_result(result)
                return result
            
            # Check custom policies
            for policy in self.custom_policies:
                policy_result = await policy(request, user)
                if not policy_result.get('allowed', True):
                    result = AccessResult(
                        decision=AccessDecision.DENY,
                        request_id=request_id,
                        user_id=user_id,
                        allowed=False,
                        reason=f"Policy violation: {policy_result.get('reason', 'Custom policy denied access')}"
                    )
                    self.metrics['denied_requests'] += 1
                    self._record_access_result(result)
                    return result
            
            # Check for anomalies
            anomaly_detected = await self._detect_access_anomaly(request, user)
            if anomaly_detected:
                result = AccessResult(
                    decision=AccessDecision.CHALLENGE,
                    request_id=request_id,
                    user_id=user_id,
                    allowed=False,
                    reason="Anomalous access pattern detected - additional verification required"
                )
                self.metrics['challenged_requests'] += 1
                self.metrics['anomalies_detected'] += 1
                self._record_access_result(result)
                return result
            
            # Access granted
            result = AccessResult(
                decision=AccessDecision.ALLOW,
                request_id=request_id,
                user_id=user_id,
                allowed=True,
                reason="Access granted"
            )
            
            self.metrics['allowed_requests'] += 1
            self._record_access_result(result)
            
            # Update access patterns
            await self._update_access_pattern(request, user)
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking permission for request {request_id}: {e}")
            result = AccessResult(
                decision=AccessDecision.DENY,
                request_id=request_id,
                user_id=user_id,
                allowed=False,
                reason=f"Internal error: {str(e)}"
            )
            self.metrics['denied_requests'] += 1
            self._record_access_result(result)
            return result
    
    async def _check_user_permissions(self,
                                    user: User,
                                    resource_type: ResourceType,
                                    permission_type: PermissionType,
                                    resource_id: Optional[str] = None) -> bool:
        """Check if user has required permission"""
        # Check cache first
        cache_key = f"{resource_type.value}:{permission_type.value}:{resource_id or 'any'}"
        
        # Get user permissions from roles
        user_permissions = []
        for role_id in user.roles:
            if role_id in self.roles:
                role = self.roles[role_id]
                if role.is_active:
                    user_permissions.extend(role.permissions)
        
        # Check permissions
        for permission in user_permissions:
            # Check if permission matches
            if (permission.resource_type == resource_type and
                permission.permission_type == permission_type):
                
                # Check resource-specific permission
                if permission.resource_id is None or permission.resource_id == resource_id:
                    # Check if permission is expired
                    if permission.expires_at is None or datetime.utcnow() < permission.expires_at:
                        # Check conditions if any
                        if self._check_permission_conditions(permission, user):
                            return True
        
        return False
    
    def _check_permission_conditions(self, permission: Permission, user: User) -> bool:
        """Check permission conditions"""
        # Example conditions that could be implemented:
        # - Time-based restrictions
        # - IP-based restrictions
        # - Resource-specific conditions
        
        conditions = permission.conditions
        
        # Time-based restrictions
        if 'allowed_hours' in conditions:
            current_hour = datetime.utcnow().hour
            allowed_hours = conditions['allowed_hours']
            if current_hour not in allowed_hours:
                return False
        
        # User-specific conditions
        if 'required_access_level' in conditions:
            required_level = AccessLevel(conditions['required_access_level'])
            if user.access_level.value < required_level.value:
                return False
        
        return True
    
    async def _check_rate_limit(self, key: str, resource_pattern: str) -> bool:
        """Check rate limiting"""
        # Find applicable rate limit rule
        rule = None
        for rule_id, r in self.rate_limit_rules.items():
            if r.resource_pattern == '*' or r.resource_pattern == resource_pattern:
                if r.is_active:
                    rule = r
                    break
        
        if not rule:
            return True  # No rate limit applies
        
        current_time = time.time()
        window_start = current_time - rule.time_window
        
        # Clean old requests
        if key in self.request_counts:
            while (self.request_counts[key] and 
                   self.request_counts[key][0] < window_start):
                self.request_counts[key].popleft()
        
        # Check current count
        current_count = len(self.request_counts.get(key, []))
        
        # Check if within limits
        if current_count < rule.max_requests:
            # Add current request
            if key not in self.request_counts:
                self.request_counts[key] = deque()
            self.request_counts[key].append(current_time)
            return True
        
        # Check burst allowance
        if rule.burst_allowance > 0:
            recent_requests = sum(1 for req_time in self.request_counts.get(key, [])
                                if req_time > current_time - 60)  # Last minute
            if recent_requests < rule.burst_allowance:
                self.request_counts[key].append(current_time)
                return True
        
        return False
    
    async def _detect_access_anomaly(self, request: AccessRequest, user: User) -> bool:
        """Detect anomalous access patterns"""
        pattern_key = f"{user.user_id}:{request.resource_type.value}:{request.permission_type.value}"
        
        if pattern_key not in self.access_patterns:
            # Create new pattern
            self.access_patterns[pattern_key] = AccessPattern(
                user_id=user.user_id,
                resource_type=request.resource_type,
                permission_type=request.permission_type,
                request_count=0,
                time_period=timedelta(hours=1)
            )
        
        pattern = self.access_patterns[pattern_key]
        
        # Check for anomalies
        current_time = datetime.utcnow()
        
        # Unusual frequency
        time_since_last = current_time - pattern.last_seen
        if time_since_last < timedelta(seconds=1) and pattern.request_count > 10:
            return True  # Too many requests too quickly
        
        # New location (IP address)
        if request.ip_address and request.ip_address not in pattern.locations:
            if len(pattern.locations) > 0:  # Not first access
                return True  # Access from new location
        
        # New user agent
        if request.user_agent and request.user_agent not in pattern.user_agents:
            if len(pattern.user_agents) > 0:  # Not first access
                return True  # Access from new user agent
        
        # Unusual time
        if current_time.hour < 6 or current_time.hour > 22:  # Outside business hours
            if pattern.request_count < 5:  # Infrequent user
                return True  # Unusual time access
        
        return False
    
    async def _update_access_pattern(self, request: AccessRequest, user: User):
        """Update access patterns for learning"""
        pattern_key = f"{user.user_id}:{request.resource_type.value}:{request.permission_type.value}"
        
        if pattern_key in self.access_patterns:
            pattern = self.access_patterns[pattern_key]
            pattern.request_count += 1
            pattern.last_seen = datetime.utcnow()
            
            if request.ip_address:
                pattern.locations.add(request.ip_address)
            
            if request.user_agent:
                pattern.user_agents.add(request.user_agent)
    
    def _record_access_result(self, result: AccessResult):
        """Record access result for audit"""
        self.access_history.append(result)
        
        # Keep only recent history
        if len(self.access_history) > 10000:
            self.access_history = self.access_history[-5000:]
    
    async def logout_user(self, session_id: str):
        """Logout user and terminate session"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.status = SessionStatus.TERMINATED
            self.metrics['active_sessions'] -= 1
            
            logger.info(f"User logged out: {session.user_id}")
    
    async def add_custom_policy(self, policy_function: Callable):
        """Add custom access policy"""
        self.custom_policies.append(policy_function)
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        current_time = datetime.utcnow()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if (session.status == SessionStatus.ACTIVE and 
                current_time > session.expires_at):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.sessions[session_id].status = SessionStatus.EXPIRED
            self.metrics['active_sessions'] -= 1
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    def get_user_permissions(self, user_id: str) -> List[Permission]:
        """Get all permissions for user"""
        if user_id not in self.users:
            return []
        
        user = self.users[user_id]
        permissions = []
        
        for role_id in user.roles:
            if role_id in self.roles:
                role = self.roles[role_id]
                if role.is_active:
                    permissions.extend(role.permissions)
        
        return permissions
    
    def get_access_history(self, 
                         user_id: Optional[str] = None,
                         limit: int = 100) -> List[AccessResult]:
        """Get access history"""
        history = self.access_history
        
        if user_id:
            history = [r for r in history if r.user_id == user_id]
        
        return history[-limit:]
    
    def get_active_sessions(self) -> List[Session]:
        """Get all active sessions"""
        return [s for s in self.sessions.values() if s.status == SessionStatus.ACTIVE]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get access controller metrics"""
        success_rate = 0
        if self.metrics['total_requests'] > 0:
            success_rate = (self.metrics['allowed_requests'] / self.metrics['total_requests']) * 100
        
        return {
            **self.metrics,
            'total_users': len(self.users),
            'total_roles': len(self.roles),
            'total_sessions': len(self.sessions),
            'success_rate': success_rate,
            'current_access_patterns': len(self.access_patterns),
            'rate_limit_rules': len(self.rate_limit_rules),
            'custom_policies': len(self.custom_policies)
        }


# Factory functions for easy setup
def create_access_controller(jwt_secret: Optional[str] = None,
                           session_timeout: int = 3600) -> AccessController:
    """Create access controller instance"""
    return AccessController(jwt_secret=jwt_secret, session_timeout=session_timeout)


def create_access_request(user_id: str,
                        resource_type: ResourceType,
                        permission_type: PermissionType,
                        session_id: Optional[str] = None,
                        **kwargs) -> AccessRequest:
    """Create access request"""
    request_id = f"req_{int(time.time())}_{secrets.token_hex(8)}"
    
    return AccessRequest(
        request_id=request_id,
        user_id=user_id,
        session_id=session_id,
        resource_type=resource_type,
        permission_type=permission_type,
        **kwargs
    )


async def check_user_access(user_id: str,
                          resource_type: ResourceType,
                          permission_type: PermissionType,
                          controller: Optional[AccessController] = None) -> bool:
    """Check if user has access to resource"""
    if not controller:
        controller = create_access_controller()
    
    request = create_access_request(user_id, resource_type, permission_type)
    result = await controller.check_permission(request)
    
    return result.allowed


def get_access_summary(controller: AccessController) -> Dict[str, Any]:
    """Get access controller summary"""
    metrics = controller.get_metrics()
    
    return {
        'total_requests': metrics['total_requests'],
        'success_rate': metrics['success_rate'],
        'active_sessions': metrics['active_sessions'],
        'total_users': metrics['total_users'],
        'denied_requests': metrics['denied_requests'],
        'throttled_requests': metrics['throttled_requests'],
        'anomalies_detected': metrics['anomalies_detected'],
        'lockouts': metrics['lockouts']
    }