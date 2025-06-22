"""
Standalone test validation for CRM components structure.
This test validates the test files themselves without importing the main app.
"""

import os
import ast
import pytest
from pathlib import Path


class TestCRMTestStructure:
    """Validate the structure and completeness of CRM tests."""
    
    def test_crm_test_files_exist(self):
        """Test that all required CRM test files exist."""
        backend_path = Path(__file__).parent.parent
        required_test_files = [
            "tests/integrations/test_crm_service.py",
            "tests/integration/test_crm_integration.py",
            "tests/integrations/test_hubspot_connector.py",
            "tests/tasks/test_hubspot_tasks.py"
        ]
        
        for test_file in required_test_files:
            test_path = backend_path / test_file
            assert test_path.exists(), f"Required test file {test_file} does not exist"
            assert test_path.is_file(), f"{test_file} is not a file"
    
    def test_crm_test_file_syntax(self):
        """Test that CRM test files have valid Python syntax."""
        backend_path = Path(__file__).parent.parent
        test_files = [
            "tests/integrations/test_crm_service.py",
            "tests/integration/test_crm_integration.py"
        ]
        
        for test_file in test_files:
            test_path = backend_path / test_file
            if test_path.exists():
                with open(test_path, 'r') as f:
                    content = f.read()
                
                # Validate Python syntax
                try:
                    ast.parse(content)
                except SyntaxError as e:
                    pytest.fail(f"Syntax error in {test_file}: {e}")
    
    def test_crm_service_test_structure(self):
        """Test that CRM service test file has expected structure."""
        backend_path = Path(__file__).parent.parent
        test_file = backend_path / "tests/integrations/test_crm_service.py"
        
        if not test_file.exists():
            pytest.skip("CRM service test file not found")
        
        with open(test_file, 'r') as f:
            content = f.read()
        
        # Parse the file
        tree = ast.parse(content)
        
        # Find all class definitions
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        class_names = [cls.name for cls in classes]
        
        # Verify expected test classes exist
        expected_classes = [
            "TestCRMConnectionService",
            "TestCRMDataValidation", 
            "TestCRMServiceOperations",
            "TestCRMSecurityAndValidation"
        ]
        
        for expected_class in expected_classes:
            assert expected_class in class_names, f"Expected test class {expected_class} not found"
        
        # Find all function definitions
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        test_functions = [func.name for func in functions if func.name.startswith('test_')]
        
        # Verify we have sufficient test coverage
        assert len(test_functions) >= 15, f"Expected at least 15 test functions, found {len(test_functions)}"
    
    def test_crm_integration_test_structure(self):
        """Test that CRM integration test file has expected structure."""
        backend_path = Path(__file__).parent.parent
        test_file = backend_path / "tests/integration/test_crm_integration.py"
        
        if not test_file.exists():
            pytest.skip("CRM integration test file not found")
        
        with open(test_file, 'r') as f:
            content = f.read()
        
        # Parse the file
        tree = ast.parse(content)
        
        # Find all class definitions
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        class_names = [cls.name for cls in classes]
        
        # Verify expected test classes exist
        expected_classes = [
            "TestCRMIntegrationEndpoints",
            "TestCRMDatabaseIntegration",
            "TestCRMAsyncOperations",
            "TestCRMErrorScenarios"
        ]
        
        for expected_class in expected_classes:
            assert expected_class in class_names, f"Expected test class {expected_class} not found"
    
    def test_test_documentation_exists(self):
        """Test that test documentation exists."""
        backend_path = Path(__file__).parent.parent.parent
        docs_path = backend_path / "docs"
        
        expected_docs = [
            "CRM_API_Documentation.md",
            "CRM_Data_Models.md"
        ]
        
        for doc_file in expected_docs:
            doc_path = docs_path / doc_file
            assert doc_path.exists(), f"Required documentation {doc_file} does not exist"
    
    def test_pytest_imports_structure(self):
        """Test that test files have proper pytest structure."""
        backend_path = Path(__file__).parent.parent
        test_files = [
            "tests/integrations/test_crm_service.py",
            "tests/integration/test_crm_integration.py"
        ]
        
        for test_file in test_files:
            test_path = backend_path / test_file
            if test_path.exists():
                with open(test_path, 'r') as f:
                    content = f.read()
                
                # Check for pytest import
                assert "import pytest" in content, f"{test_file} should import pytest"
                
                # Check for async test markers
                if "async def test_" in content:
                    assert "@pytest.mark.asyncio" in content, f"{test_file} should use @pytest.mark.asyncio for async tests"
    
    def test_mock_usage_patterns(self):
        """Test that mock patterns are used correctly."""
        backend_path = Path(__file__).parent.parent
        test_files = [
            "tests/integrations/test_crm_service.py",
            "tests/integration/test_crm_integration.py"
        ]
        
        for test_file in test_files:
            test_path = backend_path / test_file
            if test_path.exists():
                with open(test_path, 'r') as f:
                    content = f.read()
                
                # Check for proper mock imports
                if "Mock" in content or "AsyncMock" in content:
                    assert "from unittest.mock import" in content, f"{test_file} should import mocks from unittest.mock"
    
    def test_test_coverage_completeness(self):
        """Test that we have comprehensive test coverage."""
        backend_path = Path(__file__).parent.parent
        
        # Count total test functions across CRM test files
        test_files = [
            "tests/integrations/test_crm_service.py",
            "tests/integration/test_crm_integration.py"
        ]
        
        total_test_functions = 0
        
        for test_file in test_files:
            test_path = backend_path / test_file
            if test_path.exists():
                with open(test_path, 'r') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
                test_functions = [func.name for func in functions if func.name.startswith('test_')]
                total_test_functions += len(test_functions)
        
        # We should have substantial test coverage
        assert total_test_functions >= 25, f"Expected at least 25 total test functions across CRM tests, found {total_test_functions}"
    
    def test_test_naming_conventions(self):
        """Test that test functions follow naming conventions."""
        backend_path = Path(__file__).parent.parent
        test_files = [
            "tests/integrations/test_crm_service.py",
            "tests/integration/test_crm_integration.py"
        ]
        
        for test_file in test_files:
            test_path = backend_path / test_file
            if test_path.exists():
                with open(test_path, 'r') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
                test_functions = [func.name for func in functions if func.name.startswith('test_')]
                
                # Verify test function naming
                for func_name in test_functions:
                    assert func_name.startswith('test_'), f"Test function {func_name} should start with 'test_'"
                    assert len(func_name) > 5, f"Test function {func_name} should have descriptive name"
                    assert '_' in func_name, f"Test function {func_name} should use snake_case"


