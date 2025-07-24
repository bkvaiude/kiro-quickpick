import { API_BASE_URL } from '../config';

// Consent interfaces
export interface ConsentData {
  terms_accepted: boolean;
  marketing_consent: boolean;
}

export interface ConsentResponse extends ConsentData {
  user_id: string;
  timestamp: string;
}

/**
 * Service for managing user consent
 */
export const ConsentService = {
  /**
   * Creates a new consent record for the current user
   * @param consentData The consent data to store
   * @param token The authentication token
   * @returns Promise with the created consent record
   */
  async createConsent(consentData: ConsentData, token: string): Promise<ConsentResponse> {
    if (!token) {
      throw new Error('User must be authenticated to create consent');
    }
    
    const response = await fetch(`${API_BASE_URL}/consent`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(consentData)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create consent record');
    }
    
    return await response.json();
  },
  
  /**
   * Gets the current user's consent record
   * @param token The authentication token
   * @returns Promise with the user's consent record
   */
  async getMyConsent(token: string): Promise<ConsentResponse | null> {
    if (!token) {
      throw new Error('User must be authenticated to get consent');
    }
    
    const response = await fetch(`${API_BASE_URL}/consent/me`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!response.ok) {
      // If the consent record doesn't exist, return null
      if (response.status === 404) {
        return null;
      }
      
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get consent record');
    }
    
    return await response.json();
  },
  
  /**
   * Updates the current user's consent record
   * @param consentData The consent data to update
   * @param token The authentication token
   * @returns Promise with the updated consent record
   */
  async updateMyConsent(consentData: Partial<ConsentData>, token: string): Promise<ConsentResponse> {
    if (!token) {
      throw new Error('User must be authenticated to update consent');
    }
    
    const response = await fetch(`${API_BASE_URL}/consent/me`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(consentData)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update consent record');
    }
    
    return await response.json();
  },
  
  /**
   * Synchronizes consent information between local storage and the backend
   * @param isAuthenticated Whether the user is authenticated
   * @param getToken Function to get the authentication token
   * @param getUserConsent Function to get the user's consent from local storage
   */
  async syncConsent(
    isAuthenticated: boolean,
    getToken: () => Promise<string | null>,
    getUserConsent: () => { marketingConsent: boolean; timestamp: string } | null
  ): Promise<void> {
    // Only proceed if the user is authenticated
    if (!isAuthenticated) {
      return;
    }
    
    try {
      const token = await getToken();
      if (!token) return;
      
      // Get the local consent information
      const localConsent = getUserConsent();
      
      // If we have local consent information, try to get the backend consent
      if (localConsent) {
        try {
          // Try to get the backend consent
          const backendConsent = await this.getMyConsent(token);
          
          // If the backend consent exists, update the local consent if needed
          if (backendConsent) {
            // If the marketing consent is different, update the backend
            if (backendConsent.marketing_consent !== localConsent.marketingConsent) {
              await this.updateMyConsent({
                marketing_consent: localConsent.marketingConsent
              }, token);
            }
          } else {
            // If the backend consent doesn't exist, create it
            await this.createConsent({
              terms_accepted: true, // Terms must be accepted
              marketing_consent: localConsent.marketingConsent
            }, token);
          }
        } catch (error) {
          console.error('Failed to sync consent:', error);
        }
      }
    } catch (error) {
      console.error('Failed to sync consent:', error);
    }
  }
};