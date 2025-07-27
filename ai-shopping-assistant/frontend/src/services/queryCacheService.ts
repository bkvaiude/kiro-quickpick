import type { ApiResponse } from '../types/chat';

// Storage key for query cache
const CACHE_STORAGE_KEY = 'ai_shopping_assistant_query_cache';

// Default cache validity in minutes (can be overridden by config)
const DEFAULT_CACHE_VALIDITY_MINUTES = 60;

export interface CacheEntry {
  queryHash: string;
  result: ApiResponse;
  timestamp: number;
  expiresAt: number;
}

export interface CacheConfig {
  validityMinutes?: number;
}

/**
 * Service for managing client-side query caching
 * Implements local storage-based cache with TTL functionality
 */
export class QueryCacheService {
  private validityMinutes: number;

  constructor(config: CacheConfig = {}) {
    this.validityMinutes = config.validityMinutes || DEFAULT_CACHE_VALIDITY_MINUTES;
  }

  /**
   * Generate a consistent hash for a query string
   * @param query The query string to hash
   * @returns A hash string for the query
   */
  private generateQueryHash(query: string): string {
    // Simple hash function for query strings
    // Normalize the query by trimming and converting to lowercase
    const normalizedQuery = query.trim().toLowerCase();
    
    let hash = 0;
    for (let i = 0; i < normalizedQuery.length; i++) {
      const char = normalizedQuery.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    
    return Math.abs(hash).toString(36);
  }

  /**
   * Get cached result for a query if it exists and is not expired
   * @param query The query string to look up
   * @returns Cached result or null if not found or expired
   */
  async getCachedResult(query: string): Promise<ApiResponse | null> {
    try {
      const queryHash = this.generateQueryHash(query);
      const cache = this.loadCache();
      const entry = cache[queryHash];

      if (!entry) {
        return null;
      }

      // Check if cache entry is expired
      const now = Date.now();
      if (now > entry.expiresAt) {
        // Remove expired entry
        delete cache[queryHash];
        this.saveCache(cache);
        return null;
      }

      // Return cached result with cache indicator
      return {
        ...entry.result,
        cached: true
      };
    } catch (error) {
      console.error('Error retrieving cached result:', error);
      return null;
    }
  }

  /**
   * Cache a query result with TTL
   * @param query The query string
   * @param result The API response to cache
   */
  cacheResult(query: string, result: ApiResponse): void {
    try {
      const queryHash = this.generateQueryHash(query);
      const now = Date.now();
      const expiresAt = now + (this.validityMinutes * 60 * 1000);

      const entry: CacheEntry = {
        queryHash,
        result: {
          ...result,
          cached: false // Store original result without cache indicator
        },
        timestamp: now,
        expiresAt
      };

      const cache = this.loadCache();
      cache[queryHash] = entry;
      
      this.saveCache(cache);
    } catch (error) {
      console.error('Error caching result:', error);
    }
  }

  /**
   * Check if cache is valid for a given timestamp
   * @param timestamp The timestamp to check
   * @returns True if cache is still valid, false otherwise
   */
  isCacheValid(timestamp: number): boolean {
    const now = Date.now();
    const validityMs = this.validityMinutes * 60 * 1000;
    return (now - timestamp) < validityMs;
  }

  /**
   * Clear expired cache entries
   */
  clearExpiredCache(): void {
    try {
      const cache = this.loadCache();
      const now = Date.now();
      let hasExpiredEntries = false;

      for (const [hash, entry] of Object.entries(cache)) {
        if (now > entry.expiresAt) {
          delete cache[hash];
          hasExpiredEntries = true;
        }
      }

      if (hasExpiredEntries) {
        this.saveCache(cache);
      }
    } catch (error) {
      console.error('Error clearing expired cache:', error);
    }
  }

  /**
   * Clear all cached queries
   */
  clearAllCache(): void {
    try {
      localStorage.removeItem(CACHE_STORAGE_KEY);
    } catch (error) {
      console.error('Error clearing all cache:', error);
    }
  }

  /**
   * Get cache statistics
   * @returns Object with cache statistics
   */
  getCacheStats(): { totalEntries: number; expiredEntries: number; validEntries: number } {
    try {
      const cache = this.loadCache();
      const now = Date.now();
      let expiredEntries = 0;
      let validEntries = 0;

      for (const entry of Object.values(cache)) {
        if (now > entry.expiresAt) {
          expiredEntries++;
        } else {
          validEntries++;
        }
      }

      return {
        totalEntries: Object.keys(cache).length,
        expiredEntries,
        validEntries
      };
    } catch (error) {
      console.error('Error getting cache stats:', error);
      return { totalEntries: 0, expiredEntries: 0, validEntries: 0 };
    }
  }

  /**
   * Load cache from local storage
   * @returns Cache object or empty object if not found
   */
  private loadCache(): Record<string, CacheEntry> {
    try {
      const cacheData = localStorage.getItem(CACHE_STORAGE_KEY);
      if (!cacheData) {
        return {};
      }

      return JSON.parse(cacheData);
    } catch (error) {
      console.error('Error loading cache from local storage:', error);
      return {};
    }
  }

  /**
   * Save cache to local storage
   * @param cache The cache object to save
   */
  private saveCache(cache: Record<string, CacheEntry>): void {
    try {
      localStorage.setItem(CACHE_STORAGE_KEY, JSON.stringify(cache));
    } catch (error) {
      console.error('Error saving cache to local storage:', error);
    }
  }

  /**
   * Update cache validity configuration
   * @param validityMinutes New validity period in minutes
   */
  updateConfig(validityMinutes: number): void {
    this.validityMinutes = validityMinutes;
  }
}

// Create a default instance
export const queryCacheService = new QueryCacheService();