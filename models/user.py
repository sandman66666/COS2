# models/user.py
"""
User model for multi-tenant functionality
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import jwt
from pydantic import BaseModel, EmailStr, Field

from config.settings import API_SECRET_KEY
from utils.logging import structured_logger as logger

class UserCreate(BaseModel):
    """User creation schema"""
    email: EmailStr
    google_id: str

class UserProfile(BaseModel):
    """User profile data"""
    name: Optional[str] = None
    picture: Optional[str] = None
    locale: Optional[str] = None

class UserSession(BaseModel):
    """User session information"""
    token: str
    expires_at: datetime

class UserSettings(BaseModel):
    """User configurable settings"""
    notification_email: bool = True
    notification_web: bool = True
    theme: str = "light"
    language: str = "en"
    timezone: str = "UTC"

class User:
    """User model with multi-tenant functionality"""
    
    def __init__(
        self, 
        id: int, 
        email: str, 
        google_id: str, 
        profile: Optional[Dict] = None,
        settings: Optional[Dict] = None,
        created_at: Optional[datetime] = None
    ):
        self.id = id
        self.email = email
        self.google_id = google_id
        self.profile = profile or {}
        self.settings = settings or {}
        self.created_at = created_at or datetime.utcnow()
        
    @classmethod
    def from_db_row(cls, row: Dict) -> 'User':
        """Create User instance from database row"""
        return cls(
            id=row['id'],
            email=row['email'],
            google_id=row['google_id'],
            profile=row.get('profile', {}),
            settings=row.get('settings', {}),
            created_at=row.get('created_at')
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation"""
        return {
            'id': self.id,
            'email': self.email,
            'profile': self.profile,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def create_session_token(self, expires_in: int = 86400) -> UserSession:
        """Create JWT session token for authentication"""
        now = datetime.utcnow()
        expires_at = now + timedelta(seconds=expires_in)
        
        payload = {
            'sub': str(self.id),
            'email': self.email,
            'iat': int(now.timestamp()),
            'exp': int(expires_at.timestamp())
        }
        
        token = jwt.encode(payload, API_SECRET_KEY, algorithm='HS256')
        
        return UserSession(
            token=token,
            expires_at=expires_at
        )
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, API_SECRET_KEY, algorithms=['HS256'])
            return payload
        except jwt.PyJWTError as e:
            logger.error(f"Token verification failed: {str(e)}")
            return None

class UserManager:
    """Manager for user operations with multi-tenant support"""
    
    def __init__(self, storage_manager):
        self.storage = storage_manager
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        try:
            # Try cache first
            cached_user = await self.storage.cache.get_value(f"user:{user_id}")
            if cached_user:
                return User(**cached_user)
            
            # Get from database
            async with self.storage.postgres.conn_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT id, email, google_id, 
                           profile, settings, created_at
                    FROM users 
                    WHERE id = $1
                """, user_id)
                
                if not row:
                    return None
                    
                user = User.from_db_row(dict(row))
                
                # Cache user
                await self.storage.cache.set_value(
                    f"user:{user_id}", 
                    user.to_dict()
                )
                
                return user
                
        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            return None
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            async with self.storage.postgres.conn_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT id, email, google_id, 
                           profile, settings, created_at
                    FROM users 
                    WHERE email = $1
                """, email)
                
                if not row:
                    return None
                    
                user = User.from_db_row(dict(row))
                
                # Cache user
                await self.storage.cache.set_value(
                    f"user:{user.id}", 
                    user.to_dict()
                )
                
                return user
                
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            return None
    
    async def create_user(self, data: UserCreate, profile: Optional[Dict] = None) -> Optional[User]:
        """Create a new user"""
        try:
            async with self.storage.postgres.conn_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    INSERT INTO users (email, google_id, profile)
                    VALUES ($1, $2, $3)
                    RETURNING id, email, google_id, profile, settings, created_at
                """, data.email, data.google_id, json.dumps(profile or {}))
                
                if not row:
                    return None
                
                user = User.from_db_row(dict(row))
                
                # Create user node in graph database
                await self.storage.graph_db.create_user_node(user.id, user.email)
                
                # Cache user
                await self.storage.cache.set_value(
                    f"user:{user.id}", 
                    user.to_dict()
                )
                
                return user
                
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return None
    
    async def update_profile(self, user_id: int, profile_data: Dict) -> Optional[User]:
        """Update user profile"""
        try:
            async with self.storage.postgres.conn_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    UPDATE users
                    SET profile = $1
                    WHERE id = $2
                    RETURNING id, email, google_id, profile, settings, created_at
                """, json.dumps(profile_data), user_id)
                
                if not row:
                    return None
                
                user = User.from_db_row(dict(row))
                
                # Invalidate cache
                await self.storage.cache.delete_value(f"user:{user_id}")
                
                return user
                
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            return None
    
    async def update_settings(self, user_id: int, settings_data: Dict) -> Optional[User]:
        """Update user settings"""
        try:
            async with self.storage.postgres.conn_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    UPDATE users
                    SET settings = $1
                    WHERE id = $2
                    RETURNING id, email, google_id, profile, settings, created_at
                """, json.dumps(settings_data), user_id)
                
                if not row:
                    return None
                
                user = User.from_db_row(dict(row))
                
                # Invalidate cache
                await self.storage.cache.delete_value(f"user:{user_id}")
                
                return user
                
        except Exception as e:
            logger.error(f"Error updating user settings: {str(e)}")
            return None
    
    async def list_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """List all users (admin function)"""
        try:
            async with self.storage.postgres.conn_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT id, email, google_id, profile, settings, created_at
                    FROM users
                    ORDER BY created_at DESC
                    LIMIT $1 OFFSET $2
                """, limit, offset)
                
                users = [User.from_db_row(dict(row)) for row in rows]
                return users
                
        except Exception as e:
            logger.error(f"Error listing users: {str(e)}")
            return []
