import { useState, useEffect } from 'react';
import { useAuthContext } from '../../auth/AuthContext';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../ui/dialog';
import { Button } from '../ui/button';
import { PartyPopper } from 'lucide-react';

export function WelcomeMessage() {
  const { isAuthenticated, user } = useAuthContext();
  const [isOpen, setIsOpen] = useState(false);
  const [isNewLogin, setIsNewLogin] = useState(false);

  // Check if this is a new login by using session storage
  useEffect(() => {
    if (isAuthenticated && user) {
      const hasShownWelcome = sessionStorage.getItem('hasShownWelcome');
      if (!hasShownWelcome) {
        setIsNewLogin(true);
        setIsOpen(true);
        sessionStorage.setItem('hasShownWelcome', 'true');
      }
    }
  }, [isAuthenticated, user]);

  // Get personalized greeting based on time of day
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  // Get user's first name if available
  const getFirstName = () => {
    if (user?.name) {
      return user.name.split(' ')[0];
    }
    return '';
  };

  if (!isAuthenticated || !isNewLogin) {
    return null;
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-xl">
            <PartyPopper className="h-5 w-5 text-primary" />
            Welcome to AI Shopping Assistant!
          </DialogTitle>
          <DialogDescription>
            {getGreeting()}{getFirstName() ? `, ${getFirstName()}` : ''}! We're excited to have you join us.
          </DialogDescription>
        </DialogHeader>
        
        <div className="py-4">
          <p className="mb-4">
            Now that you're signed in, you have access to:
          </p>
          <ul className="space-y-2 list-disc pl-5">
            <li>Unlimited chat messages and product searches</li>
            <li>Personalized product recommendations</li>
            <li>Ability to save your favorite products</li>
            <li>Access to exclusive deals and promotions</li>
          </ul>
        </div>
        
        <DialogFooter>
          <Button onClick={() => setIsOpen(false)} className="w-full sm:w-auto">
            Get Started
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}