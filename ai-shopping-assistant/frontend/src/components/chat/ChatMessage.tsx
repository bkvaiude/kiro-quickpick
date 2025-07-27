import { useState, useEffect } from "react";
import type { ChatMessage as ChatMessageType } from "../../types/chat";
import { cn } from "../../lib/utils";
import { ProductComparisonContainer } from "../product/ProductComparisonContainer";
import { ProductResultsSummary } from "./ProductResultsSummary";
import { Button } from "../ui/button";
import { RefreshCw, Clock } from "lucide-react";
import { Badge } from "../ui/badge";

interface ChatMessageProps {
  message: ChatMessageType;
  isMobile: boolean;
  onProductResultsClick?: (messageId: string) => void;
  onRefreshCachedResult?: (query: string) => void;
  cached?: boolean;
}

export function ChatMessage({ message, isMobile, onProductResultsClick, onRefreshCachedResult, cached }: ChatMessageProps) {
  const isUser = message.sender === "user";
  const hasProducts = !isUser && message.products && message.products.length > 0;
  const hasRecommendations = !isUser && message.recommendations_summary && message.recommendations_summary.trim();
  
  // For mobile view, we might want to collapse long product lists initially
  const [isExpanded, setIsExpanded] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  // Reset expanded state when message changes
  useEffect(() => {
    setIsExpanded(false);
  }, [message.id]);
  
  const handleProductResultsClick = () => {
    if (onProductResultsClick) {
      onProductResultsClick(message.id);
    }
  };

  const handleRefresh = async () => {
    if (onRefreshCachedResult && !isRefreshing) {
      setIsRefreshing(true);
      try {
        // Extract the original query from the message text
        const queryMatch = message.text.match(/Based on your query: "(.+?)", I've found these options:/);
        const query = queryMatch ? queryMatch[1] : '';
        if (query) {
          await onRefreshCachedResult(query);
        }
      } finally {
        setIsRefreshing(false);
      }
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
          <div className="flex items-start justify-between gap-2">
            <p className="text-sm flex-1">{message.text}</p>
            {cached && !isUser && (
              <div className="flex items-center gap-2 flex-shrink-0">
                <Badge variant="secondary" className="text-xs flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  Cached
                </Badge>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleRefresh}
                  disabled={isRefreshing}
                  className="h-6 w-6 p-0 hover:bg-background/20"
                  title="Refresh result"
                >
                  <RefreshCw className={cn("h-3 w-3", isRefreshing && "animate-spin")} />
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
      
      {(hasProducts || hasRecommendations) && (
        <>
          {/* On mobile: show full product comparison or a "Show more" button */}
          {isMobile ? (
            <div className="mt-4">
              {isExpanded || (message.products && message.products.length <= 2) ? (
                <ProductComparisonContainer 
                  products={message.products || []} 
                  recommendationsSummary={message.recommendations_summary || "Based on your requirements, here are the best options available."}
                  query={message.text.includes('Based on your query:') ? 
                    message.text.match(/Based on your query: "(.+?)", I've found these options:/)?.[1] : 
                    undefined
                  }
                />
              ) : (
                <div className="space-y-4">
                  <ProductResultsSummary 
                    products={message.products || []}
                    recommendationsSummary={message.recommendations_summary || ""}
                    onClick={() => setIsExpanded(true)}
                  />
                </div>
              )}
            </div>
          ) : (
            /* On desktop: show only the summary card that will trigger product display in the right panel */
            <div className="mt-2">
              <ProductResultsSummary 
                products={message.products || []}
                recommendationsSummary={message.recommendations_summary || ""}
                onClick={handleProductResultsClick}
              />
            </div>
          )}
        </>
      )}
    </div>
  );
}