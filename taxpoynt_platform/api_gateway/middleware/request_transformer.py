"""
Role-Based Request Transformer Middleware
========================================
FastAPI middleware for transforming requests based on role-specific requirements.
Provides request enrichment, data transformation, and role-specific processing.
"""
import logging
import json
import re
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime, timezone
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.datastructures import MutableHeaders

from ...core_platform.authentication.role_manager import PlatformRole
from ..role_routing.models import HTTPRoutingContext, HTTPMethod

logger = logging.getLogger(__name__)


class TransformationType(Enum):
    """Types of request transformations."""
    HEADER_INJECTION = "header_injection"
    BODY_ENRICHMENT = "body_enrichment"
    FIELD_MAPPING = "field_mapping"
    DATA_NORMALIZATION = "data_normalization"
    ROLE_CONTEXT_INJECTION = "role_context_injection"
    ORGANIZATION_CONTEXT = "organization_context"
    TIMESTAMP_INJECTION = "timestamp_injection"
    REQUEST_ID_INJECTION = "request_id_injection"


@dataclass
class TransformationRule:
    """Request transformation rule configuration."""
    rule_id: str
    name: str
    path_pattern: str
    methods: Optional[List[HTTPMethod]] = None
    platform_roles: Optional[List[PlatformRole]] = None
    
    # Transformation types to apply
    transformations: List[TransformationType] = None
    
    # Header transformations
    inject_headers: Optional[Dict[str, str]] = None
    remove_headers: Optional[List[str]] = None
    header_mappings: Optional[Dict[str, str]] = None
    
    # Body transformations
    inject_fields: Optional[Dict[str, Any]] = None
    remove_fields: Optional[List[str]] = None
    field_mappings: Optional[Dict[str, str]] = None
    
    # Data transformations
    normalize_amounts: bool = False
    normalize_dates: bool = False
    normalize_addresses: bool = False
    
    # Role-specific transformations
    si_specific_transforms: Optional[Dict[str, Any]] = None
    app_specific_transforms: Optional[Dict[str, Any]] = None
    hybrid_specific_transforms: Optional[Dict[str, Any]] = None
    
    # Custom transformers
    custom_transformers: Optional[List[str]] = None


