"""
Tests for authentication error handlers.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from jose import JWTError

from app.main import app
from app.middleware.auth import JWTValidationError

client = TestClient(app)

class TestAuthErrorHandlers:
    """Test cases for authentication error handlers."""
    
    @pytest.mark.asyncio
    @patch('app.middleware.auth.jwt_validator.validate_token')
    async def test_jwt_error_handler(self, mock_validate_token):
        """Test handling of JWT validation errors."""
        # Mock the JWT validation to raise a JWTError
        mock_validate_token.side_effect = JWTError("Invalid token signature")
        
        # Send a request to a protected endpoint
        response = client.get(
            "/api/user/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        # Verify the response
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Invalid authentication token"
        assert data["error_type"] == "token_invalid"
        assert "WWW-Authenticate" in response.headers
        assert response.headers["WWW-Authenticate"] == "Bearer"
    
    @pytest.mark.asyncio
    @patch('app.middleware.auth.jwt_validator.validate_token')
    async def test_jwt_expired_handler(self, mock_validate_token):
        """Test handling of JWT expiration errors."""
        # Mock the JWT validation to raise a JWTValidationError for expired token
        mock_validate_token.side_effect = JWTValidationError("Token has expired")
        
        # Send a request to a protected endpoint
        response = client.get(
            "/api/user/me",
            headers={"Authorization": "Bearer expired_token"}
        )
        
        # Verify the response
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Authentication token has expired"
        assert data["error_type"] == "token_expired"
        assert "Your session has expired" in data["error_description"]
        assert "WWW-Authenticate" in response.headers
    
    @pytest.mark.asyncio
    async def test_missing_token_handler(self):
        """Test handling of missing authentication token."""
        # Send a request to a protected endpoint without a token
        response = client.get("/api/user/me")
        
        # Verify the response
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Authentication required"
        assert data["error_type"] == "token_missing"
        assert "WWW-Authenticate" in response.headers
    
    @pytest.mark.asyncio
    @patch('app.api.endpoints.query.get_optional_user')
    @patch('app.api.endpoints.query.guest_action_service.is_limit_reached')
    async def test_guest_limit_handler(self, mock_is_limit_reached, mock_get_optional_user):
        """Test handling of guest action limit errors."""
        # Mock the guest user and limit reached
        mock_get_optional_user.return_value = None
        mock_is_limit_reached.return_value = True
        
        # Send a request to an endpoint that checks guest limits
        response = client.post(
            "/api/query",
            json={"query": "Test query"}
        )
        
        # Verify the response
        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Guest action limit reached"
        assert data["error_type"] == "guest_limit_reached"
        assert "Please log in to continue" in data["error_description"]