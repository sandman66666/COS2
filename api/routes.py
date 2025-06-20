# api/routes.py
"""
API Routes for Strategic Intelligence System
===========================================
REST API routes for Gmail integration, contacts, and intelligence endpoints.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import functools
import json

from flask import Blueprint, request, jsonify, current_app, g
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
import google.auth.exceptions

from config.settings import (
    GOOGLE_CLIENT_ID, 
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    GOOGLE_SCOPES
)
from utils.logging import structured_logger as logger
from middleware.auth_middleware import require_auth, api_key_auth, rate_limit
from storage.storage_manager import get_storage_manager
from storage.postgres_client import PostgresClient
from gmail.client import GmailClient
from gmail.analyzer import SentEmailAnalyzer, analyze_user_contacts
from intelligence.claude_intelligent_augmentation import get_claude_intelligent_augmentation

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Async helper for route handlers
def async_route(f):
    """Convert async function to Flask route compatible function"""
    @functools.wraps(f)  # This preserves the original function name
    @require_auth  # All API routes require authentication
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper

def async_route_no_auth(f):
    """Convert async function to Flask route compatible function - no auth for testing"""
    @functools.wraps(f)  # This preserves the original function name
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper

# === Health Check ===

@api_bp.route('/health')
def health_check():
    """Simple health check endpoint - no auth required"""
    return jsonify({
        'status': 'healthy',
        'service': 'strategic_intelligence_api',
        'timestamp': datetime.utcnow().isoformat()
    })

@api_bp.route('/system/health')
@async_route
async def system_health():
    """Detailed system health check"""
    try:
        storage_manager = await get_storage_manager()
        health_status = await storage_manager.health_check()
        
        return jsonify({
            'status': 'healthy' if health_status.get('all_healthy') else 'degraded',
            'components': health_status,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@api_bp.route('/system/flush', methods=['POST'])
@async_route
async def flush_system():
    """
    Flush all user data and start clean
    WARNING: This permanently deletes all user data
    """
    from flask import session
    user_email = session.get('user_id')  # This is actually the email
    
    # For testing - provide a default user
    if not user_email:
        user_email = 'test@session-42.com'
        logger.info("No session user found, using test user")
    
    cleared_items = []
    
    try:
        # Get storage manager first
        storage_manager = await get_storage_manager()
        
        # 1. Get the actual user ID from the email
        user_id = None
        if user_email and storage_manager.postgres:
            try:
                async with storage_manager.postgres.conn_pool.acquire() as conn:
                    user_row = await conn.fetchrow("""
                        SELECT id FROM users WHERE email = $1
                    """, user_email)
                    if user_row:
                        user_id = user_row['id']
                        logger.info(f"Found user ID {user_id} for email {user_email}")
            except Exception as e:
                logger.warning(f"Could not lookup user ID: {e}")
        
        # 2. Clear session data
        session.clear()
        cleared_items.append("Session data cleared")
        
        # 3. COMPREHENSIVE Redis cache clearing
        if storage_manager.cache:
            try:
                # Clear ALL possible cache keys for both email and user_id
                cache_keys_to_clear = []
                
                # For email-based keys
                if user_email:
                    cache_keys_to_clear.extend([
                        f"trusted_contacts:{user_email}",
                        f"knowledge_tree:{user_email}",
                        f"oauth_creds:{user_email}",
                        f"user_data:{user_email}",
                        f"email_analysis:{user_email}",
                        f"contacts_cache:{user_email}",
                        f"gmail_cache:{user_email}",
                        f"sent_emails:{user_email}",
                        f"user:{user_email}:trusted_contacts",
                        f"user:{user_email}:knowledge_tree",
                        f"user:{user_email}:oauth_creds",
                        f"user:{user_email}:profile"
                    ])
                
                # For user_id-based keys  
                if user_id:
                    cache_keys_to_clear.extend([
                        f"trusted_contacts:{user_id}",
                        f"knowledge_tree:{user_id}",
                        f"oauth_creds:{user_id}",
                        f"user_data:{user_id}",
                        f"email_analysis:{user_id}",
                        f"contacts_cache:{user_id}",
                        f"gmail_cache:{user_id}",
                        f"sent_emails:{user_id}",
                        f"user:{user_id}:trusted_contacts",
                        f"user:{user_id}:knowledge_tree",
                        f"user:{user_id}:oauth_creds",
                        f"user:{user_id}:profile",
                        f"network:{user_id}",
                        f"analysis:{user_id}"
                    ])
                
                # Clear all cache keys using the cache client methods
                cleared_count = 0
                for key in cache_keys_to_clear:
                    try:
                        await storage_manager.cache.delete_value(key)
                        cleared_count += 1
                    except:
                        pass
                
                # Also try to clear using direct Redis access if available
                if hasattr(storage_manager.cache, 'client') and storage_manager.cache.client:
                    # Clear all user-related keys using pattern matching
                    if user_email:
                        try:
                            # Use SCAN to find keys containing the email
                            cursor = 0
                            while True:
                                cursor, keys = storage_manager.cache.client.scan(cursor, match=f"*{user_email}*", count=100)
                                if keys:
                                    storage_manager.cache.client.delete(*keys)
                                    cleared_count += len(keys)
                                if cursor == 0:
                                    break
                        except Exception as e:
                            logger.warning(f"Pattern delete failed for email: {e}")
                    
                    if user_id:
                        try:
                            # Use SCAN to find keys containing the user_id  
                            cursor = 0
                            while True:
                                cursor, keys = storage_manager.cache.client.scan(cursor, match=f"*{user_id}*", count=100)
                                if keys:
                                    storage_manager.cache.client.delete(*keys)
                                    cleared_count += len(keys)
                                if cursor == 0:
                                    break
                        except Exception as e:
                            logger.warning(f"Pattern delete failed for user_id: {e}")
                
                cleared_items.append(f"Redis cache cleared ({cleared_count} keys)")
                
            except Exception as cache_error:
                logger.warning("Failed to clear cache", error=str(cache_error))
                cleared_items.append(f"Cache clear failed: {cache_error}")
        
        # 4. Clear PostgreSQL data with proper user ID handling
        if storage_manager.postgres and user_id:
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Ensure connection is healthy
                    if not await storage_manager.postgres.health_check():
                        await storage_manager.postgres.reset_connection_pool()
                    
                    async with storage_manager.postgres.conn_pool.acquire() as conn:
                        async with conn.transaction():
                            # Clear contacts
                            deleted_contacts = await conn.execute("""
                                DELETE FROM contacts WHERE user_id = $1
                            """, user_id)
                            
                            # Clear emails
                            deleted_emails = await conn.execute("""
                                DELETE FROM emails WHERE user_id = $1
                            """, user_id)
                            
                            # Clear knowledge trees
                            deleted_trees = await conn.execute("""
                                DELETE FROM knowledge_tree WHERE user_id = $1
                            """, user_id)
                            
                            # Clear oauth credentials
                            deleted_oauth = await conn.execute("""
                                DELETE FROM oauth_credentials WHERE user_id = $1
                            """, user_id)
                            
                            # Clear user settings (but keep user record)
                            await conn.execute("""
                                UPDATE users SET settings = '{}', updated_at = CURRENT_TIMESTAMP
                                WHERE id = $1
                            """, user_id)
                            
                            cleared_items.extend([
                                f"PostgreSQL contacts cleared (user_id: {user_id})",
                                f"PostgreSQL emails cleared (user_id: {user_id})", 
                                f"PostgreSQL knowledge trees cleared (user_id: {user_id})",
                                f"PostgreSQL OAuth credentials cleared (user_id: {user_id})",
                                f"User settings reset (user_id: {user_id})"
                            ])
                            break  # Success, exit retry loop
                            
                except Exception as db_error:
                    error_msg = str(db_error)
                    if ("another operation is in progress" in error_msg.lower() or 
                        "event loop is closed" in error_msg.lower()) and attempt < max_retries - 1:
                        
                        logger.warning(f"DB connection issue on flush attempt {attempt + 1}, retrying: {error_msg}")
                        try:
                            await storage_manager.postgres.reset_connection_pool()
                        except:
                            pass
                        await asyncio.sleep(1)
                        continue
                    else:
                        logger.warning("Failed to clear PostgreSQL data", error=str(db_error))
                        cleared_items.append(f"PostgreSQL clear failed: {db_error}")
                        break
        else:
            cleared_items.append("PostgreSQL clear skipped (no user_id or connection)")
        
        # 5. Clear Neo4j data (if available)
        if storage_manager and hasattr(storage_manager, 'graph') and storage_manager.graph and user_id:
            try:
                async with storage_manager.graph.driver.session() as neo4j_session:
                    await neo4j_session.run("""
                        MATCH (n {user_id: $user_id})
                        DETACH DELETE n
                    """, user_id=user_id)
                    cleared_items.append(f"Neo4j graph data cleared (user_id: {user_id})")
            except Exception as graph_error:
                cleared_items.append(f"Neo4j clear failed: {graph_error}")
        else:
            cleared_items.append("Neo4j clear skipped (not configured)")
        
        # 6. Clear ChromaDB embeddings (if available)
        if storage_manager and hasattr(storage_manager, 'vector') and storage_manager.vector and user_id:
            try:
                collection_name = f"user_{user_id}_emails"
                try:
                    collection = storage_manager.vector.client.get_collection(collection_name)
                    storage_manager.vector.client.delete_collection(collection_name)
                    cleared_items.append(f"ChromaDB embeddings cleared (collection: {collection_name})")
                except:
                    cleared_items.append("ChromaDB clear skipped (collection didn't exist)")
            except Exception as vector_error:
                cleared_items.append(f"ChromaDB clear failed: {vector_error}")
        else:
            cleared_items.append("ChromaDB clear skipped (not configured)")
        
        logger.info("COMPREHENSIVE system flush completed", 
                   user_email=user_email, user_id=user_id, cleared_items=cleared_items)
        
        return jsonify({
            'success': True,
            'message': 'System completely flushed - all data cleared!',
            'cleared': cleared_items,
            'user_email': user_email,
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat(),
            'note': 'Please refresh your browser and re-authenticate'
        })
        
    except Exception as e:
        logger.error("System flush failed", user_email=user_email, error=str(e))
        return jsonify({
            'success': False,
            'error': str(e),
            'cleared': cleared_items,  # Show what was cleared before the error
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# === User Data Routes ===

@api_bp.route('/user/profile')
@require_auth
def get_user_profile():
    """Get current user profile"""
    from flask import session
    user_id = session.get('user_id')
    
    return jsonify({
        'id': user_id,
        'email': session.get('user_email'),
        'authenticated': True,
        'session_id': session.get('session_id')
    })

@api_bp.route('/user/settings', methods=['GET'])
@async_route
async def get_user_settings():
    """Get user settings"""
    from flask import session
    user_id = session.get('user_id')
    
    # Get storage manager
    storage_manager = await get_storage_manager()
    
    # Get user settings from database
    async with storage_manager.postgres.conn_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT settings FROM users WHERE id = $1
        """, user_id)
        
        if not row:
            return jsonify({'error': 'User not found'}), 404
            
        settings = row.get('settings', {})
        
        return jsonify({
            'settings': settings,
            'user_id': user_id
        })

