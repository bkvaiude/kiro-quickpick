export interface ChatMessage {
  id: string;
  text: string;
  sender: 'user' | 'system';
  timestamp: Date;
  products?: Product[];
  recommendationsSummary?: string;
}

export interface Product {
  title: string;
  price: number;
  rating: number;
  features: string[];
  pros: string[];
  cons: string[];
  link: string;
}

export interface ConversationContext {
  messages: ChatMessage[];
  lastQuery?: string;
  lastProductCriteria?: {
    category?: string;
    priceRange?: {min?: number; max?: number};
    features?: string[];
    brand?: string;
    marketplace?: string;
  };
}

export interface ApiResponse {
  query: string;
  products: Product[];
  recommendationsSummary: string;
  error?: string;
}