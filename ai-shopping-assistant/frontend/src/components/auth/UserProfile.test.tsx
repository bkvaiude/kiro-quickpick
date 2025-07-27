import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';
import { UserProfile } from './UserProfile';
import { useAuthContext } from '../../auth/AuthContext';

// Mock the navigate function
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const mockUser = {
  id: 'test-user-id',
  name: 'Test User',
  email: 'test@example.com',
  picture: 'https://example.com/avatar.jpg',
};

const mockAuthContext = {
  user: mockUser,
  isAuthenticated: true,
  login: vi.fn(),
  logout: vi.fn(),
  isLoading: false,
  remainingGuestActions: 10,
  getToken: vi.fn(),
  saveUserConsent: vi.fn(),
  getUserConsent: vi.fn(),
  getRemainingGuestActions: vi.fn(),
  incrementGuestAction: vi.fn(),
  isGuestLimitReached: vi.fn(),
  resetGuestActions: vi.fn(),
};

// Mock the useAuthContext hook
vi.mock('../../auth/AuthContext', () => ({
  useAuthContext: () => mockAuthContext,
}));

const renderUserProfile = () => {
  return render(
    <BrowserRouter>
      <UserProfile />
    </BrowserRouter>
  );
};

describe('UserProfile Mobile Dropdown', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render user avatar button with proper touch target size', () => {
    renderUserProfile();
    
    const avatarButton = screen.getByRole('button', { name: /user menu/i });
    expect(avatarButton).toBeInTheDocument();
    expect(avatarButton).toHaveClass('h-10', 'w-10', 'touch-manipulation');
  });

  it('should open dropdown menu on click/touch', async () => {
    renderUserProfile();
    
    const avatarButton = screen.getByRole('button', { name: /user menu/i });
    fireEvent.click(avatarButton);
    
    await waitFor(() => {
      expect(screen.getByText('Profile')).toBeInTheDocument();
      expect(screen.getByText('Log out')).toBeInTheDocument();
    });
  });

  it('should navigate to profile page when profile menu item is clicked', async () => {
    renderUserProfile();
    
    const avatarButton = screen.getByRole('button', { name: /user menu/i });
    fireEvent.click(avatarButton);
    
    await waitFor(() => {
      const profileMenuItem = screen.getByText('Profile');
      expect(profileMenuItem).toBeInTheDocument();
    });
    
    const profileMenuItem = screen.getByText('Profile');
    fireEvent.click(profileMenuItem);
    
    expect(mockNavigate).toHaveBeenCalledWith('/profile');
  });

  it('should call logout when logout menu item is clicked', async () => {
    renderUserProfile();
    
    const avatarButton = screen.getByRole('button', { name: /user menu/i });
    fireEvent.click(avatarButton);
    
    await waitFor(() => {
      const logoutMenuItem = screen.getByText('Log out');
      expect(logoutMenuItem).toBeInTheDocument();
    });
    
    const logoutMenuItem = screen.getByText('Log out');
    fireEvent.click(logoutMenuItem);
    
    expect(mockAuthContext.logout).toHaveBeenCalled();
  });

  it('should have proper touch-friendly menu items', async () => {
    renderUserProfile();
    
    const avatarButton = screen.getByRole('button', { name: /user menu/i });
    fireEvent.click(avatarButton);
    
    await waitFor(() => {
      const profileMenuItem = screen.getByText('Profile').closest('[role="menuitem"]');
      const logoutMenuItem = screen.getByText('Log out').closest('[role="menuitem"]');
      
      expect(profileMenuItem).toHaveClass('touch-manipulation');
      expect(logoutMenuItem).toHaveClass('touch-manipulation');
    });
  });

  it('should display user information correctly', async () => {
    renderUserProfile();
    
    const avatarButton = screen.getByRole('button', { name: /user menu/i });
    fireEvent.click(avatarButton);
    
    await waitFor(() => {
      expect(screen.getByText('Test User')).toBeInTheDocument();
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
    });
  });

  it('should handle user without name gracefully', async () => {
    const userWithoutName = { ...mockUser, name: undefined };
    
    // Temporarily override the mock for this test
    vi.mocked(useAuthContext).mockReturnValueOnce({
      ...mockAuthContext,
      user: userWithoutName,
    });
    
    render(
      <BrowserRouter>
        <UserProfile />
      </BrowserRouter>
    );
    
    const avatarButton = screen.getByRole('button', { name: /user menu/i });
    fireEvent.click(avatarButton);
    
    await waitFor(() => {
      expect(screen.getByText('User')).toBeInTheDocument();
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
    });
  });

  it('should show loading state during logout', async () => {
    renderUserProfile();
    
    const avatarButton = screen.getByRole('button', { name: /user menu/i });
    fireEvent.click(avatarButton);
    
    await waitFor(() => {
      const logoutMenuItem = screen.getByText('Log out');
      expect(logoutMenuItem).toBeInTheDocument();
    });
    
    // Mock a slow logout process
    mockAuthContext.logout.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
    
    const logoutMenuItem = screen.getByText('Log out');
    fireEvent.click(logoutMenuItem);
    
    // Should show loading state
    await waitFor(() => {
      expect(screen.getByText('Logging out...')).toBeInTheDocument();
    });
  });
});