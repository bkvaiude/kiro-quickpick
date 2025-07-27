import { render, screen, fireEvent } from '@testing-library/react';
import { EmptyProductState } from './EmptyProductState';
import { vi } from 'vitest';

// Mock the useChatContext hook
const mockSendMessage = vi.fn();
vi.mock('../../context/ChatContext', () => ({
  useChatContext: () => ({
    sendMessage: mockSendMessage
  })
}));

describe('EmptyProductState', () => {
  beforeEach(() => {
    mockSendMessage.mockClear();
  });

  test('renders default state without query', () => {
    render(<EmptyProductState />);
    
    expect(screen.getByText("Let's find what you're looking for")).toBeInTheDocument();
    expect(screen.getByText("Ask me about any product and I'll provide personalized recommendations with detailed comparisons.")).toBeInTheDocument();
  });

  test('renders with query and shows no exact matches message', () => {
    const query = 'best smartphone under 10000';
    render(<EmptyProductState query={query} />);
    
    expect(screen.getByText('No exact matches found')).toBeInTheDocument();
    expect(screen.getByText(`I couldn't find specific products for "${query}", but I can help you with similar or related items.`)).toBeInTheDocument();
  });

  test('renders recommendations summary when provided', () => {
    const recommendationsSummary = 'Here are some alternative suggestions for your search.';
    render(<EmptyProductState recommendationsSummary={recommendationsSummary} />);
    
    expect(screen.getByText('AI Recommendations')).toBeInTheDocument();
    expect(screen.getByText(recommendationsSummary)).toBeInTheDocument();
  });

  test('generates phone-related suggestions for phone queries', () => {
    const query = 'best phone under 15000';
    render(<EmptyProductState query={query} />);
    
    expect(screen.getByText('Try these related searches:')).toBeInTheDocument();
    expect(screen.getByText('Best smartphones under ₹20,000')).toBeInTheDocument();
    expect(screen.getByText('iPhone vs Android comparison 2024')).toBeInTheDocument();
  });

  test('generates laptop-related suggestions for laptop queries', () => {
    const query = 'gaming laptop recommendations';
    render(<EmptyProductState query={query} />);
    
    expect(screen.getByText('Try these related searches:')).toBeInTheDocument();
    expect(screen.getByText('Best laptops for students under ₹40,000')).toBeInTheDocument();
    expect(screen.getByText('Gaming laptops vs workstation laptops')).toBeInTheDocument();
  });

  test('calls sendMessage when suggestion is clicked', () => {
    const query = 'phone recommendations';
    render(<EmptyProductState query={query} />);
    
    const suggestion = screen.getByText('Best smartphones under ₹20,000');
    fireEvent.click(suggestion);
    
    expect(mockSendMessage).toHaveBeenCalledWith('Best smartphones under ₹20,000');
  });

  test('shows marketing content about AI assistant features', () => {
    render(<EmptyProductState />);
    
    expect(screen.getByText('Why Choose Our AI Shopping Assistant?')).toBeInTheDocument();
    expect(screen.getByText('Precise Matching')).toBeInTheDocument();
    expect(screen.getByText('Instant Results')).toBeInTheDocument();
    expect(screen.getByText('Best Value')).toBeInTheDocument();
  });

  test('generates generic suggestions for unknown queries', () => {
    const query = 'random product search';
    render(<EmptyProductState query={query} />);
    
    expect(screen.getByText('Try these related searches:')).toBeInTheDocument();
    expect(screen.getByText('Popular products in electronics')).toBeInTheDocument();
    expect(screen.getByText('Best deals available today')).toBeInTheDocument();
  });
});