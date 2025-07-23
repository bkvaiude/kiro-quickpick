import { vi } from 'vitest';
import { render, RenderOptions } from '@testing-library/react';
import { ReactElement } from 'react';

/**
 * Helper function to mock Date in tests
 * @param isoDate ISO date string to mock
 * @returns Cleanup function to restore the original Date
 */
export function mockDate(isoDate: string) {
  const realDate = global.Date;
  const mockDate = new Date(isoDate);
  
  // Mock Date constructor
  global.Date = class extends Date {
    constructor(...args: any[]) {
      if (args.length === 0) {
        super(mockDate);
      } else {
        super(...args);
      }
    }
    
    // Mock Date.now()
    static now() {
      return mockDate.getTime();
    }
  } as DateConstructor;
  
  // Ensure toISOString works
  Object.defineProperty(global.Date.prototype, 'toISOString', {
    value: function() {
      return new realDate(this.valueOf()).toISOString();
    }
  });
  
  // Return cleanup function
  return () => {
    global.Date = realDate;
  };
}

/**
 * Helper function to mock localStorage in tests
 */
export function mockLocalStorage() {
  const store: Record<string, string> = {};
  
  const localStorageMock = {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value.toString();
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      Object.keys(store).forEach(key => delete store[key]);
    }),
    length: 0,
    key: vi.fn((index: number) => Object.keys(store)[index] || null),
  };
  
  Object.defineProperty(window, 'localStorage', {
    value: localStorageMock,
    writable: true
  });
  
  return localStorageMock;
}

/**
 * Helper function to mock window.matchMedia
 */
export function mockMatchMedia(matches = false) {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation(query => ({
      matches,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
}

/**
 * Custom render function that includes common providers
 * @param ui Component to render
 * @param options Render options
 * @returns Result of render
 */
export function renderWithProviders(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  // Add providers here as needed
  return render(ui, { ...options });
}