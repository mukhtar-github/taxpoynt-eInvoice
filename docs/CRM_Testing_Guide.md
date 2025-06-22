# TaxPoynt CRM Integration - Testing Guide

## Overview

This guide provides comprehensive instructions for testing the TaxPoynt CRM integration components, including unit tests, integration tests, and validation procedures.

## Test Structure

### Test Organization

```
backend/tests/
├── integrations/
│   ├── test_crm_service.py          # Unit tests for CRM service layer
│   ├── test_hubspot_connector.py    # HubSpot connector tests (existing)
│   └── test_auth.py                 # Authentication tests (existing)
├── integration/
│   ├── test_crm_integration.py      # End-to-end integration tests
│   ├── test_firs_integration.py     # FIRS integration tests (existing)
│   └── test_odoo_connection_integration.py  # Odoo tests (existing)
├── tasks/
│   └── test_hubspot_tasks.py        # Background task tests (existing)
└── test_crm_structure_validation.py # Test validation and structure verification
```

## Test Categories

### 1. Unit Tests (`test_crm_service.py`)

**Coverage**: Core CRM functionality without external dependencies

**Test Classes**:
- `TestCRMConnectionService` - CRM connection model and operations
- `TestCRMDataValidation` - Data validation and sanitization
- `TestCRMServiceOperations` - Service layer operations and logic
- `TestCRMSecurityAndValidation` - Security features and data protection

**Key Test Areas**:
- CRM connection creation and management
- Deal data validation and transformation
- Pagination and filtering logic
- Error handling patterns
- Security features (credential masking, rate limiting)
- Data sanitization and validation

### 2. Integration Tests (`test_crm_integration.py`)

**Coverage**: Full workflow integration from API to database

**Test Classes**:
- `TestCRMIntegrationEndpoints` - API endpoint testing
- `TestCRMDatabaseIntegration` - Database operations and CRUD
- `TestCRMAsyncOperations` - Asynchronous operation testing
- `TestCRMErrorScenarios` - Error handling and recovery

**Key Test Areas**:
- API endpoint functionality
- Database operations and transactions
- Asynchronous processing workflows
- Error scenarios and recovery mechanisms
- Authentication and authorization flows
- Webhook processing

### 3. Existing Tests (Maintained)

**HubSpot Connector Tests** (`test_hubspot_connector.py`):
- OAuth authentication flows
- Deal retrieval and processing
- Webhook event handling
- Data transformation logic

**HubSpot Tasks Tests** (`test_hubspot_tasks.py`):
- Background task execution
- Deal synchronization workflows
- Batch processing operations
- Task scheduling and management

## Running Tests

### Prerequisites

1. **Environment Setup**:
   ```bash
   cd /home/mukhtar-tanimu/taxpoynt-eInvoice/backend
   source venv/bin/activate
   ```

2. **Environment Variables**:
   ```bash
   export ENVIRONMENT=test
   export DATABASE_URL=sqlite:///test.db
   export REDIS_URL=redis://localhost:6379/1
   ```

### Test Execution Commands

#### Run All CRM Tests
```bash
# Run all CRM-related tests
pytest tests/integrations/crm/ tests/integration/test_crm_integration.py tests/tasks/test_hubspot_tasks.py -v

# Run with coverage
pytest tests/integrations/crm/ tests/integration/test_crm_integration.py tests/tasks/test_hubspot_tasks.py --cov=app.integrations.crm --cov-report=html
```

#### Run Specific Test Categories

**Unit Tests Only**:
```bash
pytest tests/integrations/test_crm_service.py -v
```

**Integration Tests Only**:
```bash
pytest tests/integration/test_crm_integration.py -v
```

**HubSpot Specific Tests**:
```bash
pytest tests/integrations/test_hubspot_connector.py tests/tasks/test_hubspot_tasks.py -v
```

#### Run Structure Validation
```bash
# Validate test structure and completeness
python tests/test_crm_structure_validation.py

# Or with pytest
pytest tests/test_crm_structure_validation.py -v
```

### Test Configuration

#### Pytest Configuration

Create or update `pytest.ini`:
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --disable-warnings
    --tb=short
