import { useState, useEffect, useRef, forwardRef, useImperativeHandle } from 'react';
import { useAuthContext } from '../../auth/AuthContext';
import { useCredits } from '../../hooks/useCredits';
import { Button } from '../ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../ui/dialog';
import { CheckCircle, Lock, UserPlus, Clock } from 'lucide-react';
import { UserProfile } from './UserProfile';

export interface LoginButtonRef {
  showDialog: (reason?: 'credits_expired' | 'general') => void;
}

interface LoginButtonProps {
  variant?: "default" | "outline";
  size?: "default" | "sm" | "lg";
  className?: string;
}

export const LoginButton = forwardRef<LoginButtonRef, LoginButtonProps>(({ variant = "default", size = "default", className }, ref) => {
  const { isAuthenticated, login, logout, user, saveUserConsent } = useAuthContext();
  const { creditInfo } = useCredits();
  const [showDialog, setShowDialog] = useState(false);
  const [dialogReason, setDialogReason] = useState<'credits_expired' | 'general'>('general');
  const [error, setError] = useState<string | null>(null);
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const hasShownDialog = useRef(false);
  const lastCreditCheck = useRef<number | null>(null);

  // Reset the dialog flag when user becomes authenticated
  useEffect(() => {
    if (isAuthenticated) {
      hasShownDialog.current = false;
      lastCreditCheck.current = null;
    }
  }, [isAuthenticated]);

  // Expose showDialog method to parent components
  useImperativeHandle(ref, () => ({
    showDialog: (reason: 'credits_expired' | 'general' = 'general') => {
      setDialogReason(reason);
      setShowDialog(true);
      hasShownDialog.current = false;
    }
  }));

  const handleLoginClick = () => {
    if (isAuthenticated) {
      logout();
    } else {
      // Show dialog for general login
      setDialogReason('general');
      setShowDialog(true);
      hasShownDialog.current = false;
    }
  };

  const handleLogin = async () => {
    setIsLoggingIn(true);
    setError(null);

    try {
      // Automatically agree to terms and marketing consent
      const timestamp = new Date().toISOString();
      saveUserConsent({
        termsAccepted: true,
        marketingConsent: true,
        timestamp
      });

      // Close the dialog and proceed to Auth0 login
      setShowDialog(false);
      await login();
    } catch (error) {
      console.error('Login failed:', error);
      setError('Login failed. Please try again.');
    } finally {
      setIsLoggingIn(false);
    }
  };

  const handleDialogClose = (open: boolean) => {
    setShowDialog(open);
    if (!open) {
      setError(null);
    }
  };

  // If user is authenticated, show the user profile component
  if (isAuthenticated && user) {
    return <UserProfile />;
  }

  // Otherwise show the login button
  return (
    <>
      <Button
        onClick={handleLoginClick}
        variant={variant}
        size={size}
        className={className}
      >
        Login / Register
      </Button>

      <Dialog open={showDialog} onOpenChange={handleDialogClose}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-xl">
              {dialogReason === 'credits_expired' ? (
                <>
                  <Lock className="h-5 w-5 text-primary" />
                  Message Limit Reached
                </>
              ) : (
                <>
                  <UserPlus className="h-5 w-5 text-primary" />
                  Sign In / Create Account
                </>
              )}
            </DialogTitle>
            <DialogDescription>
              {dialogReason === 'credits_expired' ? (
                creditInfo?.isGuest ? (
                  "You've used all your guest messages. Create a free account to get daily credits that reset automatically."
                ) : (
                  "You've used all your daily messages. Credits will reset in 24 hours, or create an account for more benefits."
                )
              ) : (
                "Create a free account to unlock daily message credits and upcoming premium features."
              )}
            </DialogDescription>
          </DialogHeader>

          <div className="py-6">
            {dialogReason === 'credits_expired' && !creditInfo?.isGuest ? (
              // Show different content for authenticated users who hit the limit
              <div className="text-center">
                <Clock className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground mb-4">
                  Your daily message credits have been used up. They will automatically reset in 24 hours.
                </p>
                <p className="text-sm text-muted-foreground">
                  Want more messages? Premium features are coming soon!
                </p>
              </div>
            ) : (
              // Show benefits for guest users or general signup
              <>
                <h3 className="font-medium mb-4">
                  {dialogReason === 'credits_expired' ? 'Get unlimited daily messages:' : 'Benefits of creating an account:'}
                </h3>
                <ul className="space-y-3">
                  <li className="flex items-start gap-2">
                    <CheckCircle className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                    <span>Daily message credits that reset automatically</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                    <span className="text-muted-foreground">
                      Save your favorite products and comparisons <span className="text-xs bg-muted px-1.5 py-0.5 rounded">Coming Soon</span>
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                    <span className="text-muted-foreground">
                      Personalized product recommendations <span className="text-xs bg-muted px-1.5 py-0.5 rounded">Coming Soon</span>
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                    <span className="text-muted-foreground">
                      Access to exclusive deals and promotions <span className="text-xs bg-muted px-1.5 py-0.5 rounded">Coming Soon</span>
                    </span>
                  </li>
                </ul>
              </>
            )}
          </div>

          {error && (
            <div className="text-red-500 text-sm mb-4">
              {error}
            </div>
          )}

          <div className="text-xs text-muted-foreground text-center mb-4">
            By signing up, you agree to our{' '}
            <a href="/terms" className="text-primary hover:underline" target="_blank" rel="noopener noreferrer">
              Terms of Service
            </a>{' '}
            and{' '}
            <a href="/privacy" className="text-primary hover:underline" target="_blank" rel="noopener noreferrer">
              Privacy Policy
            </a>
          </div>

          <DialogFooter className="flex flex-col sm:flex-row sm:justify-center gap-2">
            {(dialogReason !== 'credits_expired' || creditInfo?.isGuest) && (
              <Button
                onClick={handleLogin}
                disabled={isLoggingIn}
                className="w-full sm:w-auto"
                size="lg"
              >
                <UserPlus className="mr-2 h-4 w-4" />
                {isLoggingIn ? 'Signing in...' : 'Sign in for free'}
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
});

LoginButton.displayName = 'LoginButton';