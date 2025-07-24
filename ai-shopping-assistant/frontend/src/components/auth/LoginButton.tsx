import { useState } from 'react';
import { useAuthContext } from '../../auth/AuthContext';
import { Button } from '../ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../ui/dialog';
import { Checkbox } from '../ui/checkbox';
import { Label } from '../ui/label';
import { UserProfile } from './UserProfile';

export function LoginButton() {
  const { isAuthenticated, login, logout, user, saveUserConsent } = useAuthContext();
  const [showConsentDialog, setShowConsentDialog] = useState(false);
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [marketingConsent, setMarketingConsent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLoginClick = () => {
    if (isAuthenticated) {
      logout();
    } else {
      // Show consent dialog before proceeding to Auth0 login
      setShowConsentDialog(true);
    }
  };

  const handleContinueToLogin = async () => {
    if (!termsAccepted) {
      setError('You must accept the Terms of Use and Privacy Policy to continue.');
      return;
    }

    setError(null);
    
    // Store the user consent information
    const timestamp = new Date().toISOString();
    saveUserConsent({
      termsAccepted,
      marketingConsent,
      timestamp
    });
    
    // Close the dialog and proceed to Auth0 login
    setShowConsentDialog(false);
    
    // Add consent parameters to the Auth0 login
    await login();
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
        variant="default"
      >
        Login / Register
      </Button>

      <Dialog open={showConsentDialog} onOpenChange={setShowConsentDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Before you continue</DialogTitle>
            <DialogDescription>
              Please review and accept our terms before creating your account.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="flex items-start space-x-2">
              <Checkbox 
                id="terms" 
                checked={termsAccepted} 
                onCheckedChange={(checked) => setTermsAccepted(checked === true)}
                required
              />
              <div className="grid gap-1.5 leading-none">
                <Label 
                  htmlFor="terms" 
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  I accept the <a href="#" className="text-primary underline">Terms of Use</a> and <a href="#" className="text-primary underline">Privacy Policy</a>
                </Label>
                <p className="text-sm text-muted-foreground">
                  This is required to create an account.
                </p>
              </div>
            </div>
            
            <div className="flex items-start space-x-2">
              <Checkbox 
                id="marketing" 
                checked={marketingConsent} 
                onCheckedChange={(checked) => setMarketingConsent(checked === true)}
              />
              <div className="grid gap-1.5 leading-none">
                <Label 
                  htmlFor="marketing" 
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  I agree to receive marketing communications
                </Label>
                <p className="text-sm text-muted-foreground">
                  We'll send you updates about new features and promotions.
                </p>
              </div>
            </div>
            
            {error && (
              <div className="text-red-500 text-sm mt-2">
                {error}
              </div>
            )}
          </div>
          
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowConsentDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleContinueToLogin}>
              Continue to Login
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}