@api_bp.route('/user/settings', methods=['POST'])
@async_route
async def update_user_settings():
    """Update user settings"""
    from flask import session
    user_id = session.get('user_id')
    
    # Get request body
    settings = request.json.get('settings')
    if not settings:
        return jsonify({'error': 'No settings provided'}), 400
    
    # Get storage manager
    storage_manager = await get_storage_manager()
    
    # Update settings in database
    async with storage_manager.postgres.conn_pool.acquire() as conn:
        await conn.execute("""
            UPDATE users 
            SET settings = $1, updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
        """, settings, user_id)
        
    return jsonify({
        'success': True,
        'message': 'Settings updated successfully',
        'user_id': user_id
    })

# === Gmail Integration Routes ===

@api_bp.route('/emails/sync', methods=['POST'])
@async_route_no_auth
async def sync_emails():
    """
    Sync emails from Gmail API
    """
    import json
    from datetime import datetime, timedelta
    from flask import session, request, jsonify
    
    # Get parameters
    days = int(request.json.get('days', 7))
    
    # Get user session and OAuth credentials
    try:
        user_email = session.get('user_id', 'test@session-42.com')
        oauth_creds = session.get('oauth_credentials', {})
        
        # DEBUG: Log what's actually in the session
        logger.info(f"🔍 DEBUG SESSION: user_email={user_email}, has_oauth_creds={bool(oauth_creds)}, oauth_keys={list(oauth_creds.keys()) if oauth_creds else []}")
        
    except:
        oauth_creds = {}
        user_email = 'test@session-42.com'
    
    # IMPROVED REAL CREDENTIAL DETECTION
    # Check for real OAuth access token (must be long enough to be real)
    has_real_access_token = (
        oauth_creds.get('access_token') and 
        len(str(oauth_creds.get('access_token', ''))) > 50 and
        not str(oauth_creds.get('access_token', '')).startswith('test_') and
        oauth_creds.get('access_token') != 'fake_access_token'
    )
    
    # Check for real client credentials in environment
    from config.settings import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
    has_real_client_creds = (
        GOOGLE_CLIENT_ID and 
        GOOGLE_CLIENT_SECRET and
        GOOGLE_CLIENT_ID != 'your_google_client_id_here' and
        GOOGLE_CLIENT_SECRET != 'your_google_client_secret_here' and
        len(GOOGLE_CLIENT_ID) > 20 and
        len(GOOGLE_CLIENT_SECRET) > 20
    )
    
    # Return errors instead of mock data when credentials are missing
    if not has_real_client_creds:
        return jsonify({
            'success': False,
            'error': 'Google OAuth client credentials not configured',
            'details': 'GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in .env file',
            'debug_info': {
                'client_id_length': len(GOOGLE_CLIENT_ID) if GOOGLE_CLIENT_ID else 0,
                'client_secret_length': len(GOOGLE_CLIENT_SECRET) if GOOGLE_CLIENT_SECRET else 0,
                'has_client_id': bool(GOOGLE_CLIENT_ID),
                'has_client_secret': bool(GOOGLE_CLIENT_SECRET)
            }
        }), 401
    
    if not has_real_access_token:
        return jsonify({
            'success': False,
            'error': 'Gmail authentication required',
            'details': 'No valid OAuth access token found in session. Please authenticate with Google first.',
            'action_required': 'Visit /login to authenticate with Google and grant Gmail permissions',
            'debug_info': {
                'user_email': user_email,
                'has_oauth_creds': bool(oauth_creds),
                'access_token_length': len(str(oauth_creds.get('access_token', ''))),
                'oauth_keys': list(oauth_creds.keys()) if oauth_creds else []
            }
        }), 401
    
    # REAL MODE: Only import and use storage/database components here
    logger.info(f"🔄 REAL MODE: Starting email sync for {user_email}, last {days} days")
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Import storage components only in real mode
            from storage.storage_manager import get_storage_manager
            from google.oauth2.credentials import Credentials
            from gmail.client import GmailClient
            
            # Initialize storage manager for real sync
            storage_manager = await get_storage_manager()
            
            # Ensure PostgreSQL connection is healthy before proceeding
            if not await storage_manager.postgres.health_check():
                logger.warning(f"PostgreSQL connection unhealthy, attempting reconnect (attempt {attempt + 1})")
                await storage_manager.postgres.reset_connection_pool()
                await asyncio.sleep(2)
                
                # Verify connection is working
                if not await storage_manager.postgres.health_check():
                    if attempt < max_retries - 1:
                        continue
                    else:
                        raise Exception("Failed to establish stable database connection")
            
            # Get the actual user ID from the email with retry logic
            user_id = None
            for db_attempt in range(3):
                try:
                    async with storage_manager.postgres.conn_pool.acquire() as conn:
                        user_row = await conn.fetchrow("""
                            SELECT id FROM users WHERE email = $1
                        """, user_email)
                        
                        if not user_row:
                            # Create user if doesn't exist
                            user_row = await conn.fetchrow("""
                                INSERT INTO users (email, google_id)
                                VALUES ($1, $1)
                                ON CONFLICT (email) DO UPDATE
                                SET email = $1
                                RETURNING id
                            """, user_email)
                        
                        user_id = int(user_row['id'])
                        break
                        
                except Exception as db_error:
                    if "another operation is in progress" in str(db_error).lower() and db_attempt < 2:
                        logger.warning(f"Database conflict, retrying user lookup (attempt {db_attempt + 1})")
                        await asyncio.sleep(1)
                        continue
                    else:
                        raise db_error
            
            if user_id is None:
                raise Exception("Failed to get or create user ID")
            
            # Create credentials object for Gmail
            creds = Credentials(
                token=oauth_creds['access_token'],
                refresh_token=oauth_creds.get('refresh_token'),
                token_uri='https://oauth2.googleapis.com/token',
                client_id=GOOGLE_CLIENT_ID,
                client_secret=GOOGLE_CLIENT_SECRET,
                scopes=oauth_creds.get('scopes', GOOGLE_SCOPES)
            )
            
            # Initialize Gmail client with correct parameters
            gmail_client = GmailClient(user_id=user_id, credentials=creds)
            
            # Connect the Gmail client
            if not await gmail_client.connect():
                raise Exception("Failed to connect to Gmail API")
            
            # Get emails from the last N days
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            logger.info(f"Fetching emails since {cutoff_date.isoformat()}")
            
            # Fetch emails (this might take a while for large inboxes)
            messages = await gmail_client.get_messages(
                query=f'after:{cutoff_date.strftime("%Y/%m/%d")}',
                max_results=1000  # Reasonable limit
            )
            
            logger.info(f"Found {len(messages)} emails to process")
            
            # Process and store emails in batches to avoid connection conflicts
            processed_count = 0
            error_count = 0
            batch_size = 10  # Process in smaller batches
            
            for i in range(0, len(messages), batch_size):
                batch = messages[i:i + batch_size]
                
                for message in batch:
                    try:
                        # The message is already parsed by gmail_client.get_messages()
                        email_data = message
                        
                        # Store email in database with retry logic using correct column names
                        for store_attempt in range(3):
                            try:
                                async with storage_manager.postgres.conn_pool.acquire() as conn:
                                    await conn.execute("""
                                        INSERT INTO emails (user_id, gmail_id, content, metadata)
                                        VALUES ($1, $2, $3, $4)
                                        ON CONFLICT (gmail_id) DO UPDATE
                                        SET content = EXCLUDED.content,
                                            metadata = EXCLUDED.metadata,
                                            updated_at = CURRENT_TIMESTAMP
                                    """, 
                                    user_id,
                                    email_data.get('message_id'),
                                    email_data.get('body_text', ''),
                                    json.dumps({
                                        'subject': email_data.get('subject', ''),
                                        'from': email_data.get('from', ''),
                                        'to': email_data.get('to', []),
                                        'cc': email_data.get('cc', []),
                                        'date': email_data.get('date'),
                                        'thread_id': email_data.get('thread_id'),
                                        'headers': email_data.get('headers', {}),
                                        'is_sent': email_data.get('is_sent', False)
                                    })
                                    )
                                break  # Success, exit retry loop
                                
                            except Exception as store_error:
                                if "another operation is in progress" in str(store_error).lower() and store_attempt < 2:
                                    logger.warning(f"Database store conflict, retrying (attempt {store_attempt + 1})")
                                    await asyncio.sleep(0.5)
                                    continue
                                else:
                                    raise store_error
                        
                        processed_count += 1
                        
                    except Exception as e:
                        logger.warning(f"Failed to process email {message.get('message_id', 'unknown')}: {str(e)}")
                        error_count += 1
                        continue
                
                # Small delay between batches to prevent overwhelming the connection pool
                if i + batch_size < len(messages):
                    await asyncio.sleep(0.1)
            
            logger.info(f"Email sync completed: {processed_count} processed, {error_count} errors")
            
            return jsonify({
                'success': True,
                'message': f'Email synchronization completed',
                'status': 'completed',
                'stats': {
                    'days_synced': days,
                    'total_found': len(messages),
                    'processed': processed_count,
                    'errors': error_count,
                    'cutoff_date': cutoff_date.isoformat()
                }
            })
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Email sync failed (attempt {attempt + 1}): {error_msg}", user_email=user_email)
            
            # Check if this is a retryable error
            if any(phrase in error_msg.lower() for phrase in [
                "another operation is in progress",
                "connection was closed",
                "event loop is closed",
                "pool is closed"
            ]) and attempt < max_retries - 1:
                logger.warning(f"Retryable error, attempting again (attempt {attempt + 1})")
                
                # Reset storage manager connections
                try:
                    storage_manager = await get_storage_manager()
                    await storage_manager.postgres.reset_connection_pool()
                except:
                    pass
                
                await asyncio.sleep(2)
                continue
            else:
                # Non-retryable error or max retries reached
                return jsonify({
                    'success': False,
                    'error': error_msg,
                    'status': 'failed',
                    'attempt': attempt + 1
                }), 500
    
    # If we get here, all retries failed
    return jsonify({
        'success': False,
        'error': 'Email sync failed after multiple retries due to database connection issues',
        'status': 'failed'
    }), 500

