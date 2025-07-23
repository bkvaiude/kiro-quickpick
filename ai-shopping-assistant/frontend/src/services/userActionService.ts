import { LocalStorageService } from './localStorage';

// Action types that count toward guest limits
export const ActionType = {
  CHAT: 'chat',
  SEARCH: 'search'
} as const;

export type ActionType = typeof ActionType[keyof typeof ActionType];

// Storage keys
const STORAGE_KEYS = {
  GUEST_ACTIONS: 'guest_actions',
  GUEST_ACTION_HISTORY: 'guest_action_history'
};

// Maximum number of actions for guest users
const MAX_GUEST_ACTIONS = 10;

// Interface for tracking individual actions
export interface UserAction {
  type: ActionType;
  timestamp: string; // ISO string format
}

/**
 * Service for tracking and managing user actions
 */
export const UserActionService = {
  /**
   * Track a new user action
   * @param actionType The type of action being performed
   * @returns True if the action was counted, false if the limit is reached
   */
  trackAction(actionType: ActionType): boolean {
    // Get current action count
    const currentCount = this.getActionCount();
    
    // Check if limit is reached
    if (currentCount >= MAX_GUEST_ACTIONS) {
      return false;
    }
    
    // Record the action
    this.storeAction(actionType);
    
    // Increment the counter
    this.setActionCount(currentCount + 1);
    
    return true;
  },

  /**
   * Get the total number of actions performed by the guest user
   * @returns Number of actions performed
   */
  getActionCount(): number {
    try {
      const countStr = localStorage.getItem(STORAGE_KEYS.GUEST_ACTIONS);
      return countStr ? parseInt(countStr, 10) : 0;
    } catch (error) {
      console.error('Error getting action count:', error);
      return 0;
    }
  },

  /**
   * Set the action count to a specific value
   * @param count The new action count
   */
  setActionCount(count: number): void {
    try {
      localStorage.setItem(STORAGE_KEYS.GUEST_ACTIONS, count.toString());
    } catch (error) {
      console.error('Error setting action count:', error);
    }
  },

  /**
   * Store details about an action for analytics purposes
   * @param actionType The type of action being performed
   */
  storeAction(actionType: ActionType): void {
    try {
      // Get existing action history
      const historyStr = localStorage.getItem(STORAGE_KEYS.GUEST_ACTION_HISTORY);
      const history: UserAction[] = historyStr ? JSON.parse(historyStr) : [];
      
      // Add new action
      const newAction: UserAction = {
        type: actionType,
        timestamp: new Date().toISOString()
      };
      
      // Limit history size to prevent excessive storage usage
      const updatedHistory = [...history, newAction].slice(-50);
      
      // Save updated history
      localStorage.setItem(STORAGE_KEYS.GUEST_ACTION_HISTORY, JSON.stringify(updatedHistory));
    } catch (error) {
      console.error('Error storing action:', error);
    }
  },

  /**
   * Get the action history
   * @returns Array of user actions
   */
  getActionHistory(): UserAction[] {
    try {
      const historyStr = localStorage.getItem(STORAGE_KEYS.GUEST_ACTION_HISTORY);
      return historyStr ? JSON.parse(historyStr) : [];
    } catch (error) {
      console.error('Error getting action history:', error);
      return [];
    }
  },

  /**
   * Get the number of remaining actions for guest users
   * @returns Number of remaining actions
   */
  getRemainingActions(): number {
    const currentCount = this.getActionCount();
    return Math.max(0, MAX_GUEST_ACTIONS - currentCount);
  },

  /**
   * Check if the guest action limit is reached
   * @returns True if the limit is reached, false otherwise
   */
  isLimitReached(): boolean {
    return this.getRemainingActions() <= 0;
  },

  /**
   * Reset the guest action count and history
   */
  resetActions(): void {
    try {
      localStorage.removeItem(STORAGE_KEYS.GUEST_ACTIONS);
      localStorage.removeItem(STORAGE_KEYS.GUEST_ACTION_HISTORY);
    } catch (error) {
      console.error('Error resetting actions:', error);
    }
  },
  
  /**
   * Get the maximum number of actions allowed for guest users
   * @returns Maximum number of actions
   */
  getMaxActions(): number {
    return MAX_GUEST_ACTIONS;
  }
};