markers =
    unit: Unit tests
    integration: Integration tests
    asyncio: Asynchronous tests
    slow: Slow running tests
    crm: CRM-related tests
    hubspot: HubSpot-specific tests
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
```

#### Test Environment Variables

Create `.env.test`:
```bash
# Test Environment Configuration
ENVIRONMENT=test
DEBUG=True

# Database
DATABASE_URL=sqlite:///test_taxpoynt.db
TEST_DATABASE_URL=sqlite:///test_taxpoynt.db

# Redis
REDIS_URL=redis://localhost:6379/1

# JWT
SECRET_KEY=test_secret_key_for_testing_only
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CRM Test Configuration
HUBSPOT_TEST_CLIENT_ID=test_client_id
HUBSPOT_TEST_CLIENT_SECRET=test_client_secret
HUBSPOT_TEST_PORTAL_ID=12345

# Mock API URLs
HUBSPOT_API_BASE_URL=https://api.hubapi.com
MOCK_CRM_RESPONSES=true

# Logging
LOG_LEVEL=INFO
ENABLE_AUDIT_LOGGING=true
```

## Test Data Management

### Test Fixtures

#### Database Fixtures
```python
@pytest.fixture
def test_db_session():
    """Create test database session."""
    # Implementation for test database setup
    pass

@pytest.fixture
def test_organization():
    """Create test organization."""
    return Organization(
        id=str(uuid4()),
        name="Test Organization",
        email="test@example.com"
    )

@pytest.fixture
def test_crm_connection(test_organization):
    """Create test CRM connection."""
    return CRMConnection(
        id=str(uuid4()),
        organization_id=test_organization.id,
        crm_type="hubspot",
        connection_name="Test HubSpot",
        status="connected"
    )
```

#### Mock Data Fixtures
```python
@pytest.fixture
def mock_hubspot_deal():
    """Mock HubSpot deal data."""
    return {
        "id": "123456789",
        "properties": {
            "dealname": "Test Deal",
            "amount": "50000",
            "dealstage": "closedwon",
            "closedate": "1703030400000"
        }
    }

@pytest.fixture
def mock_customer_data():
    """Mock customer data."""
    return {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+2341234567890",
        "company": "Acme Corporation"
    }
