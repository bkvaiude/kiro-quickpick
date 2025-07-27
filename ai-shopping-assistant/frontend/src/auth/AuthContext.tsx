import { createContext, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { useAuth } from './useAuth';
import type { UserConsent, UserProfile } from '../services/unifiedAuthService';
import { ConsentService } from '../services/consentService';

// Define the context interface
interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: UserProfile | null;
  remainingGuestActions: number;
  login: () => Promise<void>;
  logout: () => void;
  getToken: () => Promise<string | null>;
  saveUserConsent: (consent: UserConsent) => void;
  getUserConsent: () => UserConsent | null;
  getRemainingGuestActions: () => number;
  incrementGuestAction: (actionType?: string) => boolean;
  isGuestLimitReached: () => boolean;
  resetGuestActions: () => void;
}

// Create the context with default values
const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  isLoading: true,
  user: null,
  remainingGuestActions: 10,
  login: async () => {},
  logout: () => {},
  getToken: async () => null,
  saveUserConsent: () => {},
  getUserConsent: () => null,
  getRemainingGuestActions: () => 0,
  incrementGuestAction: () => false,
  isGuestLimitReached: () => true,
  resetGuestActions: () => {}
});

interface AuthProviderProps {
  children: ReactNode;
}

/**
 * Authentication provider component
 */
export const AuthProvider = ({ children }: AuthProviderProps) => {
  const auth = useAuth();
  const [user, setUser] = useState<UserProfile | null>(null);
  const [remainingGuestActions, setRemainingGuestActions] = useState<number>(10);
  
  // Update user when authentication state changes
  useEffect(() => {
    if (auth.isAuthenticated) {
      setUser(auth.getUserInfo());
      setRemainingGuestActions(Infinity);
    } else {
      setUser(null);
      setRemainingGuestActions(auth.getRemainingGuestActions());
    }
  }, [auth.isAuthenticated, auth.getUserInfo, auth.getRemainingGuestActions]);
  
  // Sync consent with backend when user is authenticated
  useEffect(() => {
    if (auth.isAuthenticated) {
      ConsentService.syncConsent(
        auth.isAuthenticated,
        auth.getToken,
        auth.getUserConsent
      );
    }
  }, [auth.isAuthenticated]);
  
  const value = {
    isAuthenticated: auth.isAuthenticated,
    isLoading: auth.isLoading,
    user,
    remainingGuestActions,
    login: auth.login,
    logout: auth.logout,
    getToken: auth.getToken,
    saveUserConsent: auth.saveUserConsent,
    getUserConsent: auth.getUserConsent,
    getRemainingGuestActions: auth.getRemainingGuestActions,
    incrementGuestAction: (actionType = 'chat') => {
      const result = auth.incrementGuestAction(actionType);
      if (result && !auth.isAuthenticated) {
        setRemainingGuestActions(auth.getRemainingGuestActions());
      }
      return result;
    },
    isGuestLimitReached: auth.isGuestLimitReached,
    resetGuestActions: auth.resetGuestActions
  };
  
  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

/**
 * Hook to use the authentication context
 */
export const useAuthContext = () => useContext(AuthContext);