class TestCRMDocumentationStructure:
    """Validate CRM documentation structure."""
    
    def test_api_documentation_structure(self):
        """Test that API documentation has proper structure."""
        backend_path = Path(__file__).parent.parent.parent
        doc_path = backend_path / "docs/CRM_API_Documentation.md"
        
        if not doc_path.exists():
            pytest.skip("CRM API documentation not found")
        
        with open(doc_path, 'r') as f:
            content = f.read()
        
        # Check for required sections
        required_sections = [
            "# TaxPoynt CRM Integration API Documentation",
            "## Overview",
            "## Data Models",
            "## CRM Connection Endpoints",
            "## Deal Management Endpoints",
            "## Webhook Endpoints",
            "## Error Handling",
            "## Examples"
        ]
        
        for section in required_sections:
            assert section in content, f"Required section '{section}' not found in API documentation"
    
    def test_data_models_documentation_structure(self):
        """Test that data models documentation has proper structure."""
        backend_path = Path(__file__).parent.parent.parent
        doc_path = backend_path / "docs/CRM_Data_Models.md"
        
        if not doc_path.exists():
            pytest.skip("CRM data models documentation not found")
        
        with open(doc_path, 'r') as f:
            content = f.read()
        
        # Check for required sections
        required_sections = [
            "# TaxPoynt CRM Integration - Data Models Documentation",
            "## Core Models",
            "### CRMConnection Model",
            "### CRMDeal Model", 
            "## Database Schema",
            "## API Schema Models",
            "## Validation Rules",
            "## Data Transformations",
            "## Security Considerations"
        ]
        
        for section in required_sections:
            assert section in content, f"Required section '{section}' not found in data models documentation"
    
    def test_documentation_code_examples(self):
        """Test that documentation includes code examples."""
        backend_path = Path(__file__).parent.parent.parent
        doc_path = backend_path / "docs/CRM_API_Documentation.md"
        
        if not doc_path.exists():
            pytest.skip("CRM API documentation not found")
        
        with open(doc_path, 'r') as f:
            content = f.read()
        
        # Check for code examples
        assert "```bash" in content, "API documentation should include bash examples"
        assert "```json" in content, "API documentation should include JSON examples"
        assert "```python" in content, "API documentation should include Python examples"
        assert "curl -X" in content, "API documentation should include curl examples"


