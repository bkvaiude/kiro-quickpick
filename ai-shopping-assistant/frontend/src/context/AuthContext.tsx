import { createContext, useContext, useReducer, useEffect, type ReactNode } from 'react';
import { AuthService, type UserProfile, type AuthState } from '../services/authService';
import { ActionType } from '../services/userActionService';
import { ConsentService } from '../services/consentService';
import { AuthStateService } from '../services/authStateService';

// Define the auth context type
interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: UserProfile | null;
  remainingGuestActions: number;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  decrementGuestActions: (actionType?: ActionType) => void;
}

// Define action types
type AuthAction =
  | { type: 'SET_AUTHENTICATED'; payload: { user: UserProfile | null } }
  | { type: 'SET_UNAUTHENTICATED' }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'DECREMENT_GUEST_ACTIONS' }
  | { type: 'SET_REMAINING_ACTIONS'; payload: number };

// Initial state
const initialState = {
  isAuthenticated: false,
  isLoading: true,
  user: null as UserProfile | null,
  remainingGuestActions: 10,
};

// Create the context
const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  isLoading: true,
  user: null as UserProfile | null,
  remainingGuestActions: 10,
  login: async () => {},
  logout: async () => {},
  decrementGuestActions: () => {},
});

// Reducer function
const authReducer = (state: typeof initialState, action: AuthAction): typeof initialState => {
  switch (action.type) {
    case 'SET_AUTHENTICATED':
      return {
        ...state,
        isAuthenticated: true,
        isLoading: false,
        user: action.payload.user,
        remainingGuestActions: Infinity,
      };
    case 'SET_UNAUTHENTICATED':
      return {
        ...state,
        isAuthenticated: false,
        isLoading: false,
        user: null,
        remainingGuestActions: AuthService.getRemainingGuestActions(),
      };
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload,
      };
    case 'DECREMENT_GUEST_ACTIONS':
      if (state.isAuthenticated) {
        return state; // No change for authenticated users
      }
      const decremented = state.remainingGuestActions - 1;
      return {
        ...state,
        remainingGuestActions: Math.max(0, decremented),
      };
    case 'SET_REMAINING_ACTIONS':
      return {
        ...state,
        remainingGuestActions: action.payload,
      };
    default:
      return state;
  }
};

// Provider component
export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Check authentication status on initial render
  useEffect(() => {
    const checkAuth = async () => {
      dispatch({ type: 'SET_LOADING', payload: true });
      
      try {
        // First, try to initialize from stored auth state
        const storedState = await AuthStateService.initializeAuthState();
        
        // If we have a stored state, use it
        if (storedState && storedState.isAuthenticated) {
          dispatch({ type: 'SET_AUTHENTICATED', payload: { user: storedState.user } });
          
          // Sync consent information with the backend
          await ConsentService.syncConsent();
          return;
        }
        
        // Handle Auth0 redirect if there's a hash in the URL
        if (window.location.hash) {
          const success = await AuthService.handleRedirect();
          if (success) {
            const user = AuthService.getUserInfo();
            dispatch({ type: 'SET_AUTHENTICATED', payload: { user } });
            
            // Save authentication state
            const authState = AuthService.getAuthState();
            AuthStateService.saveAuthState(authState);
            
            // Sync consent information with the backend
            await ConsentService.syncConsent();
            return;
          }
        }
        
        // Check if user is already authenticated
        if (AuthService.isAuthenticated()) {
          const user = AuthService.getUserInfo();
          dispatch({ type: 'SET_AUTHENTICATED', payload: { user } });
          
          // Save authentication state
          const authState = AuthService.getAuthState();
          AuthStateService.saveAuthState(authState);
          
          // Sync consent information with the backend
          await ConsentService.syncConsent();
        } else {
          dispatch({ type: 'SET_UNAUTHENTICATED' });
        }
      } catch (error) {
        console.error('Error during authentication check:', error);
        dispatch({ type: 'SET_UNAUTHENTICATED' });
      }
    };

    checkAuth();
  }, []);

  // Periodically check and refresh authentication if needed
  useEffect(() => {
    if (!state.isAuthenticated) return;
    
    const checkInterval = 5 * 60 * 1000; // 5 minutes
    
    const intervalId = setInterval(async () => {
      try {
        // Check if token needs refresh
        if (AuthService.needsTokenRefresh()) {
          dispatch({ type: 'SET_LOADING', payload: true });
          const success = await AuthService.refreshToken();
          
          if (success) {
            const user = AuthService.getUserInfo();
            dispatch({ type: 'SET_AUTHENTICATED', payload: { user } });
            
            // Save updated authentication state
            const authState = AuthService.getAuthState();
            AuthStateService.saveAuthState(authState);
          } else {
            // If refresh failed, log out
            await logout();
          }
        } else {
          // Update last check time even if token doesn't need refresh
          AuthStateService.updateLastAuthCheckTime();
        }
      } catch (error) {
        console.error('Error during authentication refresh:', error);
      } finally {
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    }, checkInterval);
    
    return () => clearInterval(intervalId);
  }, [state.isAuthenticated]);

  // Update remaining actions when authentication state changes
  useEffect(() => {
    if (!state.isAuthenticated) {
      const remainingActions = AuthService.getRemainingGuestActions();
      dispatch({ type: 'SET_REMAINING_ACTIONS', payload: remainingActions });
    }
  }, [state.isAuthenticated]);

  // Login function
  const login = async () => {
    dispatch({ type: 'SET_LOADING', payload: true });
    await AuthService.login();
  };

  // Logout function
  const logout = async () => {
    dispatch({ type: 'SET_LOADING', payload: true });
    
    // Clear authentication state from storage
    AuthStateService.clearAuthState();
    
    await AuthService.logout();
    dispatch({ type: 'SET_UNAUTHENTICATED' });
  };

  // Decrement guest actions
  const decrementGuestActions = (actionType: ActionType = ActionType.CHAT) => {
    if (!state.isAuthenticated) {
      const success = AuthService.incrementGuestAction(actionType);
      if (success) {
        dispatch({ type: 'DECREMENT_GUEST_ACTIONS' });
      }
    }
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated: state.isAuthenticated,
        isLoading: state.isLoading,
        user: state.user,
        remainingGuestActions: state.remainingGuestActions,
        login,
        logout,
        decrementGuestActions,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to use the auth context
export const useAuth = () => useContext(AuthContext);