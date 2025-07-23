import { API_BASE_URL } from '../config';
import { UserActionService } from './userActionService';

// Auth0 configuration
// These values should be moved to environment variables in a real application
const AUTH0_DOMAIN = import.meta.env.VITE_AUTH0_DOMAIN || 'your-auth0-domain.auth0.com';
const AUTH0_CLIENT_ID = import.meta.env.VITE_AUTH0_CLIENT_ID || 'your-auth0-client-id';
const AUTH0_REDIRECT_URI = import.meta.env.VITE_AUTH0_REDIRECT_URI || window.location.origin;
const AUTH0_AUDIENCE = import.meta.env.VITE_AUTH0_AUDIENCE || `https://${AUTH0_DOMAIN}/api/v2/`;

// Storage keys
const STORAGE_KEYS = {
  AUTH_TOKEN: 'auth_token',
  AUTH_EXPIRY: 'auth_expiry',
  USER_INFO: 'user_info',
  AUTH_STATE: 'auth_state',
  AUTH_NONCE: 'auth_nonce',
  MARKETING_CONSENT: 'marketing_consent',
  CONSENT_TIMESTAMP: 'consent_timestamp'
};

// User profile interface
export interface UserProfile {
  sub: string;           // Auth0 user ID
  email?: string;        // User email
  phone_number?: string; // User phone number
  name?: string;         // User name
  picture?: string;      // User profile picture URL
  updated_at: string;    // Last update timestamp
  marketingConsent?: boolean; // Marketing consent flag
}

// User consent interface
export interface UserConsent {
  termsAccepted: boolean;      // Terms of Use and Privacy Policy acceptance
  marketingConsent: boolean;   // Marketing communications consent
  timestamp: string;           // When consent was provided
}

// Authentication state interface
export interface AuthState {
  isAuthenticated: boolean;
  token: string | null;
  expiresAt: number;
  user: UserProfile | null;
}

/**
 * Service for handling Auth0 authentication
 */
