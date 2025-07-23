import { UserActionService, ActionType } from './userActionService';
import { AuthService } from './authService';

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
    if (AuthService.isAuthenticated()) {
      return true;
    }
    
    // Check if the guest limit is reached
    if (AuthService.isGuestLimitReached()) {
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
    if (AuthService.isAuthenticated()) {
      return true;
    }
    
    // Check if the guest limit is reached
    return !AuthService.isGuestLimitReached();
  },
  
  /**
   * Get the number of remaining actions for the current user
   * @returns Number of remaining actions (Infinity for authenticated users)
   */
  getRemainingActions(): number {
    return AuthService.getRemainingGuestActions();
  }
};