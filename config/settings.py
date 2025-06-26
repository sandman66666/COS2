# config/settings.py
import os
from pathlib import Path
from dotenv import load_dotenv
import urllib.parse

# Load environment variables from .env file (for local development)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Helper function to parse DATABASE_URL (Heroku style)
def parse_database_url():
    """Parse DATABASE_URL for Heroku PostgreSQL"""
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Parse the URL
        parsed = urllib.parse.urlparse(database_url)
        return {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'user': parsed.username,
            'password': parsed.password,
            'database': parsed.path[1:] if parsed.path else None  # Remove leading slash
        }
    return None

# Database settings - Heroku compatible
heroku_db = parse_database_url()
if heroku_db:
    # Use Heroku DATABASE_URL
    POSTGRES_HOST = heroku_db['host']
    POSTGRES_PORT = heroku_db['port']
    POSTGRES_USER = heroku_db['user']
    POSTGRES_PASSWORD = heroku_db['password']
    POSTGRES_DB = heroku_db['database']
else:
    # Use individual environment variables (local development)
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', 5432))
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'oudiantebi')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'chief_of_staff')

# Neo4j settings
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'password')

# Redis settings - Heroku compatible
REDIS_URL = os.getenv('REDIS_URL')  # Heroku Redis addon format
if REDIS_URL:
    # Parse Redis URL for Heroku
    parsed_redis = urllib.parse.urlparse(REDIS_URL)
    REDIS_HOST = parsed_redis.hostname
    REDIS_PORT = parsed_redis.port or 6379
    REDIS_PASSWORD = parsed_redis.password
else:
    # Individual settings for local development
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')

# ChromaDB settings
CHROMA_HOST = os.getenv('CHROMA_HOST', 'localhost')
CHROMA_PORT = int(os.getenv('CHROMA_PORT', 8000))

# Google OAuth settings - Environment-aware
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

# Dynamic redirect URI based on environment
force_domain = os.getenv('FORCE_DOMAIN')
if force_domain:
    # Use forced domain (the actual Heroku domain)
    GOOGLE_REDIRECT_URI = f"https://{force_domain}/auth/callback"
elif os.getenv('HEROKU_APP_NAME'):
    # Fallback for Heroku environment without FORCE_DOMAIN
    heroku_app_name = os.getenv('HEROKU_APP_NAME')
    GOOGLE_REDIRECT_URI = f"https://{heroku_app_name}.herokuapp.com/auth/callback"
else:
    # Local development
    GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8080/auth/callback')

GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'openid'
]

# API settings - Heroku compatible
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('PORT', os.getenv('API_PORT', 8080)))  # Heroku uses PORT
API_DEBUG = os.getenv('API_DEBUG', 'False').lower() == 'true'
API_SECRET_KEY = os.getenv('API_SECRET_KEY', 'very-secure-secret-key')

# Anthropic settings
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# Application settings
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# Heroku detection
IS_HEROKU = bool(os.getenv('DYNO'))  # Heroku sets DYNO environment variable

# Force domain for OAuth consistency (used in Heroku to maintain session state)
FORCE_DOMAIN = os.getenv('FORCE_DOMAIN')
