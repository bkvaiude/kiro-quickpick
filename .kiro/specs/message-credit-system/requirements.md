# Requirements Document

## Introduction

The Message Credit System & Caching Optimization feature aims to replace the current "Guest Actions" system with a more refined "Message Credits" approach, while also implementing a robust caching strategy to optimize resource usage. This feature will provide a clearer usage model for both guest and registered users, with different credit allocations and reset policies. Additionally, the caching mechanism will improve response times and reduce unnecessary API calls by storing and reusing query results for a configurable period.

## Requirements

### Requirement 1: Message Credit System Implementation

**User Story:** As a system administrator, I want to replace the "Guest Actions" system with a "Message Credits" system, so that user interactions are more clearly defined and managed.

#### Acceptance Criteria

1. WHEN the system is updated THEN the system SHALL completely remove "Guest Actions" terminology and implementation
2. WHEN referring to usage limits THEN the system SHALL use "Message Credits" terminology instead of "API Credits"
3. WHEN defining credit usage THEN the system SHALL follow the rule that 1 message equals 1 credit
4. WHEN a guest user interacts with the system THEN the system SHALL allot them a maximum of 10 credits total (one-time)
5. WHEN a guest user exhausts their credits THEN the system SHALL NOT allow them to earn or reset credits without registering
6. WHEN a registered user interacts with the system THEN the system SHALL allot them 50 credits per day
7. WHEN a new day starts THEN the system SHALL automatically reset registered users' credits
8. WHEN configuring the system THEN the system SHALL allow administrators to modify the following settings:
   - MAX_GUEST_CREDITS
   - MAX_REGISTERED_CREDITS
   - CREDIT_RESET_INTERVAL_HOURS
   - CACHE_VALIDITY_MINUTES

### Requirement 2: Credit Validation and Security

**User Story:** As a system administrator, I want credit validation to be enforced on both frontend and backend, so that the system is secure and cannot be bypassed.

#### Acceptance Criteria

1. WHEN a user has exhausted their credits THEN the system SHALL disable the input functionality on the frontend
2. WHEN a request is received by the backend THEN the system SHALL validate the user's available credits before processing
3. WHEN a user attempts to bypass frontend restrictions THEN the system SHALL reject the request if credits are exhausted
4. WHEN credit validation fails THEN the system SHALL provide a clear error message to the user

### Requirement 3: Server-Side Query Caching

**User Story:** As a system administrator, I want to implement server-side caching for product queries, so that identical queries don't consume additional credits and system resources.

#### Acceptance Criteria

1. WHEN a product query is received THEN the system SHALL generate a unique hash for the query string
2. WHEN storing a query result THEN the system SHALL associate it with the query hash and set a TTL based on CACHE_VALIDITY_MINUTES
3. WHEN an identical query is received THEN the system SHALL return the cached result if it has not expired
4. WHEN returning a cached result THEN the system SHALL NOT deduct credits from the user's balance
5. WHEN a cached result is returned THEN the system SHALL include an indicator in the response that it's a cached result

### Requirement 4: Client-Side Caching

**User Story:** As a user, I want my previous queries to be cached locally, so that I can see results faster without consuming additional credits.

#### Acceptance Criteria

1. WHEN a query result is received THEN the system SHALL store it in local storage with the query string as the key
2. WHEN a user submits a query THEN the system SHALL check if an unexpired cached result exists
3. WHEN using a cached result THEN the system SHALL display an indicator that it's a cached result
4. WHEN displaying a cached result THEN the system SHALL provide an option to refresh the result (consuming a credit)
5. WHEN the cache validity period expires THEN the system SHALL remove the cached result

### Requirement 5: Frontend UX Updates

**User Story:** As a user, I want a clear and intuitive interface that shows my credit usage and cached results, so that I can manage my interactions efficiently.

#### Acceptance Criteria

1. WHEN the header is displayed THEN the system SHALL show "Message Credits" instead of "Guest Actions"
2. WHEN a user has no credits left THEN the system SHALL display a helpful marketing message
3. WHEN a guest user has low credits THEN the system SHALL encourage registration
4. WHEN displaying cached results THEN the system SHALL highlight them with a "(cached)" tag or badge
5. WHEN a cached result is displayed THEN the system SHALL provide a refresh button to get updated results