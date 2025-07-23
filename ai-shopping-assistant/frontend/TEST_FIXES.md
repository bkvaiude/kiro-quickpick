# Test Fixes Guide

This document provides specific guidance on how to fix the failing tests in the frontend application.

## Common Issues and Solutions

### 1. AuthStateService Tests

The `authStateService.test.ts` file has several failing tests due to mismatches between the implementation and the test expectations. The following changes have been made to fix these issues:

- Added `loadAuthState` function to match test expectations
- Added `needsRefresh` and `refreshIfNeeded` functions
- Updated `saveAuthState` to handle both the new and old storage formats
- Updated `clearAuthState` to remove all auth-related items
- Added compatibility with both `auth_last_check` and `last_auth_check` keys

### 2. UserActionService Tests

The `userActionService.test.ts` file has issues with Date mocking:

- Fixed Date.prototype.toISOString in setupTests.ts
- Ensure proper Date mocking in tests:

```ts
// Use this pattern for Date mocking
const realDate = Date;
const mockDate = new Date('2023-01-01T12:00:00Z');
vi.spyOn(global, 'Date').mockImplementation(() => mockDate as any);

// Reset after test
afterEach(() => {
  global.Date = realDate;
});
```

### 3. Component Tests

For component tests like `ChatMessage.test.tsx`, the main issues are:

- Missing data-testid attributes
- Component structure changes

To fix these:

1. Check the current component implementation:
```tsx
// Look at the actual component structure
<div data-testid="product-results-summary">
  {/* This might have changed from product-comparison */}
</div>
```

2. Update the tests to match the current component structure:
```tsx
// Update test expectations
expect(screen.getByTestId('product-results-summary')).toBeInTheDocument();
```

### 4. E2E Tests

For end-to-end tests in `e2e.test.tsx`, the issues include:

- Multiple elements matching the same selector
- Missing mocks for API calls

To fix these:

1. Use more specific selectors:
```tsx
// Instead of
screen.getByText('What's the best 5G phone under ₹12,000 with 8GB RAM?')

// Use
screen.getByText('What's the best 5G phone under ₹12,000 with 8GB RAM?', { selector: '.example-query' })
```

2. Properly mock API calls:
```tsx
vi.mock('../services/api.ts', () => ({
  ApiService: {
    sendQueryWithRetry: vi.fn().mockResolvedValue({
      // Mock response data
    })
  }
}));
```

### 5. Guest Limit Integration Tests

For `guest-limit-integration.test.tsx`, the issue is with the AuthService mock:

```tsx
// Update the mock to prevent incrementGuestAction from being called for authenticated users
vi.mock('../services/authService', () => ({
  AuthService: {
    isAuthenticated: vi.fn().mockReturnValue(true),
    incrementGuestAction: vi.fn(),
    // other methods...
  }
}));

// In the test setup
beforeEach(() => {
  vi.clearAllMocks();
  // Set up the authenticated state
  (AuthService.isAuthenticated as any).mockReturnValue(true);
});
```

## Step-by-Step Approach to Fixing Tests

1. Start with the simplest tests first (utility functions, services)
2. Fix one test file at a time
3. Run tests with the `--bail 1` option to stop on the first failure:
   ```
   npm test -- --bail 1 src/services/authStateService.test.ts
   ```
4. For component tests, render the component in isolation first to verify it works
5. Add necessary providers and mocks gradually
6. For E2E tests, mock all external dependencies and focus on user interactions

## Using the Vitest UI

The Vitest UI provides a helpful interface for debugging tests:

```
npm run test:ui
```

This will open a browser interface where you can:
- See test results in real-time
- Filter tests by status or name
- View the component tree
- Inspect test errors with detailed stack traces