import { useAuthContext as useAuth } from '../../auth/AuthContext';
import { Progress } from '../ui/progress';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../ui/tooltip';
import { InfoIcon } from 'lucide-react';

export function MessageCreditCounter() {
  const { isAuthenticated, remainingGuestActions } = useAuth();
  
  // Don't show the counter for authenticated users
  if (isAuthenticated || remainingGuestActions === Infinity) {
    return null;
  }
  
  // Calculate the percentage of credits remaining (assuming max is 10)
  const maxCredits = 10;
  const percentage = Math.max(0, Math.min(100, (remainingGuestActions / maxCredits) * 100));
  
  // Determine the color based on remaining credits
  const getColorClass = () => {
    if (remainingGuestActions <= 2) return 'text-destructive';
    if (remainingGuestActions <= 5) return 'text-warning';
    return 'text-muted-foreground';
  };
  
  // Determine the progress color based on remaining credits
  const getProgressColor = () => {
    if (remainingGuestActions <= 2) return 'bg-destructive';
    if (remainingGuestActions <= 5) return 'bg-warning';
    return 'bg-primary';
  };

  return (
    <div className="flex items-center space-x-2">
      <div className="flex flex-col space-y-1 min-w-[120px]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium">Message Credits</span>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <InfoIcon className="h-3 w-3 text-muted-foreground cursor-help" />
              </TooltipTrigger>
              <TooltipContent>
                <p className="text-xs max-w-[200px]">
                  Guest users are limited to {maxCredits} message credits. 
                  Sign in to get unlimited access.
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
        <div className="flex items-center space-x-2">
          <Progress value={percentage} className="h-2" progressColor={getProgressColor()} />
          <span className={`text-xs font-medium ${getColorClass()}`}>
            {remainingGuestActions}/{maxCredits}
          </span>
        </div>
      </div>
    </div>
  );
}