"""
Test cases for Square OAuth integration.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from app.integrations.pos.square.oauth import SquareOAuthManager


class TestSquareOAuth:
    """Test cases for Square OAuth functionality."""
    
    def test_oauth_manager_init(self):
        """Test OAuth manager initialization.""" 
        config = {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret", 
            "redirect_uri": "https://example.com/callback"
        }
        
        oauth_manager = SquareOAuthManager(config)
        assert oauth_manager.client_id == "test_client_id"
        assert oauth_manager.client_secret == "test_client_secret"
        assert oauth_manager.redirect_uri == "https://example.com/callback"
    
    @pytest.mark.asyncio
    async def test_initiate_oauth_flow(self):
        """Test OAuth flow initiation."""
        config = {
            "client_id": "test_client_id",
            "redirect_uri": "https://example.com/callback"
        }
        
        oauth_manager = SquareOAuthManager(config)
        result = await oauth_manager.initiate_oauth_flow("user123")
        
        assert "authorization_url" in result
        assert "state" in result
        assert "client_id=test_client_id" in result["authorization_url"]