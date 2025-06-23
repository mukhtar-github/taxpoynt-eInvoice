"""
Test cases for Square POS integration connector.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

# Import test dependencies
from app.integrations.pos.square.connector import SquarePOSConnector
from app.integrations.pos.square.oauth import SquareOAuthManager
from app.integrations.base.errors import IntegrationError, AuthenticationError


class TestSquareConnector:
    """Test cases for SquarePOSConnector."""
    
    def test_init(self):
        """Test SquarePOSConnector initialization."""
        config = {
            "connection_id": "square-test-123", 
            "access_token": "test_access_token",
            "environment": "sandbox",
            "location_id": "test_location"
        }
        
        connector = SquarePOSConnector(config)
        assert connector.config == config
        assert connector.access_token == "test_access_token"
        assert connector.environment == "sandbox"
    
    @pytest.mark.asyncio
    @patch('app.integrations.pos.square.connector.Client')
    async def test_authenticate_success(self, mock_client):
        """Test successful authentication with Square."""
        # Mock Square SDK client
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        
        config = {"access_token": "test_token", "environment": "sandbox"}
        connector = SquarePOSConnector(config)
        
        result = await connector.authenticate()
        assert result is True
        mock_client.assert_called_once()