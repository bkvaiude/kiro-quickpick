import { render, screen } from '@testing-library/react';
import { ChatMessage } from './ChatMessage';
import { vi, describe, test, expect, beforeEach } from 'vitest';
import type { ChatMessage as ChatMessageType } from "../../types/chat";

// Mock the ProductResultsSummary component
vi.mock('./ProductResultsSummary', () => ({
  ProductResultsSummary: ({ products, recommendationsSummary, onClick }: any) => (
    <div 
      data-testid="product-comparison" 
      onClick={onClick}
      className="rounded-lg border bg-[hsl(var(--card))] text-[hsl(var(--card-foreground))] shadow-sm p-4 cursor-pointer hover:bg-[hsl(var(--muted))] transition-colors mt-2"
    >
      <div className="flex items-center justify-between">
        <div>
          <h3 data-testid="products-count" className="font-medium text-sm">
            {products.length} product{products.length !== 1 ? 's' : ''} found
          </h3>
          <p data-testid="recommendations-summary" className="text-xs text-[hsl(var(--muted-foreground))] mt-1 line-clamp-1">
            {recommendationsSummary || 'Based on your requirements, here are the best options available.'}
          </p>
        </div>
        <div className="flex items-center text-[hsl(var(--primary))]">
          <span className="text-sm mr-1">View results</span>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="m9 18 6-6-6-6" />
          </svg>
        </div>
      </div>
    </div>
  )
}));

// Mock the ProductComparisonContainer component
vi.mock('../product/ProductComparisonContainer', () => ({
  ProductComparisonContainer: ({ products, recommendationsSummary }: any) => (
    <div data-testid="product-comparison-container">
      <div data-testid="products-count">{products.length}</div>
      <div data-testid="recommendations-summary">{recommendationsSummary}</div>
    </div>
  )
}));

// Mock the ChatContext
vi.mock('../../context/ChatContext', () => ({
  useChatContext: () => ({
    selectedProductMessageId: null,
    setSelectedProductMessageId: vi.fn(),
  })
}));

describe('ChatMessage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('renders user message correctly', () => {
    const message: ChatMessageType = {
      id: '1',
      text: 'Hello, I need a new phone',
      sender: 'user',
      timestamp: new Date()
    };
    
    render(<ChatMessage message={message} isMobile={false} />);
    
    expect(screen.getByText('Hello, I need a new phone')).toBeInTheDocument();
    expect(screen.queryByTestId('product-comparison')).not.toBeInTheDocument();
  });
  
  test('renders system message without products correctly', () => {
    const message: ChatMessageType = {
      id: '2',
      text: 'How can I help you today?',
      sender: 'system',
      timestamp: new Date()
    };
    
    render(<ChatMessage message={message} isMobile={false} />);
    
    expect(screen.getByText('How can I help you today?')).toBeInTheDocument();
    expect(screen.queryByTestId('product-comparison')).not.toBeInTheDocument();
  });
  
  test('renders system message with products correctly', () => {
    const message: ChatMessageType = {
      id: '3',
      text: 'Here are some phone recommendations:',
      sender: 'system',
      timestamp: new Date(),
      products: [
        {
          title: 'Phone 1',
          price: 10000,
          rating: 4.5,
          features: ['Feature 1', 'Feature 2'],
          pros: ['Pro 1', 'Pro 2'],
          cons: ['Con 1'],
          link: 'https://example.com/phone1'
        },
        {
          title: 'Phone 2',
          price: 15000,
          rating: 4.2,
          features: ['Feature 1', 'Feature 3'],
          pros: ['Pro 1', 'Pro 3'],
          cons: ['Con 2'],
          link: 'https://example.com/phone2'
        }
      ],
      recommendationsSummary: 'Based on your requirements, Phone 1 is the best option.'
    };
    
    render(<ChatMessage message={message} isMobile={false} />);
    
    expect(screen.getByText('Here are some phone recommendations:')).toBeInTheDocument();
    expect(screen.getByTestId('product-comparison')).toBeInTheDocument();
    expect(screen.getByTestId('products-count')).toHaveTextContent('2');
    expect(screen.getByTestId('recommendations-summary')).toHaveTextContent('Based on your requirements, Phone 1 is the best option.');
  });
  
  test('renders system message with products but no summary correctly', () => {
    const message: ChatMessageType = {
      id: '4',
      text: 'Here are some phone recommendations:',
      sender: 'system',
      timestamp: new Date(),
      products: [
        {
          title: 'Phone 1',
          price: 10000,
          rating: 4.5,
          features: ['Feature 1', 'Feature 2'],
          pros: ['Pro 1', 'Pro 2'],
          cons: ['Con 1'],
          link: 'https://example.com/phone1'
        }
      ]
    };
    
    render(<ChatMessage message={message} isMobile={false} />);
    
    expect(screen.getByText('Here are some phone recommendations:')).toBeInTheDocument();
    expect(screen.getByTestId('product-comparison')).toBeInTheDocument();
    expect(screen.getByTestId('products-count')).toHaveTextContent('1');
    expect(screen.getByTestId('recommendations-summary')).toHaveTextContent('Based on your requirements, here are the best options available.');
  });
  
  test('renders mobile view with products correctly', () => {
    const message: ChatMessageType = {
      id: '5',
      text: 'Here are some phone recommendations:',
      sender: 'system',
      timestamp: new Date(),
      products: [
        {
          title: 'Phone 1',
          price: 10000,
          rating: 4.5,
          features: ['Feature 1', 'Feature 2'],
          pros: ['Pro 1', 'Pro 2'],
          cons: ['Con 1'],
          link: 'https://example.com/phone1'
        }
      ],
      recommendationsSummary: 'Based on your requirements, Phone 1 is the best option.'
    };
    
    render(<ChatMessage message={message} isMobile={true} />);
    
    expect(screen.getByText('Here are some phone recommendations:')).toBeInTheDocument();
    // In mobile view with only one product, it shows the product-comparison-container instead
    expect(screen.getByTestId('product-comparison-container')).toBeInTheDocument();
  });
});