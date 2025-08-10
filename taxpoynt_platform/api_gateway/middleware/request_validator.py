"""
Role-Based Request Validator Middleware
======================================
FastAPI middleware for validating requests according to role-specific rules.
Provides comprehensive request validation, sanitization, and security checks.
"""
import logging
import json
import re
from typing import Dict, Any, List, Optional, Callable, Set, Pattern
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, ValidationError, validator
from email_validator import validate_email, EmailNotValidError

from ...core_platform.authentication.role_manager import PlatformRole, RoleScope
from ..role_routing.models import HTTPRoutingContext, HTTPMethod, RouteType

logger = logging.getLogger(__name__)


class ValidationRule(BaseModel):
    """Request validation rule configuration."""
    rule_id: str
    name: str
    path_pattern: str
    methods: Optional[List[HTTPMethod]] = None
    platform_roles: Optional[List[PlatformRole]] = None
    
    # Request validation
    max_payload_size: Optional[int] = None  # bytes
    allowed_content_types: Optional[List[str]] = None
    required_headers: Optional[List[str]] = None
    forbidden_headers: Optional[List[str]] = None
    
    # Field validation
    required_fields: Optional[List[str]] = None
    forbidden_fields: Optional[List[str]] = None
    field_validators: Optional[Dict[str, str]] = None  # field -> validation_type
    field_max_lengths: Optional[Dict[str, int]] = None
    
    # Security validation
    sql_injection_check: bool = True
    xss_check: bool = True
    path_traversal_check: bool = True
    command_injection_check: bool = True
    
    # Business validation
    organization_context_required: bool = False
    tenant_context_required: bool = False
    
    # Custom validators
    custom_validators: Optional[List[str]] = None


