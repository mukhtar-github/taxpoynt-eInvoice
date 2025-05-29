import pytest
from unittest.mock import patch, MagicMock
import uuid

from app.services.organization_service import OrganizationService
from app.models.organization import Organization


@pytest.fixture
def organization_service():
    return OrganizationService()


@pytest.fixture
def mock_organization():
    """Create a mock organization object."""
    org = MagicMock(spec=Organization)
    org.id = uuid.uuid4()
    org.name = "MT Garba Global Ventures"
    org.tax_id = "12345678"
    org.logo_url = "https://example.com/logo.png"
    org.branding_settings = {"primary_color": "#1a73e8", "theme": "light"}
    return org


def test_create_organization(organization_service, mock_organization):
    """Test creating an organization."""
    # Mock the database operations
    with patch("app.crud.organization.create") as mock_create:
        mock_create.return_value = mock_organization
        
        # Test data
        org_data = {
            "name": "MT Garba Global Ventures",
            "tax_id": "12345678",
            "branding_settings": {"primary_color": "#1a73e8", "theme": "light"}
        }
        
        result = organization_service.create_organization(org_data)
        
        # Verify our service returned the expected result
        assert result.id == mock_organization.id
        assert result.name == "MT Garba Global Ventures"
        assert result.tax_id == "12345678"
        assert result.branding_settings == {"primary_color": "#1a73e8", "theme": "light"}
        
        # Verify our mock was called with the right data
        mock_create.assert_called_once()


def test_get_organization(organization_service, mock_organization):
    """Test retrieving an organization."""
    # Mock the database operations
    with patch("app.crud.organization.get") as mock_get:
        mock_get.return_value = mock_organization
        
        result = organization_service.get_organization(str(mock_organization.id))
        
        # Verify our service returned the expected result
        assert result.id == mock_organization.id
        assert result.name == "MT Garba Global Ventures"
        
        # Verify our mock was called with the right data
        mock_get.assert_called_once_with(mock_organization.id)


def test_update_organization(organization_service, mock_organization):
    """Test updating an organization."""
    # Mock the database operations
    with patch("app.crud.organization.get") as mock_get:
        mock_get.return_value = mock_organization
        
        with patch("app.crud.organization.update") as mock_update:
            mock_update.return_value = mock_organization
            
            # Test data
            update_data = {
                "name": "MT Garba Global Ventures Updated",
                "branding_settings": {"primary_color": "#34a853", "theme": "dark"}
            }
            
            result = organization_service.update_organization(str(mock_organization.id), update_data)
            
            # Verify our service returned the expected result
            assert result.id == mock_organization.id
            
            # Verify our mocks were called
            mock_get.assert_called_once()
            mock_update.assert_called_once()


def test_upload_logo(organization_service, mock_organization):
    """Test uploading a logo for an organization."""
    # Mock the database operations
    with patch("app.crud.organization.get") as mock_get:
        mock_get.return_value = mock_organization
        
        with patch("app.services.storage_service.upload_file") as mock_upload:
            mock_upload.return_value = "https://example.com/uploaded-logo.png"
            
            with patch("app.crud.organization.update") as mock_update:
                mock_update.return_value = mock_organization
                
                # Create a mock file
                mock_file = MagicMock()
                mock_file.filename = "logo.png"
                
                result = organization_service.upload_logo(str(mock_organization.id), mock_file)
                
                # Verify our service returned the expected result
                assert result == "https://example.com/uploaded-logo.png"
                
                # Verify our mocks were called
                mock_get.assert_called_once()
                mock_upload.assert_called_once()
                mock_update.assert_called_once()


def test_delete_organization(organization_service, mock_organization):
    """Test deleting an organization."""
    # Mock the database operations
    with patch("app.crud.organization.get") as mock_get:
        mock_get.return_value = mock_organization
        
        with patch("app.crud.organization.delete") as mock_delete:
            result = organization_service.delete_organization(str(mock_organization.id))
            
            # Verify our service returned the expected result
            assert result is True
            
            # Verify our mocks were called
            mock_get.assert_called_once()
            mock_delete.assert_called_once_with(mock_organization.id)
