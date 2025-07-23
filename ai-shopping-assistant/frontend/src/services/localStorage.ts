import type { ChatMessage, ConversationContext, Product } from '../types/chat';

// Maximum number of messages to store in local storage
const MAX_STORED_MESSAGES = 50;

// Storage keys
const STORAGE_KEYS = {
  MESSAGES: 'ai_shopping_assistant_messages',
  CONTEXT: 'ai_shopping_assistant_context',
  LAST_ACTIVE: 'ai_shopping_assistant_last_active',
  SETTINGS: 'ai_shopping_assistant_settings'
};

/**
 * Service for handling local storage operations
 */
export const LocalStorageService = {
  /**
   * Save chat messages to local storage
   * @param messages Array of chat messages to save
   */
  saveMessages(messages: ChatMessage[]): void {
    try {
      // Limit the number of messages stored to prevent excessive storage usage
      const limitedMessages = messages.slice(-MAX_STORED_MESSAGES);
      
      // Convert Date objects to strings for storage
      const messagesToStore = limitedMessages.map(msg => ({
        ...msg,
        timestamp: msg.timestamp.toISOString(),
      }));
      
      localStorage.setItem(STORAGE_KEYS.MESSAGES, JSON.stringify(messagesToStore));
      
      // Update last active timestamp
      this.updateLastActiveTime();
    } catch (error) {
      console.error('Error saving messages to local storage:', error);
    }
  },

  /**
   * Load chat messages from local storage
   * @returns Array of chat messages or empty array if none found
   */
  loadMessages(): ChatMessage[] {
    try {
      const savedMessages = localStorage.getItem(STORAGE_KEYS.MESSAGES);
      if (!savedMessages) return [];

      const parsedMessages = JSON.parse(savedMessages);
      
      // Convert string timestamps back to Date objects and handle product data
      return parsedMessages.map((msg: any) => ({
        ...msg,
        timestamp: new Date(msg.timestamp),
        // Ensure products are properly handled if they exist
        products: msg.products ? msg.products.map((product: any) => this.sanitizeProduct(product)) : undefined
      }));
    } catch (error) {
      console.error('Error loading messages from local storage:', error);
      return [];
    }
  },

  /**
   * Save conversation context to local storage
   * @param context Conversation context to save
   */
  saveConversationContext(context: ConversationContext): void {
    try {
      // Convert Date objects to strings for storage
      const contextToStore = {
        ...context,
        messages: context.messages.slice(-10).map(msg => ({
          ...msg,
          timestamp: msg.timestamp.toISOString(),
        })),
      };
      
      localStorage.setItem(STORAGE_KEYS.CONTEXT, JSON.stringify(contextToStore));
      
      // Update last active timestamp
      this.updateLastActiveTime();
    } catch (error) {
      console.error('Error saving conversation context to local storage:', error);
    }
  },

  /**
   * Load conversation context from local storage
   * @returns Conversation context or default context if none found
   */
  loadConversationContext(): ConversationContext {
    try {
      const savedContext = localStorage.getItem(STORAGE_KEYS.CONTEXT);
      if (!savedContext) {
        return { messages: [] };
      }

      const parsedContext = JSON.parse(savedContext);
      
      // Convert string timestamps back to Date objects
      return {
        ...parsedContext,
        messages: parsedContext.messages.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp),
          // Ensure products are properly handled if they exist
          products: msg.products ? msg.products.map((product: any) => this.sanitizeProduct(product)) : undefined
        })),
      };
    } catch (error) {
      console.error('Error loading conversation context from local storage:', error);
      return { messages: [] };
    }
  },

  /**
   * Clear all chat data from local storage
   */
  clearChatData(): void {
    try {
      localStorage.removeItem(STORAGE_KEYS.MESSAGES);
      localStorage.removeItem(STORAGE_KEYS.CONTEXT);
      // Don't remove settings or last active time
    } catch (error) {
      console.error('Error clearing chat data from local storage:', error);
    }
  },
  
  /**
   * Update the last active timestamp
   */
  updateLastActiveTime(): void {
    try {
      localStorage.setItem(STORAGE_KEYS.LAST_ACTIVE, new Date().toISOString());
    } catch (error) {
      console.error('Error updating last active time:', error);
    }
  },
  
  /**
   * Get the last active timestamp
   * @returns Date object of last active time or null if not found
   */
  getLastActiveTime(): Date | null {
    try {
      const lastActive = localStorage.getItem(STORAGE_KEYS.LAST_ACTIVE);
      return lastActive ? new Date(lastActive) : null;
    } catch (error) {
      console.error('Error getting last active time:', error);
      return null;
    }
  },
  
  /**
   * Check if the conversation is expired (older than the specified days)
   * @param days Number of days after which a conversation is considered expired
   * @returns True if conversation is expired, false otherwise
   */
  isConversationExpired(days: number = 7): boolean {
    const lastActive = this.getLastActiveTime();
    if (!lastActive) return false;
    
    const expiryTime = new Date();
    expiryTime.setDate(expiryTime.getDate() - days);
    
    return lastActive < expiryTime;
  },
  
  /**
   * Extract product criteria from conversation context
   * @param context The conversation context
   * @returns Object with extracted product criteria
   */
  extractProductCriteria(context: ConversationContext): Record<string, any> {
    const criteria: Record<string, any> = {};
    
    // Start with any existing criteria
    if (context.lastProductCriteria) {
      Object.assign(criteria, context.lastProductCriteria);
    }
    
    // Analyze recent messages for additional criteria
    // This is a simplified implementation - in a real app, you might use NLP
    const recentMessages = context.messages.slice(-5);
    
    for (const msg of recentMessages) {
      if (msg.sender === 'user') {
        const text = msg.text.toLowerCase();
        
        // Extract price information
        const priceMatch = text.match(/under (?:₹|rs\.?|inr)?\s?(\d+[,\d]*)/i);
        if (priceMatch) {
          const price = parseInt(priceMatch[1].replace(/,/g, ''));
          criteria.priceRange = criteria.priceRange || {};
          criteria.priceRange.max = price;
        }
        
        // Extract brand preferences
        const brands = ['samsung', 'apple', 'xiaomi', 'redmi', 'realme', 'poco', 'oneplus', 'vivo', 'oppo'];
        for (const brand of brands) {
          if (text.includes(brand)) {
            criteria.brand = brand;
            break;
          }
        }
        
        // Extract marketplace preferences
        if (text.includes('amazon')) {
          criteria.marketplace = 'Amazon';
        } else if (text.includes('flipkart')) {
          criteria.marketplace = 'Flipkart';
        }
      }
    }
    
    return criteria;
  },
  
  /**
   * Sanitize product data to ensure it has all required fields
   * @param product The product object to sanitize
   * @returns Sanitized product object
   */
  sanitizeProduct(product: any): Product {
    return {
      title: product.title || 'Unknown Product',
      price: typeof product.price === 'number' ? product.price : 0,
      rating: typeof product.rating === 'number' ? product.rating : 0,
      features: Array.isArray(product.features) ? product.features : [],
      pros: Array.isArray(product.pros) ? product.pros : [],
      cons: Array.isArray(product.cons) ? product.cons : [],
      link: product.link || '#',
    };
  },
  
  /**
   * Save user settings to local storage
   * @param settings User settings object
   */
  saveSettings(settings: Record<string, any>): void {
    try {
      localStorage.setItem(STORAGE_KEYS.SETTINGS, JSON.stringify(settings));
    } catch (error) {
      console.error('Error saving settings to local storage:', error);
    }
  },
  
  /**
   * Load user settings from local storage
   * @returns User settings object or empty object if none found
   */
  loadSettings(): Record<string, any> {
    try {
      const savedSettings = localStorage.getItem(STORAGE_KEYS.SETTINGS);
      return savedSettings ? JSON.parse(savedSettings) : {};
    } catch (error) {
      console.error('Error loading settings from local storage:', error);
      return {};
    }
  },
};