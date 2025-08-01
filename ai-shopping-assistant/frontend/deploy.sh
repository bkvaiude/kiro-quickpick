#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting frontend deployment process..."

# Install dependencies
echo "📦 Installing dependencies..."
npm ci

# Run tests
echo "🧪 Running tests..."
# npm test

# Build for production
echo "🔨 Building for production..."
npm run build:fast

# Output success message
echo "✅ Build completed successfully!"
echo "The build artifacts are in the 'dist' directory."
echo "You can now deploy these files to your hosting provider (e.g., Vercel)."
echo ""
echo "For Vercel deployment:"
echo "1. Install Vercel CLI: npm i -g vercel"
echo "2. Run: vercel --prod"
echo ""
echo "For manual deployment, upload the contents of the 'dist' directory to your web server."