@api_bp.route('/gmail/analyze-sent', methods=['POST'])
@async_route
async def analyze_sent_emails():
    """
    Analyze sent emails to extract trusted contacts
    Core innovation: Analyzing sent emails for trust network
    """
    from flask import session
    user_email = session.get('user_id')  # This is actually the email
    
    # Debug: Log session contents for OAuth credentials
    oauth_creds = session.get('oauth_credentials', {})
    logger.info("OAuth credentials in session", 
                user_id=user_email, 
                has_access_token=bool(oauth_creds.get('access_token')),
                scopes=oauth_creds.get('scopes', []))
    
    # Get request parameters
    lookback_days = request.json.get('lookback_days', 180)
    force_refresh = request.json.get('force_refresh', True)  # Default to True to always get fresh data
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Create analyzer with proper user ID lookup
            storage_manager = await get_storage_manager()
            
            # Ensure postgres connection is healthy
            if not await storage_manager.postgres.health_check():
                logger.warning(f"PostgreSQL connection unhealthy, attempting reconnect (attempt {attempt + 1})")
                await storage_manager.postgres.reset_connection_pool()
            
            # First, get the actual user ID from the email
            async with storage_manager.postgres.conn_pool.acquire() as conn:
                user_row = await conn.fetchrow("""
                    SELECT id FROM users WHERE email = $1
                """, user_email)
                
                if not user_row:
                    # Create user if doesn't exist
                    user_row = await conn.fetchrow("""
                        INSERT INTO users (email, google_id)
                        VALUES ($1, $1)
                        ON CONFLICT (email) DO UPDATE
                        SET email = $1
                        RETURNING id
                    """, user_email)
                
                user_id = int(user_row['id'])  # Ensure it's an integer
                logger.info(f"Found/created user ID {user_id} for email {user_email}")
            
            analyzer = SentEmailAnalyzer(user_id, storage_manager)
            
            # Debug: Check analyzer user_id type
            logger.info(f"Analyzer initialized with user_id type: {type(analyzer.user_id)}, value: {analyzer.user_id}")
            
            # Run analysis
            results = await analyzer.extract_trusted_contacts(
                lookback_days=lookback_days,
                force_refresh=force_refresh
            )
            
            # Debug: Check contact data types before storage
            if results.get('contacts'):
                sample_contact = results['contacts'][0] if results['contacts'] else {}
                logger.info(f"Sample contact data types: {[(k, type(v)) for k, v in sample_contact.items()]}")
            
            return jsonify(results)
            
        except Exception as e:
            error_msg = str(e)
            if ("event loop is closed" in error_msg.lower() or 
                "another operation is in progress" in error_msg.lower() or
                "connection" in error_msg.lower()) and attempt < max_retries - 1:
                
                logger.warning(f"Connection issue on attempt {attempt + 1}, retrying: {error_msg}")
                
                # Reset connection pool
                try:
                    storage_manager = await get_storage_manager()
                    await storage_manager.postgres.reset_connection_pool()
                except:
                    pass
                
                # Wait a bit before retry
                await asyncio.sleep(1)
                continue
            else:
                logger.error(f"Email analysis failed: {error_msg}", user_email=user_email)
                return jsonify({
                    'success': False,
                    'error': error_msg,
                    'contacts': [],
                    'attempt': attempt + 1
                }), 500
    
    # If we get here, all retries failed
    return jsonify({
        'success': False,
        'error': 'Failed after multiple retries due to connection issues',
        'contacts': []
    }), 500

