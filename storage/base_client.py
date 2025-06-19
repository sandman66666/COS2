# storage/base_client.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class BaseStorageClient(ABC):
    """Base class for all storage clients"""
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if service is healthy"""
        pass
