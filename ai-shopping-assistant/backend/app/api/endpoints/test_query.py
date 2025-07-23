"""
Tests for the query endpoint.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

from app.main import app
from app.models.query import QueryRequest, QueryResponse, Product
from app.middleware.auth import get_optional_user
from app.services.guest_action_service import guest_action_service

client = TestClient(app)

class TestQueryEndpoint:
    """Test cases for the query endpoint."""
    
    @pytest.mark.asyncio
    @patch('app.api.endpoints.query.gemini_service')
    async def test_process_query_success(self, mock_gemini_service):
        """Test successful query processing."""
        # Mock the response from the GeminiService
        mock_response = QueryResponse(
            query="What's the best 5G phone under ₹12,000 with 8GB RAM?",
            products=[
                Product(
                    title="Redmi Note 12 Pro 5G",
                    price=11999,
                    rating=4.2,
                    features=["8GB RAM", "128GB Storage", "5G", "50MP Camera", "5000mAh Battery"],
                    pros=["Great display", "Good camera", "Fast charging"],
                    cons=["Average build quality", "Bloatware"],
                    link="https://www.amazon.in/product1"
                ),
                Product(
                    title="Realme 11 5G",
                    price=12499,
                    rating=4.0,
                    features=["8GB RAM", "128GB Storage", "5G", "108MP Camera", "5000mAh Battery"],
                    pros=["Excellent camera", "Fast processor", "Good battery life"],
                    cons=["UI needs improvement", "Heating issues"],
                    link="https://www.flipkart.com/product2"
                )
            ],
            recommendations_summary="Based on your requirements, Redmi Note 12 Pro 5G is the best option."
        )
        
        # Configure the mock to return our mock response
        mock_gemini_service.process_query.return_value = mock_response
        
        # Create a test request
        request_data = {
            "query": "What's the best 5G phone under ₹12,000 with 8GB RAM?"
        }
        
        # Send the request to the endpoint
        response = client.post("/api/query", json=request_data)
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "What's the best 5G phone under ₹12,000 with 8GB RAM?"
        assert len(data["products"]) == 2
        assert data["products"][0]["title"] == "Redmi Note 12 Pro 5G"
        assert data["products"][1]["title"] == "Realme 11 5G"
        assert data["recommendations_summary"] == "Based on your requirements, Redmi Note 12 Pro 5G is the best option."
        
        # Verify the mock was called correctly
        mock_gemini_service.process_query.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('app.api.endpoints.query.gemini_service')
    async def test_process_query_with_context(self, mock_gemini_service):
        """Test query processing with conversation context."""
        # Mock the response from the GeminiService
        mock_response = QueryResponse(
            query="What about under ₹15,000?",
            products=[
                Product(
                    title="Poco X5 Pro 5G",
                    price=14999,
                    rating=4.3,
                    features=["8GB RAM", "256GB Storage", "5G", "108MP Camera", "5000mAh Battery"],
                    pros=["Best value for money", "Great performance", "AMOLED display"],
                    cons=["Camera could be better", "Plastic build"],
                    link="https://www.amazon.in/product3"
                )
            ],
            recommendations_summary="Poco X5 Pro 5G offers the best value for money under ₹15,000."
        )
        
        # Configure the mock to return our mock response
        mock_gemini_service.process_query.return_value = mock_response
        
        # Create a test request with conversation context
        request_data = {
            "query": "What about under ₹15,000?",
            "conversation_context": {
                "messages": [
                    {
                        "id": "1",
                        "text": "I'm looking for a 5G phone with 8GB RAM",
                        "sender": "user",
                        "timestamp": "2023-07-19T10:00:00Z"
                    },
                    {
                        "id": "2",
                        "text": "Here are some 5G phones with 8GB RAM...",
                        "sender": "system",
                        "timestamp": "2023-07-19T10:00:05Z"
                    }
                ],
                "last_query": "I'm looking for a 5G phone with 8GB RAM",
                "last_product_criteria": {
                    "category": "phone",
                    "features": ["5G Support", "8GB RAM"]
                }
            }
        }
        
        # Send the request to the endpoint
        response = client.post("/api/query", json=request_data)
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "What about under ₹15,000?"
        assert len(data["products"]) == 1
        assert data["products"][0]["title"] == "Poco X5 Pro 5G"
        
        # Verify the mock was called correctly with the context
        mock_gemini_service.process_query.assert_called_once()
        args, kwargs = mock_gemini_service.process_query.call_args
        assert kwargs["query"] == "What about under ₹15,000?"
        assert kwargs["conversation_context"] is not None
    
    @pytest.mark.asyncio
    @patch('app.api.endpoints.query.gemini_service')
    async def test_process_query_error(self, mock_gemini_service):
        """Test error handling in query processing."""
        # Configure the mock to raise an exception
        mock_gemini_service.process_query.side_effect = Exception("Test error")
        
        # Create a test request
        request_data = {
            "query": "What's the best 5G phone under ₹12,000 with 8GB RAM?"
        }
        
        # Send the request to the endpoint
        response = client.post("/api/query", json=request_data)
        
        # Verify the response
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Error processing query" in data["detail"]
    @
pytest.mark.asyncio
    @patch('app.api.endpoints.query.gemini_service')
    @patch('app.api.endpoints.query.get_optional_user')
    async def test_authenticated_user_query(self, mock_get_optional_user, mock_gemini_service):
        """Test query processing with an authenticated user."""
        # Mock the authenticated user
        mock_get_optional_user.return_value = {
            "sub": "auth0|123456789",
            "email": "user@example.com",
            "name": "Test User"
        }
        
        # Mock the response from the GeminiService
        mock_response = QueryResponse(
            query="What's the best 5G phone?",
            products=[
                Product(
                    title="Test Phone",
                    price=12999,
                    rating=4.5,
                    features=["8GB RAM", "5G"],
                    pros=["Good performance"],
                    cons=["Average battery"],
                    link="https://example.com/product"
                )
            ],
            recommendations_summary="Test recommendation"
        )
        mock_gemini_service.process_query.return_value = mock_response
        
        # Create a test request
        request_data = {
            "query": "What's the best 5G phone?"
        }
        
        # Send the request to the endpoint with an auth token
        response = client.post(
            "/api/query", 
            json=request_data,
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert "metadata" not in data or "remaining_guest_actions" not in data.get("metadata", {})
        
        # Verify the mock was called correctly
        mock_gemini_service.process_query.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('app.api.endpoints.query.gemini_service')
    @patch('app.api.endpoints.query.get_optional_user')
    @patch('app.api.endpoints.query.guest_action_service')
    async def test_guest_user_query(self, mock_guest_service, mock_get_optional_user, mock_gemini_service):
        """Test query processing with a guest user."""
        # Mock the guest user (no authentication)
        mock_get_optional_user.return_value = None
        
        # Mock the guest action service
        mock_guest_service.is_limit_reached.return_value = False
        mock_guest_service.track_action.return_value = True
        mock_guest_service.get_remaining_actions.return_value = 9
        
        # Mock the response from the GeminiService
        mock_response = QueryResponse(
            query="What's the best 5G phone?",
            products=[
                Product(
                    title="Test Phone",
                    price=12999,
                    rating=4.5,
                    features=["8GB RAM", "5G"],
                    pros=["Good performance"],
                    cons=["Average battery"],
                    link="https://example.com/product"
                )
            ],
            recommendations_summary="Test recommendation"
        )
        mock_gemini_service.process_query.return_value = mock_response
        
        # Create a test request
        request_data = {
            "query": "What's the best 5G phone?"
        }
        
        # Send the request to the endpoint without an auth token
        response = client.post("/api/query", json=request_data)
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert "metadata" in data
        assert data["metadata"]["remaining_guest_actions"] == 9
        
        # Verify the mock was called correctly
        mock_gemini_service.process_query.assert_called_once()
        mock_guest_service.is_limit_reached.assert_called_once()
        mock_guest_service.track_action.assert_called_once()
        mock_guest_service.get_remaining_actions.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('app.api.endpoints.query.get_optional_user')
    @patch('app.api.endpoints.query.guest_action_service')
    async def test_guest_limit_reached(self, mock_guest_service, mock_get_optional_user):
        """Test query processing when guest limit is reached."""
        # Mock the guest user (no authentication)
        mock_get_optional_user.return_value = None
        
        # Mock the guest action service to indicate limit reached
        mock_guest_service.is_limit_reached.return_value = True
        
        # Create a test request
        request_data = {
            "query": "What's the best 5G phone?"
        }
        
        # Send the request to the endpoint without an auth token
        response = client.post("/api/query", json=request_data)
        
        # Verify the response indicates limit reached
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert "Guest action limit reached" in data["detail"]
        
        # Verify the mock was called correctly
        mock_guest_service.is_limit_reached.assert_called_once()
        mock_guest_service.track_action.assert_not_called()