@api_bp.route('/contacts')
@async_route
async def get_contacts():
    """Get user's trusted contacts"""
    from flask import session
    user_id = session.get('user_id', 'Sandman@session-42.com')  # Default for testing
    
    # For testing purposes, allow direct access
    if not user_id:
        user_id = 'Sandman@session-42.com'
    
    # Get request parameters
    trust_tier = request.args.get('trust_tier')
    domain = request.args.get('domain')
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    
    # Get storage manager with retry logic
    storage_manager = await get_storage_manager()
    
    contacts = []
    total = 0
    from_cache = False
    error_details = None
    
    # Robust database query with connection pool management
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Ensure connection pool is healthy before querying
            if not await storage_manager.postgres.health_check():
                logger.warning(f"PostgreSQL connection unhealthy, resetting pool (attempt {attempt + 1})")
                await storage_manager.postgres.reset_connection_pool()
                await asyncio.sleep(1)  # Give it a moment to stabilize
            
            # Get the actual user ID from email if needed
            if isinstance(user_id, str) and '@' in user_id:
                async with storage_manager.postgres.conn_pool.acquire() as conn:
                    user_row = await conn.fetchrow("""
                        SELECT id FROM users WHERE email = $1
                    """, user_id)
                    if user_row:
                        user_id = user_row['id']
                        logger.info(f"Converted email {session.get('user_id')} to user_id {user_id}")
            
            # Build query conditions
            conditions = ["user_id = $1"]
            params = [user_id]
            
            if trust_tier:
                conditions.append("trust_tier = $" + str(len(params) + 1))
                params.append(trust_tier)
                
            if domain:
                conditions.append("domain = $" + str(len(params) + 1))
                params.append(domain)
            
            # Execute query with fresh connection
            async with storage_manager.postgres.conn_pool.acquire() as conn:
                # Get total count
                count_query = "SELECT COUNT(*) FROM contacts WHERE " + " AND ".join(conditions)
                total = await conn.fetchval(count_query, *params)
                logger.info(f"Found {total} total contacts for user {user_id}")
                
                # Get contacts
                query = f"""
                    SELECT * FROM contacts 
                    WHERE {" AND ".join(conditions)}
                    ORDER BY trust_tier DESC, frequency DESC
                    LIMIT $%s OFFSET $%s
                """ % (len(params) + 1, len(params) + 2)
                params.extend([limit, offset])
                
                rows = await conn.fetch(query, *params)
                contacts = [dict(row) for row in rows]
                logger.info(f"Retrieved {len(contacts)} contacts from database")
                
                # Success - break retry loop
                break
                
        except Exception as db_error:
            error_msg = str(db_error)
            logger.error(f"Database query failed (attempt {attempt + 1}): {error_msg}")
            
            if ("another operation is in progress" in error_msg.lower() or 
                "event loop is closed" in error_msg.lower() or
                "connection" in error_msg.lower()) and attempt < max_retries - 1:
                
                logger.warning(f"Connection issue, resetting pool and retrying...")
                try:
                    await storage_manager.postgres.reset_connection_pool()
                    await asyncio.sleep(2)  # Wait longer between retries
                    continue
                except:
                    pass
            else:
                error_details = error_msg
                contacts = []
                break
    
    # If database failed, try cache as fallback
    if not contacts and storage_manager and storage_manager.cache:
        try:
            cached_data = await storage_manager.cache.get_user_data(user_id, 'trusted_contacts')
            if cached_data and cached_data.get('contacts'):
                all_contacts = cached_data['contacts']
                from_cache = True
                
                # Apply filters
                filtered_contacts = all_contacts
                
                if trust_tier:
                    filtered_contacts = [c for c in filtered_contacts if c.get('trust_tier') == trust_tier]
                
                if domain:
                    filtered_contacts = [c for c in filtered_contacts if c.get('domain') == domain]
                
                # Apply pagination
                total = len(filtered_contacts)
                contacts = filtered_contacts[offset:offset + limit]
                logger.info(f"Retrieved {len(contacts)} contacts from cache")
                
        except Exception as cache_error:
            logger.warning(f"Cache query failed: {cache_error}")
    
    return jsonify({
        'contacts': contacts,
        'total': total,
        'limit': limit,
        'offset': offset,
        'trust_tier_filter': trust_tier,
        'domain_filter': domain,
        'from_cache': from_cache,
        'database_available': storage_manager.postgres is not None if storage_manager else False,
        'user_id': user_id,
        'error_details': error_details,
        'success': len(contacts) > 0 or total == 0,
        'debug_info': {
            'storage_manager_exists': storage_manager is not None,
            'postgres_exists': hasattr(storage_manager, 'postgres') if storage_manager else False,
            'conn_pool_exists': hasattr(storage_manager.postgres, 'conn_pool') if storage_manager and hasattr(storage_manager, 'postgres') else False
        }
    })

