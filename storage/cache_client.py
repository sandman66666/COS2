# storage/cache_client.py
import redis
import json
import logging
from typing import Any, Dict, List, Optional, Union
import asyncio

from storage.base_client import BaseStorageClient
from config.settings import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
from config.constants import CacheTTL
from utils.logging import structured_logger as logger

class CacheClient(BaseStorageClient):
    """Redis client for caching and real-time updates"""
    
    def __init__(self):
        self.host = REDIS_HOST
        self.port = REDIS_PORT
        self.password = REDIS_PASSWORD
        self.client = None
        
    async def connect(self) -> None:
        """Establish connection to Redis"""
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                password=self.password,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            # Verify connection
            self.client.ping()
            logger.info("Connected to Redis", host=self.host, port=self.port)
        except Exception as e:
            logger.error(f"Redis connection error: {str(e)}")
            raise
            
    async def disconnect(self) -> None:
        """Close connection to Redis"""
        if self.client:
            self.client.close()
            self.client = None
            logger.info("Disconnected from Redis")
            
    async def health_check(self) -> bool:
        """Check if Redis is available"""
        try:
            if not self.client:
                await self.connect()
                
            return self.client.ping()
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            return False
    
    async def set_value(
        self, 
        key: str, 
        value: Any, 
        ttl: int = CacheTTL.MEDIUM
    ) -> bool:
        """Set a value in cache with TTL"""
        try:
            if not self.client:
                await self.connect()
                
            # Serialize value if it's not a string
            if not isinstance(value, str):
                value = json.dumps(value)
                
            return self.client.set(key, value, ex=ttl)
        except Exception as e:
            logger.error(f"Redis set failed: {str(e)}")
            return False
            
    async def get_value(self, key: str, default: Any = None) -> Any:
        """Get a value from cache"""
        try:
            if not self.client:
                await self.connect()
                
            value = self.client.get(key)
            
            if value is None:
                return default
                
            # Try to deserialize as JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.error(f"Redis get failed: {str(e)}")
            return default
            
    async def delete_value(self, key: str) -> bool:
        """Delete a value from cache"""
        try:
            if not self.client:
                await self.connect()
                
            return self.client.delete(key) > 0
        except Exception as e:
            logger.error(f"Redis delete failed: {str(e)}")
            return False
            
    async def cache_user_data(
        self, 
        user_id: int, 
        data_type: str, 
        data: Any, 
        ttl: int = CacheTTL.MEDIUM
    ) -> bool:
        """Cache user-specific data with type prefix"""
        key = f"user:{user_id}:{data_type}"
        return await self.set_value(key, data, ttl)
        
    async def get_user_data(
        self, 
        user_id: int, 
        data_type: str, 
        default: Any = None
    ) -> Any:
        """Get user-specific cached data"""
        key = f"user:{user_id}:{data_type}"
        return await self.get_value(key, default)
        
    async def invalidate_user_data(self, user_id: int, data_type: str) -> bool:
        """Invalidate user-specific cached data"""
        key = f"user:{user_id}:{data_type}"
        return await self.delete_value(key)
        
    async def publish_update(self, channel: str, data: Any) -> int:
        """Publish update to a channel"""
        try:
            if not self.client:
                await self.connect()
                
            # Serialize data
            if not isinstance(data, str):
                data = json.dumps(data)
                
            return self.client.publish(channel, data)
        except Exception as e:
            logger.error(f"Redis publish failed: {str(e)}")
            return 0
            
    async def user_update(self, user_id: int, update_type: str, data: Any) -> int:
        """Publish user-specific update"""
        channel = f"user:{user_id}:updates"
        payload = {
            "type": update_type,
            "timestamp": asyncio.get_event_loop().time(),
            "data": data
        }
        return await self.publish_update(channel, payload)
