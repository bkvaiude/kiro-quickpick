import { UserActionService, ActionType } from './userActionService';
import { unifiedAuthService } from './unifiedAuthService';

/**
 * Service for tracking user actions in API calls
 */
export const ActionTrackingService = {
  /**
   * Track an API call as a user action
   * @param actionType The type of action being performed
   * @returns True if the action is allowed, false if the limit is reached
   */
  trackApiAction(actionType: ActionType): boolean {
    // Authenticated users can always perform actions
    if (unifiedAuthService.isAuthenticated()) {
      return true;
    }
    
    // Check if the guest limit is reached
    if (unifiedAuthService.isGuestLimitReached()) {
      return false;
    }
    
    // Track the action
    return UserActionService.trackAction(actionType);
  },
  
  /**
   * Check if an action is allowed based on user's authentication status and action limits
   * @param actionType The type of action being checked
   * @returns True if the action is allowed, false otherwise
   */
  isActionAllowed(actionType: ActionType): boolean {
    // Authenticated users can always perform actions
    if (unifiedAuthService.isAuthenticated()) {
      return true;
    }
    
    // Check if the guest limit is reached
    return !unifiedAuthService.isGuestLimitReached();
  },
  
  /**
   * Get the number of remaining actions for the current user
   * @returns Number of remaining actions (Infinity for authenticated users)
   */
  getRemainingActions(): number {
    return unifiedAuthService.getRemainingGuestActions();
  }
};