class TestCRMImplementationCompleteness:
    """Test that CRM implementation is complete."""
    
    def test_crm_files_structure(self):
        """Test that CRM implementation files exist."""
        backend_path = Path(__file__).parent.parent
        
        # Check for CRM implementation files
        crm_files = [
            "app/integrations/crm/__init__.py",
            "app/integrations/crm/hubspot/__init__.py",
            "app/integrations/crm/hubspot/connector.py",
            "app/integrations/crm/hubspot/models.py",
            "app/integrations/crm/hubspot/router.py",
            "app/integrations/crm/hubspot/webhooks.py",
            "app/models/crm_connection.py",
            "app/routes/crm_integrations.py",
            "app/tasks/crm_tasks.py",
            "app/tasks/hubspot_tasks.py"
        ]
        
        for crm_file in crm_files:
            file_path = backend_path / crm_file
            assert file_path.exists(), f"Required CRM file {crm_file} does not exist"
    
    def test_frontend_crm_files_structure(self):
        """Test that frontend CRM files exist."""
        frontend_path = Path(__file__).parent.parent.parent / "frontend"
        
        # Check for frontend CRM files
        frontend_files = [
            "types/crm.ts",
            "services/crmService.ts",
            "components/integrations/crm/HubSpotConnector.tsx",
            "components/integrations/crm/HubSpotDealsManager.tsx",
            "components/integrations/crm/DealToInvoiceConverter.tsx",
            "pages/dashboard/crm/index.tsx",
            "pages/dashboard/crm/add.tsx",
            "pages/dashboard/crm/[id].tsx"
        ]
        
        for frontend_file in frontend_files:
            file_path = frontend_path / frontend_file
            assert file_path.exists(), f"Required frontend CRM file {frontend_file} does not exist"


# Run syntax validation directly if this file is executed
if __name__ == "__main__":
    test_instance = TestCRMTestStructure()
    
    try:
        test_instance.test_crm_test_files_exist()
        print("✅ All CRM test files exist")
        
        test_instance.test_crm_test_file_syntax()
        print("✅ All CRM test files have valid syntax")
        
        test_instance.test_crm_service_test_structure()
        print("✅ CRM service test structure is valid")
        
        test_instance.test_crm_integration_test_structure()
        print("✅ CRM integration test structure is valid")
        
        test_instance.test_test_coverage_completeness()
        print("✅ Test coverage is comprehensive")
        
        doc_instance = TestCRMDocumentationStructure()
        doc_instance.test_api_documentation_structure()
        print("✅ API documentation structure is complete")
        
        doc_instance.test_data_models_documentation_structure()
        print("✅ Data models documentation structure is complete")
        
        impl_instance = TestCRMImplementationCompleteness()
        impl_instance.test_crm_files_structure()
        print("✅ Backend CRM implementation files exist")
        
        impl_instance.test_frontend_crm_files_structure()
        print("✅ Frontend CRM implementation files exist")
        
        print("\n🎉 All CRM test and documentation validation passed!")
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        exit(1)