@api_bp.route('/contacts/stats')
@async_route
async def get_contact_stats():
    """Get statistics about user's contacts"""
    from flask import session
    user_id = session.get('user_id')
    
    # Get storage manager
    storage_manager = await get_storage_manager()
    
    # Analyze contacts from storage
    async with storage_manager.postgres.conn_pool.acquire() as conn:
        # Get trust tier counts
        tier_counts = await conn.fetch("""
            SELECT trust_tier, COUNT(*) as count
            FROM contacts
            WHERE user_id = $1
            GROUP BY trust_tier
        """, user_id)
        
        # Get domain counts
        domain_counts = await conn.fetch("""
            SELECT domain, COUNT(*) as count
            FROM contacts
            WHERE user_id = $1
            GROUP BY domain
            ORDER BY count DESC
            LIMIT 10
        """, user_id)
        
        # Get total contacts
        total_contacts = await conn.fetchval("""
            SELECT COUNT(*) FROM contacts WHERE user_id = $1
        """, user_id)
        
        return jsonify({
            'total_contacts': total_contacts,
            'trust_tiers': {row['trust_tier']: row['count'] for row in tier_counts},
            'top_domains': [{'domain': row['domain'], 'count': row['count']} for row in domain_counts],
            'user_id': user_id
        })

# === Email Search Routes ===

