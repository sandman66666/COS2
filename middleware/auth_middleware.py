# middleware/auth_middleware.py
"""
Authentication Middleware
========================
Middleware for validating user sessions, checking authentication,
and enforcing multi-tenant isolation.
"""

import jwt
import time
from functools import wraps
from typing import Dict, Optional, Callable, Any

from flask import request, session, g, jsonify, redirect, url_for, current_app

from models.user import User, UserManager
from utils.logging import structured_logger as logger
from storage.storage_manager import get_storage_manager

def get_current_user() -> Optional[Dict]:
    """
    Get the currently authenticated user from the session
    
    Returns:
        Dict containing user information or None if not authenticated
    """
    # Check if user is already in request context
    if hasattr(g, 'user') and g.user:
        return g.user
    
    # Check if user_id is in session
    user_id = session.get('user_id')
    if not user_id:
        return None
    
    # Return minimal user info from session
    return {
        'id': user_id,
        'email': session.get('user_email'),
        'authenticated': session.get('authenticated', False)
    }

async def load_user_from_token(token: str) -> Optional[Dict]:
    """
    Validate JWT token and load user
    
    Args:
        token: JWT token
        
    Returns:
        User dict if token valid, None otherwise
    """
    try:
        # Verify token
        payload = User.verify_token(token)
        if not payload:
            return None
        
        # Get user ID from token
        user_id = int(payload.get('sub'))
        if not user_id:
            return None
        
        # Get storage manager
        storage_manager = await get_storage_manager()
        
        # Create user manager with storage access
        user_manager = UserManager(storage_manager)
        
        # Get user from database
        user = await user_manager.get_user(user_id)
        if not user:
            return None
        
        return user.to_dict()
    
    except Exception as e:
        logger.error(f"Error loading user from token: {str(e)}")
        return None

def require_auth(f: Callable) -> Callable:
    """
    Decorator to require authentication on API routes
    
    Args:
        f: Flask route function to wrap
        
    Returns:
        Wrapped function that checks authentication
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Allow certain routes without authentication
        allowed_paths = ['/api/health', '/api/system/health', '/static']
        
        # Check if this is an allowed path
        if any(request.path.startswith(path) for path in allowed_paths):
            return f(*args, **kwargs)
        
        # Check if user is authenticated from session
        user = get_current_user()
        
        if not user or not user.get('authenticated', False):
            # Try to get from Authorization header for API
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                
                # We need to handle async token validation in sync context
                import asyncio
                user = asyncio.run(load_user_from_token(token))
                
                if user:
                    # Store in request context for this request
                    g.user = user
                    return f(*args, **kwargs)
            
            # Not authenticated - API routes return 401, web routes redirect
            if request.path.startswith('/api/'):
                return jsonify({
                    'error': 'Authentication required',
                    'status': 'unauthorized'
                }), 401
            else:
                return redirect(url_for('auth.login'))
        
        # User is authenticated
        return f(*args, **kwargs)
    
    return decorated

def api_key_auth(f: Callable) -> Callable:
    """
    Decorator for API key authentication on machine-to-machine endpoints
    
    Args:
        f: Flask route function to wrap
        
    Returns:
        Wrapped function that checks API key authentication
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Get API key from header or query parameter
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key:
            return jsonify({
                'error': 'API key required', 
                'status': 'unauthorized'
            }), 401
            
        # Check if API key is valid (would use database lookup in production)
        # For a real implementation, we'd validate against stored API keys in the database
        # This is just a placeholder for the structure
        if api_key != current_app.config.get('API_KEY'):
            logger.warning("Invalid API key attempt", 
                           ip=request.remote_addr, 
                           path=request.path)
            return jsonify({
                'error': 'Invalid API key',
                'status': 'forbidden'
            }), 403
            
        return f(*args, **kwargs)
        
    return decorated

class RateLimiter:
    """Simple in-memory rate limiter for API endpoints"""
    
    def __init__(self):
        self.requests = {}  # Store request counts
        self.RATE_LIMIT = 60  # requests per minute
        self.WINDOW = 60  # seconds
        
    def is_rate_limited(self, key: str) -> bool:
        """Check if a key (user, IP) is rate limited"""
        current_time = int(time.time())
        window_start = current_time - self.WINDOW
        
        # Clean old entries
        self.requests = {k: v for k, v in self.requests.items() 
                       if v.get('timestamp', 0) >= window_start}
        
        # Get or create record
        record = self.requests.get(key, {'count': 0, 'timestamp': current_time})
        
        # Only rate limit if over threshold
        if record['count'] > self.RATE_LIMIT:
            return True
            
        # Update count
        record['count'] = record.get('count', 0) + 1
        record['timestamp'] = current_time
        self.requests[key] = record
        
        return False

# Create global rate limiter
rate_limiter = RateLimiter()

def rate_limit(f: Callable) -> Callable:
    """
    Decorator for rate limiting API requests
    
    Args:
        f: Flask route function to wrap
        
    Returns:
        Wrapped function with rate limiting
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Get key based on user ID or IP
        user = get_current_user()
        if user and user.get('id'):
            key = f"user:{user.get('id')}"
        else:
            key = f"ip:{request.remote_addr}"
        
        # Check if rate limited
        if rate_limiter.is_rate_limited(key):
            logger.warning("Rate limit exceeded", key=key, path=request.path)
            return jsonify({
                'error': 'Rate limit exceeded',
                'status': 'too_many_requests'
            }), 429
            
        return f(*args, **kwargs)
        
    return decorated
