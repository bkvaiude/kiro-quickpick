import { useAuth0 } from '@auth0/auth0-react';
import { useCallback } from 'react';
import { AuthService } from '../services/authService';
import type { UserConsent, UserProfile, AuthState } from '../services/authService';

/**
 * Custom hook that combines Auth0 functionality with our AuthService
 */
export const useAuth = () => {
  const {
    isAuthenticated,
    loginWithRedirect,
    logout: auth0Logout,
    getAccessTokenSilently,
    user,
    isLoading
  } = useAuth0();

  // Get token when needed
  const getToken = useCallback(async () => {
    if (!isAuthenticated) return null;
    
    try {
      return await getAccessTokenSilently();
    } catch (error) {
      console.error('Error getting access token:', error);
      return null;
    }
  }, [isAuthenticated, getAccessTokenSilently]);

  // Login function
  const login = useCallback(() => {
    // Save current path to return to after login
    AuthService.saveReturnPath();
    
    // Redirect to Auth0 login page
    return loginWithRedirect({

      openUrl: (url) => {
  // Ensure URL is properly encoded
        // console.log("🔍 Authorize URL about to be called:", url);
        // url = encodeURI(url);
        console.log("🔍 Authorize URL about to be called:", url);
        
        window.location.assign(url);
      }
    });
  }, [loginWithRedirect]);

  // Logout function
  const logout = useCallback(() => {
    return auth0Logout({ 
      logoutParams: {
        returnTo: window.location.origin 
      }
    });
  }, [auth0Logout]);

  // Get user profile
  const getUserInfo = useCallback((): UserProfile | null => {
    if (!isAuthenticated || !user) return null;
    
    // Get marketing consent from local storage
    const userConsent = AuthService.getUserConsent();
    
    return {
      sub: user.sub || '',
      email: user.email,
      name: user.name,
      picture: user.picture,
      updated_at: user.updated_at || new Date().toISOString(),
      marketingConsent: userConsent?.marketingConsent
    };
  }, [isAuthenticated, user]);

  // Get authentication state
  const getAuthState = useCallback(async (): Promise<AuthState> => {
    const token = isAuthenticated ? await getToken() : null;
    
    return {
      isAuthenticated,
      token,
      expiresAt: 0, // Auth0 React SDK handles token expiration internally
      user: getUserInfo()
    };
  }, [isAuthenticated, getToken, getUserInfo]);

  // Save user consent
  const saveUserConsent = useCallback((consent: UserConsent) => {
    AuthService.saveUserConsent(consent);
  }, []);

  // Get user consent
  const getUserConsent = useCallback(() => {
    return AuthService.getUserConsent();
  }, []);

  // Guest user functionality
  const getRemainingGuestActions = useCallback(() => {
    if (isAuthenticated) return Infinity;
    return AuthService.getRemainingGuestActions();
  }, [isAuthenticated]);

  const incrementGuestAction = useCallback((actionType = 'chat') => {
    if (isAuthenticated) return true;
    return AuthService.incrementGuestAction(actionType);
  }, [isAuthenticated]);

  const isGuestLimitReached = useCallback(() => {
    if (isAuthenticated) return false;
    return AuthService.isGuestLimitReached();
  }, [isAuthenticated]);

  const resetGuestActions = useCallback(() => {
    AuthService.resetGuestActions();
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