# Requirements Document

## Introduction

The AI-Powered Shopping Assistant is a web application that helps Indian users find products that match their requirements through natural language queries. The application will use AI models (Gemini API) to process user queries, extract relevant product information, and present a structured comparison of top product options with affiliate links. This MVP aims to be developed within a one-day sprint using React for the frontend and FastAPI for the backend.

## Requirements

### Requirement 1: Natural Language Query Interface

**User Story:** As an Indian online shopper, I want to search for products using natural language queries, so that I can find products matching my specific requirements without having to navigate through multiple filters.

#### Acceptance Criteria

1. WHEN a user visits the application THEN the system SHALL display a chat input box for entering natural language queries.
2. WHEN a user views the chat input THEN the system SHALL display example queries below the input box.
3. WHEN a user enters a query like "Tell me the best 5G phone under ₹12,000 with 8GB RAM from Amazon India" THEN the system SHALL accept and process the query.
4. WHEN a user submits a query THEN the system SHALL display a loading indicator while processing.

### Requirement 2: AI-Powered Product Recommendations

**User Story:** As a user, I want the system to analyze my query and provide relevant product recommendations, so that I can quickly find the best products matching my criteria.

#### Acceptance Criteria

1. WHEN a user submits a query THEN the system SHALL send the query to an AI model (Gemini API).
2. WHEN the system processes a query THEN the system SHALL extract structured product information including title, price, rating, features, pros, cons, and link.
3. WHEN the AI model processes a query THEN the system SHALL return the top 3 product options in JSON format.
4. WHEN the AI model generates product recommendations THEN the system SHALL include a recommendations summary highlighting the best product and deals.
5. WHEN the system receives the AI response THEN the system SHALL parse the JSON response correctly.
6. IF the AI model fails to process the query THEN the system SHALL display an appropriate error message.

### Requirement 3: Product Comparison Interface

**User Story:** As a user, I want to see a visual comparison of recommended products, so that I can easily evaluate and choose the best option.

#### Acceptance Criteria

1. WHEN the system receives product recommendations THEN the system SHALL display them in a card or table view.
2. WHEN displaying product recommendations THEN the system SHALL show product title, price, rating, features, pros, and cons for each product.
3. WHEN displaying product recommendations THEN the system SHALL include "Buy Now" buttons with affiliate links.
4. WHEN displaying product recommendations THEN the system SHALL ensure the comparison UI is responsive across different device sizes.
5. WHEN displaying product comparisons THEN the system SHALL highlight the best value options (e.g., lowest price, highest rating).
6. WHEN viewing on mobile devices THEN the system SHALL provide a floating "View History" button to access the collapsed sidebar.

### Requirement 4: Affiliate Link Integration

**User Story:** As the product owner, I want all product links to include affiliate tags, so that the application can generate revenue through affiliate commissions.

#### Acceptance Criteria

1. WHEN generating product links THEN the system SHALL embed affiliate tags in all Amazon/Flipkart links.
2. WHEN configuring the application THEN the system SHALL allow dynamic affiliate tagging from environment variables.

### Requirement 5: Contextual Chat Session

**User Story:** As a user, I want the application to maintain context of my previous queries, so that I can refine my search without repeating information (e.g., asking about "5G phone with 8GB RAM" and then following up with "under ₹20k").

#### Acceptance Criteria

1. WHEN a user submits follow-up queries THEN the system SHALL maintain conversation context for up to 10 messages.
2. WHEN processing user queries THEN the system SHALL include previous conversation context when sending requests to the AI model.
3. WHEN storing conversation history THEN the system SHALL use client-side storage (local/session storage).
4. WHEN a user refers to previous criteria in a new query THEN the system SHALL correctly interpret the query in the context of the conversation history.
5. WHEN a user clicks on a previous query in the chat history THEN the system SHALL load the associated product comparison and scroll to it.
6. WHEN displaying the chat history THEN the system SHALL show timestamps for each query.

### Requirement 6: Deployment and Hosting

**User Story:** As a product owner, I want the application to be deployed and accessible online, so that users can access it from anywhere.

#### Acceptance Criteria

1. WHEN the MVP is complete THEN the system SHALL be deployable to Vercel (for React frontend) and a suitable platform for FastAPI backend.
2. WHEN deploying the application THEN the system SHALL securely handle API keys and environment variables.
### Requirement 7: Enhanced UI/UX Layout

**User Story:** As a user, I want a well-structured and intuitive interface that makes it easy to interact with the shopping assistant and view product comparisons, so that I can have a seamless shopping experience.

#### Acceptance Criteria

1. WHEN a user accesses the application THEN the system SHALL display a structured layout with header, two-panel content area (left for chat, right for products), and footer sections.
2. WHEN the application loads THEN the system SHALL display a header with logo, app title, theme toggle, and API credits display.
3. WHEN using the application THEN the system SHALL display the chat interface in the left panel and product results in the right panel.
4. WHEN no products are found THEN the system SHALL display a marketing message or helpful suggestions in the right panel.
5. WHEN viewing product comparisons THEN the system SHALL provide a comparison matrix view with best value highlighting.
6. WHEN typing in the input field THEN the system SHALL suggest example prompts dynamically.
7. WHEN the application is loading data THEN the system SHALL display appropriate skeleton loaders.
8. WHEN an error occurs THEN the system SHALL display a friendly fallback message with retry option.
9. WHEN the user changes the theme THEN the system SHALL persist the theme preference.
10. WHEN the application loads THEN the system SHALL restore previous chat history from localStorage if available.
11. WHEN using the application on mobile devices THEN the system SHALL adapt the two-panel layout to a stacked layout for better mobile experience.