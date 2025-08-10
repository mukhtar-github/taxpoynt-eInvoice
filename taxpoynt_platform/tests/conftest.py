"""
Shared Pytest Configuration
===========================

Common fixtures, configuration, and utilities for all TaxPoynt platform tests.
Provides consistent testing environment across all test types.
"""

import pytest
import asyncio
import os
from typing import Dict, Any, Generator
from datetime import datetime, timedelta
from decimal import Decimal

# Test environment configuration
TEST_ENV = os.getenv('TEST_ENV', 'testing')
FIRS_SANDBOX_MODE = os.getenv('FIRS_SANDBOX_MODE', 'true').lower() == 'true'

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_config() -> Dict[str, Any]:
    """Base test configuration"""
    return {
        'environment': TEST_ENV,
        'firs_sandbox_mode': FIRS_SANDBOX_MODE,
        'test_timeout': 30,
        'api_base_url': os.getenv('TEST_API_BASE_URL', 'http://localhost:8000'),
        'database_url': os.getenv('TEST_DATABASE_URL', 'sqlite:///test.db'),
        'redis_url': os.getenv('TEST_REDIS_URL', 'redis://localhost:6379/1'),
        'log_level': 'DEBUG'
    }

@pytest.fixture
def firs_test_config() -> Dict[str, Any]:
    """FIRS-specific test configuration"""
    return {
        'firs_base_url': os.getenv('FIRS_TEST_BASE_URL', 'https://sandbox.firs.gov.ng'),
        'firs_api_key': os.getenv('FIRS_TEST_API_KEY', 'test_api_key'),
        'firs_client_id': os.getenv('FIRS_TEST_CLIENT_ID', 'test_client_id'),
        'firs_client_secret': os.getenv('FIRS_TEST_CLIENT_SECRET', 'test_secret'),
        'enable_firs_integration': FIRS_SANDBOX_MODE,
        'firs_timeout': 30,
        'max_retries': 3
    }

@pytest.fixture
def sample_invoice_data() -> Dict[str, Any]:
    """Sample invoice data for testing"""
    return {
        'invoice_number': f'INV-{datetime.now().strftime("%Y%m%d")}-001',
        'invoice_date': datetime.now().isoformat(),
        'due_date': (datetime.now() + timedelta(days=30)).isoformat(),
        'supplier': {
            'name': 'TaxPoynt Test Supplier Ltd',
            'tin': '12345678-0001',
            'address': 'Victoria Island, Lagos, Nigeria',
            'phone': '+234-1-234-5678',
            'email': 'supplier@taxpoynt.com'
        },
        'customer': {
            'name': 'Test Customer Nigeria Ltd',
            'tin': '87654321-0001', 
            'address': 'Lekki Phase 1, Lagos, Nigeria',
            'phone': '+234-1-876-5432',
            'email': 'customer@testcompany.ng'
        },
        'line_items': [
            {
                'description': 'Professional Consulting Services',
                'quantity': 1,
                'unit_price': Decimal('500000.00'),
                'amount': Decimal('500000.00'),
                'vat_rate': Decimal('0.075'),
                'vat_amount': Decimal('37500.00')
            },
            {
                'description': 'Software License (Annual)',
                'quantity': 1,
                'unit_price': Decimal('200000.00'),
                'amount': Decimal('200000.00'),
                'vat_rate': Decimal('0.075'),
                'vat_amount': Decimal('15000.00')
            }
        ],
        'currency': 'NGN',
        'subtotal': Decimal('700000.00'),
        'vat_total': Decimal('52500.00'),
        'total_amount': Decimal('752500.00')
    }

@pytest.fixture
def sample_transaction_data() -> Dict[str, Any]:
    """Sample transaction data for classification testing"""
    return {
        'transaction_id': f'TXN-{int(datetime.now().timestamp())}',
        'amount': Decimal('150000.00'),
        'currency': 'NGN',
        'narration': 'Payment for professional consulting services - Lagos office',
        'transaction_date': datetime.now(),
        'time': datetime.now().strftime('%H:%M'),
        'sender_name': 'Adebayo Consulting Ltd',
        'receiver_name': 'TaxPoynt Nigeria Ltd',
        'bank': 'GTBank',
        'account_number': '0123456789'
    }

@pytest.fixture
def mock_user_context() -> Dict[str, Any]:
    """Mock user context for testing"""
    return {
        'user_id': 'test_user_123',
        'organization_id': 'test_org_456',
        'subscription_tier': 'PROFESSIONAL',
        'business_context': {
            'industry': 'Technology',
            'business_size': 'medium',
            'annual_revenue': Decimal('50000000'),
            'employee_count': 25,
            'years_in_operation': 5,
            'state': 'Lagos',
            'business_type': 'limited_liability'
        }
    }

@pytest.fixture
def firs_endpoints() -> Dict[str, str]:
    """FIRS API endpoints for testing"""
    base_url = 'https://taxpoynt-einvoice-production.up.railway.app'
    return {
        'health_check': f'{base_url}/api/v1/health/ready',
        'firs_health': f'{base_url}/api/v1/firs-certification/health-check',
        'firs_config': f'{base_url}/api/v1/firs-certification/configuration',
        'transmission_submit': f'{base_url}/api/v1/firs-certification/transmission/submit',
        'transmission_status': f'{base_url}/api/v1/firs-certification/transmission/status',
        'reporting_generate': f'{base_url}/api/v1/firs-certification/reporting/generate',
        'reporting_dashboard': f'{base_url}/api/v1/firs-certification/reporting/dashboard',
        'invoice_update': f'{base_url}/api/v1/firs-certification/update/invoice'
    }

# Test markers for categorizing tests
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "uat: mark test as a user acceptance test"
    )
    config.addinivalue_line(
        "markers", "firs: mark test as FIRS-related"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "external: mark test as requiring external services"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file paths"""
    for item in items:
        # Add markers based on directory structure
        if "unit/" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration/" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "uat/" in str(item.fspath):
            item.add_marker(pytest.mark.uat)
        
        # Add FIRS marker for FIRS-related tests
        if "firs" in str(item.fspath).lower() or "firs" in item.name.lower():
            item.add_marker(pytest.mark.firs)
        
        # Add external marker for tests requiring external services
        if any(keyword in str(item.fspath).lower() for keyword in ['integration', 'uat', 'firs']):
            item.add_marker(pytest.mark.external)