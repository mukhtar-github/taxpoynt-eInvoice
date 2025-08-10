"""
Role-Specific Postman Collections Generator
==========================================
Automatically generates Postman collections for each role type from their
respective OpenAPI specifications, enabling easy API testing and exploration.
"""

import json
import uuid
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from .si_api_docs import SIAPIDocumentationGenerator
from .app_api_docs import APPAPIDocumentationGenerator
from .hybrid_api_docs import HybridAPIDocumentationGenerator


class RoleType(Enum):
    """TaxPoynt user role types."""
    SI = "system_integrator"
    APP = "access_point_provider"
    HYBRID = "hybrid"


@dataclass
class PostmanEnvironment:
    """Postman environment configuration."""
    name: str
    values: List[Dict[str, Any]]


class PostmanCollectionGenerator:
    """Generates role-specific Postman collections from OpenAPI specifications."""
    
    def __init__(self):
        self.si_generator = SIAPIDocumentationGenerator()
        self.app_generator = APPAPIDocumentationGenerator()
        self.hybrid_generator = HybridAPIDocumentationGenerator()
        
        # Postman collection schema version
        self.schema_version = "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    
    def generate_collection(self, role: RoleType, output_dir: str, include_environments: bool = True) -> Dict[str, Any]:
        """Generate complete Postman collection for specified role."""
        
        # Get OpenAPI spec for role
        openapi_spec = self._get_openapi_spec_for_role(role)
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate collection
        collection = self._create_postman_collection(role, openapi_spec)
        
        # Save collection file
        collection_file = output_path / f"taxpoynt_{role.value}_api.postman_collection.json"
        with open(collection_file, "w") as f:
            json.dump(collection, f, indent=2)
        
        generated_files = {"collection": str(collection_file)}
        
        # Generate environments if requested
        if include_environments:
            environments = self._generate_environments(role, output_path)
            generated_files["environments"] = environments
        
        # Generate documentation
        docs = self._generate_collection_documentation(role, collection, output_path)
        generated_files["documentation"] = docs
        
        return {
            "status": "success",
            "role": role.value,
            "collection_name": collection["info"]["name"],
            "total_requests": len(self._count_requests(collection)),
            "generated_files": generated_files
        }
    
    def _get_openapi_spec_for_role(self, role: RoleType) -> Dict[str, Any]:
        """Get OpenAPI specification for specific role."""
        if role == RoleType.SI:
            return self.si_generator.generate_openapi_spec()
        elif role == RoleType.APP:
            return self.app_generator.generate_openapi_spec()
        elif role == RoleType.HYBRID:
            return self.hybrid_generator.generate_unified_openapi_spec()
        else:
            raise ValueError(f"Unknown role type: {role}")
    
    def _create_postman_collection(self, role: RoleType, openapi_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Create Postman collection from OpenAPI specification."""
        
        role_display = role.value.replace("_", " ").title()
        
        collection = {
            "info": {
                "_postman_id": str(uuid.uuid4()),
                "name": f"TaxPoynt {role_display} API",
                "description": self._get_collection_description(role, openapi_spec),
                "schema": self.schema_version,
                "_exporter_id": "taxpoynt-generator"
            },
            "item": [],
            "auth": {
                "type": "apikey",
                "apikey": [
                    {"key": "key", "value": "X-API-Key", "type": "string"},
                    {"key": "value", "value": "{{api_key}}", "type": "string"},
                    {"key": "in", "value": "header", "type": "string"}
                ]
            },
            "event": self._create_collection_events(),
            "variable": self._create_collection_variables(role)
        }
        
        # Group endpoints by tags and create folders
        endpoints_by_tag = self._group_endpoints_by_tag(openapi_spec)
        
        for tag, endpoints in endpoints_by_tag.items():
            folder = self._create_folder(tag, endpoints, openapi_spec)
            collection["item"].append(folder)
        
        return collection
    
    def _get_collection_description(self, role: RoleType, openapi_spec: Dict[str, Any]) -> str:
        """Get description for the collection."""
        
        base_description = openapi_spec.get("info", {}).get("description", "")
        
        role_descriptions = {
            RoleType.SI: """
## TaxPoynt System Integrator API Collection

This collection contains all API endpoints for System Integrator role users. Use these APIs to:

- **Connect Financial Systems**: Integrate payment processors (Paystack, Moniepoint, OPay, PalmPay, Interswitch, Flutterwave, Stripe)
- **Sync Business Data**: Connect ERP/CRM systems (Odoo, SAP, Dynamics, NetSuite)
- **Transform Data**: Convert business data to e-invoice standards
- **Generate Documents**: Create UBL-compliant e-invoices and PDFs
- **Manage Certificates**: Handle digital certificates for secure operations

### Authentication
Set your API key in the collection variables or environment:
- Variable: `api_key`
- Header: `X-API-Key`

### Environments
- **Production**: https://api.taxpoynt.com
- **Sandbox**: https://sandbox-api.taxpoynt.com
            """,
            RoleType.APP: """
## TaxPoynt Access Point Provider API Collection

This collection contains all API endpoints for Access Point Provider role users. Use these APIs to:

- **Submit to FIRS**: Direct submission of e-invoices to FIRS systems
- **Manage Taxpayers**: Register and manage taxpayer organizations
- **Track Compliance**: Monitor submission status and compliance metrics
- **Generate Reports**: Create regulatory compliance reports
- **Handle Webhooks**: Manage real-time FIRS notifications

### Authentication
Set your API key in the collection variables or environment:
- Variable: `api_key`
- Header: `X-API-Key`

### TaxPoynt as Your APP
TaxPoynt serves as your certified Access Point Provider, handling all technical complexities of FIRS integration.
            """,
            RoleType.HYBRID: """
## TaxPoynt Hybrid API Collection

This collection contains all API endpoints for Hybrid role users with both SI and APP capabilities. Use these APIs for complete end-to-end e-invoicing workflows:

### System Integration (SI) Capabilities
- Financial systems integration and data collection
- Business system synchronization and transformation
- Document generation and validation

### Access Point Provider (APP) Capabilities  
- FIRS submission and status tracking
- Taxpayer management and compliance reporting
- Regulatory compliance and analytics

### End-to-End Workflows
- Payment processor → e-invoice → FIRS submission
- ERP system → data transformation → compliance reporting
- Unified monitoring and cross-role analytics

### Authentication
Set your API key in the collection variables or environment:
- Variable: `api_key`
- Header: `X-API-Key`
            """
        }
        
        return role_descriptions.get(role, base_description)
    
    def _create_collection_events(self) -> List[Dict[str, Any]]:
        """Create collection-level events (scripts)."""
        return [
            {
                "listen": "prerequest",
                "script": {
                    "type": "text/javascript",
                    "exec": [
                        "// TaxPoynt API Collection Pre-request Script",
                        "// Automatically set base URL based on environment",
                        "",
                        "const environment = pm.environment.get('environment') || 'production';",
                        "",
                        "if (environment === 'sandbox') {",
                        "    pm.collectionVariables.set('base_url', 'https://sandbox-api.taxpoynt.com');",
                        "} else {",
                        "    pm.collectionVariables.set('base_url', 'https://api.taxpoynt.com');",
                        "}",
                        "",
                        "// Set timestamp for requests",
                        "pm.collectionVariables.set('timestamp', new Date().toISOString());",
                        "",
                        "// Validate API key is set",
                        "const apiKey = pm.collectionVariables.get('api_key') || pm.environment.get('api_key');",
                        "if (!apiKey) {",
                        "    console.warn('⚠️ API key not set. Please set api_key in collection variables or environment.');",
                        "}"
                    ]
                }
            },
            {
                "listen": "test",
                "script": {
                    "type": "text/javascript",
                    "exec": [
                        "// TaxPoynt API Collection Test Script",
                        "// Common tests for all requests",
                        "",
                        "pm.test('Response status is successful', function () {",
                        "    pm.expect(pm.response.code).to.be.oneOf([200, 201, 202]);",
                        "});",
                        "",
                        "pm.test('Response has JSON content-type', function () {",
                        "    pm.expect(pm.response.headers.get('Content-Type')).to.include('application/json');",
                        "});",
                        "",
                        "pm.test('Response time is acceptable', function () {",
                        "    pm.expect(pm.response.responseTime).to.be.below(5000);",
                        "});",
                        "",
                        "// Parse response and set common variables",
                        "if (pm.response.code === 200 || pm.response.code === 201) {",
                        "    try {",
                        "        const response = pm.response.json();",
                        "        ",
                        "        // Set common response variables for chaining requests",
                        "        if (response.data && response.data.id) {",
                        "            pm.collectionVariables.set('last_created_id', response.data.id);",
                        "        }",
                        "        ",
                        "        if (response.submission_id) {",
                        "            pm.collectionVariables.set('last_submission_id', response.submission_id);",
                        "        }",
                        "        ",
                        "        if (response.connection_id) {",
                        "            pm.collectionVariables.set('last_connection_id', response.connection_id);",
                        "        }",
                        "    } catch (e) {",
                        "        console.log('Could not parse response JSON');",
                        "    }",
                        "}"
                    ]
                }
            }
        ]
    
    def _create_collection_variables(self, role: RoleType) -> List[Dict[str, Any]]:
        """Create collection variables."""
        variables = [
            {
                "key": "base_url",
                "value": "https://api.taxpoynt.com",
                "type": "string",
                "description": "Base URL for TaxPoynt API"
            },
            {
                "key": "api_key",
                "value": "your_api_key_here",
                "type": "string",
                "description": "Your TaxPoynt API key"
            },
            {
                "key": "api_version",
                "value": "v1",
                "type": "string",
                "description": "API version"
            },
            {
                "key": "timestamp",
                "value": "{{$timestamp}}",
                "type": "string",
                "description": "Current timestamp"
            }
        ]
        
        # Add role-specific variables
        if role == RoleType.SI:
            variables.extend([
                {
                    "key": "sample_erp_connection_id",
                    "value": "conn_erp_123456",
                    "type": "string",
                    "description": "Sample ERP connection ID for testing"
                },
                {
                    "key": "sample_payment_processor",
                    "value": "paystack",
                    "type": "string",
                    "description": "Sample payment processor for testing"
                },
                {
                    "key": "sample_certificate_id",
                    "value": "cert_123456",
                    "type": "string",
                    "description": "Sample certificate ID for testing"
                }
            ])
        elif role == RoleType.APP:
            variables.extend([
                {
                    "key": "sample_taxpayer_tin",
                    "value": "12345678-001",
                    "type": "string",
                    "description": "Sample taxpayer TIN for testing"
                },
                {
                    "key": "sample_submission_id",
                    "value": "sub_123456",
                    "type": "string",
                    "description": "Sample submission ID for testing"
                },
                {
                    "key": "sample_taxpayer_id",
                    "value": "taxpayer_123456",
                    "type": "string",
                    "description": "Sample taxpayer ID for testing"
                }
            ])
        elif role == RoleType.HYBRID:
            variables.extend([
                {
                    "key": "sample_workflow_id",
                    "value": "workflow_123456",
                    "type": "string",
                    "description": "Sample workflow ID for testing"
                },
                {
                    "key": "sample_erp_connection_id",
                    "value": "conn_erp_123456",
                    "type": "string",
                    "description": "Sample ERP connection ID for testing"
                },
                {
                    "key": "sample_taxpayer_tin",
                    "value": "12345678-001",
                    "type": "string",
                    "description": "Sample taxpayer TIN for testing"
                }
            ])
        
        return variables
    
    def _group_endpoints_by_tag(self, openapi_spec: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Group endpoints by their tags."""
        endpoints_by_tag = {}
        
        for path, path_data in openapi_spec.get("paths", {}).items():
            for method, operation in path_data.items():
                if isinstance(operation, dict) and "tags" in operation:
                    for tag in operation["tags"]:
                        if tag not in endpoints_by_tag:
                            endpoints_by_tag[tag] = []
                        
                        endpoints_by_tag[tag].append({
                            "path": path,
                            "method": method.upper(),
                            "operation": operation
                        })
        
        return endpoints_by_tag
    
    def _create_folder(self, tag: str, endpoints: List[Dict[str, Any]], openapi_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Create Postman folder for a tag group."""
        
        folder = {
            "name": tag,
            "description": self._get_tag_description(tag, openapi_spec),
            "item": []
        }
        
        # Sort endpoints by path and method
        sorted_endpoints = sorted(endpoints, key=lambda x: (x["path"], x["method"]))
        
        for endpoint in sorted_endpoints:
            request = self._create_request(endpoint, openapi_spec)
            folder["item"].append(request)
        
        return folder
    
    def _get_tag_description(self, tag: str, openapi_spec: Dict[str, Any]) -> str:
        """Get description for a tag."""
        tags = openapi_spec.get("tags", [])
        for tag_info in tags:
            if tag_info.get("name") == tag:
                return tag_info.get("description", f"{tag} operations")
        return f"{tag} operations"
    
    def _create_request(self, endpoint: Dict[str, Any], openapi_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Create Postman request from endpoint."""
        
        path = endpoint["path"]
        method = endpoint["method"]
        operation = endpoint["operation"]
        
        request = {
            "name": operation.get("summary", f"{method} {path}"),
            "request": {
                "method": method,
                "header": self._create_request_headers(operation),
                "url": {
                    "raw": "{{base_url}}" + path,
                    "host": ["{{base_url}}"],
                    "path": path.strip("/").split("/"),
                    "query": self._create_query_params(operation)
                },
                "description": operation.get("description", "")
            },
            "response": []
        }
        
        # Add path variables
        path_vars = self._extract_path_variables(path)
        if path_vars:
            request["request"]["url"]["variable"] = path_vars
        
        # Add request body if present
        if "requestBody" in operation:
            request["request"]["body"] = self._create_request_body(operation["requestBody"])
        
        # Add example responses
        if "responses" in operation:
            request["response"] = self._create_example_responses(operation["responses"])
        
        # Add tests specific to this endpoint
        request["event"] = self._create_request_events(operation)
        
        return request
    
    def _create_request_headers(self, operation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create request headers."""
        headers = [
            {
                "key": "Content-Type",
                "value": "application/json",
                "type": "text"
            },
            {
                "key": "Accept",
                "value": "application/json",
                "type": "text"
            }
        ]
        
        # Add operation-specific headers from parameters
        for param in operation.get("parameters", []):
            if param.get("in") == "header":
                headers.append({
                    "key": param["name"],
                    "value": f"{{{{{param['name']}}}}}",
                    "type": "text",
                    "description": param.get("description", "")
                })
        
        return headers
    
    def _create_query_params(self, operation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create query parameters."""
        query_params = []
        
        for param in operation.get("parameters", []):
            if param.get("in") == "query":
                query_params.append({
                    "key": param["name"],
                    "value": self._get_param_example_value(param),
                    "description": param.get("description", ""),
                    "disabled": not param.get("required", False)
                })
        
        return query_params
    
    def _extract_path_variables(self, path: str) -> List[Dict[str, Any]]:
        """Extract path variables from URL."""
        import re
        
        variables = []
        path_params = re.findall(r'\{(\w+)\}', path)
        
        for param in path_params:
            variables.append({
                "key": param,
                "value": f"{{{{sample_{param}}}}}",
                "description": f"Sample {param} value"
            })
        
        return variables
    
    def _create_request_body(self, request_body: Dict[str, Any]) -> Dict[str, Any]:
        """Create request body."""
        content = request_body.get("content", {})
        
        if "application/json" in content:
            schema = content["application/json"].get("schema", {})
            example_data = self._generate_example_from_schema(schema)
            
            return {
                "mode": "raw",
                "raw": json.dumps(example_data, indent=2),
                "options": {
                    "raw": {
                        "language": "json"
                    }
                }
            }
        
        return {"mode": "raw", "raw": ""}
    
    def _generate_example_from_schema(self, schema: Dict[str, Any]) -> Any:
        """Generate example data from OpenAPI schema."""
        if "example" in schema:
            return schema["example"]
        
        schema_type = schema.get("type", "object")
        
        if schema_type == "object":
            example = {}
            properties = schema.get("properties", {})
            required = schema.get("required", [])
            
            for prop_name, prop_schema in properties.items():
                if prop_name in required or len(example) < 3:  # Limit example size
                    example[prop_name] = self._generate_example_from_schema(prop_schema)
            
            return example
        
        elif schema_type == "array":
            items_schema = schema.get("items", {})
            return [self._generate_example_from_schema(items_schema)]
        
        elif schema_type == "string":
            enum_values = schema.get("enum", [])
            if enum_values:
                return enum_values[0]
            return self._get_string_example(schema.get("format", ""))
        
        elif schema_type == "integer":
            return 123
        
        elif schema_type == "number":
            return 123.45
        
        elif schema_type == "boolean":
            return True
        
        return None
    
    def _get_string_example(self, format_type: str) -> str:
        """Get example string value based on format."""
        format_examples = {
            "email": "user@example.com",
            "date": "2024-01-15",
            "date-time": "2024-01-15T10:30:00Z",
            "uri": "https://example.com",
            "uuid": "123e4567-e89b-12d3-a456-426614174000"
        }
        return format_examples.get(format_type, "example_value")
    
    def _get_param_example_value(self, param: Dict[str, Any]) -> str:
        """Get example value for parameter."""
        param_type = param.get("schema", {}).get("type", "string")
        param_name = param["name"]
        
        # Provide contextual examples based on parameter name
        if "date" in param_name.lower():
            return "2024-01-15"
        elif "id" in param_name.lower():
            return "123456"
        elif "limit" in param_name.lower():
            return "10"
        elif "offset" in param_name.lower():
            return "0"
        elif param_type == "boolean":
            return "true"
        elif param_type == "integer":
            return "100"
        
        return "example_value"
    
    def _create_example_responses(self, responses: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create example responses."""
        example_responses = []
        
        for status_code, response_spec in responses.items():
            if status_code.startswith("2"):  # Success responses
                example_response = {
                    "name": f"Success {status_code}",
                    "originalRequest": {
                        "method": "GET",  # This would be filled by actual method
                        "header": [],
                        "url": {"raw": "{{base_url}}/example"}
                    },
                    "status": f"OK {status_code}",
                    "code": int(status_code),
                    "_postman_previewlanguage": "json",
                    "header": [
                        {
                            "key": "Content-Type",
                            "value": "application/json"
                        }
                    ],
                    "cookie": [],
                    "body": json.dumps({
                        "success": True,
                        "data": {"example": "response"},
                        "timestamp": "2024-01-15T10:30:00Z"
                    }, indent=2)
                }
                
                example_responses.append(example_response)
        
        return example_responses
    
    def _create_request_events(self, operation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create request-specific events (tests)."""
        events = []
        
        # Add operation-specific tests
        test_script = [
            f"// Tests for {operation.get('summary', 'API operation')}",
            "",
            "pm.test('Status code is successful', function () {",
            "    pm.response.to.have.status(200);",
            "});",
            "",
            "pm.test('Response has expected structure', function () {",
            "    const response = pm.response.json();",
            "    pm.expect(response).to.have.property('success');",
            "    pm.expect(response).to.have.property('timestamp');",
            "});",
        ]
        
        # Add operation-specific test logic
        operation_id = operation.get("operationId", "")
        if "create" in operation_id.lower() or "register" in operation_id.lower():
            test_script.extend([
                "",
                "// Save created resource ID for subsequent requests",
                "if (pm.response.code === 201) {",
                "    const response = pm.response.json();",
                "    if (response.data && response.data.id) {",
                "        pm.collectionVariables.set('last_created_id', response.data.id);",
                "    }",
                "}"
            ])
        
        events.append({
            "listen": "test",
            "script": {
                "type": "text/javascript",
                "exec": test_script
            }
        })
        
        return events
    
    def _generate_environments(self, role: RoleType, output_path: Path) -> Dict[str, str]:
        """Generate Postman environments for the role."""
        
        environments = {}
        
        # Production environment
        prod_env = PostmanEnvironment(
            name=f"TaxPoynt {role.value.replace('_', ' ').title()} - Production",
            values=[
                {"key": "environment", "value": "production", "enabled": True},
                {"key": "base_url", "value": "https://api.taxpoynt.com", "enabled": True},
                {"key": "api_key", "value": "your_production_api_key", "enabled": True, "type": "secret"},
                {"key": "taxpayer_tin", "value": "12345678-001", "enabled": True},
            ]
        )
        
        # Sandbox environment
        sandbox_env = PostmanEnvironment(
            name=f"TaxPoynt {role.value.replace('_', ' ').title()} - Sandbox",
            values=[
                {"key": "environment", "value": "sandbox", "enabled": True},
                {"key": "base_url", "value": "https://sandbox-api.taxpoynt.com", "enabled": True},
                {"key": "api_key", "value": "your_sandbox_api_key", "enabled": True, "type": "secret"},
                {"key": "taxpayer_tin", "value": "98765432-001", "enabled": True},
            ]
        )
        
        # Add role-specific environment variables
        if role == RoleType.SI:
            si_vars = [
                {"key": "erp_connection_id", "value": "conn_erp_sandbox", "enabled": True},
                {"key": "payment_processor", "value": "paystack", "enabled": True},
                {"key": "certificate_id", "value": "cert_sandbox", "enabled": True},
            ]
            prod_env.values.extend(si_vars)
            sandbox_env.values.extend(si_vars)
            
        elif role == RoleType.APP:
            app_vars = [
                {"key": "submission_id", "value": "sub_sandbox_123", "enabled": True},
                {"key": "taxpayer_id", "value": "taxpayer_sandbox_123", "enabled": True},
                {"key": "webhook_url", "value": "https://your-app.com/webhooks/firs", "enabled": True},
            ]
            prod_env.values.extend(app_vars)
            sandbox_env.values.extend(app_vars)
            
        elif role == RoleType.HYBRID:
            hybrid_vars = [
                {"key": "workflow_id", "value": "workflow_sandbox_123", "enabled": True},
                {"key": "erp_connection_id", "value": "conn_erp_sandbox", "enabled": True},
                {"key": "submission_id", "value": "sub_sandbox_123", "enabled": True},
            ]
            prod_env.values.extend(hybrid_vars)
            sandbox_env.values.extend(hybrid_vars)
        
        # Generate environment files
        for env in [prod_env, sandbox_env]:
            env_data = {
                "id": str(uuid.uuid4()),
                "name": env.name,
                "values": env.values,
                "_postman_variable_scope": "environment",
                "_postman_exported_at": datetime.now().isoformat() + "Z",
                "_postman_exported_using": "TaxPoynt Documentation Generator"
            }
            
            env_filename = f"{env.name.lower().replace(' ', '_').replace('-', '_')}.postman_environment.json"
            env_file = output_path / env_filename
            
            with open(env_file, "w") as f:
                json.dump(env_data, f, indent=2)
            
            environments[env.name] = str(env_file)
        
        return environments
    
    def _generate_collection_documentation(self, role: RoleType, collection: Dict[str, Any], output_path: Path) -> str:
        """Generate documentation for the Postman collection."""
        
        role_display = role.value.replace("_", " ").title()
        
        doc_template = f"""# TaxPoynt {role_display} API - Postman Collection

## Overview

This Postman collection provides comprehensive API testing capabilities for TaxPoynt {role_display} role users.

## Collection Information

- **Name**: {collection["info"]["name"]}
- **Total Requests**: {len(self._count_requests(collection))}
- **Authentication**: API Key (X-API-Key header)
- **Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Setup Instructions

### 1. Import Collection

1. Open Postman
2. Click "Import" button
3. Select the collection file: `{collection["info"]["name"].lower().replace(" ", "_")}.postman_collection.json`

### 2. Import Environment

Choose the appropriate environment:

- **Production**: `taxpoynt_{role.value}_production.postman_environment.json`
- **Sandbox**: `taxpoynt_{role.value}_sandbox.postman_environment.json`

### 3. Configure API Key

Set your API key in the environment variables:

1. Select the imported environment
2. Set the `api_key` variable value
3. Save the environment

## Collection Structure

The collection is organized into folders based on API functionality:

{self._generate_folder_documentation(collection)}

## Environment Variables

### Required Variables

- `api_key`: Your TaxPoynt API key
- `base_url`: API base URL (automatically set based on environment)
- `environment`: Current environment (production/sandbox)

### Auto-Generated Variables

The collection automatically generates variables for request chaining:

- `last_created_id`: ID of last created resource
- `last_submission_id`: ID of last submission (APP role)
- `last_connection_id`: ID of last connection (SI role)
- `timestamp`: Current timestamp

## Usage Examples

### Getting Started

1. Start with authentication-related requests
2. Use the generated variables for subsequent requests
3. Check the "Tests" tab for automated validations

### Request Chaining

Many requests automatically save response data for use in subsequent requests. For example:

1. Create a connection → saves `last_connection_id`
2. Use the connection → references `{{{{last_connection_id}}}}`

## Authentication

All requests use API Key authentication:

```
Header: X-API-Key
Value: {{{{api_key}}}}
```

## Error Handling

The collection includes comprehensive error handling tests:

- Status code validation
- Response structure validation
- Performance checks (< 5 seconds)

## Support

For support with this Postman collection:

- Email: info@taxpoynt.com
- Documentation: https://docs.taxpoynt.com/{role.value}
- Collection Issues: Check the console tab for detailed error messages

## Version Information

- Collection Schema: v2.1.0
- API Version: v1
- Generated by: TaxPoynt Documentation Generator
"""
        
        doc_file = output_path / f"README_postman_{role.value}.md"
        with open(doc_file, "w") as f:
            f.write(doc_template)
        
        return str(doc_file)
    
    def _generate_folder_documentation(self, collection: Dict[str, Any]) -> str:
        """Generate documentation for collection folders."""
        folders_doc = ""
        
        for item in collection.get("item", []):
            if "item" in item:  # It's a folder
                folder_name = item["name"]
                request_count = len(item["item"])
                folders_doc += f"\n### {folder_name}\n"
                folders_doc += f"- **Requests**: {request_count}\n"
                folders_doc += f"- **Description**: {item.get('description', 'API operations for ' + folder_name)}\n"
        
        return folders_doc
    
    def _count_requests(self, collection: Dict[str, Any]) -> int:
        """Count total requests in collection."""
        count = 0
        for item in collection.get("item", []):
            if "item" in item:  # It's a folder
                count += len(item["item"])
            else:  # It's a request
                count += 1
        return count


def generate_all_postman_collections(output_dir: str) -> Dict[str, Any]:
    """Generate Postman collections for all roles."""
    
    generator = PostmanCollectionGenerator()
    results = {}
    
    roles = [RoleType.SI, RoleType.APP, RoleType.HYBRID]
    
    for role in roles:
        try:
            result = generator.generate_collection(role, output_dir, include_environments=True)
            results[role.value] = result
        except Exception as e:
            results[role.value] = {
                "status": "error",
                "error": str(e)
            }
    
    return {
        "status": "success",
        "generated_collections": results,
        "total_collections": len(roles),
        "output_directory": output_dir
    }


# Export main functionality
__all__ = [
    "PostmanCollectionGenerator",
    "PostmanEnvironment",
    "RoleType",
    "generate_all_postman_collections"
]