export const AuthService = {
  /**
   * Redirects the user to Auth0 login page
   * @returns Promise that resolves when the login process is initiated
   */
  login(): Promise<void> {
    return new Promise((resolve) => {
      // Generate and store a nonce for security
      const nonce = this.generateNonce();
      localStorage.setItem(STORAGE_KEYS.AUTH_NONCE, nonce);
      
      // Save authentication state for CSRF protection
      const state = this.generateNonce();
      localStorage.setItem(STORAGE_KEYS.AUTH_STATE, state);
      
      // Construct Auth0 authorization URL
      const authUrl = new URL(`https://${AUTH0_DOMAIN}/authorize`);
      
      // Add required parameters
      authUrl.searchParams.append('client_id', AUTH0_CLIENT_ID);
      authUrl.searchParams.append('redirect_uri', AUTH0_REDIRECT_URI);
      authUrl.searchParams.append('response_type', 'token id_token');
      authUrl.searchParams.append('scope', 'openid profile email phone');
      authUrl.searchParams.append('audience', AUTH0_AUDIENCE);
      authUrl.searchParams.append('nonce', nonce);
      authUrl.searchParams.append('state', state);
      
      // Get marketing consent from local storage if available
      const marketingConsent = localStorage.getItem(STORAGE_KEYS.MARKETING_CONSENT);
      if (marketingConsent !== null) {
        // Pass consent information as custom parameters
        // These will be available in the user's metadata in Auth0
        authUrl.searchParams.append('marketing_consent', marketingConsent);
        const consentTimestamp = localStorage.getItem(STORAGE_KEYS.CONSENT_TIMESTAMP) || '';
        authUrl.searchParams.append('consent_timestamp', consentTimestamp);
      }
      
      // Save the current URL to return to after login
      localStorage.setItem('auth_return_to', window.location.pathname);
      
      // Redirect to Auth0
      window.location.href = authUrl.toString();
      resolve();
    });
  },

  /**
   * Logs out the user
   * @returns Promise that resolves when the logout process is initiated
   */
  logout(): Promise<void> {
    return new Promise((resolve) => {
      // Clear authentication data
      localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN);
      localStorage.removeItem(STORAGE_KEYS.AUTH_EXPIRY);
      localStorage.removeItem(STORAGE_KEYS.USER_INFO);
      localStorage.removeItem(STORAGE_KEYS.AUTH_NONCE);
      localStorage.removeItem(STORAGE_KEYS.AUTH_STATE);
      
      // Construct logout URL
      const logoutUrl = new URL(`https://${AUTH0_DOMAIN}/v2/logout`);
      logoutUrl.searchParams.append('client_id', AUTH0_CLIENT_ID);
      logoutUrl.searchParams.append('returnTo', window.location.origin);
      
      // Redirect to Auth0 logout
      window.location.href = logoutUrl.toString();
      resolve();
    });
  },

  /**
   * Handles the redirect from Auth0 after login
   * @returns Promise that resolves when the redirect is handled
   */
  async handleRedirect(): Promise<boolean> {
    // Check if we have a hash in the URL (Auth0 response)
    if (!window.location.hash) {
      return false;
    }

    // Parse the hash
    const params = new URLSearchParams(window.location.hash.substring(1));
    const accessToken = params.get('access_token');
    const idToken = params.get('id_token');
    const expiresIn = params.get('expires_in');
    const error = params.get('error');
    const state = params.get('state');
    
    // Verify state to prevent CSRF attacks
    const storedState = localStorage.getItem(STORAGE_KEYS.AUTH_STATE);
    if (state !== storedState) {
      console.error('Auth0 state mismatch');
      return false;
    }
    
    // Clean up state
    localStorage.removeItem(STORAGE_KEYS.AUTH_STATE);

    // Handle errors
    if (error) {
      console.error('Auth0 error:', error);
      return false;
    }

    // If we have tokens, store them
    if (accessToken && idToken && expiresIn) {
      // Calculate expiry time
      const expiryTime = Date.now() + parseInt(expiresIn) * 1000;
      
      // Store tokens and expiry
      localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, accessToken);
      localStorage.setItem(STORAGE_KEYS.AUTH_EXPIRY, expiryTime.toString());
      
      // Get user info
      try {
        const userInfo = await this.fetchUserInfo(accessToken);
        
        // Add marketing consent information to user info if available
        const marketingConsent = localStorage.getItem(STORAGE_KEYS.MARKETING_CONSENT);
        if (marketingConsent !== null) {
          userInfo.marketingConsent = marketingConsent === 'true';
        }
        
        localStorage.setItem(STORAGE_KEYS.USER_INFO, JSON.stringify(userInfo));
        
        // Clean up the URL
        window.history.replaceState({}, document.title, window.location.pathname);
        
        // Redirect back to the original page if available
        const returnTo = localStorage.getItem('auth_return_to');
        if (returnTo) {
          localStorage.removeItem('auth_return_to');
          window.location.href = returnTo;
        }
        
        return true;
      } catch (error) {
        console.error('Failed to fetch user info:', error);
        return false;
      }
    }
    
    return false;
  },

  /**
   * Checks if the user is authenticated
   * @returns True if the user is authenticated, false otherwise
   */
  isAuthenticated(): boolean {
    const token = localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN);
    const expiryTime = localStorage.getItem(STORAGE_KEYS.AUTH_EXPIRY);
    
    if (!token || !expiryTime) {
      return false;
    }
    
    // Check if token is expired
    return parseInt(expiryTime) > Date.now();
  },

  /**
   * Gets the current authentication token
   * @returns The authentication token or null if not authenticated
   */
  getToken(): string | null {
    if (!this.isAuthenticated()) {
      return null;
    }
    
    return localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN);
  },

  /**
   * Gets the user profile information
   * @returns The user profile or null if not authenticated
   */
  getUserInfo(): UserProfile | null {
    if (!this.isAuthenticated()) {
      return null;
    }
    
    const userInfoStr = localStorage.getItem(STORAGE_KEYS.USER_INFO);
    if (!userInfoStr) {
      return null;
    }
    
    try {
      return JSON.parse(userInfoStr);
    } catch (error) {
      console.error('Failed to parse user info:', error);
      return null;
    }
  },

  /**
   * Fetches user information from Auth0
   * @param accessToken The access token
   * @returns Promise with the user profile
   */
  async fetchUserInfo(accessToken: string): Promise<UserProfile> {
    const response = await fetch(`https://${AUTH0_DOMAIN}/userinfo`, {
      headers: {
        Authorization: `Bearer ${accessToken}`
      }
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch user info: ${response.statusText}`);
    }
    
    return await response.json();
  },

  /**
   * Generates a random nonce for Auth0 authentication
   * @returns Random nonce string
   */
  generateNonce(): string {
    const array = new Uint32Array(4);
    window.crypto.getRandomValues(array);
    return Array.from(array).map(n => n.toString(16)).join('');
  },

  /**
   * Gets the number of remaining actions for guest users
   * @returns Number of remaining actions
   */
  getRemainingGuestActions(): number {
    if (this.isAuthenticated()) {
      return Infinity; // Authenticated users have unlimited actions
    }
    
    return UserActionService.getRemainingActions();
  },

  /**
   * Increments the guest action count
   * @param actionType The type of action being performed (defaults to 'chat')
   * @returns True if the action was counted, false if the limit is reached
   */
  incrementGuestAction(actionType = 'chat'): boolean {
    if (this.isAuthenticated()) {
      return true; // Authenticated users have unlimited actions
    }
    
    return UserActionService.trackAction(actionType as any);
  },

  /**
   * Checks if the guest action limit is reached
   * @returns True if the limit is reached, false otherwise
   */
  isGuestLimitReached(): boolean {
    return this.getRemainingGuestActions() <= 0;
  },

  /**
   * Resets the guest action count
   */
  resetGuestActions(): void {
    UserActionService.resetActions();
  },
  
  /**
   * Gets the current authentication state
   * @returns The authentication state
   */
  getAuthState(): AuthState {
    return {
      isAuthenticated: this.isAuthenticated(),
      token: this.getToken(),
      expiresAt: parseInt(localStorage.getItem(STORAGE_KEYS.AUTH_EXPIRY) || '0'),
      user: this.getUserInfo()
    };
  },
  
  /**
   * Checks if the token needs to be refreshed
   * @returns True if the token needs to be refreshed, false otherwise
   */
  needsTokenRefresh(): boolean {
    if (!this.isAuthenticated()) {
      return false;
    }
    
    const expiryTime = parseInt(localStorage.getItem(STORAGE_KEYS.AUTH_EXPIRY) || '0');
    // Refresh if token expires in less than 5 minutes
    return expiryTime - Date.now() < 5 * 60 * 1000;
  },
  
  /**
   * Refreshes the authentication token
   * @returns Promise that resolves when the token is refreshed
   */
  async refreshToken(): Promise<boolean> {
    // Auth0 SPA SDK doesn't support refresh tokens directly
    // For a real implementation, you would use a silent authentication flow
    // For now, we'll just redirect to login if the token is about to expire
    if (this.needsTokenRefresh()) {
      await this.login();
      return true;
    }
    
    return false;
  },

  /**
   * Saves user consent information
   * @param consent User consent information
   */
  saveUserConsent(consent: UserConsent): void {
    localStorage.setItem(STORAGE_KEYS.MARKETING_CONSENT, consent.marketingConsent ? 'true' : 'false');
    localStorage.setItem(STORAGE_KEYS.CONSENT_TIMESTAMP, consent.timestamp);
    
    // If the user is authenticated, update their profile with consent information
    if (this.isAuthenticated()) {
      const userInfo = this.getUserInfo();
      if (userInfo) {
        const updatedUserInfo = {
          ...userInfo,
          marketingConsent: consent.marketingConsent
        };
        localStorage.setItem(STORAGE_KEYS.USER_INFO, JSON.stringify(updatedUserInfo));
      }
    }
  },

  /**
   * Gets user consent information
   * @returns User consent information or null if not available
   */
  getUserConsent(): UserConsent | null {
    const marketingConsent = localStorage.getItem(STORAGE_KEYS.MARKETING_CONSENT);
    const timestamp = localStorage.getItem(STORAGE_KEYS.CONSENT_TIMESTAMP);
    
    if (marketingConsent === null || timestamp === null) {
      return null;
    }
    
    return {
      termsAccepted: true, // If we have consent data, terms were accepted
      marketingConsent: marketingConsent === 'true',
      timestamp
    };
  }
};