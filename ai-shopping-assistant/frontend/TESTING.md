# Testing Guide for Frontend

This document provides guidance on how to run and write tests for the frontend application.

## Running Tests

The project uses Vitest for testing. Here are the available test commands:

```bash
# Run all tests
npm test

# Run tests in watch mode (useful during development)
npm run test:watch

# Run tests with UI
npm run test:ui

# Run a specific test file
npm run test:single -- path/to/test.ts
```

## Test Setup

Tests are configured in `vitest.config.ts` and global test setup is in `src/setupTests.ts`. The setup file includes:

- Jest DOM matchers
- Mocks for browser APIs like `window.matchMedia`
- Mock for `localStorage`
- Fixes for Date object mocking

## Writing Tests

### Component Tests

For testing React components, use React Testing Library:

```tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import YourComponent from './YourComponent';

describe('YourComponent', () => {
  it('renders correctly', () => {
    render(<YourComponent />);
    expect(screen.getByText('Expected Text')).toBeInTheDocument();
  });
});
```

### Mocking

Use Vitest's mocking capabilities:

```tsx
import { vi } from 'vitest';

// Mock a module
vi.mock('../path/to/module', () => ({
  functionName: vi.fn().mockReturnValue('mocked value')
}));

// Mock a function
const mockFn = vi.fn().mockImplementation(() => 'result');
```

## Fixing Common Test Issues

### 1. Jest vs Vitest Syntax

Replace Jest syntax with Vitest:

```ts
// Instead of jest.fn()
vi.fn()

// Instead of jest.mock()
vi.mock()

// Instead of jest.spyOn()
vi.spyOn()
```

### 2. Mocking Browser APIs

The setupTests.ts file includes mocks for:
- window.matchMedia
- localStorage
- Date object

If you need to mock other browser APIs, add them to setupTests.ts.

### 3. Component Testing Issues

For component tests that fail with "Unable to find an element by data-testid":

1. Check if the component actually renders the element with that data-testid
2. Make sure you're providing the necessary context providers:

```tsx
// Wrap components that need context in their tests
render(
  <ThemeProvider>
    <ChatProvider>
      <YourComponent />
    </ChatProvider>
  </ThemeProvider>
);
```

### 4. Date Mocking

For tests that use Date objects:

```tsx
// Mock a specific date
const mockDate = new Date('2023-01-01T12:00:00Z');
vi.setSystemTime(mockDate);

// Reset after test
afterEach(() => {
  vi.useRealTimers();
});
```

### 5. E2E Test Issues

For end-to-end tests, make sure to:

1. Mock all external API calls
2. Provide test data for components
3. Use `userEvent` instead of `fireEvent` for more realistic interactions:

```tsx
import userEvent from '@testing-library/user-event';

test('user interaction', async () => {
  const user = userEvent.setup();
  render(<YourComponent />);
  
  await user.type(screen.getByRole('textbox'), 'Hello');
  await user.click(screen.getByRole('button'));
  
  expect(screen.getByText('Response')).toBeInTheDocument();
});
```

## Best Practices

1. Test component behavior, not implementation details
2. Use data-testid attributes for stable element selection
3. Keep tests focused and simple
4. Use setup and teardown functions for common test logic
5. Mock external dependencies
6. Group related tests with describe blocks
7. Use beforeEach/afterEach for test setup and cleanup
8. Test both success and error paths