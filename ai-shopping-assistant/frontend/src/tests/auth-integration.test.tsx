import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '../context/AuthContext';
import { AuthService } from '../services/authService';
import { UserActionService, ActionType } from '../services/userActionService';

// Mock dependencies
vi.mock('../services/authService', () => ({
  AuthService: {
    login: vi.fn().mockResolvedValue(undefined),
    logout: vi.fn().mockResolvedValue(undefined),
    isAuthenticated: vi.fn().mockReturnValue(false),
    getUserInfo: vi.fn().mockReturnValue(null),
    getRemainingGuestActions: vi.fn().mockReturnValue(10),
    incrementGuestAction: vi.fn().mockReturnValue(true),
    isGuestLimitReached: vi.fn().mockReturnValue(false),
    getToken: vi.fn().mockReturnValue(null),
    handleRedirect: vi.fn().mockResolvedValue(false),
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

// Test component that uses auth context
function TestComponent() {
  const { isAuthenticated, isLoading, user, remainingGuestActions, login, logout, decrementGuestActions } = useAuth();
  
  return (
    <div>
      <div data-testid="auth-status">
        {isLoading ? 'Loading...' : isAuthenticated ? 'Authenticated' : 'Not authenticated'}
      </div>
      <div data-testid="remaining-actions">{remainingGuestActions}</div>
      <div data-testid="user-info">{user ? JSON.stringify(user) : 'No user'}</div>
      <button data-testid="login-button" onClick={() => login()}>Login</button>
      <button data-testid="logout-button" onClick={() => logout()}>Logout</button>
      <button data-testid="action-button" onClick={() => decrementGuestActions(ActionType.CHAT)}>
        Perform Action
      </button>
    </div>
  );
}

describe('Authentication Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.clear();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  test('initial state shows not authenticated', async () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );
    
    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Not authenticated');
    });
    expect(screen.getByTestId('remaining-actions')).toHaveTextContent('10');
    expect(screen.getByTestId('user-info')).toHaveTextContent('No user');
  });

  test('login button triggers AuthService.login', async () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );
    
    fireEvent.click(screen.getByTestId('login-button'));
    
    expect(AuthService.login).toHaveBeenCalled();
  });

  test('logout button triggers AuthService.logout', async () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );
    
    fireEvent.click(screen.getByTestId('logout-button'));
    
    expect(AuthService.logout).toHaveBeenCalled();
  });

  test('action button decrements guest actions', async () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );
    
    fireEvent.click(screen.getByTestId('action-button'));
    
    expect(AuthService.incrementGuestAction).toHaveBeenCalledWith(ActionType.CHAT);
  });

  test('shows authenticated state when user is logged in', async () => {
    // Mock authenticated state
    (AuthService.isAuthenticated as any).mockReturnValue(true);
    (AuthService.getUserInfo as any).mockReturnValue({
      sub: 'user123',
      name: 'Test User',
      updated_at: '2023-01-01'
    });
    
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );
    
    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Authenticated');
    });
    expect(screen.getByTestId('remaining-actions')).toHaveTextContent('Infinity');
    expect(screen.getByTestId('user-info')).toHaveTextContent('Test User');
  });

  test('handles auth redirect on initial load', async () => {
    // Mock window location hash
    Object.defineProperty(window, 'location', {
      value: {
        hash: '#access_token=test-token&id_token=test-id-token&expires_in=3600&state=test-state',
        pathname: '/',
        origin: 'http://localhost:3000',
      },
      writable: true,
    });
    
    // Mock successful redirect handling
    (AuthService.handleRedirect as any).mockResolvedValue(true);
    (AuthService.getUserInfo as any).mockReturnValue({
      sub: 'user123',
      name: 'Test User',
      updated_at: '2023-01-01'
    });
    
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );
    
    await waitFor(() => {
      expect(AuthService.handleRedirect).toHaveBeenCalled();
    });
    
    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Authenticated');
    });
  });

  test('shows guest limit reached state', async () => {
    // Mock guest limit reached
    (AuthService.getRemainingGuestActions as any).mockReturnValue(0);
    (AuthService.isGuestLimitReached as any).mockReturnValue(true);
    
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );
    
    await waitFor(() => {
      expect(screen.getByTestId('remaining-actions')).toHaveTextContent('0');
    });
    
    // Action should not be allowed
    (AuthService.incrementGuestAction as any).mockReturnValue(false);
    
    fireEvent.click(screen.getByTestId('action-button'));
    
    expect(AuthService.incrementGuestAction).toHaveBeenCalledWith(ActionType.CHAT);
  });
});