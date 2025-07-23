#!/bin/bash

# AI Shopping Assistant Deployment Verification Script
# This script checks if the deployed application is working correctly

echo "AI Shopping Assistant Deployment Verification"
echo "============================================="

# Define colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
FRONTEND_URL=${1:-"https://ai-shopping-assistant.vercel.app"}
BACKEND_URL=${2:-"https://ai-shopping-assistant-api.onrender.com"}

echo -e "${YELLOW}Testing with:${NC}"
echo "Frontend URL: $FRONTEND_URL"
echo "Backend URL: $BACKEND_URL"
echo

# Check if curl is installed
if ! command -v curl &> /dev/null; then
    echo -e "${RED}Error: curl is not installed. Please install curl to run this script.${NC}"
    exit 1
fi

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}Warning: jq is not installed. JSON responses will not be formatted.${NC}"
    JQ_AVAILABLE=false
else
    JQ_AVAILABLE=true
fi

echo "1. Checking backend health endpoint..."
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/health")

if [ "$HEALTH_RESPONSE" == "200" ]; then
    echo -e "${GREEN}✓ Backend health endpoint is responding (HTTP 200)${NC}"
else
    echo -e "${RED}✗ Backend health endpoint returned HTTP $HEALTH_RESPONSE${NC}"
    echo -e "${YELLOW}This may indicate that the backend is not deployed correctly or is experiencing issues.${NC}"
fi

echo

echo "2. Checking backend root endpoint..."
ROOT_RESPONSE=$(curl -s "$BACKEND_URL/")

if [ -n "$ROOT_RESPONSE" ]; then
    echo -e "${GREEN}✓ Backend root endpoint is responding${NC}"
    if [ "$JQ_AVAILABLE" == true ]; then
        echo "Response:"
        echo "$ROOT_RESPONSE" | jq .
    else
        echo "Response: $ROOT_RESPONSE"
    fi
else
    echo -e "${RED}✗ Backend root endpoint is not responding${NC}"
fi

echo

echo "3. Testing frontend accessibility..."
FRONTEND_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL")

if [ "$FRONTEND_RESPONSE" == "200" ]; then
    echo -e "${GREEN}✓ Frontend is accessible (HTTP 200)${NC}"
else
    echo -e "${RED}✗ Frontend returned HTTP $FRONTEND_RESPONSE${NC}"
    echo -e "${YELLOW}This may indicate that the frontend is not deployed correctly or is experiencing issues.${NC}"
fi

echo

echo "4. Testing API query endpoint with a simple request..."
QUERY_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d '{"query":"What is the best smartphone under 15000 rupees?", "conversation_context":{"messages":[]}}' \
    "$BACKEND_URL/api/query")

if [ -n "$QUERY_RESPONSE" ]; then
    if [[ "$QUERY_RESPONSE" == *"products"* ]]; then
        echo -e "${GREEN}✓ API query endpoint is responding with product data${NC}"
        if [ "$JQ_AVAILABLE" == true ]; then
            echo "Number of products returned:"
            echo "$QUERY_RESPONSE" | jq '.products | length'
        fi
    else
        echo -e "${RED}✗ API query endpoint response does not contain product data${NC}"
        if [ "$JQ_AVAILABLE" == true ]; then
            echo "Response:"
            echo "$QUERY_RESPONSE" | jq .
        else
            echo "Response: $QUERY_RESPONSE"
        fi
    fi
else
    echo -e "${RED}✗ API query endpoint is not responding${NC}"
fi

echo

echo "5. Checking CORS configuration..."
CORS_RESPONSE=$(curl -s -I -X OPTIONS \
    -H "Origin: $FRONTEND_URL" \
    -H "Access-Control-Request-Method: POST" \
    "$BACKEND_URL/api/query" | grep -i "access-control-allow-origin")

if [ -n "$CORS_RESPONSE" ]; then
    echo -e "${GREEN}✓ CORS headers are configured${NC}"
    echo "Response: $CORS_RESPONSE"
else
    echo -e "${RED}✗ CORS headers are not properly configured${NC}"
    echo -e "${YELLOW}This may cause issues with frontend-backend communication.${NC}"
fi

echo

echo "Deployment Verification Summary:"
echo "-------------------------------"

if [ "$HEALTH_RESPONSE" == "200" ] && [ -n "$ROOT_RESPONSE" ] && [ "$FRONTEND_RESPONSE" == "200" ] && [[ "$QUERY_RESPONSE" == *"products"* ]] && [ -n "$CORS_RESPONSE" ]; then
    echo -e "${GREEN}✓ All checks passed! The application appears to be deployed correctly.${NC}"
else
    echo -e "${RED}✗ Some checks failed. Please review the issues above.${NC}"
fi

echo
echo "For more detailed testing, please use a web browser to access the frontend at:"
echo "$FRONTEND_URL"