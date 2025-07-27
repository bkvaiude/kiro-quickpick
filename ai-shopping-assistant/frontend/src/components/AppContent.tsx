import { useState, useEffect } from "react";
import { Layout } from "./layout/Layout";
import { ChatInterface } from "./chat/ChatInterface";
import { useChatContext } from "../context/ChatContext";
import { Card } from "./ui/card";
import { LoginPromptModal } from "./auth/LoginPromptModal";
import { WelcomeMessage } from "./auth/WelcomeMessage";
import { ProductComparisonContainer } from "./product/ProductComparisonContainer";

// Create a component that uses the context
function AppContent() {
  const { state } = useChatContext();
  const [isMobile, setIsMobile] = useState(false);
  const [selectedMessageId, setSelectedMessageId] = useState<string | null>(null);
  
  // Find the message with products or recommendations to display
  const getMessageToDisplay = () => {
    if (selectedMessageId) {
      // If a specific message is selected, find it
      const selectedMessage = state.messages.find(
        msg => msg.id === selectedMessageId && (
          (msg.products && msg.products.length > 0) || 
          msg.recommendationsSummary
        )
      );
      if (selectedMessage) return selectedMessage;
    }
    
    // Otherwise, get the last message with products or recommendations
    return state.messages
      .filter(msg => msg.sender === 'system' && (
        (msg.products && msg.products.length > 0) || 
        msg.recommendationsSummary
      ))
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
  
  // When a new message with products or recommendations arrives, select it automatically
  useEffect(() => {
    const lastMessageWithContent = state.messages
      .filter(msg => msg.sender === 'system' && (
        (msg.products && msg.products.length > 0) || 
        msg.recommendationsSummary
      ))
      .pop();
      
    if (lastMessageWithContent) {
      setSelectedMessageId(lastMessageWithContent.id);
    }
  }, [state.messages]);
  
  // Handle product results click from chat message
  const handleProductResultsClick = (messageId: string) => {
    setSelectedMessageId(messageId);
  };

  // AI Recommendations component for popular categories
  const AIRecommendations = () => {
    const popularCategories = [
      {
        title: "Smartphones",
        description: "Latest 5G phones with great cameras",
        suggestions: ["Best phones under ₹15,000", "iPhone vs Android comparison", "Gaming phones 2024"],
        icon: "📱"
      },
      {
        title: "Laptops",
        description: "Work, gaming, and student laptops",
        suggestions: ["Best laptops for programming", "Gaming laptops under ₹60,000", "Ultrabooks for professionals"],
        icon: "💻"
      },
      {
        title: "Smart TVs",
        description: "4K, OLED, and budget-friendly options",
        suggestions: ["Best 55-inch smart TVs", "OLED vs QLED comparison", "Budget smart TVs under ₹30,000"],
        icon: "📺"
      },
      {
        title: "Headphones",
        description: "Wireless, noise-canceling, and gaming",
        suggestions: ["Best wireless earbuds", "Noise canceling headphones", "Gaming headsets under ₹5,000"],
        icon: "🎧"
      },
      {
        title: "Home Appliances",
        description: "Kitchen, cleaning, and comfort solutions",
        suggestions: ["Best air conditioners", "Washing machines comparison", "Kitchen appliances for small homes"],
        icon: "🏠"
      },
      {
        title: "Fashion & Beauty",
        description: "Trending styles and beauty essentials",
        suggestions: ["Summer fashion trends", "Best skincare products", "Affordable designer alternatives"],
        icon: "👗"
      }
    ];

    const handleSuggestionClick = (suggestion: string) => {
      // Use the sendMessage function from chat context
      const { sendMessage } = useChatContext();
      sendMessage(suggestion);
    };

    return (
      <div className="space-y-8">
        {/* Hero Section */}
        <div className="text-center mb-8">
          <div className="mb-6">
            <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                viewBox="0 0 24 24" 
                fill="none" 
                stroke="white" 
                strokeWidth="2" 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                className="w-10 h-10"
              >
                <path d="M9 11H5a2 2 0 0 0-2 2v3c0 1.1.9 2 2 2h4" />
                <path d="M20 12v6a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-6" />
                <path d="M9 7V4a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v3" />
                <path d="M8 21l4-7 4 7" />
                <path d="M12 11V9" />
              </svg>
            </div>
          </div>
          <h2 className="text-4xl font-bold tracking-tight mb-4 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Your AI Shopping Assistant
          </h2>
          <p className="text-[hsl(var(--muted-foreground))] mb-6 max-w-2xl mx-auto text-lg">
            Get personalized product recommendations, detailed comparisons, and find the best deals across thousands of products. 
            Just ask me what you're looking for!
          </p>
          
          {/* Key Features */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8 max-w-4xl mx-auto">
            <Card className="p-4 text-center border-2 hover:border-blue-300 transition-colors">
              <div className="text-2xl mb-2">🤖</div>
              <h3 className="font-semibold mb-2">AI-Powered Search</h3>
              <p className="text-sm text-[hsl(var(--muted-foreground))]">
                Natural language understanding for precise product matching
              </p>
            </Card>
            <Card className="p-4 text-center border-2 hover:border-purple-300 transition-colors">
              <div className="text-2xl mb-2">⚡</div>
              <h3 className="font-semibold mb-2">Instant Comparisons</h3>
              <p className="text-sm text-[hsl(var(--muted-foreground))]">
                Side-by-side analysis with pros, cons, and value ratings
              </p>
            </Card>
            <Card className="p-4 text-center border-2 hover:border-green-300 transition-colors">
              <div className="text-2xl mb-2">💰</div>
              <h3 className="font-semibold mb-2">Best Deals</h3>
              <p className="text-sm text-[hsl(var(--muted-foreground))]">
                Real-time price tracking and value-for-money recommendations
              </p>
            </Card>
          </div>
        </div>

        {/* Popular Categories */}
        <div>
          <h3 className="text-2xl font-bold mb-6 text-center">Popular Categories & AI Suggestions</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {popularCategories.map((category, index) => (
              <Card key={index} className="p-6 hover:shadow-lg transition-shadow border-l-4 border-l-blue-500">
                <div className="flex items-center mb-4">
                  <span className="text-3xl mr-3">{category.icon}</span>
                  <div>
                    <h4 className="font-semibold text-lg">{category.title}</h4>
                    <p className="text-sm text-[hsl(var(--muted-foreground))]">{category.description}</p>
                  </div>
                </div>
                <div className="space-y-2">
                  <p className="text-sm font-medium text-[hsl(var(--primary))]">Try asking:</p>
                  {category.suggestions.map((suggestion, i) => (
                    <button
                      key={i}
                      onClick={() => handleSuggestionClick(suggestion)}
                      className="block w-full text-left text-sm p-2 rounded-md bg-[hsl(var(--muted))] hover:bg-[hsl(var(--muted))]/80 transition-colors"
                    >
                      "• {suggestion}"
                    </button>
                  ))}
                </div>
              </Card>
            ))}
          </div>
        </div>

        {/* Call to Action */}
        <div className="text-center bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950/20 dark:to-purple-950/20 rounded-lg p-8">
          <h3 className="text-2xl font-bold mb-4">Ready to Find Your Perfect Product?</h3>
          <p className="text-[hsl(var(--muted-foreground))] mb-6 max-w-2xl mx-auto">
            Start by typing what you're looking for in the chat. I'll analyze your requirements and provide 
            personalized recommendations with detailed comparisons to help you make the best choice.
          </p>
          <div className="flex flex-wrap justify-center gap-2 text-sm">
            <span className="bg-white dark:bg-gray-800 px-3 py-1 rounded-full border">💬 Natural language queries</span>
            <span className="bg-white dark:bg-gray-800 px-3 py-1 rounded-full border">🔍 Smart product matching</span>
            <span className="bg-white dark:bg-gray-800 px-3 py-1 rounded-full border">📊 Detailed comparisons</span>
            <span className="bg-white dark:bg-gray-800 px-3 py-1 rounded-full border">💡 Expert recommendations</span>
          </div>
        </div>
      </div>
    );
  };

  // Marketing message component when no products are displayed
  const MarketingMessage = () => <AIRecommendations />;

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
          {messageToDisplay ? (
            <ProductComparisonContainer 
              products={messageToDisplay.products || []} 
              recommendationsSummary={messageToDisplay.recommendationsSummary || ''} 
              query={state.conversationContext.lastQuery}
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

export default AppContent;