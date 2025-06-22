# storage/storage_manager.py
"""
Multi-Database Storage Manager
==============================
Orchestrates PostgreSQL (structured data), ChromaDB (vectors), 
Neo4j (graph), and Redis (cache)
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple
import aiohttp
import numpy as np
import json

from storage.postgres_client import PostgresClient
from storage.vector_client import VectorClient
from storage.graph_client import GraphClient
from storage.cache_client import CacheClient
from utils.logging import structured_logger as logger

class StorageManager:
    """Unified storage manager for the Strategic Intelligence System"""
    
    def __init__(self):
        self.postgres = PostgresClient()
        self.vector_db = VectorClient()
        self.graph_db = GraphClient()
        self.cache = CacheClient()
        
    async def initialize(self) -> Dict[str, bool]:
        """Initialize all database connections"""
        try:
            results = {}
            
            # Connect to all databases in parallel
            tasks = [
                self._safe_connect(self.postgres, "postgres"),
                self._safe_connect(self.vector_db, "vector_db"),
                self._safe_connect(self.graph_db, "graph_db"),
                self._safe_connect(self.cache, "cache")
            ]
            
            # Wait for all to complete
            statuses = await asyncio.gather(*tasks)
            
            for db_name, status in statuses:
                results[db_name] = status
                
            return results
        except Exception as e:
            logger.error(f"Storage initialization error: {str(e)}")
            return {"error": str(e)}
    
    async def _safe_connect(self, client, name: str) -> Tuple[str, bool]:
        """Safely connect to a database with error handling"""
        try:
            await client.connect()
            logger.info(f"Connected to {name}")
            return (name, True)
        except Exception as e:
            logger.error(f"Failed to connect to {name}: {str(e)}")
            return (name, False)
    
    async def close_all(self) -> None:
        """Close all database connections"""
        try:
            await asyncio.gather(
                self.postgres.disconnect(),
                self.vector_db.disconnect(),
                self.graph_db.disconnect(),
                self.cache.disconnect()
            )
        except Exception as e:
            logger.error(f"Error while closing connections: {str(e)}")
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all storage systems"""
        try:
            postgres_health = await self.postgres.health_check()
            vector_health = await self.vector_db.health_check()
            graph_health = await self.graph_db.health_check()
            cache_health = await self.cache.health_check()
            
            return {
                "postgres": postgres_health,
                "vector_db": vector_health,
                "graph_db": graph_health,
                "cache": cache_health,
                "all_healthy": all([
                    postgres_health, 
                    vector_health, 
                    graph_health, 
                    cache_health
                ])
            }
        except Exception as e:
            logger.error(f"Health check error: {str(e)}")
            return {"error": str(e)}
    
    # ===== USER OPERATIONS =====
    
    async def create_user(self, email: str, google_id: str) -> Dict:
        """Create a new user or get existing one"""
        try:
            # Store in PostgreSQL
            user = await self.postgres.create_user(email, google_id)
            
            # Create user node in graph DB
            await self.graph_db.create_user_node(user['id'], email)
            
            # Cache basic user info
            await self.cache.cache_user_data(
                user['id'], 
                'profile', 
                {'email': email, 'google_id': google_id}
            )
            
            return user
        except Exception as e:
            logger.error(f"Create user error: {str(e)}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email address"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Try cache first
                try:
                    cached_user = await self.cache.get_user_data_by_key(f"user_email:{email}")
                    if cached_user:
                        return cached_user
                except Exception as cache_error:
                    logger.warning(f"Cache lookup failed (attempt {attempt + 1}): {cache_error}")
                
                # Ensure PostgreSQL connection is healthy
                if not await self.postgres.health_check():
                    logger.warning(f"PostgreSQL connection unhealthy, resetting pool (attempt {attempt + 1})")
                    await self.postgres.reset_connection_pool()
                    await asyncio.sleep(1)
                
                # Get from PostgreSQL - use pool's built-in acquire timeout
                async with self.postgres.conn_pool.acquire() as conn:
                    row = await asyncio.wait_for(conn.fetchrow("""
                        SELECT id, email, google_id, created_at, updated_at
                        FROM users WHERE email = $1
                    """, email), timeout=15)
                    
                    if not row:
                        return None
                    
                    user_data = {
                        'id': row['id'],
                        'email': row['email'],
                        'google_id': row['google_id'],
                        'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                        'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None
                    }
                    
                    # Cache for future requests (best effort)
                    try:
                        await self.cache.cache_user_data_by_key(
                            f"user_email:{email}", user_data
                        )
                    except Exception as cache_error:
                        logger.warning(f"Failed to cache user data: {cache_error}")
                    
                    return user_data
                    
            except asyncio.TimeoutError:
                logger.warning(f"Database timeout getting user by email (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    try:
                        await self.postgres.reset_connection_pool()
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    except:
                        pass
                else:
                    logger.error(f"Failed to get user by email after {max_retries} attempts due to timeouts")
                    return None
                    
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Get user by email error (attempt {attempt + 1}): {error_msg}")
                
                # Check if this is a retryable error
                if any(phrase in error_msg.lower() for phrase in [
                    "another operation is in progress",
                    "connection was closed",
                    "event loop is closed",
                    "pool is closed",
                    "connection"
                ]) and attempt < max_retries - 1:
                    
                    logger.warning(f"Retryable database error, resetting pool and retrying (attempt {attempt + 1})")
                    try:
                        await self.postgres.reset_connection_pool()
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    except:
                        pass
                else:
                    # Non-retryable error or max retries reached
                    logger.error(f"Non-retryable error or max retries reached: {error_msg}")
                    return None
        
        logger.error(f"Failed to get user by email after {max_retries} attempts")
        return None
    
    # ===== CONTACT OPERATIONS =====
    
    async def store_trusted_contacts(self, user_id: int, contacts: List[Dict]) -> Dict:
        """Store trusted contacts across all databases"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Ensure postgres connection is healthy
                if not await self.postgres.health_check():
                    logger.warning(f"PostgreSQL connection unhealthy, attempting reconnect (attempt {attempt + 1})")
                    await self.postgres.reset_connection_pool()
                
                # Store in PostgreSQL
                stored_count = await self.postgres.store_contacts(user_id, contacts)
                
                # Try to add to graph database (optional - can fail)
                graph_result = {}
                try:
                    graph_result = await self.graph_db.build_relationship_graph(
                        user_id, 
                        contacts, 
                        []  # No email data for initial storage
                    )
                except Exception as graph_error:
                    logger.warning(f"Graph database operation failed: {graph_error}")
                    graph_result = {'status': 'failed', 'error': str(graph_error)}
                
                # Try to invalidate cached contact list (optional - can fail)
                try:
                    await self.cache.invalidate_user_data(user_id, 'contacts')
                    await self.cache.user_update(
                        user_id, 
                        'contacts_updated', 
                        {'count': stored_count}
                    )
                except Exception as cache_error:
                    logger.warning(f"Cache operation failed: {cache_error}")
                
                logger.info(f"Successfully stored {stored_count} contacts for user {user_id}")
                return {
                    'success': True,
                    'stored_count': stored_count,
                    'graph_stats': graph_result,
                    'attempt': attempt + 1
                }
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Store trusted contacts error (attempt {attempt + 1}): {error_msg}")
                
                if attempt < max_retries - 1:
                    # Try to reset connections before retrying
                    try:
                        await self.postgres.reset_connection_pool()
                        await asyncio.sleep(1)
                    except:
                        pass
                else:
                    return {'success': False, 'error': error_msg, 'attempts': max_retries}
        
        return {'success': False, 'error': 'Max retries exceeded', 'attempts': max_retries}
    
    # ===== EMAIL OPERATIONS =====
    
    async def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for text using external service"""
        # TODO: Implement actual embedding generation with OpenAI or other provider
        # This is a simplified placeholder
        embeddings = []
        for _ in range(len(texts)):
            # Generate random embedding of correct dimension for testing
            embedding = list(np.random.random(1536).astype(float))
            embeddings.append(embedding)
        return embeddings
    
    async def store_emails(self, user_id: int, emails: List[Dict]) -> Dict:
        """Store emails with metadata and embeddings"""
        try:
            # Generate embeddings for semantic search
            texts = [
                f"{email.get('subject', '')} {email.get('body_text', '')[:500]}"
                for email in emails
            ]
            embeddings = await self._generate_embeddings(texts)
            
            # First store in vector DB
            vector_result = await self.vector_db.store_email_vectors(
                user_id, 
                emails, 
                embeddings
            )
            
            # Update relationship graph with email data
            graph_result = await self.graph_db.build_relationship_graph(
                user_id, 
                [],  # No new contacts
                emails
            )
            
            # Invalidate email cache
            await self.cache.invalidate_user_data(user_id, 'recent_emails')
            
            # Notify of updates
            await self.cache.user_update(
                user_id, 
                'emails_stored', 
                {'count': len(emails)}
            )
            
            return {
                'success': True,
                'emails_stored': len(emails),
                'vector_result': vector_result,
                'graph_result': graph_result
            }
        except Exception as e:
            logger.error(f"Store emails error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def search_emails_semantic(
        self, 
        user_id: int, 
        query: str, 
        limit: int = 10
    ) -> Dict:
        """Search emails semantically by converting query to embedding"""
        try:
            # Get cached results if available
            cache_key = f"search:{query}:{limit}"
            cached = await self.cache.get_user_data(user_id, cache_key)
            if cached:
                return {
                    'success': True,
                    'results': cached,
                    'cached': True
                }
            
            # Generate embedding for query
            query_embedding = (await self._generate_embeddings([query]))[0]
            
            # Search vector database
            results = await self.vector_db.search_similar_emails(
                user_id,
                query_embedding,
                limit
            )
            
            # Cache results
            await self.cache.cache_user_data(user_id, cache_key, results)
            
            return {
                'success': True,
                'results': results,
                'result_count': len(results)
            }
        except Exception as e:
            logger.error(f"Semantic email search error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # ===== CONTACT NETWORK OPERATIONS =====
    
    async def get_contact_network(self, user_id: int, email: str) -> Dict:
        """Get network graph for a specific contact"""
        try:
            # Try cache first
            cache_key = f"network:{email}"
            cached = await self.cache.get_user_data(user_id, cache_key)
            if cached:
                return {
                    'success': True,
                    'network': cached,
                    'cached': True
                }
            
            # Get from graph database
            network = await self.graph_db.get_contact_network(user_id, email)
            
            # Cache result
            await self.cache.cache_user_data(user_id, cache_key, network)
            
            return {
                'success': True,
                'network': network
            }
        except Exception as e:
            logger.error(f"Get contact network error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # ===== KNOWLEDGE TREE OPERATIONS =====
    
    async def store_knowledge_tree(self, user_id: int, tree_data: Dict, analysis_type: str = "default") -> bool:
        """Store knowledge tree structure in PostgreSQL with analysis type"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Ensure PostgreSQL connection is healthy
                if not await self.postgres.health_check():
                    logger.warning(f"PostgreSQL connection unhealthy, resetting pool (attempt {attempt + 1})")
                    await self.postgres.reset_connection_pool()
                    await asyncio.sleep(1)
                
                # Store directly in PostgreSQL as JSONB - use pool's built-in timeout
                async with self.postgres.conn_pool.acquire() as conn:
                    # Check if tree exists for this analysis type
                    exists = await asyncio.wait_for(conn.fetchval("""
                        SELECT EXISTS(
                            SELECT 1 FROM knowledge_tree 
                            WHERE user_id = $1 AND analysis_type = $2
                        )
                    """, user_id, analysis_type), timeout=15)
                    
                    if exists:
                        # Update existing tree
                        await asyncio.wait_for(conn.execute("""
                            UPDATE knowledge_tree
                            SET tree_data = $1, updated_at = CURRENT_TIMESTAMP
                            WHERE user_id = $2 AND analysis_type = $3
                        """, json.dumps(tree_data), user_id, analysis_type), timeout=30)
                    else:
                        # Create new tree
                        await asyncio.wait_for(conn.execute("""
                            INSERT INTO knowledge_tree (user_id, tree_data, analysis_type)
                            VALUES ($1, $2, $3)
                        """, user_id, json.dumps(tree_data), analysis_type), timeout=30)
                    
                # Invalidate cache (best effort)
                try:
                    await self.cache.invalidate_user_data(user_id, f'knowledge_tree_{analysis_type}')
                except Exception as cache_error:
                    logger.warning(f"Failed to invalidate cache: {cache_error}")
                
                # Notify of update (best effort)
                try:
                    await self.cache.user_update(
                        user_id, 
                        'knowledge_tree_updated', 
                        {'timestamp': tree_data.get('timestamp'), 'analysis_type': analysis_type}
                    )
                except Exception as cache_error:
                    logger.warning(f"Failed to send cache update: {cache_error}")
                
                return True
                
            except asyncio.TimeoutError:
                logger.warning(f"Database timeout storing knowledge tree (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    try:
                        await self.postgres.reset_connection_pool()
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    except:
                        pass
                else:
                    logger.error(f"Failed to store knowledge tree after {max_retries} attempts due to timeouts")
                    return False
                    
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Store knowledge tree error (attempt {attempt + 1}): {error_msg}")
                
                # Check if this is a retryable error
                if any(phrase in error_msg.lower() for phrase in [
                    "another operation is in progress",
                    "connection was closed",
                    "event loop is closed",
                    "pool is closed",
                    "connection"
                ]) and attempt < max_retries - 1:
                    
                    logger.warning(f"Retryable database error, resetting pool and retrying (attempt {attempt + 1})")
                    try:
                        await self.postgres.reset_connection_pool()
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    except:
                        pass
                else:
                    # Non-retryable error or max retries reached
                    logger.error(f"Non-retryable error or max retries reached: {error_msg}")
                    return False
        
        logger.error(f"Failed to store knowledge tree after {max_retries} attempts")
        return False
    
    async def get_knowledge_tree(self, user_id: int, analysis_type: str = "default") -> Optional[Dict]:
        """Get knowledge tree from storage by analysis type"""
        try:
            # Try cache first
            cache_key = f'knowledge_tree_{analysis_type}'
            cached_tree = await self.cache.get_user_data(user_id, cache_key)
            if cached_tree:
                return cached_tree
            
            # Get from PostgreSQL
            async with self.postgres.conn_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT tree_data FROM knowledge_tree 
                    WHERE user_id = $1 AND analysis_type = $2
                """, user_id, analysis_type)
                
                if not row:
                    return None
                
                tree_data = row['tree_data']
                
                # Cache for future requests
                if tree_data:
                    await self.cache.cache_user_data(
                        user_id, cache_key, tree_data
                    )
                
                return tree_data
                
        except Exception as e:
            logger.error(f"Get knowledge tree error: {str(e)}")
            return None

    async def get_latest_knowledge_tree(self, user_id: int) -> Optional[Dict]:
        """Get the most recently updated knowledge tree for a user"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Ensure PostgreSQL connection is healthy
                if not await self.postgres.health_check():
                    logger.warning(f"PostgreSQL connection unhealthy, resetting pool (attempt {attempt + 1})")
                    await self.postgres.reset_connection_pool()
                    await asyncio.sleep(1)
                
                # Get from PostgreSQL - latest by updated_at - use pool's built-in timeout
                async with self.postgres.conn_pool.acquire() as conn:
                    row = await asyncio.wait_for(conn.fetchrow("""
                        SELECT tree_data, analysis_type, updated_at 
                        FROM knowledge_tree 
                        WHERE user_id = $1 
                        ORDER BY updated_at DESC 
                        LIMIT 1
                    """, user_id), timeout=15)
                    
                    if not row:
                        return None
                    
                    tree_data = row['tree_data']
                    
                    # Add metadata about the retrieval
                    if tree_data and isinstance(tree_data, dict):
                        tree_data['_retrieval_metadata'] = {
                            'analysis_type': row['analysis_type'],
                            'last_updated': row['updated_at'].isoformat() if row['updated_at'] else None
                        }
                    
                    return tree_data
                    
            except asyncio.TimeoutError:
                logger.warning(f"Database timeout getting latest knowledge tree (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    try:
                        await self.postgres.reset_connection_pool()
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    except:
                        pass
                else:
                    logger.error(f"Failed to get latest knowledge tree after {max_retries} attempts due to timeouts")
                    return None
                    
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Get latest knowledge tree error (attempt {attempt + 1}): {error_msg}")
                
                # Check if this is a retryable error
                if any(phrase in error_msg.lower() for phrase in [
                    "another operation is in progress",
                    "connection was closed",
                    "event loop is closed",
                    "pool is closed",
                    "connection"
                ]) and attempt < max_retries - 1:
                    
                    logger.warning(f"Retryable database error, resetting pool and retrying (attempt {attempt + 1})")
                    try:
                        await self.postgres.reset_connection_pool()
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    except:
                        pass
                else:
                    # Non-retryable error or max retries reached
                    logger.error(f"Non-retryable error or max retries reached: {error_msg}")
                    return None
        
        logger.error(f"Failed to get latest knowledge tree after {max_retries} attempts")
        return None
    
    async def get_emails_for_user(self, user_id: int, limit: int = 100, time_window_days: int = 30) -> List[Dict]:
        """Get emails for a user with optional time window filtering"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Ensure PostgreSQL connection is healthy
                if not await self.postgres.health_check():
                    logger.warning(f"PostgreSQL connection unhealthy, resetting pool (attempt {attempt + 1})")
                    await self.postgres.reset_connection_pool()
                    await asyncio.sleep(1)
                
                # Calculate date filter for time window
                from datetime import datetime, timedelta
                cutoff_date = datetime.now() - timedelta(days=time_window_days)
                
                # Get emails from PostgreSQL using correct schema
                async with self.postgres.conn_pool.acquire() as conn:
                    rows = await asyncio.wait_for(conn.fetch("""
                        SELECT id, gmail_id, content, metadata, created_at, updated_at
                        FROM emails 
                        WHERE user_id = $1 
                        AND created_at >= $2
                        ORDER BY created_at DESC 
                        LIMIT $3
                    """, user_id, cutoff_date, limit), timeout=30)
                    
                    emails = []
                    for row in rows:
                        try:
                            # Handle metadata that might be dict or JSON string
                            metadata = row['metadata']
                            if isinstance(metadata, str):
                                metadata = json.loads(metadata) if metadata else {}
                            elif not isinstance(metadata, dict):
                                metadata = {}
                        except:
                            metadata = {}
                        
                        # Convert to expected email format
                        email_data = {
                            'id': row['id'],
                            'gmail_id': row['gmail_id'],
                            'sender': metadata.get('from', ''),
                            'recipients': metadata.get('to', []),
                            'subject': metadata.get('subject', ''),
                            'body_text': row['content'] or '',
                            'email_date': row['created_at'].isoformat() if row['created_at'] else None,
                            'thread_id': metadata.get('thread_id', ''),
                            'content': row['content'] or '',
                            'metadata': {
                                'sender': metadata.get('from', ''),
                                'subject': metadata.get('subject', ''),
                                'date': row['created_at'].isoformat() if row['created_at'] else None
                            }
                        }
                        emails.append(email_data)
                    
                    return emails
                    
            except asyncio.TimeoutError:
                logger.warning(f"Database timeout getting emails for user (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    try:
                        await self.postgres.reset_connection_pool()
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    except:
                        pass
                else:
                    logger.error(f"Failed to get emails for user after {max_retries} attempts due to timeouts")
                    return []
                    
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Get emails for user error (attempt {attempt + 1}): {error_msg}")
                
                # Check if this is a retryable error
                if any(phrase in error_msg.lower() for phrase in [
                    "another operation is in progress",
                    "connection was closed",
                    "event loop is closed",
                    "pool is closed",
                    "connection"
                ]) and attempt < max_retries - 1:
                    
                    logger.warning(f"Retryable database error, resetting pool and retrying (attempt {attempt + 1})")
                    try:
                        await self.postgres.reset_connection_pool()
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    except:
                        pass
                else:
                    # Non-retryable error or max retries reached
                    logger.error(f"Non-retryable error or max retries reached: {error_msg}")
                    return []
        
        logger.error(f"Failed to get emails for user after {max_retries} attempts")
        return []


# Global instance for easy access
_storage_manager = None

async def get_storage_manager() -> StorageManager:
    """Get global storage manager instance"""
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = StorageManager()
        await _storage_manager.initialize()
    return _storage_manager

async def initialize_storage_manager():
    """Initialize the global storage manager - alias for get_storage_manager"""
    return await get_storage_manager()

# Create a simple instance that can be imported directly
# This will need to be initialized before use
storage_manager = StorageManager()
