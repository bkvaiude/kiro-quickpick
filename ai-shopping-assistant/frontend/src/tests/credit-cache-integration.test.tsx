/**
 * Integration tests for credit system and caching mechanisms.
 * Tests the end-to-end flow of credit management and query caching across frontend and backend.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, beforeEach, describe, test, expect } from 'vitest';
import App from '../App';
import { ChatProvider } from '../context/ChatContext';
import { ThemeProvider } from '../components/theme/ThemeProvider';
import { queryCacheService } from '../services/queryCacheService';

// Mock scrollIntoView
Element.prototype.scrollIntoView = vi.fn();

// Mock the API service
vi.mock('../services/api.ts', () => ({
  ApiService: {
    sendQueryWithRetry: vi.fn(),
    getErrorMessage: vi.fn().mockReturnValue('An error occurred'),
    sendQuery: vi.fn(),
    getCredits: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    constructor(message: string, type: string) {
      super(message);
      this.name = 'ApiError';
      this.type = type;
    }
    type: string;
  },
  ApiErrorType: {
    NETWORK: 'network',
    SERVER: 'server',
    TIMEOUT: 'timeout',
    PARSE: 'parse',
    UNKNOWN: 'unknown',
    CREDITS_EXHAUSTED: 'credits_exhausted',
  }
}));

// Mock the credit service
vi.mock('../services/creditService', () => ({
  CreditService: {
    getCreditStatus: vi.fn(),
    hasCredits: vi.fn(),
    getCreditDisplayInfo: vi.fn(),
  },
}));

// Mock localStorage service
vi.mock('../services/localStorage', () => ({
  LocalStorageService: {
    saveMessages: vi.fn(),
    loadMessages: vi.fn().mockReturnValue([]),
    saveConversationContext: vi.fn(),
    loadConversationContext: vi.fn().mockReturnValue(null),
    clearChatData: vi.fn(),
    isConversationExpired: vi.fn().mockReturnValue(false),
    extractProductCriteria: vi.fn().mockReturnValue({})
  }
}));

describe('Credit and Cache Integration Tests', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    vi.clearAllMocks();
    
    // Clear local storage
    localStorage.clear();
    
    // Clear query cache
    queryCacheService.clearAllCache();
  });

  test('End-to-end credit flow: guest user credit deduction and exhaustion', async () => {
    const { ApiService } = await import('../services/api');
    const { CreditService } = await import('../services/creditService');
    
    // Mock API responses for queries
    const mockQueryResponse = {
      query: 'Find me a phone under 15000',
      products: [
        {
          title: 'Test Phone',
          price: 12000,
          rating: 4.5,
          features: ['8GB RAM', '128GB Storage'],
          pros: ['Good camera'],
          cons: ['Average battery'],
          link: 'https://example.com/phone'
        }
      ],
      recommendations_summary: 'Test phone recommendation',
      cached: false
    };

    // Set up credit progression: 10 -> 9 -> 8 -> ... -> 0
    let currentCredits = 10;
    vi.mocked(ApiService.sendQueryWithRetry).mockImplementation(async () => {
      if (currentCredits > 0) {
        currentCredits--;
        return mockQueryResponse;
      } else {
        const error = new Error('Insufficient credits');
        (error as any).type = 'credits_exhausted';
        throw error;
      }
    });

    vi.mocked(CreditService.getCreditStatus).mockImplementation(async () => ({
      available_credits: currentCredits,
      max_credits: 10,
      is_guest: true,
      can_reset: false,
    }));

    vi.mocked(CreditService.hasCredits).mockImplementation(async () => currentCredits > 0);

    // Render the app
    render(
      <ThemeProvider defaultTheme="light" storageKey="ui-theme">
        <ChatProvider>
          <App />
        </ChatProvider>
      </ThemeProvider>
    );

    // Verify initial credit display shows "Message Credits"
    await waitFor(() => {
      expect(screen.getByText(/Message Credits/)).toBeInTheDocument();
    });

    const inputs = screen.getAllByPlaceholderText('Ask about products...');
    const input = inputs[0]; // Use the first input (main chat input)
    const form = input.closest('form');

    // Test multiple queries to exhaust credits
    for (let i = 10; i > 0; i--) {
      // Submit query
      fireEvent.change(input, { target: { value: `Query ${11 - i}` } });
      fireEvent.submit(form!);

      // Wait for response
      await waitFor(() => {
        expect(screen.queryByText('Thinking...')).not.toBeInTheDocument();
      });

      // Verify credit count decreased
      await waitFor(() => {
        expect(screen.getByText(new RegExp(`${i - 1}.*remaining`))).toBeInTheDocument();
      });
    }

    // Now credits should be exhausted - input should be disabled
    await waitFor(() => {
      expect(input).toBeDisabled();
    });

    // Verify exhaustion message is shown
    expect(screen.getByText(/no credits left/i)).toBeInTheDocument();
    expect(screen.getByText(/register/i)).toBeInTheDocument();

    // Try to submit another query - should fail
    fireEvent.change(input, { target: { value: 'This should fail' } });
    fireEvent.submit(form!);

    // Verify error message for credit exhaustion
    await waitFor(() => {
      expect(screen.getByText(/insufficient credits/i)).toBeInTheDocument();
    });
  });

  test('End-to-end caching flow: client-side and server-side cache integration (Requirements 4.3, 4.4)', async () => {
    const { ApiService } = await import('../services/api');
    const { CreditService } = await import('../services/creditService');
    
    const query = 'Find me a laptop under 50000';
    const mockQueryResponse = {
      query,
      products: [
        {
          title: 'Test Laptop',
          price: 45000,
          rating: 4.2,
          features: ['16GB RAM', '512GB SSD'],
          pros: ['Fast performance'],
          cons: ['Heavy weight'],
          link: 'https://example.com/laptop'
        }
      ],
      recommendations_summary: 'Great laptop for work',
      cached: false
    };

    const mockCachedResponse = {
      ...mockQueryResponse,
      cached: true
    };

    // First call returns fresh result, second call returns cached result
    vi.mocked(ApiService.sendQueryWithRetry)
      .mockResolvedValueOnce(mockQueryResponse)
      .mockResolvedValueOnce(mockCachedResponse);

    vi.mocked(CreditService.getCreditStatus).mockResolvedValue({
      available_credits: 10,
      max_credits: 10,
      is_guest: true,
      can_reset: false,
    });

    vi.mocked(CreditService.hasCredits).mockResolvedValue(true);

    // Render the app
    render(
      <ThemeProvider defaultTheme="light" storageKey="ui-theme">
        <ChatProvider>
          <App />
        </ChatProvider>
      </ThemeProvider>
    );

    const inputs = screen.getAllByPlaceholderText('Ask about products...');
    const input = inputs[0]; // Use the first input (main chat input)
    const form = input.closest('form');

    // First query - should be fresh
    fireEvent.change(input, { target: { value: query } });
    fireEvent.submit(form!);

    await waitFor(() => {
      expect(screen.queryByText('Thinking...')).not.toBeInTheDocument();
    });

    // Verify fresh result is displayed
    expect(screen.getByText('Test Laptop')).toBeInTheDocument();
    expect(screen.getByText('Great laptop for work')).toBeInTheDocument();
    
    // Should not show cached indicator for fresh result (Requirement 4.3)
    expect(screen.queryByText(/cached/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/refresh/i)).not.toBeInTheDocument();

    // Second identical query - should use cache
    fireEvent.change(input, { target: { value: query } });
    fireEvent.submit(form!);

    await waitFor(() => {
      expect(screen.queryByText('Thinking...')).not.toBeInTheDocument();
    });

    // Verify cached result is displayed with cache indicator (Requirement 4.3)
    expect(screen.getByText('Test Laptop')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText(/cached/i)).toBeInTheDocument();
    });

    // Verify refresh button is available for cached results (Requirement 4.4)
    const refreshButton = screen.getByText(/refresh/i);
    expect(refreshButton).toBeInTheDocument();
    expect(refreshButton).toBeEnabled();

    // Test refresh functionality (Requirement 4.4)
    vi.mocked(ApiService.sendQueryWithRetry).mockResolvedValueOnce({
      ...mockQueryResponse,
      recommendations_summary: 'Updated laptop recommendation',
      cached: false
    });

    fireEvent.click(refreshButton);

    // Verify loading state during refresh
    await waitFor(() => {
      expect(screen.getByText('Thinking...')).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.queryByText('Thinking...')).not.toBeInTheDocument();
    });

    // Verify refreshed content shows fresh result
    expect(screen.getByText('Updated laptop recommendation')).toBeInTheDocument();
    expect(screen.queryByText(/cached/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/refresh/i)).not.toBeInTheDocument();

    // Verify API was called 3 times: initial, cached (server-side), refresh
    expect(vi.mocked(ApiService.sendQueryWithRetry)).toHaveBeenCalledTimes(3);
  });

  test('Client-side cache persistence and expiration', async () => {
    const { ApiService } = await import('../services/api');
    const { CreditService } = await import('../services/creditService');
    
    const query = 'Find me headphones under 5000';
    const mockQueryResponse = {
      query,
      products: [
        {
          title: 'Test Headphones',
          price: 3500,
          rating: 4.0,
          features: ['Wireless', 'Noise Cancelling'],
          pros: ['Good sound quality'],
          cons: ['Short battery life'],
          link: 'https://example.com/headphones'
        }
      ],
      recommendations_summary: 'Good headphones for the price',
      cached: false
    };

    vi.mocked(ApiService.sendQueryWithRetry).mockResolvedValue(mockQueryResponse);
    vi.mocked(CreditService.getCreditStatus).mockResolvedValue({
      available_credits: 10,
      max_credits: 10,
      is_guest: true,
      can_reset: false,
    });
    vi.mocked(CreditService.hasCredits).mockResolvedValue(true);

    // Test client-side caching
    const cachedResult = await queryCacheService.getCachedResult(query);
    expect(cachedResult).toBeNull(); // Should be null initially

    // Cache a result
    queryCacheService.cacheResult(query, mockQueryResponse);

    // Retrieve cached result
    const retrievedResult = await queryCacheService.getCachedResult(query);
    expect(retrievedResult).not.toBeNull();
    expect(retrievedResult?.cached).toBe(true);
    expect(retrievedResult?.query).toBe(query);

    // Test cache expiration
    vi.useFakeTimers();
    vi.advanceTimersByTime(60 * 60 * 1000 + 1000); // Advance past 1 hour + 1 second

    queryCacheService.clearExpiredCache();
    const expiredResult = await queryCacheService.getCachedResult(query);
    expect(expiredResult).toBeNull(); // Should be null after expiration

    vi.useRealTimers();
  });

  test('Error handling preserves credits and cache state', async () => {
    const { ApiService } = await import('../services/api');
    const { CreditService } = await import('../services/creditService');
    
    const query = 'Find me a tablet';
    
    // First call succeeds, second call fails
    vi.mocked(ApiService.sendQueryWithRetry)
      .mockResolvedValueOnce({
        query,
        products: [
          {
            title: 'Test Tablet',
            price: 20000,
            rating: 4.1,
            features: ['10 inch display', '64GB Storage'],
            pros: ['Portable'],
            cons: ['Limited storage'],
            link: 'https://example.com/tablet'
          }
        ],
        recommendations_summary: 'Good tablet for basic use',
        cached: false
      })
      .mockRejectedValueOnce(new Error('Network error'));

    let currentCredits = 10;
    vi.mocked(CreditService.getCreditStatus).mockImplementation(async () => ({
      available_credits: currentCredits,
      max_credits: 10,
      is_guest: true,
      can_reset: false,
    }));

    vi.mocked(CreditService.hasCredits).mockResolvedValue(true);

    // Render the app
    render(
      <ThemeProvider defaultTheme="light" storageKey="ui-theme">
        <ChatProvider>
          <App />
        </ChatProvider>
      </ThemeProvider>
    );

    const inputs = screen.getAllByPlaceholderText('Ask about products...');
    const input = inputs[0]; // Use the first input (main chat input)
    const form = input.closest('form');

    // First successful query
    fireEvent.change(input, { target: { value: query } });
    fireEvent.submit(form!);

    await waitFor(() => {
      expect(screen.queryByText('Thinking...')).not.toBeInTheDocument();
    });

    expect(screen.getByText('Test Tablet')).toBeInTheDocument();

    // Simulate credit deduction after successful query
    currentCredits = 9;

    // Second query that fails
    fireEvent.change(input, { target: { value: 'Another query' } });
    fireEvent.submit(form!);

    await waitFor(() => {
      expect(screen.queryByText('Thinking...')).not.toBeInTheDocument();
    });

    // Verify error message is shown
    expect(screen.getByText(/error occurred/i)).toBeInTheDocument();

    // Verify previous successful result is still visible
    expect(screen.getByText('Test Tablet')).toBeInTheDocument();
  });

  test('Cache statistics and management', () => {
    // Test cache statistics
    const initialStats = queryCacheService.getCacheStats();
    expect(initialStats.totalEntries).toBe(0);
    expect(initialStats.validEntries).toBe(0);
    expect(initialStats.expiredEntries).toBe(0);

    // Add some cache entries
    queryCacheService.cacheResult('query1', {
      query: 'query1',
      products: [],
      recommendations_summary: 'Test 1',
      cached: false
    });

    queryCacheService.cacheResult('query2', {
      query: 'query2',
      products: [],
      recommendations_summary: 'Test 2',
      cached: false
    });

    const statsAfterCaching = queryCacheService.getCacheStats();
    expect(statsAfterCaching.totalEntries).toBe(2);
    expect(statsAfterCaching.validEntries).toBe(2);
    expect(statsAfterCaching.expiredEntries).toBe(0);

    // Clear all cache
    queryCacheService.clearAllCache();
    const statsAfterClear = queryCacheService.getCacheStats();
    expect(statsAfterClear.totalEntries).toBe(0);
  });
});