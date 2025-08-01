# AI Shopping Assistant

An AI-powered shopping assistant that helps Indian users find products through natural language queries. The application uses the Gemini API to process user queries, extract relevant product information, and present a structured comparison of top product options with affiliate links.

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/ai-shopping-assistant.git
   cd ai-shopping-assistant
   ```

2. **Set up the backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your API keys
   python run.py
   ```

3. **Set up the frontend**
   ```bash
   cd ../frontend
   npm install
   cp .env.example .env
   # Edit .env with your settings
   npm run dev
   ```

4. **Open your browser** to `http://localhost:5173`

## Features

- **Natural Language Queries**: Search for products using conversational language
- **AI-Powered Recommendations**: Get personalized product suggestions based on your criteria
- **Product Comparison**: View side-by-side comparisons of recommended products
- **Contextual Conversations**: Refine your search without repeating information
- **Affiliate Integration**: All product links include affiliate tags for revenue generation

## Project Structure

- `frontend/`: React frontend application with TypeScript and Vite
- `backend/`: FastAPI backend application with Python

## Setup Instructions

### Prerequisites

- Node.js 18+ and npm for frontend development
- Python 3.9+ for backend development
- Docker (optional, for containerized deployment)
- Gemini API key (obtain from [Google AI Studio](https://ai.google.dev/))
- Affiliate program account (e.g., Amazon Associates)

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd ai-shopping-assistant/frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```

4. Edit the `.env` file with your development settings:
   ```
   VITE_API_BASE_URL=http://localhost:8000/api
   VITE_ENABLE_ANALYTICS=false
   ```

5. Start the development server:
   ```bash
   npm run dev
   ```

6. The frontend will be available at `http://localhost:5173`

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd ai-shopping-assistant/backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```

5. Edit the `.env` file with your development settings:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   AFFILIATE_TAG=your_affiliate_tag_here
   AFFILIATE_PROGRAM=amazon
   API_HOST=0.0.0.0
   API_PORT=8000
   DEBUG=True
   LOG_LEVEL=DEBUG
   WORKERS=1
   ALLOWED_HOSTS=localhost
   FRONTEND_URL=http://localhost:5173
   ```

6. Start the development server:
   ```bash
   python run.py
   ```

7. The backend API will be available at `http://localhost:8000`
   - API documentation: `http://localhost:8000/docs` (only in debug mode)
   - ReDoc: `http://localhost:8000/redoc` (only in debug mode)

## Testing

### Frontend Testing

```bash
cd ai-shopping-assistant/frontend
npm test
```

### Backend Testing

```bash
cd ai-shopping-assistant/backend
pytest
```

## Deployment Instructions

### Frontend Deployment (Vercel)

1. Navigate to the frontend directory:
   ```bash
   cd ai-shopping-assistant/frontend
   ```

2. Create a `.env.production` file with your production environment variables:
   ```
   VITE_API_BASE_URL=https://ai-shopping-assistant-api.onrender.com/api
   VITE_ENABLE_ANALYTICS=true
   ```

3. Run the deployment script:
   ```bash
   ./deploy.sh
   ```

4. Follow the Vercel CLI prompts to complete the deployment.

### Backend Deployment (Render)

1. Navigate to the backend directory:
   ```bash
   cd ai-shopping-assistant/backend
   ```

2. Create a `.env.production` file with your production environment variables:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   AFFILIATE_TAG=your_affiliate_tag_here
   AFFILIATE_PROGRAM=amazon
   API_HOST=0.0.0.0
   API_PORT=10000
   DEBUG=False
   LOG_LEVEL=INFO
   WORKERS=4
   ALLOWED_HOSTS=ai-shopping-assistant-api.onrender.com,localhost
   FRONTEND_URL=https://ai-shopping-assistant.vercel.app
   ```

3. Run the deployment script and select option 2 for Render deployment:
   ```bash
   ./deploy.sh
   ```

4. Follow the Render CLI prompts to complete the deployment.

### Alternative: Local Docker Deployment

1. Navigate to the backend directory:
   ```bash
   cd ai-shopping-assistant/backend
   ```

2. Create a `.env.production` file with your environment variables.

3. Run the deployment script and select option 1 for Docker deployment:
   ```bash
   ./deploy.sh
   ```

4. Alternatively, use Docker Compose:
   ```bash
   docker-compose up -d
   ```

## API Documentation

For detailed API documentation, see [API_DOCUMENTATION.md](backend/API_DOCUMENTATION.md).

### Quick API Reference

- `GET /`: Health check endpoint with version information
- `GET /health`: Simple health check endpoint
- `POST /api/query`: Process a user query and return product recommendations

## Production URLs

- Frontend: https://ai-shopping-assistant.vercel.app
- Backend API: https://ai-shopping-assistant-api.onrender.com

## CORS Configuration

The backend is configured to accept requests from the following origins:
- http://localhost:5173 (Development)
- http://localhost:3000 (Development)
- https://ai-shopping-assistant.vercel.app (Production)

If you deploy the frontend to a different URL, update the `FRONTEND_URL` environment variable in the backend's `.env.production` file.

## License

This project is licensed under the [Mozilla Public License 2.0](LICENSE) - see the LICENSE file for details.

### Commercial Use

While this project is open source, **commercial use requires a separate license**. Please see [COMMERCIAL_LICENSE.md](../COMMERCIAL_LICENSE.md) for details or contact **bhushan@highguts.com** for commercial licensing inquiries.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. By contributing to this project, you agree that your contributions will be licensed under the same license as the project.

## Troubleshooting

### Common Issues

1. **API Key Issues**: Ensure your Gemini API key is correctly set in the environment variables.
2. **CORS Errors**: Verify that the frontend URL is correctly set in the backend's CORS configuration.
3. **Docker Issues**: Make sure Docker is running and you have sufficient permissions.
4. **Deployment Failures**: Check the deployment logs for specific error messages.

### Getting Help

If you encounter any issues, please check the existing documentation and test files for guidance. For further assistance, please open an issue in the repository.