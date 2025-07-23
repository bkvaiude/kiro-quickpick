import { render } from '@testing-library/react';

describe('Scrollbar Styles', () => {
  it('applies custom scrollbar class correctly', () => {
    // Create a test component with the custom-scrollbar class
    const { container } = render(
      <div className="custom-scrollbar" style={{ height: '100px', overflow: 'auto' }}>
        <div style={{ height: '500px' }}>Content that forces scrollbar to appear</div>
      </div>
    );
    
    // Check if the custom-scrollbar class is applied
    const scrollableElement = container.firstChild as HTMLElement;
    expect(scrollableElement).toHaveClass('custom-scrollbar');
  });
});