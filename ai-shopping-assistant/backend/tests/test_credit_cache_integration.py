"""
Integration tests for credit system and caching mechanisms.
Tests the end-to-end flow of credit management and query caching.
"""
import pytest
import time
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.services.credit_service import credit_service
from app.services.query_cache_service import query_cache_service
from app.models.query import QueryRequest

client = TestClient(app)


class TestCreditCacheIntegration:
    """Integration tests for credit system and caching mechanisms."""
    
    def setup_method(self):
        """Set up test environment before each test"""
        # Clear credit service data
        credit_service._user_credits = {}
        credit_service._credit_transactions = []
        
        # Clear cache service data
        query_cache_service.clear_cache()
    
    @patch('app.services.gemini_service.GeminiService.process_query')
    def test_guest_user_credit_flow_with_caching(self, mock_process_query):
        """Test complete guest user flow with credit deduction and caching"""
        # Mock the process_query method to return a QueryResponse
        from app.models.query import QueryResponse, Product
        
        mock_product = Product(
            title="Test Product",
            price=1000,
            rating=4.5,
            features=["Feature 1", "Feature 2"],
            pros=["Pro 1"],
            cons=["Con 1"],
            link="https://example.com/product"
        )
        
        mock_response = QueryResponse(
            query="Find me a laptop under 50000",
            products=[mock_product],
            recommendations_summary="Test recommendation"
        )
        
        mock_process_query.return_value = mock_response
        
        # First query - should deduct credit and cache result
        query = "Find me a laptop under 50000"
        response1 = client.post(
            "/api/query",
            json={"query": query},
            headers={"X-Session-ID": "guest_session_123"}
        )
        
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["query"] == query
        assert len(data1["products"]) == 1
        
        # Check credit was deducted
        credits_after_first = client.get(
            "/api/credits/status",
            headers={"X-Session-ID": "guest_session_123"}
        )
        assert credits_after_first.status_code == 200
        credit_data = credits_after_first.json()
        assert credit_data["available_credits"] == 9  # 10 - 1
        assert credit_data["is_guest"] is True
        
        # Second identical query - should use cache and still deduct credit
        response2 = client.post(
            "/api/query",
            json={"query": query},
            headers={"X-Session-ID": "guest_session_123"}
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["query"] == query
        assert data2 == data1  # Should be identical due to caching
        
        # Check credit was deducted again (cache doesn't prevent credit deduction)
        credits_after_second = client.get(
            "/api/credits/status",
            headers={"X-Session-ID": "guest_session_123"}
        )
        assert credits_after_second.status_code == 200
        credit_data2 = credits_after_second.json()
        assert credit_data2["available_credits"] == 8  # 9 - 1
        
        # Verify process_query was called only once due to caching
        assert mock_process_query.call_count == 1
    
    @patch('app.services.gemini_service.genai')
    def test_registered_user_credit_flow_with_auto_reset(self, mock_genai):
        """Test registered user credit flow with automatic reset"""
        # Mock Gemini API
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_chat = MagicMock()
        mock_model.start_chat.return_value = mock_chat
        
        mock_response = MagicMock()
        mock_response.text = '''
        {
            "products": [{"title": "Test Product", "price": 1000, "rating": 4.5, "features": [], "pros": [], "cons": [], "link": "https://example.com"}],
            "recommendationsSummary": "Test recommendation"
        }
        '''
        mock_chat.send_message_async.return_value = mock_response
        
        # Mock JWT token for registered user
        mock_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhdXRoMHwxMjM0NTYiLCJleHAiOjk5OTk5OTk5OTl9.test"
        
        with patch('app.services.credit_service.datetime') as mock_datetime:
            base_time = datetime(2025, 7, 24, 12, 0, 0)
            mock_datetime.utcnow.return_value = base_time
            
            # First query
            response1 = client.post(
                "/api/query",
                json={"query": "Find me a phone"},
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response1.status_code == 200
            
            # Check initial credits
            credits_response = client.get(
                "/api/credits/status",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            assert credits_response.status_code == 200
            credit_data = credits_response.json()
            assert credit_data["available_credits"] == 49  # 50 - 1
            assert credit_data["is_guest"] is False
            assert credit_data["can_reset"] is True
            
            # Advance time past reset interval
            future_time = base_time + timedelta(hours=25)  # Past 24-hour reset
            mock_datetime.utcnow.return_value = future_time
            
            # Next query should trigger auto-reset
            response2 = client.post(
                "/api/query",
                json={"query": "Find me a tablet"},
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response2.status_code == 200
            
            # Check credits were reset and then deducted
            credits_after_reset = client.get(
                "/api/credits/status",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            assert credits_after_reset.status_code == 200
            reset_credit_data = credits_after_reset.json()
            assert reset_credit_data["available_credits"] == 49  # Reset to 50, then deducted 1
    
    @patch('app.services.gemini_service.genai')
    def test_credit_exhaustion_prevents_queries(self, mock_genai):
        """Test that exhausted credits prevent new queries"""
        # Mock Gemini API
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_chat = MagicMock()
        mock_model.start_chat.return_value = mock_chat
        
        mock_response = MagicMock()
        mock_response.text = '''
        {
            "products": [{"title": "Test Product", "price": 1000, "rating": 4.5, "features": [], "pros": [], "cons": [], "link": "https://example.com"}],
            "recommendationsSummary": "Test recommendation"
        }
        '''
        mock_chat.send_message_async.return_value = mock_response
        
        session_id = "guest_exhausted_123"
        
        # Exhaust all guest credits (10 queries)
        for i in range(10):
            response = client.post(
                "/api/query",
                json={"query": f"Query {i}"},
                headers={"X-Session-ID": session_id}
            )
            assert response.status_code == 200
        
        # Check credits are exhausted
        credits_response = client.get(
            "/api/credits/status",
            headers={"X-Session-ID": session_id}
        )
        assert credits_response.status_code == 200
        credit_data = credits_response.json()
        assert credit_data["available_credits"] == 0
        
        # Next query should fail with 429 (Too Many Requests)
        response = client.post(
            "/api/query",
            json={"query": "This should fail"},
            headers={"X-Session-ID": session_id}
        )
        
        assert response.status_code == 429
        error_data = response.json()
        assert error_data["error_type"] == "credits_exhausted"
        assert "Insufficient credits" in error_data["detail"]
    
    @patch('app.services.gemini_service.genai')
    def test_cache_expiration_forces_new_api_call(self, mock_genai):
        """Test that expired cache entries force new API calls"""
        # Mock Gemini API
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_chat = MagicMock()
        mock_model.start_chat.return_value = mock_chat
        
        mock_response = MagicMock()
        mock_response.text = '''
        {
            "products": [{"title": "Test Product", "price": 1000, "rating": 4.5, "features": [], "pros": [], "cons": [], "link": "https://example.com"}],
            "recommendationsSummary": "Test recommendation"
        }
        '''
        mock_chat.send_message_async.return_value = mock_response
        
        query = "Find me a laptop"
        session_id = "cache_test_session"
        
        # First query - caches result
        response1 = client.post(
            "/api/query",
            json={"query": query},
            headers={"X-Session-ID": session_id}
        )
        assert response1.status_code == 200
        
        # Verify cache was used (only 1 API call so far)
        assert mock_chat.send_message_async.call_count == 1
        
        # Manually expire cache
        with patch('time.time') as mock_time:
            # Set time to far in the future to expire cache
            mock_time.return_value = time.time() + 7200  # 2 hours later
            
            # Clear expired cache
            query_cache_service.clear_expired_cache()
            
            # Same query should now make new API call
            response2 = client.post(
                "/api/query",
                json={"query": query},
                headers={"X-Session-ID": session_id}
            )
            assert response2.status_code == 200
            
            # Verify new API call was made
            assert mock_chat.send_message_async.call_count == 2
    
    @patch('app.services.gemini_service.genai')
    def test_different_users_separate_credits_and_cache(self, mock_genai):
        """Test that different users have separate credit accounts and cache"""
        # Mock Gemini API
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_chat = MagicMock()
        mock_model.start_chat.return_value = mock_chat
        
        mock_response = MagicMock()
        mock_response.text = '''
        {
            "products": [{"title": "Test Product", "price": 1000, "rating": 4.5, "features": [], "pros": [], "cons": [], "link": "https://example.com"}],
            "recommendationsSummary": "Test recommendation"
        }
        '''
        mock_chat.send_message_async.return_value = mock_response
        
        query = "Find me a smartphone"
        
        # User 1 (guest)
        response1 = client.post(
            "/api/query",
            json={"query": query},
            headers={"X-Session-ID": "guest_user_1"}
        )
        assert response1.status_code == 200
        
        # User 2 (guest)
        response2 = client.post(
            "/api/query",
            json={"query": query},
            headers={"X-Session-ID": "guest_user_2"}
        )
        assert response2.status_code == 200
        
        # Check both users have separate credit accounts
        credits1 = client.get(
            "/api/credits/status",
            headers={"X-Session-ID": "guest_user_1"}
        )
        credits2 = client.get(
            "/api/credits/status",
            headers={"X-Session-ID": "guest_user_2"}
        )
        
        assert credits1.status_code == 200
        assert credits2.status_code == 200
        
        credit_data1 = credits1.json()
        credit_data2 = credits2.json()
        
        # Both should have 9 credits (started with 10, used 1)
        assert credit_data1["available_credits"] == 9
        assert credit_data2["available_credits"] == 9
        assert credit_data1["user_id"] != credit_data2["user_id"]
        
        # Cache should be shared (only 1 API call for same query)
        assert mock_chat.send_message_async.call_count == 1
    
    @patch('app.services.gemini_service.genai')
    def test_conversation_context_with_credits_and_cache(self, mock_genai):
        """Test conversation context handling with credit deduction and caching"""
        # Mock Gemini API
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_chat = MagicMock()
        mock_model.start_chat.return_value = mock_chat
        
        # Different responses for different queries
        mock_response1 = MagicMock()
        mock_response1.text = '''
        {
            "products": [{"title": "Laptop 1", "price": 50000, "rating": 4.5, "features": [], "pros": [], "cons": [], "link": "https://example.com/1"}],
            "recommendationsSummary": "Best laptop recommendation"
        }
        '''
        
        mock_response2 = MagicMock()
        mock_response2.text = '''
        {
            "products": [{"title": "Laptop 1", "price": 50000, "rating": 4.5, "features": [], "pros": [], "cons": [], "link": "https://example.com/1"}],
            "recommendationsSummary": "Laptop 1 has better battery life"
        }
        '''
        
        mock_chat.send_message_async.side_effect = [mock_response1, mock_response2]
        
        session_id = "conversation_test"
        
        # First query
        response1 = client.post(
            "/api/query",
            json={"query": "Find me a laptop under 60000"},
            headers={"X-Session-ID": session_id}
        )
        assert response1.status_code == 200
        
        # Follow-up query with context
        conversation_context = {
            "messages": [
                {
                    "id": "1",
                    "text": "Find me a laptop under 60000",
                    "sender": "user",
                    "timestamp": "2025-07-24T10:00:00Z"
                },
                {
                    "id": "2",
                    "text": "Best laptop recommendation",
                    "sender": "system",
                    "timestamp": "2025-07-24T10:00:05Z"
                }
            ]
        }
        
        response2 = client.post(
            "/api/query",
            json={
                "query": "Which one has better battery life?",
                "conversation_context": conversation_context
            },
            headers={"X-Session-ID": session_id}
        )
        assert response2.status_code == 200
        
        # Check credits were deducted for both queries
        credits_response = client.get(
            "/api/credits/status",
            headers={"X-Session-ID": session_id}
        )
        assert credits_response.status_code == 200
        credit_data = credits_response.json()
        assert credit_data["available_credits"] == 8  # 10 - 2
        
        # Verify both API calls were made (different queries, no cache hit)
        assert mock_chat.send_message_async.call_count == 2
    
    def test_cache_statistics_tracking(self):
        """Test cache statistics are tracked correctly"""
        # Initial stats should be empty
        stats = query_cache_service.get_cache_stats()
        assert stats['cache_size'] == 0
        assert stats['cache_hits'] == 0
        assert stats['cache_misses'] == 0
        
        # Cache some results
        query_cache_service.cache_result("hash1", {"result": "data1"})
        query_cache_service.cache_result("hash2", {"result": "data2"})
        
        # Test cache hits and misses
        result1 = query_cache_service.get_cached_result("hash1")  # Hit
        result2 = query_cache_service.get_cached_result("hash1")  # Hit
        result3 = query_cache_service.get_cached_result("nonexistent")  # Miss
        
        assert result1 == {"result": "data1"}
        assert result2 == {"result": "data1"}
        assert result3 is None
        
        # Check final stats
        final_stats = query_cache_service.get_cache_stats()
        assert final_stats['cache_size'] == 2
        assert final_stats['cache_hits'] == 2
        assert final_stats['cache_misses'] == 1
        assert final_stats['hit_rate_percent'] == 66.67
    
    @patch('app.services.gemini_service.genai')
    def test_error_handling_with_credits(self, mock_genai):
        """Test error handling doesn't deduct credits"""
        # Mock Gemini API to raise an error
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_chat = MagicMock()
        mock_model.start_chat.return_value = mock_chat
        mock_chat.send_message_async.side_effect = Exception("API Error")
        
        session_id = "error_test_session"
        
        # Check initial credits
        initial_credits = client.get(
            "/api/credits/status",
            headers={"X-Session-ID": session_id}
        )
        assert initial_credits.status_code == 200
        initial_data = initial_credits.json()
        initial_count = initial_data["available_credits"]
        
        # Query that will fail
        response = client.post(
            "/api/query",
            json={"query": "This will fail"},
            headers={"X-Session-ID": session_id}
        )
        
        # Should return error
        assert response.status_code == 500
        
        # Credits should not be deducted on error
        final_credits = client.get(
            "/api/credits/status",
            headers={"X-Session-ID": session_id}
        )
        assert final_credits.status_code == 200
        final_data = final_credits.json()
        
        # Credits should remain the same (no deduction on error)
        assert final_data["available_credits"] == initial_count
    
    @patch('app.services.gemini_service.genai')
    def test_cache_indicator_in_response(self, mock_genai):
        """Test that cached results include cache indicator in response (Requirement 3.5)"""
        # Mock Gemini API
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_chat = MagicMock()
        mock_model.start_chat.return_value = mock_chat
        
        mock_response = MagicMock()
        mock_response.text = '''
        {
            "products": [{"title": "Test Product", "price": 1000, "rating": 4.5, "features": [], "pros": [], "cons": [], "link": "https://example.com"}],
            "recommendationsSummary": "Test recommendation"
        }
        '''
        mock_chat.send_message_async.return_value = mock_response
        
        query = "Find me a laptop"
        session_id = "cache_indicator_test"
        
        # First query - should not be cached
        response1 = client.post(
            "/api/query",
            json={"query": query},
            headers={"X-Session-ID": session_id}
        )
        
        assert response1.status_code == 200
        data1 = response1.json()
        assert "cached" in data1
        assert data1["cached"] is False
        
        # Second identical query - should be cached
        response2 = client.post(
            "/api/query",
            json={"query": query},
            headers={"X-Session-ID": session_id}
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        assert "cached" in data2
        assert data2["cached"] is True
        
        # Verify API was called only once due to caching
        assert mock_chat.send_message_async.call_count == 1
    
    @patch('app.services.gemini_service.genai')
    def test_cached_results_no_credit_deduction(self, mock_genai):
        """Test that cached results don't deduct credits (Requirement 3.4)"""
        # Mock Gemini API
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_chat = MagicMock()
        mock_model.start_chat.return_value = mock_chat
        
        mock_response = MagicMock()
        mock_response.text = '''
        {
            "products": [{"title": "Test Product", "price": 1000, "rating": 4.5, "features": [], "pros": [], "cons": [], "link": "https://example.com"}],
            "recommendationsSummary": "Test recommendation"
        }
        '''
        mock_chat.send_message_async.return_value = mock_response
        
        query = "Find me a smartphone"
        session_id = "no_credit_deduction_test"
        
        # First query - should deduct credit and cache result
        response1 = client.post(
            "/api/query",
            json={"query": query},
            headers={"X-Session-ID": session_id}
        )
        
        assert response1.status_code == 200
        
        # Check credits after first query
        credits_after_first = client.get(
            "/api/credits/status",
            headers={"X-Session-ID": session_id}
        )
        assert credits_after_first.status_code == 200
        first_credit_data = credits_after_first.json()
        assert first_credit_data["available_credits"] == 9  # 10 - 1
        
        # Second identical query - should use cache and NOT deduct credit
        response2 = client.post(
            "/api/query",
            json={"query": query},
            headers={"X-Session-ID": session_id}
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["cached"] is True
        
        # Check credits after second query - should remain the same
        credits_after_second = client.get(
            "/api/credits/status",
            headers={"X-Session-ID": session_id}
        )
        assert credits_after_second.status_code == 200
        second_credit_data = credits_after_second.json()
        assert second_credit_data["available_credits"] == 9  # No deduction for cached result
        
        # Verify API was called only once
        assert mock_chat.send_message_async.call_count == 1
    
    @patch('app.services.gemini_service.genai')
    def test_frontend_backend_credit_validation_integration(self, mock_genai):
        """Test that backend validates credits even if frontend is bypassed (Requirement 2.3)"""
        # Mock Gemini API
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_chat = MagicMock()
        mock_model.start_chat.return_value = mock_chat
        
        mock_response = MagicMock()
        mock_response.text = '''
        {
            "products": [{"title": "Test Product", "price": 1000, "rating": 4.5, "features": [], "pros": [], "cons": [], "link": "https://example.com"}],
            "recommendationsSummary": "Test recommendation"
        }
        '''
        mock_chat.send_message_async.return_value = mock_response
        
        session_id = "validation_bypass_test"
        
        # Exhaust all guest credits (10 queries)
        for i in range(10):
            response = client.post(
                "/api/query",
                json={"query": f"Query {i}"},
                headers={"X-Session-ID": session_id}
            )
            assert response.status_code == 200
        
        # Verify credits are exhausted
        credits_response = client.get(
            "/api/credits/status",
            headers={"X-Session-ID": session_id}
        )
        assert credits_response.status_code == 200
        credit_data = credits_response.json()
        assert credit_data["available_credits"] == 0
        
        # Attempt to bypass frontend validation by directly calling API
        bypass_response = client.post(
            "/api/query",
            json={"query": "Bypass attempt"},
            headers={"X-Session-ID": session_id}
        )
        
        # Backend should reject the request
        assert bypass_response.status_code == 429
        error_data = bypass_response.json()
        assert error_data["error_type"] == "credits_exhausted"
        assert "Insufficient credits" in error_data["detail"]
        
        # Verify credits remain at 0
        final_credits = client.get(
            "/api/credits/status",
            headers={"X-Session-ID": session_id}
        )
        assert final_credits.status_code == 200
        final_data = final_credits.json()
        assert final_data["available_credits"] == 0
    
    @patch('app.services.gemini_service.genai')
    def test_comprehensive_credit_and_cache_flow_integration(self, mock_genai):
        """Test comprehensive integration of credit system with caching across multiple scenarios"""
        # Mock Gemini API
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_chat = MagicMock()
        mock_model.start_chat.return_value = mock_chat
        
        mock_response = MagicMock()
        mock_response.text = '''
        {
            "products": [{"title": "Integration Test Product", "price": 2000, "rating": 4.3, "features": ["Feature A"], "pros": ["Pro A"], "cons": ["Con A"], "link": "https://example.com/integration"}],
            "recommendationsSummary": "Integration test recommendation"
        }
        '''
        mock_chat.send_message_async.return_value = mock_response
        
        # Test scenario 1: Fresh query with credit deduction
        session_id = "comprehensive_test"
        query = "Find me a comprehensive test product"
        
        response1 = client.post(
            "/api/query",
            json={"query": query},
            headers={"X-Session-ID": session_id}
        )
        
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["cached"] is False
        assert data1["query"] == query
        assert len(data1["products"]) == 1
        
        # Verify credit deduction
        credits_after_first = client.get(
            "/api/credits/status",
            headers={"X-Session-ID": session_id}
        )
        assert credits_after_first.status_code == 200
        assert credits_after_first.json()["available_credits"] == 9
        
        # Test scenario 2: Identical query should use cache and NOT deduct credit
        response2 = client.post(
            "/api/query",
            json={"query": query},
            headers={"X-Session-ID": session_id}
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["cached"] is True  # Should be cached
        assert data2["query"] == query
        assert data2["products"] == data1["products"]  # Same products
        
        # Verify NO credit deduction for cached result
        credits_after_second = client.get(
            "/api/credits/status",
            headers={"X-Session-ID": session_id}
        )
        assert credits_after_second.status_code == 200
        assert credits_after_second.json()["available_credits"] == 9  # Same as before
        
        # Test scenario 3: Different user should have separate credits but share cache
        different_session = "different_user_test"
        
        response3 = client.post(
            "/api/query",
            json={"query": query},  # Same query
            headers={"X-Session-ID": different_session}
        )
        
        assert response3.status_code == 200
        data3 = response3.json()
        assert data3["cached"] is True  # Should use shared cache
        
        # Different user should have full credits
        credits_different_user = client.get(
            "/api/credits/status",
            headers={"X-Session-ID": different_session}
        )
        assert credits_different_user.status_code == 200
        assert credits_different_user.json()["available_credits"] == 10  # Full credits
        
        # Verify API was called only once (due to caching)
        assert mock_chat.send_message_async.call_count == 1
        
        # Test scenario 4: Cache expiration forces new API call
        with patch('time.time') as mock_time:
            # Advance time to expire cache
            mock_time.return_value = time.time() + 7200  # 2 hours later
            query_cache_service.clear_expired_cache()
            
            # Same query should now make new API call
            response4 = client.post(
                "/api/query",
                json={"query": query},
                headers={"X-Session-ID": session_id}
            )
            
            assert response4.status_code == 200
            data4 = response4.json()
            assert data4["cached"] is False  # Fresh result after cache expiration
            
            # Should deduct credit for fresh result
            credits_after_expiry = client.get(
                "/api/credits/status",
                headers={"X-Session-ID": session_id}
            )
            assert credits_after_expiry.status_code == 200
            assert credits_after_expiry.json()["available_credits"] == 8  # 9 - 1
            
            # Verify new API call was made
            assert mock_chat.send_message_async.call_count == 2
    
    @patch('app.services.gemini_service.genai')
    def test_query_hash_generation_consistency(self, mock_genai):
        """Test that identical queries generate consistent hashes for caching"""
        # Mock Gemini API
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_chat = MagicMock()
        mock_model.start_chat.return_value = mock_chat
        
        mock_response = MagicMock()
        mock_response.text = '''
        {
            "products": [{"title": "Test Product", "price": 1000, "rating": 4.5, "features": [], "pros": [], "cons": [], "link": "https://example.com"}],
            "recommendationsSummary": "Test recommendation"
        }
        '''
        mock_chat.send_message_async.return_value = mock_response
        
        # Test that identical queries (with different whitespace/casing) use same cache
        queries = [
            "Find me a laptop under 50000",
            "find me a laptop under 50000",  # Different case
            " Find me a laptop under 50000 ",  # Extra whitespace
            "Find me a laptop under 50000",  # Exact duplicate
        ]
        
        session_id = "hash_consistency_test"
        
        # Send all variations of the query
        for i, query in enumerate(queries):
            response = client.post(
                "/api/query",
                json={"query": query},
                headers={"X-Session-ID": f"{session_id}_{i}"}
            )
            assert response.status_code == 200
        
        # Only the first query should have called the API (others should be cached)
        # Note: This depends on the hash generation normalizing the queries
        assert mock_chat.send_message_async.call_count == 1
    
    @patch('app.services.gemini_service.genai')
    def test_cache_ttl_expiration_behavior(self, mock_genai):
        """Test cache TTL behavior and automatic cleanup"""
        # Mock Gemini API
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_chat = MagicMock()
        mock_model.start_chat.return_value = mock_chat
        
        mock_response = MagicMock()
        mock_response.text = '''
        {
            "products": [{"title": "Test Product", "price": 1000, "rating": 4.5, "features": [], "pros": [], "cons": [], "link": "https://example.com"}],
            "recommendationsSummary": "Test recommendation"
        }
        '''
        mock_chat.send_message_async.return_value = mock_response
        
        query = "Find me a tablet"
        session_id = "ttl_test"
        
        # First query - caches result
        response1 = client.post(
            "/api/query",
            json={"query": query},
            headers={"X-Session-ID": session_id}
        )
        assert response1.status_code == 200
        assert response1.json()["cached"] is False
        
        # Immediate second query - should use cache
        response2 = client.post(
            "/api/query",
            json={"query": query},
            headers={"X-Session-ID": session_id}
        )
        assert response2.status_code == 200
        assert response2.json()["cached"] is True
        
        # Verify only one API call so far
        assert mock_chat.send_message_async.call_count == 1
        
        # Manually expire cache by advancing time
        with patch('time.time') as mock_time:
            # Set time to far in the future to expire cache (default TTL is 1 hour)
            mock_time.return_value = time.time() + 7200  # 2 hours later
            
            # Clear expired entries
            query_cache_service.clear_expired_cache()
            
            # Same query should now make new API call
            response3 = client.post(
                "/api/query",
                json={"query": query},
                headers={"X-Session-ID": session_id}
            )
            assert response3.status_code == 200
            assert response3.json()["cached"] is False
            
            # Verify new API call was made
            assert mock_chat.send_message_async.call_count == 2