"""
Synchronous Storage Manager for Flask Integration
================================================
Eliminates async/sync conflicts by using only synchronous database operations
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
import json
import threading

from storage.postgres_client_sync import PostgresClientSync
from utils.logging import structured_logger as logger

class StorageManagerSync:
    """Synchronous storage manager for Flask"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.postgres = PostgresClientSync()
            self.initialized = False
    
    def initialize(self) -> Dict[str, bool]:
        """Initialize database connections (synchronous)"""
        try:
            with self._lock:
                if not self.initialized:
                    self.postgres.connect()
                    self.initialized = True
                    logger.info("Synchronous storage manager initialized")
                return {"postgres": True, "initialized": True}
        except Exception as e:
            logger.error(f"Storage initialization error: {str(e)}")
            return {"postgres": False, "error": str(e)}
    
    def close_all(self) -> None:
        """Close all database connections"""
        try:
            if hasattr(self, 'postgres'):
                self.postgres.disconnect()
            self.initialized = False
        except Exception as e:
            logger.error(f"Error while closing connections: {str(e)}")
    
    def health_check(self) -> Dict[str, bool]:
        """Check health of storage systems (synchronous)"""
        try:
            postgres_health = self.postgres.health_check()
            return {
                "postgres": postgres_health,
                "all_healthy": postgres_health
            }
        except Exception as e:
            logger.error(f"Health check error: {str(e)}")
            return {"postgres": False, "error": str(e)}
    
    # ===== USER OPERATIONS =====
    
    def create_user(self, email: str, google_id: str) -> Dict:
        """Create a new user or get existing one"""
        try:
            return self.postgres.create_user(email, google_id)
        except Exception as e:
            logger.error(f"Create user error: {str(e)}")
            raise
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email address"""
        try:
            return self.postgres.get_user_by_email(email)
        except Exception as e:
            logger.error(f"Get user by email error: {str(e)}")
            return None
    
    # ===== CONTACT OPERATIONS =====
    
    def store_trusted_contacts(self, user_id: int, contacts: List[Dict]) -> Dict:
        """Store trusted contacts"""
        try:
            stored_count = self.postgres.store_contacts(user_id, contacts)
            logger.info(f"Successfully stored {stored_count} contacts for user {user_id}")
            return {
                'success': True,
                'stored_count': stored_count
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Store trusted contacts error: {error_msg}")
            return {'success': False, 'error': error_msg}
    
    def get_contacts(self, user_id: int, trust_tier: str = None, domain: str = None, 
                    limit: int = 100, offset: int = 0) -> Tuple[List[Dict], int]:
        """Get contacts for user"""
        try:
            return self.postgres.get_contacts(user_id, trust_tier, domain, limit, offset)
        except Exception as e:
            logger.error(f"Get contacts error: {str(e)}")
            return [], 0
    
    def update_contact_metadata(self, user_id: int, email: str, metadata_update: Dict) -> bool:
        """Update contact metadata with enrichment data"""
        try:
            return self.postgres.update_contact_metadata(user_id, email, metadata_update)
        except Exception as e:
            logger.error(f"Update contact metadata error: {str(e)}")
            return False
    
    # ===== KNOWLEDGE TREE OPERATIONS =====
    
    def store_knowledge_tree(self, user_id: int, tree_data: Dict, analysis_type: str = "default") -> bool:
        """Store knowledge tree structure"""
        try:
            return self.postgres.store_knowledge_tree(user_id, tree_data, analysis_type)
        except Exception as e:
            logger.error(f"Store knowledge tree error: {str(e)}")
            return False
    
    def get_knowledge_tree(self, user_id: int, analysis_type: str = "default") -> Optional[Dict]:
        """Get knowledge tree from storage"""
        try:
            return self.postgres.get_knowledge_tree(user_id, analysis_type)
        except Exception as e:
            logger.error(f"Get knowledge tree error: {str(e)}")
            return None
    
    def get_latest_knowledge_tree(self, user_id: int) -> Optional[Dict]:
        """Get the most recent knowledge tree for a user"""
        # For now, just get the default tree
        return self.get_knowledge_tree(user_id, "default")
    
    # ===== EMAIL OPERATIONS =====
    
    def get_emails_for_user(self, user_id: int, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get emails for user"""
        try:
            emails, total = self.postgres.get_emails(user_id, limit, offset)
            # Add total count to response
            for email in emails:
                email['total_count'] = total
            return emails
        except Exception as e:
            logger.error(f"Get emails error: {str(e)}")
            return []

# Global storage manager instance
_storage_manager_sync = None
_storage_lock = threading.Lock()

def get_storage_manager_sync() -> StorageManagerSync:
    """Get singleton storage manager instance (synchronous)"""
    global _storage_manager_sync
    
    if _storage_manager_sync is None:
        with _storage_lock:
            if _storage_manager_sync is None:
                _storage_manager_sync = StorageManagerSync()
                _storage_manager_sync.initialize()
    
    return _storage_manager_sync

def initialize_storage_manager_sync():
    """Initialize the storage manager (synchronous)"""
    storage_manager = get_storage_manager_sync()
    return storage_manager.initialize() 