import { useState, useEffect, useCallback } from 'react';
import { CreditService, CreditStatus } from '../services/creditService';
import { useAuthContext as useAuth } from '../auth/AuthContext';

export interface CreditDisplayInfo {
  available: number;
  max: number;
  isGuest: boolean;
  percentage: number;
  colorClass: string;
  progressColor: string;
  canReset: boolean;
  nextResetTime?: string;
}

export function useCredits() {
  const { isAuthenticated } = useAuth();
  const [creditInfo, setCreditInfo] = useState<CreditDisplayInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCredits = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const status = await CreditService.getCreditStatus();
      const displayInfo = await CreditService.getCreditDisplayInfo();
      
      setCreditInfo({
        ...displayInfo,
        canReset: status.can_reset,
        nextResetTime: status.next_reset_time,
      });
    } catch (err) {
      setError('Failed to fetch credit information');
      console.error('Error fetching credits:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const hasCredits = useCallback(async (): Promise<boolean> => {
    try {
      return await CreditService.hasCredits();
    } catch (err) {
      console.error('Error checking credits:', err);
      return false;
    }
  }, []);

  const refreshCredits = useCallback(() => {
    fetchCredits();
  }, [fetchCredits]);

  useEffect(() => {
    fetchCredits();
  }, [fetchCredits, isAuthenticated]);

  return {
    creditInfo,
    isLoading,
    error,
    hasCredits,
    refreshCredits,
  };
}