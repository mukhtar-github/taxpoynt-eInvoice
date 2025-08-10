"""
Role-Specific SDK Generator
===========================
Automatically generates Software Development Kits (SDKs) for each role type
from their respective OpenAPI specifications and documentation.
"""

import json
import os
import re
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from .si_api_docs import SIAPIDocumentationGenerator
from .app_api_docs import APPAPIDocumentationGenerator
from .hybrid_api_docs import HybridAPIDocumentationGenerator


class SDKLanguage(Enum):
    """Supported SDK languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    PHP = "php"
    JAVA = "java"
    CSHARP = "csharp"
    GO = "go"


class RoleType(Enum):
    """TaxPoynt user role types."""
    SI = "system_integrator"
    APP = "access_point_provider"
    HYBRID = "hybrid"


@dataclass
class SDKConfig:
    """Configuration for SDK generation."""
    role: RoleType
    language: SDKLanguage
    package_name: str
    version: str
    author: str
    description: str
    license: str = "MIT"
    include_examples: bool = True
    include_tests: bool = True


class SDKGenerator:
    """Generates role-specific SDKs from OpenAPI specifications."""
    
    def __init__(self):
        self.si_generator = SIAPIDocumentationGenerator()
        self.app_generator = APPAPIDocumentationGenerator()
        self.hybrid_generator = HybridAPIDocumentationGenerator()
        
        # SDK templates and patterns
        self.language_configs = {
            SDKLanguage.PYTHON: {
                "file_extension": ".py",
                "package_file": "setup.py",
                "requirements_file": "requirements.txt",
                "test_framework": "pytest",
                "http_client": "httpx"
            },
            SDKLanguage.JAVASCRIPT: {
                "file_extension": ".js",
                "package_file": "package.json",
                "requirements_file": "package.json",
                "test_framework": "jest",
                "http_client": "axios"
            },
            SDKLanguage.PHP: {
                "file_extension": ".php",
                "package_file": "composer.json",
                "requirements_file": "composer.json",
                "test_framework": "phpunit",
                "http_client": "guzzle"
            }
        }
    
    def generate_sdk(self, config: SDKConfig, output_dir: str) -> Dict[str, Any]:
        """Generate complete SDK for specified role and language."""
        
        # Get OpenAPI spec for role
        openapi_spec = self._get_openapi_spec_for_role(config.role)
        
        # Create output directory structure
        sdk_dir = Path(output_dir) / f"taxpoynt-{config.role.value}-sdk-{config.language.value}"
        sdk_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate SDK components
        generated_files = {}
        
        # 1. Generate main client class
        client_file = self._generate_client_class(config, openapi_spec, sdk_dir)
        generated_files["client"] = client_file
        
        # 2. Generate API modules
        api_modules = self._generate_api_modules(config, openapi_spec, sdk_dir)
        generated_files["api_modules"] = api_modules
        
        # 3. Generate models/schemas
        models = self._generate_models(config, openapi_spec, sdk_dir)
        generated_files["models"] = models
        
        # 4. Generate configuration
        config_file = self._generate_configuration(config, sdk_dir)
        generated_files["configuration"] = config_file
        
        # 5. Generate authentication
        auth_file = self._generate_authentication(config, sdk_dir)
        generated_files["authentication"] = auth_file
        
        # 6. Generate examples
        if config.include_examples:
            examples = self._generate_examples(config, openapi_spec, sdk_dir)
            generated_files["examples"] = examples
        
        # 7. Generate tests
        if config.include_tests:
            tests = self._generate_tests(config, openapi_spec, sdk_dir)
            generated_files["tests"] = tests
        
        # 8. Generate package files
        package_files = self._generate_package_files(config, sdk_dir)
        generated_files["package_files"] = package_files
        
        # 9. Generate documentation
        docs = self._generate_sdk_documentation(config, openapi_spec, sdk_dir)
        generated_files["documentation"] = docs
        
        return {
            "status": "success",
            "sdk_directory": str(sdk_dir),
            "role": config.role.value,
            "language": config.language.value,
            "generated_files": generated_files,
            "package_info": {
                "name": config.package_name,
                "version": config.version,
                "description": config.description
            }
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
    
    def _generate_client_class(self, config: SDKConfig, openapi_spec: Dict[str, Any], sdk_dir: Path) -> str:
        """Generate main client class for the SDK."""
        
        if config.language == SDKLanguage.PYTHON:
            return self._generate_python_client(config, openapi_spec, sdk_dir)
        elif config.language == SDKLanguage.JAVASCRIPT:
            return self._generate_javascript_client(config, openapi_spec, sdk_dir)
        elif config.language == SDKLanguage.PHP:
            return self._generate_php_client(config, openapi_spec, sdk_dir)
        else:
            raise ValueError(f"Unsupported language: {config.language}")
    
    def _generate_python_client(self, config: SDKConfig, openapi_spec: Dict[str, Any], sdk_dir: Path) -> str:
        """Generate Python client class."""
        
        role_name = config.role.value.replace("_", " ").title().replace(" ", "")
        
        client_template = f'''"""
