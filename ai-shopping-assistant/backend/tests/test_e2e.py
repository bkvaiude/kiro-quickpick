"""
End-to-end tests for the AI Shopping Assistant backend.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.models.query import QueryRequest, QueryResponse, Product, ConversationContext, ChatMessage

client = TestClient(app)

class TestEndToEnd:
    """End-to-end test cases for the AI Shopping Assistant backend."""
    
    @patch('app.services.gemini_service.genai')
    def test_complete_user_flow(self, mock_genai):
        """Test the complete user flow from query to response with conversation context."""
        # Mock the GenerativeModel and chat
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        mock_chat = MagicMock()
        mock_model.start_chat.return_value = mock_chat
        
        # Mock the first response
        mock_response1 = MagicMock()
        mock_response1.text = """
        {
            "products": [
                {
                    "title": "Redmi Note 12 Pro 5G",
                    "price": 11999,
                    "rating": 4.2,
                    "features": ["8GB RAM", "128GB Storage", "5G", "50MP Camera", "5000mAh Battery"],
                    "pros": ["Great display", "Good camera", "Fast charging"],
                    "cons": ["Average build quality", "Bloatware"],
                    "link": "https://www.amazon.in/product1"
                },
                {
                    "title": "Realme 11 5G",
                    "price": 12499,
                    "rating": 4.0,
                    "features": ["8GB RAM", "128GB Storage", "5G", "108MP Camera", "5000mAh Battery"],
                    "pros": ["Excellent camera", "Fast processor", "Good battery life"],
                    "cons": ["UI needs improvement", "Heating issues"],
                    "link": "https://www.flipkart.com/product2"
                }
            ],
            "recommendationsSummary": "Based on your requirements, Redmi Note 12 Pro 5G is the best option."
        }
        """
        
        # Mock the second response
        mock_response2 = MagicMock()
        mock_response2.text = """
        {
            "products": [
                {
                    "title": "Redmi Note 12 Pro 5G",
                    "price": 11999,
                    "rating": 4.2,
                    "features": ["8GB RAM", "128GB Storage", "5G", "50MP Camera", "5000mAh Battery"],
                    "pros": ["Great display", "Good camera", "Fast charging"],
                    "cons": ["Average build quality", "Bloatware"],
                    "link": "https://www.amazon.in/product1"
                }
            ],
            "recommendationsSummary": "Redmi Note 12 Pro 5G has better battery life with 5000mAh capacity and efficient processor."
        }
        """
        
        # Configure the mock to return different responses for different calls
        mock_chat.send_message_async.side_effect = [mock_response1, mock_response2]
        
        # First query
        first_query = "What's the best 5G phone under ₹12,000 with 8GB RAM?"
        response1 = client.post(
            "/api/query",
            json={"query": first_query}
        )
        
        # Verify the first response
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["query"] == first_query
        assert len(data1["products"]) == 2
        assert data1["products"][0]["title"] == "Redmi Note 12 Pro 5G"
        assert data1["products"][1]["title"] == "Realme 11 5G"
        
        # Extract conversation context from the first response
        # In a real scenario, the frontend would send this back
        # Here we'll construct it manually
        conversation_context = {
            "messages": [
                {
                    "id": "1",
                    "text": first_query,
                    "sender": "user",
                    "timestamp": "2023-07-19T10:00:00Z"
                },
                {
                    "id": "2",
                    "text": f"Recommendations for: {first_query}\nBased on your requirements, Redmi Note 12 Pro 5G is the best option.",
                    "sender": "system",
                    "timestamp": "2023-07-19T10:00:05Z"
                }
            ],
            "last_query": first_query,
            "last_product_criteria": {
                "category": "phone",
                "price_range": {"max": 12000},
                "features": ["5G Support", "8GB RAM"]
            }
        }
        
        # Second query (follow-up)
        second_query = "Which one has better battery life?"
        response2 = client.post(
            "/api/query",
            json={
                "query": second_query,
                "conversation_context": conversation_context
            }
        )
        
        # Verify the second response
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["query"] == second_query
        assert len(data2["products"]) == 1
        assert data2["products"][0]["title"] == "Redmi Note 12 Pro 5G"
        assert "battery life" in data2["recommendations_summary"].lower()
        
        # Verify the mocks were called correctly
        assert mock_chat.send_message_async.call_count == 2
    
    @patch('app.services.gemini_service.genai')
    def test_error_handling(self, mock_genai):
        """Test error handling in the API."""
        # Mock the GenerativeModel to raise an exception
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        mock_chat = MagicMock()
        mock_model.start_chat.return_value = mock_chat
        
        # Mock the chat to raise an exception
        mock_chat.send_message_async.side_effect = Exception("Test error")
        
        # Send a query
        response = client.post(
            "/api/query",
            json={"query": "What's the best 5G phone under ₹12,000?"}
        )
        
        # Verify the error response
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Error processing query" in data["detail"]
    
    @patch('app.services.gemini_service.genai')
    def test_malformed_response_handling(self, mock_genai):
        """Test handling of malformed responses from the Gemini API."""
        # Mock the GenerativeModel and chat
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        mock_chat = MagicMock()
        mock_model.start_chat.return_value = mock_chat
        
        # Mock a malformed response
        mock_response = MagicMock()
        mock_response.text = "This is not valid JSON"
        mock_chat.send_message_async.return_value = mock_response
        
        # Send a query
        response = client.post(
            "/api/query",
            json={"query": "What's the best 5G phone under ₹12,000?"}
        )
        
        # Verify the error response
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Failed to parse" in data["detail"]