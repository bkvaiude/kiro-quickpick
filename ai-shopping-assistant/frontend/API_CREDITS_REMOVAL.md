# API Credits Component Removal

## Overview
Removed the redundant `ApiCredits` component from the header since we now have a proper `MessageCreditDisplay` component that handles credit tracking more comprehensively.

## Changes Made

### 1. Removed Files
- **`src/components/layout/ApiCredits.tsx`** - Deleted the entire component file

### 2. Updated Files

#### `src/components/layout/Layout.tsx`
- Removed import: `import { ApiCredits } from "./ApiCredits";`
- Removed component usage: `<ApiCredits />` from the header
- Header now shows only: MessageCreditDisplay, ThemeToggle, and UserProfile/LoginButton

#### `src/components/layout/Layout.test.tsx`
- Removed ApiCredits mock: `vi.mock('./ApiCredits', ...)`
- Removed test: "renders the API credits in the header"
- Added MessageCreditDisplay mock and test
- Added auth component mocks for complete test coverage

## Why This Change Was Needed

### Problems with ApiCredits Component:
1. **Redundancy**: Both ApiCredits and MessageCreditDisplay were showing credit information
2. **Inconsistency**: ApiCredits used a simple message count, while MessageCreditDisplay uses proper backend integration
3. **User Confusion**: Having two credit displays was confusing for users
4. **Maintenance Overhead**: Two components doing similar things increased complexity

### Benefits of Removal:
1. **Cleaner UI**: Single, clear credit display in the header
2. **Consistency**: All credit logic now goes through the proper MessageCreditDisplay component
3. **Better UX**: Users see one authoritative credit count
4. **Simplified Codebase**: Less code to maintain and test

## MessageCreditDisplay vs ApiCredits Comparison

### Old ApiCredits Component:
- Simple message count based on chat context
- Hardcoded 10 credit limit
- Basic color coding (red/yellow/green)
- No backend integration
- Mock implementation

### Current MessageCreditDisplay Component:
- Proper backend integration
- Real-time credit tracking
- Handles authenticated and guest users
- Integrates with the credit system architecture
- Shows actual remaining credits from the API

## Header Layout After Changes

The header now contains (left to right):
1. **Logo & Title**: "AI Shopping Assistant"
2. **Right Side Controls**:
   - MessageCreditDisplay (shows current credits)
   - ThemeToggle (dark/light mode)
   - UserProfile (if authenticated) OR LoginButton (if not authenticated)

## Testing
- All existing Layout tests updated and passing
- Removed ApiCredits-specific tests
- Added proper MessageCreditDisplay test coverage
- No functionality lost, only redundancy removed

## Impact
- **Users**: Cleaner, less confusing interface
- **Developers**: Simpler codebase with single source of truth for credits
- **Maintenance**: Fewer components to maintain and update
- **Performance**: Slightly reduced bundle size and render complexity