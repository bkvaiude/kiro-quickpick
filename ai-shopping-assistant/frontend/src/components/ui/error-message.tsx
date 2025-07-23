import { AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "./button";

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorMessage({ message, onRetry }: ErrorMessageProps) {
  return (
    <div className="flex w-full items-center justify-start p-4">
      <div className="flex flex-col space-y-2 rounded-lg bg-destructive/10 px-4 py-3 text-destructive w-full">
        <div className="flex items-center space-x-2">
          <AlertCircle className="h-5 w-5" />
          <p className="font-medium">Error</p>
        </div>
        <p className="text-sm">{message}</p>
        {onRetry && (
          <div className="flex justify-end">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={onRetry}
              className="flex items-center space-x-1"
            >
              <RefreshCw className="h-3 w-3 mr-1" />
              <span>Retry</span>
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}