class RequestValidator(BaseHTTPMiddleware):
    """
    Role-Based Request Validator Middleware
    ======================================
    
    **Validation Categories:**
    - **Input Sanitization**: SQL injection, XSS, path traversal prevention
    - **Data Validation**: Type checking, format validation, business rules
    - **Role-Specific Rules**: Different validation rules per platform role
    - **Security Checks**: Payload size limits, content type validation
    - **Business Logic**: Organization context, tenant validation
    
    **Role-Specific Validation:**
    - **SI Requests**: ERP data formats, integration schemas, certificate validation
    - **APP Requests**: FIRS compliance, taxpayer data, transmission formats
    - **Hybrid Requests**: Cross-role data consistency, workflow validation
    - **Admin Requests**: System configuration, user management data
    """
    
    def __init__(
        self,
        app,
        enable_sql_injection_protection: bool = True,
        enable_xss_protection: bool = True,
        enable_path_traversal_protection: bool = True,
        default_max_payload_size: int = 10 * 1024 * 1024,  # 10MB
        strict_validation: bool = False,
        excluded_paths: Optional[List[str]] = None
    ):
        super().__init__(app)
        self.logger = logging.getLogger(__name__)
        
        # Security configuration
        self.enable_sql_injection_protection = enable_sql_injection_protection
        self.enable_xss_protection = enable_xss_protection
        self.enable_path_traversal_protection = enable_path_traversal_protection
        self.default_max_payload_size = default_max_payload_size
        self.strict_validation = strict_validation
        
        # Excluded paths
        self.excluded_paths = excluded_paths or [
            "/health", "/docs", "/redoc", "/openapi.json"
        ]
        
        # Validation rules
        self.validation_rules: Dict[str, ValidationRule] = {}
        self.custom_validators: Dict[str, Callable] = {}
        
        # Security patterns
        self.sql_injection_patterns = self._compile_sql_injection_patterns()
        self.xss_patterns = self._compile_xss_patterns()
        self.path_traversal_patterns = self._compile_path_traversal_patterns()
        self.command_injection_patterns = self._compile_command_injection_patterns()
        
        # Business validation patterns
        self.business_validators = self._initialize_business_validators()
        
        # Metrics
        self.validation_metrics = {
            "total_validations": 0,
            "successful_validations": 0,
            "failed_validations": 0,
            "security_violations": 0,
            "business_rule_violations": 0,
            "validation_errors_by_type": {}
        }
        
        # Initialize default validation rules
        self._initialize_default_rules()
        
        logger.info("RequestValidator middleware initialized")
    
    async def dispatch(self, request: Request, call_next):
        """Main middleware dispatch method."""
        try:
            # Skip validation for excluded paths
            if self._is_excluded_path(request.url.path):
                return await call_next(request)
            
            self.validation_metrics["total_validations"] += 1
            
            # Get routing context from previous middleware
            routing_context = getattr(request.state, "routing_context", None)
            
            # Perform request validation
            await self._validate_request(request, routing_context)
            
            # Continue with request
            response = await call_next(request)
            
            self.validation_metrics["successful_validations"] += 1
            return response
            
        except HTTPException as e:
            self.validation_metrics["failed_validations"] += 1
            
            # Track specific error types
            error_type = self._classify_error(e)
            self.validation_metrics["validation_errors_by_type"][error_type] = \
                self.validation_metrics["validation_errors_by_type"].get(error_type, 0) + 1
            
            self.logger.warning(f"Request validation failed: {e.detail}")
            raise
        except Exception as e:
            self.logger.error(f"Validation error: {str(e)}")
            self.validation_metrics["failed_validations"] += 1
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Request validation service error"
            )
    
    async def _validate_request(self, request: Request, routing_context: Optional[HTTPRoutingContext]):
        """Perform comprehensive request validation."""
        
        # 1. Basic security validation
        await self._validate_basic_security(request)
        
        # 2. Find applicable validation rules
        applicable_rules = self._find_applicable_rules(request, routing_context)
        
        # 3. Apply validation rules
        for rule in applicable_rules:
            await self._apply_validation_rule(request, rule, routing_context)
        
        # 4. Role-specific validation
        if routing_context and routing_context.platform_role:
            await self._validate_role_specific_rules(request, routing_context)
        
        # 5. Business logic validation
        await self._validate_business_logic(request, routing_context)
    
    async def _validate_basic_security(self, request: Request):
        """Perform basic security validation."""
        
        # Check payload size
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.default_max_payload_size:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Payload too large. Maximum allowed: {self.default_max_payload_size} bytes"
                    )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Content-Length header"
                )
        
        # Validate URL path
        if self.enable_path_traversal_protection:
            await self._check_path_traversal(request.url.path)
        
        # Validate query parameters
        for key, value in request.query_params.items():
            await self._validate_parameter_security(key, value)
        
        # Validate headers
        await self._validate_headers_security(request)
    
    async def _check_path_traversal(self, path: str):
        """Check for path traversal attacks."""
        for pattern in self.path_traversal_patterns:
            if pattern.search(path):
                self.validation_metrics["security_violations"] += 1
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Path traversal attempt detected"
                )
    
    async def _validate_parameter_security(self, key: str, value: str):
        """Validate parameter for security issues."""
        
        # SQL injection check
        if self.enable_sql_injection_protection:
            for pattern in self.sql_injection_patterns:
                if pattern.search(value.lower()):
                    self.validation_metrics["security_violations"] += 1
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"SQL injection attempt detected in parameter: {key}"
                    )
        
        # XSS check
        if self.enable_xss_protection:
            for pattern in self.xss_patterns:
                if pattern.search(value.lower()):
                    self.validation_metrics["security_violations"] += 1
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"XSS attempt detected in parameter: {key}"
                    )
        
        # Command injection check
        for pattern in self.command_injection_patterns:
            if pattern.search(value):
                self.validation_metrics["security_violations"] += 1
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Command injection attempt detected in parameter: {key}"
                )
    
    async def _validate_headers_security(self, request: Request):
        """Validate request headers for security."""
        suspicious_headers = [
            "x-forwarded-host", "x-cluster-client-ip", "x-real-ip"
        ]
        
        for header in suspicious_headers:
            value = request.headers.get(header)
            if value:
                # Basic validation for IP headers
                if header.endswith("-ip") and not self._is_valid_ip(value):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid IP address in header: {header}"
                    )
    
    def _find_applicable_rules(
        self, 
        request: Request, 
        routing_context: Optional[HTTPRoutingContext]
    ) -> List[ValidationRule]:
        """Find validation rules applicable to the request."""
        applicable_rules = []
        path = str(request.url.path)
        method = HTTPMethod(request.method)
        
        for rule in self.validation_rules.values():
            # Check path pattern
            if not self._path_matches_pattern(path, rule.path_pattern):
                continue
            
            # Check HTTP method
            if rule.methods and method not in rule.methods:
                continue
            
            # Check platform role
            if rule.platform_roles and routing_context:
                if routing_context.platform_role not in rule.platform_roles:
                    continue
            
            applicable_rules.append(rule)
        
        return applicable_rules
    
    async def _apply_validation_rule(
        self, 
        request: Request, 
        rule: ValidationRule, 
        routing_context: Optional[HTTPRoutingContext]
    ):
        """Apply a specific validation rule."""
        
        # Validate content type
        if rule.allowed_content_types:
            content_type = request.headers.get("content-type", "")
            if not any(ct in content_type for ct in rule.allowed_content_types):
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail=f"Content type not allowed. Allowed: {rule.allowed_content_types}"
                )
        
        # Validate required headers
        if rule.required_headers:
            for header in rule.required_headers:
                if header not in request.headers:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Required header missing: {header}"
                    )
        
        # Check forbidden headers
        if rule.forbidden_headers:
            for header in rule.forbidden_headers:
                if header in request.headers:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Forbidden header present: {header}"
                    )
        
        # Validate payload size
        if rule.max_payload_size:
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > rule.max_payload_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Payload exceeds rule limit: {rule.max_payload_size} bytes"
                )
        
        # Validate request body if JSON
        if request.method in ["POST", "PUT", "PATCH"]:
            await self._validate_request_body(request, rule)
        
        # Apply custom validators
        if rule.custom_validators:
            for validator_name in rule.custom_validators:
                validator_func = self.custom_validators.get(validator_name)
                if validator_func:
                    await validator_func(request, rule, routing_context)
    
    async def _validate_request_body(self, request: Request, rule: ValidationRule):
        """Validate request body content."""
        content_type = request.headers.get("content-type", "")
        
        if "application/json" not in content_type:
            return
        
        try:
            # Get request body (this might consume the stream)
            body = await request.body()
            if not body:
                return
            
            # Parse JSON
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid JSON in request body"
                )
            
            # Validate required fields
            if rule.required_fields:
                missing_fields = []
                for field in rule.required_fields:
                    if not self._has_nested_field(data, field):
                        missing_fields.append(field)
                
                if missing_fields:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Missing required fields: {missing_fields}"
                    )
            
            # Check forbidden fields
            if rule.forbidden_fields:
                forbidden_found = []
                for field in rule.forbidden_fields:
                    if self._has_nested_field(data, field):
                        forbidden_found.append(field)
                
                if forbidden_found:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Forbidden fields present: {forbidden_found}"
                    )
            
            # Apply field validators
            if rule.field_validators:
                await self._validate_fields(data, rule.field_validators)
            
            # Check field max lengths
            if rule.field_max_lengths:
                await self._validate_field_lengths(data, rule.field_max_lengths)
            
            # Security checks on all string values
            await self._validate_body_security(data)
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error validating request body: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request body validation failed"
            )
    
    async def _validate_fields(self, data: Dict[str, Any], field_validators: Dict[str, str]):
        """Validate specific fields using validators."""
        for field_path, validator_type in field_validators.items():
            value = self._get_nested_field(data, field_path)
            if value is not None:
                await self._apply_field_validator(field_path, value, validator_type)
    
    async def _apply_field_validator(self, field_path: str, value: Any, validator_type: str):
        """Apply specific validator to field value."""
        try:
            if validator_type == "email":
                if isinstance(value, str):
                    validate_email(value)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Field {field_path} must be a string for email validation"
                    )
            
            elif validator_type == "uuid":
                import uuid
                if isinstance(value, str):
                    uuid.UUID(value)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Field {field_path} must be a valid UUID string"
                    )
            
            elif validator_type == "tin":  # Tax Identification Number
                if isinstance(value, str) and not re.match(r'^\d{10,14}$', value):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Field {field_path} must be a valid TIN (10-14 digits)"
                    )
            
            elif validator_type == "amount":
                try:
                    if isinstance(value, (int, float)):
                        decimal_value = Decimal(str(value))
                    elif isinstance(value, str):
                        decimal_value = Decimal(value)
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Field {field_path} must be a valid number"
                        )
                    
                    if decimal_value < 0:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Field {field_path} must be a positive amount"
                        )
                except InvalidOperation:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Field {field_path} must be a valid decimal amount"
                    )
            
            elif validator_type == "date":
                if isinstance(value, str):
                    try:
                        datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except ValueError:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Field {field_path} must be a valid ISO date"
                        )
            
            elif validator_type == "phone":
                if isinstance(value, str) and not re.match(r'^\+?[\d\s\-\(\)]{7,15}$', value):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Field {field_path} must be a valid phone number"
                    )
            
        except EmailNotValidError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Field {field_path} must be a valid email address"
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Field {field_path} validation failed: {str(e)}"
            )
    
    async def _validate_field_lengths(self, data: Dict[str, Any], field_max_lengths: Dict[str, int]):
        """Validate field maximum lengths."""
        for field_path, max_length in field_max_lengths.items():
            value = self._get_nested_field(data, field_path)
            if value is not None and isinstance(value, str):
                if len(value) > max_length:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Field {field_path} exceeds maximum length of {max_length}"
                    )
    
    async def _validate_body_security(self, data: Any):
        """Recursively validate all string values in request body for security."""
        if isinstance(data, dict):
            for key, value in data.items():
                await self._validate_body_security(value)
        elif isinstance(data, list):
            for item in data:
                await self._validate_body_security(item)
        elif isinstance(data, str):
            await self._validate_parameter_security("body_field", data)
    
    async def _validate_role_specific_rules(self, request: Request, routing_context: HTTPRoutingContext):
        """Apply role-specific validation rules."""
        role = routing_context.platform_role
        
        if role == PlatformRole.SYSTEM_INTEGRATOR:
            await self._validate_si_request(request, routing_context)
        elif role == PlatformRole.ACCESS_POINT_PROVIDER:
            await self._validate_app_request(request, routing_context)
        elif role == PlatformRole.HYBRID:
            await self._validate_hybrid_request(request, routing_context)
        elif role == PlatformRole.PLATFORM_ADMIN:
            await self._validate_admin_request(request, routing_context)
    
    async def _validate_si_request(self, request: Request, routing_context: HTTPRoutingContext):
        """Validate SI-specific request requirements."""
        # Require organization context for SI operations
        if not routing_context.organization_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization context required for SI operations"
            )
        
        # Validate SI-specific headers
        si_headers = ["x-erp-system", "x-integration-type"]
        for header in si_headers:
            if header in request.headers:
                value = request.headers[header]
                if not re.match(r'^[a-zA-Z0-9_\-\.]+$', value):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid format for header {header}"
                    )
    
    async def _validate_app_request(self, request: Request, routing_context: HTTPRoutingContext):
        """Validate APP-specific request requirements."""
        # Validate taxpayer context if required
        path = str(request.url.path)
        if "/taxpayer/" in path or "/firs/" in path:
            taxpayer_id = request.headers.get("x-taxpayer-id") or request.query_params.get("taxpayer_id")
            if not taxpayer_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Taxpayer ID required for this operation"
                )
    
    async def _validate_hybrid_request(self, request: Request, routing_context: HTTPRoutingContext):
        """Validate hybrid request requirements."""
        # For hybrid requests, validate cross-role consistency
        path = str(request.url.path)
        if "/hybrid/cross-role" in path:
            # Require both organization and process context
            if not routing_context.organization_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Organization context required for cross-role operations"
                )
    
    async def _validate_admin_request(self, request: Request, routing_context: HTTPRoutingContext):
        """Validate admin request requirements."""
        # Admin requests require strict validation
        if request.method in ["DELETE", "PUT"]:
            confirmation = request.headers.get("x-admin-confirmation")
            if not confirmation or confirmation.lower() != "confirmed":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Admin confirmation required for destructive operations"
                )
    
    async def _validate_business_logic(self, request: Request, routing_context: Optional[HTTPRoutingContext]):
        """Validate business logic rules."""
        # Apply business validators
        for validator_name, validator_func in self.business_validators.items():
            try:
                await validator_func(request, routing_context)
            except Exception as e:
                self.validation_metrics["business_rule_violations"] += 1
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Business rule violation ({validator_name}): {str(e)}"
                )
    
    def _compile_sql_injection_patterns(self) -> List[Pattern]:
        """Compile SQL injection detection patterns."""
        patterns = [
            r'\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b',
            r'[\'\"]\s*;\s*--',
            r'\b(or|and)\s+[\'\"]*\d+[\'\"]*\s*=\s*[\'\"]*\d+[\'\"]*',
            r'\'\s*(or|and)\s+\'',
            r'(\%27)|(\')|(\\x27)',
            r'(\%22)|(\")|(\\x22)',
        ]
        return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    def _compile_xss_patterns(self) -> List[Pattern]:
        """Compile XSS detection patterns."""
        patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'<link[^>]*>',
            r'<meta[^>]*>',
        ]
        return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    def _compile_path_traversal_patterns(self) -> List[Pattern]:
        """Compile path traversal detection patterns."""
        patterns = [
            r'\.\./|\.\.\',
            r'%2e%2e%2f',
            r'%252e%252e%252f',
            r'\.\.\\|\.\.%5c',
            r'%2e%2e%5c',
        ]
        return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    def _compile_command_injection_patterns(self) -> List[Pattern]:
        """Compile command injection detection patterns."""
        patterns = [
            r'[;&|`]',
            r'\$\(',
            r'`[^`]*`',
            r'\|\s*\w+',
            r'&&|\|\|',
        ]
        return [re.compile(pattern) for pattern in patterns]
    
    def _initialize_business_validators(self) -> Dict[str, Callable]:
        """Initialize business logic validators."""
        return {
            "invoice_amount_validator": self._validate_invoice_amount,
            "organization_permissions": self._validate_organization_permissions,
            "rate_limit_validator": self._validate_rate_limits,
        }
    
    async def _validate_invoice_amount(self, request: Request, routing_context: Optional[HTTPRoutingContext]):
        """Validate invoice amounts are reasonable."""
        if request.method not in ["POST", "PUT"]:
            return
        
        body = await request.body()
        if body:
            try:
                data = json.loads(body)
                amount = data.get("amount") or data.get("total_amount")
                if amount and isinstance(amount, (int, float)):
                    if amount > 1000000000:  # 1 billion limit
                        raise ValueError("Invoice amount exceeds maximum allowed")
                    if amount < 0:
                        raise ValueError("Invoice amount cannot be negative")
            except json.JSONDecodeError:
                pass  # Already handled in earlier validation
    
    async def _validate_organization_permissions(self, request: Request, routing_context: Optional[HTTPRoutingContext]):
        """Validate organization-level permissions."""
        if not routing_context or not routing_context.organization_id:
            return
        
        # Check if user has permission to access this organization
        # This would typically check against a database
        pass
    
    async def _validate_rate_limits(self, request: Request, routing_context: Optional[HTTPRoutingContext]):
        """Validate request against rate limits."""
        # This would typically integrate with a rate limiting service
        pass
    
    def _initialize_default_rules(self):
        """Initialize default validation rules for different endpoints."""
        
        # SI endpoints validation rule
        si_rule = ValidationRule(
            rule_id="si_endpoints",
            name="SI Endpoints Validation",
            path_pattern="/api/v*/si/**",
            methods=[HTTPMethod.POST, HTTPMethod.PUT],
            platform_roles=[PlatformRole.SYSTEM_INTEGRATOR, PlatformRole.HYBRID],
            max_payload_size=5 * 1024 * 1024,  # 5MB
            allowed_content_types=["application/json"],
            required_headers=["x-organization-id"],
            field_validators={
                "organization_id": "uuid",
                "amount": "amount",
                "email": "email"
            },
            organization_context_required=True
        )
        
        # APP endpoints validation rule
        app_rule = ValidationRule(
            rule_id="app_endpoints",
            name="APP Endpoints Validation",
            path_pattern="/api/v*/app/**",
            methods=[HTTPMethod.POST, HTTPMethod.PUT],
            platform_roles=[PlatformRole.ACCESS_POINT_PROVIDER, PlatformRole.HYBRID],
            max_payload_size=10 * 1024 * 1024,  # 10MB
            allowed_content_types=["application/json", "application/xml"],
            field_validators={
                "taxpayer_id": "tin",
                "amount": "amount",
                "submission_date": "date"
            },
            organization_context_required=True
        )
        
        # Admin endpoints validation rule
        admin_rule = ValidationRule(
            rule_id="admin_endpoints",
            name="Admin Endpoints Validation",
            path_pattern="/api/v*/admin/**",
            methods=[HTTPMethod.POST, HTTPMethod.PUT, HTTPMethod.DELETE],
            platform_roles=[PlatformRole.PLATFORM_ADMIN],
            max_payload_size=1 * 1024 * 1024,  # 1MB
            allowed_content_types=["application/json"],
            required_headers=["x-admin-confirmation"],
            field_validators={
                "user_id": "uuid",
                "email": "email"
            }
        )
        
        # Store rules
        self.validation_rules = {
            si_rule.rule_id: si_rule,
            app_rule.rule_id: app_rule,
            admin_rule.rule_id: admin_rule
        }
    
    # Helper methods
    def _is_excluded_path(self, path: str) -> bool:
        """Check if path is excluded from validation."""
        return any(path.startswith(excluded) for excluded in self.excluded_paths)
    
    def _path_matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if path matches pattern."""
        import fnmatch
        return fnmatch.fnmatch(path, pattern)
    
    def _has_nested_field(self, data: Dict[str, Any], field_path: str) -> bool:
        """Check if nested field exists in data."""
        return self._get_nested_field(data, field_path) is not None
    
    def _get_nested_field(self, data: Dict[str, Any], field_path: str) -> Any:
        """Get nested field value from data."""
        keys = field_path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Validate IP address format."""
        import ipaddress
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def _classify_error(self, error: HTTPException) -> str:
        """Classify error for metrics."""
        if error.status_code == 400:
            if "SQL injection" in error.detail:
                return "sql_injection"
            elif "XSS" in error.detail:
                return "xss_attempt"
            elif "validation failed" in error.detail:
                return "validation_error"
            else:
                return "bad_request"
        elif error.status_code == 413:
            return "payload_too_large"
        elif error.status_code == 415:
            return "unsupported_media_type"
        elif error.status_code == 422:
            return "business_rule_violation"
        else:
            return "other"
    
    # Public API methods
    async def add_validation_rule(self, rule: ValidationRule):
        """Add a new validation rule."""
        self.validation_rules[rule.rule_id] = rule
        self.logger.info(f"Added validation rule: {rule.name}")
    
    async def add_custom_validator(self, name: str, validator_func: Callable):
        """Add a custom validator function."""
        self.custom_validators[name] = validator_func
        self.logger.info(f"Added custom validator: {name}")
    
    async def get_validation_metrics(self) -> Dict[str, Any]:
        """Get validation metrics."""
        return {
            "validation_metrics": self.validation_metrics.copy(),
            "active_rules": len(self.validation_rules),
            "custom_validators": len(self.custom_validators)
        }


def create_request_validator(**kwargs) -> RequestValidator:
    """Factory function to create RequestValidator middleware."""
    return RequestValidator(app=None, **kwargs)