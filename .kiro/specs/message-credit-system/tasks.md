# Implementation Plan

- [x] 1. Set up configuration system for message credits
  - Create configuration constants for credit limits and cache settings
  - Implement environment variable overrides
  - _Requirements: 1.8_

- [x] 2. Implement backend credit management system
  - [x] 2.1 Create credit management service
    - Implement credit tracking for guest and registered users
    - Add methods for checking, deducting, and resetting credits
    - _Requirements: 1.3, 1.4, 1.6_
  
  - [x] 2.2 Implement credit reset mechanism
    - Create scheduled job for resetting registered user credits
    - Implement daily credit reset logic
    - _Requirements: 1.7_
  
  - [x] 2.3 Implement credit validation middleware
    - Create middleware to check credit availability before processing requests
    - Add proper error responses for credit exhaustion
    - _Requirements: 2.2, 2.3, 2.4_

- [x] 3. Implement server-side query caching
  - [x] 3.1 Create query hash generation utility
    - Implement function to generate consistent hashes from query strings
    - Add tests for hash generation
    - _Requirements: 3.1_
  
  - [x] 3.2 Implement cache storage and retrieval
    - Create service for storing query results with TTL
    - Implement cache lookup before query processing
    - Add cache hit/miss tracking
    - _Requirements: 3.2, 3.3_
  
  - [x] 3.3 Modify query processing flow
    - Update query endpoint to check cache before processing
    - Skip credit deduction for cached results
    - Add cache indicator to response
    - _Requirements: 3.4, 3.5_

- [x] 4. Implement frontend credit management
  - [x] 4.1 Create credit display component
    - Replace "Guest Actions" with "Message Credits" in UI
    - Show appropriate credit information based on user type
    - _Requirements: 5.1_
  
  - [x] 4.2 Implement credit-aware input handling
    - Disable input when credits are exhausted
    - Show appropriate messages for low/no credits
    - Add registration prompts for guests with low credits
    - _Requirements: 2.1, 5.2, 5.3_

- [x] 5. Implement client-side caching
  - [x] 5.1 Create client-side cache manager
    - Implement local storage-based cache with TTL
    - Add cache lookup before sending queries
    - Implement cache expiration logic
    - _Requirements: 4.1, 4.2, 4.5_
  
  - [x] 5.2 Update UI for cached results
    - Add cache indicators to query results
    - Implement refresh button for cached results
    - _Requirements: 4.3, 4.4, 5.4, 5.5_

- [x] 6. Update API endpoints
  - [x] 6.1 Modify user endpoints
    - Update user model to include credit information
    - Add endpoints for checking credit balance
    - _Requirements: 1.4, 1.6_
  
  - [x] 6.2 Update query endpoint
    - Integrate with credit system and caching
    - Add cache status to response
    - _Requirements: 3.5_

- [-] 7. Write comprehensive tests
  - [x] 7.1 Write unit tests for credit management
    - Test credit allocation, deduction, and reset
    - Test different user types (guest vs registered)
    - _Requirements: 1.4, 1.5, 1.6, 1.7_
  
  - [x] 7.2 Write unit tests for caching mechanisms
    - Test cache hit/miss scenarios
    - Test cache expiration
    - _Requirements: 3.3, 3.4, 4.2, 4.5_
  
  - [x] 7.3 Write integration tests
    - Test end-to-end credit flow
    - Test caching across frontend and backend
    - _Requirements: 2.3, 3.5, 4.3, 4.4_

- [x] 8. Fix mobile view user avatar dropdown issue
  - Fix user avatar dropdown menu not working properly on mobile devices
  - Ensure profile navigation works correctly on mobile screens
  - Test dropdown positioning and touch interactions on mobile
  - _Bug Fix: Mobile UI Issue_

- [ ] 9. Remove legacy "Guest Actions" code
  - Identify and remove all references to "Guest Actions"
  - Update documentation to reflect new terminology
  - _Requirements: 1.1, 1.2_