class RequestTransformer(BaseHTTPMiddleware):
    """
    Role-Based Request Transformer Middleware
    ========================================
    
    **Transformation Categories:**
    - **Header Management**: Inject, remove, or map request headers
    - **Body Enrichment**: Add context data to request bodies
    - **Data Normalization**: Standardize formats for amounts, dates, addresses
    - **Role Context**: Inject role-specific context and metadata
    - **Field Mapping**: Map between different data formats/schemas
    - **Organization Context**: Add organization-specific transformations
    
    **Role-Specific Transformations:**
    - **SI Requests**: ERP data normalization, integration metadata injection
    - **APP Requests**: FIRS format compliance, taxpayer context injection
    - **Hybrid Requests**: Cross-role data consistency, workflow metadata
    - **Admin Requests**: Audit trail injection, system context data
    """
    
    def __init__(
        self,
        app,
        enable_transformations: bool = True,
        enable_role_context_injection: bool = True,
        enable_data_normalization: bool = True,
        enable_audit_logging: bool = True,
        excluded_paths: Optional[List[str]] = None
    ):
        super().__init__(app)
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.enable_transformations = enable_transformations
        self.enable_role_context_injection = enable_role_context_injection
        self.enable_data_normalization = enable_data_normalization
        self.enable_audit_logging = enable_audit_logging
        
        # Excluded paths
        self.excluded_paths = excluded_paths or [
            "/health", "/docs", "/redoc", "/openapi.json"
        ]
        
        # Transformation rules
        self.transformation_rules: Dict[str, TransformationRule] = {}
        self.custom_transformers: Dict[str, Callable] = {}
        
        # Data normalizers
        self.data_normalizers = {
            "amount": self._normalize_amount,
            "date": self._normalize_date,
            "address": self._normalize_address,
            "phone": self._normalize_phone,
            "email": self._normalize_email,
            "tin": self._normalize_tin
        }
        
        # Metrics
        self.transformation_metrics = {
            "total_transformations": 0,
            "transformations_by_type": {},
            "transformations_by_role": {},
            "failed_transformations": 0
        }
        
        # Initialize default rules
        self._initialize_default_rules()
        
        logger.info("RequestTransformer middleware initialized")
    
    async def dispatch(self, request: Request, call_next):
        """Main middleware dispatch method."""
        try:
            # Skip transformations for excluded paths
            if not self.enable_transformations or self._is_excluded_path(request.url.path):
                return await call_next(request)
            
            # Get routing context from previous middleware
            routing_context = getattr(request.state, "routing_context", None)
            
            # Apply request transformations
            transformed_request = await self._transform_request(request, routing_context)
            
            # Continue with transformed request
            response = await call_next(transformed_request)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Request transformation error: {str(e)}")
            self.transformation_metrics["failed_transformations"] += 1
            # Continue without transformation on error
            return await call_next(request)
    
    async def _transform_request(
        self, 
        request: Request, 
        routing_context: Optional[HTTPRoutingContext]
    ) -> Request:
        """Apply transformations to the request."""
        
        self.transformation_metrics["total_transformations"] += 1
        
        # Track role-specific transformations
        if routing_context and routing_context.platform_role:
            role_key = routing_context.platform_role.value
            self.transformation_metrics["transformations_by_role"][role_key] = \
                self.transformation_metrics["transformations_by_role"].get(role_key, 0) + 1
        
        # Find applicable transformation rules
        applicable_rules = self._find_applicable_rules(request, routing_context)
        
        # Start with the original request
        transformed_request = request
        
        # Apply global transformations first
        if self.enable_role_context_injection and routing_context:
            transformed_request = await self._inject_role_context(transformed_request, routing_context)
        
        # Apply rule-based transformations
        for rule in applicable_rules:
            transformed_request = await self._apply_transformation_rule(
                transformed_request, rule, routing_context
            )
        
        # Apply role-specific transformations
        if routing_context and routing_context.platform_role:
            transformed_request = await self._apply_role_specific_transformations(
                transformed_request, routing_context
            )
        
        return transformed_request
    
    async def _inject_role_context(
        self, 
        request: Request, 
        routing_context: HTTPRoutingContext
    ) -> Request:
        """Inject role context into request."""
        
        # Create new headers with role context
        new_headers = dict(request.headers)
        
        # Inject role information
        new_headers["x-user-role"] = routing_context.platform_role.value
        new_headers["x-user-id"] = routing_context.user_id or ""
        new_headers["x-organization-id"] = routing_context.organization_id or ""
        new_headers["x-tenant-id"] = routing_context.tenant_id or ""
        new_headers["x-request-id"] = routing_context.request_id
        new_headers["x-request-timestamp"] = routing_context.request_timestamp.isoformat()
        
        # Inject correlation ID if present
        if routing_context.correlation_id:
            new_headers["x-correlation-id"] = routing_context.correlation_id
        
        # Inject permissions
        if routing_context.permissions:
            new_headers["x-user-permissions"] = ",".join(routing_context.permissions)
        
        # Track transformation
        self._track_transformation(TransformationType.ROLE_CONTEXT_INJECTION)
        
        return self._create_request_with_headers(request, new_headers)
    
    async def _apply_transformation_rule(
        self, 
        request: Request, 
        rule: TransformationRule,
        routing_context: Optional[HTTPRoutingContext]
    ) -> Request:
        """Apply a specific transformation rule."""
        
        transformed_request = request
        
        # Apply header transformations
        if rule.inject_headers or rule.remove_headers or rule.header_mappings:
            transformed_request = await self._transform_headers(
                transformed_request, rule, routing_context
            )
        
        # Apply body transformations
        if (rule.inject_fields or rule.remove_fields or rule.field_mappings or
            rule.normalize_amounts or rule.normalize_dates or rule.normalize_addresses):
            transformed_request = await self._transform_body(
                transformed_request, rule, routing_context
            )
        
        # Apply custom transformers
        if rule.custom_transformers:
            for transformer_name in rule.custom_transformers:
                transformer_func = self.custom_transformers.get(transformer_name)
                if transformer_func:
                    transformed_request = await transformer_func(
                        transformed_request, rule, routing_context
                    )
        
        return transformed_request
    
    async def _transform_headers(
        self, 
        request: Request, 
        rule: TransformationRule,
        routing_context: Optional[HTTPRoutingContext]
    ) -> Request:
        """Transform request headers."""
        
        new_headers = dict(request.headers)
        
        # Inject headers
        if rule.inject_headers:
            for header_name, header_value in rule.inject_headers.items():
                # Support dynamic values
                processed_value = self._process_dynamic_value(header_value, routing_context)
                new_headers[header_name] = processed_value
        
        # Remove headers
        if rule.remove_headers:
            for header_name in rule.remove_headers:
                new_headers.pop(header_name, None)
        
        # Map headers
        if rule.header_mappings:
            for old_header, new_header in rule.header_mappings.items():
                if old_header in new_headers:
                    new_headers[new_header] = new_headers.pop(old_header)
        
        self._track_transformation(TransformationType.HEADER_INJECTION)
        
        return self._create_request_with_headers(request, new_headers)
    
    async def _transform_body(
        self, 
        request: Request, 
        rule: TransformationRule,
        routing_context: Optional[HTTPRoutingContext]
    ) -> Request:
        """Transform request body."""
        
        if request.method not in ["POST", "PUT", "PATCH"]:
            return request
        
        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type:
            return request
        
        try:
            # Get request body
            body = await request.body()
            if not body:
                return request
            
            # Parse JSON
            data = json.loads(body)
            
            # Apply transformations
            transformed_data = await self._apply_body_transformations(
                data, rule, routing_context
            )
            
            # Create new request with transformed body
            new_body = json.dumps(transformed_data, default=str).encode()
            
            return self._create_request_with_body(request, new_body)
            
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse JSON body for transformation")
            return request
        except Exception as e:
            self.logger.error(f"Error transforming request body: {str(e)}")
            return request
    
    async def _apply_body_transformations(
        self,
        data: Dict[str, Any],
        rule: TransformationRule,
        routing_context: Optional[HTTPRoutingContext]
    ) -> Dict[str, Any]:
        """Apply body transformations to data."""
        
        # Make a copy to avoid modifying original
        transformed_data = data.copy()
        
        # Inject fields
        if rule.inject_fields:
            for field_name, field_value in rule.inject_fields.items():
                processed_value = self._process_dynamic_value(field_value, routing_context)
                self._set_nested_field(transformed_data, field_name, processed_value)
            
            self._track_transformation(TransformationType.BODY_ENRICHMENT)
        
        # Remove fields
        if rule.remove_fields:
            for field_name in rule.remove_fields:
                self._remove_nested_field(transformed_data, field_name)
        
        # Map fields
        if rule.field_mappings:
            for old_field, new_field in rule.field_mappings.items():
                value = self._get_nested_field(transformed_data, old_field)
                if value is not None:
                    self._set_nested_field(transformed_data, new_field, value)
                    self._remove_nested_field(transformed_data, old_field)
            
            self._track_transformation(TransformationType.FIELD_MAPPING)
        
        # Apply data normalization
        if rule.normalize_amounts or rule.normalize_dates or rule.normalize_addresses:
            transformed_data = await self._normalize_data(transformed_data, rule)
        
        return transformed_data
    
    async def _normalize_data(
        self, 
        data: Dict[str, Any], 
        rule: TransformationRule
    ) -> Dict[str, Any]:
        """Apply data normalization to request data."""
        
        def normalize_recursive(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {key: normalize_recursive(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [normalize_recursive(item) for item in obj]
            else:
                return obj
        
        # Normalize specific fields
        normalized_data = data.copy()
        
        if rule.normalize_amounts:
            normalized_data = self._normalize_amounts_in_data(normalized_data)
            self._track_transformation(TransformationType.DATA_NORMALIZATION)
        
        if rule.normalize_dates:
            normalized_data = self._normalize_dates_in_data(normalized_data)
            self._track_transformation(TransformationType.DATA_NORMALIZATION)
        
        if rule.normalize_addresses:
            normalized_data = self._normalize_addresses_in_data(normalized_data)
            self._track_transformation(TransformationType.DATA_NORMALIZATION)
        
        return normalized_data
    
    async def _apply_role_specific_transformations(
        self, 
        request: Request, 
        routing_context: HTTPRoutingContext
    ) -> Request:
        """Apply role-specific transformations."""
        
        role = routing_context.platform_role
        
        if role == PlatformRole.SYSTEM_INTEGRATOR:
            return await self._apply_si_transformations(request, routing_context)
        elif role == PlatformRole.ACCESS_POINT_PROVIDER:
            return await self._apply_app_transformations(request, routing_context)
        elif role == PlatformRole.HYBRID:
            return await self._apply_hybrid_transformations(request, routing_context)
        elif role == PlatformRole.PLATFORM_ADMIN:
            return await self._apply_admin_transformations(request, routing_context)
        
        return request
    
    async def _apply_si_transformations(
        self, 
        request: Request, 
        routing_context: HTTPRoutingContext
    ) -> Request:
        """Apply SI-specific transformations."""
        
        new_headers = dict(request.headers)
        
        # Inject SI-specific headers
        new_headers["x-integration-source"] = "taxpoynt_si"
        new_headers["x-erp-integration-timestamp"] = datetime.now(timezone.utc).isoformat()
        
        # Add organization context
        if routing_context.organization_id:
            new_headers["x-si-organization-context"] = routing_context.organization_id
        
        return self._create_request_with_headers(request, new_headers)
    
    async def _apply_app_transformations(
        self, 
        request: Request, 
        routing_context: HTTPRoutingContext
    ) -> Request:
        """Apply APP-specific transformations."""
        
        new_headers = dict(request.headers)
        
        # Inject APP-specific headers
        new_headers["x-app-source"] = "taxpoynt_app"
        new_headers["x-firs-submission-timestamp"] = datetime.now(timezone.utc).isoformat()
        
        # Add compliance context
        new_headers["x-compliance-mode"] = "firs_compliant"
        
        return self._create_request_with_headers(request, new_headers)
    
    async def _apply_hybrid_transformations(
        self, 
        request: Request, 
        routing_context: HTTPRoutingContext
    ) -> Request:
        """Apply hybrid-specific transformations."""
        
        new_headers = dict(request.headers)
        
        # Inject hybrid-specific headers
        new_headers["x-cross-role-operation"] = "true"
        new_headers["x-hybrid-timestamp"] = datetime.now(timezone.utc).isoformat()
        
        # Add workflow context
        if "/cross-role/" in str(request.url.path):
            new_headers["x-workflow-type"] = "cross_role"
        
        return self._create_request_with_headers(request, new_headers)
    
    async def _apply_admin_transformations(
        self, 
        request: Request, 
        routing_context: HTTPRoutingContext
    ) -> Request:
        """Apply admin-specific transformations."""
        
        new_headers = dict(request.headers)
        
        # Inject admin audit headers
        new_headers["x-admin-operation"] = "true"
        new_headers["x-audit-timestamp"] = datetime.now(timezone.utc).isoformat()
        new_headers["x-admin-user"] = routing_context.user_id
        
        # Add operation context for audit trail
        if request.method in ["PUT", "DELETE"]:
            new_headers["x-destructive-operation"] = "true"
        
        return self._create_request_with_headers(request, new_headers)
    
    # Data normalization methods
    def _normalize_amounts_in_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize monetary amounts in data."""
        
        amount_fields = ["amount", "total", "subtotal", "tax_amount", "net_amount", "gross_amount"]
        
        def normalize_amount_recursive(obj: Any) -> Any:
            if isinstance(obj, dict):
                normalized = {}
                for key, value in obj.items():
                    if key.lower() in amount_fields or "amount" in key.lower():
                        normalized[key] = self._normalize_amount(value)
                    else:
                        normalized[key] = normalize_amount_recursive(value)
                return normalized
            elif isinstance(obj, list):
                return [normalize_amount_recursive(item) for item in obj]
            else:
                return obj
        
        return normalize_amount_recursive(data)
    
    def _normalize_dates_in_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize date fields in data."""
        
        date_fields = ["date", "created_at", "updated_at", "timestamp", "due_date", "invoice_date"]
        
        def normalize_date_recursive(obj: Any) -> Any:
            if isinstance(obj, dict):
                normalized = {}
                for key, value in obj.items():
                    if key.lower() in date_fields or "date" in key.lower() or "time" in key.lower():
                        normalized[key] = self._normalize_date(value)
                    else:
                        normalized[key] = normalize_date_recursive(value)
                return normalized
            elif isinstance(obj, list):
                return [normalize_date_recursive(item) for item in obj]
            else:
                return obj
        
        return normalize_date_recursive(data)
    
    def _normalize_addresses_in_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize address fields in data."""
        
        address_fields = ["address", "billing_address", "shipping_address"]
        
        def normalize_address_recursive(obj: Any) -> Any:
            if isinstance(obj, dict):
                normalized = {}
                for key, value in obj.items():
                    if key.lower() in address_fields and isinstance(value, dict):
                        normalized[key] = self._normalize_address(value)
                    else:
                        normalized[key] = normalize_address_recursive(value)
                return normalized
            elif isinstance(obj, list):
                return [normalize_address_recursive(item) for item in obj]
            else:
                return obj
        
        return normalize_address_recursive(data)
    
    def _normalize_amount(self, value: Any) -> str:
        """Normalize amount to decimal string format."""
        if value is None:
            return "0.00"
        
        try:
            if isinstance(value, (int, float)):
                return f"{Decimal(str(value)):.2f}"
            elif isinstance(value, str):
                # Remove currency symbols and spaces
                cleaned = re.sub(r'[^\d.-]', '', value)
                return f"{Decimal(cleaned):.2f}"
            else:
                return str(value)
        except:
            return str(value)
    
    def _normalize_date(self, value: Any) -> str:
        """Normalize date to ISO format."""
        if value is None:
            return ""
        
        if isinstance(value, str):
            try:
                # Try to parse and reformat to ISO
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                return dt.isoformat()
            except:
                return value
        
        return str(value)
    
    def _normalize_address(self, address: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize address structure."""
        if not isinstance(address, dict):
            return address
        
        # Standard address field mapping
        field_mappings = {
            "addr1": "line1",
            "addr2": "line2", 
            "street": "line1",
            "street2": "line2",
            "city": "city",
            "state": "state",
            "province": "state",
            "zip": "postal_code",
            "zipcode": "postal_code",
            "postal": "postal_code",
            "country": "country"
        }
        
        normalized = {}
        for old_key, new_key in field_mappings.items():
            if old_key in address:
                normalized[new_key] = address[old_key]
        
        # Keep any unmapped fields
        for key, value in address.items():
            if key not in field_mappings and key not in normalized:
                normalized[key] = value
        
        return normalized
    
    def _normalize_phone(self, value: Any) -> str:
        """Normalize phone number format."""
        if not value:
            return ""
        
        # Remove all non-digit characters except +
        phone = re.sub(r'[^\d+]', '', str(value))
        
        # Basic formatting (this could be more sophisticated)
        if phone.startswith('+'):
            return phone
        elif len(phone) == 10:
            return f"+1{phone}"  # Assume US if 10 digits
        else:
            return phone
    
    def _normalize_email(self, value: Any) -> str:
        """Normalize email format."""
        if not value:
            return ""
        
        return str(value).lower().strip()
    
    def _normalize_tin(self, value: Any) -> str:
        """Normalize Tax Identification Number."""
        if not value:
            return ""
        
        # Remove all non-digit characters
        tin = re.sub(r'\D', '', str(value))
        return tin
    
    def _find_applicable_rules(
        self, 
        request: Request, 
        routing_context: Optional[HTTPRoutingContext]
    ) -> List[TransformationRule]:
        """Find transformation rules applicable to the request."""
        applicable_rules = []
        path = str(request.url.path)
        method = HTTPMethod(request.method)
        
        for rule in self.transformation_rules.values():
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
    
    def _process_dynamic_value(
        self, 
        value: str, 
        routing_context: Optional[HTTPRoutingContext]
    ) -> str:
        """Process dynamic values in transformation rules."""
        if not isinstance(value, str) or not routing_context:
            return str(value)
        
        # Replace placeholders
        replacements = {
            "{user_id}": routing_context.user_id or "",
            "{organization_id}": routing_context.organization_id or "",
            "{tenant_id}": routing_context.tenant_id or "",
            "{request_id}": routing_context.request_id,
            "{timestamp}": datetime.now(timezone.utc).isoformat(),
            "{role}": routing_context.platform_role.value if routing_context.platform_role else ""
        }
        
        processed_value = value
        for placeholder, replacement in replacements.items():
            processed_value = processed_value.replace(placeholder, replacement)
        
        return processed_value
    
    def _initialize_default_rules(self):
        """Initialize default transformation rules."""
        
        # SI endpoints rule
        si_rule = TransformationRule(
            rule_id="si_endpoints",
            name="SI Endpoints Transformation",
            path_pattern="/api/v*/si/**",
            methods=[HTTPMethod.POST, HTTPMethod.PUT],
            platform_roles=[PlatformRole.SYSTEM_INTEGRATOR, PlatformRole.HYBRID],
            transformations=[
                TransformationType.ROLE_CONTEXT_INJECTION,
                TransformationType.TIMESTAMP_INJECTION,
                TransformationType.DATA_NORMALIZATION
            ],
            inject_headers={
                "x-si-request": "true",
                "x-processing-timestamp": "{timestamp}"
            },
            inject_fields={
                "metadata.processed_by": "taxpoynt_si",
                "metadata.processing_timestamp": "{timestamp}",
                "metadata.organization_id": "{organization_id}"
            },
            normalize_amounts=True,
            normalize_dates=True
        )
        
        # APP endpoints rule
        app_rule = TransformationRule(
            rule_id="app_endpoints",
            name="APP Endpoints Transformation",
            path_pattern="/api/v*/app/**",
            methods=[HTTPMethod.POST, HTTPMethod.PUT],
            platform_roles=[PlatformRole.ACCESS_POINT_PROVIDER, PlatformRole.HYBRID],
            transformations=[
                TransformationType.ROLE_CONTEXT_INJECTION,
                TransformationType.BODY_ENRICHMENT
            ],
            inject_headers={
                "x-app-request": "true",
                "x-firs-compliance": "true"
            },
            inject_fields={
                "metadata.firs_compliant": True,
                "metadata.submission_timestamp": "{timestamp}",
                "metadata.app_version": "2.0"
            },
            normalize_amounts=True,
            normalize_dates=True
        )
        
        # Admin endpoints rule
        admin_rule = TransformationRule(
            rule_id="admin_endpoints",
            name="Admin Endpoints Transformation",
            path_pattern="/api/v*/admin/**",
            platform_roles=[PlatformRole.PLATFORM_ADMIN],
            inject_headers={
                "x-admin-request": "true",
                "x-audit-required": "true"
            },
            inject_fields={
                "audit.admin_user": "{user_id}",
                "audit.operation_timestamp": "{timestamp}",
                "audit.request_id": "{request_id}"
            }
        )
        
        # Store rules
        self.transformation_rules = {
            si_rule.rule_id: si_rule,
            app_rule.rule_id: app_rule,
            admin_rule.rule_id: admin_rule
        }
    
    # Helper methods
    def _is_excluded_path(self, path: str) -> bool:
        """Check if path is excluded from transformation."""
        return any(path.startswith(excluded) for excluded in self.excluded_paths)
    
    def _path_matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if path matches pattern."""
        import fnmatch
        return fnmatch.fnmatch(path, pattern)
    
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
    
    def _set_nested_field(self, data: Dict[str, Any], field_path: str, value: Any):
        """Set nested field value in data."""
        keys = field_path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _remove_nested_field(self, data: Dict[str, Any], field_path: str):
        """Remove nested field from data."""
        keys = field_path.split('.')
        current = data
        
        for key in keys[:-1]:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return
        
        if isinstance(current, dict) and keys[-1] in current:
            del current[keys[-1]]
    
    def _create_request_with_headers(self, request: Request, new_headers: Dict[str, str]) -> Request:
        """Create new request with modified headers."""
        # This is a simplified implementation
        # In a real scenario, you might need to handle this differently
        # depending on your FastAPI setup
        
        # Update request headers
        request._headers = MutableHeaders(new_headers)
        return request
    
    def _create_request_with_body(self, request: Request, new_body: bytes) -> Request:
        """Create new request with modified body."""
        # This is a simplified implementation
        # You might need to create a new Request object or use a different approach
        # depending on your specific requirements
        
        # Store new body in request state for access by downstream handlers
        request.state.transformed_body = new_body
        return request
    
    def _track_transformation(self, transformation_type: TransformationType):
        """Track transformation metrics."""
        type_key = transformation_type.value
        self.transformation_metrics["transformations_by_type"][type_key] = \
            self.transformation_metrics["transformations_by_type"].get(type_key, 0) + 1
    
    # Public API methods
    async def add_transformation_rule(self, rule: TransformationRule):
        """Add a new transformation rule."""
        self.transformation_rules[rule.rule_id] = rule
        self.logger.info(f"Added transformation rule: {rule.name}")
    
    async def add_custom_transformer(self, name: str, transformer_func: Callable):
        """Add a custom transformer function."""
        self.custom_transformers[name] = transformer_func
        self.logger.info(f"Added custom transformer: {name}")
    
    async def get_transformation_metrics(self) -> Dict[str, Any]:
        """Get transformation metrics."""
        return {
            "transformation_metrics": self.transformation_metrics.copy(),
            "active_rules": len(self.transformation_rules),
            "custom_transformers": len(self.custom_transformers),
            "data_normalizers": len(self.data_normalizers)
        }


def create_request_transformer(**kwargs) -> RequestTransformer:
    """Factory function to create RequestTransformer middleware."""
    return RequestTransformer(app=None, **kwargs)