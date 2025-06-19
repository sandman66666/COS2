#!/bin/bash
# Strategic Intelligence System Startup Script
# ============================================

echo "🚀 Starting Strategic Intelligence System..."

# Function to check if a service is running
check_service() {
    local service=$1
    local port=$2
    
    if lsof -ti:$port > /dev/null 2>&1; then
        echo "✅ $service is running on port $port"
        return 0
    else
        echo "❌ $service is not running on port $port"
        return 1
    fi
}

# Start PostgreSQL if not running
echo "🐘 Checking PostgreSQL..."
if ! check_service "PostgreSQL" 5432; then
    echo "🚀 Starting PostgreSQL..."
    brew services start postgresql@15
    sleep 3
fi

# Start Redis if not running  
echo "🔴 Checking Redis..."
if ! check_service "Redis" 6379; then
    echo "🚀 Starting Redis..."
    brew services start redis
    sleep 2
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️  No virtual environment found. Run setup.py first."
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Run setup.py first or create one manually."
fi

# Start the application
echo "🌟 Starting Strategic Intelligence System..."
echo "📊 Dashboard will be available at: http://localhost:8080/dashboard"
echo "🔍 Health check: http://localhost:8080/api/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 app.py 