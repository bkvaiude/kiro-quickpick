import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '../context/AuthContext';
import { ChatInput } from '../components/chat/ChatInput';
import { AuthService } from '../services/authService';
import { UserActionService, ActionType } from '../services/userActionService';

// Mock dependencies
vi.mock('../services/authService', () => ({
  AuthService: {
    isAuthenticated: vi.fn().mockReturnValue(false),
    getRemainingGuestActions: vi.fn().mockReturnValue(10),
    incrementGuestAction: vi.fn().mockReturnValue(true),
    isGuestLimitReached: vi.fn().mockReturnValue(false),
    login: vi.fn().mockResolvedValue(undefined),
    logout: vi.fn().mockResolvedValue(undefined),
    getUserInfo: vi.fn().mockReturnValue(null),
    handleRedirect: vi.fn().mockResolvedValue(false),
    getToken: vi.fn().mockReturnValue(null),
    needsTokenRefresh: vi.fn().mockReturnValue(false),
    refreshToken: vi.fn().mockResolvedValue(false),
    getAuthState: vi.fn().mockReturnValue({
      isAuthenticated: false,
      token: null,
      expiresAt: 0,
      user: null
    })
  }
}));

vi.mock('../services/userActionService', () => ({
  UserActionService: {
    trackAction: vi.fn().mockReturnValue(true),
    getRemainingActions: vi.fn().mockReturnValue(10),
    resetActions: vi.fn(),
    isLimitReached: vi.fn().mockReturnValue(false)
  },
  ActionType: {
    CHAT: 'chat',
    SEARCH: 'search'
  }
}));

// Mock the AuthContext directly to control the behavior
vi.mock('../context/AuthContext', () => {
  const actual = vi.importActual('../context/AuthContext');
  return {
    ...actual,
    useAuth: () => ({
      isAuthenticated: AuthService.isAuthenticated(),
      isLoading: false,
      user: AuthService.getUserInfo(),
      remainingGuestActions: AuthService.getRemainingGuestActions(),
      login: AuthService.login,
      logout: AuthService.logout,
      decrementGuestActions: (actionType) => {
        // Only call incrementGuestAction for non-authenticated users
        if (!AuthService.isAuthenticated()) {
          AuthService.incrementGuestAction(actionType);
        }
      }
    }),
    AuthProvider: ({ children }) => <>{children}</>
  };
});

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value.toString();
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      store = {};
    }),
    length: 0,
    key: vi.fn((index: number) => ''),
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Test component that simulates chat interface
function TestChatInterface() {
  const { decrementGuestActions } = useAuth();
  const handleSendMessage = (message: string) => {
    decrementGuestActions(ActionType.CHAT);
  };
  
  return (
    <div>
      <ChatInput onSendMessage={handleSendMessage} isLoading={false} />
    </div>
  );
}

describe('Guest Limit Enforcement Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.clear();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  test('chat input is enabled when guest has remaining actions', async () => {
    (AuthService.isAuthenticated as any).mockReturnValue(false);
    (AuthService.getRemainingGuestActions as any).mockReturnValue(5);
    (AuthService.isGuestLimitReached as any).mockReturnValue(false);
    
    render(
      <AuthProvider>
        <TestChatInterface />
      </AuthProvider>
    );
    
    const input = screen.getByPlaceholderText('Ask about products...');
    expect(input).not.toBeDisabled();
    
    // Enter text and submit
    fireEvent.change(input, { target: { value: 'test message' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    
    expect(AuthService.incrementGuestAction).toHaveBeenCalledWith(ActionType.CHAT);
  });

  test('chat input is disabled when guest limit is reached', async () => {
    (AuthService.isAuthenticated as any).mockReturnValue(false);
    (AuthService.getRemainingGuestActions as any).mockReturnValue(0);
    (AuthService.isGuestLimitReached as any).mockReturnValue(true);
    
    render(
      <AuthProvider>
        <TestChatInterface />
      </AuthProvider>
    );
    
    const input = screen.getByPlaceholderText('Login to continue chatting');
    expect(input).toBeDisabled();
    
    // Lock icon should be visible
    const lockIcon = document.querySelector('svg');
    expect(lockIcon).toBeInTheDocument();
  });

  test('chat input is always enabled for authenticated users', async () => {
    // Set up the mock to return true for isAuthenticated
    (AuthService.isAuthenticated as any).mockReturnValue(true);
    (AuthService.getRemainingGuestActions as any).mockReturnValue(Infinity);
    (AuthService.isGuestLimitReached as any).mockReturnValue(false);
    
    render(
      <AuthProvider>
        <TestChatInterface />
      </AuthProvider>
    );
    
    const input = screen.getByPlaceholderText('Ask about products...');
    expect(input).not.toBeDisabled();
    
    // Enter text and submit
    fireEvent.change(input, { target: { value: 'test message' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    
    // Should not increment guest action for authenticated users
    expect(AuthService.incrementGuestAction).not.toHaveBeenCalled();
  });

  test('guest actions are tracked correctly', async () => {
    let remainingActions = 3;
    
    (AuthService.isAuthenticated as any).mockReturnValue(false);
    (AuthService.getRemainingGuestActions as any).mockImplementation(() => remainingActions);
    (AuthService.incrementGuestAction as any).mockImplementation(() => {
      if (remainingActions > 0) {
        remainingActions--;
        return true;
      }
      return false;
    });
    (AuthService.isGuestLimitReached as any).mockImplementation(() => remainingActions <= 0);
    
    const { rerender } = render(
      <AuthProvider>
        <TestChatInterface />
      </AuthProvider>
    );
    
    // First message
    const input = screen.getByPlaceholderText('Ask about products...');
    fireEvent.change(input, { target: { value: 'message 1' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    
    expect(AuthService.incrementGuestAction).toHaveBeenCalledWith(ActionType.CHAT);
    expect(remainingActions).toBe(2);
    
    // Update mocks to reflect new state
    rerender(
      <AuthProvider>
        <TestChatInterface />
      </AuthProvider>
    );
    
    // Second message
    fireEvent.change(input, { target: { value: 'message 2' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    
    expect(remainingActions).toBe(1);
    
    // Update mocks to reflect new state
    rerender(
      <AuthProvider>
        <TestChatInterface />
      </AuthProvider>
    );
    
    // Third message
    fireEvent.change(input, { target: { value: 'message 3' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    
    expect(remainingActions).toBe(0);
    
    // Update mocks to reflect new state
    rerender(
      <AuthProvider>
        <TestChatInterface />
      </AuthProvider>
    );
    
    // Input should now be disabled
    await waitFor(() => {
      const disabledInput = screen.getByPlaceholderText('Login to continue chatting');
      expect(disabledInput).toBeDisabled();
    });
  });
});