# api/auth_routes.py
"""
Authentication Routes
====================

Routes for Google OAuth authentication, login, logout, and session management
for the multi-tenant Strategic Intelligence System.
"""

import os
import uuid
import time
from datetime import datetime
import asyncio
from functools import wraps

from flask import (
    Blueprint, session, render_template, redirect, url_for, 
    request, jsonify, make_response, current_app, g
)

from auth.gmail_auth import gmail_auth
from models.user import User, UserCreate, UserManager
from storage.storage_manager import get_storage_manager
from middleware.auth_middleware import get_current_user, require_auth
from utils.logging import structured_logger as logger

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='')

# Async helper for route handlers
def async_route(f):
    """Convert async function to Flask route compatible function"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper

# @auth_bp.route('/')
# def index():
#     """Main index route - redirects to React dashboard if authenticated"""
#     user = get_current_user()
#     if not user:
#         return redirect('/login')
#     
#     # Redirect to React dashboard instead of HTML dashboard
#     return redirect('/react')

@auth_bp.route('/home')
@require_auth
def home():
    """Home page route - redirects to React dashboard"""
    user = get_current_user()
    
    # Redirect to React dashboard instead of old HTML dashboard
    return redirect('/react')

@auth_bp.route('/auth/google')
def google_auth():
    """Initiate Google OAuth flow"""
    try:
        # Clear any existing OAuth state to prevent conflicts
        session.pop('oauth_state', None)
        
        # Generate CSRF token if not present
        if 'csrf_token' not in session:
            session['csrf_token'] = str(uuid.uuid4())
        
        # Generate unique state for security (make it more robust)
        state = f"cos_{str(uuid.uuid4()).replace('-', '')}"
        
        # Get authorization URL from our Gmail auth handler
        auth_url, returned_state = gmail_auth.get_authorization_url(
            user_id=session.get('temp_user_id', 'anonymous'),
            state=state
        )
        
        # Store the actual state returned by the auth handler in session
        session['oauth_state'] = returned_state
        
        # Make session permanent to ensure it persists
        session.permanent = True
        
        logger.info("Generated OAuth authorization URL", state=returned_state)
        
        return redirect(auth_url)
        
    except Exception as e:
        logger.error("Failed to initiate Google OAuth", error=str(e))
        return redirect('/login?error=oauth_init_failed')

@auth_bp.route('/auth/google/callback')
@auth_bp.route('/auth/callback')  # Additional route for compatibility
@async_route
async def google_callback():
    """Handle Google OAuth callback with multi-tenant session management"""
    try:
        # Get authorization code and state
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        if error:
            logger.error("OAuth error returned", error=error)
            return redirect('/login' + f'?error={error}')
        
        if not code:
            logger.error("No authorization code received")
            return redirect('/login' + '?error=no_code')
        
        # Validate state (anti-CSRF) BEFORE clearing session
        expected_state = session.get('oauth_state')
        if state != expected_state:
            logger.error("OAuth state mismatch - potential CSRF attempt", 
                         received=state, expected=expected_state)
            return redirect('/login' + '?error=state_mismatch')
        
        # Handle OAuth callback with Gmail auth handler
        result = gmail_auth.handle_oauth_callback(
            authorization_code=code,
            state=state
        )
        
        if not result.get('success'):
            error_msg = result.get('error', 'Unknown OAuth error')
            logger.error("OAuth callback failed", error=error_msg)
            return redirect('/login' + f'?error=oauth_failed')
        
        # Extract user info from OAuth result
        user_info = result.get('user_info', {})
        credentials = result.get('credentials', {})
        
        user_email = user_info.get('email')
        user_google_id = user_info.get('google_id')
        
        if not user_email:
            logger.error("No email received from OAuth")
            return redirect('/login' + '?error=no_email')
        
        # Create or get user in database to ensure sync routes work
        try:
            storage_manager = await get_storage_manager()
            
            # Check if user exists in database
            existing_user = None
            try:
                async with storage_manager.postgres.conn_pool.acquire() as conn:
                    existing_user = await conn.fetchrow(
                        "SELECT id, email, google_id FROM users WHERE email = $1", 
                        user_email
                    )
            except Exception as e:
                logger.warning(f"Could not check for existing user: {e}")
            
            # Create user if they don't exist
            if not existing_user:
                try:
                    async with storage_manager.postgres.conn_pool.acquire() as conn:
                        user_id = await conn.fetchval("""
                            INSERT INTO users (email, google_id, created_at)
                            VALUES ($1, $2, CURRENT_TIMESTAMP)
                            RETURNING id
                        """, 
                        user_email, 
                        user_google_id
                        )
                        logger.info(f"Created new user in database: {user_email} with ID {user_id}")
                except Exception as e:
                    logger.error(f"Failed to create user in database: {e}")
                    # Continue anyway - the session will work even if DB creation fails
            else:
                logger.info(f"User already exists in database: {user_email} with ID {existing_user['id']}")
        
        except Exception as e:
            logger.error(f"Database operations failed during user creation: {e}")
            # Continue anyway - the session auth will still work
        
        # Clear session AFTER validation and create new authenticated session
        session.clear()
        
        # Store authentication info in session
        session['user_id'] = user_email  # Use email as ID temporarily until DB is connected
        session['user_email'] = user_email
        session['authenticated'] = True
        session['session_id'] = str(uuid.uuid4())
        session['auth_time'] = int(time.time())
        session['oauth_credentials'] = credentials  # Store credentials in session for now
        session['user_name'] = user_info.get('name', user_email)
        session['google_id'] = user_google_id
        
        # Set session to be permanent
        session.permanent = True
        
        logger.info("User authenticated successfully", email=user_email)
        
        # Redirect to React app - use current host to work on both localhost and Heroku
        base_url = request.host_url.rstrip('/')
        response = redirect(f'{base_url}/?login_success=true&authenticated=true&t={int(time.time())}')
        
        # Set auth cookie with the actual access token
        response.set_cookie(
            'auth_token',
            credentials.get('access_token', f"oauth_{int(time.time())}_{user_email}"),
            httponly=True,
            max_age=86400,  # 24 hours
            path='/',
            secure=request.is_secure  # Use HTTPS in production, HTTP in development
        )
        
        # Prevent caching
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        
        return response
        
    except Exception as e:
        logger.error("OAuth callback error", error=str(e))
        return redirect('/login' + '?error=callback_failed')

def create_test_session():
    """DEPRECATED: Removed test session fallback for production"""
    pass

@auth_bp.route('/logout')
def logout():
    """Logout and clear session completely"""
    user_email = session.get('user_email')
    user_id = session.get('user_id')
    
    # Complete session cleanup
    session.clear()
    
    logger.info("User logged out", user_id=user_id, email=user_email)
    
    # Redirect to React app - use current host to work on both localhost and Heroku
    base_url = request.host_url.rstrip('/')
    response = redirect(f'{base_url}/?logged_out=true&t={int(time.time())}')
    
    # Clear auth token cookie
    response.set_cookie('auth_token', '', expires=0, path='/')
    
    # Set cache headers
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

@auth_bp.route('/force-logout')
def force_logout():
    """Force complete logout and session reset - use when switching users"""
    try:
        # Clear current session
        user_email = session.get('user_email', 'unknown')
        user_id = session.get('user_id', 'unknown')
        
        session.clear()
        
        logger.info("Force logout completed", 
                   user_id=user_id, email=user_email)
        
        # Create response with aggressive cache clearing - use current host to work on both localhost and Heroku
        base_url = request.host_url.rstrip('/')
        response = redirect(f'{base_url}/?force_logout=true&t={int(time.time())}')
        
        # Clear all possible cookies and cache
        response.set_cookie('session', '', expires=0, path='/')
        response.set_cookie('auth_token', '', expires=0, path='/')
        
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response.headers['Clear-Site-Data'] = '"cache", "cookies", "storage"'
        
        return response
        
    except Exception as e:
        logger.error("Force logout error", error=str(e))
        return jsonify({'error': 'Force logout failed', 'details': str(e)}), 500

# ===== API Routes =====

@auth_bp.route('/api/auth/status')
def auth_status():
    """Check authentication status"""
    user = get_current_user()
    
    if user and user.get('authenticated'):
        return jsonify({
            'authenticated': True,
            'user': {
                'id': user.get('id'),
                'email': user.get('email')
            }
        })
    
    return jsonify({
        'authenticated': False
    })

@auth_bp.route('/api/auth/token')
@require_auth
def get_token():
    """Get a new JWT token for authenticated user"""
    user = get_current_user()
    
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # In a real implementation, we would fetch the full user from the database
    # This is a simplification for the example
    # We'd also add more claims like roles, permissions, etc.
    
    # Create temporary User instance for token generation
    temp_user = User(
        id=user.get('id'),
        email=user.get('email'),
        google_id=user.get('google_id', '')
    )
    
    user_session = temp_user.create_session_token()
    
    return jsonify({
        'token': user_session.token,
        'expires_at': user_session.expires_at.isoformat()
    })

@auth_bp.route('/debug/oauth-config')
def debug_oauth_config():
    """Debug OAuth configuration - only available in development"""
    # Allow in development mode or when ENV is not explicitly set to production
    env = current_app.config.get('ENV', 'development')
    if env == 'production':
        return jsonify({'error': 'Not available in production'}), 403
    
    from config.settings import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI
    
    return jsonify({
        'client_id_configured': bool(GOOGLE_CLIENT_ID),
        'client_id_length': len(GOOGLE_CLIENT_ID) if GOOGLE_CLIENT_ID else 0,
        'client_id_starts_with': GOOGLE_CLIENT_ID[:20] + '...' if GOOGLE_CLIENT_ID and len(GOOGLE_CLIENT_ID) > 20 else 'Not set',
        'client_secret_configured': bool(GOOGLE_CLIENT_SECRET),
        'client_secret_length': len(GOOGLE_CLIENT_SECRET) if GOOGLE_CLIENT_SECRET else 0,
        'redirect_uri': GOOGLE_REDIRECT_URI,
        'redirect_uri_configured': bool(GOOGLE_REDIRECT_URI),
        'environment': env
    })

@auth_bp.route('/debug/session')
def debug_session():
    """Debug session information - only available in development"""
    # Allow in development mode or when ENV is not explicitly set to production
    env = current_app.config.get('ENV', 'development')
    if env == 'production':
        return jsonify({'error': 'Not available in production'}), 403
        
    return jsonify({
        'session_data': dict(session),
        'user_email': session.get('user_email'),
        'user_id': session.get('user_id'),
        'authenticated': session.get('authenticated'),
        'session_keys': list(session.keys()),
        'headers': dict(request.headers),
        'environment': env
    })
