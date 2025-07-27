import { render, screen } from '@testing-library/react';
import { ProductComparisonContainer } from './ProductComparisonContainer';
import { vi } from 'vitest';
import type { Product } from "../../types/chat";

// Mock the RecommendationsSummary component
vi.mock('./RecommendationsSummary', () => ({
  RecommendationsSummary: ({ summary }: { summary: string }) => (
    <div data-testid="recommendations-summary">{summary}</div>
  )
}));

// Mock the EmptyProductState component
vi.mock('./EmptyProductState', () => ({
  EmptyProductState: ({ query, recommendationsSummary }: { query?: string, recommendationsSummary?: string }) => (
    <div data-testid="empty-product-state">
      <div data-testid="empty-query">{query || 'No query'}</div>
      <div data-testid="empty-recommendations">{recommendationsSummary || 'No recommendations'}</div>
    </div>
  )
}));

describe('ProductComparisonContainer', () => {
  const mockProducts: Product[] = [
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
  ];

  const mockSummary = 'Based on your requirements, Phone 1 is the best option.';

  test('renders recommendations summary correctly', () => {
    render(<ProductComparisonContainer products={mockProducts} recommendationsSummary={mockSummary} />);
    
    expect(screen.getByTestId('recommendations-summary')).toHaveTextContent(mockSummary);
  });

  test('renders product cards correctly', () => {
    render(<ProductComparisonContainer products={mockProducts} recommendationsSummary={mockSummary} />);
    
    // Check product titles
    expect(screen.getByText('Phone 1')).toBeInTheDocument();
    expect(screen.getByText('Phone 2')).toBeInTheDocument();
    
    // Check prices
    expect(screen.getByText('₹10,000')).toBeInTheDocument();
    expect(screen.getByText('₹15,000')).toBeInTheDocument();
    
    // Check ratings
    expect(screen.getByText('4.5')).toBeInTheDocument();
    expect(screen.getByText('4.2')).toBeInTheDocument();
    
    // Check features
    expect(screen.getAllByText('Feature 1').length).toBe(2);
    expect(screen.getByText('Feature 2')).toBeInTheDocument();
    expect(screen.getByText('Feature 3')).toBeInTheDocument();
    
    // Check pros
    expect(screen.getAllByText('Pro 1').length).toBe(2);
    expect(screen.getByText('Pro 2')).toBeInTheDocument();
    expect(screen.getByText('Pro 3')).toBeInTheDocument();
    
    // Check cons
    expect(screen.getByText('Con 1')).toBeInTheDocument();
    expect(screen.getByText('Con 2')).toBeInTheDocument();
    
    // Check buy now links
    const buyLinks = screen.getAllByText('Buy Now');
    expect(buyLinks.length).toBe(2);
    expect(buyLinks[0]).toHaveAttribute('href', 'https://example.com/phone1');
    expect(buyLinks[1]).toHaveAttribute('href', 'https://example.com/phone2');
  });

  test('renders empty product list correctly', () => {
    render(<ProductComparisonContainer products={[]} recommendationsSummary={mockSummary} />);
    
    expect(screen.getByTestId('empty-product-state')).toBeInTheDocument();
    expect(screen.getByTestId('empty-recommendations')).toHaveTextContent(mockSummary);
    expect(screen.queryByText('Phone 1')).not.toBeInTheDocument();
  });

  test('passes query to EmptyProductState when no products', () => {
    const testQuery = 'best smartphone under 15000';
    render(<ProductComparisonContainer products={[]} recommendationsSummary={mockSummary} query={testQuery} />);
    
    expect(screen.getByTestId('empty-product-state')).toBeInTheDocument();
    expect(screen.getByTestId('empty-query')).toHaveTextContent(testQuery);
  });
});