```

### Test Data Cleanup

```python
@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Automatically cleanup test data after each test."""
    yield
    # Cleanup logic here
    pass
```

## Mocking Strategies

### External API Mocking

#### HubSpot API Mocking
```python
@patch('httpx.AsyncClient')
async def test_hubspot_api_call(mock_client):
    """Mock HubSpot API responses."""
    mock_response = Mock()
    mock_response.json.return_value = {"results": []}
    mock_response.raise_for_status = Mock()
    
    mock_client_instance = AsyncMock()
    mock_client_instance.get = AsyncMock(return_value=mock_response)
    mock_client.return_value.__aenter__.return_value = mock_client_instance
    
    # Test implementation
```

#### Database Mocking
```python
@patch('app.db.session.SessionLocal')
def test_database_operation(mock_session):
    """Mock database operations."""
    mock_db = Mock()
    mock_session.return_value = mock_db
    
    # Configure mock behavior
    mock_db.query.return_value.filter.return_value.first.return_value = mock_connection
    
    # Test implementation
```

### Authentication Mocking
```python
@patch('app.dependencies.auth.get_current_user')
def test_authenticated_endpoint(mock_auth):
    """Mock authentication for API tests."""
    mock_user = User(id="test_user_id", email="test@example.com")
    mock_auth.return_value = mock_user
    
    # Test implementation
```

## Performance Testing

### Load Testing for CRM Operations

```python
@pytest.mark.slow
async def test_concurrent_deal_processing():
    """Test concurrent deal processing performance."""
    import asyncio
    
    async def process_deal(deal_id):
        # Simulate deal processing
        await asyncio.sleep(0.1)
        return {"deal_id": deal_id, "status": "processed"}
    
    # Test concurrent processing
    deal_ids = [f"deal-{i}" for i in range(100)]
    start_time = time.time()
    
    results = await asyncio.gather(*[process_deal(deal_id) for deal_id in deal_ids])
    
    end_time = time.time()
    duration = end_time - start_time
    
    assert len(results) == 100
    assert duration < 5.0  # Should complete within 5 seconds
```

### Memory Usage Testing
```python
import psutil
import os

def test_memory_usage_during_sync():
    """Test memory usage during large sync operations."""
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    # Simulate large data processing
    large_dataset = [{"id": i, "data": "x" * 1000} for i in range(10000)]
    
    # Process data
    processed = []
    for item in large_dataset:
        processed.append({"id": item["id"], "processed": True})
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    # Memory increase should be reasonable (less than 100MB)
    assert memory_increase < 100 * 1024 * 1024
```

## Test Reporting

### Coverage Reports

```bash
# Generate HTML coverage report
pytest tests/integrations/test_crm_service.py tests/integration/test_crm_integration.py \
    --cov=app.integrations.crm \
    --cov=app.models.crm_connection \
    --cov=app.routes.crm_integrations \
    --cov=app.tasks.crm_tasks \
    --cov-report=html \
    --cov-report=term-missing

# View coverage report
open htmlcov/index.html
```

### Test Results Export

```bash
# Generate JUnit XML report
pytest tests/integrations/test_crm_service.py tests/integration/test_crm_integration.py \
    --junitxml=test_results.xml

# Generate JSON report
pytest tests/integrations/test_crm_service.py tests/integration/test_crm_integration.py \
    --json-report --json-report-file=test_results.json
```

## Continuous Integration

### GitHub Actions Workflow

Create `.github/workflows/crm_tests.yml`:
```yaml
name: CRM Integration Tests

on:
  push:
    paths:
      - 'backend/app/integrations/crm/**'
      - 'backend/tests/integrations/test_crm_service.py'
      - 'backend/tests/integration/test_crm_integration.py'
  pull_request:
    paths:
      - 'backend/app/integrations/crm/**'
      - 'backend/tests/**'

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      redis:
        image: redis:6
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
    
    - name: Run CRM tests
      run: |
        cd backend
        pytest tests/integrations/test_crm_service.py tests/integration/test_crm_integration.py -v --cov=app.integrations.crm
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
```

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# If you get import errors, ensure the Python path is set correctly
export PYTHONPATH="${PYTHONPATH}:/home/mukhtar-tanimu/taxpoynt-eInvoice/backend"
```

#### Database Connection Issues
```bash
# Reset test database
rm test_taxpoynt.db
alembic upgrade head
```

#### Mock Issues
```python
# If mocks aren't working as expected, verify patch targets
# Patch where the function is used, not where it's defined
@patch('app.integrations.crm.hubspot.connector.httpx.AsyncClient')  # Correct
# NOT @patch('httpx.AsyncClient')  # May not work in all cases
```

### Debugging Tests

#### Verbose Output
```bash
pytest tests/integrations/test_crm_service.py -v -s --tb=long
```

#### Debug Specific Test
```bash
pytest tests/integrations/test_crm_service.py::TestCRMConnectionService::test_crm_connection_creation -v -s
```

#### Use pytest debugger
```python
import pytest

def test_debug_example():
    # Add this line to start debugger
    pytest.set_trace()
    
    # Your test code here
    assert True
```

## Test Maintenance

### Regular Tasks

1. **Update test data** when API responses change
2. **Review mock configurations** for accuracy
3. **Update performance benchmarks** as the system grows
4. **Verify test coverage** remains above 85%
5. **Update documentation** when test structure changes

### Test Review Checklist

- [ ] All test functions have descriptive names
- [ ] Tests are independent and can run in any order
- [ ] Mocks are properly configured and realistic
- [ ] Error scenarios are adequately tested
- [ ] Performance tests cover critical operations
- [ ] Security tests validate data protection
- [ ] Documentation is up to date

## Conclusion

This testing guide provides comprehensive coverage for the TaxPoynt CRM integration components. Following these guidelines ensures robust, maintainable, and reliable tests that validate both functionality and performance of the CRM integration system.

For questions or issues with testing, refer to the main project documentation or contact the development team.