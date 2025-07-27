import { useCredits } from '../../hooks/useCredits';
import { useAuthContext as useAuth } from '../../auth/AuthContext';
import { Progress } from '../ui/progress';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../ui/tooltip';
import { InfoIcon, RefreshCw } from 'lucide-react';
import { Button } from '../ui/button';

export function MessageCreditDisplay() {
  const { isAuthenticated } = useAuth();
  const { creditInfo, isLoading, refreshCredits } = useCredits();
  
  // Don't show for authenticated users with unlimited credits
  if (isAuthenticated && creditInfo && !creditInfo.isGuest && creditInfo.available === Infinity) {
    return null;
  }
  
  // Don't show while loading or if no credit info
  if (isLoading || !creditInfo) {
    return null;
  }

  const formatNextResetTime = (nextResetTime?: string) => {
    if (!nextResetTime) return null;
    
    const resetDate = new Date(nextResetTime);
    const now = new Date();
    const diffMs = resetDate.getTime() - now.getTime();
    const diffHours = Math.ceil(diffMs / (1000 * 60 * 60));
    
    if (diffHours <= 0) return 'Soon';
    if (diffHours === 1) return '1 hour';
    if (diffHours < 24) return `${diffHours} hours`;
    
    const diffDays = Math.ceil(diffHours / 24);
    return diffDays === 1 ? '1 day' : `${diffDays} days`;
  };

  const getTooltipContent = () => {
    if (creditInfo.isGuest) {
      return `Guest users are limited to ${creditInfo.max} messages. Sign in to get daily credits that reset automatically.`;
    } else {
      const resetInfo = formatNextResetTime(creditInfo.nextResetTime);
      return `Registered users get ${creditInfo.max} messages daily. ${resetInfo ? `Credits reset in ${resetInfo}.` : 'Credits reset daily.'}`;
    }
  };

  return (
    <div className="flex items-center space-x-2">
      <div className="flex flex-col space-y-1 min-w-[140px]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium">Message Credits</span>
          <div className="flex items-center space-x-1">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <InfoIcon className="h-3 w-3 text-muted-foreground cursor-help" />
                </TooltipTrigger>
                <TooltipContent>
                  <p className="text-xs max-w-[200px]">
                    {getTooltipContent()}
                  </p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            {!creditInfo.isGuest && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-4 w-4 p-0"
                      onClick={refreshCredits}
                    >
                      <RefreshCw className="h-3 w-3" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p className="text-xs">Refresh credit status</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Progress 
            value={creditInfo.percentage} 
            className="h-2" 
            progressColor={creditInfo.progressColor} 
          />
          <span className={`text-xs font-medium ${creditInfo.colorClass}`}>
            {creditInfo.available === Infinity ? '∞' : creditInfo.available}/{creditInfo.max === Infinity ? '∞' : creditInfo.max}
          </span>
        </div>
        {!creditInfo.isGuest && creditInfo.nextResetTime && (
          <div className="text-xs text-muted-foreground">
            Resets in {formatNextResetTime(creditInfo.nextResetTime)}
          </div>
        )}
      </div>
    </div>
  );
}