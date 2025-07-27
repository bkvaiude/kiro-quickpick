import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import App from '../App';
import { ChatProvider } from '../context/ChatContext';
import { ThemeProvider } from '../components/theme/ThemeProvider';

// Mock scrollIntoView
Element.prototype.scrollIntoView = vi.fn();

// Mock the API service
vi.mock('../services/api.ts', () => ({
  ApiService: {
    sendQueryWithRetry: vi.fn().mockImplementation(async (query) => {
      // Simulate API response based on query
      if (query.toLowerCase().includes('phone')) {
        return {
          query,
          products: [
            {
              title: 'Redmi Note 12 Pro 5G',
              price: 11999,
              rating: 4.2,
              features: ['8GB RAM', '128GB Storage', '5G', '50MP Camera', '5000mAh Battery'],
              pros: ['Great display', 'Good camera', 'Fast charging'],
              cons: ['Average build quality', 'Bloatware'],
              link: 'https://example.com/product1'
            },
            {
              title: 'Realme 11 5G',
              price: 12499,
              rating: 4.0,
              features: ['8GB RAM', '128GB Storage', '5G', '108MP Camera', '5000mAh Battery'],
              pros: ['Excellent camera', 'Fast processor', 'Good battery life'],
              cons: ['UI needs improvement', 'Heating issues'],
              link: 'https://example.com/product2'
            }
          ],
          recommendations_summary: 'Based on your requirements, Redmi Note 12 Pro 5G is the best option.'
        };
      } else {
        return {
          query,
          products: [],
          recommendations_summary: 'No products found matching your criteria.'
        };
      }
    }),
    getErrorMessage: vi.fn().mockReturnValue('An error occurred'),
    sendQuery: vi.fn(),
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
  }
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

describe('End-to-End Tests', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    vi.clearAllMocks();
  });

  test('Complete user flow from query to product display', async () => {
    // Render the app with providers
    render(
      <ThemeProvider defaultTheme="light" storageKey="ui-theme">
        <ChatProvider>
          <App />
        </ChatProvider>
      </ThemeProvider>
    );

    // Verify initial state
    expect(screen.getByPlaceholderText('Ask about products...')).toBeInTheDocument();
    expect(screen.getByText('Try asking:')).toBeInTheDocument();

    // Type a query
    const input = screen.getByPlaceholderText('Ask about products...');
    fireEvent.change(input, { target: { value: 'What is the best phone under 12000?' } });

    // Submit the query
    const form = input.closest('form');
    fireEvent.submit(form!);

    // Verify loading state
    expect(screen.getByText('Thinking...')).toBeInTheDocument();

    // Wait for response
    await waitFor(() => {
      expect(screen.queryByText('Thinking...')).not.toBeInTheDocument();
    });

    // Verify response
    expect(screen.getByText('Redmi Note 12 Pro 5G')).toBeInTheDocument();
    expect(screen.getByText('Realme 11 5G')).toBeInTheDocument();
    expect(screen.getByText('Based on your requirements, Redmi Note 12 Pro 5G is the best option.')).toBeInTheDocument();

    // Verify product details
    expect(screen.getByText('₹11,999')).toBeInTheDocument();
    expect(screen.getByText('₹12,499')).toBeInTheDocument();
    expect(screen.getByText('4.2')).toBeInTheDocument();
    expect(screen.getByText('4.0')).toBeInTheDocument();

    // Verify features
    expect(screen.getAllByText('8GB RAM').length).toBe(2);
    expect(screen.getAllByText('5G').length).toBe(2);
    expect(screen.getByText('50MP Camera')).toBeInTheDocument();
    expect(screen.getByText('108MP Camera')).toBeInTheDocument();

    // Verify pros and cons
    expect(screen.getByText('Great display')).toBeInTheDocument();
    expect(screen.getByText('UI needs improvement')).toBeInTheDocument();

    // Verify buy links
    const buyLinks = screen.getAllByText('Buy Now');
    expect(buyLinks.length).toBe(2);
    expect(buyLinks[0]).toHaveAttribute('href', 'https://example.com/product1');
    expect(buyLinks[1]).toHaveAttribute('href', 'https://example.com/product2');

    // Test conversation context maintenance by sending a follow-up query
    fireEvent.change(input, { target: { value: 'Which one has better battery life?' } });
    fireEvent.submit(form!);

    // Verify loading state again
    expect(screen.getByText('Thinking...')).toBeInTheDocument();

    // Wait for response
    await waitFor(() => {
      expect(screen.queryByText('Thinking...')).not.toBeInTheDocument();
    });

    // Verify that the previous context was maintained (both products should still be visible)
    expect(screen.getAllByText('Redmi Note 12 Pro 5G').length).toBe(2);
    expect(screen.getAllByText('Realme 11 5G').length).toBe(2);
  });

  test('Handles error states gracefully', async () => {
    // Mock API to throw an error for the first call only
    const mockSendQueryWithRetry = vi.fn()
      .mockRejectedValueOnce(new Error('API Error'))
      .mockResolvedValueOnce({
        query: 'Show me laptops under 50000',
        products: [],
        recommendations_summary: 'No products found matching your criteria.'
      });
    
    vi.mocked(vi.importActual('../services/api.ts')).ApiService.sendQueryWithRetry = mockSendQueryWithRetry;

    // Render the app with providers
    render(
      <ThemeProvider defaultTheme="light" storageKey="ui-theme">
        <ChatProvider>
          <App />
        </ChatProvider>
      </ThemeProvider>
    );

    // Type a query
    const input = screen.getByPlaceholderText('Ask about products...');
    fireEvent.change(input, { target: { value: 'What is the best phone under 12000?' } });

    // Submit the query
    const form = input.closest('form');
    fireEvent.submit(form!);

    // Verify loading state
    expect(screen.getByText('Thinking...')).toBeInTheDocument();

    // Wait for error response
    await waitFor(() => {
      expect(screen.queryByText('Thinking...')).not.toBeInTheDocument();
    });

    // Verify error message
    expect(screen.getByText('An error occurred')).toBeInTheDocument();

    // Verify we can still send another query after an error
    fireEvent.change(input, { target: { value: 'Show me laptops under 50000' } });
    fireEvent.submit(form!);

    // Wait for response
    await waitFor(() => {
      expect(screen.queryByText('Thinking...')).not.toBeInTheDocument();
    });

    // Verify response for the second query
    expect(screen.getByText('No products found matching your criteria.')).toBeInTheDocument();
  });

  test('Example queries work correctly', async () => {
    // Render the app with providers
    render(
      <ThemeProvider defaultTheme="light" storageKey="ui-theme">
        <ChatProvider>
          <App />
        </ChatProvider>
      </ThemeProvider>
    );

    // Find and click an example query
    const exampleQuery = screen.getByText("What's the best 5G phone under ₹12,000 with 8GB RAM?");
    fireEvent.click(exampleQuery);

    // Verify loading state
    expect(screen.getByText('Thinking...')).toBeInTheDocument();

    // Wait for response
    await waitFor(() => {
      expect(screen.queryByText('Thinking...')).not.toBeInTheDocument();
    });

    // Verify response
    expect(screen.getByText('Redmi Note 12 Pro 5G')).toBeInTheDocument();
    expect(screen.getByText('Realme 11 5G')).toBeInTheDocument();

    // Verify example queries are no longer shown after a message is sent
    expect(screen.queryByText('Try asking:')).not.toBeInTheDocument();
  });
});