@api_bp.route('/emails/search')
@async_route_no_auth
async def search_emails():
    """
    Search emails by topic, contact, or other criteria
    """
    from flask import request
    
    # Get search parameters
    topic = request.args.get('topic')
    contact = request.args.get('contact')
    limit = int(request.args.get('limit', 50))
    
    try:
        # Get storage manager
        storage_manager = await get_storage_manager()
        
        # Build search query
        if topic:
            # Search emails containing the topic
            async with storage_manager.postgres.conn_pool.acquire() as conn:
                emails = await conn.fetch("""
                    SELECT e.*, u.email as user_email
                    FROM emails e
                    JOIN users u ON e.user_id = u.id
                    WHERE e.content ILIKE $1
                    ORDER BY e.created_at DESC
                    LIMIT $2
                """, f'%{topic}%', limit)
                
        elif contact:
            # Search emails from or to the contact
            async with storage_manager.postgres.conn_pool.acquire() as conn:
                emails = await conn.fetch("""
                    SELECT e.*, u.email as user_email
                    FROM emails e
                    JOIN users u ON e.user_id = u.id
                    WHERE e.metadata::text ILIKE $1
                    OR e.content ILIKE $1
                    ORDER BY e.created_at DESC
                    LIMIT $2
                """, f'%{contact}%', limit)
        else:
            return jsonify({'error': 'No search criteria provided'}), 400
        
        # Format email results
        email_list = []
        for email in emails:
            try:
                metadata = json.loads(email['metadata']) if email['metadata'] else {}
            except:
                metadata = {}
                
            email_data = {
                'id': email['id'],
                'subject': metadata.get('subject', 'No Subject'),
                'from': metadata.get('from', 'Unknown'),
                'to': metadata.get('to', 'Unknown'),
                'date': email['created_at'].isoformat() if email['created_at'] else None,
                'content': email['content'][:1000] if email['content'] else 'No content',  # Limit content length
                'user_email': email['user_email']
            }
            email_list.append(email_data)
        
        return jsonify({
            'success': True,
            'emails': email_list,
            'total': len(email_list),
            'search_criteria': {
                'topic': topic,
                'contact': contact,
                'limit': limit
            }
        })
        
    except Exception as e:
        logger.error(f"Email search failed: {str(e)}")
        return jsonify({
            'error': f'Search failed: {str(e)}',
            'emails': []
        }), 500

@api_bp.route('/emails')
@async_route_no_auth
async def get_all_emails():
    """
    Get all emails for the current user
    """
    from flask import session
    
    try:
        user_email = session.get('user_id', 'Sandman@session-42.com')
        
        # Get storage manager
        storage_manager = await get_storage_manager()
        
        # Get user ID
        async with storage_manager.postgres.conn_pool.acquire() as conn:
            user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", user_email)
            if not user:
                return jsonify({'error': 'User not found', 'emails': []}), 404
            
            user_id = user['id']
            
            # Get all emails for user
            emails = await conn.fetch("""
                SELECT e.*, u.email as user_email
                FROM emails e
                JOIN users u ON e.user_id = u.id
                WHERE e.user_id = $1
                ORDER BY e.created_at DESC
                LIMIT 200
            """, user_id)
        
        # Format email results
        email_list = []
        for email in emails:
            try:
                metadata = json.loads(email['metadata']) if email['metadata'] else {}
            except:
                metadata = {}
                
            email_data = {
                'id': email['id'],
                'subject': metadata.get('subject', 'No Subject'),
                'from': metadata.get('from', 'Unknown'),
                'to': metadata.get('to', 'Unknown'),
                'date': email['created_at'].isoformat() if email['created_at'] else None,
                'content': email['content'][:2000] if email['content'] else 'No content',  # Longer content for full view
                'user_email': email['user_email']
            }
            email_list.append(email_data)
        
        return jsonify({
            'success': True,
            'emails': email_list,
            'total': len(email_list),
            'user_email': user_email
        })
        
    except Exception as e:
        logger.error(f"Get all emails failed: {str(e)}")
        return jsonify({
            'error': f'Failed to get emails: {str(e)}',
            'emails': []
        }), 500

# === Intelligence Analysis Routes ===

@api_bp.route('/intelligence/analyze', methods=['POST'])
@async_route
async def analyze_intelligence():
    """
    Run intelligence analysis on user data
    This would trigger the Claude Opus analysis in production
    """
    from flask import session
    user_id = session.get('user_id')
    
    # Get analysis parameters
    analysis_type = request.json.get('type', 'general')
    time_range = request.json.get('time_range', 90)
    contact_email = request.json.get('contact_email')
    
    # This is a placeholder for the actual Claude Opus analysis
    # In the real implementation, we would:
    # 1. Fetch relevant emails, contacts, and other data
    # 2. Send to Claude Opus for analysis
    # 3. Store and return the results
    
    return jsonify({
        'analysis_id': f"analysis_{user_id}_{int(datetime.utcnow().timestamp())}",
        'analysis_type': analysis_type,
        'status': 'scheduled',
        'message': 'Intelligence analysis scheduled',
        'estimated_completion': (datetime.utcnow() + timedelta(minutes=5)).isoformat()
    })

@api_bp.route('/intelligence/results/<analysis_id>')
@async_route
async def get_analysis_results(analysis_id):
    """Get results of a previously scheduled analysis"""
    from flask import session
    user_id = session.get('user_id')
    
    # This is a placeholder for retrieving actual analysis results
    # In the real implementation, we would fetch from database
    
    return jsonify({
        'analysis_id': analysis_id,
        'user_id': user_id,
        'status': 'completed',
        'completed_at': datetime.utcnow().isoformat(),
        'results': {
            'summary': 'This is a placeholder for actual intelligence analysis results.',
            'key_insights': [
                'Placeholder insight 1',
                'Placeholder insight 2',
                'Placeholder insight 3'
            ]
        }
    })

# === Knowledge Tree Routes ===

