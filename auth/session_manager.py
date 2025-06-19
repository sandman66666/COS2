"""
Session Manager for Strategic Intelligence Platform
==================================================
Handles user sessions with secure token management and verification.
"""

import os
import time
import uuid
import json
import logging
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Tuple

import redis
from flask import request, g, session

from utils.logging import get_logger

logger = get_logger(__name__)

class SessionManager:
    """
    Handles user session management with multi-tenant security isolation.
    Provides secure session creation, validation, and expiration.
    """
    
    def __init__(self, redis_url: str = None):
        # Redis client for session storage
        self.redis_client = redis.Redis.from_url(redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        
        # Session configuration
        self.session_expiry = int(os.getenv('SESSION_EXPIRY_SECONDS', 86400))  # 24 hours default
        self.session_prefix = "session:"
        self.secret_key = os.getenv('SESSION_SECRET_KEY', os.urandom(32).hex())
        
    def create_session(self, user_id: str, user_email: str, metadata: Dict = None) -> Tuple[str, Dict]:
        """
        Create a new session for a user
        
        Args:
            user_id: Unique identifier for the user
            user_email: User's email address
            metadata: Additional session metadata
            
        Returns:
            Tuple of (session_id, session_data)
        """
        try:
            # Generate a unique session ID
            session_id = str(uuid.uuid4())
            
            # Current timestamp
            now = int(time.time())
            
            # Session data
            session_data = {
                "user_id": user_id,
                "email": user_email,
                "created_at": now,
                "expires_at": now + self.session_expiry,
                "last_active": now,
                "metadata": metadata or {},
                "ip_address": request.remote_addr if request else None
            }
            
            # Store session in Redis
            self.redis_client.setex(
                f"{self.session_prefix}{session_id}",
                self.session_expiry,
                json.dumps(session_data)
            )
            
            # Generate HMAC for session verification
            session_hmac = self._generate_session_hmac(session_id, user_id)
            session_data['hmac'] = session_hmac
            
            logger.info(f"Created session for user: {user_id}")
            return session_id, session_data
            
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            raise
    
    def validate_session(self, session_id: str, hmac_token: str = None) -> Optional[Dict]:
        """
        Validate a session and return the session data if valid
        
        Args:
            session_id: The session ID to validate
            hmac_token: Optional HMAC token for additional verification
            
        Returns:
            Session data if valid, None otherwise
        """
        try:
            if not session_id:
                return None
                
            # Get session from Redis
            session_data_raw = self.redis_client.get(f"{self.session_prefix}{session_id}")
            if not session_data_raw:
                logger.warning(f"Session not found: {session_id}")
                return None
                
            # Parse session data
            try:
                session_data = json.loads(session_data_raw)
            except json.JSONDecodeError:
                logger.error(f"Invalid session data format: {session_id}")
                return None
                
            # Check if session has expired
            now = int(time.time())
            if session_data.get('expires_at', 0) < now:
                logger.warning(f"Session expired: {session_id}")
                self.delete_session(session_id)
                return None
                
            # Verify HMAC if provided
            if hmac_token:
                user_id = session_data.get('user_id')
                expected_hmac = self._generate_session_hmac(session_id, user_id)
                if not hmac.compare_digest(hmac_token, expected_hmac):
                    logger.warning(f"Invalid session HMAC for session: {session_id}")
                    return None
            
            # Update last active time
            session_data['last_active'] = now
            self.redis_client.setex(
                f"{self.session_prefix}{session_id}",
                self.session_expiry,
                json.dumps(session_data)
            )
            
            return session_data
            
        except Exception as e:
            logger.error(f"Error validating session: {str(e)}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        
        Args:
            session_id: The session ID to delete
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            result = self.redis_client.delete(f"{self.session_prefix}{session_id}")
            return result > 0
        except Exception as e:
            logger.error(f"Error deleting session: {str(e)}")
            return False
    
    def get_user_sessions(self, user_id: str) -> Dict[str, Dict]:
        """
        Get all active sessions for a user
        
        Args:
            user_id: The user ID to get sessions for
            
        Returns:
            Dictionary of session_id -> session_data
        """
        try:
            # Get all keys matching the session prefix
            all_sessions = {}
            for key in self.redis_client.scan_iter(f"{self.session_prefix}*"):
                key_str = key.decode('utf-8')
                session_id = key_str.replace(self.session_prefix, '')
                
                # Get session data
                session_data_raw = self.redis_client.get(key)
                if session_data_raw:
                    session_data = json.loads(session_data_raw)
                    if session_data.get('user_id') == user_id:
                        all_sessions[session_id] = session_data
            
            return all_sessions
            
        except Exception as e:
            logger.error(f"Error getting user sessions: {str(e)}")
            return {}
    
    def extend_session(self, session_id: str, extension_seconds: int = None) -> bool:
        """
        Extend a session's expiry time
        
        Args:
            session_id: The session ID to extend
            extension_seconds: Optional custom extension time
            
        Returns:
            True if extended, False otherwise
        """
        try:
            # Get session data
            session_data_raw = self.redis_client.get(f"{self.session_prefix}{session_id}")
            if not session_data_raw:
                return False
                
            session_data = json.loads(session_data_raw)
            
            # Update expiry time
            now = int(time.time())
            extension = extension_seconds or self.session_expiry
            session_data['expires_at'] = now + extension
            session_data['last_active'] = now
            
            # Save updated session
            self.redis_client.setex(
                f"{self.session_prefix}{session_id}",
                extension,
                json.dumps(session_data)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error extending session: {str(e)}")
            return False
    
    def _generate_session_hmac(self, session_id: str, user_id: str) -> str:
        """
        Generate HMAC for session verification
        
        Args:
            session_id: Session ID
            user_id: User ID
            
        Returns:
            HMAC token as string
        """
        message = f"{session_id}:{user_id}"
        return hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
