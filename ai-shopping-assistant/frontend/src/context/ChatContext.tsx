import { createContext, useContext, useReducer, useEffect } from 'react';
import type { ReactNode } from 'react';
import { v4 as uuidv4 } from 'uuid';
import type { ChatMessage, ConversationContext, ApiResponse } from '../types/chat';
import { LocalStorageService } from '../services/localStorage';
import { ApiService, ApiError, ApiErrorType } from '../services/api';
import { useAuth } from './AuthContext';
import { ActionType } from '../services/userActionService';

// Define the state type
interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  conversationContext: ConversationContext;
}

// Define action types
type ChatAction =
  | { type: 'ADD_MESSAGE'; payload: ChatMessage }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'CLEAR_MESSAGES' }
  | { type: 'UPDATE_CONVERSATION_CONTEXT'; payload: Partial<ConversationContext> }
  | { type: 'LOAD_MESSAGES'; payload: ChatMessage[] };

// Initial state
const initialState: ChatState = {
  messages: [],
  isLoading: false,
  error: null,
  conversationContext: {
    messages: [],
    lastQuery: undefined,
    lastProductCriteria: undefined,
  },
};

// Create the context
const ChatContext = createContext<{
  state: ChatState;
  dispatch: React.Dispatch<ChatAction>;
  sendMessage: (text: string) => Promise<void>;
  clearChat: () => void;
}>({
  state: initialState,
  dispatch: () => null,
  sendMessage: async () => {},
  clearChat: () => {},
});

// Reducer function
const chatReducer = (state: ChatState, action: ChatAction): ChatState => {
  switch (action.type) {
    case 'ADD_MESSAGE':
      const updatedMessages = [...state.messages, action.payload];
      return {
        ...state,
        messages: updatedMessages,
        conversationContext: {
          ...state.conversationContext,
          messages: updatedMessages,
        },
      };
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    case 'CLEAR_MESSAGES':
      return { 
        ...state, 
        messages: [], 
        conversationContext: { 
          messages: [],
          lastQuery: undefined,
          lastProductCriteria: undefined,
        } 
      };
    case 'UPDATE_CONVERSATION_CONTEXT':
      return {
        ...state,
        conversationContext: {
          ...state.conversationContext,
          ...action.payload,
        },
      };
    case 'LOAD_MESSAGES':
      return {
        ...state,
        messages: action.payload,
        conversationContext: {
          ...state.conversationContext,
          messages: action.payload,
        },
      };
    default:
      return state;
  }
};

// Helper function to extract product criteria from a query
const extractProductCriteria = (query: string): Partial<ConversationContext['lastProductCriteria']> => {
  const mockContext: ConversationContext = {
    messages: [
      {
        id: 'temp',
        text: query,
        sender: 'user',
        timestamp: new Date()
      }
    ]
  };
  
  // Use the LocalStorageService's more sophisticated extraction logic
  return LocalStorageService.extractProductCriteria(mockContext);
};

