import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest';
import { ActionTrackingService } from './actionTrackingService';
import { UserActionService, ActionType } from './userActionService';
import { AuthService } from './authService';

// Mock dependencies
vi.mock('./userActionService', () => ({
  UserActionService: {
    trackAction: vi.fn(),
    ActionType: {
      CHAT: 'chat',
      SEARCH: 'search'
    }
  }
}));

vi.mock('./authService', () => ({
  AuthService: {
    isAuthenticated: vi.fn(),
    isGuestLimitReached: vi.fn(),
    getRemainingGuestActions: vi.fn()
  }
}));

describe('ActionTrackingService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('trackApiAction', () => {
    test('should return true for authenticated users without tracking', () => {
      (AuthService.isAuthenticated as any).mockReturnValueOnce(true);
      
      const result = ActionTrackingService.trackApiAction(ActionType.CHAT);
      
      expect(result).toBe(true);
      expect(UserActionService.trackAction).not.toHaveBeenCalled();
    });

    test('should return false if guest limit is reached', () => {
      (AuthService.isAuthenticated as any).mockReturnValueOnce(false);
      (AuthService.isGuestLimitReached as any).mockReturnValueOnce(true);
      
      const result = ActionTrackingService.trackApiAction(ActionType.CHAT);
      
      expect(result).toBe(false);
      expect(UserActionService.trackAction).not.toHaveBeenCalled();
    });

    test('should track action for guest users with remaining actions', () => {
      (AuthService.isAuthenticated as any).mockReturnValueOnce(false);
      (AuthService.isGuestLimitReached as any).mockReturnValueOnce(false);
      (UserActionService.trackAction as any).mockReturnValueOnce(true);
      
      const result = ActionTrackingService.trackApiAction(ActionType.SEARCH);
      
      expect(result).toBe(true);
      expect(UserActionService.trackAction).toHaveBeenCalledWith(ActionType.SEARCH);
    });

    test('should return false if tracking fails', () => {
      (AuthService.isAuthenticated as any).mockReturnValueOnce(false);
      (AuthService.isGuestLimitReached as any).mockReturnValueOnce(false);
      (UserActionService.trackAction as any).mockReturnValueOnce(false);
      
      const result = ActionTrackingService.trackApiAction(ActionType.CHAT);
      
      expect(result).toBe(false);
      expect(UserActionService.trackAction).toHaveBeenCalledWith(ActionType.CHAT);
    });
  });

  describe('isActionAllowed', () => {
    test('should return true for authenticated users', () => {
      (AuthService.isAuthenticated as any).mockReturnValueOnce(true);
      
      const result = ActionTrackingService.isActionAllowed(ActionType.CHAT);
      
      expect(result).toBe(true);
      expect(AuthService.isGuestLimitReached).not.toHaveBeenCalled();
    });

    test('should return false if guest limit is reached', () => {
      (AuthService.isAuthenticated as any).mockReturnValueOnce(false);
      (AuthService.isGuestLimitReached as any).mockReturnValueOnce(true);
      
      const result = ActionTrackingService.isActionAllowed(ActionType.SEARCH);
      
      expect(result).toBe(false);
    });

    test('should return true for guest users with remaining actions', () => {
      (AuthService.isAuthenticated as any).mockReturnValueOnce(false);
      (AuthService.isGuestLimitReached as any).mockReturnValueOnce(false);
      
      const result = ActionTrackingService.isActionAllowed(ActionType.CHAT);
      
      expect(result).toBe(true);
    });
  });

  describe('getRemainingActions', () => {
    test('should delegate to AuthService.getRemainingGuestActions', () => {
      (AuthService.getRemainingGuestActions as any).mockReturnValueOnce(5);
      
      const result = ActionTrackingService.getRemainingActions();
      
      expect(result).toBe(5);
      expect(AuthService.getRemainingGuestActions).toHaveBeenCalled();
    });

    test('should return Infinity for authenticated users', () => {
      (AuthService.getRemainingGuestActions as any).mockReturnValueOnce(Infinity);
      
      const result = ActionTrackingService.getRemainingActions();
      
      expect(result).toBe(Infinity);
    });
  });
});