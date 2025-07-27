import { useEffect, useRef } from "react";
import type { ChatMessage as ChatMessageType } from "../../types/chat";
import { ChatMessage } from "./ChatMessage";

interface ChatHistoryProps {
  messages: ChatMessageType[];
  isMobile: boolean;
  onProductResultsClick?: (messageId: string) => void;
  onRefreshCachedResult?: (query: string) => void;
}

export function ChatHistory({ messages, isMobile, onProductResultsClick, onRefreshCachedResult }: ChatHistoryProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex flex-col space-y-4 overflow-y-auto p-4 custom-scrollbar h-full flex-grow">
      {messages.length === 0 ? (
        <div className="flex h-full items-center justify-center">
          <p className="text-center text-[hsl(var(--muted-foreground))]">
            No messages yet. Start a conversation!
          </p>
        </div>
      ) : (
        messages.map((message) => (
          <ChatMessage 
            key={message.id} 
            message={message} 
            isMobile={isMobile}
            onProductResultsClick={onProductResultsClick}
            onRefreshCachedResult={onRefreshCachedResult}
            cached={message.sender === 'system' && message.text.includes('(cached)')}
          />
        ))
      )}
      <div ref={messagesEndRef} />
    </div>
  );
}