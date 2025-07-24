/**
 * JWT utility functions for decoding tokens
 */

export interface DecodedToken {
  // Standard JWT claims
  iss?: string; // Issuer
  sub?: string; // Subject (user ID)
  aud?: string | string[]; // Audience
  exp?: number; // Expiration time
  iat?: number; // Issued at
  nbf?: number; // Not before
  jti?: string; // JWT ID
  
  // Auth0 specific claims
  email?: string;
  email_verified?: boolean;
  name?: string;
  nickname?: string;
  picture?: string;
  updated_at?: string;
  
  // Custom claims (namespace prefixed)
  [key: string]: any;
}

/**
 * Decode a JWT token without verification (client-side only)
 * Note: This is for display purposes only, never trust client-side decoded tokens for security
 */
export function decodeJWT(token: string): DecodedToken | null {
  try {
    // JWT has 3 parts separated by dots
    const parts = token.split('.');
    if (parts.length !== 3) {
      throw new Error('Invalid JWT format');
    }

    // Decode the payload (second part)
    const payload = parts[1];
    
    // Add padding if needed for base64 decoding
    const paddedPayload = payload + '='.repeat((4 - payload.length % 4) % 4);
    
    // Decode base64url
    const decodedPayload = atob(paddedPayload.replace(/-/g, '+').replace(/_/g, '/'));
    
    // Parse JSON
    return JSON.parse(decodedPayload);
  } catch (error) {
    console.error('Error decoding JWT:', error);
    return null;
  }
}

/**
 * Format timestamp to readable date
 */
export function formatTimestamp(timestamp?: number): string {
  if (!timestamp) return 'N/A';
  
  try {
    return new Date(timestamp * 1000).toLocaleString();
  } catch (error) {
    return 'Invalid date';
  }
}

/**
 * Check if token is expired
 */
export function isTokenExpired(token: DecodedToken): boolean {
  if (!token.exp) return false;
  
  const now = Math.floor(Date.now() / 1000);
  return token.exp < now;
}

/**
 * Get time until token expires
 */
export function getTimeUntilExpiry(token: DecodedToken): string {
  if (!token.exp) return 'No expiration';
  
  const now = Math.floor(Date.now() / 1000);
  const timeLeft = token.exp - now;
  
  if (timeLeft <= 0) return 'Expired';
  
  const hours = Math.floor(timeLeft / 3600);
  const minutes = Math.floor((timeLeft % 3600) / 60);
  
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  } else {
    return `${minutes}m`;
  }
}