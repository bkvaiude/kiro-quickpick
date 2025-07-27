#!/bin/bash

# Docker Helper Script for AI Shopping Assistant Backend

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to check if .env file exists
check_env_file() {
    local env_file=$1
    if [ ! -f "$env_file" ]; then
        print_warning "$env_file not found. Creating from .env.example..."
        if [ -f ".env.example" ]; then
            cp .env.example "$env_file"
            print_status "Created $env_file from .env.example"
            print_warning "Please update $env_file with your actual configuration values"
        else
            print_error ".env.example not found. Cannot create $env_file"
            exit 1
        fi
    fi
}

# Function to start development environment
start_dev() {
    print_status "Starting development environment..."
    check_env_file ".env"
    docker-compose -f docker-compose.dev.yml up --build
}

# Function to start production environment
start_prod() {
    print_status "Starting production environment..."
    check_env_file ".env.production"
    docker-compose up --build -d
    print_status "Services started in background. Use 'docker-compose logs -f' to view logs."
}

# Function to stop services
stop_services() {
    print_status "Stopping services..."
    docker-compose down
    docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
    print_status "Services stopped."
}

# Function to view logs
view_logs() {
    local service=${1:-""}
    if [ -z "$service" ]; then
        print_status "Viewing logs for all services..."
        docker-compose logs -f
    else
        print_status "Viewing logs for $service..."
        docker-compose logs -f "$service"
    fi
}

# Function to run database migrations
run_migrations() {
    print_status "Running database migrations..."
    docker-compose exec api python -c "
from app.database.manager import database_manager
import asyncio
try:
    database_manager.run_migrations()
    print('Migrations completed successfully')
except Exception as e:
    print(f'Migration failed: {e}')
    exit(1)
"
}

# Function to check health
check_health() {
    print_status "Checking service health..."
    
    # Check if containers are running
    if ! docker-compose ps | grep -q "Up"; then
        print_error "No services are running. Start services first."
        exit 1
    fi
    
    # Check PostgreSQL health
    print_status "Checking PostgreSQL health..."
    if docker-compose exec postgres pg_isready -U postgres -d ai_shopping_assistant > /dev/null 2>&1; then
        print_status "PostgreSQL is healthy"
    else
        print_error "PostgreSQL is not healthy"
    fi
    
    # Check API health
    print_status "Checking API health..."
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_status "API is healthy"
    else
        print_error "API is not healthy or not accessible"
    fi
}

# Function to access PostgreSQL shell
psql_shell() {
    print_status "Opening PostgreSQL shell..."
    docker-compose exec postgres psql -U postgres -d ai_shopping_assistant
}

# Function to clean up (remove containers and volumes)
cleanup() {
    print_warning "This will remove all containers and data volumes. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        print_status "Cleaning up containers and volumes..."
        docker-compose down -v
        docker-compose -f docker-compose.dev.yml down -v 2>/dev/null || true
        print_status "Cleanup completed."
    else
        print_status "Cleanup cancelled."
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  dev         Start development environment with hot reloading"
    echo "  prod        Start production environment in background"
    echo "  stop        Stop all services"
    echo "  logs [svc]  View logs (optionally for specific service: api, postgres)"
    echo "  migrate     Run database migrations"
    echo "  health      Check service health status"
    echo "  psql        Open PostgreSQL shell"
    echo "  cleanup     Remove containers and volumes (WARNING: deletes data)"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 dev                 # Start development environment"
    echo "  $0 logs api           # View API logs"
    echo "  $0 health             # Check all services"
}

# Main script logic
main() {
    check_docker
    
    case "${1:-help}" in
        "dev")
            start_dev
            ;;
        "prod")
            start_prod
            ;;
        "stop")
            stop_services
            ;;
        "logs")
            view_logs "$2"
            ;;
        "migrate")
            run_migrations
            ;;
        "health")
            check_health
            ;;
        "psql")
            psql_shell
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|*)
            show_usage
            ;;
    esac
}

# Run main function with all arguments
main "$@"