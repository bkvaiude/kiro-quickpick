import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest';
import { AuthStateService } from './authStateService';
import { AuthService } from './authService';
import type { AuthState, UserProfile } from './authService';

// Mock AuthService
vi.mock('./authService', () => ({
  AuthService: {
    needsTokenRefresh: vi.fn().mockReturnValue(false),
    refreshToken: vi.fn().mockResolvedValue(false),
    getAuthState: vi.fn(),
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

describe('AuthStateService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.clear();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('saveAuthState', () => {
    test('should save auth state to localStorage', () => {
      const mockState: AuthState = {
        isAuthenticated: true,
        token: 'test-token',
        expiresAt: 1234567890,
        user: {
          sub: 'user123',
          name: 'Test User',
          updated_at: '2023-01-01',
        },
      };

      AuthStateService.saveAuthState(mockState);

      expect(localStorageMock.setItem).toHaveBeenCalledWith('auth_token', 'test-token');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('auth_expiry', '1234567890');
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'user_info',
        JSON.stringify(mockState.user)
      );
      expect(localStorageMock.setItem).toHaveBeenCalledWith('last_auth_check', expect.any(String));
    });

    test('should remove auth data when token is null', () => {
      const mockState: AuthState = {
        isAuthenticated: false,
        token: null,
        expiresAt: 0,
        user: null,
      };

      AuthStateService.saveAuthState(mockState);

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('auth_token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('auth_expiry');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('user_info');
    });

    test('should handle errors gracefully', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      localStorageMock.setItem.mockImplementationOnce(() => {
        throw new Error('Storage error');
      });

      const mockState: AuthState = {
        isAuthenticated: true,
        token: 'test-token',
        expiresAt: 1234567890,
        user: null,
      };

      expect(() => AuthStateService.saveAuthState(mockState)).not.toThrow();
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Error saving authentication state to local storage:',
        expect.any(Error)
      );
    });
  });

  describe('loadAuthState', () => {
    test('should return null if no token in localStorage', () => {
      const result = AuthStateService.loadAuthState();
      expect(result).toBeNull();
    });

    test('should return null if token is expired', () => {
      localStorageMock.getItem.mockImplementation((key: string) => {
        if (key === 'auth_token') return 'test-token';
        if (key === 'auth_expiry') return (Date.now() - 1000).toString(); // Expired 1 second ago
        return null;
      });

      const result = AuthStateService.loadAuthState();
      expect(result).toBeNull();
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('auth_token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('auth_expiry');
    });

    test('should return auth state if token is valid', () => {
      const mockUser: UserProfile = {
        sub: 'user123',
        name: 'Test User',
        updated_at: '2023-01-01',
      };
      
      const expiresAt = Date.now() + 3600000; // Expires in 1 hour
      
      localStorageMock.getItem.mockImplementation((key: string) => {
        if (key === 'auth_token') return 'test-token';
        if (key === 'auth_expiry') return expiresAt.toString();
        if (key === 'user_info') return JSON.stringify(mockUser);
        return null;
      });

      const result = AuthStateService.loadAuthState();
      
      expect(result).toEqual({
        isAuthenticated: true,
        token: 'test-token',
        expiresAt,
        user: mockUser,
      });
    });

    test('should handle invalid user info JSON', () => {
      const expiresAt = Date.now() + 3600000; // Expires in 1 hour
      
      localStorageMock.getItem.mockImplementation((key: string) => {
        if (key === 'auth_token') return 'test-token';
        if (key === 'auth_expiry') return expiresAt.toString();
        if (key === 'user_info') return 'invalid-json';
        return null;
      });

      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      const result = AuthStateService.loadAuthState();
      
      expect(result).toEqual({
        isAuthenticated: true,
        token: 'test-token',
        expiresAt,
        user: null,
      });
      
      expect(consoleErrorSpy).toHaveBeenCalledWith('Error parsing user info:', expect.any(Error));
    });

    test('should handle errors gracefully', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      localStorageMock.getItem.mockImplementationOnce(() => {
        throw new Error('Storage error');
      });

      const result = AuthStateService.loadAuthState();
      
      expect(result).toBeNull();
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Error loading authentication state from local storage:',
        expect.any(Error)
      );
    });
  });

  describe('clearAuthState', () => {
    test('should remove all auth items from localStorage', () => {
      AuthStateService.clearAuthState();
      
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('auth_token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('auth_expiry');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('user_info');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('auth_state');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('auth_nonce');
    });

    test('should handle errors gracefully', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      localStorageMock.removeItem.mockImplementationOnce(() => {
        throw new Error('Storage error');
      });

      expect(() => AuthStateService.clearAuthState()).not.toThrow();
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Error clearing authentication state from local storage:',
        expect.any(Error)
      );
    });
  });

  describe('updateLastAuthCheckTime', () => {
    test('should update last auth check timestamp', () => {
      AuthStateService.updateLastAuthCheckTime();
      
      expect(localStorageMock.setItem).toHaveBeenCalledWith('last_auth_check', expect.any(String));
      
      // Verify it's a valid timestamp (number)
      const timestamp = localStorageMock.setItem.mock.calls[0][1];
      expect(Number.isNaN(parseInt(timestamp))).toBe(false);
    });

    test('should handle errors gracefully', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      localStorageMock.setItem.mockImplementationOnce(() => {
        throw new Error('Storage error');
      });

      expect(() => AuthStateService.updateLastAuthCheckTime()).not.toThrow();
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Error updating last auth check time:',
        expect.any(Error)
      );
    });
  });

  describe('getLastAuthCheckTime', () => {
    test('should return timestamp from localStorage', () => {
      const mockTimestamp = '1234567890';
      localStorageMock.getItem.mockReturnValueOnce(mockTimestamp);
      
      const result = AuthStateService.getLastAuthCheckTime();
      
      expect(result).toBe(parseInt(mockTimestamp));
      expect(localStorageMock.getItem).toHaveBeenCalledWith('last_auth_check');
    });

    test('should return 0 if no timestamp in localStorage', () => {
      localStorageMock.getItem.mockReturnValueOnce(null);
      
      const result = AuthStateService.getLastAuthCheckTime();
      
      expect(result).toBe(0);
    });

    test('should handle errors gracefully', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      localStorageMock.getItem.mockImplementationOnce(() => {
        throw new Error('Storage error');
      });

      const result = AuthStateService.getLastAuthCheckTime();
      
      expect(result).toBe(0);
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Error getting last auth check time:',
        expect.any(Error)
      );
    });
  });

  describe('needsRefresh', () => {
    test('should return true if last check is older than maxAge', () => {
      const now = Date.now();
      const sixMinutesAgo = now - 6 * 60 * 1000;
      
      vi.spyOn(AuthStateService, 'getLastAuthCheckTime').mockReturnValueOnce(sixMinutesAgo);
      
      // Default maxAge is 5 minutes
      const result = AuthStateService.needsRefresh();
      
      expect(result).toBe(true);
    });

    test('should return false if last check is newer than maxAge', () => {
      const now = Date.now();
      const fourMinutesAgo = now - 4 * 60 * 1000;
      
      vi.spyOn(AuthStateService, 'getLastAuthCheckTime').mockReturnValueOnce(fourMinutesAgo);
      
      // Default maxAge is 5 minutes
      const result = AuthStateService.needsRefresh();
      
      expect(result).toBe(false);
    });

    test('should respect custom maxAge parameter', () => {
      const now = Date.now();
      const threeMinutesAgo = now - 3 * 60 * 1000;
      
      vi.spyOn(AuthStateService, 'getLastAuthCheckTime').mockReturnValueOnce(threeMinutesAgo);
      
      // Custom maxAge of 2 minutes
      const result = AuthStateService.needsRefresh(2 * 60 * 1000);
      
      expect(result).toBe(true);
    });
  });

  describe('refreshIfNeeded', () => {
    test('should not refresh if not needed', async () => {
      vi.spyOn(AuthStateService, 'needsRefresh').mockReturnValueOnce(false);
      
      const result = await AuthStateService.refreshIfNeeded();
      
      expect(result).toBe(false);
      expect(AuthService.needsTokenRefresh).not.toHaveBeenCalled();
      expect(AuthService.refreshToken).not.toHaveBeenCalled();
    });

    test('should refresh token if needed and update last check time', async () => {
      vi.spyOn(AuthStateService, 'needsRefresh').mockReturnValueOnce(true);
      vi.spyOn(AuthStateService, 'updateLastAuthCheckTime').mockImplementationOnce(() => {});
      
      (AuthService.needsTokenRefresh as any).mockReturnValueOnce(true);
      (AuthService.refreshToken as any).mockResolvedValueOnce(true);
      
      const result = await AuthStateService.refreshIfNeeded();
      
      expect(result).toBe(true);
      expect(AuthService.needsTokenRefresh).toHaveBeenCalled();
      expect(AuthService.refreshToken).toHaveBeenCalled();
    });

    test('should update last check time even if token refresh not needed', async () => {
      vi.spyOn(AuthStateService, 'needsRefresh').mockReturnValueOnce(true);
      vi.spyOn(AuthStateService, 'updateLastAuthCheckTime').mockImplementationOnce(() => {});
      
      (AuthService.needsTokenRefresh as any).mockReturnValueOnce(false);
      
      const result = await AuthStateService.refreshIfNeeded();
      
      expect(result).toBe(true);
      expect(AuthService.needsTokenRefresh).toHaveBeenCalled();
      expect(AuthService.refreshToken).not.toHaveBeenCalled();
      expect(AuthStateService.updateLastAuthCheckTime).toHaveBeenCalled();
    });
  });

  describe('initializeAuthState', () => {
    test('should return null if no stored auth state', async () => {
      vi.spyOn(AuthStateService, 'loadAuthState').mockReturnValueOnce(null);
      
      const result = await AuthStateService.initializeAuthState();
      
      expect(result).toBeNull();
    });

    test('should refresh token if needed and return updated state', async () => {
      const mockState: AuthState = {
        isAuthenticated: true,
        token: 'test-token',
        expiresAt: 1234567890,
        user: { sub: 'user123', name: 'Test User', updated_at: '2023-01-01' },
      };
      
      vi.spyOn(AuthStateService, 'loadAuthState').mockReturnValueOnce(mockState);
      vi.spyOn(AuthStateService, 'updateLastAuthCheckTime').mockImplementationOnce(() => {});
      
      (AuthService.needsTokenRefresh as any).mockReturnValueOnce(true);
      (AuthService.refreshToken as any).mockResolvedValueOnce(true);
      
      // Mock loadAuthState to return updated state after refresh
      const updatedState = { ...mockState, expiresAt: 9876543210 };
      vi.spyOn(AuthStateService, 'loadAuthState').mockReturnValueOnce(mockState)
        .mockReturnValueOnce(updatedState);
      
      const result = await AuthStateService.initializeAuthState();
      
      expect(result).toEqual(updatedState);
      expect(AuthService.needsTokenRefresh).toHaveBeenCalled();
      expect(AuthService.refreshToken).toHaveBeenCalled();
      expect(AuthStateService.loadAuthState).toHaveBeenCalledTimes(2);
    });

    test('should update last check time and return state if token refresh not needed', async () => {
      const mockState: AuthState = {
        isAuthenticated: true,
        token: 'test-token',
        expiresAt: 1234567890,
        user: { sub: 'user123', name: 'Test User', updated_at: '2023-01-01' },
      };
      
      vi.spyOn(AuthStateService, 'loadAuthState').mockReturnValueOnce(mockState);
      vi.spyOn(AuthStateService, 'updateLastAuthCheckTime').mockImplementationOnce(() => {});
      
      (AuthService.needsTokenRefresh as any).mockReturnValueOnce(false);
      
      const result = await AuthStateService.initializeAuthState();
      
      expect(result).toEqual(mockState);
      expect(AuthService.needsTokenRefresh).toHaveBeenCalled();
      expect(AuthService.refreshToken).not.toHaveBeenCalled();
      expect(AuthStateService.updateLastAuthCheckTime).toHaveBeenCalled();
    });
  });
});