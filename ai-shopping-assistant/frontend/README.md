# AI Shopping Assistant Frontend

This is the frontend application for the AI Shopping Assistant, built with React, TypeScript, and Vite. It provides a user-friendly interface for interacting with the AI-powered shopping assistant.

## Features

- **Natural Language Query Interface**: Intuitive chat interface for product searches
- **AI-Powered Product Recommendations**: Display of AI-generated product suggestions
- **Product Comparison Interface**: Side-by-side comparison of recommended products
- **Contextual Chat Session**: Conversation history with context awareness
- **Responsive Design**: Works on desktop and mobile devices
- **Affiliate Link Integration**: Product links with affiliate tags

## Project Structure

```
frontend/
├── public/
├── src/
│   ├── assets/
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatHistory.tsx
│   │   │   ├── ChatInput.tsx
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── ChatMessage.tsx
│   │   │   ├── ExampleQueries.tsx
│   │   │   └── LoadingIndicator.tsx
│   │   ├── layout/
│   │   ├── product/
│   │   │   ├── ProductComparisonContainer.tsx
│   │   │   └── RecommendationsSummary.tsx
│   │   ├── theme/
│   │   └── ui/
│   ├── context/
│   │   └── ChatContext.tsx
│   ├── lib/
│   │   └── utils.ts
│   ├── services/
│   │   ├── api.ts
│   │   └── localStorage.ts
│   ├── tests/
│   ├── types/
│   │   └── chat.ts
│   ├── App.tsx
│   ├── config.ts
│   └── main.tsx
├── .env
├── .env.example
├── .env.production
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## Prerequisites

- Node.js 18+ and npm
- Access to the backend API

## Development Setup

1. Clone the repository
2. Navigate to the frontend directory:
   ```bash
   cd ai-shopping-assistant/frontend
   ```
3. Install dependencies:
   ```bash
   npm install
   ```
4. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```
5. Edit the `.env` file with your development settings:
   ```
   VITE_API_BASE_URL=http://localhost:8000/api
   VITE_ENABLE_ANALYTICS=false
   ```
6. Start the development server:
   ```bash
   npm run dev
   ```
7. The application will be available at `http://localhost:5173`

## Key Components

### Chat Components

- **ChatInterface**: Main component that orchestrates the chat experience
- **ChatInput**: Component for user query input
- **ChatHistory**: Component for displaying conversation history
- **ChatMessage**: Component for rendering individual chat messages
- **ExampleQueries**: Component for displaying example queries
- **LoadingIndicator**: Visual feedback during API calls

### Product Components

- **ProductComparisonContainer**: Container for product comparison display
- **RecommendationsSummary**: Component for displaying AI-generated recommendations summary

### Services

- **ApiService**: Service for communicating with the backend API
- **LocalStorageService**: Service for persisting chat history

## Testing

The application includes unit tests and end-to-end tests:

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

## Building for Production

```bash
# Build the application
npm run build

# Preview the production build locally
npm run preview
```

## Deployment Options

### Option 1: Using the Deployment Script

The repository includes a deployment script for Vercel:

```bash
# Make the script executable
chmod +x deploy.sh

# Run the deployment script
./deploy.sh
```

### Option 2: Manual Deployment

```bash
# Install dependencies
npm ci

# Build for production
npm run build

# The build artifacts will be in the 'dist' directory
```

### Option 3: Vercel Deployment

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy to Vercel
vercel --prod
```

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| VITE_API_BASE_URL | URL of the backend API | http://localhost:8000/api | Yes |
| VITE_ENABLE_ANALYTICS | Enable analytics | false | No |

These can be set in the `.env.production` file or directly in your hosting provider's environment configuration.

## API Integration

The frontend communicates with the backend API using the ApiService. The main endpoint used is:

- `POST /api/query`: Send a user query and receive product recommendations

The API service includes:
- Error handling with retry logic
- Timeout handling
- User-friendly error messages

## Local Storage

The application uses local storage to persist:
- Chat history
- User preferences
- Conversation context

## Troubleshooting

### Common Issues

1. **API Connection Issues**: Ensure the backend API is running and the `VITE_API_BASE_URL` is correctly set.
2. **Build Errors**: Make sure all dependencies are installed with `npm install`.
3. **Test Failures**: Check that the backend API is mocked correctly in tests.

### Development Tips

- Use the React DevTools extension for debugging
- Check the browser console for errors
- Use the Network tab to inspect API requests

## Code Style and Linting

The project uses ESLint and Prettier for code quality:

```bash
# Run linting
npm run lint

# Fix linting issues
npm run lint:fix
```

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default tseslint.config([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      ...tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      ...tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      ...tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules.