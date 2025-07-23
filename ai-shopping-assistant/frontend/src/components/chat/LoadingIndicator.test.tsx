import { render, screen } from '@testing-library/react';
import { LoadingIndicator } from './LoadingIndicator';
import { vi } from 'vitest';

// Mock the Spinner component
vi.mock('../ui/spinner', () => ({
  Spinner: ({ size }: { size: string }) => <div data-testid="spinner" data-size={size}></div>
}));

describe('LoadingIndicator', () => {
  test('renders spinner and text correctly', () => {
    render(<LoadingIndicator />);
    
    expect(screen.getByTestId('spinner')).toBeInTheDocument();
    expect(screen.getByTestId('spinner')).toHaveAttribute('data-size', 'sm');
    expect(screen.getByText('Thinking...')).toBeInTheDocument();
  });
});