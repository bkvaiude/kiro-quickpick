import { render, screen, fireEvent } from '@testing-library/react';
import { ExampleQueries } from './ExampleQueries';
import { vi } from 'vitest';

describe('ExampleQueries', () => {
  const mockSelectQuery = vi.fn();

  beforeEach(() => {
    mockSelectQuery.mockClear();
  });

  test('renders example queries correctly', () => {
    render(<ExampleQueries onSelectQuery={mockSelectQuery} />);
    
    expect(screen.getByText('Try asking:')).toBeInTheDocument();
    expect(screen.getByText("What's the best 5G phone under ₹12,000 with 8GB RAM?")).toBeInTheDocument();
    expect(screen.getByText("Recommend a good laptop for programming under ₹50,000")).toBeInTheDocument();
    expect(screen.getByText("What are the best wireless earbuds under ₹2,000?")).toBeInTheDocument();
    expect(screen.getByText("Compare top washing machines under ₹20,000")).toBeInTheDocument();
  });

  test('calls onSelectQuery when a query button is clicked', () => {
    render(<ExampleQueries onSelectQuery={mockSelectQuery} />);
    
    const queryButton = screen.getByText("What's the best 5G phone under ₹12,000 with 8GB RAM?");
    fireEvent.click(queryButton);
    
    expect(mockSelectQuery).toHaveBeenCalledWith("What's the best 5G phone under ₹12,000 with 8GB RAM?");
  });

  test('calls onSelectQuery with correct query for each button', () => {
    render(<ExampleQueries onSelectQuery={mockSelectQuery} />);
    
    const buttons = screen.getAllByRole('button');
    expect(buttons.length).toBe(4);
    
    // Click each button and verify the correct query is passed
    fireEvent.click(buttons[0]);
    expect(mockSelectQuery).toHaveBeenLastCalledWith("What's the best 5G phone under ₹12,000 with 8GB RAM?");
    
    fireEvent.click(buttons[1]);
    expect(mockSelectQuery).toHaveBeenLastCalledWith("Recommend a good laptop for programming under ₹50,000");
    
    fireEvent.click(buttons[2]);
    expect(mockSelectQuery).toHaveBeenLastCalledWith("What are the best wireless earbuds under ₹2,000?");
    
    fireEvent.click(buttons[3]);
    expect(mockSelectQuery).toHaveBeenLastCalledWith("Compare top washing machines under ₹20,000");
  });
});