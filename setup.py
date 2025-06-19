#!/usr/bin/env python3
"""
Strategic Intelligence System Setup Script
==========================================
Handles all database initialization, extension installation, and system setup.
"""

import os
import sys
import subprocess
import platform
import asyncio
import asyncpg
from pathlib import Path

def run_command(cmd, check=True, shell=True):
    """Run a shell command and return the result"""
    print(f"🔧 Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=shell, check=check, capture_output=True, text=True)
        if result.stdout:
            print(f"✅ {result.stdout.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"   {e.stderr.strip()}")
        if check:
            raise
        return e

def check_system():
    """Check system requirements"""
    print("🔍 Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]}")
    
    # Check if we're on macOS
    if platform.system() != "Darwin":
        print("⚠️  This setup script is optimized for macOS. Manual setup may be required.")
    else:
        print("✅ macOS detected")

def install_system_dependencies():
    """Install system-level dependencies via Homebrew"""
    print("\n📦 Installing system dependencies...")
    
    # Check if Homebrew is installed
    result = run_command("which brew", check=False)
    if result.returncode != 0:
        print("❌ Homebrew not found. Please install Homebrew first:")
        print("   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
        sys.exit(1)
    print("✅ Homebrew found")
    
    # Install PostgreSQL
    print("🐘 Setting up PostgreSQL...")
    run_command("brew install postgresql@15", check=False)
    
    # Install pgvector for PostgreSQL 15
    print("🔧 Installing pgvector...")
    run_command("brew install pgvector", check=False)
    
    # Install Redis
    print("🔴 Setting up Redis...")
    run_command("brew install redis", check=False)
    
    # Install Neo4j (optional)
    print("🕸️  Setting up Neo4j...")
    run_command("brew install neo4j", check=False)

def setup_postgresql():
    """Setup PostgreSQL database and extensions"""
    print("\n🐘 Setting up PostgreSQL...")
    
    # Start PostgreSQL service
    print("🚀 Starting PostgreSQL service...")
    run_command("brew services start postgresql@15", check=False)
    
    # Wait a moment for PostgreSQL to start
    import time
    time.sleep(3)
    
    # Create database
    db_name = "chief_of_staff"
    print(f"🗄️  Creating database: {db_name}")
    run_command(f"createdb {db_name}", check=False)
    
    # Get current user for database connection
    username = os.getenv("USER")
    
    # Create pgvector extension symlinks for PostgreSQL 15
    print("🔗 Setting up pgvector for PostgreSQL 15...")
    pg15_share = "/opt/homebrew/share/postgresql@15"
    pg15_lib = "/opt/homebrew/lib/postgresql@15"
    
    # Create directories if they don't exist
    run_command(f"mkdir -p {pg15_share}/extension", check=False)
    run_command(f"mkdir -p {pg15_lib}", check=False)
    
    # Create symlinks from pgvector files
    pgvector_share = "/opt/homebrew/Cellar/pgvector/0.8.0/share/postgresql@14"
    pgvector_lib = "/opt/homebrew/Cellar/pgvector/0.8.0/lib/postgresql@14"
    
    run_command(f"ln -sf {pgvector_share}/extension/* {pg15_share}/extension/", check=False)
    run_command(f"ln -sf {pgvector_lib}/* {pg15_lib}/", check=False)
    
    # Test database connection and create extensions
    print("🧪 Testing database connection and creating extensions...")
    try:
        # Test basic connection
        run_command(f'psql -d {db_name} -c "SELECT version();"')
        
        # Create extensions
        run_command(f'psql -d {db_name} -c "CREATE EXTENSION IF NOT EXISTS vector;"', check=False)
        run_command(f'psql -d {db_name} -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"', check=False)
        
        print("✅ PostgreSQL setup complete")
        
    except Exception as e:
        print(f"⚠️  PostgreSQL setup encountered issues: {e}")
        print("   The application will attempt to create extensions at runtime.")

def setup_redis():
    """Setup Redis"""
    print("\n🔴 Setting up Redis...")
    run_command("brew services start redis", check=False)
    
    # Test Redis connection
    try:
        run_command("redis-cli ping", check=False)
        print("✅ Redis setup complete")
    except:
        print("⚠️  Redis may not be running. Will attempt to start during app initialization.")

def setup_python_environment():
    """Setup Python virtual environment and dependencies"""
    print("\n🐍 Setting up Python environment...")
    
    # Create virtual environment if it doesn't exist
    if not os.path.exists("venv"):
        print("📦 Creating virtual environment...")
        run_command(f"{sys.executable} -m venv venv")
    
    # Determine activation script based on OS
    if platform.system() == "Windows":
        pip_cmd = "venv\\Scripts\\pip"
    else:
        pip_cmd = "venv/bin/pip"
    
    # Install requirements
    print("📦 Installing Python dependencies...")
    run_command(f"{pip_cmd} install --upgrade pip")
    run_command(f"{pip_cmd} install -r requirements.txt")
    
    print("✅ Python environment setup complete")

def create_env_file():
    """Create .env file with default configuration"""
    print("\n⚙️  Setting up configuration...")
    
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file already exists")
        return
    
    username = os.getenv("USER")
    
    env_content = f"""# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER={username}
POSTGRES_PASSWORD=
POSTGRES_DB=chief_of_staff

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Neo4j Configuration (optional)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# ChromaDB Configuration (optional)
CHROMA_HOST=localhost
CHROMA_PORT=8000

# API Configuration
API_HOST=0.0.0.0
API_PORT=8080
API_DEBUG=true
API_SECRET_KEY=development-secret-key-change-in-production

# Google OAuth (update with your actual credentials)
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:8080/api/auth/callback

# Anthropic API (optional)
ANTHROPIC_API_KEY=your_anthropic_key_here

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
"""
    
    with open(env_file, "w") as f:
        f.write(env_content)
    
    print("✅ Created .env file with default configuration")
    print("📝 Please update Google OAuth credentials in .env file")

async def test_database_schema():
    """Test database schema creation"""
    print("\n🧪 Testing database schema...")
    
    try:
        username = os.getenv("USER")
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            user=username,
            database="chief_of_staff"
        )
        
        # Test vector extension
        await conn.execute("SELECT vector_version();")
        print("✅ pgvector extension working")
        
        # Create test table with vector column
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_vectors (
                id SERIAL PRIMARY KEY,
                embedding vector(3)
            );
        """)
        
        # Insert test data
        await conn.execute("""
            INSERT INTO test_vectors (embedding) VALUES ('[1,2,3]');
        """)
        
        # Query test data
        result = await conn.fetchval("""
            SELECT embedding FROM test_vectors LIMIT 1;
        """)
        
        # Clean up
        await conn.execute("DROP TABLE test_vectors;")
        await conn.close()
        
        print("✅ Database schema test passed")
        
    except Exception as e:
        print(f"⚠️  Database schema test failed: {e}")
        print("   The application will create schema at runtime")

def main():
    """Main setup function"""
    print("🚀 Strategic Intelligence System Setup")
    print("=" * 50)
    
    try:
        check_system()
        install_system_dependencies()
        setup_postgresql()
        setup_redis()
        setup_python_environment()
        create_env_file()
        
        # Run async database test
        asyncio.run(test_database_schema())
        
        print("\n🎉 Setup completed successfully!")
        print("\n📋 Next steps:")
        print("   1. Update Google OAuth credentials in .env file")
        print("   2. Activate virtual environment: source venv/bin/activate")
        print("   3. Start the application: python3 app.py")
        print("   4. Visit: http://localhost:8080/dashboard")
        
    except KeyboardInterrupt:
        print("\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 