import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest';
import { AuthService } from './authService';
import { UserActionService } from './userActionService';

// Mock the UserActionService
vi.mock('./userActionService', () => ({
  UserActionService: {
    getRemainingActions: vi.fn().mockReturnValue(5),
    trackAction: vi.fn().mockReturnValue(true),
    resetActions: vi.fn(),
  }
}));

// Mock fetch
global.fetch = vi.fn();

// Mock window.location
const mockLocation = {
  href: '',
  origin: 'http://localhost:3000',
  pathname: '/',
  hash: '',
};

Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true,
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

// Mock crypto.getRandomValues
Object.defineProperty(window, 'crypto', {
  value: {
    getRandomValues: vi.fn((arr: Uint32Array) => {
      for (let i = 0; i < arr.length; i++) {
        arr[i] = Math.floor(Math.random() * 1000000);
      }
      return arr;
    }),
  },
});

describe('AuthService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.clear();
    mockLocation.hash = '';
    mockLocation.href = '';
    mockLocation.pathname = '/';
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('login', () => {
    test('should redirect to Auth0 login page', async () => {
      await AuthService.login();
      
      // Check that localStorage was updated with nonce and state
      expect(localStorageMock.setItem).toHaveBeenCalledWith('auth_nonce', expect.any(String));
      expect(localStorageMock.setItem).toHaveBeenCalledWith('auth_state', expect.any(String));
      
      // Check that window.location.href was updated with Auth0 URL
      expect(mockLocation.href).toContain('authorize');
      expect(mockLocation.href).toContain('client_id=');
      expect(mockLocation.href).toContain('redirect_uri=');
      expect(mockLocation.href).toContain('response_type=token+id_token');
    });

    test('should include marketing consent if available', async () => {
      localStorageMock.setItem('marketing_consent', 'true');
      localStorageMock.setItem('consent_timestamp', '2023-01-01T00:00:00Z');
      
      await AuthService.login();
      
      expect(mockLocation.href).toContain('marketing_consent=true');
      expect(mockLocation.href).toContain('consent_timestamp=2023-01-01T00:00:00Z');
    });
  });

  describe('logout', () => {
    test('should clear auth data and redirect to Auth0 logout', async () => {
      // Set up some auth data
      localStorageMock.setItem('auth_token', 'test-token');
      localStorageMock.setItem('auth_expiry', '1234567890');
      localStorageMock.setItem('user_info', '{"name":"Test User"}');
      
      await AuthService.logout();
      
      // Check that localStorage was cleared
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('auth_token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('auth_expiry');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('user_info');
      
      // Check that window.location.href was updated with Auth0 logout URL
      expect(mockLocation.href).toContain('logout');
      expect(mockLocation.href).toContain('client_id=');
      expect(mockLocation.href).toContain('returnTo=');
    });
  });

  describe('handleRedirect', () => {
    test('should return false if no hash in URL', async () => {
      mockLocation.hash = '';
      
      const result = await AuthService.handleRedirect();
      
      expect(result).toBe(false);
    });

    test('should handle successful authentication', async () => {
      // Mock the hash in the URL
      mockLocation.hash = '#access_token=test-token&id_token=test-id-token&expires_in=3600&state=test-state';
      
      // Mock localStorage state
      localStorageMock.setItem('auth_state', 'test-state');
      
      // Mock fetch response for userInfo
      const mockUserInfo = { sub: 'user123', name: 'Test User', updated_at: '2023-01-01' };
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUserInfo,
      });
      
      const result = await AuthService.handleRedirect();
      
      expect(result).toBe(true);
      expect(localStorageMock.setItem).toHaveBeenCalledWith('auth_token', 'test-token');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('auth_expiry', expect.any(String));
      expect(localStorageMock.setItem).toHaveBeenCalledWith('user_info', JSON.stringify(mockUserInfo));
    });

    test('should handle state mismatch', async () => {
      // Mock the hash in the URL
      mockLocation.hash = '#access_token=test-token&id_token=test-id-token&expires_in=3600&state=wrong-state';
      
      // Mock localStorage state
      localStorageMock.setItem('auth_state', 'test-state');
      
      const result = await AuthService.handleRedirect();
      
      expect(result).toBe(false);
    });

    test('should handle error in hash', async () => {
      // Mock the hash in the URL with error
      mockLocation.hash = '#error=access_denied&error_description=User%20denied%20access';
      
      const result = await AuthService.handleRedirect();
      
      expect(result).toBe(false);
    });
  });

  describe('isAuthenticated', () => {
    test('should return false if no token', () => {
      localStorageMock.removeItem('auth_token');
      
      const result = AuthService.isAuthenticated();
      
      expect(result).toBe(false);
    });

    test('should return false if token is expired', () => {
      localStorageMock.setItem('auth_token', 'test-token');
      localStorageMock.setItem('auth_expiry', (Date.now() - 1000).toString()); // Expired 1 second ago
      
      const result = AuthService.isAuthenticated();
      
      expect(result).toBe(false);
    });

    test('should return true if token is valid and not expired', () => {
      localStorageMock.setItem('auth_token', 'test-token');
      localStorageMock.setItem('auth_expiry', (Date.now() + 3600000).toString()); // Expires in 1 hour
      
      const result = AuthService.isAuthenticated();
      
      expect(result).toBe(true);
    });
  });

  describe('getToken', () => {
    test('should return null if not authenticated', () => {
      vi.spyOn(AuthService, 'isAuthenticated').mockReturnValueOnce(false);
      
      const result = AuthService.getToken();
      
      expect(result).toBeNull();
    });

    test('should return token if authenticated', () => {
      vi.spyOn(AuthService, 'isAuthenticated').mockReturnValueOnce(true);
      localStorageMock.setItem('auth_token', 'test-token');
      
      const result = AuthService.getToken();
      
      expect(result).toBe('test-token');
    });
  });

  describe('getUserInfo', () => {
    test('should return null if not authenticated', () => {
      vi.spyOn(AuthService, 'isAuthenticated').mockReturnValueOnce(false);
      
      const result = AuthService.getUserInfo();
      
      expect(result).toBeNull();
    });

    test('should return user info if authenticated', () => {
      vi.spyOn(AuthService, 'isAuthenticated').mockReturnValueOnce(true);
      const userInfo = { sub: 'user123', name: 'Test User', updated_at: '2023-01-01' };
      localStorageMock.setItem('user_info', JSON.stringify(userInfo));
      
      const result = AuthService.getUserInfo();
      
      expect(result).toEqual(userInfo);
    });

    test('should return null if user info is invalid JSON', () => {
      vi.spyOn(AuthService, 'isAuthenticated').mockReturnValueOnce(true);
      localStorageMock.setItem('user_info', 'invalid-json');
      
      const result = AuthService.getUserInfo();
      
      expect(result).toBeNull();
    });
  });

  describe('fetchUserInfo', () => {
    test('should fetch user info from Auth0', async () => {
      const mockUserInfo = { sub: 'user123', name: 'Test User', updated_at: '2023-01-01' };
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUserInfo,
      });
      
      const result = await AuthService.fetchUserInfo('test-token');
      
      expect(result).toEqual(mockUserInfo);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/userinfo'),
        expect.objectContaining({
          headers: {
            Authorization: 'Bearer test-token',
          },
        })
      );
    });

    test('should throw error if fetch fails', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        statusText: 'Unauthorized',
      });
      
      await expect(AuthService.fetchUserInfo('test-token')).rejects.toThrow('Failed to fetch user info');
    });
  });

  describe('generateNonce', () => {
    test('should generate a random nonce', () => {
      const nonce1 = AuthService.generateNonce();
      const nonce2 = AuthService.generateNonce();
      
      expect(nonce1).toMatch(/^[0-9a-f]+$/);
      expect(nonce2).toMatch(/^[0-9a-f]+$/);
      expect(nonce1).not.toBe(nonce2); // Should be different each time
    });
  });

  describe('getRemainingGuestActions', () => {
    test('should return Infinity for authenticated users', () => {
      vi.spyOn(AuthService, 'isAuthenticated').mockReturnValueOnce(true);
      
      const result = AuthService.getRemainingGuestActions();
      
      expect(result).toBe(Infinity);
    });

    test('should return remaining actions from UserActionService for guests', () => {
      vi.spyOn(AuthService, 'isAuthenticated').mockReturnValueOnce(false);
      
      const result = AuthService.getRemainingGuestActions();
      
      expect(result).toBe(5); // From the mock
      expect(UserActionService.getRemainingActions).toHaveBeenCalled();
    });
  });

  describe('incrementGuestAction', () => {
    test('should return true for authenticated users without tracking', () => {
      vi.spyOn(AuthService, 'isAuthenticated').mockReturnValueOnce(true);
      
      const result = AuthService.incrementGuestAction();
      
      expect(result).toBe(true);
      expect(UserActionService.trackAction).not.toHaveBeenCalled();
    });

    test('should track action for guest users', () => {
      vi.spyOn(AuthService, 'isAuthenticated').mockReturnValueOnce(false);
      
      const result = AuthService.incrementGuestAction('chat');
      
      expect(result).toBe(true); // From the mock
      expect(UserActionService.trackAction).toHaveBeenCalledWith('chat');
    });
  });

  describe('isGuestLimitReached', () => {
    test('should return false for authenticated users', () => {
      vi.spyOn(AuthService, 'isAuthenticated').mockReturnValueOnce(true);
      vi.spyOn(AuthService, 'getRemainingGuestActions').mockReturnValueOnce(Infinity);
      
      const result = AuthService.isGuestLimitReached();
      
      expect(result).toBe(false);
    });

    test('should return true when guest limit is reached', () => {
      vi.spyOn(AuthService, 'isAuthenticated').mockReturnValueOnce(false);
      vi.spyOn(AuthService, 'getRemainingGuestActions').mockReturnValueOnce(0);
      
      const result = AuthService.isGuestLimitReached();
      
      expect(result).toBe(true);
    });

    test('should return false when guest has remaining actions', () => {
      vi.spyOn(AuthService, 'isAuthenticated').mockReturnValueOnce(false);
      vi.spyOn(AuthService, 'getRemainingGuestActions').mockReturnValueOnce(3);
      
      const result = AuthService.isGuestLimitReached();
      
      expect(result).toBe(false);
    });
  });

  describe('resetGuestActions', () => {
    test('should call UserActionService.resetActions', () => {
      AuthService.resetGuestActions();
      
      expect(UserActionService.resetActions).toHaveBeenCalled();
    });
  });

  describe('getAuthState', () => {
    test('should return current auth state', () => {
      const mockToken = 'test-token';
      const mockExpiry = '1234567890';
      const mockUser = { sub: 'user123', name: 'Test User', updated_at: '2023-01-01' };
      
      vi.spyOn(AuthService, 'isAuthenticated').mockReturnValueOnce(true);
      vi.spyOn(AuthService, 'getToken').mockReturnValueOnce(mockToken);
      vi.spyOn(AuthService, 'getUserInfo').mockReturnValueOnce(mockUser);
      
      localStorageMock.setItem('auth_expiry', mockExpiry);
      
      const result = AuthService.getAuthState();
      
      expect(result).toEqual({
        isAuthenticated: true,
        token: mockToken,
        expiresAt: parseInt(mockExpiry),
        user: mockUser,
      });
    });
  });

  describe('needsTokenRefresh', () => {
    test('should return false if not authenticated', () => {
      vi.spyOn(AuthService, 'isAuthenticated').mockReturnValueOnce(false);
      
      const result = AuthService.needsTokenRefresh();
      
      expect(result).toBe(false);
    });

    test('should return true if token expires soon', () => {
      vi.spyOn(AuthService, 'isAuthenticated').mockReturnValueOnce(true);
      
      // Token expires in 4 minutes (less than the 5 minute threshold)
      localStorageMock.setItem('auth_expiry', (Date.now() + 4 * 60 * 1000).toString());
      
      const result = AuthService.needsTokenRefresh();
      
      expect(result).toBe(true);
    });

    test('should return false if token expiry is far in the future', () => {
      vi.spyOn(AuthService, 'isAuthenticated').mockReturnValueOnce(true);
      
      // Token expires in 10 minutes (more than the 5 minute threshold)
      localStorageMock.setItem('auth_expiry', (Date.now() + 10 * 60 * 1000).toString());
      
      const result = AuthService.needsTokenRefresh();
      
      expect(result).toBe(false);
    });
  });

  describe('refreshToken', () => {
    test('should call login if token needs refresh', async () => {
      vi.spyOn(AuthService, 'needsTokenRefresh').mockReturnValueOnce(true);
      vi.spyOn(AuthService, 'login').mockResolvedValueOnce();
      
      const result = await AuthService.refreshToken();
      
      expect(result).toBe(true);
      expect(AuthService.login).toHaveBeenCalled();
    });

    test('should not call login if token does not need refresh', async () => {
      vi.spyOn(AuthService, 'needsTokenRefresh').mockReturnValueOnce(false);
      vi.spyOn(AuthService, 'login').mockResolvedValueOnce();
      
      const result = await AuthService.refreshToken();
      
      expect(result).toBe(false);
      expect(AuthService.login).not.toHaveBeenCalled();
    });
  });

  describe('saveUserConsent and getUserConsent', () => {
    test('should save and retrieve user consent', () => {
      const consent = {
        termsAccepted: true,
        marketingConsent: true,
        timestamp: '2023-01-01T00:00:00Z',
      };
      
      AuthService.saveUserConsent(consent);
      
      expect(localStorageMock.setItem).toHaveBeenCalledWith('marketing_consent', 'true');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('consent_timestamp', consent.timestamp);
      
      // Mock the localStorage for getUserConsent
      localStorageMock.getItem.mockImplementation((key: string) => {
        if (key === 'marketing_consent') return 'true';
        if (key === 'consent_timestamp') return consent.timestamp;
        return null;
      });
      
      const retrievedConsent = AuthService.getUserConsent();
      
      expect(retrievedConsent).toEqual(consent);
    });

    test('should update user info with consent for authenticated users', () => {
      vi.spyOn(AuthService, 'isAuthenticated').mockReturnValueOnce(true);
      vi.spyOn(AuthService, 'getUserInfo').mockReturnValueOnce({
        sub: 'user123',
        name: 'Test User',
        updated_at: '2023-01-01',
      });
      
      const consent = {
        termsAccepted: true,
        marketingConsent: true,
        timestamp: '2023-01-01T00:00:00Z',
      };
      
      AuthService.saveUserConsent(consent);
      
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'user_info',
        JSON.stringify({
          sub: 'user123',
          name: 'Test User',
          updated_at: '2023-01-01',
          marketingConsent: true,
        })
      );
    });

    test('getUserConsent should return null if consent data is missing', () => {
      localStorageMock.getItem.mockImplementation((key: string) => null);
      
      const result = AuthService.getUserConsent();
      
      expect(result).toBeNull();
    });
  });
});