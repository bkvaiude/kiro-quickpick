import { useState, useEffect } from "react";
import { Layout } from "./components/layout/Layout";
import { ChatInterface } from "./components/chat/ChatInterface";
import { ChatProvider } from "./context/ChatContext";
import { AuthProvider } from "./context/AuthContext";
import { ThemeProvider } from "./components/theme/ThemeProvider";
import { ProductComparisonContainer } from "./components/product/ProductComparisonContainer";
import { useChatContext } from "./context/ChatContext";
import { Card } from "./components/ui/card";
import { LoginPromptModal } from "./components/auth/LoginPromptModal";
import { WelcomeMessage } from "./components/auth/WelcomeMessage";

// Create a component that uses the context
function AppContent() {
  const { state } = useChatContext();
  const [isMobile, setIsMobile] = useState(false);
  const [selectedMessageId, setSelectedMessageId] = useState<string | null>(null);
  
  // Find the message with products to display
  const getMessageToDisplay = () => {
    if (selectedMessageId) {
      // If a specific message is selected, find it
      const selectedMessage = state.messages.find(
        msg => msg.id === selectedMessageId && msg.products && msg.products.length > 0
      );
      if (selectedMessage) return selectedMessage;
    }
    
    // Otherwise, get the last message with products
    return state.messages
      .filter(msg => msg.sender === 'system' && msg.products && msg.products.length > 0)
      .pop();
  };
  
  const messageToDisplay = getMessageToDisplay();

  // Check if the screen is mobile size
  useEffect(() => {
    const checkIfMobile = () => {
      setIsMobile(window.innerWidth < 768); // 768px is the md breakpoint in Tailwind
    };

    // Initial check
    checkIfMobile();

    // Add event listener for window resize
    window.addEventListener("resize", checkIfMobile);

    // Clean up
    return () => window.removeEventListener("resize", checkIfMobile);
  }, []);
  
  // When a new message with products arrives, select it automatically
  useEffect(() => {
    const lastMessageWithProducts = state.messages
      .filter(msg => msg.sender === 'system' && msg.products && msg.products.length > 0)
      .pop();
      
    if (lastMessageWithProducts) {
      setSelectedMessageId(lastMessageWithProducts.id);
    }
  }, [state.messages]);
  
  // Handle product results click from chat message
  const handleProductResultsClick = (messageId: string) => {
    setSelectedMessageId(messageId);
  };

  // Marketing message component when no products are displayed
  const MarketingMessage = () => (
    <div className="flex flex-col items-center justify-center h-full p-8 text-center">
      <div className="mb-6">
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          strokeWidth="2" 
          strokeLinecap="round" 
          strokeLinejoin="round" 
          className="w-16 h-16 text-[hsl(var(--primary))] mx-auto mb-4"
        >
          <circle cx="12" cy="12" r="10" />
          <path d="M12 16v-4" />
          <path d="M12 8h.01" />
        </svg>
      </div>
      <h2 className="text-3xl font-bold tracking-tight mb-4">
        Your AI Shopping Assistant
      </h2>
      <p className="text-[hsl(var(--muted-foreground))] mb-6 max-w-md">
        Ask me about products and I'll help you find the best options based on your requirements.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full max-w-3xl">
        <Card className="p-4 text-center">
          <h3 className="font-medium mb-2">Natural Language</h3>
          <p className="text-sm text-[hsl(var(--muted-foreground))]">
            Ask in your own words about products you're looking for
          </p>
        </Card>
        <Card className="p-4 text-center">
          <h3 className="font-medium mb-2">Smart Comparison</h3>
          <p className="text-sm text-[hsl(var(--muted-foreground))]">
            Get detailed comparisons with pros and cons
          </p>
        </Card>
        <Card className="p-4 text-center">
          <h3 className="font-medium mb-2">Best Value</h3>
          <p className="text-sm text-[hsl(var(--muted-foreground))]">
            We highlight the best value options for you
          </p>
        </Card>
      </div>
    </div>
  );

  return (
    <Layout onProductResultsClick={handleProductResultsClick} isMobile={isMobile}>
      {/* Right panel content */}
      <div className="flex flex-col h-full overflow-hidden">
        {/* Mobile chat interface (only visible on mobile) */}
        <div className="md:hidden w-full border-b p-4">
          <ChatInterface isMobile={true} />
        </div>
        
        {/* Product comparison or marketing message */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 custom-scrollbar">
          {messageToDisplay && messageToDisplay.products && messageToDisplay.products.length > 0 ? (
            <ProductComparisonContainer 
              products={messageToDisplay.products} 
              recommendationsSummary={messageToDisplay.recommendationsSummary || ''} 
            />
          ) : (
            <MarketingMessage />
          )}
        </div>
      </div>
      
      {/* Authentication-related modals */}
      <LoginPromptModal />
      <WelcomeMessage />
    </Layout>
  );
}

function App() {
  return (
    <ThemeProvider defaultTheme="system" storageKey="shopping-assistant-theme">
      <AuthProvider>
        <ChatProvider>
          <AppContent />
        </ChatProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;