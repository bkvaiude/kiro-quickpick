# Requirements Document

## Introduction

This document outlines the requirements for implementing Auth0 authentication and guest access limits in the AI Shopping Assistant application. The feature will introduce a distinction between guest and registered users, with guests having limited access to encourage sign-ups. Authentication will be handled through Auth0, and JWT validation will be implemented for all protected endpoints.

## Requirements

### Requirement 1: Auth0 Integration

**User Story:** As a user, I want to be able to register and log in using Auth0 authentication, so that I can access the full functionality of the AI Shopping Assistant.

#### Acceptance Criteria

1. WHEN a user clicks on the login button THEN the system SHALL redirect them to the Auth0 Universal Login page.
2. WHEN a user completes the Auth0 login process THEN the system SHALL receive and store the JWT token.
3. WHEN a user logs in via Auth0 THEN the system SHALL support authentication via email or phone number.
4. WHEN a user successfully authenticates THEN the system SHALL store the authentication token securely.
5. WHEN a user's token expires THEN the system SHALL prompt the user to re-authenticate.

### Requirement 2: Guest Access Limitations

**User Story:** As a product owner, I want to limit guest users to 10 total actions (chat + search), so that they are encouraged to register for full access.

#### Acceptance Criteria

1. WHEN a guest user accesses the application THEN the system SHALL allow them to perform up to 10 combined chat and search actions.
2. WHEN a guest user reaches the 10-action limit THEN the system SHALL display a login prompt.
3. WHEN a guest user reaches the 10-action limit THEN the system SHALL disable further inputs until the user registers.
4. WHEN a guest user attempts to perform actions beyond the limit THEN the system SHALL reject API calls with a "login required" message.
5. WHEN the system tracks guest usage THEN it SHALL count both chat messages and search queries toward the 10-action limit.

### Requirement 3: JWT Validation

**User Story:** As a system administrator, I want all protected endpoints to validate JWT tokens, so that only authenticated users can access restricted functionality.

#### Acceptance Criteria

1. WHEN a request is made to a protected endpoint THEN the system SHALL validate the JWT token.
2. WHEN a request contains a valid JWT token THEN the system SHALL process the request normally.
3. WHEN a request contains an invalid or expired JWT token THEN the system SHALL return an authentication error.
4. WHEN a guest user exceeds their usage limit THEN the system SHALL require a valid JWT token for further requests.
5. WHEN validating a JWT token THEN the system SHALL verify the token signature, expiration, and issuer.

### Requirement 4: User Consent Collection

**User Story:** As a business owner, I want to collect user consent for terms of service and marketing communications during registration, so that we comply with regulations and can send marketing updates.

#### Acceptance Criteria

1. WHEN a user registers THEN the system SHALL require acceptance of Terms of Use and Privacy Policy.
2. WHEN a user registers THEN the system SHALL provide an optional checkbox for marketing consent.
3. WHEN a user provides marketing consent THEN the system SHALL store this preference.
4. WHEN a user completes registration THEN the system SHALL record the timestamp and details of all consents provided.
5. WHEN displaying the registration form THEN the system SHALL clearly distinguish between required and optional consent items.

### Requirement 5: UI State Management

**User Story:** As a user, I want the UI to clearly reflect my authentication state and remaining guest actions, so that I understand my current limitations and options.

#### Acceptance Criteria

1. WHEN a guest user is using the application THEN the system SHALL display the number of remaining actions (optional).
2. WHEN a guest user reaches the action limit THEN the system SHALL display a modal explaining the benefits of registration.
3. WHEN a guest user reaches the action limit THEN the system SHALL disable chat and search input fields.
4. WHEN a user successfully logs in THEN the system SHALL restore full access to all features.
5. WHEN a user successfully logs in THEN the system SHALL display a welcome message.
6. WHEN a user is authenticated THEN the system SHALL display their authentication status.