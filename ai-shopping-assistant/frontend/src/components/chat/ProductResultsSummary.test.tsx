import { render, screen, fireEvent } from '@testing-library/react';
import { ProductResultsSummary } from './ProductResultsSummary';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { Product } from '../../types/chat';

// Mock the ChatContext
vi.mock('../../context/ChatContext', () => ({
  useChatContext: () => ({
    selectedProductMessageId: null,
    setSelectedProductMessageId: vi.fn(),
  })
}));

describe('ProductResultsSummary Component', () => {
  const mockProducts: Product[] = [
    {
      title: 'Test Product 1',
      price: 999,
      rating: 4.5,
      features: ['Feature 1', 'Feature 2'],
      pros: ['Pro 1', 'Pro 2'],
      cons: ['Con 1'],
      link: 'https://example.com/product1'
    },
    {
      title: 'Test Product 2',
      price: 1299,
      rating: 4.2,
      features: ['Feature 1', 'Feature 2'],
      pros: ['Pro 1'],
      cons: ['Con 1', 'Con 2'],
      link: 'https://example.com/product2'
    }
  ];
  
  const mockRecommendationsSummary = 'Test Product 1 offers the best value for money';
  const mockOnClick = vi.fn();
  
  beforeEach(() => {
    vi.clearAllMocks();
  });
  
  it('renders the correct number of products found', () => {
    render(
      <ProductResultsSummary 
        products={mockProducts} 
        recommendationsSummary={mockRecommendationsSummary}
        onClick={mockOnClick}
      />
    );
    
    expect(screen.getByText('2 products found')).toBeInTheDocument();
  });
  
  it('renders singular form when only one product', () => {
    render(
      <ProductResultsSummary 
        products={[mockProducts[0]]} 
        recommendationsSummary={mockRecommendationsSummary}
        onClick={mockOnClick}
      />
    );
    
    expect(screen.getByText('1 product found')).toBeInTheDocument();
  });
  
  it('displays the recommendation summary', () => {
    render(
      <ProductResultsSummary 
        products={mockProducts} 
        recommendationsSummary={mockRecommendationsSummary}
        onClick={mockOnClick}
      />
    );
    
    expect(screen.getByText(mockRecommendationsSummary)).toBeInTheDocument();
  });
  
  it('calls onClick when clicked', () => {
    render(
      <ProductResultsSummary 
        products={mockProducts} 
        recommendationsSummary={mockRecommendationsSummary}
        onClick={mockOnClick}
      />
    );
    
    fireEvent.click(screen.getByText('View results'));
    expect(mockOnClick).toHaveBeenCalledTimes(1);
  });
  
  it('displays best value product title when no summary is provided', () => {
    render(
      <ProductResultsSummary 
        products={mockProducts} 
        recommendationsSummary=""
        onClick={mockOnClick}
      />
    );
    
    expect(screen.getByText(/Including Test Product 1/)).toBeInTheDocument();
  });
});