import { useState } from "react";
import type { FormEvent, KeyboardEvent } from "react";
import { Input } from "../ui/input";
import { Button } from "../ui/button";
import { Send, Lock } from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "../ui/tooltip";
import type { CreditDisplayInfo } from "../../hooks/useCredits";

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  creditInfo?: CreditDisplayInfo | null;
}

export function ChatInput({ onSendMessage, isLoading, creditInfo }: ChatInputProps) {
  const [message, setMessage] = useState("");
  
  // Check if the user has reached the credit limit
  const isCreditLimitReached = creditInfo && creditInfo.available <= 0;

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      if (isCreditLimitReached) {
        // Still call onSendMessage - let the parent handle the credit check and dialog
        onSendMessage(message);
      } else {
        onSendMessage(message);
        setMessage("");
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex w-full items-center space-x-2">
      <div className="relative flex-1">
        <Input
          type="text"
          placeholder={
            isCreditLimitReached 
              ? (creditInfo?.isGuest ? "Type your message and press Enter to sign in..." : "Daily message limit reached")
              : "Ask about products..."
          }
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          className={`flex-1 pr-10 ${isCreditLimitReached && creditInfo?.isGuest ? 'border-primary' : ''}`}
        />
        {isCreditLimitReached && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Lock className="h-4 w-4 text-muted-foreground" />
                </TooltipTrigger>
                <TooltipContent>
                  <p className="text-xs">
                    {creditInfo?.isGuest 
                      ? "You've used all your guest messages. Sign in to get daily credits."
                      : "You've used all your daily messages. Credits reset in 24 hours."
                    }
                  </p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        )}
      </div>
      <Button 
        type="submit" 
        disabled={!message.trim() || isLoading}
        size="icon"
      >
        <Send className="h-4 w-4" />
      </Button>
    </form>
  );
}