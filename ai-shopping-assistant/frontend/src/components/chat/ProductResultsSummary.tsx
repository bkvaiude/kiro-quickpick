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
  
  // Extract a short summary from the recommendations
  const shortSummary = recommendationsSummary
    .split('\n')
    .filter(line => line.trim())
    .slice(0, 1)
    .join('');
  
  return (
    <Card 
      className="p-4 cursor-pointer hover:bg-[hsl(var(--muted))] transition-colors mt-2"
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-medium text-sm">
            {products.length} product{products.length !== 1 ? 's' : ''} found
          </h3>
          <p className="text-xs text-[hsl(var(--muted-foreground))] mt-1 line-clamp-1">
            {shortSummary || `Including ${bestValueProduct?.title || 'top recommendations'}`}
          </p>
        </div>
        <div className="flex items-center text-[hsl(var(--primary))]">
          <span className="text-sm mr-1">View results</span>
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