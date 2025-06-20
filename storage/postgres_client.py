# storage/postgres_client.py
import asyncio
import asyncpg
import logging
from typing import Any, Dict, List, Optional, Tuple
import os
from datetime import datetime
import json

from storage.base_client import BaseStorageClient
from config.settings import (
    POSTGRES_HOST, 
    POSTGRES_PORT, 
    POSTGRES_USER, 
    POSTGRES_PASSWORD,
    POSTGRES_DB
)
from utils.logging import structured_logger as logger

class PostgresClient(BaseStorageClient):
    """PostgreSQL client with pgvector support"""
    
    def __init__(self):
        self.host = POSTGRES_HOST
        self.port = POSTGRES_PORT
        self.user = POSTGRES_USER
        self.password = POSTGRES_PASSWORD
        self.database = POSTGRES_DB
        self.conn_pool = None
        self.vector_supported = False
        
    async def connect(self) -> None:
        """Establish connection pool to PostgreSQL"""
        try:
            # Close existing pool if any
            if self.conn_pool:
                await self.conn_pool.close()
                await asyncio.sleep(0.5)  # Give it time to close properly
                
            self.conn_pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                min_size=5,  # Increased from 2
                max_size=20,  # Increased from 10
                command_timeout=60,  # Increased from 30
                max_inactive_connection_lifetime=300,  # 5 minutes
                server_settings={
                    'application_name': 'strategic_intelligence_system',
                    'tcp_keepalives_idle': '600',
                    'tcp_keepalives_interval': '30',
                    'tcp_keepalives_count': '3',
                }
            )
            
            # Initialize pgvector extension if not exists
            await self._init_pgvector()
            logger.info("Connected to PostgreSQL database", 
                       host=self.host, 
                       port=self.port,
                       database=self.database)
        except Exception as e:
            logger.error(f"PostgreSQL connection error: {str(e)}")
            raise
    
    async def disconnect(self) -> None:
        """Close all connections"""
        if self.conn_pool:
            await self.conn_pool.close()
            logger.info("Disconnected from PostgreSQL database")
    
    async def health_check(self) -> bool:
        """Check if PostgreSQL is available"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Always try to reconnect if pool is None or broken
                if not self.conn_pool:
                    await self.connect()
                
                # Test the connection with timeout - fix the async context manager issue
                connection = await asyncio.wait_for(self.conn_pool.acquire(), timeout=5)
                try:
                    result = await asyncio.wait_for(connection.fetchval("SELECT 1"), timeout=5)
                    return result == 1
                finally:
                    # Always release the connection back to the pool
                    await self.conn_pool.release(connection)
                    
            except asyncio.TimeoutError:
                logger.warning(f"PostgreSQL health check timeout (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    await self.reset_connection_pool()
                    await asyncio.sleep(1)
                    continue
                return False
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"PostgreSQL health check failed (attempt {attempt + 1}): {error_msg}")
                
                # If connection issues, try to reconnect
                if any(phrase in error_msg.lower() for phrase in [
                    "event loop is closed", 
                    "connection", 
                    "another operation is in progress",
                    "pool is closed",
                    "coroutine"
                ]):
                    if attempt < max_retries - 1:
                        try:
                            await self.reset_connection_pool()
                            await asyncio.sleep(1)
                            continue
                        except:
                            pass
                return False
        
        return False
    
    async def _init_pgvector(self) -> None:
        """Initialize pgvector extension and indexes"""
        try:
            async with self.conn_pool.acquire() as conn:
                # Try to create pgvector extension
                try:
                    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                    self.vector_supported = True
                    logger.info("Successfully enabled pgvector extension")
                except Exception as vector_error:
                    logger.warning(f"pgvector extension not available: {vector_error}")
                    logger.info("Running without vector support - semantic search will be limited")
                    self.vector_supported = False
                
                # Create pg_trgm extension for text search
                try:
                    await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
                    logger.info("Successfully enabled pg_trgm extension")
                except Exception as trgm_error:
                    logger.warning(f"pg_trgm extension not available: {trgm_error}")
                
                # Create tables with conditional vector support
                await self._initialize_schema(conn)
                
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL extensions: {str(e)}")
            raise
    
    async def _initialize_schema(self, conn) -> None:
        """Initialize database schema with conditional vector support"""
        try:
            # Create users table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    google_id VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    settings JSONB DEFAULT '{}'
                )
            """)
            
            # Create emails table with conditional vector embeddings
            if self.vector_supported:
                email_table_sql = """
                    CREATE TABLE IF NOT EXISTS emails (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id),
                        gmail_id VARCHAR(255) UNIQUE NOT NULL,
                        content TEXT,
                        embedding vector(1536),
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
            else:
                email_table_sql = """
                    CREATE TABLE IF NOT EXISTS emails (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id),
                        gmail_id VARCHAR(255) UNIQUE NOT NULL,
                        content TEXT,
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
            
            await conn.execute(email_table_sql)
            
            # Add updated_at column to existing emails table if it doesn't exist
            try:
                await conn.execute("""
                    ALTER TABLE emails ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """)
                logger.info("Successfully added updated_at column to emails table")
            except Exception as migration_error:
                # Ignore errors - column might already exist
                logger.debug(f"Column addition skipped: {migration_error}")
            
            # Create contacts table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS contacts (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    email VARCHAR(255) NOT NULL,
                    name VARCHAR(255),
                    trust_tier VARCHAR(20) NOT NULL,
                    trust_score FLOAT,
                    frequency INTEGER DEFAULT 1,
                    last_contact TEXT,
                    domain VARCHAR(255),
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, email)
                )
            """)
            
            # Migrate existing last_contact TIMESTAMP columns to TEXT (if any exist)
            try:
                await conn.execute("""
                    ALTER TABLE contacts ALTER COLUMN last_contact TYPE TEXT USING last_contact::TEXT
                """)
                logger.info("Successfully migrated last_contact column from TIMESTAMP to TEXT")
            except Exception as migration_error:
                # Ignore errors - column might already be TEXT or table might be new
                logger.debug(f"Column migration skipped: {migration_error}")
            
            # Create knowledge_tree table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_tree (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) UNIQUE,
                    tree_data JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Add unique constraint to existing knowledge_tree table if it doesn't exist
            try:
                await conn.execute("""
                    ALTER TABLE knowledge_tree ADD CONSTRAINT knowledge_tree_user_id_unique UNIQUE (user_id)
                """)
                logger.info("Successfully added unique constraint to knowledge_tree table")
            except Exception as constraint_error:
                # Ignore errors - constraint might already exist
                logger.debug(f"Constraint addition skipped: {constraint_error}")
            
            # Create OAuth credentials table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS oauth_credentials (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    provider VARCHAR(50) NOT NULL,
                    access_token TEXT,
                    refresh_token TEXT,
                    token_expiry TIMESTAMP,
                    scopes TEXT[],
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, provider)
                )
            """)
            
            # Create indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_contacts_user_id ON contacts(user_id);
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_contacts_trust_tier ON contacts(trust_tier);
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_contacts_domain ON contacts(domain);
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_emails_user_id ON emails(user_id);
            """)
            
            # Create vector index only if vector extension is available
            if self.vector_supported:
                try:
                    await conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_email_embedding 
                        ON emails USING ivfflat (embedding vector_l2_ops)
                        WITH (lists = 100);
                    """)
                    logger.info("Created vector similarity index")
                except Exception as e:
                    logger.warning(f"Failed to create vector index: {e}")
            
            logger.info("Successfully initialized database schema")
        except Exception as e:
            logger.error(f"Schema initialization error: {str(e)}")
            raise
            
    async def create_user(self, email: str, google_id: str) -> Dict:
        """Create a new user or get existing one"""
        try:
            async with self.conn_pool.acquire() as conn:
                # Try to insert, if it fails due to conflict, get existing user
                user = await conn.fetchrow("""
                    INSERT INTO users (email, google_id)
                    VALUES ($1, $2)
                    ON CONFLICT (email) DO UPDATE
                    SET google_id = $2
                    RETURNING id, email, google_id, created_at
                """, email, google_id)
                
                return {
                    'id': user['id'],
                    'email': user['email'],
                    'google_id': user['google_id'],
                    'created_at': user['created_at'].isoformat()
                }
        except Exception as e:
            logger.error(f"Failed to create/get user: {str(e)}")
            raise
    
    async def store_contacts(self, user_id: int, contacts: List[Dict]) -> int:
        """Store contacts with trust tier information"""
        max_retries = 2
        for attempt in range(max_retries):
            try:
                async with self.conn_pool.acquire() as conn:
                    count = 0
                    async with conn.transaction():
                        for contact in contacts:
                            # Simple last_contact handling - store as text, no parsing needed
                            last_contact = contact.get('last_contact')
                            if last_contact and not isinstance(last_contact, str):
                                # Convert any non-string to string
                                last_contact = str(last_contact)
                            
                            # Ensure metadata is properly JSON serialized
                            metadata = contact.get('metadata', {})
                            if isinstance(metadata, str):
                                try:
                                    # If it's already a JSON string, validate it
                                    json.loads(metadata)
                                except:
                                    # If invalid JSON string, reset to empty dict
                                    metadata = {}
                            
                            # Convert dict to JSON string for PostgreSQL JSONB
                            if isinstance(metadata, dict):
                                metadata = json.dumps(metadata)
                            elif metadata is None:
                                metadata = "{}"
                            else:
                                # Unknown type, reset to empty JSON
                                metadata = "{}"
                            
                            await conn.execute("""
                                INSERT INTO contacts (
                                    user_id, email, name, trust_tier, trust_score, 
                                    frequency, last_contact, domain, metadata
                                )
                                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                                ON CONFLICT (user_id, email) DO UPDATE
                                SET 
                                    name = EXCLUDED.name,
                                    trust_tier = EXCLUDED.trust_tier,
                                    trust_score = EXCLUDED.trust_score,
                                    frequency = EXCLUDED.frequency,
                                    last_contact = EXCLUDED.last_contact,
                                    domain = EXCLUDED.domain,
                                    metadata = EXCLUDED.metadata,
                                    updated_at = CURRENT_TIMESTAMP
                            """, 
                            user_id,
                            contact['email'],
                            contact.get('name', ''),
                            contact.get('trust_tier', 'tier_3'),
                            contact.get('trust_score', 0.0),
                            contact.get('frequency', 1),
                            last_contact,  # Just pass as string
                            contact.get('domain', ''),
                            metadata
                            )
                            count += 1
                    logger.info(f"Successfully stored {count} contacts for user {user_id}")
                    return count
                    
            except Exception as e:
                error_msg = str(e)
                if "another operation is in progress" in error_msg and attempt < max_retries - 1:
                    logger.warning(f"Connection pool issue, resetting pool (attempt {attempt + 1})")
                    await self.reset_connection_pool()
                    await asyncio.sleep(1)
                    continue
                else:
                    logger.error(f"Failed to store contacts: {error_msg}")
                    # Add debug info for datetime errors
                    if "datetime" in error_msg.lower() and "timezone" in error_msg.lower():
                        logger.error(f"Contact data causing datetime error: {contacts[:2] if contacts else 'No contacts'}")
                    raise
        
        return 0
    
    async def semantic_email_search(
        self, 
        user_id: int, 
        query_embedding: List[float], 
        limit: int = 10
    ) -> List[Dict]:
        """Search emails using vector similarity"""
        try:
            async with self.conn_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT 
                        id, 
                        gmail_id, 
                        content, 
                        metadata, 
                        embedding <-> $1 as distance
                    FROM emails
                    WHERE user_id = $2
                    ORDER BY distance ASC
                    LIMIT $3
                """, query_embedding, user_id, limit)
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Semantic email search failed: {str(e)}")
            raise

    async def reset_connection_pool(self) -> None:
        """Reset the connection pool if it gets into a bad state"""
        try:
            if self.conn_pool:
                await self.conn_pool.close()
                await asyncio.sleep(1)  # Give it a moment
            await self.connect()
            logger.info("Successfully reset PostgreSQL connection pool")
        except Exception as e:
            logger.error(f"Failed to reset connection pool: {str(e)}")
            raise
