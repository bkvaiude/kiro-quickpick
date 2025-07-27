import { useAuth0 } from '@auth0/auth0-react';
import { useCallback, useEffect } from 'react';
import { unifiedAuthService } from '../services/unifiedAuthService';
import type { UserConsent, UserProfile } from '../services/unifiedAuthService';

// Legacy AuthState interface for backward compatibility
export interface AuthState {
  isAuthenticated: boolean;
  token: string | null;
  expiresAt: number;
  user: UserProfile | null;
}

/**
 * Custom hook that combines Auth0 functionality with our UnifiedAuthService
 */
export const useAuth = () => {
  const auth0Context = useAuth0();
  const {
    isAuthenticated,
    logout: auth0Logout,
    isLoading
  } = auth0Context;

  // Initialize the unified auth service with Auth0 context
  useEffect(() => {
    unifiedAuthService.initialize(auth0Context);
  }, [auth0Context]);

  // Get token when needed
  const getToken = useCallback(async () => {
    return await unifiedAuthService.getToken();
  }, []);

  // Login function
  const login = useCallback(() => {
    return unifiedAuthService.login();
  }, []);

  // Logout function
  const logout = useCallback(() => {
    return unifiedAuthService.logout();
  }, []);

  // Get user profile
  const getUserInfo = useCallback((): UserProfile | null => {
    return unifiedAuthService.getUserProfile();
  }, []);

  // Get authentication state (for backward compatibility)
  const getAuthState = useCallback(async (): Promise<AuthState> => {
    const token = await getToken();
    
    return {
      isAuthenticated: unifiedAuthService.isAuthenticated(),
      token,
      expiresAt: 0, // Auth0 React SDK handles token expiration internally
      user: getUserInfo()
    };
  }, [getToken, getUserInfo]);

  // Save user consent
  const saveUserConsent = useCallback((consent: UserConsent) => {
    unifiedAuthService.saveUserConsent(consent);
  }, []);

  // Get user consent
  const getUserConsent = useCallback(() => {
    return unifiedAuthService.getUserConsent();
  }, []);

  // Guest user functionality
  const getRemainingGuestActions = useCallback(() => {
    return unifiedAuthService.getRemainingGuestActions();
  }, []);

  const incrementGuestAction = useCallback((actionType = 'chat') => {
    return unifiedAuthService.incrementGuestAction(actionType);
  }, []);

  const isGuestLimitReached = useCallback(() => {
    return unifiedAuthService.isGuestLimitReached();
  }, []);

  const resetGuestActions = useCallback(() => {
    unifiedAuthService.resetGuestActions();
  }, []);

  return {
    isAuthenticated,
    isLoading,
    login,
    logout,
    getToken,
    getUserInfo,
    getAuthState,
    saveUserConsent,
    getUserConsent,
    getRemainingGuestActions,
    incrementGuestAction,
    isGuestLimitReached,
    resetGuestActions
  };
};