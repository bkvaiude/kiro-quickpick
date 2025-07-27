import { Card } from "../ui/card";
import { useChatContext } from "../../context/ChatContext";

interface EmptyProductStateProps {
  query?: string;
  recommendationsSummary?: string;
}

export function EmptyProductState({ query, recommendationsSummary }: EmptyProductStateProps) {
  const { sendMessage } = useChatContext();

  // Generate smart suggestions based on the query
  const generateSmartSuggestions = (query: string) => {
    const lowerQuery = query.toLowerCase();
    
    // Category-based suggestions
    if (lowerQuery.includes('phone') || lowerQuery.includes('mobile')) {
      return [
        "Best smartphones under ₹20,000",
        "iPhone vs Android comparison 2024",
        "5G phones with best camera",
        "Gaming phones under ₹30,000"
      ];
    }
    
    if (lowerQuery.includes('laptop') || lowerQuery.includes('computer')) {
      return [
        "Best laptops for students under ₹40,000",
        "Gaming laptops vs workstation laptops",
        "MacBook vs Windows laptop comparison",
        "Ultrabooks with best battery life"
      ];
    }
    
    if (lowerQuery.includes('tv') || lowerQuery.includes('television')) {
      return [
        "Best 55-inch smart TVs under ₹50,000",
        "OLED vs QLED TV comparison",
        "Budget smart TVs with good picture quality",
        "Best TVs for gaming and movies"
      ];
    }
    
    if (lowerQuery.includes('headphone') || lowerQuery.includes('earphone') || lowerQuery.includes('audio')) {
      return [
        "Best wireless earbuds under ₹5,000",
        "Noise canceling headphones comparison",
        "Gaming headsets with best mic quality",
        "Audiophile headphones for music lovers"
      ];
    }
    
    // Generic suggestions if no specific category detected
    return [
      "Popular products in electronics",
      "Best deals available today",
      "Top rated products this month",
      "Budget-friendly alternatives"
    ];
  };

  const suggestions = query ? generateSmartSuggestions(query) : [];

  const handleSuggestionClick = (suggestion: string) => {
    sendMessage(suggestion);
  };

  return (
    <div className="space-y-6">
      {/* Show recommendations summary if available */}
      {recommendationsSummary && (
        <Card className="p-6 bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                viewBox="0 0 24 24" 
                fill="none" 
                stroke="currentColor" 
                strokeWidth="2" 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                className="w-6 h-6 text-blue-600 dark:text-blue-400"
              >
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">AI Recommendations</h3>
              <div className="text-blue-800 dark:text-blue-200 whitespace-pre-line">
                {recommendationsSummary}
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* No products found message */}
      <div className="text-center py-12">
        <div className="mb-6">
          <div className="w-16 h-16 bg-gradient-to-br from-orange-400 to-red-500 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="white" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              className="w-8 h-8"
            >
              <circle cx="11" cy="11" r="8" />
              <path d="M21 21l-4.35-4.35" />
            </svg>
          </div>
        </div>
        
        <h2 className="text-2xl font-bold mb-4">
          {query ? "No exact matches found" : "Let's find what you're looking for"}
        </h2>
        
        <p className="text-[hsl(var(--muted-foreground))] mb-8 max-w-md mx-auto">
          {query 
            ? `I couldn't find specific products for "${query}", but I can help you with similar or related items.`
            : "Ask me about any product and I'll provide personalized recommendations with detailed comparisons."
          }
        </p>

        {/* Smart suggestions based on query */}
        {suggestions.length > 0 && (
          <div className="mb-8">
            <h3 className="text-lg font-semibold mb-4">Try these related searches:</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
              {suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="p-3 text-left bg-[hsl(var(--muted))] hover:bg-[hsl(var(--muted))]/80 rounded-lg transition-colors border border-transparent hover:border-[hsl(var(--primary))]/20"
                >
                  <div className="flex items-center">
                    <span className="text-[hsl(var(--primary))] mr-2">💡</span>
                    <span className="text-sm">{suggestion}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Why choose our AI assistant */}
        <div className="bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-950/20 dark:to-blue-950/20 rounded-lg p-6 max-w-3xl mx-auto">
          <h3 className="text-xl font-bold mb-4">Why Choose Our AI Shopping Assistant?</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl mb-2">🎯</div>
              <h4 className="font-semibold mb-1">Precise Matching</h4>
              <p className="text-sm text-[hsl(var(--muted-foreground))]">
                Advanced AI understands your exact requirements
              </p>
            </div>
            <div className="text-center">
              <div className="text-2xl mb-2">⚡</div>
              <h4 className="font-semibold mb-1">Instant Results</h4>
              <p className="text-sm text-[hsl(var(--muted-foreground))]">
                Get comprehensive comparisons in seconds
              </p>
            </div>
            <div className="text-center">
              <div className="text-2xl mb-2">💎</div>
              <h4 className="font-semibold mb-1">Best Value</h4>
              <p className="text-sm text-[hsl(var(--muted-foreground))]">
                We highlight the best deals and value options
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}