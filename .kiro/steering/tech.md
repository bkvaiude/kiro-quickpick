# Technology Stack

## Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite 4.4.5
- **Styling**: Tailwind CSS with custom components
- **UI Components**: Radix UI primitives
- **Icons**: Lucide React
- **Testing**: Vitest with React Testing Library
- **Authentication**: Auth0 React SDK
- **Routing**: React Router DOM v7

## Backend
- **Framework**: FastAPI 0.104.1
- **Runtime**: Python 3.9+
- **ASGI Server**: Uvicorn (development), Gunicorn (production)
- **AI Integration**: Google Generative AI (Gemini API)
- **HTTP Client**: HTTPX for async requests
- **Validation**: Pydantic v2
- **Testing**: pytest with pytest-asyncio
- **Authentication**: Auth0 with python-jose

## Development Tools
- **Package Management**: 
  - Frontend: npm
  - Backend: pip with requirements.txt and Pipfile
- **Environment**: python-dotenv for configuration
- **Code Quality**: ESLint, Prettier (frontend)

## Deployment
- **Frontend**: Vercel (production), Vite dev server (development)
- **Backend**: Render (production), Docker support available
- **Containerization**: Docker with docker-compose

## Common Commands

### Frontend Development
```bash
cd ai-shopping-assistant/frontend
npm install                 # Install dependencies
npm run dev                # Start development server (localhost:5173)
npm run build              # Build for production
npm run preview            # Preview production build
npm test                   # Run tests
npm run test:watch         # Run tests in watch mode
```

### Backend Development
```bash
cd ai-shopping-assistant/backend
python -m venv venv        # Create virtual environment
source venv/bin/activate   # Activate virtual environment (Linux/Mac)
pip install -r requirements.txt  # Install dependencies
python run.py              # Start development server (localhost:8000)
pytest                     # Run tests
pytest -v                  # Run tests with verbose output
```

### Docker Commands
```bash
cd ai-shopping-assistant/backend
docker build -t ai-shopping-assistant-api .
docker-compose up -d       # Start with docker-compose
docker-compose down        # Stop containers
docker-compose logs -f     # View logs
```

### Deployment Scripts
```bash
# Frontend deployment to Vercel
cd ai-shopping-assistant/frontend
./deploy.sh

# Backend deployment (Docker or Render)
cd ai-shopping-assistant/backend
./deploy.sh
```

## Environment Configuration
- Frontend: `.env` files with `VITE_` prefixed variables
- Backend: `.env` files loaded via python-dotenv
- Separate `.env.production` files for production deployments