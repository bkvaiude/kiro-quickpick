# Docker Setup for AI Shopping Assistant Backend

This document explains how to run the AI Shopping Assistant backend using Docker with PostgreSQL.

## Prerequisites

- Docker and Docker Compose installed
- Environment variables configured (see `.env.example`)

## Environment Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Update the environment variables in `.env` with your actual values:
   - `GEMINI_API_KEY`: Your Google Gemini API key
   - `AFFILIATE_TAG`: Your affiliate program tag
   - `POSTGRES_PASSWORD`: Set a secure password for PostgreSQL
   - Other database and API settings as needed

## Development Setup

For development with hot reloading:

```bash
# Start PostgreSQL and API with hot reloading
docker-compose -f docker-compose.dev.yml up --build

# Or start only PostgreSQL (if you want to run the API locally)
docker-compose -f docker-compose.dev.yml up postgres
```

The development setup includes:
- Hot reloading for code changes
- Volume mounting for live code updates
- Debug mode enabled
- PostgreSQL with persistent data volume

## Production Setup

For production deployment:

```bash
# Create production environment file
cp .env.example .env.production

# Update .env.production with production values
# Make sure to set DEBUG=False and secure passwords

# Start the services
docker-compose up --build -d
```

## Database Initialization

The PostgreSQL container will automatically:
1. Create the database specified in `POSTGRES_DB`
2. Run initialization scripts from `init-scripts/`
3. Set up required extensions (uuid-ossp, pg_trgm)

The API will automatically:
1. Run database migrations on startup
2. Initialize connection pools
3. Perform health checks

## Health Checks

Both services include health checks:

- **PostgreSQL**: Uses `pg_isready` to check database availability
- **API**: Uses HTTP health check endpoint at `/health`

Check service status:
```bash
docker-compose ps
```

## Useful Commands

```bash
# View logs
docker-compose logs -f api
docker-compose logs -f postgres

# Access PostgreSQL directly
docker-compose exec postgres psql -U postgres -d ai_shopping_assistant

# Run database migrations manually (if needed)
docker-compose exec api python -c "from app.database.manager import database_manager; database_manager.run_migrations()"

# Stop services
docker-compose down

# Stop services and remove volumes (WARNING: This deletes all data)
docker-compose down -v
```

## Troubleshooting

### Database Connection Issues

1. Check if PostgreSQL is healthy:
   ```bash
   docker-compose ps postgres
   ```

2. Check PostgreSQL logs:
   ```bash
   docker-compose logs postgres
   ```

3. Verify database connectivity from API container:
   ```bash
   docker-compose exec api python -c "from app.database.manager import database_manager; import asyncio; asyncio.run(database_manager.health_check())"
   ```

### API Startup Issues

1. Check API logs:
   ```bash
   docker-compose logs api
   ```

2. Verify environment variables:
   ```bash
   docker-compose exec api env | grep -E "(DATABASE_URL|POSTGRES_|GEMINI_)"
   ```

3. Test API health endpoint:
   ```bash
   curl http://localhost:8000/health
   ```

## Data Persistence

- **Development**: Data is stored in `postgres_dev_data` volume
- **Production**: Data is stored in `postgres_data` volume

Volumes persist between container restarts but can be removed with `docker-compose down -v`.

## Security Notes

- Change default PostgreSQL password in production
- Use secure environment variable management in production
- Consider using Docker secrets for sensitive data
- Ensure proper network security and firewall rules