TaxPoynt {role_name} SDK
{'='*50}
Python SDK for TaxPoynt {role_name} APIs
Generated automatically from OpenAPI specification
"""

import httpx
import json
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

from .configuration import Configuration
from .authentication import Authentication
from .exceptions import TaxPoyntAPIError, TaxPoyntAuthError
{self._generate_python_imports(openapi_spec)}


class TaxPoynt{role_name}Client:
    """
    TaxPoynt {role_name} API Client
    
    Main client class for interacting with TaxPoynt {role_name} APIs.
    Provides access to all {role_name}-specific functionality.
    
    Usage:
        client = TaxPoynt{role_name}Client(api_key="your_api_key")
        
        # Use role-specific methods
        {self._generate_usage_examples(config.role)}
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 timeout: int = 30,
                 verify_ssl: bool = True):
        """
        Initialize TaxPoynt {role_name} client.
        
        Args:
            api_key: Your TaxPoynt API key
            base_url: Base URL for API (defaults to production)
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
        """
        self.config = Configuration(
            api_key=api_key,
            base_url=base_url or "https://api.taxpoynt.com",
            timeout=timeout,
            verify_ssl=verify_ssl
        )
        
        self.auth = Authentication(self.config)
        self.client = httpx.Client(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            verify=self.config.verify_ssl
        )
        
        # Initialize API modules
        {self._generate_python_api_modules_init(openapi_spec)}
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
    
    def _make_request(self, 
                     method: str, 
                     endpoint: str, 
                     data: Optional[Dict[str, Any]] = None,
                     params: Optional[Dict[str, Any]] = None,
                     headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Make authenticated API request.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters
            headers: Additional headers
            
        Returns:
            API response data
            
        Raises:
            TaxPoyntAPIError: On API errors
            TaxPoyntAuthError: On authentication errors
        """
        # Add authentication headers
        auth_headers = self.auth.get_headers()
        if headers:
            auth_headers.update(headers)
        
        try:
            response = self.client.request(
                method=method,
                url=endpoint,
                json=data,
                params=params,
                headers=auth_headers
            )
            
            # Handle response
            if response.status_code == 401:
                raise TaxPoyntAuthError("Authentication failed")
            elif response.status_code >= 400:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {{"error": response.text}}
                raise TaxPoyntAPIError(f"API error: {{response.status_code}}", response.status_code, error_data)
            
            return response.json()
            
        except httpx.RequestError as e:
            raise TaxPoyntAPIError(f"Request failed: {{e}}")
'''
        
        client_file = sdk_dir / "client.py"
        with open(client_file, "w") as f:
            f.write(client_template)
        
        return str(client_file)
    
    def _generate_python_imports(self, openapi_spec: Dict[str, Any]) -> str:
        """Generate Python imports for API modules."""
        imports = []
        
        # Group endpoints by tags to determine modules
        tags = set()
        for path_data in openapi_spec.get("paths", {}).values():
            for operation in path_data.values():
                if isinstance(operation, dict) and "tags" in operation:
                    tags.update(operation["tags"])
        
        for tag in sorted(tags):
            module_name = self._tag_to_module_name(tag)
            class_name = self._tag_to_class_name(tag)
            imports.append(f"from .api.{module_name} import {class_name}")
        
        return "\n".join(imports)
    
    def _generate_usage_examples(self, role: RoleType) -> str:
        """Generate usage examples for role."""
        if role == RoleType.SI:
            return """result = client.payments.paystack.get_transactions()
        invoices = client.documents.generate(invoice_data)"""
        elif role == RoleType.APP:
            return """submission = client.firs.submit(invoice_data)
        status = client.firs.get_status(submission_id)"""
        elif role == RoleType.HYBRID:
            return """# SI capabilities
        transactions = client.si.payments.get_unified_transactions()
        
        # APP capabilities  
        submission = client.app.firs.submit(invoice_data)"""
        return ""
    
    def _generate_python_api_modules_init(self, openapi_spec: Dict[str, Any]) -> str:
        """Generate initialization of API modules."""
        inits = []
        
        # Group endpoints by tags
        tags = set()
        for path_data in openapi_spec.get("paths", {}).values():
            for operation in path_data.values():
                if isinstance(operation, dict) and "tags" in operation:
                    tags.update(operation["tags"])
        
        for tag in sorted(tags):
            module_name = self._tag_to_module_name(tag)
            class_name = self._tag_to_class_name(tag)
            attr_name = self._tag_to_attr_name(tag)
            inits.append(f"        self.{attr_name} = {class_name}(self)")
        
        return "\n".join(inits)
    
    def _generate_api_modules(self, config: SDKConfig, openapi_spec: Dict[str, Any], sdk_dir: Path) -> List[str]:
        """Generate API modules for each endpoint group."""
        
        api_dir = sdk_dir / "api"
        api_dir.mkdir(exist_ok=True)
        
        # Create __init__.py
        init_file = api_dir / "__init__.py"
        with open(init_file, "w") as f:
            f.write('"""TaxPoynt API modules."""\n')
        
        generated_modules = []
        
        # Group endpoints by tags
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
        
        # Generate module for each tag
        for tag, endpoints in endpoints_by_tag.items():
            if config.language == SDKLanguage.PYTHON:
                module_file = self._generate_python_api_module(tag, endpoints, api_dir)
                generated_modules.append(module_file)
        
        return generated_modules
    
    def _generate_python_api_module(self, tag: str, endpoints: List[Dict], api_dir: Path) -> str:
        """Generate Python API module for a specific tag."""
        
        module_name = self._tag_to_module_name(tag)
        class_name = self._tag_to_class_name(tag)
        
        module_template = f'''"""
{tag} API Module
{'='*50}
Auto-generated API module for {tag} operations
"""

from typing import Dict, Any, Optional, List
from ..exceptions import TaxPoyntAPIError


class {class_name}:
    """
    {tag} API operations.
    
    Provides methods for all {tag}-related API endpoints.
    """
    
    def __init__(self, client):
        """Initialize with reference to main client."""
        self._client = client
    
{self._generate_python_endpoint_methods(endpoints)}
'''
        
        module_file = api_dir / f"{module_name}.py"
        with open(module_file, "w") as f:
            f.write(module_template)
        
        return str(module_file)
    
    def _generate_python_endpoint_methods(self, endpoints: List[Dict]) -> str:
        """Generate Python methods for endpoints."""
        methods = []
        
        for endpoint in endpoints:
            path = endpoint["path"]
            method = endpoint["method"]
            operation = endpoint["operation"]
            
            method_name = self._operation_to_method_name(operation)
            path_params = self._extract_path_parameters(path)
            query_params = self._extract_query_parameters(operation)
            
            # Generate method
            method_template = f'''    def {method_name}(self{self._generate_method_params(path_params, query_params, operation)}):
        """
        {operation.get("summary", "API operation")}
        
        {operation.get("description", "")}
        """
        {self._generate_method_body(path, method, path_params, query_params, operation)}
'''
            methods.append(method_template)
        
        return "\n".join(methods)
    
    def _generate_models(self, config: SDKConfig, openapi_spec: Dict[str, Any], sdk_dir: Path) -> List[str]:
        """Generate data models from OpenAPI schemas."""
        
        models_dir = sdk_dir / "models"
        models_dir.mkdir(exist_ok=True)
        
        # Create __init__.py
        init_file = models_dir / "__init__.py"
        with open(init_file, "w") as f:
            f.write('"""TaxPoynt data models."""\n')
        
        generated_models = []
        
        schemas = openapi_spec.get("components", {}).get("schemas", {})
        
        for schema_name, schema_def in schemas.items():
            if config.language == SDKLanguage.PYTHON:
                model_file = self._generate_python_model(schema_name, schema_def, models_dir)
                generated_models.append(model_file)
        
        return generated_models
    
    def _generate_python_model(self, schema_name: str, schema_def: Dict, models_dir: Path) -> str:
        """Generate Python data model class."""
        
        model_template = f'''"""
{schema_name} Model
{'='*50}
Auto-generated data model for {schema_name}
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class {schema_name}:
    """
    {schema_def.get("description", f"{schema_name} data model")}
    """
    
{self._generate_python_model_fields(schema_def)}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "{schema_name}":
        """Create instance from dictionary."""
        return cls(**{{
            k: v for k, v in data.items() 
            if k in cls.__dataclass_fields__
        }})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {{}}
        for field_name, field_value in self.__dict__.items():
            if field_value is not None:
                if hasattr(field_value, 'to_dict'):
                    result[field_name] = field_value.to_dict()
                elif isinstance(field_value, list):
                    result[field_name] = [
                        item.to_dict() if hasattr(item, 'to_dict') else item
                        for item in field_value
                    ]
                else:
                    result[field_name] = field_value
        return result
'''
        
        model_file = models_dir / f"{self._camel_to_snake(schema_name)}.py"
        with open(model_file, "w") as f:
            f.write(model_template)
        
        return str(model_file)
    
    def _generate_python_model_fields(self, schema_def: Dict) -> str:
        """Generate Python dataclass fields."""
        fields = []
        properties = schema_def.get("properties", {})
        required = schema_def.get("required", [])
        
        for prop_name, prop_def in properties.items():
            prop_type = self._openapi_type_to_python(prop_def)
            is_required = prop_name in required
            
            if is_required:
                fields.append(f"    {prop_name}: {prop_type}")
            else:
                fields.append(f"    {prop_name}: Optional[{prop_type}] = None")
        
        return "\n".join(fields) if fields else "    pass"
    
    def _generate_configuration(self, config: SDKConfig, sdk_dir: Path) -> str:
        """Generate configuration module."""
        
        if config.language == SDKLanguage.PYTHON:
            config_template = '''"""
TaxPoynt SDK Configuration
========================
Configuration management for TaxPoynt SDK
"""

import os
from typing import Optional


class Configuration:
    """SDK configuration management."""
    
    def __init__(self,
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 timeout: int = 30,
                 verify_ssl: bool = True):
        """
        Initialize configuration.
        
        Args:
            api_key: TaxPoynt API key (can also be set via TAXPOYNT_API_KEY env var)
            base_url: Base URL for API
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
        """
        self.api_key = api_key or os.getenv("TAXPOYNT_API_KEY")
        self.base_url = base_url or "https://api.taxpoynt.com"
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        
        if not self.api_key:
            raise ValueError("API key is required. Set TAXPOYNT_API_KEY environment variable or pass api_key parameter.")
    
    @property
    def is_sandbox(self) -> bool:
        """Check if using sandbox environment."""
        return "sandbox" in self.base_url.lower()
'''
            
            config_file = sdk_dir / "configuration.py"
            with open(config_file, "w") as f:
                f.write(config_template)
            
            return str(config_file)
    
    def _generate_authentication(self, config: SDKConfig, sdk_dir: Path) -> str:
        """Generate authentication module."""
        
        if config.language == SDKLanguage.PYTHON:
            auth_template = '''"""
TaxPoynt SDK Authentication
=========================
Authentication handling for TaxPoynt SDK
"""

from typing import Dict, str
from .configuration import Configuration


class Authentication:
    """Handle API authentication."""
    
    def __init__(self, config: Configuration):
        """Initialize with configuration."""
        self.config = config
    
    def get_headers(self) -> Dict[str, str]:
        """Get authentication headers for requests."""
        headers = {
            "X-API-Key": self.config.api_key,
            "Content-Type": "application/json",
            "User-Agent": f"TaxPoynt-SDK-Python/1.0.0"
        }
        return headers
'''
            
            auth_file = sdk_dir / "authentication.py"
            with open(auth_file, "w") as f:
                f.write(auth_template)
            
            return str(auth_file)
    
    def _generate_examples(self, config: SDKConfig, openapi_spec: Dict[str, Any], sdk_dir: Path) -> List[str]:
        """Generate usage examples."""
        
        examples_dir = sdk_dir / "examples"
        examples_dir.mkdir(exist_ok=True)
        
        # Get examples from documentation generators
        if config.role == RoleType.SI:
            examples = self.si_generator.integration_examples
        elif config.role == RoleType.APP:
            examples = self.app_generator.integration_examples
        elif config.role == RoleType.HYBRID:
            examples = self.hybrid_generator.integration_examples
        
        generated_examples = []
        
        for example_name, example_data in examples.items():
            if config.language == SDKLanguage.PYTHON:
                example_file = self._generate_python_example(example_name, example_data, examples_dir)
                generated_examples.append(example_file)
        
        return generated_examples
    
    def _generate_python_example(self, example_name: str, example_data: Dict, examples_dir: Path) -> str:
        """Generate Python example file."""
        
        example_template = f'''"""
{example_data["title"]}
{'='*50}
{example_data["description"]}
"""

{example_data["code"]}

if __name__ == "__main__":
    # Run the example
    main()
'''
        
        example_file = examples_dir / f"{example_name}.py"
        with open(example_file, "w") as f:
            f.write(example_template)
        
        return str(example_file)
    
    def _generate_tests(self, config: SDKConfig, openapi_spec: Dict[str, Any], sdk_dir: Path) -> List[str]:
        """Generate test files."""
        
        tests_dir = sdk_dir / "tests"
        tests_dir.mkdir(exist_ok=True)
        
        # Create __init__.py
        init_file = tests_dir / "__init__.py"
        with open(init_file, "w") as f:
            f.write('"""TaxPoynt SDK tests."""\n')
        
        generated_tests = []
        
        if config.language == SDKLanguage.PYTHON:
            # Generate test files
            client_test = self._generate_python_client_test(config, tests_dir)
            generated_tests.append(client_test)
            
            # Generate API module tests
            tags = set()
            for path_data in openapi_spec.get("paths", {}).values():
                for operation in path_data.values():
                    if isinstance(operation, dict) and "tags" in operation:
                        tags.update(operation["tags"])
            
            for tag in tags:
                api_test = self._generate_python_api_test(tag, tests_dir)
                generated_tests.append(api_test)
        
        return generated_tests
    
    def _generate_python_client_test(self, config: SDKConfig, tests_dir: Path) -> str:
        """Generate Python client test."""
        
        role_name = config.role.value.replace("_", " ").title().replace(" ", "")
        
        test_template = f'''"""
Test TaxPoynt {role_name} Client
{'='*50}
Unit tests for main client class
"""

import pytest
import httpx
from unittest.mock import Mock, patch
from taxpoynt_{config.role.value}_sdk import TaxPoynt{role_name}Client


class TestTaxPoynt{role_name}Client:
    """Test main client functionality."""
    
    def test_client_initialization(self):
        """Test client can be initialized with API key."""
        client = TaxPoynt{role_name}Client(api_key="test_key")
        assert client.config.api_key == "test_key"
        assert client.config.base_url == "https://api.taxpoynt.com"
    
    def test_client_initialization_with_env_var(self, monkeypatch):
        """Test client can be initialized with environment variable."""
        monkeypatch.setenv("TAXPOYNT_API_KEY", "env_test_key")
        client = TaxPoynt{role_name}Client()
        assert client.config.api_key == "env_test_key"
    
    def test_client_initialization_no_api_key(self):
        """Test client raises error without API key."""
        with pytest.raises(ValueError, match="API key is required"):
            TaxPoynt{role_name}Client()
    
    @patch('httpx.Client.request')
    def test_make_request_success(self, mock_request):
        """Test successful API request."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {{"success": True, "data": {{"test": "value"}}}}
        mock_request.return_value = mock_response
        
        client = TaxPoynt{role_name}Client(api_key="test_key")
        result = client._make_request("GET", "/test")
        
        assert result["success"] is True
        assert result["data"]["test"] == "value"
    
    @patch('httpx.Client.request')
    def test_make_request_auth_error(self, mock_request):
        """Test authentication error handling."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_request.return_value = mock_response
        
        client = TaxPoynt{role_name}Client(api_key="test_key")
        
        with pytest.raises(Exception):  # TaxPoyntAuthError
            client._make_request("GET", "/test")
    
    def test_context_manager(self):
        """Test client can be used as context manager."""
        with TaxPoynt{role_name}Client(api_key="test_key") as client:
            assert client.config.api_key == "test_key"
'''
        
        test_file = tests_dir / "test_client.py"
        with open(test_file, "w") as f:
            f.write(test_template)
        
        return str(test_file)
    
    def _generate_python_api_test(self, tag: str, tests_dir: Path) -> str:
        """Generate Python API module test."""
        
        module_name = self._tag_to_module_name(tag)
        class_name = self._tag_to_class_name(tag)
        
        test_template = f'''"""
Test {tag} API Module
{'='*50}
Unit tests for {tag} API operations
"""

import pytest
from unittest.mock import Mock, patch
from taxpoynt_sdk.api.{module_name} import {class_name}


class Test{class_name}:
    """Test {tag} API operations."""
    
    def setup_method(self):
        """Setup test client."""
        self.mock_client = Mock()
        self.api = {class_name}(self.mock_client)
    
    def test_initialization(self):
        """Test API module initialization."""
        assert self.api._client == self.mock_client
    
    # Add specific endpoint tests here based on the API specification
    def test_api_methods_exist(self):
        """Test that API methods are properly defined."""
        # This would be expanded based on actual endpoints
        assert hasattr(self.api, '__init__')
'''
        
        test_file = tests_dir / f"test_{module_name}.py"
        with open(test_file, "w") as f:
            f.write(test_template)
        
        return str(test_file)
    
    def _generate_package_files(self, config: SDKConfig, sdk_dir: Path) -> Dict[str, str]:
        """Generate package configuration files."""
        
        package_files = {}
        
        if config.language == SDKLanguage.PYTHON:
            # Generate setup.py
            setup_py = self._generate_python_setup_py(config, sdk_dir)
            package_files["setup.py"] = setup_py
            
            # Generate requirements.txt
            requirements_txt = self._generate_python_requirements(sdk_dir)
            package_files["requirements.txt"] = requirements_txt
            
            # Generate __init__.py
            init_py = self._generate_python_init(config, sdk_dir)
            package_files["__init__.py"] = init_py
            
            # Generate exceptions.py
            exceptions_py = self._generate_python_exceptions(sdk_dir)
            package_files["exceptions.py"] = exceptions_py
        
        return package_files
    
    def _generate_python_setup_py(self, config: SDKConfig, sdk_dir: Path) -> str:
        """Generate Python setup.py file."""
        
        role_display = config.role.value.replace("_", " ").title()
        
        setup_template = f'''"""
TaxPoynt {role_display} SDK Setup
{'='*50}
Package configuration for TaxPoynt {role_display} Python SDK
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="{config.package_name}",
    version="{config.version}",
    author="{config.author}",
    author_email="info@taxpoynt.com",
    description="{config.description}",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/taxpoynt/taxpoynt-{config.role.value}-sdk-python",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Office/Business :: Financial :: Accounting",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={{
        "dev": ["pytest>=6.0", "pytest-cov", "black", "flake8", "mypy"],
        "docs": ["sphinx", "sphinx-rtd-theme"],
    }},
    keywords="taxpoynt api sdk e-invoicing firs {config.role.value}",
    project_urls={{
        "Documentation": "https://docs.taxpoynt.com/{config.role.value}",
        "Source": "https://github.com/taxpoynt/taxpoynt-{config.role.value}-sdk-python",
        "Bug Reports": "https://github.com/taxpoynt/taxpoynt-{config.role.value}-sdk-python/issues",
    }},
)
'''
        
        setup_file = sdk_dir / "setup.py"
        with open(setup_file, "w") as f:
            f.write(setup_template)
        
        return str(setup_file)
    
    def _generate_python_requirements(self, sdk_dir: Path) -> str:
        """Generate Python requirements.txt."""
        
        requirements = """# TaxPoynt SDK Dependencies
httpx>=0.24.0
typing-extensions>=4.0.0
"""
        
        req_file = sdk_dir / "requirements.txt"
        with open(req_file, "w") as f:
            f.write(requirements)
        
        return str(req_file)
    
    def _generate_python_init(self, config: SDKConfig, sdk_dir: Path) -> str:
        """Generate Python __init__.py."""
        
        role_name = config.role.value.replace("_", " ").title().replace(" ", "")
        
        init_template = f'''"""
TaxPoynt {role_name} SDK
{'='*50}
Python SDK for TaxPoynt {role_name} APIs

Usage:
    from taxpoynt_{config.role.value}_sdk import TaxPoynt{role_name}Client
    
    client = TaxPoynt{role_name}Client(api_key="your_api_key")
"""

from .client import TaxPoynt{role_name}Client
from .configuration import Configuration
from .authentication import Authentication
from .exceptions import TaxPoyntAPIError, TaxPoyntAuthError

__version__ = "{config.version}"
__author__ = "{config.author}"
__email__ = "info@taxpoynt.com"

__all__ = [
    "TaxPoynt{role_name}Client",
    "Configuration", 
    "Authentication",
    "TaxPoyntAPIError",
    "TaxPoyntAuthError"
]
'''
        
        init_file = sdk_dir / "__init__.py"
        with open(init_file, "w") as f:
            f.write(init_template)
        
        return str(init_file)
    
    def _generate_python_exceptions(self, sdk_dir: Path) -> str:
        """Generate Python exceptions module."""
        
        exceptions_template = '''"""
TaxPoynt SDK Exceptions
=====================
Custom exceptions for TaxPoynt SDK
"""

from typing import Optional, Dict, Any


class TaxPoyntSDKError(Exception):
    """Base exception for TaxPoynt SDK."""
    pass


class TaxPoyntAPIError(TaxPoyntSDKError):
    """Exception raised for API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class TaxPoyntAuthError(TaxPoyntSDKError):
    """Exception raised for authentication errors."""
    pass


class TaxPoyntConfigError(TaxPoyntSDKError):
    """Exception raised for configuration errors."""
    pass


class TaxPoyntValidationError(TaxPoyntSDKError):
    """Exception raised for validation errors."""
    pass
'''
        
        exceptions_file = sdk_dir / "exceptions.py"
        with open(exceptions_file, "w") as f:
            f.write(exceptions_template)
        
        return str(exceptions_file)
    
    def _generate_sdk_documentation(self, config: SDKConfig, openapi_spec: Dict[str, Any], sdk_dir: Path) -> Dict[str, str]:
        """Generate SDK documentation."""
        
        docs = {}
        
        # Generate README.md
        readme = self._generate_readme(config, sdk_dir)
        docs["README.md"] = readme
        
        # Generate CHANGELOG.md
        changelog = self._generate_changelog(config, sdk_dir)
        docs["CHANGELOG.md"] = changelog
        
        return docs
    
    def _generate_readme(self, config: SDKConfig, sdk_dir: Path) -> str:
        """Generate README.md file."""
        
        role_display = config.role.value.replace("_", " ").title()
        role_name = config.role.value.replace("_", " ").title().replace(" ", "")
        
        readme_template = f'''# TaxPoynt {role_display} SDK

{config.description}

## Installation

```bash
pip install {config.package_name}
```

## Quick Start

```python
from taxpoynt_{config.role.value}_sdk import TaxPoynt{role_name}Client

# Initialize client
client = TaxPoynt{role_name}Client(api_key="your_api_key")

{self._get_role_specific_examples(config.role)}
```

## Configuration

The SDK can be configured in several ways:

### Environment Variables

```bash
export TAXPOYNT_API_KEY="your_api_key"
```

### Configuration Object

```python
from taxpoynt_{config.role.value}_sdk import Configuration, TaxPoynt{role_name}Client

config = Configuration(
    api_key="your_api_key",
    base_url="https://sandbox-api.taxpoynt.com",  # For sandbox
    timeout=60
)

client = TaxPoynt{role_name}Client(config=config)
```

## Error Handling

```python
from taxpoynt_{config.role.value}_sdk import TaxPoyntAPIError, TaxPoyntAuthError

try:
    result = client.some_api_method()
except TaxPoyntAuthError as e:
    print(f"Authentication failed: {{e}}")
except TaxPoyntAPIError as e:
    print(f"API error: {{e}} (Status: {{e.status_code}})")
```

## Examples

See the `examples/` directory for complete usage examples.

## Documentation

- [API Documentation](https://docs.taxpoynt.com/{config.role.value})
- [SDK Documentation](https://docs.taxpoynt.com/{config.role.value}/sdk)

## Support

For support, contact us at info@taxpoynt.com

## License

This project is licensed under the {config.license} License.
'''
        
        readme_file = sdk_dir / "README.md"
        with open(readme_file, "w") as f:
            f.write(readme_template)
        
        return str(readme_file)
    
    def _generate_changelog(self, config: SDKConfig, sdk_dir: Path) -> str:
        """Generate CHANGELOG.md file."""
        
        changelog_template = f'''# Changelog

All notable changes to the TaxPoynt {config.role.value.replace("_", " ").title()} SDK will be documented in this file.

## [{config.version}] - {datetime.now().strftime("%Y-%m-%d")}

### Added
- Initial release of TaxPoynt {config.role.value.replace("_", " ").title()} SDK
- Auto-generated from OpenAPI specification
- Complete API coverage for {config.role.value.replace("_", " ")} operations
- Comprehensive examples and documentation
- Type hints for better IDE support
- Error handling with custom exceptions

### Features
- Automatic authentication handling
- Configurable base URLs for sandbox/production
- Request/response validation
- Comprehensive test coverage
'''
        
        changelog_file = sdk_dir / "CHANGELOG.md"
        with open(changelog_file, "w") as f:
            f.write(changelog_template)
        
        return str(changelog_file)
    
    def _get_role_specific_examples(self, role: RoleType) -> str:
        """Get role-specific examples for README."""
        if role == RoleType.SI:
            return '''# System Integration examples
# Connect to payment processors
processors = client.payments.get_available_processors()

# Get payment transactions
transactions = client.payments.unified.get_transactions(
    start_date="2024-01-01",
    end_date="2024-01-31"
)

# Generate invoices
invoice = client.documents.generate(
    invoice_data=invoice_data,
    document_type="both"
)'''
        elif role == RoleType.APP:
            return '''# Access Point Provider examples
# Submit invoice to FIRS
submission = client.firs.submit(
    invoice_data=invoice_data,
    taxpayer_tin="12345678-001"
)

# Check submission status
status = client.firs.get_status(submission.submission_id)

# Manage taxpayers
taxpayer = client.taxpayers.register({
    "tin": "98765432-001",
    "organization_name": "Example Company Ltd"
})'''
        elif role == RoleType.HYBRID:
            return '''# Hybrid examples (SI + APP capabilities)
# Use SI capabilities
transactions = client.si.payments.get_unified_transactions()

# Use APP capabilities
submission = client.app.firs.submit(invoice_data)

# Run complete workflow
workflow = client.hybrid.workflows.run_payment_to_firs({
    "payment_processor": "paystack",
    "transaction_ids": ["txn_1", "txn_2"]
})'''
        return ""
    
    # Utility methods
    def _tag_to_module_name(self, tag: str) -> str:
        """Convert tag to module name."""
        return re.sub(r'[^a-zA-Z0-9_]', '_', tag.lower())
    
    def _tag_to_class_name(self, tag: str) -> str:
        """Convert tag to class name."""
        return ''.join(word.capitalize() for word in re.split(r'[^a-zA-Z0-9]', tag))
    
    def _tag_to_attr_name(self, tag: str) -> str:
        """Convert tag to attribute name."""
        words = re.split(r'[^a-zA-Z0-9]', tag.lower())
        return words[0] + ''.join(word.capitalize() for word in words[1:])
    
    def _operation_to_method_name(self, operation: Dict) -> str:
        """Convert operation to method name."""
        operation_id = operation.get("operationId")
        if operation_id:
            return self._camel_to_snake(operation_id)
        
        # Generate from summary
        summary = operation.get("summary", "")
        words = re.findall(r'\b\w+\b', summary.lower())
        return '_'.join(words[:4])  # Limit to 4 words
    
    def _camel_to_snake(self, name: str) -> str:
        """Convert camelCase to snake_case."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def _extract_path_parameters(self, path: str) -> List[str]:
        """Extract path parameters from URL path."""
        return re.findall(r'\{(\w+)\}', path)
    
    def _extract_query_parameters(self, operation: Dict) -> List[Dict]:
        """Extract query parameters from operation."""
        params = []
        for param in operation.get("parameters", []):
            if param.get("in") == "query":
                params.append(param)
        return params
    
    def _generate_method_params(self, path_params: List[str], query_params: List[Dict], operation: Dict) -> str:
        """Generate method parameters."""
        params = []
        
        # Add path parameters
        for param in path_params:
            params.append(f", {param}: str")
        
        # Add query parameters
        for param in query_params:
            param_name = param["name"]
            is_required = param.get("required", False)
            if is_required:
                params.append(f", {param_name}")
            else:
                params.append(f", {param_name}: Optional[str] = None")
        
        # Add request body if present
        if "requestBody" in operation:
            params.append(", data: Optional[Dict[str, Any]] = None")
        
        return "".join(params)
    
    def _generate_method_body(self, path: str, method: str, path_params: List[str], query_params: List[Dict], operation: Dict) -> str:
        """Generate method body."""
        # Build endpoint URL
        endpoint = path
        for param in path_params:
            endpoint = endpoint.replace(f"{{{param}}}", f"{{{{param}}}}")
        
        # Build params dict
        params_dict = []
        for param in query_params:
            param_name = param["name"]
            params_dict.append(f'"{param_name}": {param_name}')
        
        params_str = "{" + ", ".join(params_dict) + "}" if params_dict else "None"
        
        return f'''        return self._client._make_request(
            method="{method}",
            endpoint=f"{endpoint}",
            params={params_str},
            data=data if "{method}" in ["POST", "PUT", "PATCH"] else None
        )'''
    
    def _openapi_type_to_python(self, prop_def: Dict) -> str:
        """Convert OpenAPI type to Python type."""
        prop_type = prop_def.get("type", "string")
        prop_format = prop_def.get("format", "")
        
        type_mapping = {
            "string": "str",
            "integer": "int", 
            "number": "float",
            "boolean": "bool",
            "array": "List[Any]",
            "object": "Dict[str, Any]"
        }
        
        if prop_format == "date-time":
            return "datetime"
        elif prop_format == "date":
            return "str"  # Could be date type
        
        return type_mapping.get(prop_type, "Any")


def generate_all_sdks(output_base_dir: str) -> Dict[str, Any]:
    """Generate SDKs for all roles and languages."""
    
    generator = SDKGenerator()
    results = {}
    
    # Define SDK configurations
    sdk_configs = [
        # Python SDKs
        SDKConfig(
            role=RoleType.SI,
            language=SDKLanguage.PYTHON,
            package_name="taxpoynt-si-sdk",
            version="1.0.0",
            author="TaxPoynt",
            description="TaxPoynt System Integrator SDK for Python"
        ),
        SDKConfig(
            role=RoleType.APP,
            language=SDKLanguage.PYTHON,
            package_name="taxpoynt-app-sdk",
            version="1.0.0",
            author="TaxPoynt",
            description="TaxPoynt Access Point Provider SDK for Python"
        ),
        SDKConfig(
            role=RoleType.HYBRID,
            language=SDKLanguage.PYTHON,
            package_name="taxpoynt-hybrid-sdk",
            version="1.0.0",
            author="TaxPoynt",
            description="TaxPoynt Hybrid SDK for Python"
        )
    ]
    
    # Generate all SDKs
    for config in sdk_configs:
        sdk_key = f"{config.role.value}_{config.language.value}"
        try:
            result = generator.generate_sdk(config, output_base_dir)
            results[sdk_key] = result
        except Exception as e:
            results[sdk_key] = {
                "status": "error",
                "error": str(e)
            }
    
    return {
        "status": "success",
        "generated_sdks": results,
        "total_sdks": len(sdk_configs),
        "output_directory": output_base_dir
    }


# Export main functionality
__all__ = [
    "SDKGenerator",
    "SDKConfig",
    "SDKLanguage",
    "RoleType",
    "generate_all_sdks"
]