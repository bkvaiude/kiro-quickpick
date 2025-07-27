import { useChatContext } from "../../context/ChatContext";
import { Card } from "../ui/card";
import type { Product } from "../../types/chat";

interface ProductResultsSummaryProps {
  products: Product[];
  recommendationsSummary: string;
  onClick: () => void;
}

export function ProductResultsSummary({ 
  products, 
  recommendationsSummary,
  onClick 
}: ProductResultsSummaryProps) {
  // Find the best value product
  const findBestValue = () => {
    if (!products.length) return null;
    
    // Calculate a value score for each product (higher is better)
    const productsWithScore = products.map(product => ({
      ...product,
      valueScore: (product.rating / product.price) * 1000
    }));
    
    // Sort by value score (descending)
    productsWithScore.sort((a, b) => b.valueScore - a.valueScore);
    
    // Return the product with the highest value score
    return productsWithScore[0];
  };
  
  const bestValueProduct = findBestValue();
  const hasProducts = products && products.length > 0;
  const hasRecommendations = recommendationsSummary && recommendationsSummary.trim();
  
  // Don't render if there are no products and no recommendations
  if (!hasProducts && !hasRecommendations) {
    return null;
  }
  
  // Extract a short summary from the recommendations
  const shortSummary = recommendationsSummary
    .split('\n')
    .filter(line => line.trim())
    .slice(0, 1)
    .join('');
  
  // Determine the display content based on what's available
  const getDisplayContent = () => {
    if (hasProducts) {
      return {
        title: `${products.length} product${products.length !== 1 ? 's' : ''} found`,
        subtitle: shortSummary || `Including ${bestValueProduct?.title || 'top recommendations'}`,
        actionText: 'View results',
        cardClass: 'border-green-200 dark:border-green-800'
      };
    } else {
      return {
        title: 'AI Recommendations Available',
        subtitle: shortSummary || 'Smart suggestions and alternatives for your search',
        actionText: 'View suggestions',
        cardClass: 'border-blue-200 dark:border-blue-800'
      };
    }
  };
  
  const displayContent = getDisplayContent();
  
  return (
    <Card 
      className={`p-4 cursor-pointer hover:bg-[hsl(var(--muted))] transition-colors mt-2 ${displayContent.cardClass}`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          {/* Icon based on content type */}
          <div className="mr-3">
            {hasProducts ? (
              <div className="w-8 h-8 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center">
                <svg 
                  xmlns="http://www.w3.org/2000/svg" 
                  width="16" 
                  height="16" 
                  viewBox="0 0 24 24" 
                  fill="none" 
                  stroke="currentColor" 
                  strokeWidth="2" 
                  strokeLinecap="round" 
                  strokeLinejoin="round"
                  className="text-green-600 dark:text-green-400"
                >
                  <path d="M5 7h14l-1 10H6L5 7z"/>
                  <path d="M5 7l-1-4H2"/>
                  <circle cx="9" cy="20" r="1"/>
                  <circle cx="20" cy="20" r="1"/>
                </svg>
              </div>
            ) : (
              <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                <svg 
                  xmlns="http://www.w3.org/2000/svg" 
                  width="16" 
                  height="16" 
                  viewBox="0 0 24 24" 
                  fill="none" 
                  stroke="currentColor" 
                  strokeWidth="2" 
                  strokeLinecap="round" 
                  strokeLinejoin="round"
                  className="text-blue-600 dark:text-blue-400"
                >
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                </svg>
              </div>
            )}
          </div>
          <div>
            <h3 className="font-medium text-sm">
              {displayContent.title}
            </h3>
            <p className="text-xs text-[hsl(var(--muted-foreground))] mt-1 line-clamp-1">
              {displayContent.subtitle}
            </p>
          </div>
        </div>
        <div className="flex items-center text-[hsl(var(--primary))]">
          <span className="text-sm mr-1">{displayContent.actionText}</span>
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            width="16" 
            height="16" 
            viewBox="0 0 24 24" 
            fill="none" 
            stroke="currentColor" 
            strokeWidth="2" 
            strokeLinecap="round" 
            strokeLinejoin="round"
          >
            <path d="m9 18 6-6-6-6"/>
          </svg>
        </div>
      </div>
    </Card>
  );
}