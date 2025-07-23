import { render, screen } from '@testing-library/react';
import { ChatInterface } from './ChatInterface';
import { vi } from 'vitest';
import type { ChatMessage } from '../../types/chat';

// Mock the context
vi.mock('../../context/ChatContext', () => ({
  useChatContext: () => ({
    state: {
      messages: mockMessages,
      isLoading: mockIsLoading,
    },
    sendMessage: mockSendMessage,
  }),
}));

// Mock the child components
vi.mock('./ChatInput', () => ({
  ChatInput: ({ onSendMessage, isLoading }: any) => (
    <div data-testid="chat-input" data-loading={isLoading}>
      <button onClick={() => onSendMessage('test message')}>Send</button>
    </div>
  ),
}));

vi.mock('./ExampleQueries', () => ({
  ExampleQueries: ({ onSelectQuery }: any) => (
    <div data-testid="example-queries">
      <button onClick={() => onSelectQuery('example query')}>Example</button>
    </div>
  ),
}));

vi.mock('./ChatHistory', () => ({
  ChatHistory: ({ messages }: any) => (
    <div data-testid="chat-history">
      {messages.map((msg: ChatMessage) => (
        <div key={msg.id} data-message-id={msg.id}>{msg.text}</div>
      ))}
    </div>
  ),
}));

vi.mock('./LoadingIndicator', () => ({
  LoadingIndicator: () => <div data-testid="loading-indicator">Loading...</div>,
}));

// Mock data and functions
let mockMessages: ChatMessage[] = [];
let mockIsLoading = false;
const mockSendMessage = vi.fn();

describe('ChatInterface', () => {
  beforeEach(() => {
    mockMessages = [];
    mockIsLoading = false;
    mockSendMessage.mockClear();
  });

  test('renders chat input', () => {
    render(<ChatInterface />);
    expect(screen.getByTestId('chat-input')).toBeInTheDocument();
  });

  test('renders example queries when no messages', () => {
    mockMessages = [];
    render(<ChatInterface />);
    expect(screen.getByTestId('example-queries')).toBeInTheDocument();
  });

  test('does not render example queries when messages exist', () => {
    mockMessages = [
      {
        id: '1',
        text: 'Hello',
        sender: 'user',
        timestamp: new Date(),
      },
    ];
    render(<ChatInterface />);
    expect(screen.queryByTestId('example-queries')).not.toBeInTheDocument();
  });

  test('renders chat history with messages', () => {
    mockMessages = [
      {
        id: '1',
        text: 'Hello',
        sender: 'user',
        timestamp: new Date(),
      },
      {
        id: '2',
        text: 'Hi there!',
        sender: 'system',
        timestamp: new Date(),
      },
    ];
    render(<ChatInterface />);
    expect(screen.getByTestId('chat-history')).toBeInTheDocument();
    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText('Hi there!')).toBeInTheDocument();
  });

  test('renders loading indicator when loading', () => {
    mockIsLoading = true;
    render(<ChatInterface />);
    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();
  });

  test('does not render loading indicator when not loading', () => {
    mockIsLoading = false;
    render(<ChatInterface />);
    expect(screen.queryByTestId('loading-indicator')).not.toBeInTheDocument();
  });

  test('sends message when chat input triggers onSendMessage', () => {
    render(<ChatInterface />);
    screen.getByText('Send').click();
    expect(mockSendMessage).toHaveBeenCalledWith('test message');
  });

  test('sends message when example query is selected', () => {
    mockMessages = [];
    render(<ChatInterface />);
    screen.getByText('Example').click();
    expect(mockSendMessage).toHaveBeenCalledWith('example query');
  });
});