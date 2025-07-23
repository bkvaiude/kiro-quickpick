import { render, screen, fireEvent } from '@testing-library/react';
import { ChatInput } from './ChatInput';
import { vi } from 'vitest';

describe('ChatInput', () => {
  const mockSendMessage = vi.fn();

  beforeEach(() => {
    mockSendMessage.mockClear();
  });

  test('renders input and button', () => {
    render(<ChatInput onSendMessage={mockSendMessage} isLoading={false} />);
    
    expect(screen.getByPlaceholderText('Ask about products...')).toBeInTheDocument();
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  test('button is disabled when input is empty', () => {
    render(<ChatInput onSendMessage={mockSendMessage} isLoading={false} />);
    
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
  });

  test('button is enabled when input has text', () => {
    render(<ChatInput onSendMessage={mockSendMessage} isLoading={false} />);
    
    const input = screen.getByPlaceholderText('Ask about products...');
    fireEvent.change(input, { target: { value: 'test message' } });
    
    const button = screen.getByRole('button');
    expect(button).not.toBeDisabled();
  });

  test('calls onSendMessage when form is submitted', () => {
    render(<ChatInput onSendMessage={mockSendMessage} isLoading={false} />);
    
    const input = screen.getByPlaceholderText('Ask about products...');
    const form = input.closest('form');
    
    fireEvent.change(input, { target: { value: 'test message' } });
    fireEvent.submit(form!);
    
    expect(mockSendMessage).toHaveBeenCalledWith('test message');
    expect(input).toHaveValue('');
  });

  test('calls onSendMessage when Enter key is pressed', () => {
    render(<ChatInput onSendMessage={mockSendMessage} isLoading={false} />);
    
    const input = screen.getByPlaceholderText('Ask about products...');
    
    fireEvent.change(input, { target: { value: 'test message' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    
    expect(mockSendMessage).toHaveBeenCalledWith('test message');
    expect(input).toHaveValue('');
  });

  test('does not call onSendMessage when Shift+Enter is pressed', () => {
    render(<ChatInput onSendMessage={mockSendMessage} isLoading={false} />);
    
    const input = screen.getByPlaceholderText('Ask about products...');
    
    fireEvent.change(input, { target: { value: 'test message' } });
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: true });
    
    expect(mockSendMessage).not.toHaveBeenCalled();
    expect(input).toHaveValue('test message');
  });

  test('input and button are disabled when isLoading is true', () => {
    render(<ChatInput onSendMessage={mockSendMessage} isLoading={true} />);
    
    const input = screen.getByPlaceholderText('Ask about products...');
    const button = screen.getByRole('button');
    
    expect(input).toBeDisabled();
    expect(button).toBeDisabled();
  });
});