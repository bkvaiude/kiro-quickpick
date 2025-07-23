import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from './App';

// Mock the ChatContext
vi.mock('./context/ChatContext', () => ({
  useChatContext: () => ({
    state: {
      messages: [],
      isLoading: false,
      error: null,
    },
    sendMessage: vi.fn(),
    clearMessages: vi.fn(),
    selectedProductMessageId: null,
    setSelectedProductMessageId: vi.fn(),
  }),
  ChatProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Mock the ThemeProvider
vi.mock('./components/theme/ThemeProvider', () => ({
  ThemeProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Mock the AuthProvider
vi.mock('./context/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useAuth: () => ({
    isAuthenticated: false,
    login: vi.fn(),
    logout: vi.fn(),
    user: null,
    isLoading: false,
    remainingGuestActions: 10,
    decrementGuestActions: vi.fn(),
  }),
}));

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock the LoginPromptModal component
vi.mock('./components/auth/LoginPromptModal', () => ({
  LoginPromptModal: () => <div data-testid="login-prompt-modal"></div>
}));

// Mock the WelcomeMessage component
vi.mock('./components/auth/WelcomeMessage', () => ({
  WelcomeMessage: () => <div data-testid="welcome-message"></div>
}));

// Mock the Layout component
vi.mock('./components/layout/Layout', () => ({
  Layout: ({ children }: { children: React.ReactNode }) => <div data-testid="layout">{children}</div>
}));

// Mock the ChatInterface component
vi.mock('./components/chat/ChatInterface', () => ({
  ChatInterface: () => <div data-testid="chat-interface"></div>
}));

// Mock the ProductComparisonContainer component
vi.mock('./components/product/ProductComparisonContainer', () => ({
  ProductComparisonContainer: () => <div data-testid="product-comparison"></div>
}));

describe('App', () => {
  // Mock scrollIntoView before each test
  beforeEach(() => {
    // Mock scrollIntoView
    Element.prototype.scrollIntoView = vi.fn();
    
    // Mock window.innerWidth for mobile detection
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      value: 1024, // Desktop width
    });
    
    // Mock resize event
    window.dispatchEvent = vi.fn();
  });

  it('renders without crashing', () => {
    render(<App />);
    // This is a basic test to ensure the component renders
    expect(document.body).toBeDefined();
  });
  
  it('renders the layout component', () => {
    render(<App />);
    expect(screen.getByTestId('layout')).toBeInTheDocument();
  });
  
  it('renders the marketing message when no products are displayed', () => {
    render(<App />);
    expect(screen.getByText('Your AI Shopping Assistant')).toBeInTheDocument();
    expect(screen.getByText("Ask me about products and I'll help you find the best options based on your requirements.")).toBeInTheDocument();
  });
});