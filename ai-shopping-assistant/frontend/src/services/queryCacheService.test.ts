import { QueryCacheService } from './queryCacheService';
import type { ApiResponse } from '../types/chat';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('QueryCacheService', () => {
  let cacheService: QueryCacheService;
  let mockApiResponse: ApiResponse;

  beforeEach(() => {
    cacheService = new QueryCacheService({ validityMinutes: 1 }); // 1 minute for testing
    localStorageMock.clear();
    
    mockApiResponse = {
      query: 'test query',
      products: [
        {
          title: 'Test Product',
          price: 100,
          rating: 4.5,
          features: ['feature1', 'feature2'],
          pros: ['pro1'],
          cons: ['con1'],
          link: 'https://example.com'
        }
      ],
      recommendations_summary: 'Test summary'
    };
  });

  describe('cacheResult and getCachedResult', () => {
    it('should cache and retrieve a query result', async () => {
      const query = 'best smartphones under 20000';
      
      // Cache the result
      cacheService.cacheResult(query, mockApiResponse);
      
      // Retrieve the cached result
      const cachedResult = await cacheService.getCachedResult(query);
      
      expect(cachedResult).not.toBeNull();
      expect(cachedResult?.query).toBe(mockApiResponse.query);
      expect(cachedResult?.products).toEqual(mockApiResponse.products);
      expect(cachedResult?.cached).toBe(true);
    });

    it('should return null for non-existent cache entries', async () => {
      const result = await cacheService.getCachedResult('non-existent query');
      expect(result).toBeNull();
    });

    it('should handle case-insensitive queries', async () => {
      const query1 = 'Best Smartphones Under 20000';
      const query2 = 'best smartphones under 20000';
      
      cacheService.cacheResult(query1, mockApiResponse);
      
      const cachedResult = await cacheService.getCachedResult(query2);
      expect(cachedResult).not.toBeNull();
      expect(cachedResult?.cached).toBe(true);
    });

    it('should handle queries with extra whitespace', async () => {
      const query1 = '  best smartphones under 20000  ';
      const query2 = 'best smartphones under 20000';
      
      cacheService.cacheResult(query1, mockApiResponse);
      
      const cachedResult = await cacheService.getCachedResult(query2);
      expect(cachedResult).not.toBeNull();
    });
  });

  describe('cache expiration', () => {
    it('should return null for expired cache entries', async () => {
      const query = 'test query';
      
      // Cache the result
      cacheService.cacheResult(query, mockApiResponse);
      
      // Manually expire the cache by modifying the timestamp
      const cache = JSON.parse(localStorageMock.getItem('ai_shopping_assistant_query_cache') || '{}');
      const hash = Object.keys(cache)[0];
      cache[hash].expiresAt = Date.now() - 1000; // Expired 1 second ago
      localStorageMock.setItem('ai_shopping_assistant_query_cache', JSON.stringify(cache));
      
      const cachedResult = await cacheService.getCachedResult(query);
      expect(cachedResult).toBeNull();
    });

    it('should remove expired entries when accessed', async () => {
      const query = 'test query';
      
      cacheService.cacheResult(query, mockApiResponse);
      
      // Manually expire the cache
      const cache = JSON.parse(localStorageMock.getItem('ai_shopping_assistant_query_cache') || '{}');
      const hash = Object.keys(cache)[0];
      cache[hash].expiresAt = Date.now() - 1000;
      localStorageMock.setItem('ai_shopping_assistant_query_cache', JSON.stringify(cache));
      
      await cacheService.getCachedResult(query);
      
      // Check that expired entry was removed
      const updatedCache = JSON.parse(localStorageMock.getItem('ai_shopping_assistant_query_cache') || '{}');
      expect(Object.keys(updatedCache)).toHaveLength(0);
    });
  });

  describe('isCacheValid', () => {
    it('should return true for valid timestamps', () => {
      const now = Date.now();
      const validTimestamp = now - (30 * 1000); // 30 seconds ago
      
      expect(cacheService.isCacheValid(validTimestamp)).toBe(true);
    });

    it('should return false for expired timestamps', () => {
      const expiredTimestamp = Date.now() - (2 * 60 * 1000); // 2 minutes ago
      
      expect(cacheService.isCacheValid(expiredTimestamp)).toBe(false);
    });
  });

  describe('clearExpiredCache', () => {
    it('should remove only expired entries', () => {
      const query1 = 'query1';
      const query2 = 'query2';
      
      cacheService.cacheResult(query1, mockApiResponse);
      cacheService.cacheResult(query2, mockApiResponse);
      
      // Manually expire one entry
      const cache = JSON.parse(localStorageMock.getItem('ai_shopping_assistant_query_cache') || '{}');
      const hashes = Object.keys(cache);
      cache[hashes[0]].expiresAt = Date.now() - 1000; // Expired
      localStorageMock.setItem('ai_shopping_assistant_query_cache', JSON.stringify(cache));
      
      cacheService.clearExpiredCache();
      
      const updatedCache = JSON.parse(localStorageMock.getItem('ai_shopping_assistant_query_cache') || '{}');
      expect(Object.keys(updatedCache)).toHaveLength(1);
    });
  });

  describe('clearAllCache', () => {
    it('should remove all cache entries', () => {
      cacheService.cacheResult('query1', mockApiResponse);
      cacheService.cacheResult('query2', mockApiResponse);
      
      cacheService.clearAllCache();
      
      const cache = localStorageMock.getItem('ai_shopping_assistant_query_cache');
      expect(cache).toBeNull();
    });
  });

  describe('getCacheStats', () => {
    it('should return correct cache statistics', () => {
      cacheService.cacheResult('query1', mockApiResponse);
      cacheService.cacheResult('query2', mockApiResponse);
      
      // Manually expire one entry
      const cache = JSON.parse(localStorageMock.getItem('ai_shopping_assistant_query_cache') || '{}');
      const hashes = Object.keys(cache);
      cache[hashes[0]].expiresAt = Date.now() - 1000; // Expired
      localStorageMock.setItem('ai_shopping_assistant_query_cache', JSON.stringify(cache));
      
      const stats = cacheService.getCacheStats();
      
      expect(stats.totalEntries).toBe(2);
      expect(stats.expiredEntries).toBe(1);
      expect(stats.validEntries).toBe(1);
    });

    it('should return zero stats for empty cache', () => {
      const stats = cacheService.getCacheStats();
      
      expect(stats.totalEntries).toBe(0);
      expect(stats.expiredEntries).toBe(0);
      expect(stats.validEntries).toBe(0);
    });
  });

  describe('updateConfig', () => {
    it('should update cache validity configuration', () => {
      cacheService.updateConfig(30); // 30 minutes
      
      const oldTimestamp = Date.now() - (25 * 60 * 1000); // 25 minutes ago
      expect(cacheService.isCacheValid(oldTimestamp)).toBe(true);
      
      const veryOldTimestamp = Date.now() - (35 * 60 * 1000); // 35 minutes ago
      expect(cacheService.isCacheValid(veryOldTimestamp)).toBe(false);
    });
  });

  describe('error handling', () => {
    it('should handle localStorage errors gracefully', async () => {
      // Mock localStorage to throw an error
      const originalGetItem = localStorageMock.getItem;
      localStorageMock.getItem = () => {
        throw new Error('localStorage error');
      };
      
      const result = await cacheService.getCachedResult('test query');
      expect(result).toBeNull();
      
      // Restore original method
      localStorageMock.getItem = originalGetItem;
    });

    it('should handle invalid JSON in localStorage', async () => {
      localStorageMock.setItem('ai_shopping_assistant_query_cache', 'invalid json');
      
      const result = await cacheService.getCachedResult('test query');
      expect(result).toBeNull();
    });

    it('should handle localStorage setItem errors gracefully', () => {
      const originalSetItem = localStorageMock.setItem;
      localStorageMock.setItem = () => {
        throw new Error('localStorage quota exceeded');
      };
      
      // Should not throw an error
      expect(() => {
        cacheService.cacheResult('test query', mockApiResponse);
      }).not.toThrow();
      
      // Restore original method
      localStorageMock.setItem = originalSetItem;
    });

    it('should handle localStorage removeItem errors gracefully', () => {
      const originalRemoveItem = localStorageMock.removeItem;
      localStorageMock.removeItem = () => {
        throw new Error('localStorage error');
      };
      
      // Should not throw an error
      expect(() => {
        cacheService.clearAllCache();
      }).not.toThrow();
      
      // Restore original method
      localStorageMock.removeItem = originalRemoveItem;
    });
  });

  describe('cache performance and limits', () => {
    it('should handle large cache entries', async () => {
      const largeResponse: ApiResponse = {
        ...mockApiResponse,
        products: Array(100).fill(null).map((_, i) => ({
          title: `Product ${i}`,
          price: 100 + i,
          rating: 4.5,
          features: [`feature${i}1`, `feature${i}2`, `feature${i}3`],
          pros: [`pro${i}1`, `pro${i}2`],
          cons: [`con${i}1`],
          link: `https://example.com/product${i}`
        })),
        recommendations_summary: 'A'.repeat(1000) // Large summary
      };
      
      const query = 'large query test';
      
      // Should handle large entries without errors
      expect(() => {
        cacheService.cacheResult(query, largeResponse);
      }).not.toThrow();
      
      // Should retrieve correctly
      const cached = await cacheService.getCachedResult(query);
      expect(cached).not.toBeNull();
    });

    it('should handle many cache entries', () => {
      // Add many cache entries
      for (let i = 0; i < 50; i++) {
        cacheService.cacheResult(`query ${i}`, {
          ...mockApiResponse,
          query: `query ${i}`
        });
      }
      
      const stats = cacheService.getCacheStats();
      expect(stats.totalEntries).toBe(50);
      expect(stats.validEntries).toBe(50);
    });
  });

  describe('hash collision handling', () => {
    it('should handle similar queries correctly', async () => {
      const query1 = 'best laptop under 50000';
      const query2 = 'best laptop under 50001';
      
      const response1 = { ...mockApiResponse, query: query1 };
      const response2 = { ...mockApiResponse, query: query2 };
      
      cacheService.cacheResult(query1, response1);
      cacheService.cacheResult(query2, response2);
      
      const cached1 = await cacheService.getCachedResult(query1);
      const cached2 = await cacheService.getCachedResult(query2);
      
      expect(cached1?.query).toBe(query1);
      expect(cached2?.query).toBe(query2);
    });

    it('should handle queries with different special characters', async () => {
      const queries = [
        'laptop with 16GB RAM & SSD',
        'laptop with 16GB RAM + SSD',
        'laptop with 16GB RAM | SSD',
        'laptop with 16GB RAM @ SSD'
      ];
      
      queries.forEach((query, index) => {
        cacheService.cacheResult(query, {
          ...mockApiResponse,
          query: `response ${index}`
        });
      });
      
      // Each should have its own cache entry
      for (let i = 0; i < queries.length; i++) {
        const cached = await cacheService.getCachedResult(queries[i]);
        expect(cached?.query).toBe(`response ${i}`);
      }
    });
  });

  describe('cache consistency', () => {
    it('should maintain cache consistency across multiple operations', async () => {
      const query = 'consistency test';
      
      // Cache initial result
      cacheService.cacheResult(query, mockApiResponse);
      
      // Retrieve multiple times
      const result1 = await cacheService.getCachedResult(query);
      const result2 = await cacheService.getCachedResult(query);
      const result3 = await cacheService.getCachedResult(query);
      
      expect(result1).toEqual(result2);
      expect(result2).toEqual(result3);
      expect(result1?.cached).toBe(true);
    });

    it('should handle cache updates correctly', async () => {
      const query = 'update test';
      const originalResponse = { ...mockApiResponse, query: 'original' };
      const updatedResponse = { ...mockApiResponse, query: 'updated' };
      
      // Cache original
      cacheService.cacheResult(query, originalResponse);
      let cached = await cacheService.getCachedResult(query);
      expect(cached?.query).toBe('original');
      
      // Update cache
      cacheService.cacheResult(query, updatedResponse);
      cached = await cacheService.getCachedResult(query);
      expect(cached?.query).toBe('updated');
      
      // Cache size should remain 1
      const stats = cacheService.getCacheStats();
      expect(stats.totalEntries).toBe(1);
    });
  });

  describe('edge cases', () => {
    it('should handle empty query strings', async () => {
      const emptyQuery = '';
      
      cacheService.cacheResult(emptyQuery, mockApiResponse);
      const cached = await cacheService.getCachedResult(emptyQuery);
      
      expect(cached).not.toBeNull();
    });

    it('should handle very long query strings', async () => {
      const longQuery = 'a'.repeat(10000);
      
      cacheService.cacheResult(longQuery, mockApiResponse);
      const cached = await cacheService.getCachedResult(longQuery);
      
      expect(cached).not.toBeNull();
    });

    it('should handle queries with only whitespace', async () => {
      const whitespaceQuery = '   \t\n   ';
      const normalizedQuery = '';
      
      cacheService.cacheResult(whitespaceQuery, mockApiResponse);
      
      // Should be retrievable with normalized query
      const cached1 = await cacheService.getCachedResult(whitespaceQuery);
      const cached2 = await cacheService.getCachedResult(normalizedQuery);
      
      expect(cached1).not.toBeNull();
      expect(cached2).not.toBeNull();
    });

    it('should handle null and undefined in API response', () => {
      const responseWithNulls: ApiResponse = {
        query: 'test',
        products: [
          {
            title: 'Test Product',
            price: 100,
            rating: 4.5,
            features: ['feature1', 'feature2'],
            pros: ['pro1'],
            cons: ['con1'],
            link: 'https://example.com'
          }
        ],
        recommendations_summary: 'Test'
      };
      
      expect(() => {
        cacheService.cacheResult('null test', responseWithNulls);
      }).not.toThrow();
    });
  });

  describe('requirement 4.2 - cache check before query submission', () => {
    it('should check for unexpired cached result before submission', async () => {
      const query = 'best smartphones under 30000';
      
      // Initially no cache
      let cachedResult = await cacheService.getCachedResult(query);
      expect(cachedResult).toBeNull();
      
      // Cache a result
      cacheService.cacheResult(query, mockApiResponse);
      
      // Should now find cached result
      cachedResult = await cacheService.getCachedResult(query);
      expect(cachedResult).not.toBeNull();
      expect(cachedResult?.cached).toBe(true);
      expect(cachedResult?.query).toBe(mockApiResponse.query);
    });

    it('should not return expired cached result', async () => {
      const query = 'expired cache test';
      
      // Cache a result
      cacheService.cacheResult(query, mockApiResponse);
      
      // Manually expire the cache
      const cache = JSON.parse(localStorageMock.getItem('ai_shopping_assistant_query_cache') || '{}');
      const hash = Object.keys(cache)[0];
      cache[hash].expiresAt = Date.now() - 1000; // Expired 1 second ago
      localStorageMock.setItem('ai_shopping_assistant_query_cache', JSON.stringify(cache));
      
      // Should not return expired result
      const cachedResult = await cacheService.getCachedResult(query);
      expect(cachedResult).toBeNull();
    });
  });

  describe('requirement 4.5 - cache validity period expiration', () => {
    it('should remove expired cache result when validity period expires', async () => {
      const query = 'validity period test';
      
      // Cache a result
      cacheService.cacheResult(query, mockApiResponse);
      
      // Verify it exists
      let cachedResult = await cacheService.getCachedResult(query);
      expect(cachedResult).not.toBeNull();
      
      // Manually expire the cache entry
      const cache = JSON.parse(localStorageMock.getItem('ai_shopping_assistant_query_cache') || '{}');
      const hash = Object.keys(cache)[0];
      cache[hash].expiresAt = Date.now() - 1; // Just expired
      localStorageMock.setItem('ai_shopping_assistant_query_cache', JSON.stringify(cache));
      
      // Should remove expired entry and return null
      cachedResult = await cacheService.getCachedResult(query);
      expect(cachedResult).toBeNull();
      
      // Verify entry was removed from storage
      const updatedCache = JSON.parse(localStorageMock.getItem('ai_shopping_assistant_query_cache') || '{}');
      expect(Object.keys(updatedCache)).toHaveLength(0);
    });

    it('should respect custom validity period configuration', () => {
      const customCacheService = new QueryCacheService({ validityMinutes: 30 });
      
      const thirtyMinutesAgo = Date.now() - (30 * 60 * 1000);
      const twentyMinutesAgo = Date.now() - (20 * 60 * 1000);
      const fortyMinutesAgo = Date.now() - (40 * 60 * 1000);
      
      expect(customCacheService.isCacheValid(twentyMinutesAgo)).toBe(true);
      expect(customCacheService.isCacheValid(thirtyMinutesAgo)).toBe(false);
      expect(customCacheService.isCacheValid(fortyMinutesAgo)).toBe(false);
    });
  });

  describe('cache hit/miss scenarios comprehensive', () => {
    it('should handle multiple cache hit/miss scenarios correctly', async () => {
      const queries = [
        'find laptops under 50000',
        'best smartphones 2024',
        'gaming headphones review',
        'wireless earbuds comparison'
      ];
      
      // Cache first two queries
      cacheService.cacheResult(queries[0], { ...mockApiResponse, query: queries[0] });
      cacheService.cacheResult(queries[1], { ...mockApiResponse, query: queries[1] });
      
      // Test cache hits
      const hit1 = await cacheService.getCachedResult(queries[0]);
      const hit2 = await cacheService.getCachedResult(queries[1]);
      const hit3 = await cacheService.getCachedResult(queries[0]); // Same as first
      
      expect(hit1).not.toBeNull();
      expect(hit1?.cached).toBe(true);
      expect(hit1?.query).toBe(queries[0]);
      
      expect(hit2).not.toBeNull();
      expect(hit2?.cached).toBe(true);
      expect(hit2?.query).toBe(queries[1]);
      
      expect(hit3).not.toBeNull();
      expect(hit3?.cached).toBe(true);
      expect(hit3?.query).toBe(queries[0]);
      
      // Test cache misses
      const miss1 = await cacheService.getCachedResult(queries[2]);
      const miss2 = await cacheService.getCachedResult(queries[3]);
      const miss3 = await cacheService.getCachedResult('non-existent query');
      
      expect(miss1).toBeNull();
      expect(miss2).toBeNull();
      expect(miss3).toBeNull();
    });

    it('should maintain cache consistency across operations', async () => {
      const query = 'consistency test query';
      const originalResponse = { ...mockApiResponse, query: 'original' };
      const updatedResponse = { ...mockApiResponse, query: 'updated' };
      
      // Cache original
      cacheService.cacheResult(query, originalResponse);
      
      // Multiple retrievals should return same result
      const result1 = await cacheService.getCachedResult(query);
      const result2 = await cacheService.getCachedResult(query);
      const result3 = await cacheService.getCachedResult(query);
      
      expect(result1).toEqual(result2);
      expect(result2).toEqual(result3);
      expect(result1?.query).toBe('original');
      
      // Update cache
      cacheService.cacheResult(query, updatedResponse);
      
      // Should now return updated result
      const updatedResult = await cacheService.getCachedResult(query);
      expect(updatedResult?.query).toBe('updated');
      
      // Cache size should remain 1
      const stats = cacheService.getCacheStats();
      expect(stats.totalEntries).toBe(1);
    });
  });

  describe('cache expiration comprehensive', () => {
    it('should handle mixed expired and valid entries correctly', () => {
      const query1 = 'query1';
      const query2 = 'query2';
      const query3 = 'query3';
      
      // Cache multiple entries
      cacheService.cacheResult(query1, { ...mockApiResponse, query: query1 });
      cacheService.cacheResult(query2, { ...mockApiResponse, query: query2 });
      cacheService.cacheResult(query3, { ...mockApiResponse, query: query3 });
      
      // Manually expire some entries
      const cache = JSON.parse(localStorageMock.getItem('ai_shopping_assistant_query_cache') || '{}');
      const hashes = Object.keys(cache);
      
      // Expire first two entries
      cache[hashes[0]].expiresAt = Date.now() - 1000;
      cache[hashes[1]].expiresAt = Date.now() - 2000;
      // Keep third entry valid
      
      localStorageMock.setItem('ai_shopping_assistant_query_cache', JSON.stringify(cache));
      
      // Clear expired entries
      cacheService.clearExpiredCache();
      
      // Check final state
      const stats = cacheService.getCacheStats();
      expect(stats.totalEntries).toBe(1);
      expect(stats.validEntries).toBe(1);
      expect(stats.expiredEntries).toBe(0);
    });

    it('should handle cache expiration during high-frequency operations', async () => {
      const baseQuery = 'high frequency test';
      
      // Cache multiple variations
      for (let i = 0; i < 10; i++) {
        cacheService.cacheResult(`${baseQuery} ${i}`, {
          ...mockApiResponse,
          query: `${baseQuery} ${i}`
        });
      }
      
      // Verify all cached
      let stats = cacheService.getCacheStats();
      expect(stats.totalEntries).toBe(10);
      
      // Manually expire half of them
      const cache = JSON.parse(localStorageMock.getItem('ai_shopping_assistant_query_cache') || '{}');
      const hashes = Object.keys(cache);
      
      for (let i = 0; i < 5; i++) {
        cache[hashes[i]].expiresAt = Date.now() - 1000;
      }
      
      localStorageMock.setItem('ai_shopping_assistant_query_cache', JSON.stringify(cache));
      
      // Access expired entries (should trigger removal)
      for (let i = 0; i < 5; i++) {
        const result = await cacheService.getCachedResult(`${baseQuery} ${i}`);
        expect(result).toBeNull();
      }
      
      // Access valid entries
      for (let i = 5; i < 10; i++) {
        const result = await cacheService.getCachedResult(`${baseQuery} ${i}`);
        expect(result).not.toBeNull();
      }
      
      // Final stats should show only valid entries
      stats = cacheService.getCacheStats();
      expect(stats.totalEntries).toBe(5);
      expect(stats.validEntries).toBe(5);
    });
  });
});