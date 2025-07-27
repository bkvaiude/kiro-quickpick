import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import Request
from app.api.endpoints.query import process_query
from app.models.query import QueryRequest, QueryResponse, ConversationContext, Product


class TestQueryEndpoint:
    """Test cases for the query endpoint with caching and credit integration"""
    
    def setup_method(self):
        """Set up test environment before each test"""
        self.mock_request = Mock(spec=Request)
        self.mock_request.client.host = "127.0.0.1"
        
        # Sample query request
        self.query_request = QueryRequest(
            query="Find me a laptop under $1000",
            conversation_context=None
        )
        
        # Sample query response
        self.sample_response = QueryResponse(
            query="Find me a laptop under $1000",
            products=[
                Product(
                    title="Test Laptop",
                    price=899.99,
                    rating=4.5,
                    features=["16GB RAM", "512GB SSD"],
                    pros=["Fast performance", "Good value"],
                    cons=["Average battery life"],
                    link="https://example.com/laptop"
                )
            ],
            recommendations_summary="Great laptop for the price",
            metadata={}
        )
        
        # Sample credit status
        self.sample_credit_status = {
            "user_id": "127.0.0.1",
            "available_credits": 9,
            "max_credits": 10,
            "is_guest": True,
            "can_reset": False,
            "next_reset_time": None
        }
    
    @pytest.mark.asyncio
    @patch('app.api.endpoints.query.query_cache_service')
    @patch('app.api.endpoints.query.get_credit_status')
    @patch('app.api.endpoints.query.gemini_service')
    async def test_cache_hit_guest_user(self, mock_gemini, mock_get_credit_status, mock_cache_service):
        """Test cache hit for guest user - should not deduct credits"""
        # Mock cache hit
        mock_cache_service.generate_query_hash.return_value = "test_hash_123"
        mock_cache_service.get_cached_result.return_value = self.sample_response.model_dump()
        
        # Mock credit status
        mock_get_credit_status.return_value = self.sample_credit_status
        
        # Process query
        result = await process_query(self.query_request, self.mock_request, user=None)
        
        # Verify cache was checked
        mock_cache_service.generate_query_hash.assert_called_once_with(
            query="Find me a laptop under $1000",
            conversation_context=None
        )
        mock_cache_service.get_cached_result.assert_called_once_with("test_hash_123")
        
        # Verify gemini was NOT called for cache hit
        mock_gemini.process_query.assert_not_called()
        
        # Verify response has cache indicators
        assert result.metadata["cached"] is True
        assert result.metadata["cache_hit"] is True
        assert result.metadata["available_credits"] == 9
        assert result.metadata["is_guest"] is True
    
    @pytest.mark.asyncio
    @patch('app.api.endpoints.query.query_cache_service')
    @patch('app.api.endpoints.query.get_credit_status')
    @patch('app.api.endpoints.query.validate_credits')
    @patch('app.api.endpoints.query.deduct_credit')
    @patch('app.api.endpoints.query.gemini_service')
    async def test_cache_miss_guest_user(self, mock_gemini, mock_deduct_credit, mock_validate_credits, mock_get_credit_status, mock_cache_service):
        """Test cache miss for guest user - should deduct credits and cache result"""
        # Mock cache miss
        mock_cache_service.generate_query_hash.return_value = "test_hash_123"
        mock_cache_service.get_cached_result.return_value = None
        
        # Mock credit functions
        mock_validate_credits.return_value = None
        mock_deduct_credit.return_value = True
        mock_get_credit_status.return_value = {
            **self.sample_credit_status,
            "available_credits": 8  # After deduction
        }
        
        # Mock gemini service
        mock_gemini.process_query.return_value = self.sample_response
        
        # Process query
        result = await process_query(self.query_request, self.mock_request, user=None)
        
        # Verify cache was checked
        mock_cache_service.get_cached_result.assert_called_once_with("test_hash_123")
        
        # Verify credits were validated and deducted
        mock_validate_credits.assert_called_once_with(self.mock_request, None)
        mock_deduct_credit.assert_called_once_with(self.mock_request, None)
        
        # Verify query was processed
        mock_gemini.process_query.assert_called_once()
        
        # Verify result was cached (the response gets modified with metadata before caching)
        mock_cache_service.cache_result.assert_called_once()
        cached_args = mock_cache_service.cache_result.call_args[0]
        assert cached_args[0] == "test_hash_123"
        assert cached_args[1]["query"] == "Find me a laptop under $1000"
        assert len(cached_args[1]["products"]) == 1
        
        # Verify response has correct indicators
        assert result.metadata["cached"] is False
        assert result.metadata["cache_hit"] is False
        assert result.metadata["available_credits"] == 8
        assert result.metadata["is_guest"] is True
    
    @pytest.mark.asyncio
    @patch('app.api.endpoints.query.query_cache_service')
    @patch('app.api.endpoints.query.get_credit_status')
    @patch('app.api.endpoints.query.gemini_service')
    async def test_cache_hit_registered_user(self, mock_gemini, mock_get_credit_status, mock_cache_service):
        """Test cache hit for registered user"""
        # Mock user
        user = {"sub": "auth0|123456"}
        
        # Mock cache hit
        mock_cache_service.generate_query_hash.return_value = "test_hash_123"
        mock_cache_service.get_cached_result.return_value = self.sample_response.model_dump()
        
        # Mock credit status for registered user
        mock_get_credit_status.return_value = {
            "user_id": "auth0|123456",
            "available_credits": 45,
            "max_credits": 50,
            "is_guest": False,
            "can_reset": True,
            "next_reset_time": "2024-01-02T00:00:00"
        }
        
        # Process query
        result = await process_query(self.query_request, self.mock_request, user=user)
        
        # Verify cache was checked
        mock_cache_service.get_cached_result.assert_called_once_with("test_hash_123")
        
        # Verify gemini was NOT called for cache hit
        mock_gemini.process_query.assert_not_called()
        
        # Verify response has cache indicators
        assert result.metadata["cached"] is True
        assert result.metadata["cache_hit"] is True
        assert result.metadata["available_credits"] == 45
        assert result.metadata["is_guest"] is False
    
    @pytest.mark.asyncio
    @patch('app.api.endpoints.query.query_cache_service')
    @patch('app.api.endpoints.query.get_credit_status')
    @patch('app.api.endpoints.query.validate_credits')
    @patch('app.api.endpoints.query.deduct_credit')
    @patch('app.api.endpoints.query.gemini_service')
    async def test_conversation_context_affects_cache(self, mock_gemini, mock_deduct_credit, mock_validate_credits, mock_get_credit_status, mock_cache_service):
        """Test that conversation context affects cache key generation"""
        # Create request with conversation context
        context = ConversationContext(
            messages=[],
            last_query="Previous query about phones"
        )
        request_with_context = QueryRequest(
            query="What about laptops?",
            conversation_context=context
        )
        
        # Mock cache miss
        mock_cache_service.generate_query_hash.return_value = "test_hash_with_context"
        mock_cache_service.get_cached_result.return_value = None
        
        # Mock other services
        mock_validate_credits.return_value = None
        mock_deduct_credit.return_value = True
        mock_gemini.process_query.return_value = self.sample_response
        mock_get_credit_status.return_value = self.sample_credit_status
        
        # Process query
        await process_query(request_with_context, self.mock_request, user=None)
        
        # Verify cache key generation included context
        expected_context_str = json.dumps(context.model_dump(), sort_keys=True)
        mock_cache_service.generate_query_hash.assert_called_once_with(
            query="What about laptops?",
            conversation_context=expected_context_str
        )
    
    @pytest.mark.asyncio
    @patch('app.api.endpoints.query.query_cache_service')
    @patch('app.api.endpoints.query.validate_credits')
    async def test_credit_exhausted_exception(self, mock_validate_credits, mock_cache_service):
        """Test that credit exhaustion is handled properly"""
        from app.middleware.credit_middleware import CreditExhaustedException
        
        # Mock cache miss
        mock_cache_service.generate_query_hash.return_value = "test_hash_123"
        mock_cache_service.get_cached_result.return_value = None
        
        # Mock credit validation to raise exception
        mock_validate_credits.side_effect = CreditExhaustedException("No credits remaining")
        
        # Process query should raise CreditExhaustedException
        with pytest.raises(CreditExhaustedException):
            await process_query(self.query_request, self.mock_request, user=None)
        
        # Verify cache was checked first
        mock_cache_service.get_cached_result.assert_called_once()
        
        # Verify credits were validated
        mock_validate_credits.assert_called_once_with(self.mock_request, None)
    
    @pytest.mark.asyncio
    @patch('app.api.endpoints.query.query_cache_service')
    @patch('app.api.endpoints.query.validate_credits')
    @patch('app.api.endpoints.query.deduct_credit')
    @patch('app.api.endpoints.query.gemini_service')
    async def test_gemini_service_error_handling(self, mock_gemini, mock_deduct_credit, mock_validate_credits, mock_cache_service):
        """Test error handling when Gemini service fails"""
        # Mock cache miss
        mock_cache_service.generate_query_hash.return_value = "test_hash_123"
        mock_cache_service.get_cached_result.return_value = None
        
        # Mock credit functions (should pass)
        mock_validate_credits.return_value = None
        mock_deduct_credit.return_value = True
        
        # Mock gemini service to raise exception
        mock_gemini.process_query.side_effect = Exception("Gemini API error")
        
        # Process query should raise Exception
        with pytest.raises(Exception):
            await process_query(self.query_request, self.mock_request, user=None)
        
        # Verify cache was checked
        mock_cache_service.get_cached_result.assert_called_once()
        
        # Verify credits were validated and deducted
        mock_validate_credits.assert_called_once()
        mock_deduct_credit.assert_called_once()
        
        # Verify gemini was called
        mock_gemini.process_query.assert_called_once()
        
        # Verify result was NOT cached due to error
        mock_cache_service.cache_result.assert_not_called()