"""
Tests for the user endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.middleware.auth import get_current_user

client = TestClient(app)

class TestUserEndpoints:
    """Test cases for the user endpoints."""
    
    @pytest.mark.asyncio
    @patch('app.middleware.auth.get_current_user')
    async def test_get_user_profile_authenticated(self, mock_get_current_user):
        """Test getting user profile when authenticated."""
        # Mock the authenticated user
        mock_user = {
            "sub": "auth0|123456789",
            "email": "user@example.com",
            "name": "Test User",
            "picture": "https://example.com/profile.jpg"
        }
        mock_get_current_user.return_value = mock_user
        
        # Send the request to the endpoint with an auth token
        response = client.get(
            "/api/user/me",
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "auth0|123456789"
        assert data["email"] == "user@example.com"
        assert data["name"] == "Test User"
        assert data["picture"] == "https://example.com/profile.jpg"
    
    @pytest.mark.asyncio
    async def test_get_user_profile_unauthenticated(self):
        """Test getting user profile when not authenticated."""
        # Send the request to the endpoint without an auth token
        response = client.get("/api/user/me")
        
        # Verify the response indicates authentication required
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Missing authentication token" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_get_remaining_actions(self):
        """Test getting remaining actions information."""
        # Send the request to the endpoint
        response = client.get("/api/user/remaining-actions")
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert "message" in data