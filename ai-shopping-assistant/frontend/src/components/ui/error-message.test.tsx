import { render, screen, fireEvent } from '@testing-library/react';
import { ErrorMessage } from './error-message';
import { vi } from 'vitest';

describe('ErrorMessage', () => {
  test('renders error message correctly', () => {
    render(<ErrorMessage message="Test error message" />);
    
    expect(screen.getByText('Error')).toBeInTheDocument();
    expect(screen.getByText('Test error message')).toBeInTheDocument();
  });

  test('does not show retry button when onRetry is not provided', () => {
    render(<ErrorMessage message="Test error message" />);
    
    expect(screen.queryByText('Retry')).not.toBeInTheDocument();
  });

  test('shows retry button when onRetry is provided', () => {
    render(<ErrorMessage message="Test error message" onRetry={() => {}} />);
    
    expect(screen.getByText('Retry')).toBeInTheDocument();
  });

  test('calls onRetry when retry button is clicked', () => {
    const mockOnRetry = vi.fn();
    render(<ErrorMessage message="Test error message" onRetry={mockOnRetry} />);
    
    const retryButton = screen.getByText('Retry');
    fireEvent.click(retryButton);
    
    expect(mockOnRetry).toHaveBeenCalledTimes(1);
  });
});