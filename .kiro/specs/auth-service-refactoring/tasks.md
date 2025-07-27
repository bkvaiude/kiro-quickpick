# Implementation Plan

- [ ] 1. Create new unified authentication service structure
  - Create new auth service directory structure with factory pattern
  - Implement type definitions and error classes for the new service
  - _Requirements: 1.1, 1.3_

- [ ] 1.1 Create auth service types and error definitions
  - Create authTypes.ts with all preserved interfaces and new service types
  - Implement AuthError class with proper error codes and handling
  - _Requirements: 1.5, 7.4_

- [ ] 1.2 Implement createAuthService factory function
  - Create factory function that accepts Auth0 context and returns service instance
  - Implement all authentication methods using Auth0 SDK instead of manual token handling
  - Preserve all existing guest user functionality from original services
  - _Requirements: 2.1, 2.2, 2.3, 2.6, 3.1, 3.2, 3.4, 6.1, 6.4_

- [ ] 1.3 Add consent management and navigation helpers
  - Implement consent management methods using existing ConsentService
  - Add navigation helper methods for return path handling
  - _Requirements: 6.4, 1.2_

- [ ] 2. Update API service to use new authentication service
  - Modify API service to accept auth service instance through dependency injection
  - Update all authentication-related methods to use new service interface
  - _Requirements: 4.1, 4.2, 4.3, 4.5_

- [ ] 2.1 Refactor API service constructor and authentication methods
  - Update ApiService to accept AuthServiceInstance in constructor
  - Modify getAuthHeaders method to use auth service's getAccessToken
  - Update authentication error handling to use auth service methods
  - _Requirements: 4.1, 4.2, 4.4_

- [ ] 2.2 Create API service factory function
  - Implement createApiService factory that accepts auth service instance
  - Update all API service method calls to use injected auth service
  - _Requirements: 4.1, 3.3_

- [ ] 3. Update credit service to use new authentication service
  - Modify credit service to use new auth service for authentication
  - Update all token handling to use auth service methods
  - _Requirements: 5.1, 5.2, 5.3, 5.5_

- [ ] 3.1 Refactor credit service authentication methods
  - Update CreditService.getAuthHeaders to use auth service instance
  - Modify credit service to accept auth service through dependency injection
  - Remove direct AuthService imports and localStorage access
  - _Requirements: 5.1, 5.2, 5.4_

- [ ] 3.2 Create credit service factory function
  - Implement createCreditService factory that accepts auth service instance
  - Update credit service error handling to use auth service methods
  - _Requirements: 5.3, 5.5_

- [ ] 4. Create service integration utilities and hooks
  - Implement useAuthService hook for components to create auth service instances
  - Create service composition utilities for managing multiple service dependencies
  - _Requirements: 3.1, 3.2, 3.3_

- [ ] 4.1 Implement useAuthService hook
  - Create React hook that uses useAuth0 and returns configured auth service
  - Add memoization to prevent unnecessary service recreation
  - _Requirements: 3.2, 3.4_

- [ ] 4.2 Create service composition utilities
  - Implement utilities for creating multiple services with shared auth service
  - Add helper functions for service dependency management
  - _Requirements: 3.3, 3.4_

- [ ] 5. Update existing components to use new service pattern
  - Update components that directly import old auth services
  - Modify components to use factory pattern with dependency injection
  - _Requirements: 1.4, 3.2, 3.3_

- [ ] 5.1 Update AuthContext and related components
  - Modify AuthContext to use new auth service factory
  - Update components that consume AuthContext to use new service interface
  - _Requirements: 1.4, 1.5_

- [ ] 5.2 Update API and credit service consumers
  - Modify components that use API service to use new factory pattern
  - Update components that use credit service to use new factory pattern
  - _Requirements: 3.2, 3.3_

- [ ] 6. Update and create comprehensive tests
  - Create unit tests for new auth service factory and methods
  - Update existing tests to work with new service architecture
  - _Requirements: 7.1, 7.2, 7.4, 7.5_

- [ ] 6.1 Create unit tests for auth service factory
  - Test createAuthService factory with mocked Auth0 context
  - Test all authentication methods and error handling scenarios
  - Test guest user functionality preservation
  - _Requirements: 7.1, 7.4, 6.1, 6.2, 6.3_

- [ ] 6.2 Update integration tests for service dependencies
  - Update API service tests to work with new dependency injection pattern
  - Update credit service tests to work with new auth service integration
  - Test service factory composition and dependency management
  - _Requirements: 7.2, 7.3_

- [ ] 6.3 Create migration compatibility tests
  - Test that all existing method signatures continue to work
  - Verify that existing test mocks are compatible with new service
  - Test backward compatibility for all preserved functionality
  - _Requirements: 7.1, 7.5, 1.5_

- [ ] 7. Remove old authentication services and clean up imports
  - Delete authStateService.ts file after verifying all functionality is preserved
  - Clean up authService.ts and update all import statements
  - _Requirements: 1.1, 1.4_

- [ ] 7.1 Remove authStateService.ts and update imports
  - Delete authStateService.ts file completely
  - Update all files that import authStateService to use new auth service
  - Verify no functionality is lost in the migration
  - _Requirements: 1.1, 1.4_

- [ ] 7.2 Clean up authService.ts and finalize migration
  - Remove duplicate functionality from authService.ts that's now in new service
  - Keep only necessary type exports if needed for backward compatibility
  - Update all remaining import statements to use new service structure
  - _Requirements: 1.1, 1.4, 1.5_

- [ ] 8. Verify guest user functionality preservation
  - Test all guest user credit tracking functionality
  - Verify guest limit enforcement continues to work
  - Test guest user UI states and consent management
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 8.1 Test guest credit tracking and limits
  - Verify guest credit counting works with new service architecture
  - Test guest limit enforcement in UI components
  - Test guest action tracking integration with new auth service
  - _Requirements: 6.1, 6.2, 6.5_

- [ ] 8.2 Test guest UI states and consent functionality
  - Verify guest-specific UI components work with new service
  - Test consent management functionality preservation
  - Test guest user experience flows end-to-end
  - _Requirements: 6.3, 6.4_