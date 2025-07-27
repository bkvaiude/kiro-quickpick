# Project Structure

## Root Organization
```
ai-shopping-assistant/
├── frontend/           # React TypeScript frontend
├── backend/            # FastAPI Python backend
├── README.md          # Main project documentation
└── verify_deployment.sh
```

## Frontend Structure (`ai-shopping-assistant/frontend/`)
```
frontend/
├── src/
│   ├── components/     # React components organized by feature
│   │   ├── auth/      # Authentication components
│   │   ├── chat/      # Chat interface components
│   │   ├── credit/    # Credit system components
│   │   ├── layout/    # Layout components
│   │   ├── product/   # Product display components
│   │   ├── profile/   # User profile components
│   │   ├── theme/     # Theme and styling components
│   │   └── ui/        # Reusable UI primitives
│   ├── auth/          # Auth0 integration and context
│   ├── context/       # React context providers
│   ├── hooks/         # Custom React hooks
│   ├── services/      # API and external service integrations
│   ├── types/         # TypeScript type definitions
│   ├── utils/         # Utility functions and helpers
│   ├── tests/         # Integration and E2E tests
│   └── styles/        # Global styles and CSS
├── public/            # Static assets
├── dist/              # Build output (generated)
└── node_modules/      # Dependencies (generated)
```

## Backend Structure (`ai-shopping-assistant/backend/`)
```
backend/
├── app/
│   ├── api/
│   │   ├── endpoints/ # API route handlers
│   │   └── router.py  # API routing configuration
│   ├── middleware/    # FastAPI middleware
│   ├── models/        # Pydantic data models
│   ├── services/      # Business logic and external integrations
│   ├── config.py      # Application configuration
│   └── main.py        # FastAPI application setup
├── tests/             # Integration and E2E tests
├── venv/              # Virtual environment (generated)
└── pitshop-shop-ai/   # Additional project files
```

## Key Architectural Patterns

### Frontend Patterns
- **Component Organization**: Features grouped by domain (auth, chat, product)
- **Service Layer**: Separate services for API calls, auth, and data management
- **Context Providers**: React Context for global state (auth, chat)
- **Custom Hooks**: Reusable logic abstracted into hooks
- **UI Components**: Radix UI primitives with custom styling

### Backend Patterns
- **Layered Architecture**: API → Services → Models
- **Dependency Injection**: FastAPI's built-in DI for services
- **Service Layer**: Business logic separated from API handlers
- **Configuration Management**: Centralized config with environment variables
- **Middleware**: Cross-cutting concerns (auth, credits, error handling)

## File Naming Conventions
- **Frontend**: PascalCase for components (`ChatInterface.tsx`), camelCase for utilities
- **Backend**: snake_case for Python files (`gemini_service.py`)
- **Tests**: Prefix with `test_` for backend, suffix with `.test.tsx` for frontend

## Import Patterns
- **Frontend**: Absolute imports using `@/` alias for src directory
- **Backend**: Relative imports within app, absolute for external packages
- **Barrel Exports**: `__init__.py` and `index.ts` files for clean imports

## Environment Files
- `.env.example` - Template with all required variables
- `.env` - Local development configuration
- `.env.production` - Production deployment configuration

## Documentation Files
- Component-level: Inline JSDoc/docstrings
- API: `API_DOCUMENTATION.md` in backend
- Feature-specific: Markdown files for major features
- Deployment: README files in each directory