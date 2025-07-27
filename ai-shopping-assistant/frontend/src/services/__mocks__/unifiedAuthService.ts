import { vi } from 'vitest';
import { UserProfile, UserConsent } from '../unifiedAuthService';

// Mock user profile
const mockUserProfile: UserProfile = {
  sub: 'user123',
  name: 'Test User',
  email: 'test@example.com',
  updated_at: '2023-01-01',
  marketingConsent: true
};

// Mock user consent
const mockUserConsent: UserConsent = {
  termsAccepted: true,
  marketingConsent: true,
  timestamp: '2023-01-01T00:00:00Z'
};

// Mock UnifiedAuthService class
export class UnifiedAuthService {
  initialize = vi.fn();
  isAuthenticated = vi.fn().mockReturnValue(true);
  isLoading = vi.fn().mockReturnValue(false);
  getToken = vi.fn().mockResolvedValue('test-token');
  getUserProfile = vi.fn().mockReturnValue(mockUserProfile);
  login = vi.fn().mockResolvedValue(undefined);
  logout = vi.fn().mockReturnValue(undefined);
  getAuthHeaders = vi.fn().mockResolvedValue({
    'Content-Type': 'application/json',
    'Authorization': 'Bearer test-token'
  });
  saveReturnPath = vi.fn();
  getReturnPath = vi.fn().mockReturnValue('/');
  clearReturnPath = vi.fn();
  saveUserConsent = vi.fn();
  getUserConsent = vi.fn().mockReturnValue(mockUserConsent);
  getRemainingGuestActions = vi.fn().mockReturnValue(5);
  incrementGuestAction = vi.fn().mockReturnValue(true);
  isGuestLimitReached = vi.fn().mockReturnValue(false);
  resetGuestActions = vi.fn();
}

// Mock singleton instance
export const unifiedAuthService = new UnifiedAuthService();