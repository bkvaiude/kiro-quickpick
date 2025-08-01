import { useState, useEffect, useRef } from "react";
import { ChatInput } from "./ChatInput";
import { ExampleQueries } from "./ExampleQueries";
import { ChatHistory } from "./ChatHistory";
import { LoadingIndicator } from "./LoadingIndicator";
import { ErrorMessage } from "../ui/error-message";
import { useChatContext } from "../../context/ChatContext";

import { useCredits } from "../../hooks/useCredits";
import { LoginButton, type LoginButtonRef } from "../auth/LoginButton";
import { AlertCircle } from "lucide-react";

interface ChatInterfaceProps {
  isMobile?: boolean;
  onProductResultsClick?: (messageId: string) => void;
}

export function ChatInterface({ isMobile = false, onProductResultsClick }: ChatInterfaceProps) {
  const { state, sendMessage } = useChatContext();
  const { messages, isLoading, error } = state;
  const [lastQuery, setLastQuery] = useState<string>("");

  const { creditInfo, hasCredits, refreshCredits } = useCredits();
  const [showCreditWarning, setShowCreditWarning] = useState(false);
  const loginButtonRef = useRef<LoginButtonRef>(null);
  
  // Check if the user is approaching the credit limit (3 or fewer credits left)
  const isApproachingLimit = creditInfo && creditInfo.available <= 3 && creditInfo.available > 0;
  
  // Check if the user has reached the credit limit
  const isCreditLimitReached = creditInfo && creditInfo.available <= 0;
  
  // Show warning when approaching limit
  useEffect(() => {
    console.log("isApproachingLimit", isApproachingLimit);
    if (isApproachingLimit && !showCreditWarning) {
      setShowCreditWarning(true);
    } else if (!isApproachingLimit) {
      setShowCreditWarning(false);
    }
  }, [isApproachingLimit, creditInfo?.available]);

  const handleSendMessage = async (text: string) => {
    if (!text.trim()) return;
    setLastQuery(text);
    
    // Check if user has credits available
    const canSend = await hasCredits();
    if (canSend) {
      await sendMessage(text);
      // Refresh credits after sending to get updated count
      refreshCredits();
    } else {
      // If user has no credits, show login dialog with appropriate reason
      if (loginButtonRef.current) {
        loginButtonRef.current.showDialog('credits_expired');
      }
    }
  };

  const handleRetry = async () => {
    if (lastQuery) {
      // Check if user has credits available for retry
      const canRetry = await hasCredits();
      if (canRetry) {
        await sendMessage(lastQuery);
        // Refresh credits after retry to get updated count
        refreshCredits();
      }
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Credit limit warning banner */}
      {showCreditWarning && !isCreditLimitReached && creditInfo && (
        <div className="bg-amber-50 border-amber-200 border-b p-2 px-4 flex items-center justify-between">
          <div className="flex items-center text-amber-800 text-sm">
            <AlertCircle className="h-4 w-4 mr-2" />
            <span>
              You have {creditInfo.available} message{creditInfo.available !== 1 ? 's' : ''} left. 
              {creditInfo.isGuest ? ' Sign in for daily credits that reset automatically.' : ' Credits reset daily.'}
            </span>
          </div>
          {creditInfo.isGuest && <LoginButton ref={loginButtonRef} variant="outline" size="sm" className="ml-2" />}
        </div>
      )}
      
      {/* Credit limit reached banner */}
      {isCreditLimitReached && creditInfo && (
        <div className="bg-red-50 border-red-200 border-b p-2 px-4 flex items-center justify-between">
          <div className="flex items-center text-red-800 text-sm">
            <AlertCircle className="h-4 w-4 mr-2" />
            <span>
              {creditInfo.isGuest 
                ? "You've used all your guest messages. Sign in to get daily credits that reset automatically."
                : "You've used all your daily messages. Credits will reset in 24 hours."
              }
            </span>
          </div>
          {creditInfo.isGuest && <LoginButton ref={loginButtonRef} variant="default" size="sm" className="ml-2" />}
        </div>
      )}
      
      <div className="flex-1 overflow-auto relative">
        <div className="absolute inset-0 flex flex-col">
          <ChatHistory 
            messages={messages} 
            isMobile={isMobile} 
            onProductResultsClick={onProductResultsClick}
            onRefreshCachedResult={handleSendMessage}
          />
          {isLoading && <LoadingIndicator />}
          {error && !isLoading && <ErrorMessage message={error} onRetry={handleRetry} />}
        </div>
      </div>
      
      <div className="border-t p-4 flex-shrink-0">
        <ChatInput 
          onSendMessage={handleSendMessage} 
          isLoading={isLoading}
          creditInfo={creditInfo}
        />
        
        {messages.length === 0 && !error && (
          <div className="mt-4">
            <ExampleQueries onSelectQuery={handleSendMessage} />
          </div>
        )}
      </div>
      
      {/* Hidden LoginButton for triggering dialog when needed */}
      {!showCreditWarning && !isCreditLimitReached && (
        <LoginButton ref={loginButtonRef} className="hidden" />
      )}
    </div>
  );
}