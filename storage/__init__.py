# storage/__init__.py
# Package initialization for storage modules

# Allow submodules to be imported normally without circular dependencies
# Clients can import directly: from storage.storage_manager_sync import get_storage_manager_sync

__all__ = [
    'storage_manager_sync',
    'storage_manager', 
    'postgres_client_sync',
    'postgres_client'
]
