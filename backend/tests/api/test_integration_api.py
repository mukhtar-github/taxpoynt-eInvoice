import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid
from unittest.mock import patch

from app.main import app
from app.db.base import Base
from app.models.client import Client
from app.models.integration import Integration


@pytest.fixture
def client():
    """Create a test client for the API."""
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Mock database session for testing."""
    return pytest.MonkeyPatch()


@pytest.fixture
def mock_authentication():
    """Mock authentication to bypass token verification."""
    with patch("app.api.dependencies.verify_token", return_value={"sub": str(uuid.uuid4())}):
        with patch("app.api.dependencies.get_current_user") as mock_user:
            # Create a mock user with required attributes
            mock_user.return_value.id = uuid.uuid4()
            mock_user.return_value.is_active = True
            yield mock_user


def test_create_integration_with_sensitive_data(client, mock_db_session, mock_authentication):
    """Test creating an integration with sensitive configuration data."""
    # Create a test client for integration
    test_client_id = str(uuid.uuid4())
    
    # Mock the database operations
    with patch("app.services.integration_service.encrypt_sensitive_config_fields") as mock_encrypt:
        mock_encrypt.side_effect = lambda config: {
            **config,
            "api_key": f"encrypted_{config['api_key']}" if "api_key" in config else None,
            "client_secret": f"encrypted_{config['client_secret']}" if "client_secret" in config else None,
        }
        
        # Mock the crud operation to return a properly structured integration
        with patch("app.crud.integration.create") as mock_create:
            mock_integration = Integration()
            mock_integration.id = uuid.uuid4()
            mock_integration.client_id = test_client_id
            mock_integration.name = "Test Integration"
            mock_integration.description = "Test integration description"
            mock_integration.config = {
                "api_url": "https://api.example.com",
                "api_key": "encrypted_secret-api-key",
                "client_secret": "encrypted_super-secret-value"
            }
            mock_integration.status = "configured"
            mock_create.return_value = mock_integration
            
            # Mock decryption to simulate retrieving unencrypted values
            with patch("app.services.integration_service.decrypt_sensitive_config_fields") as mock_decrypt:
                mock_decrypt.side_effect = lambda config: {
                    **config,
                    "api_key": config["api_key"].replace("encrypted_", "") if config.get("api_key") else None,
                    "client_secret": config["client_secret"].replace("encrypted_", "") if config.get("client_secret") else None,
                }
                
                # Test creating an integration
                integration_data = {
                    "client_id": test_client_id,
                    "name": "Test Integration",
                    "description": "Test integration description",
                    "config": {
                        "api_url": "https://api.example.com",
                        "api_key": "secret-api-key",
                        "client_secret": "super-secret-value"
                    }
                }
                
                with patch("app.api.dependencies.get_db"):
                    response = client.post(
                        "/api/v1/integrations/",
                        json=integration_data,
                        headers={"Authorization": "Bearer test_token"}
                    )
                
                # Assert response
                assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
                
                # Verify the data in the response
                response_data = response.json()
                assert response_data["name"] == "Test Integration"
                assert response_data["config"]["api_url"] == "https://api.example.com"
                
                # Important: verify the sensitive data is returned unencrypted to the client
                assert response_data["config"]["api_key"] == "secret-api-key"
                assert response_data["config"]["client_secret"] == "super-secret-value"
                
                # Verify our service was called with the right data
                mock_encrypt.assert_called_once()
                mock_decrypt.assert_called()


def test_get_integration_decrypts_sensitive_data(client, mock_db_session, mock_authentication):
    """Test retrieving an integration decrypts sensitive configuration data."""
    # Create a test integration ID
    test_integration_id = str(uuid.uuid4())
    
    # Mock the database operations
    with patch("app.crud.integration.get") as mock_get:
        mock_integration = Integration()
        mock_integration.id = test_integration_id
        mock_integration.client_id = str(uuid.uuid4())
        mock_integration.name = "Test Integration"
        mock_integration.description = "Test integration description"
        mock_integration.config = {
            "api_url": "https://api.example.com",
            "api_key": "encrypted_secret-api-key",
            "client_secret": "encrypted_super-secret-value"
        }
        mock_integration.status = "configured"
        mock_get.return_value = mock_integration
        
        # Mock decryption
        with patch("app.services.integration_service.decrypt_sensitive_config_fields") as mock_decrypt:
            mock_decrypt.side_effect = lambda config: {
                **config,
                "api_key": config["api_key"].replace("encrypted_", ""),
                "client_secret": config["client_secret"].replace("encrypted_", "")
            }
            
            # Test retrieving the integration
            with patch("app.api.dependencies.get_db"):
                response = client.get(
                    f"/api/v1/integrations/{test_integration_id}",
                    headers={"Authorization": "Bearer test_token"}
                )
            
            # Assert response
            assert response.status_code == 200
            
            # Verify the data in the response
            response_data = response.json()
            assert response_data["name"] == "Test Integration"
            assert response_data["config"]["api_url"] == "https://api.example.com"
            
            # Verify sensitive data is decrypted
            assert response_data["config"]["api_key"] == "secret-api-key"
            assert response_data["config"]["client_secret"] == "super-secret-value"
            
            # Verify our service was called
            mock_decrypt.assert_called() 