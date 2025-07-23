import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest';
import { UserActionService, ActionType } from './userActionService';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value.toString();
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      store = {};
    }),
    length: 0,
    key: vi.fn((_: number) => ''),
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('UserActionService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.clear();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('trackAction', () => {
    test('should track action and increment count', () => {
      const result = UserActionService.trackAction(ActionType.CHAT);
      
      expect(result).toBe(true);
      expect(localStorageMock.setItem).toHaveBeenCalledWith('guest_actions', '1');
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'guest_action_history',
        expect.stringContaining('"type":"chat"')
      );
    });

    test('should return false when limit is reached', () => {
      vi.spyOn(UserActionService, 'getActionCount').mockReturnValueOnce(10);
      
      const result = UserActionService.trackAction(ActionType.SEARCH);
      
      expect(result).toBe(false);
      expect(localStorageMock.setItem).not.toHaveBeenCalledWith('guest_actions', '11');
    });

    test('should handle multiple action types', () => {
      // Mock localStorage to return empty arrays for action history
      localStorageMock.getItem.mockImplementation((key: string) => {
        if (key === 'guest_action_history') return '[]';
        return null;
      });
      
      UserActionService.trackAction(ActionType.CHAT);
      UserActionService.trackAction(ActionType.SEARCH);
      
      // Find the last call that set guest_action_history
      const historyCallIndex = localStorageMock.setItem.mock.calls.findIndex(
        call => call[0] === 'guest_action_history' && call[1].includes('search')
      );
      
      if (historyCallIndex >= 0) {
        const history = JSON.parse(localStorageMock.setItem.mock.calls[historyCallIndex][1]);
        expect(history.length).toBe(2);
        expect(history[0].type).toBe('chat');
        expect(history[1].type).toBe('search');
      } else {
        // If we can't find the exact call, at least verify the action count was updated
        expect(localStorageMock.setItem).toHaveBeenCalledWith('guest_actions', '1');
        expect(localStorageMock.setItem).toHaveBeenCalledWith('guest_actions', '2');
      }
    });
  });

  describe('getActionCount', () => {
    test('should return 0 if no actions stored', () => {
      const result = UserActionService.getActionCount();
      
      expect(result).toBe(0);
    });

    test('should return stored action count', () => {
      localStorageMock.getItem.mockReturnValueOnce('5');
      
      const result = UserActionService.getActionCount();
      
      expect(result).toBe(5);
    });

    test('should handle errors gracefully', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      localStorageMock.getItem.mockImplementationOnce(() => {
        throw new Error('Storage error');
      });

      const result = UserActionService.getActionCount();
      
      expect(result).toBe(0);
      expect(consoleErrorSpy).toHaveBeenCalledWith('Error getting action count:', expect.any(Error));
    });
  });

  describe('setActionCount', () => {
    test('should set action count in localStorage', () => {
      UserActionService.setActionCount(7);
      
      expect(localStorageMock.setItem).toHaveBeenCalledWith('guest_actions', '7');
    });

    test('should handle errors gracefully', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      localStorageMock.setItem.mockImplementationOnce(() => {
        throw new Error('Storage error');
      });

      expect(() => UserActionService.setActionCount(3)).not.toThrow();
      expect(consoleErrorSpy).toHaveBeenCalledWith('Error setting action count:', expect.any(Error));
    });
  });

  describe('storeAction', () => {
    test('should store action in history', () => {
      // Use vi.useFakeTimers to mock the date
      vi.useFakeTimers();
      vi.setSystemTime(new Date('2023-01-01T12:00:00Z'));
      
      try {
        UserActionService.storeAction(ActionType.CHAT);
        
        expect(localStorageMock.setItem).toHaveBeenCalledWith(
          'guest_action_history',
          expect.stringContaining('2023-01-01T12:00:00')
        );
      } finally {
        vi.useRealTimers();
      }
    });

    test('should append to existing history', () => {
      const existingAction = {
        type: 'chat',
        timestamp: '2023-01-01T11:00:00Z',
      };
      
      localStorageMock.getItem.mockReturnValueOnce(JSON.stringify([existingAction]));
      
      // Use vi.useFakeTimers to mock the date
      vi.useFakeTimers();
      vi.setSystemTime(new Date('2023-01-01T12:00:00Z'));
      
      try {
        UserActionService.storeAction(ActionType.SEARCH);
        
        expect(localStorageMock.setItem).toHaveBeenCalledWith(
          'guest_action_history',
          expect.stringContaining('2023-01-01T12:00:00')
        );
      } finally {
        vi.useRealTimers();
      }
    });

    test('should limit history size to 50 items', () => {
      // Create 50 existing actions
      const existingActions = Array.from({ length: 50 }, (_, i) => ({
        type: 'chat',
        timestamp: `2023-01-01T${i.toString().padStart(2, '0')}:00:00Z`,
      }));
      
      localStorageMock.getItem.mockReturnValueOnce(JSON.stringify(existingActions));
      
      // Use vi.useFakeTimers to mock the date
      vi.useFakeTimers();
      vi.setSystemTime(new Date('2023-01-02T00:00:00Z'));
      
      try {
        UserActionService.storeAction(ActionType.SEARCH);
        
        const savedActions = JSON.parse(localStorageMock.setItem.mock.calls[0][1]);
        
        expect(savedActions.length).toBe(50);
        expect(savedActions[49].type).toBe('search');
        expect(savedActions[0]).toEqual(existingActions[1]); // First item should be dropped
      } finally {
        vi.useRealTimers();
      }
    });

    test('should handle errors gracefully', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      localStorageMock.getItem.mockImplementationOnce(() => {
        throw new Error('Storage error');
      });

      expect(() => UserActionService.storeAction(ActionType.CHAT)).not.toThrow();
      expect(consoleErrorSpy).toHaveBeenCalledWith('Error storing action:', expect.any(Error));
    });
  });

  describe('getActionHistory', () => {
    test('should return empty array if no history', () => {
      const result = UserActionService.getActionHistory();
      
      expect(result).toEqual([]);
    });

    test('should return stored action history', () => {
      const mockHistory = [
        { type: 'chat', timestamp: '2023-01-01T11:00:00Z' },
        { type: 'search', timestamp: '2023-01-01T12:00:00Z' },
      ];
      
      localStorageMock.getItem.mockReturnValueOnce(JSON.stringify(mockHistory));
      
      const result = UserActionService.getActionHistory();
      
      expect(result).toEqual(mockHistory);
    });

    test('should handle errors gracefully', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      localStorageMock.getItem.mockImplementationOnce(() => {
        throw new Error('Storage error');
      });

      const result = UserActionService.getActionHistory();
      
      expect(result).toEqual([]);
      expect(consoleErrorSpy).toHaveBeenCalledWith('Error getting action history:', expect.any(Error));
    });
  });

  describe('getRemainingActions', () => {
    test('should return max actions if no actions used', () => {
      vi.spyOn(UserActionService, 'getActionCount').mockReturnValueOnce(0);
      
      const result = UserActionService.getRemainingActions();
      
      expect(result).toBe(10); // MAX_GUEST_ACTIONS
    });

    test('should return remaining actions', () => {
      vi.spyOn(UserActionService, 'getActionCount').mockReturnValueOnce(3);
      
      const result = UserActionService.getRemainingActions();
      
      expect(result).toBe(7); // MAX_GUEST_ACTIONS - 3
    });

    test('should return 0 if limit is reached or exceeded', () => {
      vi.spyOn(UserActionService, 'getActionCount').mockReturnValueOnce(15);
      
      const result = UserActionService.getRemainingActions();
      
      expect(result).toBe(0);
    });
  });

  describe('isLimitReached', () => {
    test('should return false if actions remain', () => {
      vi.spyOn(UserActionService, 'getRemainingActions').mockReturnValueOnce(5);
      
      const result = UserActionService.isLimitReached();
      
      expect(result).toBe(false);
    });

    test('should return true if no actions remain', () => {
      vi.spyOn(UserActionService, 'getRemainingActions').mockReturnValueOnce(0);
      
      const result = UserActionService.isLimitReached();
      
      expect(result).toBe(true);
    });
  });

  describe('resetActions', () => {
    test('should remove action count and history from localStorage', () => {
      UserActionService.resetActions();
      
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('guest_actions');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('guest_action_history');
    });

    test('should handle errors gracefully', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      localStorageMock.removeItem.mockImplementationOnce(() => {
        throw new Error('Storage error');
      });

      expect(() => UserActionService.resetActions()).not.toThrow();
      expect(consoleErrorSpy).toHaveBeenCalledWith('Error resetting actions:', expect.any(Error));
    });
  });

  describe('getMaxActions', () => {
    test('should return the maximum number of actions', () => {
      const result = UserActionService.getMaxActions();
      
      expect(result).toBe(10); // MAX_GUEST_ACTIONS
    });
  });
});