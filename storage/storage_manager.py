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
    
    async def store_knowledge_tree(self, user_id: int, tree_data: Dict) -> bool:
        """Store knowledge tree structure in PostgreSQL"""
        try:
            # Store directly in PostgreSQL as JSONB
            async with self.postgres.conn_pool.acquire() as conn:
                # Check if tree exists
                exists = await conn.fetchval("""
                    SELECT EXISTS(
                        SELECT 1 FROM knowledge_tree WHERE user_id = $1
                    )
                """, user_id)
                
                if exists:
                    # Update existing tree
                    await conn.execute("""
                        UPDATE knowledge_tree
                        SET tree_data = $1, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = $2
                    """, tree_data, user_id)
                else:
                    # Create new tree
                    await conn.execute("""
                        INSERT INTO knowledge_tree (user_id, tree_data)
                        VALUES ($1, $2)
                    """, user_id, tree_data)
                
            # Invalidate cache
            await self.cache.invalidate_user_data(user_id, 'knowledge_tree')
            
            # Notify of update
            await self.cache.user_update(
                user_id, 
                'knowledge_tree_updated', 
                {'timestamp': tree_data.get('timestamp')}
            )
            
            return True
        except Exception as e:
            logger.error(f"Store knowledge tree error: {str(e)}")
            return False


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
