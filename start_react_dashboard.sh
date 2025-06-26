#!/bin/bash

echo "🚀 Building React Dashboard for Production..."

# Navigate to React app directory
cd dashboard-react

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Build for production
echo "🔨 Building production build..."
npm run build

# Copy build files to serve alongside Flask app
echo "📋 Copying build files..."
cp -r build/* ../static/react/

echo "✅ React Dashboard built and ready!"
echo "📍 React files copied to static/react/"
echo "💡 You can now serve the React dashboard at /react route" 