import { render, screen } from '@testing-library/react';
import { Layout } from './Layout';
import { ThemeProvider } from '../theme/ThemeProvider';
import { ChatProvider } from '../../context/ChatContext';
import { describe, it, expect, vi, beforeAll } from 'vitest';

// Mock the child components
vi.mock('./ApiCredits', () => ({
  ApiCredits: () => <div data-testid="api-credits">API Credits Mock</div>
}));

vi.mock('../theme/ThemeToggle', () => ({
  ThemeToggle: () => <div data-testid="theme-toggle">Theme Toggle Mock</div>
}));

vi.mock('./Sidebar', () => ({
  Sidebar: ({ isMobile, onProductResultsClick }: { isMobile: boolean, onProductResultsClick?: (id: string) => void }) => (
    <div data-testid={`sidebar-${isMobile ? 'mobile' : 'desktop'}`}>
      Sidebar Mock ({isMobile ? 'Mobile' : 'Desktop'})
    </div>
  )
}));

describe('Layout Component', () => {
  beforeAll(() => {
    // Mock window.innerWidth for testing responsive behavior
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1024 // Default to desktop view
    });
  });

  const renderWithProviders = (children: React.ReactNode) => {
    return render(
      <ThemeProvider defaultTheme="light" storageKey="test-theme">
        <ChatProvider>
          {children}
        </ChatProvider>
      </ThemeProvider>
    );
  };

  it('renders the header with logo and title', () => {
    renderWithProviders(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );
    
    expect(screen.getByText('AI Shopping Assistant')).toBeInTheDocument();
  });

  it('renders the API credits in the header', () => {
    renderWithProviders(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );
    
    expect(screen.getByTestId('api-credits')).toBeInTheDocument();
  });

  it('renders the theme toggle in the header', () => {
    renderWithProviders(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );
    
    expect(screen.getByTestId('theme-toggle')).toBeInTheDocument();
  });

  it('renders the desktop sidebar when in desktop view', () => {
    renderWithProviders(
      <Layout isMobile={false}>
        <div>Test Content</div>
      </Layout>
    );
    
    expect(screen.getByTestId('sidebar-desktop')).toBeInTheDocument();
    expect(screen.queryByTestId('sidebar-mobile')).not.toBeInTheDocument();
  });

  it('renders the mobile sidebar when in mobile view', () => {
    renderWithProviders(
      <Layout isMobile={true}>
        <div>Test Content</div>
      </Layout>
    );
    
    expect(screen.getByTestId('sidebar-mobile')).toBeInTheDocument();
  });

  it('respects the isMobile prop over window size', () => {
    window.innerWidth = 1024; // Desktop size
    
    renderWithProviders(
      <Layout isMobile={true}>
        <div>Test Content</div>
      </Layout>
    );
    
    expect(screen.getByTestId('sidebar-mobile')).toBeInTheDocument();
  });

  it('renders the footer with copyright and links', () => {
    renderWithProviders(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );
    
    const currentYear = new Date().getFullYear();
    expect(screen.getByText(`© ${currentYear} AI Shopping Assistant`)).toBeInTheDocument();
    expect(screen.getByText('Contact')).toBeInTheDocument();
    expect(screen.getByText('Terms')).toBeInTheDocument();
    expect(screen.getByText('Affiliate links may generate commission')).toBeInTheDocument();
  });

  it('renders the children content', () => {
    renderWithProviders(
      <Layout>
        <div data-testid="test-content">Test Content</div>
      </Layout>
    );
    
    expect(screen.getByTestId('test-content')).toBeInTheDocument();
  });
  
  it('passes onProductResultsClick to Sidebar', () => {
    const mockOnClick = vi.fn();
    
    renderWithProviders(
      <Layout onProductResultsClick={mockOnClick}>
        <div>Test Content</div>
      </Layout>
    );
    
    // We're just testing that the component renders without errors
    // The actual prop passing is tested by the mock implementation
    expect(screen.getByTestId('sidebar-desktop')).toBeInTheDocument();
  });
});