@api_bp.route('/knowledge/tree')
@async_route
async def get_knowledge_tree():
    """Get user's knowledge tree"""
    from flask import session
    user_id = session.get('user_id')
    
    # Get storage manager
    storage_manager = await get_storage_manager()
    
    # Try cache first
    cached_tree = await storage_manager.cache.get_user_data(
        user_id, 'knowledge_tree'
    )
    if cached_tree:
        return jsonify({
            'tree': cached_tree,
            'cached': True
        })
    
    # Get from database if not cached
    async with storage_manager.postgres.conn_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT tree_data FROM knowledge_tree WHERE user_id = $1
        """, user_id)
        
        tree_data = row.get('tree_data') if row else {}
        
        # Cache for future requests
        if tree_data:
            await storage_manager.cache.cache_user_data(
                user_id, 'knowledge_tree', tree_data
            )
        
        return jsonify({
            'tree': tree_data,
            'user_id': user_id
        })

@api_bp.route('/intelligence/build-knowledge-tree', methods=['POST'])
@async_route_no_auth
async def build_knowledge_tree():
    """
    Build knowledge tree using Claude analysis on user's email data
    """
    from flask import session
    user_email = session.get('user_id', 'Sandman@session-42.com')  # Default for testing
    
    # Get request parameters
    time_window_days = request.json.get('time_window_days', 30) if request.json else 30
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Get storage manager with retry logic
            storage_manager = await get_storage_manager()
            
            # Ensure PostgreSQL connection is healthy before proceeding
            if not await storage_manager.postgres.health_check():
                logger.warning(f"PostgreSQL connection unhealthy, attempting reconnect (attempt {attempt + 1})")
                await storage_manager.postgres.reset_connection_pool()
                await asyncio.sleep(2)
                
                # Verify connection is working
                if not await storage_manager.postgres.health_check():
                    if attempt < max_retries - 1:
                        continue
                    else:
                        raise Exception("Failed to establish stable database connection")
            
            # Get the actual user ID from the email with retry logic
            user_id = None
            for db_attempt in range(3):
                try:
                    async with storage_manager.postgres.conn_pool.acquire() as conn:
                        user_row = await conn.fetchrow("""
                            SELECT id FROM users WHERE email = $1
                        """, user_email)
                        
                        if not user_row:
                            # Create user if doesn't exist
                            user_row = await conn.fetchrow("""
                                INSERT INTO users (email, google_id)
                                VALUES ($1, $1)
                                ON CONFLICT (email) DO UPDATE
                                SET email = $1
                                RETURNING id
                            """, user_email)
                        
                        user_id = int(user_row['id'])
                        break
                        
                except Exception as db_error:
                    if "another operation is in progress" in str(db_error).lower() and db_attempt < 2:
                        logger.warning(f"Database conflict, retrying user lookup (attempt {db_attempt + 1})")
                        await asyncio.sleep(1)
                        continue
                    else:
                        raise db_error
            
            if user_id is None:
                raise Exception("Failed to get or create user ID")
            
            logger.info(f"Starting knowledge tree building for user {user_id} ({user_email})")
            
            # Check if we have enough email data with retry logic
            email_count = 0
            for db_attempt in range(3):
                try:
                    async with storage_manager.postgres.conn_pool.acquire() as conn:
                        email_count = await conn.fetchval("""
                            SELECT COUNT(*) FROM emails WHERE user_id = $1
                        """, user_id)
                    break
                except Exception as db_error:
                    if "another operation is in progress" in str(db_error).lower() and db_attempt < 2:
                        logger.warning(f"Database conflict, retrying email count (attempt {db_attempt + 1})")
                        await asyncio.sleep(1)
                        continue
                    else:
                        raise db_error
            
            if email_count < 10:
                return jsonify({
                    'success': False,
                    'error': f'Insufficient email data. Found {email_count} emails, need at least 10 for knowledge tree building.',
                    'suggestion': 'Please sync more emails first using the email sync feature.'
                }), 400
            
            logger.info(f"Found {email_count} emails for knowledge tree building")
            
            # Get recent emails with metadata using retry logic
            emails = []
            for db_attempt in range(3):
                try:
                    async with storage_manager.postgres.conn_pool.acquire() as conn:
                        # Simplified query to avoid interval issues
                        emails = await conn.fetch("""
                            SELECT content, metadata, created_at 
                            FROM emails 
                            WHERE user_id = $1 
                            ORDER BY created_at DESC
                            LIMIT 500
                        """, user_id)
                    break
                except Exception as db_error:
                    if "another operation is in progress" in str(db_error).lower() and db_attempt < 2:
                        logger.warning(f"Database conflict, retrying email fetch (attempt {db_attempt + 1})")
                        await asyncio.sleep(1)
                        continue
                    else:
                        raise db_error
            
            # Build basic knowledge tree structure
            knowledge_tree = {
                'user_id': user_id,
                'time_window': {
                    'days': time_window_days,
                    'start_date': (datetime.utcnow() - timedelta(days=time_window_days)).isoformat(),
                    'end_date': datetime.utcnow().isoformat()
                },
                'email_count': len(emails),
                'topics': [],
                'entities': [],
                'relationships': [],
                'insights': {},
                'created_at': datetime.utcnow().isoformat(),
                'version': '1.0'
            }
            
            # Extract basic topics from email subjects and content
            topics = set()
            entities = set()
            
            for email in emails:
                try:
                    metadata = email['metadata'] if isinstance(email['metadata'], dict) else json.loads(email['metadata'] or '{}')
                    subject = metadata.get('subject', '').lower()
                    content = (email['content'] or '').lower()
                    
                    # Simple topic extraction (in production, use Claude)
                    if 'meeting' in subject or 'meeting' in content:
                        topics.add('meetings')
                    if 'project' in subject or 'project' in content:
                        topics.add('projects')
                    if 'deadline' in subject or 'deadline' in content:
                        topics.add('deadlines')
                    if 'budget' in subject or 'budget' in content:
                        topics.add('budget')
                    if 'report' in subject or 'report' in content:
                        topics.add('reports')
                    if 'schedule' in subject or 'schedule' in content:
                        topics.add('scheduling')
                    
                    # Extract email addresses as entities
                    from_email = metadata.get('from', '')
                    to_emails = metadata.get('to', [])
                    
                    if from_email and '@' in from_email:
                        entities.add(from_email)
                    
                    for to_email in (to_emails if isinstance(to_emails, list) else []):
                        if '@' in str(to_email):
                            entities.add(str(to_email))
                            
                except Exception as e:
                    logger.warning(f"Error processing email for knowledge tree: {e}")
                    continue
            
            knowledge_tree['topics'] = list(topics)
            knowledge_tree['entities'] = list(entities)[:50]  # Limit entities
            
            # Store the knowledge tree in database with retry logic
            for db_attempt in range(3):
                try:
                    async with storage_manager.postgres.conn_pool.acquire() as conn:
                        await conn.execute("""
                            INSERT INTO knowledge_tree (user_id, tree_data)
                            VALUES ($1, $2)
                            ON CONFLICT (user_id) DO UPDATE
                            SET tree_data = EXCLUDED.tree_data,
                                updated_at = CURRENT_TIMESTAMP
                        """, user_id, json.dumps(knowledge_tree))
                    break
                except Exception as db_error:
                    if "another operation is in progress" in str(db_error).lower() and db_attempt < 2:
                        logger.warning(f"Database conflict, retrying knowledge tree save (attempt {db_attempt + 1})")
                        await asyncio.sleep(1)
                        continue
                    else:
                        raise db_error
            
            # Cache the knowledge tree
            try:
                await storage_manager.cache.cache_user_data(
                    user_id, 'knowledge_tree', knowledge_tree
                )
            except Exception as cache_error:
                logger.warning(f"Failed to cache knowledge tree: {cache_error}")
            
            logger.info(f"Successfully built knowledge tree for user {user_id}")
            
            return jsonify({
                'success': True,
                'message': 'Knowledge tree successfully built',
                'knowledge_tree_summary': {
                    'time_window': knowledge_tree['time_window'],
                    'email_count': knowledge_tree['email_count'],
                    'topic_count': len(knowledge_tree['topics']),
                    'entity_count': len(knowledge_tree['entities']),
                    'topics': knowledge_tree['topics'][:10],  # Show first 10 topics
                    'entities': knowledge_tree['entities'][:10],  # Show first 10 entities
                    'created_at': knowledge_tree['created_at']
                }
            })
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Knowledge tree building failed (attempt {attempt + 1}): {error_msg}")
            
            # Check if this is a retryable error
            if any(phrase in error_msg.lower() for phrase in [
                "another operation is in progress",
                "connection was closed",
                "event loop is closed",
                "pool is closed"
            ]) and attempt < max_retries - 1:
                logger.warning(f"Retryable error, attempting again (attempt {attempt + 1})")
                
                # Reset storage manager connections
                try:
                    storage_manager = await get_storage_manager()
                    await storage_manager.postgres.reset_connection_pool()
                except:
                    pass
                
                await asyncio.sleep(2)
                continue
            else:
                # Non-retryable error or max retries reached
                return jsonify({
                    'success': False,
                    'error': error_msg,
                    'attempt': attempt + 1
                }), 500
    
    # If we get here, all retries failed
    return jsonify({
        'success': False,
        'error': 'Knowledge tree building failed after multiple retries due to database connection issues'
    }), 500

# === Intelligence Routes ===

@api_bp.route('/intelligence/enrich-contacts', methods=['POST'])
@async_route
async def enrich_contacts():
    """
    Enrich contacts with professional intelligence using Claude Opus 4 Intelligent Augmentation
    """
    from flask import session
    from intelligence.claude_intelligent_augmentation import get_claude_intelligent_augmentation
    
    user_email = session.get('user_email')
    if not user_email:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json() or {}
        sources = data.get('sources', ['person', 'company', 'professional'])
        limit = data.get('limit', 50)
        
        logger.info(f"Starting Claude Opus 4 intelligent augmentation for user {user_email}", 
                   extra={"sources": sources, "limit": limit})
        
        # Initialize PostgreSQL client
        postgres_client = PostgresClient()
        await postgres_client.connect()
        
        # Get user ID and contacts to enrich
        async with postgres_client.conn_pool.acquire() as conn:
            # Get user ID
            user_record = await conn.fetchrow(
                "SELECT id FROM users WHERE email = $1", user_email
            )
            
            if not user_record:
                return jsonify({'error': 'User not found'}), 404
                
            user_id = user_record['id']
            logger.info(f"Found user ID {user_id} for email {user_email}")
            
            # Get contacts to enrich (prioritize tier 1 and tier 2)
            contacts = await conn.fetch("""
                SELECT * FROM contacts 
                WHERE user_id = $1 AND trust_tier IN ('tier_1', 'tier_2')
                ORDER BY trust_tier ASC, frequency DESC
                LIMIT $2
            """, user_id, limit)
        
        logger.info(f"Found {len(contacts)} contacts to enrich")
        
        enriched_count = 0
        failed_count = 0
        
        for contact in contacts:
            try:
                email_addr = contact.get('email', '')
                name = contact.get('name', '')
                
                if not email_addr:
                    continue
                
                logger.info(f"🧠 Starting Claude Opus 4 intelligent augmentation for {email_addr}")
                
                # Use Claude Opus 4 intelligent augmentation
                intelligence_result = await get_claude_intelligent_augmentation(email_addr, name)
                
                if intelligence_result.get('success'):
                    # Store the intelligence data
                    metadata = {
                        'enrichment_method': 'claude_opus_4_intelligent_augmentation',
                        'enrichment_timestamp': datetime.utcnow().isoformat(),
                        'enrichment_status': 'success',
                        'intelligence_data': {
                            'person': intelligence_result.get('person', {}),
                            'company': intelligence_result.get('company', {}),
                            'professional': intelligence_result.get('intelligence_summary', {})
                        }
                    }
                    
                    # Update contact with intelligence data
                    async with postgres_client.conn_pool.acquire() as conn:
                        await conn.execute("""
                            UPDATE contacts 
                            SET metadata = metadata || $1
                            WHERE user_id = $2 AND email = $3
                        """, json.dumps(metadata), user_id, email_addr)
                    
                    enriched_count += 1
                    logger.info(f"✅ Successfully enriched {email_addr} with Claude intelligence")
                    
                else:
                    failed_count += 1
                    logger.warning(f"❌ Failed to enrich {email_addr}: {intelligence_result.get('error', 'Unknown error')}")
                
                # Rate limiting to avoid overwhelming Claude API
                await asyncio.sleep(2)
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to process contact {email_addr}: {e}")
                continue
        
        await postgres_client.disconnect()
        
        return jsonify({
            'success': True,
            'message': f'Claude Opus 4 intelligent augmentation completed',
            'enriched_count': enriched_count,
            'failed_count': failed_count,
            'total_processed': len(contacts),
            'method': 'claude_opus_4_intelligent_augmentation'
        })
        
    except Exception as e:
        logger.error(f"Contact enrichment failed: {e}")
        return jsonify({'error': str(e)}), 500

# === Test Endpoints ===

@api_bp.route('/test/no-auth')
@async_route_no_auth
async def test_no_auth():
    """Simple test endpoint without authentication"""
    return jsonify({
        'message': 'This endpoint works without authentication',
        'timestamp': datetime.utcnow().isoformat(),
        'auth_required': False
    })
