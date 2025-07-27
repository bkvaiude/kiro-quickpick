import { unifiedAuthService, type Auth0Context } from './unifiedAuthService';

/**
 * Factory function to create auth-enabled service instances
 * This allows services to access auth functionality when called from React components
 */
export function createAuthEnabledService<T>(
  serviceFactory: (authService: typeof unifiedAuthService) => T,
  auth0Context: Auth0Context
): T {
  // Initialize the unified auth service with the provided context
  unifiedAuthService.initialize(auth0Context);
  
  // Return the service instance with auth capabilities
  return serviceFactory(unifiedAuthService);
}

/**
 * Hook-like function to get an auth-enabled API service
 * Must be called from within a React component that has access to useAuth0
 */
export function useAuthEnabledApiService(auth0Context: Auth0Context) {
  unifiedAuthService.initialize(auth0Context);
  return unifiedAuthService;
}