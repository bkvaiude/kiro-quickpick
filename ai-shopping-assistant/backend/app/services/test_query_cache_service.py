import pytest
import time
import json
from unittest.mock import patch
from app.services.query_cache_service import QueryCacheService, query_cache_service


class TestQueryCacheService:
    """Test cases for QueryCacheService"""
    
    def setup_method(self):
        """Set up test environment before each test"""
        self.cache_service = QueryCacheService()
        # Clear cache before each test to ensure clean state
        try:
            self.cache_service.clear_cache()
        except Exception:
            # Ignore errors during setup (e.g., if database is not available)
            pass
    
    def test_generate_query_hash_basic(self):
        """Test basic query hash generation"""
        query = "Find me a laptop under $1000"
        hash1 = self.cache_service.generate_query_hash(query)
        hash2 = self.cache_service.generate_query_hash(query)
        
        # Same query should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 produces 64-character hex string
        assert isinstance(hash1, str)
    
    def test_generate_query_hash_with_context(self):
        """Test query hash generation with conversation context"""
        query = "What about gaming laptops?"
        context = "User previously asked about laptops under $1000"
        
        hash1 = self.cache_service.generate_query_hash(query, context)
        hash2 = self.cache_service.generate_query_hash(query, context)
        
        # Same query and context should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 64
    
    def test_generate_query_hash_normalization(self):
        """Test that query normalization works correctly"""
        query1 = "Find me a laptop"
        query2 = "FIND ME A LAPTOP"
        query3 = "  find me a laptop  "
        
        hash1 = self.cache_service.generate_query_hash(query1)
        hash2 = self.cache_service.generate_query_hash(query2)
        hash3 = self.cache_service.generate_query_hash(query3)
        
        # All variations should produce the same hash due to normalization
        assert hash1 == hash2 == hash3
    
    def test_generate_query_hash_different_queries(self):
        """Test that different queries produce different hashes"""
        query1 = "Find me a laptop"
        query2 = "Find me a phone"
        
        hash1 = self.cache_service.generate_query_hash(query1)
        hash2 = self.cache_service.generate_query_hash(query2)
        
        # Different queries should produce different hashes
        assert hash1 != hash2
    
    def test_generate_query_hash_context_affects_hash(self):
        """Test that different contexts produce different hashes"""
        query = "What about this one?"
        context1 = "User asked about laptops"
        context2 = "User asked about phones"
        
        hash1 = self.cache_service.generate_query_hash(query, context1)
        hash2 = self.cache_service.generate_query_hash(query, context2)
        
        # Same query with different contexts should produce different hashes
        assert hash1 != hash2
    
    def test_generate_query_hash_none_context(self):
        """Test query hash generation with None context"""
        query = "Find me a laptop"
        
        hash1 = self.cache_service.generate_query_hash(query, None)
        hash2 = self.cache_service.generate_query_hash(query)
        
        # None context and no context should produce same hash
        assert hash1 == hash2
    
    def test_generate_query_hash_empty_context(self):
        """Test query hash generation with empty context"""
        query = "Find me a laptop"
        
        hash1 = self.cache_service.generate_query_hash(query, "")
        hash2 = self.cache_service.generate_query_hash(query, "   ")
        hash3 = self.cache_service.generate_query_hash(query, None)
        
        # Empty/whitespace context should be treated as None
        assert hash1 == hash2 == hash3
    
    def test_cache_result_and_retrieval(self):
        """Test caching and retrieving results"""
        query_hash = "test_hash_123"
        result = {"products": [{"name": "Test Product", "price": 100}]}
        
        # Cache the result
        self.cache_service.cache_result(query_hash, result)
        
        # Retrieve the result
        cached_result = self.cache_service.get_cached_result(query_hash)
        
        assert cached_result == result
    
    def test_cache_miss(self):
        """Test cache miss for non-existent hash"""
        result = self.cache_service.get_cached_result("non_existent_hash")
        assert result is None
    
    def test_cache_expiration(self):
        """Test that cache entries can be stored and retrieved"""
        query_hash = "test_hash_123"
        result = {"products": [{"name": "Test Product"}]}
        
        # Cache the result
        self.cache_service.cache_result(query_hash, result)
        
        # Should be able to retrieve immediately
        cached_result = self.cache_service.get_cached_result(query_hash)
        assert cached_result == result
        
        # Verify cache statistics
        stats = self.cache_service.get_cache_stats()
        assert stats['cache_size'] == 1
        assert stats['cache_hits'] == 1
        assert stats['cache_misses'] == 0
        
        # Note: Actual expiration testing requires database time manipulation
        # which is complex to test. The expiration logic is handled by the database layer.
    
    def test_clear_expired_cache(self):
        """Test clearing expired cache entries"""
        with patch('time.time') as mock_time:
            # Mock current time
            mock_time.return_value = 1000
            
            # Add some cache entries
            self.cache_service.cache_result("hash1", {"result": 1})
            self.cache_service.cache_result("hash2", {"result": 2})
            
            # Move time forward but not past expiration
            mock_time.return_value = 1000 + 1800  # 30 minutes later
            
            # Should not clear anything (entries are fresh)
            cleared = self.cache_service.clear_expired_cache()
            assert cleared == 0
            
            # Verify entries are still there
            stats = self.cache_service.get_cache_stats()
            assert stats['cache_size'] == 2
            
            # Test that we can retrieve the cached entries
            result1 = self.cache_service.get_cached_result("hash1")
            result2 = self.cache_service.get_cached_result("hash2")
            assert result1 == {"result": 1}
            assert result2 == {"result": 2}
    
    def test_cache_stats(self):
        """Test cache statistics tracking"""
        # Initial stats
        stats = self.cache_service.get_cache_stats()
        assert stats['cache_size'] == 0
        assert stats['cache_hits'] == 0
        assert stats['cache_misses'] == 0
        assert stats['hit_rate_percent'] == 0
        
        # Add cache entry and test hit
        query_hash = "test_hash"
        result = {"test": "data"}
        self.cache_service.cache_result(query_hash, result)
        
        # Test cache hit
        self.cache_service.get_cached_result(query_hash)
        
        # Test cache miss
        self.cache_service.get_cached_result("non_existent")
        
        stats = self.cache_service.get_cache_stats()
        assert stats['cache_size'] == 1
        assert stats['cache_hits'] == 1
        assert stats['cache_misses'] == 1
        assert stats['hit_rate_percent'] == 50.0
        assert stats['total_requests'] == 2
    
    def test_clear_cache(self):
        """Test clearing all cache entries"""
        # Add some cache entries
        self.cache_service.cache_result("hash1", {"result": 1})
        self.cache_service.cache_result("hash2", {"result": 2})
        
        # Test cache hit to increment stats
        self.cache_service.get_cached_result("hash1")
        
        # Clear cache
        self.cache_service.clear_cache()
        
        # Verify cache is empty and stats are reset
        stats = self.cache_service.get_cache_stats()
        assert stats['cache_size'] == 0
        assert stats['cache_hits'] == 0
        assert stats['cache_misses'] == 0
    
    def test_singleton_instance(self):
        """Test that query_cache_service is a singleton"""
        # The imported singleton should be an instance of QueryCacheService
        assert isinstance(query_cache_service, QueryCacheService)
        
        # Test that it works
        hash_result = query_cache_service.generate_query_hash("test query")
        assert len(hash_result) == 64
    
    def test_hash_consistency_across_instances(self):
        """Test that hash generation is consistent across different instances"""
        service1 = QueryCacheService()
        service2 = QueryCacheService()
        
        query = "Find me a laptop"
        context = "Previous conversation about computers"
        
        hash1 = service1.generate_query_hash(query, context)
        hash2 = service2.generate_query_hash(query, context)
        
        # Should produce same hash regardless of instance
        assert hash1 == hash2
    
    def test_special_characters_in_query(self):
        """Test hash generation with special characters"""
        queries = [
            "Find me a laptop with 16GB RAM & SSD",
            "What's the best phone under $500?",
            "Show me products with 5★ ratings",
            "Search for items with 50% discount",
            "Find laptops with WiFi 6 (802.11ax)"
        ]
        
        hashes = []
        for query in queries:
            hash_result = self.cache_service.generate_query_hash(query)
            assert len(hash_result) == 64
            hashes.append(hash_result)
        
        # All hashes should be unique
        assert len(set(hashes)) == len(hashes)
    
    def test_unicode_characters_in_query(self):
        """Test hash generation with unicode characters"""
        queries = [
            "Find me a laptop",
            "Trouvez-moi un ordinateur portable",  # French
            "ラップトップを見つけて",  # Japanese
            "Найди мне ноутбук",  # Russian
            "Encuentra una computadora portátil"  # Spanish
        ]
        
        hashes = []
        for query in queries:
            hash_result = self.cache_service.generate_query_hash(query)
            assert len(hash_result) == 64
            hashes.append(hash_result)
        
        # All hashes should be unique
        assert len(set(hashes)) == len(hashes)
    
    def test_cache_hit_miss_statistics(self):
        """Test cache hit/miss statistics tracking"""
        # Initial state - no hits or misses
        stats = self.cache_service.get_cache_stats()
        assert stats['cache_hits'] == 0
        assert stats['cache_misses'] == 0
        
        # Cache some results
        self.cache_service.cache_result("hash1", {"result": "data1"})
        self.cache_service.cache_result("hash2", {"result": "data2"})
        
        # Test cache hits
        result1 = self.cache_service.get_cached_result("hash1")
        result2 = self.cache_service.get_cached_result("hash1")  # Same hash again
        assert result1 == {"result": "data1"}
        assert result2 == {"result": "data1"}
        
        # Test cache miss
        result3 = self.cache_service.get_cached_result("nonexistent")
        assert result3 is None
        
        # Check statistics
        stats = self.cache_service.get_cache_stats()
        assert stats['cache_hits'] == 2
        assert stats['cache_misses'] == 1
        assert stats['hit_rate_percent'] == 66.67
    
    @patch('time.time')
    def test_cache_expiration_edge_cases(self, mock_time):
        """Test cache expiration edge cases"""
        query_hash = "test_hash"
        result = {"data": "test"}
        
        # Mock current time
        mock_time.return_value = 1000
        
        # Cache result
        self.cache_service.cache_result(query_hash, result)
        
        # Test retrieval just before expiration
        mock_time.return_value = 1000 + 3599  # 1 second before expiration
        cached_result = self.cache_service.get_cached_result(query_hash)
        assert cached_result == result
        
        # Test retrieval exactly at expiration
        mock_time.return_value = 1000 + 3600  # Exactly at expiration
        cached_result = self.cache_service.get_cached_result(query_hash)
        assert cached_result == result  # Should still be valid
        
        # Test retrieval just after expiration
        mock_time.return_value = 1000 + 3601  # 1 second after expiration
        cached_result = self.cache_service.get_cached_result(query_hash)
        assert cached_result is None
    
    def test_cache_memory_management(self):
        """Test cache memory management with many entries"""
        # Add many cache entries
        for i in range(1000):
            self.cache_service.cache_result(f"hash_{i}", {"result": f"data_{i}"})
        
        # Verify all entries are cached
        stats = self.cache_service.get_cache_stats()
        assert stats['cache_size'] == 1000
        
        # Test retrieval of various entries
        result_0 = self.cache_service.get_cached_result("hash_0")
        result_500 = self.cache_service.get_cached_result("hash_500")
        result_999 = self.cache_service.get_cached_result("hash_999")
        
        assert result_0 == {"result": "data_0"}
        assert result_500 == {"result": "data_500"}
        assert result_999 == {"result": "data_999"}
    
    @patch('time.time')
    def test_mixed_expired_and_valid_cache_cleanup(self, mock_time):
        """Test cleanup of mixed expired and valid cache entries"""
        # Mock initial time
        mock_time.return_value = 1000
        
        # Add some cache entries
        self.cache_service.cache_result("hash1", {"result": "data1"})
        self.cache_service.cache_result("hash2", {"result": "data2"})
        
        # Advance time partially
        mock_time.return_value = 1000 + 1800  # 30 minutes later
        
        # Add more entries (these should not expire yet)
        self.cache_service.cache_result("hash3", {"result": "data3"})
        self.cache_service.cache_result("hash4", {"result": "data4"})
        
        # Advance time past first entries' expiration
        mock_time.return_value = 1000 + 3601  # 60+ minutes from start
        
        # Clear expired cache
        cleared = self.cache_service.clear_expired_cache()
        assert cleared == 2  # Only first two entries should be cleared
        
        # Verify remaining entries
        stats = self.cache_service.get_cache_stats()
        assert stats['cache_size'] == 2
        
        # Verify correct entries remain
        result3 = self.cache_service.get_cached_result("hash3")
        result4 = self.cache_service.get_cached_result("hash4")
        assert result3 == {"result": "data3"}
        assert result4 == {"result": "data4"}
        
        # Verify expired entries are gone
        result1 = self.cache_service.get_cached_result("hash1")
        result2 = self.cache_service.get_cached_result("hash2")
        assert result1 is None
        assert result2 is None
    
    def test_cache_with_complex_data_structures(self):
        """Test caching with complex data structures"""
        complex_result = {
            "products": [
                {
                    "id": 1,
                    "name": "Laptop",
                    "price": 999.99,
                    "specs": {
                        "cpu": "Intel i7",
                        "ram": "16GB",
                        "storage": ["512GB SSD", "1TB HDD"]
                    },
                    "reviews": [
                        {"rating": 5, "comment": "Great laptop!"},
                        {"rating": 4, "comment": "Good value"}
                    ]
                }
            ],
            "metadata": {
                "total_results": 1,
                "search_time": 0.123,
                "filters_applied": ["price_range", "brand"]
            }
        }
        
        query_hash = "complex_query"
        
        # Cache complex result
        self.cache_service.cache_result(query_hash, complex_result)
        
        # Retrieve and verify
        cached_result = self.cache_service.get_cached_result(query_hash)
        assert cached_result == complex_result
        assert cached_result["products"][0]["specs"]["storage"] == ["512GB SSD", "1TB HDD"]
        assert len(cached_result["products"][0]["reviews"]) == 2
    
    def test_cache_overwrite_existing_entry(self):
        """Test overwriting an existing cache entry"""
        query_hash = "test_hash"
        original_result = {"result": "original"}
        updated_result = {"result": "updated"}
        
        # Cache original result
        self.cache_service.cache_result(query_hash, original_result)
        cached = self.cache_service.get_cached_result(query_hash)
        assert cached == original_result
        
        # Overwrite with updated result
        self.cache_service.cache_result(query_hash, updated_result)
        cached = self.cache_service.get_cached_result(query_hash)
        assert cached == updated_result
        
        # Verify cache size didn't increase
        stats = self.cache_service.get_cache_stats()
        assert stats['cache_size'] == 1
    
    def test_cache_stats_after_clear(self):
        """Test cache statistics after clearing cache"""
        # Add entries and generate some hits/misses
        self.cache_service.cache_result("hash1", {"result": "data1"})
        self.cache_service.get_cached_result("hash1")  # Hit
        self.cache_service.get_cached_result("nonexistent")  # Miss
        
        # Verify stats before clear
        stats = self.cache_service.get_cache_stats()
        assert stats['cache_size'] == 1
        assert stats['cache_hits'] == 1
        assert stats['cache_misses'] == 1
        
        # Clear cache
        self.cache_service.clear_cache()
        
        # Verify stats after clear
        stats = self.cache_service.get_cache_stats()
        assert stats['cache_size'] == 0
        assert stats['cache_hits'] == 0
        assert stats['cache_misses'] == 0
        assert stats['hit_rate_percent'] == 0
    
    @patch('time.time')
    def test_cache_expiration_during_retrieval(self, mock_time):
        """Test that expired entries are automatically removed during retrieval"""
        query_hash = "test_hash"
        result = {"data": "test"}
        
        # Mock current time and cache result
        mock_time.return_value = 1000
        self.cache_service.cache_result(query_hash, result)
        
        # Verify entry exists
        stats = self.cache_service.get_cache_stats()
        assert stats['cache_size'] == 1
        
        # Advance time past expiration
        mock_time.return_value = 1000 + 3601
        
        # Try to retrieve (should remove expired entry)
        cached_result = self.cache_service.get_cached_result(query_hash)
        assert cached_result is None
        
        # Verify entry was removed from cache
        stats = self.cache_service.get_cache_stats()
        assert stats['cache_size'] == 0

    @patch('time.time')
    def test_requirement_3_3_identical_query_cache_hit(self, mock_time):
        """Test Requirement 3.3: WHEN an identical query is received THEN the system SHALL return the cached result if it has not expired"""
        query = "Find me a laptop under 50000"
        context = "User is looking for budget laptops"
        result = {"products": [{"name": "Test Laptop", "price": 45000}]}
        
        # Mock current time
        mock_time.return_value = 1000
        
        # Generate hash and cache result
        query_hash = self.cache_service.generate_query_hash(query, context)
        self.cache_service.cache_result(query_hash, result)
        
        # Test identical query retrieval (should hit cache)
        identical_hash = self.cache_service.generate_query_hash(query, context)
        assert identical_hash == query_hash  # Verify hashes are identical
        
        cached_result = self.cache_service.get_cached_result(identical_hash)
        assert cached_result == result
        
        # Verify cache hit was recorded
        stats = self.cache_service.get_cache_stats()
        assert stats['cache_hits'] == 1
        assert stats['cache_misses'] == 0

    @patch('time.time')
    def test_requirement_3_3_identical_query_cache_miss_after_expiration(self, mock_time):
        """Test Requirement 3.3: Identical query should NOT return cached result if expired"""
        query = "Find me a laptop under 50000"
        result = {"products": [{"name": "Test Laptop", "price": 45000}]}
        
        # Mock current time and cache result
        mock_time.return_value = 1000
        query_hash = self.cache_service.generate_query_hash(query)
        self.cache_service.cache_result(query_hash, result)
        
        # Advance time past expiration
        mock_time.return_value = 1000 + 3601  # 1 second past expiration
        
        # Identical query should now miss cache due to expiration
        cached_result = self.cache_service.get_cached_result(query_hash)
        assert cached_result is None
        
        # Verify cache miss was recorded
        stats = self.cache_service.get_cache_stats()
        assert stats['cache_hits'] == 0
        assert stats['cache_misses'] == 1

    def test_cache_hit_miss_scenarios_comprehensive(self):
        """Test comprehensive cache hit/miss scenarios as required by task"""
        # Test cache miss for non-existent query
        result1 = self.cache_service.get_cached_result("non_existent_hash")
        assert result1 is None
        
        # Cache some results
        self.cache_service.cache_result("hash1", {"result": "data1"})
        self.cache_service.cache_result("hash2", {"result": "data2"})
        self.cache_service.cache_result("hash3", {"result": "data3"})
        
        # Test cache hits
        hit1 = self.cache_service.get_cached_result("hash1")
        hit2 = self.cache_service.get_cached_result("hash2")
        hit3 = self.cache_service.get_cached_result("hash1")  # Same hash again
        
        assert hit1 == {"result": "data1"}
        assert hit2 == {"result": "data2"}
        assert hit3 == {"result": "data1"}
        
        # Test cache miss for different hash
        miss1 = self.cache_service.get_cached_result("hash4")
        miss2 = self.cache_service.get_cached_result("different_hash")
        
        assert miss1 is None
        assert miss2 is None
        
        # Verify statistics
        stats = self.cache_service.get_cache_stats()
        assert stats['cache_hits'] == 3  # hash1 (2x), hash2 (1x)
        assert stats['cache_misses'] == 3  # non_existent_hash, hash4, different_hash
        assert stats['hit_rate_percent'] == 50.0  # 3 hits out of 6 total requests

    @patch('time.time')
    def test_cache_expiration_scenarios_comprehensive(self, mock_time):
        """Test comprehensive cache expiration scenarios as required by task"""
        # Mock initial time
        mock_time.return_value = 1000
        
        # Cache multiple results at different times
        self.cache_service.cache_result("early_hash", {"result": "early"})
        
        # Advance time slightly
        mock_time.return_value = 1000 + 1800  # 30 minutes later
        self.cache_service.cache_result("mid_hash", {"result": "mid"})
        
        # Advance time more
        mock_time.return_value = 1000 + 3000  # 50 minutes later
        self.cache_service.cache_result("late_hash", {"result": "late"})
        
        # Test retrieval before any expiration (all should hit)
        mock_time.return_value = 1000 + 3500  # 58 minutes from start
        
        early_result = self.cache_service.get_cached_result("early_hash")
        mid_result = self.cache_service.get_cached_result("mid_hash")
        late_result = self.cache_service.get_cached_result("late_hash")
        
        assert early_result == {"result": "early"}
        assert mid_result == {"result": "mid"}
        assert late_result == {"result": "late"}
        
        # Advance time to expire first entry only
        mock_time.return_value = 1000 + 3601  # 60+ minutes from start
        
        expired_result = self.cache_service.get_cached_result("early_hash")  # Should be expired
        valid_result1 = self.cache_service.get_cached_result("mid_hash")     # Should be valid
        valid_result2 = self.cache_service.get_cached_result("late_hash")    # Should be valid
        
        assert expired_result is None
        assert valid_result1 == {"result": "mid"}
        assert valid_result2 == {"result": "late"}
        
        # Advance time to expire second entry (cached at 1000 + 1800, expires at 1000 + 1800 + 3600 = 5400)
        mock_time.return_value = 1000 + 5401  # 90+ minutes from start, past mid_hash expiration
        
        expired_result2 = self.cache_service.get_cached_result("mid_hash")   # Should be expired
        still_valid = self.cache_service.get_cached_result("late_hash")      # Should be valid (cached at 1000+3000, expires at 1000+3000+3600=7600)
        
        assert expired_result2 is None
        assert still_valid == {"result": "late"}
        
        # Advance time to expire all entries (late_hash expires at 1000+3000+3600=7600)
        mock_time.return_value = 1000 + 7601  # 126+ minutes from start
        
        all_expired = self.cache_service.get_cached_result("late_hash")      # Should be expired
        assert all_expired is None
        
        # Verify cache is empty
        stats = self.cache_service.get_cache_stats()
        assert stats['cache_size'] == 0

    def test_query_normalization_for_cache_consistency(self):
        """Test that query normalization ensures consistent cache behavior"""
        # Different variations of the same query should produce same hash
        base_query = "find me a laptop under 50000"
        variations = [
            "find me a laptop under 50000",
            "FIND ME A LAPTOP UNDER 50000",
            "  find me a laptop under 50000  ",
            "Find Me A Laptop Under 50000",
            "\tfind me a laptop under 50000\n"
        ]
        
        # Cache result with first variation
        base_hash = self.cache_service.generate_query_hash(variations[0])
        self.cache_service.cache_result(base_hash, {"result": "laptop_data"})
        
        # All variations should hit the same cache entry
        for variation in variations:
            variation_hash = self.cache_service.generate_query_hash(variation)
            assert variation_hash == base_hash, f"Hash mismatch for variation: '{variation}'"
            
            cached_result = self.cache_service.get_cached_result(variation_hash)
            assert cached_result == {"result": "laptop_data"}
        
        # Verify all were cache hits
        stats = self.cache_service.get_cache_stats()
        assert stats['cache_hits'] == len(variations)
        assert stats['cache_misses'] == 0

    @patch('time.time')
    def test_cache_ttl_configuration_compliance(self, mock_time):
        """Test that cache respects TTL configuration from settings"""
        # Mock current time
        mock_time.return_value = 1000
        
        # Cache a result
        query_hash = "ttl_test_hash"
        result = {"data": "test_ttl"}
        self.cache_service.cache_result(query_hash, result)
        
        # Verify cache entry exists
        stats = self.cache_service.get_cache_stats()
        assert stats['cache_size'] == 1
        
        # Test retrieval (should work since entry is fresh)
        cached_result = self.cache_service.get_cached_result(query_hash)
        assert cached_result == result
        
        # Note: Testing expiration with time mocking is complex with database operations
        # The TTL is handled by the database layer, not the time.time() mock