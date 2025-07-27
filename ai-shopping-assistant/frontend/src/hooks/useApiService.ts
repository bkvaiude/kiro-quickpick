import { useAuth0 } from '@auth0/auth0-react';
import { useEffect } from 'react';
import { unifiedAuthService } from '../services/unifiedAuthService';
import { ApiService } from '../services/api';

/**
 * Hook to initialize auth context for services that need it
 * This ensures the unifiedAuthService is properly initialized before API calls
 */
export function useApiService() {
  const auth0Context = useAuth0();

  useEffect(() => {
    unifiedAuthService.initialize(auth0Context);
  }, [auth0Context]);

  return ApiService;
}