import pytest # type: ignore
from fastapi.testclient import TestClient # type: ignore
from unittest.mock import patch, MagicMock
from datetime import datetime
from uuid import UUID, uuid4

from app.main import app
from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.models.organization import Organization
from app.models.integration import Integration
from app.models.irn import IRNRecord


# Setup test client
client = TestClient(app)


# Mock dependencies
@pytest.fixture
def mock_db():
    """Create a mock database session"""
    db = MagicMock()
    return db


@pytest.fixture
def mock_current_user():
    """Create a mock current user"""
    return User(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        organization_id=uuid4(),
        role="admin",
        is_active=True
    )


@pytest.fixture
def mock_integration():
    """Create a mock integration"""
    return Integration(
        id=uuid4(),
        organization_id=uuid4(),
        name="Test Integration",
        integration_type="odoo",
        config={"url": "https://test.odoo.com"}
    )


# Override dependencies for testing
def override_get_db():
    """Override database dependency for testing"""
    db = MagicMock()
    try:
        yield db
    finally:
        pass


def override_get_current_active_user():
    """Override current user dependency for testing"""
    return User(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        organization_id=uuid4(),
        role="admin",
        is_active=True
    )


# Apply overrides
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_active_user] = override_get_current_active_user


class TestIRNEndpoints:
    """Test suite for IRN API endpoints"""
    
    def test_generate_irn(self, mock_db, mock_current_user, mock_integration):
        """Test generate IRN endpoint"""
        # Setup
        integration_id = uuid4()
        mock_organization = Organization(
            id=mock_current_user.organization_id,
            firs_service_id="94ND90NR"
        )
        mock_integration.id = integration_id
        mock_integration.organization_id = mock_current_user.organization_id
        
        # Create test request data
        request_data = {
            "integration_id": str(integration_id),
            "invoice_number": "INV001"
        }
        
        # Mock database operations
        with patch('app.crud.integration.get_integration_by_id', return_value=mock_integration):
            with patch('app.crud.organization.get_organization_by_id', return_value=mock_organization):
                with patch('app.crud.irn.create_irn') as mock_create_irn:
                    # Setup mock return value for create_irn
                    mock_irn = IRNRecord(
                        irn="INV001-94ND90NR-20240611",
                        integration_id=str(integration_id),
                        invoice_number="INV001",
                        service_id="94ND90NR",
                        timestamp="20240611",
                        status="unused",
                        generated_at=datetime.now(),
                        valid_until=datetime.now(),
                    )
                    mock_create_irn.return_value = mock_irn
                    
                    # Call API
                    response = client.post("/api/v1/irn/generate", json=request_data)
                    
                    # Assertions
                    assert response.status_code == 201
                    assert response.json()["irn"] == "INV001-94ND90NR-20240611"
                    assert response.json()["status"] == "unused"
                    mock_create_irn.assert_called_once()
    
    def test_generate_irn_invalid_integration(self, mock_db, mock_current_user):
        """Test generate IRN endpoint with invalid integration"""
        # Setup
        integration_id = uuid4()
        
        # Create test request data
        request_data = {
            "integration_id": str(integration_id),
            "invoice_number": "INV001"
        }
        
        # Mock database operations - integration not found
        with patch('app.crud.integration.get_integration_by_id', return_value=None):
            # Call API
            response = client.post("/api/v1/irn/generate", json=request_data)
            
            # Assertions
            assert response.status_code == 404
            assert "Integration not found" in response.json()["detail"]
    
    def test_generate_batch_irn(self, mock_db, mock_current_user, mock_integration):
        """Test batch generate IRN endpoint"""
        # Setup
        integration_id = uuid4()
        mock_organization = Organization(
            id=mock_current_user.organization_id,
            firs_service_id="94ND90NR"
        )
        mock_integration.id = integration_id
        mock_integration.organization_id = mock_current_user.organization_id
        
        # Create test request data
        request_data = {
            "integration_id": str(integration_id),
            "invoice_numbers": ["INV001", "INV002", "INV003"]
        }
        
        # Mock database operations
        with patch('app.crud.integration.get_integration_by_id', return_value=mock_integration):
            with patch('app.crud.organization.get_organization_by_id', return_value=mock_organization):
                with patch('app.crud.irn.create_batch_irn') as mock_create_batch:
                    # Setup mock return values
                    mock_irns = [
                        IRNRecord(
                            irn=f"INV00{i}-94ND90NR-20240611",
                            integration_id=str(integration_id),
                            invoice_number=f"INV00{i}",
                            service_id="94ND90NR",
                            timestamp="20240611",
                            status="unused",
                            generated_at=datetime.now(),
                            valid_until=datetime.now(),
                        ) for i in range(1, 4)
                    ]
                    failed_invoices = []
                    mock_create_batch.return_value = (mock_irns, failed_invoices)
                    
                    # Call API
                    response = client.post("/api/v1/irn/generate-batch", json=request_data)
                    
                    # Assertions
                    assert response.status_code == 201
                    assert len(response.json()["irns"]) == 3
                    assert response.json()["count"] == 3
                    assert response.json()["failed_count"] == 0
    
    def test_get_irn_details(self, mock_db, mock_current_user, mock_integration):
        """Test get IRN details endpoint"""
        # Setup
        integration_id = uuid4()
        mock_integration.id = integration_id
        mock_integration.organization_id = mock_current_user.organization_id
        
        mock_irn = IRNRecord(
            irn="INV001-94ND90NR-20240611",
            integration_id=str(integration_id),
            invoice_number="INV001",
            service_id="94ND90NR",
            timestamp="20240611",
            status="unused",
            generated_at=datetime.now(),
            valid_until=datetime.now(),
        )
        
        # Mock database operations
        with patch('app.crud.irn.get_irn_by_value', return_value=mock_irn):
            with patch('app.crud.integration.get_integration_by_id', return_value=mock_integration):
                # Call API
                response = client.get(f"/api/v1/irn/{mock_irn.irn}")
                
                # Assertions
                assert response.status_code == 200
                assert response.json()["irn"] == "INV001-94ND90NR-20240611"
    
    def test_update_irn_status(self, mock_db, mock_current_user, mock_integration):
        """Test update IRN status endpoint"""
        # Setup
        integration_id = uuid4()
        mock_integration.id = integration_id
        mock_integration.organization_id = mock_current_user.organization_id
        
        mock_irn = IRNRecord(
            irn="INV001-94ND90NR-20240611",
            integration_id=str(integration_id),
            invoice_number="INV001",
            service_id="94ND90NR",
            timestamp="20240611",
            status="unused",
            generated_at=datetime.now(),
            valid_until=datetime.now(),
        )
        
        updated_irn = IRNRecord(
            irn="INV001-94ND90NR-20240611",
            integration_id=str(integration_id),
            invoice_number="INV001",
            service_id="94ND90NR",
            timestamp="20240611",
            status="used",
            invoice_id="EXT123",
            used_at=datetime.now(),
            generated_at=datetime.now(),
            valid_until=datetime.now(),
        )
        
        # Request data
        request_data = {
            "status": "used",
            "invoice_id": "EXT123"
        }
        
        # Mock database operations
        with patch('app.crud.irn.get_irn_by_value', return_value=mock_irn):
            with patch('app.crud.integration.get_integration_by_id', return_value=mock_integration):
                with patch('app.crud.irn.update_irn_status', return_value=updated_irn):
                    # Call API
                    response = client.post(f"/api/v1/irn/{mock_irn.irn}/status", json=request_data)
                    
                    # Assertions
                    assert response.status_code == 200
                    assert response.json()["status"] == "used"
                    assert response.json()["invoice_id"] == "EXT123"
    
    def test_get_irn_metrics(self, mock_db, mock_current_user):
        """Test get IRN metrics endpoint"""
        # Setup
        integration_id = uuid4()
        
        # Mock metrics response
        metrics = {
            "used_count": 10,
            "unused_count": 5,
            "expired_count": 2,
            "total_count": 17,
            "recent_irns": []
        }
        
        # Mock database operations
        with patch('app.crud.irn.get_irn_metrics', return_value=metrics):
            # Call API
            response = client.get(f"/api/v1/irn/metrics/{integration_id}")
            
            # Assertions
            assert response.status_code == 200
            assert response.json()["used_count"] == 10
            assert response.json()["unused_count"] == 5
            assert response.json()["expired_count"] == 2
            assert response.json()["total_count"] == 17
