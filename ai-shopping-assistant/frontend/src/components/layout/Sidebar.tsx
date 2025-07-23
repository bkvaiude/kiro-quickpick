import { useState } from "react";
import { SessionStats } from "./SessionStats";
import { useChatContext } from "../../context/ChatContext";
import { ChatInterface } from "../chat/ChatInterface";

interface SidebarProps {
  isMobile: boolean;
  onProductResultsClick?: (messageId: string) => void;
}

export function Sidebar({ isMobile, onProductResultsClick }: SidebarProps) {
  const { state, sendMessage } = useChatContext();
  const { messages } = state;
  const [isOpen, setIsOpen] = useState(false);

  // Get only user messages for the chat history
  const userMessages = messages.filter(msg => msg.sender === 'user');

  const handleMessageClick = (text: string) => {
    sendMessage(text);
    if (isMobile) {
      setIsOpen(false);
    }
  };

  const toggleSidebar = () => {
    setIsOpen(!isOpen);
  };

  // Render the floating button for mobile view
  const renderFloatingButton = () => {
    if (!isMobile) return null;
    
    return (
      <button
        onClick={toggleSidebar}
        className="fixed bottom-20 left-4 z-50 bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] p-3 rounded-full shadow-lg"
        aria-label="View History"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.5}
          stroke="currentColor"
          className="w-6 h-6"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M8.25 6.75h12M8.25 12h12m-12 5.25h12M3.75 6.75h.007v.008H3.75V6.75zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zM3.75 12h.007v.008H3.75V12zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm-.375 5.25h.007v.008H3.75v-.008zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z"
          />
        </svg>
      </button>
    );
  };

  // Sidebar content for desktop
  const desktopSidebarContent = (
    <div className="h-full flex flex-col">
      <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
        {userMessages.length > 0 ? (
          <ul className="space-y-2">
            {userMessages.map((msg) => (
              <li key={msg.id}>
                <button
                  onClick={() => handleMessageClick(msg.text)}
                  className="w-full text-left p-2 rounded-md hover:bg-[hsl(var(--muted))] transition-colors text-sm"
                >
                  <p className="truncate">{msg.text}</p>
                  <p className="text-xs text-[hsl(var(--muted-foreground))]">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </p>
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-[hsl(var(--muted-foreground))] text-sm">
            No chat history yet. Start by asking a question!
          </p>
        )}
      </div>
      
      <div className="p-4 border-t">
        <ChatInterface 
          isMobile={isMobile} 
          onProductResultsClick={onProductResultsClick}
        />
      </div>
    </div>
  );

  // Mobile sidebar content
  const mobileSidebarContent = (
    <div className="h-full flex flex-col">
      <h2 className="text-lg font-semibold mb-4">Chat History</h2>
      
      <SessionStats />
      
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {userMessages.length > 0 ? (
          <ul className="space-y-2">
            {userMessages.map((msg) => (
              <li key={msg.id}>
                <button
                  onClick={() => handleMessageClick(msg.text)}
                  className="w-full text-left p-2 rounded-md hover:bg-[hsl(var(--muted))] transition-colors text-sm"
                >
                  <p className="truncate">{msg.text}</p>
                  <p className="text-xs text-[hsl(var(--muted-foreground))]">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </p>
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-[hsl(var(--muted-foreground))] text-sm">
            No chat history yet. Start by asking a question!
          </p>
        )}
      </div>
    </div>
  );

  // For mobile: render a drawer that can be toggled
  if (isMobile) {
    return (
      <>
        {renderFloatingButton()}
        
        {/* Mobile drawer */}
        <div
          className={`fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity ${
            isOpen ? "opacity-100" : "opacity-0 pointer-events-none"
          }`}
          onClick={toggleSidebar}
        />
        
        <div
          className={`fixed top-0 left-0 h-full w-3/4 max-w-xs bg-[hsl(var(--background))] z-50 transform transition-transform ${
            isOpen ? "translate-x-0" : "-translate-x-full"
          } p-4 overflow-y-auto custom-scrollbar`}
        >
          <button
            onClick={toggleSidebar}
            className="absolute top-4 right-4 p-2"
            aria-label="Close sidebar"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
              className="w-6 h-6"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
          
          <div className="mt-8">{mobileSidebarContent}</div>
        </div>
      </>
    );
  }

  // For desktop: render the sidebar directly
  return desktopSidebarContent;
}