import { useState } from "react";
import type { FormEvent, KeyboardEvent } from "react";
import { Input } from "../ui/input";
import { Button } from "../ui/button";
import { Send, Lock } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "../ui/tooltip";

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

export function ChatInput({ onSendMessage, isLoading }: ChatInputProps) {
  const [message, setMessage] = useState("");
  const { isAuthenticated, remainingGuestActions } = useAuth();
  
  // Check if the user has reached the guest limit
  const isGuestLimitReached = !isAuthenticated && remainingGuestActions <= 0;

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isLoading && !isGuestLimitReached) {
      onSendMessage(message);
      setMessage("");
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
          placeholder={isGuestLimitReached ? "Login to continue chatting" : "Ask about products..."}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading || isGuestLimitReached}
          className={`flex-1 pr-10 ${isGuestLimitReached ? 'bg-muted text-muted-foreground' : ''}`}
        />
        {isGuestLimitReached && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Lock className="h-4 w-4 text-muted-foreground" />
                </TooltipTrigger>
                <TooltipContent>
                  <p className="text-xs">You've reached the guest limit. Sign in to continue.</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        )}
      </div>
      <Button 
        type="submit" 
        disabled={!message.trim() || isLoading || isGuestLimitReached}
        size="icon"
      >
        <Send className="h-4 w-4" />
      </Button>
    </form>
  );
}