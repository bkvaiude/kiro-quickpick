import { type AuthState } from './authService';

/**
 * Service for managing authentication state persistence
 */
export class AuthStateService {
  private static readonly AUTH_STATE_KEY = 'auth_state';
  private static readonly LAST_CHECK_KEY = 'auth_last_check';
  private static readonly AUTH_TOKEN_KEY = 'auth_token';
  private static readonly AUTH_EXPIRY_KEY = 'auth_expiry';
  private static readonly USER_INFO_KEY = 'user_info';
  private static readonly AUTH_NONCE_KEY = 'auth_nonce';
  
  /**
   * Initialize authentication state from storage
   * @returns The stored auth state or null if not found
   */
  static async initializeAuthState(): Promise<AuthState | null> {
    try {
      const authState = this.loadAuthState();
      if (!authState) return null;
      
      // Update last check time
      this.updateLastAuthCheckTime();
      
      return authState;
    } catch (error) {
      console.error('Error initializing auth state:', error);
      return null;
    }
  }
  
  /**
   * Load authentication state from storage
   * @returns The stored auth state or null if not found or expired
   */
  static loadAuthState(): AuthState | null {
    try {
      const token = localStorage.getItem(this.AUTH_TOKEN_KEY);
      if (!token) return null;
      
      const expiryStr = localStorage.getItem(this.AUTH_EXPIRY_KEY);
      const expiry = expiryStr ? parseInt(expiryStr, 10) : 0;
      
      // Check if token is expired
      if (expiry && expiry < Date.now()) {
        this.clearAuthState();
        return null;
      }
      
      const userInfoStr = localStorage.getItem(this.USER_INFO_KEY);
      let user = null;
      
      if (userInfoStr) {
        try {
          user = JSON.parse(userInfoStr);
        } catch (e) {
          console.error('Error parsing user info:', e);
        }
      }
      
      return {
        isAuthenticated: true,
        token,
        expiresAt: expiry,
        user
      };
    } catch (error) {
      console.error('Error loading auth state:', error);
      return null;
    }
  }

  /**
   * Save authentication state to storage
   * @param authState The authentication state to save
   */
  static saveAuthState(authState: AuthState): void {
    try {
      if (authState && authState.token) {
        localStorage.setItem(this.AUTH_STATE_KEY, JSON.stringify(authState));
        localStorage.setItem(this.AUTH_TOKEN_KEY, authState.token);
        localStorage.setItem(this.AUTH_EXPIRY_KEY, authState.expiresAt.toString());
        
        if (authState.user) {
          localStorage.setItem(this.USER_INFO_KEY, JSON.stringify(authState.user));
        }
        
        this.updateLastAuthCheckTime();
      } else {
        // If no token, clear the auth state
        this.clearAuthState();
      }
    } catch (error) {
      console.error('Error saving authentication state to local storage:', error);
    }
  }

  /**
   * Clear authentication state from storage
   */
  static clearAuthState(): void {
    try {
      localStorage.removeItem(this.AUTH_STATE_KEY);
      localStorage.removeItem(this.LAST_CHECK_KEY);
      localStorage.removeItem(this.AUTH_TOKEN_KEY);
      localStorage.removeItem(this.AUTH_EXPIRY_KEY);
      localStorage.removeItem(this.USER_INFO_KEY);
      localStorage.removeItem(this.AUTH_NONCE_KEY);
    } catch (error) {
      console.error('Error clearing authentication state from local storage:', error);
    }
  }

  /**
   * Update the timestamp of the last authentication check
   */
  static updateLastAuthCheckTime(): void {
    try {
      const now = Date.now().toString();
      localStorage.setItem(this.LAST_CHECK_KEY, now);
      localStorage.setItem('last_auth_check', now);
    } catch (error) {
      console.error('Error updating last auth check time:', error);
    }
  }

  /**
   * Get the timestamp of the last authentication check
   * @returns The timestamp of the last check or 0 if not found
   */
  static getLastAuthCheckTime(): number {
    try {
      const lastCheck = localStorage.getItem(this.LAST_CHECK_KEY);
      return lastCheck ? parseInt(lastCheck, 10) : 0;
    } catch (error) {
      console.error('Error getting last auth check time:', error);
      return 0;
    }
  }
  
  /**
   * Check if the authentication state needs to be refreshed
   * @param maxAge Maximum age in milliseconds before refresh is needed (default: 5 minutes)
   * @returns True if refresh is needed, false otherwise
   */
  static needsRefresh(maxAge: number = 5 * 60 * 1000): boolean {
    const lastCheck = this.getLastAuthCheckTime();
    const now = Date.now();
    return lastCheck === 0 || (now - lastCheck) > maxAge;
  }
  
  /**
   * Refresh the authentication state if needed
   * @returns The refreshed auth state or null if not available
   */
  static async refreshIfNeeded(): Promise<AuthState | null> {
    // Always update the last check time
    this.updateLastAuthCheckTime();
    
    // If no refresh is needed, just return the current state
    if (!this.needsRefresh()) {
      return this.loadAuthState();
    }
    
    // In a real implementation, this would call an API to refresh the token
    // For now, we'll just return the current state
    return this.loadAuthState();
  }
}