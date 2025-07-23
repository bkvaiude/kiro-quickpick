import { vi } from 'vitest';
import { AuthState, UserProfile } from '../authService';

// Mock user profile
const mockUserProfile: UserProfile = {
  sub: 'user123',
  name: 'Test User',
  email: 'test@example.com',
  updated_at: '2023-01-01',
  marketingConsent: true
};

// Mock auth state
const mockAuthState: AuthState = {
  isAuthenticated: true,
  token: 'test-token',
  expiresAt: 1234567890,
  user: mockUserProfile
};

// Mock AuthService
export const AuthService = {
  login: vi.fn().mockResolvedValue(undefined),
  logout: vi.fn().mockResolvedValue(undefined),
  handleRedirect: vi.fn().mockResolvedValue(true),
  isAuthenticated: vi.fn().mockReturnValue(true),
  getToken: vi.fn().mockReturnValue('test-token'),
  getUserInfo: vi.fn().mockReturnValue(mockUserProfile),
  fetchUserInfo: vi.fn().mockResolvedValue(mockUserProfile),
  generateNonce: vi.fn().mockReturnValue('random-nonce'),
  getRemainingGuestActions: vi.fn().mockReturnValue(5),
  incrementGuestAction: vi.fn().mockReturnValue(true),
  isGuestLimitReached: vi.fn().mockReturnValue(false),
  resetGuestActions: vi.fn(),
  getAuthState: vi.fn().mockReturnValue(mockAuthState),
  needsTokenRefresh: vi.fn().mockReturnValue(false),
  refreshToken: vi.fn().mockResolvedValue(false),
  saveUserConsent: vi.fn(),
  getUserConsent: vi.fn().mockReturnValue({
    termsAccepted: true,
    marketingConsent: true,
    timestamp: '2023-01-01T00:00:00Z'
  })
};