#!/usr/bin/env python3
"""
Test Database Connections
========================
Validates connections to all databases used by the Personal Strategic Intelligence System.

This script:
1. Tests PostgreSQL connection
2. Tests ChromaDB connection
3. Tests Neo4j connection
4. Tests Redis connection

Usage:
    python test_connection.py [--verbose]

Options:
    --verbose  Show detailed connection information
"""

import os
import sys
import logging
import argparse
import asyncio
from dotenv import load_dotenv
import psycopg2
import chromadb
from neo4j import GraphDatabase
import redis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("test_connection")

# Load environment variables
load_dotenv()


async def test_postgresql(verbose=False):
    """Test PostgreSQL connection"""
    logger.info("Testing PostgreSQL connection...")
    
    # Connection parameters
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_password = os.getenv("POSTGRES_PASSWORD", "")
    db_name = os.getenv("POSTGRES_DB", "cos_intelligence")
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name
        )
        
        # Test connection
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        if verbose:
            logger.info(f"PostgreSQL version: {version}")
        
        logger.info("✓ PostgreSQL connection successful")
        return True, version
    
    except Exception as e:
        logger.error(f"✗ PostgreSQL connection error: {str(e)}")
        return False, str(e)


async def test_chromadb(verbose=False):
    """Test ChromaDB connection"""
    logger.info("Testing ChromaDB connection...")
    
    try:
        # ChromaDB persistent directory
        persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")
        
        # Create client
        client = chromadb.PersistentClient(path=persist_dir)
        
        # Test by listing collections
        collections = client.list_collections()
        collection_names = [c.name for c in collections]
        
        if verbose:
            logger.info(f"ChromaDB collections: {', '.join(collection_names) or 'None'}")
        
        logger.info("✓ ChromaDB connection successful")
        return True, collection_names
    
    except Exception as e:
        logger.error(f"✗ ChromaDB connection error: {str(e)}")
        return False, str(e)


async def test_neo4j(verbose=False):
    """Test Neo4j connection"""
    logger.info("Testing Neo4j connection...")
    
    try:
        # Neo4j connection details
        neo4j_uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        
        # Connect to Neo4j
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
        # Test connection
        with driver.session() as session:
            result = session.run("CALL dbms.components() YIELD name, versions RETURN name, versions")
            record = result.single()
            version_info = f"{record['name']} {record['versions'][0]}" if record else "Unknown"
        
        driver.close()
        
        if verbose:
            logger.info(f"Neo4j version: {version_info}")
        
        logger.info("✓ Neo4j connection successful")
        return True, version_info
    
    except Exception as e:
        logger.error(f"✗ Neo4j connection error: {str(e)}")
        return False, str(e)


async def test_redis(verbose=False):
    """Test Redis connection"""
    logger.info("Testing Redis connection...")
    
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
        info = r.info("server")
        version = info.get("redis_version", "Unknown")
        
        if verbose:
            logger.info(f"Redis version: {version}")
        
        logger.info("✓ Redis connection successful")
        return True, version
    
    except Exception as e:
        logger.error(f"✗ Redis connection error: {str(e)}")
        return False, str(e)


async def main():
    """Main test function"""
    parser = argparse.ArgumentParser(description="Test database connections for COS Intelligence System")
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")
    args = parser.parse_args()
    
    logger.info("Starting connection tests...")
    
    # Test each database type
    results = await asyncio.gather(
        test_postgresql(args.verbose),
        test_chromadb(args.verbose),
        test_neo4j(args.verbose),
        test_redis(args.verbose),
        return_exceptions=True
    )
    
    # Summarize results
    success_count = 0
    for i, result in enumerate(results):
        if isinstance(result, tuple) and result[0]:
            success_count += 1
    
    logger.info(f"\nConnection Test Summary: {success_count}/4 successful connections")
    
    if success_count == 4:
        logger.info("All connections successful!")
        return 0
    else:
        logger.error("Some connections failed. Please check the logs above.")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
