import pytest
from fastapi.testclient import TestClient
import uuid
from unittest.mock import patch, MagicMock
import json

from app.models.organization import Organization


@pytest.fixture
def client():
    """Create a test client for the API with mocked database connection."""
    # Patch the database connection before importing the app
    with patch("app.db.session.engine"):
        with patch("app.db.session.get_db"):
            # Now import the app after patching the database connection
            from app.main import app
            return TestClient(app)


@pytest.fixture
def mock_authentication():
    """Mock authentication to bypass token verification."""
    with patch("app.api.dependencies.verify_token", return_value={"sub": str(uuid.uuid4())}):
        with patch("app.api.dependencies.get_current_user") as mock_user:
            # Create a mock user with required attributes
            mock_user.return_value = MagicMock()
            mock_user.return_value.id = uuid.uuid4()
            mock_user.return_value.is_active = True
            yield mock_user


@pytest.fixture
def mock_organization():
    """Create a mock organization object."""
    org = MagicMock(spec=Organization)
    org.id = uuid.uuid4()
    org.name = "MT Garba Global Ventures"
    org.tax_id = "12345678"
    org.logo_url = "https://example.com/logo.png"
    org.branding_settings = {"primary_color": "#1a73e8", "theme": "light"}
    # Make sure __dict__ is properly mocked
    org.__dict__ = {
        "id": org.id,
        "name": org.name,
        "tax_id": org.tax_id,
        "logo_url": org.logo_url,
        "branding_settings": org.branding_settings
    }
    return org


def test_create_organization(client, mock_authentication, mock_organization):
    """Test creating an organization."""
    # Mock the organization service
    with patch("app.services.organization_service.OrganizationService.create_organization") as mock_create:
        mock_create.return_value = mock_organization
        
        # Test data
        org_data = {
            "name": "MT Garba Global Ventures",
            "tax_id": "12345678",
            "branding_settings": {"primary_color": "#1a73e8", "theme": "light"}
        }
        
        # Mock the get_db dependency
        with patch("app.api.dependencies.get_db"):
            response = client.post(
                "/api/organizations",
                json=org_data,
                headers={"Authorization": "Bearer test_token"}
            )
        
        # Check that the response is successful
        assert response.status_code == 201
        
        # Verify the response contains the expected data
        response_data = response.json()
        assert response_data["name"] == "MT Garba Global Ventures"
        assert response_data["tax_id"] == "12345678"
        assert response_data["branding_settings"]["primary_color"] == "#1a73e8"
        
        # Verify our service was called with the right data
        mock_create.assert_called_once_with(org_data)


def test_get_organization(client, mock_authentication, mock_organization):
    """Test retrieving an organization."""
    # Mock the organization service
    with patch("app.services.organization_service.OrganizationService.get_organization") as mock_get:
        mock_get.return_value = mock_organization
        
        # Mock the get_db dependency
        with patch("app.api.dependencies.get_db"):
            response = client.get(
                f"/api/organizations/{mock_organization.id}",
                headers={"Authorization": "Bearer test_token"}
            )
        
        # Check that the response is successful
        assert response.status_code == 200
        
        # Verify the response contains the expected data
        response_data = response.json()
        assert response_data["name"] == "MT Garba Global Ventures"
        assert response_data["tax_id"] == "12345678"
        
        # Verify our service was called with the right data
        mock_get.assert_called_once_with(str(mock_organization.id))


def test_update_organization(client, mock_authentication, mock_organization):
    """Test updating an organization."""
    # Mock the organization service
    with patch("app.services.organization_service.OrganizationService.update_organization") as mock_update:
        mock_update.return_value = mock_organization
        
        # Test data
        update_data = {
            "name": "MT Garba Global Ventures Updated",
            "branding_settings": {"primary_color": "#34a853", "theme": "dark"}
        }
        
        # Mock the get_db dependency
        with patch("app.api.dependencies.get_db"):
            response = client.put(
                f"/api/organizations/{mock_organization.id}",
                json=update_data,
                headers={"Authorization": "Bearer test_token"}
            )
        
        # Check that the response is successful
        assert response.status_code == 200
        
        # Verify the response contains the expected data
        response_data = response.json()
        assert response_data["name"] == "MT Garba Global Ventures"
        
        # Verify our service was called with the right data
        mock_update.assert_called_once_with(str(mock_organization.id), update_data)


def test_upload_organization_logo(client, mock_authentication, mock_organization):
    """Test uploading a logo for an organization."""
    # Mock the organization service
    with patch("app.services.organization_service.OrganizationService.upload_logo") as mock_upload:
        mock_upload.return_value = "https://example.com/uploaded-logo.png"
        
        # Create test file data
        file_content = b"test file content"
        
        # Mock the get_db dependency
        with patch("app.api.dependencies.get_db"):
            response = client.post(
                f"/api/organizations/{mock_organization.id}/logo",
                files={"file": ("logo.png", file_content, "image/png")},
                headers={"Authorization": "Bearer test_token"}
            )
        
        # Check that the response is successful
        assert response.status_code == 200
        
        # Verify the response contains the expected data
        response_data = response.json()
        assert response_data["logo_url"] == "https://example.com/uploaded-logo.png"
        
        # Verify our service was called
        mock_upload.assert_called_once()


def test_delete_organization(client, mock_authentication, mock_organization):
    """Test deleting an organization."""
    # Mock the organization service
    with patch("app.services.organization_service.OrganizationService.delete_organization") as mock_delete:
        mock_delete.return_value = True
        
        # Mock the get_db dependency
        with patch("app.api.dependencies.get_db"):
            response = client.delete(
                f"/api/organizations/{mock_organization.id}",
                headers={"Authorization": "Bearer test_token"}
            )
        
        # Check that the response is successful
        assert response.status_code == 204
        
        # Verify our service was called with the right data
        mock_delete.assert_called_once_with(str(mock_organization.id))
