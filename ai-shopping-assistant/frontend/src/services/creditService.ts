import { API_BASE_URL } from '../config';
import { unifiedAuthService } from './unifiedAuthService';


export interface CreditStatus {
  available_credits: number;
  max_credits: number;
  is_guest: boolean;
  can_reset: boolean;
  next_reset_time?: string;
}

export class CreditService {

  /**
   * Get authentication headers for API requests
   */
  private static async getAuthHeaders(): Promise<Record<string, string>> {
    return await unifiedAuthService.getAuthHeaders();
  }

  /**
   * Get credit status for the current user
   */
  static async getCreditStatus(): Promise<CreditStatus> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/credits/status`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching credit status:', error);
      // Return default values for guest users if API fails
      return {
        available_credits: 10,
        max_credits: 10,
        is_guest: true,
        can_reset: false,
      };
    }
  }

  /**
   * Check if user has sufficient credits
   */
  static async hasCredits(): Promise<boolean> {
    const status = await this.getCreditStatus();
    return status.available_credits > 0;
  }

  /**
   * Get credit information for display purposes
   */
  static async getCreditDisplayInfo(): Promise<{
    available: number;
    max: number;
    isGuest: boolean;
    percentage: number;
    colorClass: string;
    progressColor: string;
  }> {
    const status = await this.getCreditStatus();
    
    const percentage = Math.max(0, Math.min(100, (status.available_credits / status.max_credits) * 100));
    
    // Determine colors based on remaining credits
    let colorClass = 'text-muted-foreground';
    let progressColor = 'bg-primary';
    
    if (status.available_credits <= 2) {
      colorClass = 'text-destructive';
      progressColor = 'bg-destructive';
    } else if (status.available_credits <= 5) {
      colorClass = 'text-warning';
      progressColor = 'bg-warning';
    }
    
    return {
      available: status.available_credits,
      max: status.max_credits,
      isGuest: status.is_guest,
      percentage,
      colorClass,
      progressColor,
    };
  }
}