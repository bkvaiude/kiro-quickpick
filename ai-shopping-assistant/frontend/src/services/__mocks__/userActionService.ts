// Mock implementation of UserActionService
export const ActionType = {
  CHAT: 'chat',
  SEARCH: 'search'
} as const;

export type ActionType = typeof ActionType[keyof typeof ActionType];

export const UserActionService = {
  trackAction: vi.fn().mockReturnValue(true),
  getActionCount: vi.fn().mockReturnValue(5),
  setActionCount: vi.fn(),
  storeAction: vi.fn(),
  getActionHistory: vi.fn().mockReturnValue([]),
  getRemainingActions: vi.fn().mockReturnValue(5),
  isLimitReached: vi.fn().mockReturnValue(false),
  resetActions: vi.fn(),
  getMaxActions: vi.fn().mockReturnValue(10)
};