// Provider component
export const ChatProvider = ({ children }: { children: ReactNode }) => {
  const [state, dispatch] = useReducer(chatReducer, initialState);
  const { decrementGuestActions } = useAuth();

  // Load messages from local storage on initial render
  useEffect(() => {
    // Check if conversation is expired (7 days old)
    if (LocalStorageService.isConversationExpired(7)) {
      // Clear expired conversation data
      LocalStorageService.clearChatData();
      return;
    }
    
    // Load saved messages
    const savedMessages = LocalStorageService.loadMessages();
    if (savedMessages.length > 0) {
      dispatch({ type: 'LOAD_MESSAGES', payload: savedMessages });
    }
    
    // Load conversation context
    const savedContext = LocalStorageService.loadConversationContext();
    if (savedContext) {
      dispatch({ type: 'UPDATE_CONVERSATION_CONTEXT', payload: savedContext });
    }
  }, []);

  // Save messages to local storage whenever they change
  useEffect(() => {
    if (state.messages.length > 0) {
      LocalStorageService.saveMessages(state.messages);
      
      // Extract and enhance conversation context before saving
      const enhancedContext = {
        ...state.conversationContext,
        // Extract additional product criteria from recent messages
        lastProductCriteria: {
          ...state.conversationContext.lastProductCriteria,
          ...LocalStorageService.extractProductCriteria(state.conversationContext)
        }
      };
      
      LocalStorageService.saveConversationContext(enhancedContext);
      
      // Update the state with the enhanced context
      if (JSON.stringify(enhancedContext.lastProductCriteria) !== 
          JSON.stringify(state.conversationContext.lastProductCriteria)) {
        dispatch({ 
          type: 'UPDATE_CONVERSATION_CONTEXT', 
          payload: { lastProductCriteria: enhancedContext.lastProductCriteria } 
        });
      }
    }
  }, [state.messages]);

  // Function to clear chat history
  const clearChat = () => {
    dispatch({ type: 'CLEAR_MESSAGES' });
    LocalStorageService.clearChatData();
  };

  // Function to send a message
  const sendMessage = async (text: string) => {
    if (!text.trim()) return;

    // Clear any previous errors
    if (state.error) {
      dispatch({ type: 'SET_ERROR', payload: null });
    }

    // Track this action for guest users
    decrementGuestActions(ActionType.CHAT);

    // Create a new user message
    const userMessage: ChatMessage = {
      id: uuidv4(),
      text,
      sender: 'user',
      timestamp: new Date(),
    };

    // Add the user message to the chat
    dispatch({ type: 'ADD_MESSAGE', payload: userMessage });
    
    // Set loading state
    dispatch({ type: 'SET_LOADING', payload: true });

    // Extract product criteria from the query
    const productCriteria = extractProductCriteria(text);
    
    // Update conversation context with the new query and criteria
    dispatch({ 
      type: 'UPDATE_CONVERSATION_CONTEXT', 
      payload: { 
        lastQuery: text,
        lastProductCriteria: {
          ...state.conversationContext.lastProductCriteria,
          ...productCriteria
        }
      } 
    });

    try {
      // In a production environment, we would use the API service
      // For now, we'll use a simulated response for development
      console.log('Debug .............................', import.meta.env.PROD)
      if (!import.meta.env.PROD) {
        try {
          // Use the API service with retry logic
          const response = await ApiService.sendQueryWithRetry(text, state.messages);
          handleApiResponse(response, text);
        } catch (error) {
          console.error('API request failed after retries:', error);
          
          // Get user-friendly error message
          const errorMessage = ApiService.getErrorMessage(error);
          
          // Add an error message to the chat
          const systemMessage: ChatMessage = {
            id: uuidv4(),
            text: errorMessage,
            sender: 'system',
            timestamp: new Date(),
          };
          
          dispatch({ type: 'ADD_MESSAGE', payload: systemMessage });
          dispatch({ type: 'SET_LOADING', payload: false });
          dispatch({ type: 'SET_ERROR', payload: errorMessage });
        }
      } else {
        // Simulate API response for development
        setTimeout(() => {
          // Randomly simulate errors (10% chance)
          if (Math.random() < 0.1) {
            const errorMessage = 'Sorry, there was an error processing your request. Please try again.';
            
            const systemMessage: ChatMessage = {
              id: uuidv4(),
              text: errorMessage,
              sender: 'system',
              timestamp: new Date(),
            };
            
            dispatch({ type: 'ADD_MESSAGE', payload: systemMessage });
            dispatch({ type: 'SET_LOADING', payload: false });
            dispatch({ type: 'SET_ERROR', payload: errorMessage });
            return;
          }
          
          const mockResponse: ApiResponse = {
            query: text,
            products: text.toLowerCase().includes('phone') ? [
              {
                title: 'Redmi Note 12 Pro 5G',
                price: 11999,
                rating: 4.2,
                features: ['8GB RAM', '128GB Storage', '5G', '50MP Camera', '5000mAh Battery'],
                pros: ['Great display', 'Good camera', 'Fast charging'],
                cons: ['Average build quality', 'Bloatware'],
                link: 'https://example.com/product1'
              },
              {
                title: 'Realme 11 5G',
                price: 12499,
                rating: 4.0,
                features: ['8GB RAM', '128GB Storage', '5G', '108MP Camera', '5000mAh Battery'],
                pros: ['Excellent camera', 'Fast processor', 'Good battery life'],
                cons: ['UI needs improvement', 'Heating issues'],
                link: 'https://example.com/product2'
              },
              {
                title: 'Poco X5 Pro 5G',
                price: 11499,
                rating: 4.3,
                features: ['8GB RAM', '256GB Storage', '5G', '108MP Camera', '5000mAh Battery'],
                pros: ['Best value for money', 'Great performance', 'AMOLED display'],
                cons: ['Camera could be better', 'Plastic build'],
                link: 'https://example.com/product3'
              }
            ] : text.toLowerCase().includes('tv') ? [
              {
                title: 'Samsung Crystal 4K UHD TV',
                price: 32999,
                rating: 4.4,
                features: ['43-inch', '4K UHD', 'HDR', 'Smart TV', 'Voice Assistant'],
                pros: ['Excellent picture quality', 'Smart features', 'Value for money'],
                cons: ['Average sound', 'Limited app support'],
                link: 'https://example.com/tv1'
              },
              {
                title: 'LG 4K OLED Smart TV',
                price: 79999,
                rating: 4.7,
                features: ['55-inch', 'OLED', 'Dolby Vision', 'WebOS', 'HDMI 2.1'],
                pros: ['Superior picture quality', 'Perfect blacks', 'Gaming features'],
                cons: ['Expensive', 'Burn-in risk'],
                link: 'https://example.com/tv2'
              },
              {
                title: 'Mi Q1 QLED TV',
                price: 54999,
                rating: 4.3,
                features: ['55-inch', 'QLED', '4K UHD', 'Android TV', 'Dolby Audio'],
                pros: ['Vibrant colors', 'Sleek design', 'Good smart features'],
                cons: ['UI lag sometimes', 'Average remote'],
                link: 'https://example.com/tv3'
              }
            ] : [],
            recommendationsSummary: text.toLowerCase().includes('phone') ? 
              '• The Poco X5 Pro 5G offers the best value for money with 256GB storage at ₹11,499\n• Redmi Note 12 Pro has the best display quality in this price range\n• All options have 5G connectivity and 8GB RAM as requested' : 
              'Based on your requirements, here are the best options available.'
          };
          
          handleApiResponse(mockResponse, text);
        }, 1500);
      }
    } catch (error) {
      console.error('Unexpected error sending message:', error);
      
      // Add an error message
      const errorMessage = 'Sorry, there was an error processing your request. Please try again.';
      
      const systemMessage: ChatMessage = {
        id: uuidv4(),
        text: errorMessage,
        sender: 'system',
        timestamp: new Date(),
      };
      
      dispatch({ type: 'ADD_MESSAGE', payload: systemMessage });
      dispatch({ type: 'SET_LOADING', payload: false });
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
    }
  };

  // Helper function to handle API response
  const handleApiResponse = (response: ApiResponse, query: string) => {
    const systemMessage: ChatMessage = {
      id: uuidv4(),
      text: `Based on your query: "${query}", I've found these options:`,
      sender: 'system',
      timestamp: new Date(),
      products: response.products,
      recommendationsSummary: response.recommendationsSummary,
    };
    
    dispatch({ type: 'ADD_MESSAGE', payload: systemMessage });
    dispatch({ type: 'SET_LOADING', payload: false });
  };

  return (
    <ChatContext.Provider value={{ state, dispatch, sendMessage, clearChat }}>
      {children}
    </ChatContext.Provider>
  );
};

// Custom hook to use the chat context
export const useChatContext = () => useContext(ChatContext);