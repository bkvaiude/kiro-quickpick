import type { User } from '@auth0/auth0-react';
import { UserActionService } from './userActionService';
import browserFingerprintService from './fingerprint';

// Storage keys for non-Auth0 data
const STORAGE_KEYS = {
  MARKETING_CONSENT: 'marketing_consent',
  CONSENT_TIMESTAMP: 'consent_timestamp',
  AUTH_RETURN_TO: 'auth_return_to'
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

// Auth0 context interface (passed from React components)
export interface Auth0Context {
  isAuthenticated: boolean;
  isLoading: boolean;
  user?: User;
  getAccessTokenSilently: () => Promise<string>;
  loginWithRedirect: (options?: any) => Promise<void>;
  logout: (options?: any) => void;
}

/**
 * Unified authentication service that wraps Auth0 React SDK
 * This service requires Auth0 context to be passed from React components
 * since useAuth0 can only be used within React components
 */
export class UnifiedAuthService {
  private auth0Context: Auth0Context | null = null;

  /**
   * Initialize the service with Auth0 context from a React component
   * This must be called before using other methods
   */
  initialize(auth0Context: Auth0Context): void {
    this.auth0Context = auth0Context;
  }

  /**
   * Check if the service is properly initialized
   */
  private ensureInitialized(): void {
    if (!this.auth0Context) {
      throw new Error('UnifiedAuthService must be initialized with Auth0 context before use');
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    if (!this.auth0Context) {
      // Return false if not initialized yet (guest user)
      return false;
    }
    return this.auth0Context.isAuthenticated;
  }

  /**
   * Check if authentication is loading
   */
  isLoading(): boolean {
    this.ensureInitialized();
    return this.auth0Context!.isLoading;
  }

  /**
   * Get access token for API requests
   */
  async getToken(): Promise<string | null> {
    this.ensureInitialized();
    
    if (!this.auth0Context!.isAuthenticated) {
      return null;
    }

    try {
      return await this.auth0Context!.getAccessTokenSilently();
    } catch (error) {
      console.error('Error getting access token:', error);
      return null;
    }
  }

  /**
   * Get user profile information
   */
  getUserProfile(): UserProfile | null {
    this.ensureInitialized();
    
    if (!this.auth0Context!.isAuthenticated || !this.auth0Context!.user) {
      return null;
    }

    const user = this.auth0Context!.user;
    const userConsent = this.getUserConsent();

    return {
      sub: user.sub || '',
      email: user.email,
      phone_number: user.phone_number,
      name: user.name,
      picture: user.picture,
      updated_at: user.updated_at || new Date().toISOString(),
      marketingConsent: userConsent?.marketingConsent
    };
  }

  /**
   * Login with redirect
   */
  async login(): Promise<void> {
    this.ensureInitialized();
    this.saveReturnPath();
    
    return this.auth0Context!.loginWithRedirect({
      openUrl: (url: string) => {
        console.log("🔍 Authorize URL about to be called:", url);
        window.location.assign(url);
      }
    });
  }

  /**
   * Logout
   */
  logout(): void {
    this.ensureInitialized();
    
    return this.auth0Context!.logout({
      logoutParams: {
        returnTo: window.location.origin
      }
    });
  }

  /**
   * Get authentication headers for API requests
   */
  async getAuthHeaders(): Promise<Record<string, string>> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    // Only add auth headers if service is initialized and user is authenticated
    if (this.auth0Context && this.isAuthenticated()) {
      const token = await this.getToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    }else{
      const fingerprint = browserFingerprintService.getFingerprint(true);
      headers['x-session-id'] = fingerprint;
    }

    return headers;
  }

  // === Return Path Management ===

  /**
   * Saves the current path to return to after login
   */
  saveReturnPath(): void {
    localStorage.setItem(STORAGE_KEYS.AUTH_RETURN_TO, window.location.pathname);
  }

  /**
   * Gets the saved return path
   */
  getReturnPath(): string | null {
    return localStorage.getItem(STORAGE_KEYS.AUTH_RETURN_TO);
  }

  /**
   * Clears the saved return path
   */
  clearReturnPath(): void {
    localStorage.removeItem(STORAGE_KEYS.AUTH_RETURN_TO);
  }

  // === User Consent Management ===

  /**
   * Saves user consent information
   */
  saveUserConsent(consent: UserConsent): void {
    localStorage.setItem(STORAGE_KEYS.MARKETING_CONSENT, consent.marketingConsent ? 'true' : 'false');
    localStorage.setItem(STORAGE_KEYS.CONSENT_TIMESTAMP, consent.timestamp);
  }

  /**
   * Gets user consent information
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

  // === Guest User Management ===

  /**
   * Gets the number of remaining message credits for guest users
   */
  getRemainingGuestActions(): number {
    // If not initialized or authenticated, treat as guest user
    if (!this.auth0Context || !this.isAuthenticated()) {
      return UserActionService.getRemainingActions();
    }
    return Infinity; // Authenticated users have unlimited actions
  }

  /**
   * Increments the guest credit usage count
   */
  incrementGuestAction(actionType = 'chat'): boolean {
    // If not initialized or authenticated, treat as guest user
    if (!this.auth0Context || !this.isAuthenticated()) {
      return UserActionService.trackAction(actionType as any);
    }
    return true; // Authenticated users can always perform actions
  }

  /**
   * Checks if the guest credit limit is reached
   */
  isGuestLimitReached(): boolean {
    // If not initialized or authenticated, check guest limits
    if (!this.auth0Context || !this.isAuthenticated()) {
      return this.getRemainingGuestActions() <= 0;
    }
    return false; // Authenticated users never reach the limit
  }

  /**
   * Resets the guest credit count
   */
  resetGuestActions(): void {
    UserActionService.resetActions();
  }
}

// Create a singleton instance
export const unifiedAuthService = new UnifiedAuthService();