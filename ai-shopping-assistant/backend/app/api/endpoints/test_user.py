"""
Tests for the user endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta

from app.main import app
from app.middleware.auth import get_current_user, get_optional_user
from app.models.credit import CreditStatus

client = TestClient(app)

class TestUserEndpoints:
    """Test cases for the user endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_user_profile_authenticated(self):
        """Test getting user profile when authenticated."""
        from app.api.endpoints.user import get_current_user, credit_service
        
        # Mock the authenticated user
        mock_user = {
            "sub": "auth0|123456789",
            "email": "user@example.com",
            "name": "Test User",
            "picture": "https://example.com/profile.jpg"
        }
        
        # Mock credit status
        mock_credit_status = CreditStatus(
            available_credits=45,
            max_credits=50,
            is_guest=False,
            can_reset=True,
            next_reset_time=datetime.utcnow() + timedelta(hours=12)
        )
        
        # Override dependencies
        def mock_get_current_user():
            return mock_user
            
        def mock_get_credit_status(user_id, is_guest):
            return mock_credit_status
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        credit_service.get_credit_status = mock_get_credit_status
        
        try:
            # Send the request to the endpoint
            response = client.get("/api/user/me")
            
            # Verify the response
            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == "auth0|123456789"
            assert data["email"] == "user@example.com"
            assert data["name"] == "Test User"
            assert data["picture"] == "https://example.com/profile.jpg"
            assert "credits" in data
            assert data["credits"]["available_credits"] == 45
            assert data["credits"]["max_credits"] == 50
            assert data["credits"]["is_guest"] == False
            assert data["credits"]["can_reset"] == True
            assert data["credits"]["next_reset_time"] is not None
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()
    
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
    @patch('app.api.endpoints.user.get_credit_status')
    async def test_get_user_credits_authenticated(self, mock_get_credit_status):
        """Test getting user credits for authenticated user."""
        # Mock credit status response
        mock_credit_response = {
            "user_id": "auth0|123456789",
            "available_credits": 45,
            "max_credits": 50,
            "is_guest": False,
            "can_reset": True,
            "next_reset_time": (datetime.utcnow() + timedelta(hours=12)).isoformat()
        }
        mock_get_credit_status.return_value = mock_credit_response
        
        # Send the request to the endpoint
        response = client.get(
            "/api/user/credits",
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "auth0|123456789"
        assert data["available_credits"] == 45
        assert data["max_credits"] == 50
        assert data["is_guest"] == False
        assert data["can_reset"] == True
        assert data["next_reset_time"] is not None
    
    @pytest.mark.asyncio
    @patch('app.api.endpoints.user.get_credit_status')
    async def test_get_user_credits_guest(self, mock_get_credit_status):
        """Test getting user credits for guest user."""
        # Mock credit status response for guest
        mock_credit_response = {
            "user_id": "guest_127.0.0.1_abc123",
            "available_credits": 8,
            "max_credits": 10,
            "is_guest": True,
            "can_reset": False,
            "next_reset_time": None
        }
        mock_get_credit_status.return_value = mock_credit_response
        
        # Send the request to the endpoint without auth token
        response = client.get("/api/user/credits")
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert data["available_credits"] == 8
        assert data["max_credits"] == 10
        assert data["is_guest"] == True
        assert data["can_reset"] == False
        assert data["next_reset_time"] is None
    
    @pytest.mark.asyncio
    @patch('app.api.endpoints.user.get_credit_status')
    async def test_get_credit_status_endpoint(self, mock_get_credit_status):
        """Test the credit status endpoint (backward compatibility)."""
        # Mock credit status response
        mock_credit_response = {
            "user_id": "auth0|123456789",
            "available_credits": 30,
            "max_credits": 50,
            "is_guest": False,
            "can_reset": True,
            "next_reset_time": (datetime.utcnow() + timedelta(hours=8)).isoformat()
        }
        mock_get_credit_status.return_value = mock_credit_response
        
        # Send the request to the endpoint
        response = client.get(
            "/api/user/credits/status",
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "auth0|123456789"
        assert data["available_credits"] == 30
        assert data["max_credits"] == 50
        assert data["is_guest"] == False