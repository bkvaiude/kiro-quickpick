# AI Shopping Assistant Backend

This is the backend API for the AI Shopping Assistant application. It's built with FastAPI and uses the Gemini API for natural language processing to provide product recommendations based on user queries.

## Features

- Natural language query processing using Gemini API
- Structured product recommendations with detailed information
- Conversation context management for follow-up queries
- Affiliate link generation for product recommendations
- Robust error handling and retry mechanisms

## Development Setup

1. Clone the repository
2. Create a virtual environment:
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
5. Edit the `.env` file and add your Gemini API key and other settings:
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
6. Run the development server:
   ```bash
   python run.py
   ```
7. The API will be available at `http://localhost:8000`
   - API documentation: `http://localhost:8000/docs` (only in debug mode)
   - ReDoc: `http://localhost:8000/redoc` (only in debug mode)

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── __init__.py
│   │   │   ├── query.py
│   │   │   └── test_query.py
│   │   ├── __init__.py
│   │   └── router.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── query.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── affiliate_service.py
│   │   ├── context_manager_service.py
│   │   ├── gemini_service.py
│   │   ├── product_parser_service.py
│   │   ├── test_affiliate_service.py
│   │   ├── test_context_manager_service.py
│   │   └── test_gemini_service.py
│   ├── config.py
│   └── main.py
├── tests/
│   └── test_e2e.py
├── .env
├── .env.example
├── .env.production
├── API_DOCUMENTATION.md
├── deploy.sh
├── docker-compose.yml
├── Dockerfile
├── Pipfile
├── README.md
├── render.yaml
├── requirements.txt
└── run.py
```

## Testing

Run the tests using pytest:

```bash
pytest
```

For more verbose output:

```bash
pytest -v
```

To run a specific test file:

```bash
pytest app/api/endpoints/test_query.py
```

## Production Deployment

### Using Docker

1. Create a `.env.production` file based on `.env.example`:
   ```bash
   cp .env.example .env.production
   ```
2. Edit the `.env.production` file with your production settings:
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
3. Run the deployment script:
   ```bash
   ./deploy.sh
   ```
4. Follow the prompts to select your deployment option (Docker or Render)

### Using Docker Compose

1. Create a `.env.production` file with your production settings
2. Run Docker Compose:
   ```bash
   docker-compose up -d
   ```

### Manual Docker Deployment

1. Build the Docker image:
   ```bash
   docker build -t ai-shopping-assistant-api .
   ```
2. Run the container:
   ```bash
   docker run -d -p 8000:8000 --env-file .env.production --name ai-shopping-assistant-api ai-shopping-assistant-api
   ```

### Render Deployment

1. Create a `.env.production` file with your production settings
2. Make sure you have the Render CLI installed
3. Run the deployment script and select option 2:
   ```bash
   ./deploy.sh
   ```
4. Follow the Render CLI prompts to complete the deployment

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| GEMINI_API_KEY | Your Gemini API key | - | Yes |
| AFFILIATE_TAG | Your affiliate tag | - | Yes |
| AFFILIATE_PROGRAM | Affiliate program (e.g., amazon) | amazon | No |
| API_HOST | Host to bind the API server | 0.0.0.0 | No |
| API_PORT | Port to bind the API server | 8000 | No |
| DEBUG | Enable debug mode | False | No |
| LOG_LEVEL | Logging level (DEBUG, INFO, WARNING, ERROR) | INFO | No |
| WORKERS | Number of worker processes | 4 | No |
| FRONTEND_URL | URL of the frontend application | - | Yes |
| ALLOWED_HOSTS | Comma-separated list of allowed hosts | localhost | No |

## API Endpoints

For detailed API documentation, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md).

### Quick API Reference

- `GET /`: Health check endpoint with version information
- `GET /health`: Simple health check endpoint
- `POST /api/query`: Process a user query and return product recommendations

## Docker Compose

The application can be run using Docker Compose:

```bash
docker-compose up -d
```

To stop the containers:

```bash
docker-compose down
```

To view logs:

```bash
docker-compose logs -f
```

## Troubleshooting

### Common Issues

1. **API Key Issues**: Ensure your Gemini API key is correctly set in the environment variables.
2. **CORS Errors**: Verify that the frontend URL is correctly set in the backend's CORS configuration.
3. **Docker Issues**: Make sure Docker is running and you have sufficient permissions.
4. **Deployment Failures**: Check the deployment logs for specific error messages.

### Gemini API Errors

If you encounter issues with the Gemini API, check the following:

1. Verify that your API key is valid and has sufficient quota
2. Check the Gemini API status page for any service disruptions
3. Review the logs for specific error messages from the Gemini API

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the tests
5. Submit a pull request

## Database config

```
docker run -d \
  --name pg-ai-assistant \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=ai_shopping_assistant \
  -p 5433:5432 \
  -v pgdata_ai:/var/lib/postgresql/data \
  postgres
```
