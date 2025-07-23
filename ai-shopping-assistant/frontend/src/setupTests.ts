import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // Deprecated
    removeListener: vi.fn(), // Deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

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
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Fix for Date mock in tests
const RealDate = Date;

// Create a mock Date constructor that properly handles being called with or without new
const MockDate = function(...args: any[]) {
  if (!(this instanceof MockDate)) {
    return new Date(...args);
  }
  if (args.length === 0) {
    return new RealDate();
  }
  return new RealDate(...args);
} as unknown as DateConstructor;

// Copy all properties from RealDate to MockDate
Object.setPrototypeOf(MockDate, RealDate);
MockDate.prototype = RealDate.prototype;

// Override now() method
MockDate.now = () => RealDate.now();

// Replace global Date
global.Date = MockDate;

// Ensure toISOString works properly
const originalToISOString = RealDate.prototype.toISOString;
Date.prototype.toISOString = function() {
  return originalToISOString.call(this);
};

// Mock console.error to avoid cluttering test output
vi.spyOn(console, 'error').mockImplementation(() => {});