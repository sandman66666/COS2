# Strategic Intelligence System

A production-ready Strategic Intelligence System with Gmail integration, contact analysis, and multi-database architecture.

## 🚀 Quick Setup

### Automated Setup (Recommended)

1. **Run the setup script:**
   ```bash
   python3 setup.py
   ```

2. **Update Google OAuth credentials in `.env` file:**
   ```bash
   nano .env
   # Add your Google Client ID and Secret
   ```

3. **Start the system:**
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

4. **Access the dashboard:**
   - Open: http://localhost:8080/dashboard
   - Login with Google OAuth
   - Test the 6-step intelligence flow

### Manual Setup

If you prefer manual setup or the automated script doesn't work:

#### 1. System Dependencies (macOS)

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install PostgreSQL 15
brew install postgresql@15
brew services start postgresql@15

# Install pgvector extension
brew install pgvector

# Install Redis
brew install redis
brew services start redis

# Install Neo4j (optional)
brew install neo4j
```

#### 2. Database Setup

```bash
# Create database
createdb chief_of_staff

# Create pgvector extension symlinks for PostgreSQL 15
mkdir -p /opt/homebrew/share/postgresql@15/extension
mkdir -p /opt/homebrew/lib/postgresql@15

ln -sf /opt/homebrew/Cellar/pgvector/0.8.0/share/postgresql@14/extension/* /opt/homebrew/share/postgresql@15/extension/
ln -sf /opt/homebrew/Cellar/pgvector/0.8.0/lib/postgresql@14/* /opt/homebrew/lib/postgresql@15/

# Test extensions
psql chief_of_staff -c "CREATE EXTENSION IF NOT EXISTS vector;"
psql chief_of_staff -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
```

#### 3. Python Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Configuration

Create a `.env` file:

```bash
# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=your_username
POSTGRES_PASSWORD=
POSTGRES_DB=chief_of_staff

# Google OAuth
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8080/api/auth/callback

# API Configuration
API_HOST=0.0.0.0
API_PORT=8080
API_DEBUG=true
API_SECRET_KEY=your-secret-key

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
```

## 🏗️ Architecture

### Core Components

- **Gmail Integration**: OAuth2 authentication and email analysis
- **PostgreSQL**: Primary database with pgvector for semantic search
- **Redis**: Caching and session management
- **Neo4j**: Knowledge graph (optional)
- **ChromaDB**: Vector embeddings (optional)

### Multi-Analyst Architecture

1. **5 Claude Analysts**: Specialized AI agents for different analysis types
2. **Trust Network Analysis**: Identify trusted contacts from sent emails
3. **Knowledge Tree Building**: Hierarchical organization of intelligence
4. **Predictive Intelligence**: Future trend analysis
5. **Calendar Integration**: Schedule-aware recommendations

## 📊 Dashboard Features

### 6-Step Testing Flow

1. **📧 Email Contact Import**: Analyze sent emails for trusted contacts
2. **👥 Contact List Presentation**: View and manage extracted contacts
3. **🔍 Contact Augmentation**: Enrich contacts with external data
4. **📨 Email Import**: Import and process email conversations
5. **🌳 Knowledge Tree Creation**: Build hierarchical knowledge structure
6. **🔮 Advanced Features**: Predictions, calendar integration, insights

### System Management

- **🗑️ Flush DB and Start Clean**: Reset all data for fresh testing
- **💊 System Health Check**: Monitor database and service status
- **🔐 Authentication Status**: Google OAuth login state

## 🔧 Troubleshooting

### Common Issues

#### PostgreSQL Connection Failed
```bash
# Check if PostgreSQL is running
brew services list | grep postgresql

# Start PostgreSQL
brew services start postgresql@15

# Check database exists
psql -l | grep chief_of_staff
```

#### pgvector Extension Not Found
```bash
# Reinstall pgvector
brew reinstall pgvector

# Recreate symlinks (see setup script)
```

#### Google OAuth Not Working
1. Check Google Cloud Console configuration
2. Verify redirect URI: `http://localhost:8080/api/auth/callback`
3. Ensure OAuth consent screen is configured
4. Check `.env` file has correct credentials

#### Redis Connection Failed
```bash
# Start Redis
brew services start redis

# Test connection
redis-cli ping
```

### Debug Mode

Run with debug logging:
```bash
LOG_LEVEL=DEBUG python3 app.py
```

## 🚧 Development

### File Structure

```
NEW-COS/
├── app.py                  # Main application entry point
├── setup.py               # Automated setup script
├── start.sh               # Startup script
├── requirements.txt       # Python dependencies
├── config/                # Configuration management
├── auth/                  # Authentication system
├── api/                   # REST API routes
├── gmail/                 # Gmail integration
├── intelligence/          # AI analysis modules
├── storage/               # Database clients
├── middleware/            # Request/response handling
├── templates/             # HTML templates
├── static/               # Static files and dashboard
└── utils/                # Shared utilities
```

### Adding New Features

1. Follow the modular architecture
2. Add proper async/await support
3. Include comprehensive error handling
4. Update requirements.txt if needed
5. Add tests for new functionality

### Database Schema

The system automatically creates all required tables:

- `users`: User accounts and settings
- `contacts`: Trusted contacts with trust tiers
- `emails`: Email content and metadata
- `knowledge_tree`: Hierarchical intelligence data
- `oauth_credentials`: OAuth tokens

## 📝 License

This project is for educational and development purposes.

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the logs for error details
3. Ensure all dependencies are properly installed
4. Verify database connections and extensions 