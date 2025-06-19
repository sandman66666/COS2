#!/usr/bin/env python3
"""
Setup Databases Script
=====================
Initializes all database connections and creates required schemas
for the Personal Strategic Intelligence System.

This script:
1. Creates PostgreSQL tables
2. Initializes ChromaDB collections
3. Sets up Neo4j graph schema
4. Configures Redis for caching

Usage:
    python setup_databases.py [--force] [--verbose]

Options:
    --force    Drop existing databases before creating new ones
    --verbose  Show detailed output
"""

import os
import sys
import logging
import argparse
import asyncio
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import chromadb
from neo4j import GraphDatabase
import redis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("setup_databases")

# Load environment variables
load_dotenv()


async def setup_postgresql(force=False, verbose=False):
    """
    Set up PostgreSQL database with required tables
    """
    logger.info("Setting up PostgreSQL...")
    
    # Connection parameters
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_password = os.getenv("POSTGRES_PASSWORD", "")
    db_name = os.getenv("POSTGRES_DB", "cos_intelligence")
    
    try:
        # Connect to PostgreSQL server
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Drop database if force flag is set
        if force:
            logger.warning(f"Dropping database {db_name}...")
            cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
        
        # Create database if it doesn't exist
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{db_name}'")
        if cursor.fetchone() is None:
            logger.info(f"Creating database {db_name}...")
            cursor.execute(f"CREATE DATABASE {db_name}")
        
        cursor.close()
        conn.close()
        
        # Connect to the created database
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name
        )
        cursor = conn.cursor()
        
        # Define table creation SQL
        table_definitions = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                name VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active_at TIMESTAMP,
                preferences JSONB DEFAULT '{}'
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS emails (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                email_id VARCHAR(255) NOT NULL,
                thread_id VARCHAR(255),
                from_email VARCHAR(255),
                from_name VARCHAR(255),
                to_emails TEXT[],
                cc_emails TEXT[],
                subject TEXT,
                body TEXT,
                sent_at TIMESTAMP,
                received_at TIMESTAMP,
                labels TEXT[],
                importance FLOAT,
                embedding_id VARCHAR(255),
                UNIQUE(user_id, email_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS calendar_events (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                event_id VARCHAR(255) NOT NULL,
                title TEXT,
                description TEXT,
                location TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                attendees JSONB,
                recurrence TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                insights JSONB,
                UNIQUE(user_id, event_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS contacts (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                email VARCHAR(255) NOT NULL,
                name VARCHAR(255),
                company VARCHAR(255),
                title VARCHAR(255),
                first_seen_at TIMESTAMP,
                last_seen_at TIMESTAMP,
                frequency INTEGER DEFAULT 0,
                relationship_score FLOAT,
                profile_data JSONB,
                UNIQUE(user_id, email)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS insights (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                insight_type VARCHAR(50),
                category VARCHAR(50),
                title TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                priority INTEGER,
                source VARCHAR(50),
                metadata JSONB
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                prediction_type VARCHAR(50),
                subject TEXT,
                outcome TEXT,
                probability FLOAT,
                confidence FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                time_horizon VARCHAR(50),
                evidence JSONB,
                actions JSONB
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS emails_user_id_idx ON emails(user_id);
            CREATE INDEX IF NOT EXISTS emails_thread_id_idx ON emails(thread_id);
            CREATE INDEX IF NOT EXISTS emails_sent_at_idx ON emails(sent_at);
            CREATE INDEX IF NOT EXISTS calendar_events_user_id_idx ON calendar_events(user_id);
            CREATE INDEX IF NOT EXISTS calendar_events_start_time_idx ON calendar_events(start_time);
            CREATE INDEX IF NOT EXISTS contacts_user_id_idx ON contacts(user_id);
            CREATE INDEX IF NOT EXISTS contacts_frequency_idx ON contacts(frequency);
            CREATE INDEX IF NOT EXISTS insights_user_id_idx ON insights(user_id);
            CREATE INDEX IF NOT EXISTS predictions_user_id_idx ON predictions(user_id);
            """
        ]
        
        # Create tables
        for table_sql in table_definitions:
            if verbose:
                logger.debug(f"Executing SQL: {table_sql}")
            cursor.execute(table_sql)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("PostgreSQL setup complete.")
        return True
    
    except Exception as e:
        logger.error(f"PostgreSQL setup error: {str(e)}")
        return False


async def setup_chromadb(force=False, verbose=False):
    """
    Set up ChromaDB for vector embeddings storage
    """
    logger.info("Setting up ChromaDB...")
    
    try:
        # ChromaDB persistent directory
        persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")
        
        # Create client
        client = chromadb.PersistentClient(path=persist_dir)
        
        # Define collections
        collections = [
            "email_embeddings",
            "document_embeddings",
            "contact_embeddings"
        ]
        
        # Create or recreate collections
        for collection_name in collections:
            if force and collection_name in [c.name for c in client.list_collections()]:
                logger.warning(f"Deleting existing collection: {collection_name}")
                client.delete_collection(collection_name)
            
            if collection_name not in [c.name for c in client.list_collections()]:
                logger.info(f"Creating collection: {collection_name}")
                client.create_collection(name=collection_name)
                
                if verbose:
                    logger.debug(f"Collection {collection_name} created successfully")
        
        logger.info("ChromaDB setup complete.")
        return True
    
    except Exception as e:
        logger.error(f"ChromaDB setup error: {str(e)}")
        return False


async def setup_neo4j(force=False, verbose=False):
    """
    Set up Neo4j graph database
    """
    logger.info("Setting up Neo4j...")
    
    try:
        # Neo4j connection details
        neo4j_uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        
        # Connect to Neo4j
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
        with driver.session() as session:
            # Clear existing data if force flag is set
            if force:
                logger.warning("Clearing all Neo4j data...")
                session.run("MATCH (n) DETACH DELETE n")
            
            # Create constraints
            constraints = [
                "CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Person) REQUIRE p.email IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Topic) REQUIRE t.name IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (o:Organization) REQUIRE o.name IS UNIQUE"
            ]
            
            for constraint in constraints:
                if verbose:
                    logger.debug(f"Executing Neo4j: {constraint}")
                session.run(constraint)
            
            # Create indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS FOR (p:Person) ON (p.name)",
                "CREATE INDEX IF NOT EXISTS FOR (e:Email) ON (e.email_id)",
                "CREATE INDEX IF NOT EXISTS FOR (m:Meeting) ON (m.event_id)",
                "CREATE INDEX IF NOT EXISTS FOR (t:Topic) ON (t.category)"
            ]
            
            for index in indexes:
                if verbose:
                    logger.debug(f"Executing Neo4j: {index}")
                session.run(index)
        
        driver.close()
        logger.info("Neo4j setup complete.")
        return True
    
    except Exception as e:
        logger.error(f"Neo4j setup error: {str(e)}")
        return False


async def setup_redis(force=False, verbose=False):
    """
    Set up Redis for caching and rate limiting
    """
    logger.info("Setting up Redis...")
    
    try:
        # Redis connection details
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_db = int(os.getenv("REDIS_DB", "0"))
        redis_password = os.getenv("REDIS_PASSWORD", None)
        
        # Connect to Redis
        r = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            decode_responses=True
        )
        
        # Test connection
        ping_result = r.ping()
        if not ping_result:
            logger.error("Failed to connect to Redis")
            return False
        
        # Clear data if force flag is set
        if force:
            logger.warning("Flushing Redis database...")
            r.flushdb()
        
        # Set up key prefixes
        r.set("cos:config:version", "1.0.0")
        r.set("cos:config:initialized", "true")
        
        logger.info("Redis setup complete.")
        return True
    
    except Exception as e:
        logger.error(f"Redis setup error: {str(e)}")
        return False


async def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(description="Set up databases for COS Intelligence System")
    parser.add_argument("--force", action="store_true", help="Force recreation of databases")
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")
    args = parser.parse_args()
    
    logger.info("Starting database setup...")
    
    # Set up each database type
    results = await asyncio.gather(
        setup_postgresql(args.force, args.verbose),
        setup_chromadb(args.force, args.verbose),
        setup_neo4j(args.force, args.verbose),
        setup_redis(args.force, args.verbose),
        return_exceptions=True
    )
    
    # Check for any failures
    success = all(isinstance(r, bool) and r for r in results)
    
    if success:
        logger.info("All database setup completed successfully!")
        return 0
    else:
        logger.error("Some database setup tasks failed. Check logs for details.")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
