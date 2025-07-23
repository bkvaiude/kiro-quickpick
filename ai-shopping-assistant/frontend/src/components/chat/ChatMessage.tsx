import { useState, useEffect } from "react";
import type { ChatMessage as ChatMessageType } from "../../types/chat";
import { cn } from "../../lib/utils";
import { ProductComparisonContainer } from "../product/ProductComparisonContainer";
import { ProductResultsSummary } from "./ProductResultsSummary";

interface ChatMessageProps {
  message: ChatMessageType;
  isMobile: boolean;
  onProductResultsClick?: (messageId: string) => void;
}

export function ChatMessage({ message, isMobile, onProductResultsClick }: ChatMessageProps) {
  const isUser = message.sender === "user";
  const hasProducts = !isUser && message.products && message.products.length > 0;
  
  // For mobile view, we might want to collapse long product lists initially
  const [isExpanded, setIsExpanded] = useState(false);
  
  // Reset expanded state when message changes
  useEffect(() => {
    setIsExpanded(false);
  }, [message.id]);
  
  const handleProductResultsClick = () => {
    if (onProductResultsClick) {
      onProductResultsClick(message.id);
    }
  };
  
  return (
    <div className="w-full mb-4">
      <div
        className={cn(
          "flex w-full",
          isUser ? "justify-end" : "justify-start"
        )}
      >
        <div
          className={cn(
            "max-w-[80%] rounded-lg px-4 py-2",
            isUser
              ? "bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]"
              : "bg-[hsl(var(--muted))]"
          )}
        >
          <p className="text-sm">{message.text}</p>
        </div>
      </div>
      
      {hasProducts && (
        <>
          {/* On mobile: show full product comparison or a "Show more" button */}
          {isMobile ? (
            <div className="mt-4">
              {isExpanded || message.products.length <= 2 ? (
                <ProductComparisonContainer 
                  products={message.products} 
                  recommendationsSummary={message.recommendationsSummary || "Based on your requirements, here are the best options available."}
                />
              ) : (
                <div className="space-y-4">
                  <ProductResultsSummary 
                    products={message.products}
                    recommendationsSummary={message.recommendationsSummary || ""}
                    onClick={() => setIsExpanded(true)}
                  />
                </div>
              )}
            </div>
          ) : (
            /* On desktop: show only the summary card that will trigger product display in the right panel */
            <div className="mt-2">
              <ProductResultsSummary 
                products={message.products}
                recommendationsSummary={message.recommendationsSummary || ""}
                onClick={handleProductResultsClick}
              />
            </div>
          )}
        </>
      )}
    </div>
  );
}