#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting backend deployment process..."

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo "❌ Error: .env.production file not found!"
    echo "Please create a .env.production file with your production environment variables."
    exit 1
fi

# Validate required environment variables
echo "🔍 Validating environment variables..."
source .env.production
REQUIRED_VARS=("GEMINI_API_KEY" "AFFILIATE_TAG" "FRONTEND_URL")
MISSING_VARS=()

for VAR in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!VAR}" ] || [ "${!VAR}" == "your_${VAR,,}_here" ]; then
        MISSING_VARS+=("$VAR")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo "❌ Error: The following required environment variables are missing or have default values:"
    for VAR in "${MISSING_VARS[@]}"; do
        echo "  - $VAR"
    done
    echo "Please update your .env.production file with proper values."
    exit 1
fi

# Run tests
echo "🧪 Running tests..."
python -m pytest

# Deployment options
echo "📋 Select deployment option:"
echo "1) Deploy to Docker (local)"
echo "2) Deploy to Render (cloud)"
read -p "Enter your choice (1-2): " DEPLOY_OPTION

case $DEPLOY_OPTION in
    1)
        # Build and start Docker containers
        echo "🐳 Building and starting Docker containers..."
        docker-compose down
        docker-compose build --no-cache
        docker-compose up -d

        # Verify deployment
        echo "🔍 Verifying deployment..."
        MAX_RETRIES=5
        RETRY_COUNT=0
        DEPLOYED=false

        while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
            if curl -s http://localhost:${API_PORT:-8000}/health | grep -q "healthy"; then
                DEPLOYED=true
                break
            fi
            echo "Waiting for API to become available... ($(($RETRY_COUNT + 1))/$MAX_RETRIES)"
            sleep 5
            RETRY_COUNT=$((RETRY_COUNT + 1))
        done

        if [ "$DEPLOYED" = true ]; then
            # Output success message
            echo "✅ Deployment completed successfully!"
            echo "The API is now running at http://localhost:${API_PORT:-8000}"
            echo ""
            echo "To check the logs:"
            echo "docker-compose logs -f"
            echo ""
            echo "To stop the containers:"
            echo "docker-compose down"
        else
            echo "❌ Deployment verification failed. API is not responding correctly."
            echo "Check the logs with: docker-compose logs -f"
            exit 1
        fi
        ;;
    2)
        # Deploy to Render
        echo "☁️ Deploying to Render..."
        
        # Check if Render CLI is installed
        if ! command -v render &> /dev/null; then
            echo "📥 Installing Render CLI..."
            curl -s https://render.com/download/cli | bash
        fi
        
        # Deploy using render.yaml
        if [ -f render.yaml ]; then
            echo "🚀 Deploying using render.yaml configuration..."
            render deploy --yaml render.yaml
            
            echo "✅ Deployment initiated successfully!"
            echo "Your API will be available at https://ai-shopping-assistant-api.onrender.com once deployment is complete."
            echo "Check the Render dashboard for deployment status and logs."
        else
            echo "❌ Error: render.yaml file not found!"
            exit 1
        fi
        ;;
    *)
        echo "❌ Invalid option selected. Exiting."
        exit 1
        ;;
esac