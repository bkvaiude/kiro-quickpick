# Requirements Document

## Introduction

This document outlines the requirements for refactoring the authentication services in the AI Shopping Assistant application. The current implementation has duplicate logic between `authStateService.ts` and `authService.ts`, improper token handling that conflicts with Auth0's SDK, and architectural issues with using React hooks in service files. This refactoring will consolidate the services, properly integrate with the Auth0 SDK, and create a clean dependency injection pattern.

## Requirements

### Requirement 1: Service Consolidation

**User Story:** As a developer, I want a single unified authentication service instead of duplicate services, so that I can maintain consistent authentication logic without code duplication.

#### Acceptance Criteria

1. WHEN the refactoring is complete THEN the system SHALL have only one authentication service file.
2. WHEN consolidating services THEN the system SHALL preserve all existing functionality from both `authService.ts` and `authStateService.ts`.
3. WHEN the unified service is created THEN it SHALL eliminate all duplicate logic between the two services.
4. WHEN removing duplicate services THEN the system SHALL update all import statements to use the new unified service.
5. WHEN consolidating services THEN the system SHALL maintain backward compatibility for all existing method signatures used by dependent services.

### Requirement 2: Proper Auth0 SDK Integration

**User Story:** As a developer, I want the authentication service to properly use the Auth0 SDK instead of manual token handling, so that authentication is secure and follows Auth0 best practices.

#### Acceptance Criteria

1. WHEN accessing authentication tokens THEN the system SHALL use Auth0's `getAccessTokenSilently()` method instead of manual localStorage access.
2. WHEN checking authentication status THEN the system SHALL use Auth0's `isAuthenticated` property instead of custom token validation.
3. WHEN handling user information THEN the system SHALL use Auth0's `user` object instead of manually parsing stored data.
4. WHEN performing login operations THEN the system SHALL use Auth0's `loginWithRedirect()` method.
5. WHEN performing logout operations THEN the system SHALL use Auth0's `logout()` method.
6. WHEN the service needs Auth0 context THEN it SHALL receive it via dependency injection rather than direct hook usage.

### Requirement 3: Dependency Injection Architecture

**User Story:** As a developer, I want the authentication service to receive Auth0 context through dependency injection, so that it can be used in both React components and service files without architectural violations.

#### Acceptance Criteria

1. WHEN creating the authentication service THEN it SHALL accept Auth0 context as a parameter through a factory function.
2. WHEN components need the authentication service THEN they SHALL pass the result of `useAuth0()` to the service factory.
3. WHEN service files need authentication THEN they SHALL receive the configured authentication service as a parameter.
4. WHEN the service is instantiated THEN it SHALL provide wrapper methods that delegate to the Auth0 context.
5. WHEN using the service THEN it SHALL not directly import or use React hooks.

### Requirement 4: API Service Integration

**User Story:** As a developer, I want the API service to use the refactored authentication service, so that API calls have proper authentication headers without manual token handling.

#### Acceptance Criteria

1. WHEN making API requests THEN the API service SHALL use the refactored authentication service to get tokens.
2. WHEN API service needs authentication headers THEN it SHALL call the authentication service's `getAccessToken()` method.
3. WHEN API service checks authentication status THEN it SHALL use the authentication service's `isAuthenticated()` method.
4. WHEN API service handles authentication errors THEN it SHALL use the authentication service's error handling methods.
5. WHEN the API service is updated THEN it SHALL no longer directly access localStorage for authentication data.

### Requirement 5: Credit Service Integration

**User Story:** As a developer, I want the credit service to use the refactored authentication service, so that credit operations have proper authentication without manual token handling.

#### Acceptance Criteria

1. WHEN the credit service makes authenticated requests THEN it SHALL use the refactored authentication service for tokens.
2. WHEN the credit service checks user authentication THEN it SHALL use the authentication service's methods.
3. WHEN the credit service needs authentication headers THEN it SHALL delegate to the authentication service.
4. WHEN the credit service is updated THEN it SHALL no longer directly access AuthService methods that manually handle tokens.
5. WHEN credit operations fail due to authentication THEN the service SHALL use the authentication service's error handling.

### Requirement 6: Guest User Functionality Preservation

**User Story:** As a user, I want all existing guest user functionality to continue working after the refactoring, so that the user experience remains unchanged.

#### Acceptance Criteria

1. WHEN guest users access the application THEN all existing guest credit tracking SHALL continue to function.
2. WHEN guest users reach credit limits THEN the existing limit enforcement SHALL continue to work.
3. WHEN guest users interact with the UI THEN all existing guest-specific UI states SHALL be preserved.
4. WHEN the refactoring is complete THEN guest user consent management SHALL continue to function.
5. WHEN guest users perform actions THEN the existing action tracking SHALL continue to work without changes.

### Requirement 7: Testing Compatibility

**User Story:** As a developer, I want all existing tests to continue working after the refactoring, so that the test suite remains comprehensive and functional.

#### Acceptance Criteria

1. WHEN the refactoring is complete THEN all existing authentication-related tests SHALL pass without modification.
2. WHEN tests need the authentication service THEN they SHALL be able to mock the new unified service.
3. WHEN integration tests run THEN they SHALL work with the new dependency injection pattern.
4. WHEN unit tests access authentication functionality THEN they SHALL use the new service interface.
5. WHEN the refactoring is complete THEN test coverage SHALL not decrease from the current level.