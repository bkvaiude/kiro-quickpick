import { vi } from 'vitest';

/**
 * Helper function to mock Date in tests
 * @param isoString ISO date string to mock
 */
export function mockDate(isoString: string) {
  const mockDate = new Date(isoString);
  
  // Save original Date
  const OriginalDate = global.Date;
  
  // Mock Date constructor
  const MockDateConstructor = function(...args: any[]) {
    if (args.length === 0) {
      return mockDate;
    }
    return new OriginalDate(...args);
  } as unknown as DateConstructor;
  
  // Copy prototype and static methods
  MockDateConstructor.prototype = OriginalDate.prototype;
  Object.setPrototypeOf(MockDateConstructor, OriginalDate);
  
  // Mock Date.now()
  MockDateConstructor.now = () => mockDate.getTime();
  
  // Replace global Date
  global.Date = MockDateConstructor;
  
  // Return cleanup function
  return () => {
    global.Date = OriginalDate;
  };
}

/**
 * Helper function to mock Date.now() without affecting the Date constructor
 * @param timestamp Timestamp to return from Date.now()
 */
export function mockDateNow(timestamp: number) {
  const originalNow = Date.now;
  Date.now = vi.fn(() => timestamp);
  
  // Return cleanup function
  return () => {
    Date.now = originalNow;
  };
}