import pytest # type: ignore
from fastapi.testclient import TestClient # type: ignore
import uuid
from unittest.mock import patch, MagicMock

from app.models.integration import Integration


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


def test_create_integration_with_sensitive_data(client, mock_authentication):
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
            mock_integration = MagicMock(spec=Integration)
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
            # Make sure __dict__ is properly mocked
            mock_integration.__dict__ = {
                "id": mock_integration.id,
                "client_id": mock_integration.client_id,
                "name": mock_integration.name,
                "description": mock_integration.description,
                "config": mock_integration.config,
                "status": mock_integration.status
            }
            mock_create.return_value = mock_integration
            
            # Mock decryption to simulate retrieving unencrypted values
            with patch("app.services.integration_service.decrypt_sensitive_config_fields") as mock_decrypt:
                mock_decrypt.side_effect = lambda config: {
                    **config,
                    "api_key": "secret-api-key",
                    "client_secret": "super-secret-value",
                }
                
                # Mock decrypt_integration_config 
                with patch("app.services.integration_service.decrypt_integration_config") as mock_decrypt_integration:
                    # Create a mock for the response object
                    decrypted_integration = MagicMock()
                    decrypted_integration.id = mock_integration.id
                    decrypted_integration.client_id = mock_integration.client_id
                    decrypted_integration.name = mock_integration.name
                    decrypted_integration.description = mock_integration.description
                    decrypted_integration.config = {
                        "api_url": "https://api.example.com",
                        "api_key": "secret-api-key",
                        "client_secret": "super-secret-value"
                    }
                    decrypted_integration.status = mock_integration.status
                    
                    # Set the return value for the mock
                    mock_decrypt_integration.return_value = decrypted_integration
                    
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
                    
                    # Mock the get_db dependency
                    with patch("app.api.dependencies.get_db"):
                        response = client.post(
                            "/api/v1/integrations/",
                            json=integration_data,
                            headers={"Authorization": "Bearer test_token"}
                        )
                    
                    # Verify our service was called with the right data
                    assert mock_encrypt.call_count > 0
                    assert mock_decrypt.call_count > 0


def test_get_integration_decrypts_sensitive_data(client, mock_authentication):
    """Test retrieving an integration decrypts sensitive configuration data."""
    # Create a test integration ID
    test_integration_id = str(uuid.uuid4())
    
    # Mock the database operations
    with patch("app.crud.integration.get") as mock_get:
        mock_integration = MagicMock(spec=Integration)
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
        # Make sure __dict__ is properly mocked
        mock_integration.__dict__ = {
            "id": mock_integration.id,
            "client_id": mock_integration.client_id,
            "name": mock_integration.name,
            "description": mock_integration.description,
            "config": mock_integration.config,
            "status": mock_integration.status
        }
        mock_get.return_value = mock_integration
        
        # Mock the integration service
        with patch("app.services.integration_service.get_integration") as mock_get_integration:
            # Create a mock for the response object
            decrypted_integration = MagicMock()
            decrypted_integration.id = mock_integration.id
            decrypted_integration.client_id = mock_integration.client_id
            decrypted_integration.name = mock_integration.name
            decrypted_integration.description = mock_integration.description
            decrypted_integration.config = {
                "api_url": "https://api.example.com",
                "api_key": "secret-api-key",
                "client_secret": "super-secret-value"
            }
            decrypted_integration.status = mock_integration.status
            
            # Set the return value for the mock
            mock_get_integration.return_value = decrypted_integration
            
            # Test retrieving the integration
            with patch("app.api.dependencies.get_db"):
                response = client.get(
                    f"/api/v1/integrations/{test_integration_id}",
                    headers={"Authorization": "Bearer test_token"}
                )
            
            # Verify our service was called
            assert mock_get_integration.call_count > 0 