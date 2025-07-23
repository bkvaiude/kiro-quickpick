import { useState, useEffect } from "react";
import { ChatInput } from "./ChatInput";
import { ExampleQueries } from "./ExampleQueries";
import { ChatHistory } from "./ChatHistory";
import { LoadingIndicator } from "./LoadingIndicator";
import { ErrorMessage } from "../ui/error-message";
import { useChatContext } from "../../context/ChatContext";
import { useAuth } from "../../context/AuthContext";
import { Button } from "../ui/button";
import { LoginButton } from "../auth/LoginButton";
import { AlertCircle } from "lucide-react";

interface ChatInterfaceProps {
  isMobile?: boolean;
  onProductResultsClick?: (messageId: string) => void;
}

export function ChatInterface({ isMobile = false, onProductResultsClick }: ChatInterfaceProps) {
  const { state, sendMessage } = useChatContext();
  const { messages, isLoading, error } = state;
  const [lastQuery, setLastQuery] = useState<string>("");
  const { decrementGuestActions, isAuthenticated, remainingGuestActions } = useAuth();
  const [showGuestWarning, setShowGuestWarning] = useState(false);
  
  // Check if the user is approaching the guest limit (3 or fewer actions left)
  const isApproachingLimit = !isAuthenticated && remainingGuestActions <= 3 && remainingGuestActions > 0;
  
  // Check if the user has reached the guest limit
  const isGuestLimitReached = !isAuthenticated && remainingGuestActions <= 0;
  
  // Show warning when approaching limit
  useEffect(() => {
    if (isApproachingLimit && !showGuestWarning) {
      setShowGuestWarning(true);
    } else if (!isApproachingLimit) {
      setShowGuestWarning(false);
    }
  }, [isApproachingLimit, remainingGuestActions]);

  const handleSendMessage = async (text: string) => {
    if (!text.trim()) return;
    setLastQuery(text);
    
    // Check if user can send a message
    if (isAuthenticated || remainingGuestActions > 0) {
      // Decrement guest actions when sending a message
      decrementGuestActions();
      
      await sendMessage(text);
    }
  };

  const handleRetry = async () => {
    if (lastQuery) {
      // Check if user can retry
      if (isAuthenticated || remainingGuestActions > 0) {
        // Decrement guest actions when retrying a message
        decrementGuestActions();
        
        await sendMessage(lastQuery);
      }
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Guest limit warning banner */}
      {showGuestWarning && !isGuestLimitReached && (
        <div className="bg-amber-50 border-amber-200 border-b p-2 px-4 flex items-center justify-between">
          <div className="flex items-center text-amber-800 text-sm">
            <AlertCircle className="h-4 w-4 mr-2" />
            <span>You have {remainingGuestActions} actions left as a guest. Sign in for unlimited access.</span>
          </div>
          <LoginButton variant="outline" size="sm" className="ml-2" />
        </div>
      )}
      
      {/* Guest limit reached banner */}
      {isGuestLimitReached && (
        <div className="bg-red-50 border-red-200 border-b p-2 px-4 flex items-center justify-between">
          <div className="flex items-center text-red-800 text-sm">
            <AlertCircle className="h-4 w-4 mr-2" />
            <span>You've reached the guest limit. Sign in to continue using the assistant.</span>
          </div>
          <LoginButton variant="default" size="sm" className="ml-2" />
        </div>
      )}
      
      <div className="flex-1 overflow-auto relative">
        <div className="absolute inset-0 flex flex-col">
          <ChatHistory 
            messages={messages} 
            isMobile={isMobile} 
            onProductResultsClick={onProductResultsClick}
          />
          {isLoading && <LoadingIndicator />}
          {error && !isLoading && <ErrorMessage message={error} onRetry={handleRetry} />}
        </div>
      </div>
      
      <div className="border-t p-4 flex-shrink-0">
        <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
        
        {messages.length === 0 && !error && (
          <div className="mt-4">
            <ExampleQueries onSelectQuery={handleSendMessage} />
          </div>
        )}
      </div>
    </div>
  );
}