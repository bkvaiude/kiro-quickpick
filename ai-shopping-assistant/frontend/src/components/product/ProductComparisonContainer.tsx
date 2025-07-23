import type { Product } from "../../types/chat";
import { Card } from "../ui/card";
import { RecommendationsSummary } from "./RecommendationsSummary";

interface ProductComparisonContainerProps {
  products: Product[];
  recommendationsSummary: string;
}

export function ProductComparisonContainer({ 
  products, 
  recommendationsSummary 
}: ProductComparisonContainerProps) {
  // Find products with special highlights
  const findHighlightedProducts = () => {
    if (!products.length) return { bestValue: null, lowestPrice: null, highestRating: null };
    
    // Calculate a value score for each product (higher is better)
    // Formula: rating / price * 1000 (to get a reasonable number)
    const productsWithScore = products.map(product => ({
      ...product,
      valueScore: (product.rating / product.price) * 1000
    }));
    
    // Sort by different criteria
    const byValueScore = [...productsWithScore].sort((a, b) => b.valueScore - a.valueScore);
    const byPrice = [...products].sort((a, b) => a.price - b.price);
    const byRating = [...products].sort((a, b) => b.rating - a.rating);
    
    return {
      bestValue: byValueScore[0],
      lowestPrice: byPrice[0],
      highestRating: byRating[0]
    };
  };
  
  const { bestValue, lowestPrice, highestRating } = findHighlightedProducts();
  
  // Function to determine product badges
  const getProductBadges = (product: Product) => {
    const badges = [];
    
    if (bestValue && product.title === bestValue.title) {
      badges.push({ text: "Best Value", color: "green" });
    }
    
    if (lowestPrice && product.title === lowestPrice.title && product.title !== bestValue?.title) {
      badges.push({ text: "Lowest Price", color: "blue" });
    }
    
    if (highestRating && product.title === highestRating.title && 
        product.title !== bestValue?.title && product.title !== lowestPrice?.title) {
      badges.push({ text: "Highest Rating", color: "purple" });
    }
    
    return badges;
  };
  
  return (
    <div className="space-y-6">
      {/* Display the recommendations summary */}
      <RecommendationsSummary summary={recommendationsSummary} />
      
      {/* Product comparison matrix */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {products.map((product, index) => {
          const badges = getProductBadges(product);
          const isBestValue = bestValue && product.title === bestValue.title;
          
          return (
            <Card 
              key={index} 
              className={`p-5 relative ${isBestValue ? 'border-2 border-green-500 shadow-lg' : ''}`}
            >
              {/* Display badges */}
              <div className="absolute -top-3 right-3 flex flex-col gap-2">
                {badges.map((badge, i) => (
                  <div 
                    key={i} 
                    className={`bg-${badge.color}-500 text-white px-3 py-1 rounded-md text-xs font-bold shadow-md`}
                    style={{ backgroundColor: badge.color === 'green' ? '#10b981' : 
                                            badge.color === 'blue' ? '#3b82f6' : 
                                            '#8b5cf6' }}
                  >
                    {badge.text}
                  </div>
                ))}
              </div>
              
              <h3 className="font-semibold text-lg mb-2 pr-20">{product.title}</h3>
              <div className="flex justify-between items-center mb-3">
                <p className="text-xl font-bold">₹{product.price.toLocaleString()}</p>
                <div className="flex items-center">
                  <span className="text-yellow-500 mr-1">★</span>
                  <span className="font-medium">{product.rating}</span>
                </div>
              </div>
              
              <div className="mb-4">
                <h4 className="font-medium mb-2 text-[hsl(var(--primary))]">Features:</h4>
                <ul className="list-disc pl-5 text-sm space-y-1">
                  {product.features.map((feature, i) => (
                    <li key={i}>{feature}</li>
                  ))}
                </ul>
              </div>
              
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <h4 className="font-medium mb-2 text-green-600 flex items-center">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Pros:
                  </h4>
                  <ul className="list-disc pl-5 text-sm space-y-1">
                    {product.pros.map((pro, i) => (
                      <li key={i}>{pro}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h4 className="font-medium mb-2 text-red-600 flex items-center">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    Cons:
                  </h4>
                  <ul className="list-disc pl-5 text-sm space-y-1">
                    {product.cons.map((con, i) => (
                      <li key={i}>{con}</li>
                    ))}
                  </ul>
                </div>
              </div>
              
              <a 
                href={product.link} 
                target="_blank" 
                rel="noopener noreferrer"
                className={`block w-full text-center py-2 rounded-md transition-colors ${
                  isBestValue 
                    ? 'bg-green-500 hover:bg-green-600 text-white font-medium' 
                    : 'bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] hover:bg-[hsl(var(--primary))]/90'
                }`}
              >
                Buy Now
              </a>
            </Card>
          );
        })}
      </div>
    </div>
  );
}