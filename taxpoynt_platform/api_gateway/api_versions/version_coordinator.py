"""
API Version Coordinator
======================
Manages API version compatibility, routing, and lifecycle for TaxPoynt platform.
Coordinates between multiple API versions and handles deprecation, migration, and compatibility.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Set, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

from ...core_platform.authentication.role_manager import PlatformRole, RoleScope
from ...core_platform.messaging.message_router import ServiceRole, MessageRouter

logger = logging.getLogger(__name__)


class APIVersionStatus(Enum):
    """API Version lifecycle status"""
    DEVELOPMENT = "development"      # In development, not released
    STABLE = "stable"               # Current stable version
    DEPRECATED = "deprecated"       # Deprecated but still supported
    SUNSET = "sunset"              # Will be removed soon
    ARCHIVED = "archived"          # No longer supported


class VersionCompatibilityLevel(Enum):
    """Compatibility level between API versions"""
    FULL = "full"                  # Fully compatible
    BACKWARD = "backward"          # Backward compatible only
    BREAKING = "breaking"          # Breaking changes present
    MIGRATION_REQUIRED = "migration_required"  # Requires explicit migration


@dataclass
class APIVersionInfo:
    """Information about a specific API version"""
    version: str                                   # e.g., "v1", "v2"
    major: int                                     # Major version number
    minor: int                                     # Minor version number
    patch: int                                     # Patch version number
    status: APIVersionStatus                       # Current status
    release_date: datetime                         # When this version was released
    deprecation_date: Optional[datetime] = None   # When deprecation starts
    sunset_date: Optional[datetime] = None         # When version will be removed
    description: str = ""                          # Version description
    breaking_changes: List[str] = field(default_factory=list)  # List of breaking changes
    compatibility_matrix: Dict[str, VersionCompatibilityLevel] = field(default_factory=dict)
    supported_roles: Set[PlatformRole] = field(default_factory=set)  # Roles supported in this version
    
    def __post_init__(self):
        """Initialize default supported roles if not provided"""
        if not self.supported_roles:
            self.supported_roles = {
                PlatformRole.SYSTEM_INTEGRATOR,
                PlatformRole.ACCESS_POINT_PROVIDER,
                PlatformRole.ADMINISTRATOR
            }
    
    @property
    def full_version(self) -> str:
        """Get full semantic version string"""
        return f"{self.major}.{self.minor}.{self.patch}"
    
    @property
    def is_deprecated(self) -> bool:
        """Check if version is deprecated"""
        return self.status in [APIVersionStatus.DEPRECATED, APIVersionStatus.SUNSET, APIVersionStatus.ARCHIVED]
    
    @property
    def is_active(self) -> bool:
        """Check if version is actively supported"""
        return self.status in [APIVersionStatus.STABLE, APIVersionStatus.DEPRECATED]
    
    @property
    def days_until_sunset(self) -> Optional[int]:
        """Get days until sunset (if applicable)"""
        if self.sunset_date:
            return (self.sunset_date - datetime.now(timezone.utc)).days
        return None


@dataclass
class VersionRoutingConfig:
    """Configuration for version-specific routing"""
    version: str
    prefix: str                    # URL prefix for this version
    router_modules: Dict[str, str] # Role -> module path mapping
    middleware: List[str] = field(default_factory=list)  # Version-specific middleware
    rate_limits: Dict[str, int] = field(default_factory=dict)  # Role-based rate limits
    deprecation_warnings: bool = False  # Whether to include deprecation warnings
    migration_hints: Dict[str, str] = field(default_factory=dict)  # Migration guidance


class APIVersionCoordinator:
    """
    API Version Coordinator
    ======================
    Central coordinator for managing multiple API versions, handling compatibility,
    deprecation, and migration between versions.
    
    Features:
    - Version lifecycle management
    - Compatibility checking between versions
    - Automatic deprecation warning injection
    - Migration path guidance
    - Role-based version access control
    """
    
    def __init__(self, message_router: MessageRouter):
        self.message_router = message_router
        self.versions: Dict[str, APIVersionInfo] = {}
        self.routing_configs: Dict[str, VersionRoutingConfig] = {}
        self.default_version = "v1"
        self.latest_stable = "v1"
        
        # Initialize with default version information
        self._initialize_default_versions()
        
        logger.info("API Version Coordinator initialized")
    
    def _initialize_default_versions(self):
        """Initialize default version configurations"""
        
        # Version 1 (Current Stable)
        v1_info = APIVersionInfo(
            version="v1",
            major=1,
            minor=0,
            patch=0,
            status=APIVersionStatus.STABLE,
            release_date=datetime(2024, 12, 31, tzinfo=timezone.utc),
            description="Initial stable release of TaxPoynt E-Invoice Platform API",
            supported_roles={
                PlatformRole.SYSTEM_INTEGRATOR,
                PlatformRole.ACCESS_POINT_PROVIDER,
                PlatformRole.ADMINISTRATOR
            }
        )
        
        v1_routing = VersionRoutingConfig(
            version="v1",
            prefix="/api/v1",
            router_modules={
                "si": "taxpoynt_platform.api_gateway.api_versions.v1.si_endpoints",
                "app": "taxpoynt_platform.api_gateway.api_versions.v1.app_endpoints",
                "hybrid": "taxpoynt_platform.api_gateway.api_versions.v1.hybrid_endpoints"
            },
            rate_limits={
                "system_integrator": 1000,  # requests per hour
                "access_point_provider": 2000,
                "administrator": 5000
            }
        )
        
        # Version 2 (Future Development)
        v2_info = APIVersionInfo(
            version="v2",
            major=2,
            minor=0,
            patch=0,
            status=APIVersionStatus.DEVELOPMENT,
            release_date=datetime(2025, 6, 30, tzinfo=timezone.utc),
            description="Enhanced API with improved performance and new features",
            breaking_changes=[
                "Updated authentication flow",
                "Modified response format for transaction endpoints",
                "New required fields for organization creation"
            ],
            compatibility_matrix={
                "v1": VersionCompatibilityLevel.BREAKING
            },
            supported_roles={
                PlatformRole.SYSTEM_INTEGRATOR,
                PlatformRole.ACCESS_POINT_PROVIDER,
                PlatformRole.ADMINISTRATOR
            }
        )
        
        v2_routing = VersionRoutingConfig(
            version="v2",
            prefix="/api/v2",
            router_modules={
                "si": "taxpoynt_platform.api_gateway.api_versions.v2.si_endpoints",
                "app": "taxpoynt_platform.api_gateway.api_versions.v2.app_endpoints",
                "hybrid": "taxpoynt_platform.api_gateway.api_versions.v2.hybrid_endpoints"
            },
            rate_limits={
                "system_integrator": 2000,  # Increased limits for v2
                "access_point_provider": 4000,
                "administrator": 10000
            },
            migration_hints={
                "authentication": "Use new JWT format with role claims",
                "transactions": "Response now includes detailed compliance metadata",
                "organizations": "Additional validation required for new fields"
            }
        )
        
        # Register versions
        self.register_version(v1_info, v1_routing)
        self.register_version(v2_info, v2_routing)
        
        # Set compatibility relationships
        v1_info.compatibility_matrix["v2"] = VersionCompatibilityLevel.MIGRATION_REQUIRED
    
    def register_version(self, version_info: APIVersionInfo, routing_config: VersionRoutingConfig):
        """Register a new API version"""
        self.versions[version_info.version] = version_info
        self.routing_configs[version_info.version] = routing_config
        
        # Update latest stable if this is a stable version
        if (version_info.status == APIVersionStatus.STABLE and 
            version_info.major >= self.get_version_info(self.latest_stable).major):
            self.latest_stable = version_info.version
        
        logger.info(f"Registered API version {version_info.version} ({version_info.status.value})")
    
    def get_version_info(self, version: str) -> APIVersionInfo:
        """Get version information"""
        if version not in self.versions:
            raise ValueError(f"Unknown API version: {version}")
        return self.versions[version]
    
    def get_routing_config(self, version: str) -> VersionRoutingConfig:
        """Get routing configuration for version"""
        if version not in self.routing_configs:
            raise ValueError(f"No routing config for version: {version}")
        return self.routing_configs[version]
    
    def detect_version_from_request(self, request: Request) -> str:
        """Detect API version from request"""
        # Check URL path first
        path = str(request.url.path)
        version_match = re.match(r'^/api/(v\d+)', path)
        if version_match:
            version = version_match.group(1)
            if version in self.versions:
                return version
        
        # Check Accept header
        accept_header = request.headers.get("Accept", "")
        version_match = re.search(r'application/vnd\.taxpoynt\.(v\d+)\+json', accept_header)
        if version_match:
            version = version_match.group(1)
            if version in self.versions:
                return version
        
        # Check API-Version header
        api_version_header = request.headers.get("API-Version", "")
        if api_version_header in self.versions:
            return api_version_header
        
        # Default to latest stable
        return self.latest_stable
    
    def validate_version_access(self, version: str, user_role: PlatformRole) -> bool:
        """Validate if user role can access specific version"""
        version_info = self.get_version_info(version)
        
        # Check if version is accessible
        if not version_info.is_active:
            return False
        
        # Check role support
        return user_role in version_info.supported_roles
    
    def check_compatibility(self, from_version: str, to_version: str) -> VersionCompatibilityLevel:
        """Check compatibility between two versions"""
        from_info = self.get_version_info(from_version)
        
        if to_version in from_info.compatibility_matrix:
            return from_info.compatibility_matrix[to_version]
        
        # Default logic based on major/minor versions
        to_info = self.get_version_info(to_version)
        
        if from_info.major == to_info.major:
            if from_info.minor == to_info.minor:
                return VersionCompatibilityLevel.FULL
            else:
                return VersionCompatibilityLevel.BACKWARD
        else:
            return VersionCompatibilityLevel.BREAKING
    
    def get_migration_guidance(self, from_version: str, to_version: str) -> Dict[str, Any]:
        """Get migration guidance between versions"""
        from_info = self.get_version_info(from_version)
        to_info = self.get_version_info(to_version)
        to_config = self.get_routing_config(to_version)
        
        compatibility = self.check_compatibility(from_version, to_version)
        
        guidance = {
            "from_version": from_version,
            "to_version": to_version,
            "compatibility_level": compatibility.value,
            "breaking_changes": to_info.breaking_changes,
            "migration_hints": to_config.migration_hints,
            "estimated_effort": self._estimate_migration_effort(compatibility),
            "recommended_timeline": self._get_migration_timeline(from_info, to_info)
        }
        
        return guidance
    
    def _estimate_migration_effort(self, compatibility: VersionCompatibilityLevel) -> str:
        """Estimate migration effort based on compatibility"""
        effort_map = {
            VersionCompatibilityLevel.FULL: "minimal",
            VersionCompatibilityLevel.BACKWARD: "low",
            VersionCompatibilityLevel.BREAKING: "medium",
            VersionCompatibilityLevel.MIGRATION_REQUIRED: "high"
        }
        return effort_map.get(compatibility, "unknown")
    
    def _get_migration_timeline(self, from_info: APIVersionInfo, to_info: APIVersionInfo) -> Dict[str, Any]:
        """Get recommended migration timeline"""
        timeline = {
            "immediate_action_required": False,
            "recommended_start": None,
            "deadline": None,
            "phases": []
        }
        
        if from_info.is_deprecated and from_info.sunset_date:
            timeline["immediate_action_required"] = True
            timeline["deadline"] = from_info.sunset_date.isoformat()
            timeline["recommended_start"] = "immediately"
        elif from_info.deprecation_date:
            timeline["recommended_start"] = from_info.deprecation_date.isoformat()
        
        return timeline
    
    def add_version_headers(self, response: JSONResponse, version: str, request: Request) -> JSONResponse:
        """Add version-related headers to response"""
        version_info = self.get_version_info(version)
        
        # Standard version headers
        response.headers["API-Version"] = version
        response.headers["API-Version-Full"] = version_info.full_version
        response.headers["API-Version-Status"] = version_info.status.value
        
        # Deprecation warning
        if version_info.is_deprecated:
            response.headers["Deprecation"] = "true"
            if version_info.sunset_date:
                response.headers["Sunset"] = version_info.sunset_date.strftime("%a, %d %b %Y %H:%M:%S GMT")
        
        # Latest version info
        latest_info = self.get_version_info(self.latest_stable)
        if version != self.latest_stable:
            response.headers["API-Latest-Version"] = self.latest_stable
            response.headers["API-Latest-Version-Full"] = latest_info.full_version
        
        # Migration hints
        if version_info.is_deprecated and version != self.latest_stable:
            migration_url = f"{request.base_url}api/{self.latest_stable}/migration/from/{version}"
            response.headers["API-Migration-Guide"] = str(migration_url)
        
        return response
    
    def create_deprecation_warning(self, version: str) -> Dict[str, Any]:
        """Create deprecation warning for response"""
        version_info = self.get_version_info(version)
        
        if not version_info.is_deprecated:
            return {}
        
        warning = {
            "deprecation_notice": {
                "message": f"API version {version} is deprecated",
                "status": version_info.status.value,
                "recommended_action": f"Migrate to {self.latest_stable}",
                "migration_guide": f"/api/{self.latest_stable}/migration/from/{version}"
            }
        }
        
        if version_info.sunset_date:
            warning["deprecation_notice"]["sunset_date"] = version_info.sunset_date.isoformat()
            warning["deprecation_notice"]["days_remaining"] = version_info.days_until_sunset
        
        return warning
    
    def get_version_summary(self) -> Dict[str, Any]:
        """Get summary of all API versions"""
        return {
            "current_stable": self.latest_stable,
            "default_version": self.default_version,
            "available_versions": {
                version: {
                    "status": info.status.value,
                    "full_version": info.full_version,
                    "description": info.description,
                    "is_deprecated": info.is_deprecated,
                    "supported_roles": [role.value for role in info.supported_roles]
                }
                for version, info in self.versions.items()
            },
            "compatibility_matrix": {
                from_ver: {
                    to_ver: self.check_compatibility(from_ver, to_ver).value
                    for to_ver in self.versions.keys()
                    if from_ver != to_ver
                }
                for from_ver in self.versions.keys()
            }
        }
    
    def deprecate_version(self, version: str, sunset_date: Optional[datetime] = None):
        """Deprecate an API version"""
        version_info = self.get_version_info(version)
        
        version_info.status = APIVersionStatus.DEPRECATED
        version_info.deprecation_date = datetime.now(timezone.utc)
        
        if sunset_date:
            version_info.sunset_date = sunset_date
        else:
            # Default sunset 12 months after deprecation
            version_info.sunset_date = version_info.deprecation_date + timedelta(days=365)
        
        # Update routing config to include deprecation warnings
        routing_config = self.get_routing_config(version)
        routing_config.deprecation_warnings = True
        
        logger.warning(f"API version {version} deprecated, sunset scheduled for {version_info.sunset_date}")
    
    def list_active_versions(self) -> List[str]:
        """List all active (non-archived) versions"""
        return [
            version for version, info in self.versions.items()
            if info.status != APIVersionStatus.ARCHIVED
        ]
    
    def get_rate_limit(self, version: str, role: str) -> int:
        """Get rate limit for version and role"""
        routing_config = self.get_routing_config(version)
        return routing_config.rate_limits.get(role, 1000)  # Default 1000/hour


def create_version_coordinator(message_router: MessageRouter) -> APIVersionCoordinator:
    """Factory function to create version coordinator"""
    return APIVersionCoordinator(message_router)