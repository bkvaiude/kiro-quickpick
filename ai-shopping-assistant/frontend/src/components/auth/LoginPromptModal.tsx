import { useState, useEffect } from 'react';
import { useAuthContext as useAuth } from '../../auth/AuthContext';
import { useCredits } from '../../hooks/useCredits';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../ui/dialog';
import { Button } from '../ui/button';
import { CheckCircle, Lock, UserPlus } from 'lucide-react';

export function LoginPromptModal() {
  const { isAuthenticated, login } = useAuth();
  const { creditInfo } = useCredits();
  const [isOpen, setIsOpen] = useState(false);
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  // Show the modal when guest credits are depleted
  useEffect(() => {
    if (!isAuthenticated && creditInfo && creditInfo.isGuest && creditInfo.available <= 0) {
      setIsOpen(true);
    } else {
      setIsOpen(false);
    }
  }, [isAuthenticated, creditInfo]);

  const handleLogin = async () => {
    setIsLoggingIn(true);
    try {
      await login();
    } catch (error) {
      console.error('Login failed:', error);
    } finally {
      setIsLoggingIn(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-xl">
            <Lock className="h-5 w-5 text-primary" />
            Message Limit Reached
          </DialogTitle>
          <DialogDescription>
            You've used all your guest messages.
            Create a free account to get daily credits that reset automatically.
          </DialogDescription>
        </DialogHeader>
        
        <div className="py-6">
          <h3 className="font-medium mb-4">Benefits of creating an account:</h3>
          <ul className="space-y-3">
            <li className="flex items-start gap-2">
              <CheckCircle className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
              <span>Daily message credits that reset automatically</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
              <span>Save your favorite products and comparisons</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
              <span>Personalized product recommendations</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
              <span>Access to exclusive deals and promotions</span>
            </li>
          </ul>
        </div>
        
        <DialogFooter className="flex flex-col sm:flex-row sm:justify-center gap-2">
          <Button 
            onClick={handleLogin} 
            disabled={isLoggingIn}
            className="w-full sm:w-auto"
            size="lg"
          >
            <UserPlus className="mr-2 h-4 w-4" />
            {isLoggingIn ? 'Signing in...' : 'Sign in for free'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}