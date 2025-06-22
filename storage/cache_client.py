# storage/cache_client.py
import json
import redis.asyncio as redis
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
        self.redis = None
        
    async def connect(self) -> None:
        """Establish connection to Redis"""
        try:
            # Close existing connection if any
            if self.redis:
                await self.redis.close()
                
            self.redis = redis.Redis(
                host=self.host,
                port=self.port,
                password=self.password,
                decode_responses=True,
                socket_timeout=10,
                socket_connect_timeout=10,
                retry_on_timeout=True,
                max_connections=20
            )
            # Verify connection
            await self.redis.ping()
            logger.info("Connected to Redis", host=self.host, port=self.port)
        except Exception as e:
            logger.error(f"Redis connection error: {str(e)}")
            raise
            
    async def disconnect(self) -> None:
        """Close connection to Redis"""
        if self.redis:
            await self.redis.close()
            self.redis = None
            logger.info("Disconnected from Redis")
            
    async def health_check(self) -> bool:
        """Check if Redis is available"""
        try:
            if not self.redis:
                await self.connect()
                
            return await self.redis.ping()
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
            if not self.redis:
                await self.connect()
                
            # Serialize value if it's not a string
            if not isinstance(value, str):
                value = json.dumps(value)
                
            result = await self.redis.set(key, value, ex=ttl)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis set failed for key {key}: {str(e)}")
            return False
            
    async def get_value(self, key: str, default: Any = None) -> Any:
        """Get a value from cache"""
        try:
            if not self.redis:
                await self.connect()
                
            value = await self.redis.get(key)
            
            if value is None:
                return default
                
            # Try to deserialize as JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.error(f"Redis get failed for key {key}: {str(e)}")
            return default
            
    async def delete_value(self, key: str) -> bool:
        """Delete a value from cache"""
        try:
            if not self.redis:
                await self.connect()
                
            result = await self.redis.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis delete failed for key {key}: {str(e)}")
            return False
            
    async def cache_user_data(self, user_id: int, data_type: str, data: Any) -> bool:
        """Cache user-specific data"""
        try:
            if not self.redis:
                await self.connect()
                
            key = f"user:{user_id}:{data_type}"
            result = await self.redis.setex(key, 3600, json.dumps(data))  # 1 hour TTL
            return bool(result)
        except Exception as e:
            logger.error(f"Cache user data error for user {user_id}, type {data_type}: {str(e)}")
            return False

    async def get_user_data(self, user_id: int, data_type: str) -> Optional[Any]:
        """Get cached user data"""
        try:
            if not self.redis:
                await self.connect()
                
            key = f"user:{user_id}:{data_type}"
            cached = await self.redis.get(key)
            if cached:
                return json.loads(cached)
            return None
        except Exception as e:
            logger.error(f"Get cached user data error for user {user_id}, type {data_type}: {str(e)}")
            return None

    async def cache_user_data_by_key(self, cache_key: str, data: Any) -> bool:
        """Cache data using a custom key"""
        try:
            if not self.redis:
                await self.connect()
                
            result = await self.redis.setex(cache_key, 3600, json.dumps(data))  # 1 hour TTL
            return bool(result)
        except Exception as e:
            logger.error(f"Cache data by key error for key {cache_key}: {str(e)}")
            return False

    async def get_user_data_by_key(self, cache_key: str) -> Optional[Any]:
        """Get cached data using a custom key"""
        try:
            if not self.redis:
                await self.connect()
                
            cached = await self.redis.get(cache_key)
            if cached:
                return json.loads(cached)
            return None
        except Exception as e:
            logger.error(f"Get cached data by key error for key {cache_key}: {str(e)}")
            return None
        
    async def invalidate_user_data(self, user_id: int, data_type: str) -> bool:
        """Invalidate user-specific cached data"""
        key = f"user:{user_id}:{data_type}"
        return await self.delete_value(key)
        
    async def publish_update(self, channel: str, data: Any) -> int:
        """Publish update to a channel"""
        try:
            if not self.redis:
                await self.connect()
                
            # Serialize data
            if not isinstance(data, str):
                data = json.dumps(data)
                
            result = await self.redis.publish(channel, data)
            return result
        except Exception as e:
            logger.error(f"Redis publish failed for channel {channel}: {str(e)}")
            return 0
            
    async def user_update(self, user_id: int, update_type: str, data: Any) -> int:
        """Publish user-specific update"""
        try:
            channel = f"user:{user_id}:updates"
            payload = {
                "type": update_type,
                "timestamp": asyncio.get_event_loop().time(),
                "data": data
            }
            return await self.publish_update(channel, payload)
        except Exception as e:
            logger.error(f"User update failed for user {user_id}: {str(e)}")
            return 0
