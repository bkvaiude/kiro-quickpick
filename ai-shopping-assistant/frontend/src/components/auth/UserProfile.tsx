import { useState } from 'react';
import { useAuthContext } from '../../auth/AuthContext';
import { Avatar, AvatarFallback, AvatarImage } from '../ui/avatar';
import { Button } from '../ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';
import { LogOut, User } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function UserProfile() {
  const { user, logout } = useAuthContext();
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const navigate = useNavigate();

  if (!user) {
    return null;
  }

  const handleLogout = async () => {
    setIsLoggingOut(true);
    try {
      logout();
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      setIsLoggingOut(false);
    }
  };

  const handleProfileClick = () => {
    navigate('/profile');
  };

  // Get user initials for avatar fallback
  const getInitials = () => {
    if (user.name) {
      return user.name
        .split(' ')
        .map(n => n[0])
        .join('')
        .toUpperCase()
        .substring(0, 2);
    }
    return user.email ? user.email[0].toUpperCase() : 'U';
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button 
          variant="ghost" 
          className="relative h-10 w-10 rounded-full touch-manipulation"
          aria-label="User menu"
        >
          <Avatar className="h-8 w-8">
            <AvatarImage src={user.picture} alt={user.name || 'User'} />
            <AvatarFallback>{getInitials()}</AvatarFallback>
          </Avatar>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent 
        className="w-56 mr-4" 
        align="end" 
        side="bottom"
        sideOffset={8}
        avoidCollisions={true}
        collisionPadding={16}
        forceMount
      >
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium leading-none">{user.name || 'User'}</p>
            <p className="text-xs leading-none text-muted-foreground">
              {user.email || 'No email provided'}
            </p>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem 
          onClick={handleProfileClick}
          className="cursor-pointer touch-manipulation"
        >
          <User className="mr-2 h-4 w-4" />
          <span>Profile</span>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem 
          onClick={handleLogout} 
          disabled={isLoggingOut}
          className="cursor-pointer touch-manipulation"
        >
          <LogOut className="mr-2 h-4 w-4" />
          <span>{isLoggingOut ? 'Logging out...' : 'Log out'}</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}