import { UserActionService } from './userActionService';

// Storage keys
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

// Authentication state interface
export interface AuthState {
  isAuthenticated: boolean;
  token: string | null;
  expiresAt: number;
  user: UserProfile | null;
}

/**
 * Service for handling Auth0 authentication
 * This service provides methods to interact with Auth0 authentication
 * and user consent management
 */
export const AuthService = {
  /**
   * Saves the current path to return to after login
   */
  saveReturnPath(): void {
    localStorage.setItem(STORAGE_KEYS.AUTH_RETURN_TO, window.location.pathname);
  },

  /**
   * Gets the saved return path
   * @returns The saved return path or null if not available
   */
  getReturnPath(): string | null {
    return localStorage.getItem(STORAGE_KEYS.AUTH_RETURN_TO);
  },

  /**
   * Clears the saved return path
   */
  clearReturnPath(): void {
    localStorage.removeItem(STORAGE_KEYS.AUTH_RETURN_TO);
  },

  /**
   * Gets the number of remaining actions for guest users
   * @returns Number of remaining actions
   */
  getRemainingGuestActions(): number {
    return UserActionService.getRemainingActions();
  },

  /**
   * Increments the guest action count
   * @param actionType The type of action being performed (defaults to 'chat')
   * @returns True if the action was counted, false if the limit is reached
   */
  incrementGuestAction(actionType = 'chat'): boolean {
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
   * Saves user consent information
   * @param consent User consent information
   */
  saveUserConsent(consent: UserConsent): void {
    localStorage.setItem(STORAGE_KEYS.MARKETING_CONSENT, consent.marketingConsent ? 'true' : 'false');
    localStorage.setItem(STORAGE_KEYS.CONSENT_TIMESTAMP, consent.timestamp);
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