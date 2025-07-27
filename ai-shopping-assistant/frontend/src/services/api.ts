import type { ApiResponse, ChatMessage } from '../types/chat';
import { API_BASE_URL } from '../config';
import { ActionTrackingService } from './actionTrackingService';
import { ActionType } from './userActionService';
import { unifiedAuthService } from './unifiedAuthService';
import { queryCacheService } from './queryCacheService';

// Define error types
export const ApiErrorType = {
  NETWORK: 'network',
  SERVER: 'server',
  TIMEOUT: 'timeout',
  PARSE: 'parse',
  UNKNOWN: 'unknown',
} as const;

export type ApiErrorType = typeof ApiErrorType[keyof typeof ApiErrorType];

// Custom API error class
export class ApiError extends Error {
  type: ApiErrorType;
  statusCode?: number;

  constructor(message: string, type: ApiErrorType, statusCode?: number) {
    super(message);
    this.name = 'ApiError';
    this.type = type;
    this.statusCode = statusCode;
  }
}

// Request timeout helper
const timeoutPromise = (ms: number): Promise<never> => {
  return new Promise((_, reject) => {
    setTimeout(() => reject(new ApiError('Request timed out', ApiErrorType.TIMEOUT)), ms);
  });
};

/**
 * Service for handling API communication with the backend
 */
export const ApiService = {
  /**
   * Send a query to the backend API
   * @param query The user's query text
   * @param conversationHistory Previous messages in the conversation
   * @param timeout Timeout in milliseconds (default: 10000)
   * @returns Promise with the API response
   */
  async sendQuery(
    query: string,
    conversationHistory: ChatMessage[],
    timeout: number = 10000
  ): Promise<ApiResponse> {
    try {
      // Check cache first before validating credits or making API call
      const cachedResult = await queryCacheService.getCachedResult(query);
      if (cachedResult) {
        console.log('Returning cached result for query:', query);
        return cachedResult;
      }

      // Check if the user can perform this action
      if (!unifiedAuthService.isAuthenticated() && !ActionTrackingService.isActionAllowed(ActionType.CHAT)) {
        throw new ApiError(
          'Message credit limit reached. Please log in to continue.',
          ApiErrorType.SERVER,
          403
        );
      }

      // Track this action only for guest users (only if not cached)
      if (!unifiedAuthService.isAuthenticated()) {
        ActionTrackingService.trackApiAction(ActionType.CHAT);
      }

      // Get headers with authentication if available
      const headers = await this.getAuthHeaders();

      // Create a request with timeout
      const fetchPromise = fetch(`${API_BASE_URL}/query`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          query,
          conversation_history: conversationHistory.map(msg => ({
            text: msg.text,
            sender: msg.sender,
            timestamp: msg.timestamp.toISOString(),
          })),
        }),
      });

      // Race between fetch and timeout
      const response = await Promise.race([fetchPromise, timeoutPromise(timeout)]);
      if (!response.ok) {
        // Handle authentication errors
        if (response.status === 401 && unifiedAuthService.isAuthenticated()) {
          // Token might be expired - Auth0 React SDK handles refresh automatically
          // Just retry once with a fresh token
          const retryHeaders = await this.getAuthHeaders();
          const retryResponse = await fetch(`${API_BASE_URL}/query`, {
            method: 'POST',
            headers: retryHeaders,
            body: JSON.stringify({
              query,
              conversation_history: conversationHistory.map(msg => ({
                text: msg.text,
                sender: msg.sender,
                timestamp: msg.timestamp.toISOString(),
              })),
            }),
          });

          if (retryResponse.ok) {
            const result = await retryResponse.json();
            queryCacheService.cacheResult(query, result);
            return result;
          }
        }

        const errorData = await response.json().catch(() => ({}));
        throw new ApiError(
          errorData.detail || `API error: ${response.status}`,
          ApiErrorType.SERVER,
          response.status
        );
      }

      try {
        const result = await response.json();

        // Cache the successful result
        queryCacheService.cacheResult(query, result);

        return result;
      } catch (error) {
        throw new ApiError('Failed to parse API response', ApiErrorType.PARSE);
      }
    } catch (error) {
      console.error('API request failed:', error);

      // Rethrow ApiError instances
      if (error instanceof ApiError) {
        throw error;
      }

      // Convert other errors to ApiError
      throw new ApiError(
        error instanceof Error ? error.message : 'Unknown error occurred',
        ApiErrorType.NETWORK
      );
    }
  },

  /**
   * Send a query with retry logic
   * @param query The user's query text
   * @param conversationHistory Previous messages in the conversation
   * @param maxRetries Maximum number of retries (default: 3)
   * @param timeout Timeout in milliseconds (default: 15000)
   * @returns Promise with the API response
   */
  async sendQueryWithRetry(
    query: string,
    conversationHistory: ChatMessage[],
    maxRetries: number = 1,
    timeout: number = 15000
  ): Promise<ApiResponse> {
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        // Add exponential backoff for retries
        if (attempt > 0) {
          const backoffTime = Math.min(1000 * Math.pow(2, attempt - 1), 8000);
          console.log(`Retrying in ${backoffTime}ms (attempt ${attempt} of ${maxRetries})...`);
          await new Promise(resolve => setTimeout(resolve, backoffTime));
        }

        // Increase timeout for subsequent attempts
        const adjustedTimeout = timeout * (1 + attempt * 0.5);

        return await this.sendQuery(query, conversationHistory, adjustedTimeout);
      } catch (error) {
        console.error(`API request attempt ${attempt + 1} failed:`, error);
        lastError = error instanceof Error ? error : new Error('Unknown error');

        // Don't retry on certain error types
        if (
          error instanceof ApiError &&
          (
            error.type === ApiErrorType.SERVER &&
            error.statusCode !== 503 &&
            error.statusCode !== 429 &&
            error.statusCode !== 500 &&
            error.statusCode !== 401 // Allow retry on authentication errors
          )
        ) {
          throw error;
        }

        // If this is the last attempt, throw the error
        if (attempt === maxRetries) {
          throw lastError || new ApiError('Failed after multiple retries', ApiErrorType.UNKNOWN);
        }
      }
    }

    // If we've exhausted all retries
    throw lastError || new ApiError('Failed after multiple retries', ApiErrorType.UNKNOWN);
  },

  /**
   * Helper method to format error messages for display
   * @param error The error object
   * @returns User-friendly error message
   */
  /**
   * Gets authentication headers for API requests
   * @returns Headers object with authentication token if available
   */
  async getAuthHeaders(): Promise<Record<string, string>> {
    return await unifiedAuthService.getAuthHeaders();
  },

  getErrorMessage(error: unknown): string {
    if (error instanceof ApiError) {
      switch (error.type) {
        case ApiErrorType.NETWORK:
          return 'Network error. Please check your internet connection and try again.';
        case ApiErrorType.SERVER:
          // Special handling for guest limit errors
          if (error.statusCode === 403 && error.message.includes('Message credit limit')) {
            return 'You have reached the message credit limit. Please log in to continue using the assistant.';
          }
          // Special handling for authentication errors
          if (error.statusCode === 401) {
            return 'Authentication error. Please log in again.';
          }
          return `Server error (${error.statusCode}). Please try again later.`;
        case ApiErrorType.TIMEOUT:
          return 'Request timed out. Please try again.';
        case ApiErrorType.PARSE:
          return 'Error processing the response. Please try again.';
        default:
          return 'An unexpected error occurred. Please try again.';
      }
    }

    return error instanceof Error
      ? `Error: ${error.message}`
      : 'An unknown error occurred. Please try again.';
  }
};