import { render, screen } from '@testing-library/react';
import { RecommendationsSummary } from './RecommendationsSummary';

describe('RecommendationsSummary', () => {
  test('renders plain text summary correctly', () => {
    const summary = 'This is a simple recommendation summary.';
    render(<RecommendationsSummary summary={summary} />);
    
    expect(screen.getByText('AI Recommendations')).toBeInTheDocument();
    expect(screen.getByText(summary)).toBeInTheDocument();
  });

  test('renders bullet points correctly', () => {
    const summary = '• First point\n• Second point\n• Third point';
    render(<RecommendationsSummary summary={summary} />);
    
    expect(screen.getByText('AI Recommendations')).toBeInTheDocument();
    expect(screen.getByText('First point')).toBeInTheDocument();
    expect(screen.getByText('Second point')).toBeInTheDocument();
    expect(screen.getByText('Third point')).toBeInTheDocument();
  });
});