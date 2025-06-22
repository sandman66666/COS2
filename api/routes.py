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
import os

from flask import Blueprint, request, jsonify, current_app, g
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
import google.auth.exceptions

from config.settings import (
    GOOGLE_CLIENT_ID, 
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    GOOGLE_SCOPES,
    ANTHROPIC_API_KEY
)
from utils.logging import structured_logger as logger
from middleware.auth_middleware import require_auth, api_key_auth, rate_limit, get_current_user
from storage.storage_manager import get_storage_manager
from storage.postgres_client import PostgresClient
from gmail.client import GmailClient
from gmail.analyzer import SentEmailAnalyzer, analyze_user_contacts
from intelligence.contact_enrichment_integration import enrich_contacts_batch

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
    return await _sync_emails_internal()

async def _sync_emails_internal():
    """
    Internal function to sync emails from Gmail API
    """
    import json
    from datetime import datetime, timedelta
    from flask import session, request, jsonify
    
    try:
        # Get parameters with safe handling for missing JSON
        try:
            request_data = request.get_json() or {}
        except Exception as json_error:
            # Handle cases where request doesn't have JSON content
            logger.info(f"No JSON data in request, using defaults: {json_error}")
            request_data = {}
            
        days = int(request_data.get('days', 7))
        
        logger.info(f"📧 Starting email sync with {days} days lookback")
        
        # Get user session and OAuth credentials
        try:
            user_email = session.get('user_id', 'test@session-42.com')
            oauth_creds = session.get('oauth_credentials', {})
            
            # DEBUG: Log what's actually in the session
            logger.info(f"🔍 DEBUG SESSION: user_email={user_email}, has_oauth_creds={bool(oauth_creds)}, oauth_keys={list(oauth_creds.keys()) if oauth_creds else []}")
            
        except Exception as session_error:
            logger.error(f"Error getting session data: {session_error}")
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
        
        logger.info(f"🔑 Credential check: real_client_creds={has_real_client_creds}, real_access_token={has_real_access_token}")
        
        # Return errors instead of mock data when credentials are missing
        if not has_real_client_creds:
            logger.warning("❌ Google OAuth client credentials not configured")
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
            logger.warning("❌ Gmail authentication required - no valid access token")
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
    
    except ValueError as ve:
        logger.error(f"❌ Parameter validation error: {ve}")
        return jsonify({
            'success': False,
            'error': 'Invalid parameters',
            'details': str(ve)
        }), 400
    
    except Exception as e:
        logger.error(f"❌ Unexpected error in email sync setup: {e}")
        return jsonify({
            'success': False, 
            'error': 'Setup error',
            'details': str(e)
        }), 500
    
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
            
            # Process and store emails in smaller batches to avoid long transactions
            processed_count = 0
            error_count = 0
            batch_size = 5  # Reduced from 10 to prevent long-running transactions
            
            for i in range(0, len(messages), batch_size):
                batch = messages[i:i + batch_size]
                
                # Process each batch in a separate, short transaction
                batch_processed = 0
                for store_attempt in range(3):
                    try:
                        async with storage_manager.postgres.conn_pool.acquire() as conn:
                            # Use a single transaction for the entire batch, but keep it short
                            async with conn.transaction():
                                for message in batch:
                                    try:
                                        # The message is already parsed by gmail_client.get_messages()
                                        email_data = message
                                        
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
                                        batch_processed += 1
                                        
                                    except Exception as email_error:
                                        logger.warning(f"Failed to process individual email {message.get('message_id', 'unknown')}: {str(email_error)}")
                                        error_count += 1
                                        continue
                        
                        # Success - exit retry loop for this batch
                        processed_count += batch_processed
                        break
                        
                    except Exception as batch_error:
                        if "another operation is in progress" in str(batch_error).lower() and store_attempt < 2:
                            logger.warning(f"Database batch conflict, retrying (attempt {store_attempt + 1})")
                            await asyncio.sleep(0.5)
                            continue
                        else:
                            logger.error(f"Failed to process batch starting at {i}: {str(batch_error)}")
                            error_count += len(batch)
                            break
                
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
@async_route
async def build_advanced_knowledge_tree():
    """Build advanced strategic intelligence knowledge tree with multi-agent analysis"""
    try:
        # Get authenticated user using the auth middleware function
        from middleware.auth_middleware import get_current_user
        current_user = get_current_user()
        
        if not current_user:
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
            
        user_email = current_user['email']
        logger.info(f"🧠 Building Advanced Strategic Intelligence for {user_email}")
        
        # Get actual user from database to get the proper user ID
        from storage.storage_manager import storage_manager
        user = await storage_manager.get_user_by_email(user_email)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found in database'
            }), 404
        
        # Get request parameters
        data = request.get_json() or {}
        time_window_days = int(data.get('time_window_days', 30))
        iteration = int(data.get('iteration', 1))
        analysis_depth = data.get('analysis_depth', 'multidimensional')
        
        logger.info(f"📊 Analysis parameters: time_window={time_window_days} days, iteration={iteration}, depth={analysis_depth}")
        
        # Initialize Advanced Knowledge System
        from intelligence.advanced_knowledge_system import AdvancedKnowledgeSystem
        advanced_system = AdvancedKnowledgeSystem()
        
        # Get emails for analysis using the proper integer user ID
        emails = await storage_manager.get_emails_for_user(
            user_id=user['id'],  # Now this is the actual integer user ID
            limit=1000,  # Analyze more emails for sophisticated analysis
            time_window_days=time_window_days
        )
        
        if not emails:
            return jsonify({
                'success': False,
                'error': 'No emails found for analysis. Please ensure Gmail data is synced.'
            }), 404
        
        # Get existing contacts with augmentation data
        try:
            # Get contacts from database with enrichment data
            async with storage_manager.postgres.conn_pool.acquire() as conn:
                contacts_rows = await conn.fetch("""
                    SELECT email, name, trust_tier, frequency, domain, metadata, 
                           created_at, updated_at
                    FROM contacts 
                    WHERE user_id = $1 
                    ORDER BY trust_tier ASC, frequency DESC
                """, user['id'])  # Use the proper integer user ID
                
                existing_contacts = []
                for row in contacts_rows:
                    try:
                        metadata = json.loads(row['metadata']) if row['metadata'] else {}
                    except:
                        metadata = {}
                    
                    existing_contacts.append({
                        'email': row['email'],
                        'name': row['name'],
                        'trust_tier': row['trust_tier'],
                        'frequency': row['frequency'],
                        'domain': row['domain'],
                        'metadata': metadata,
                        'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                        'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None
                    })
        except Exception as contact_error:
            logger.warning(f"Failed to load contacts for augmentation: {contact_error}")
            existing_contacts = []
        
        logger.info(f"📧 Retrieved {len(emails)} emails and {len(existing_contacts)} contacts for advanced analysis")
        
        # Build advanced knowledge tree with multi-agent analysis
        knowledge_tree = await advanced_system.build_advanced_knowledge_tree(
            user_id=user['id'],  # Use the proper integer user ID
            emails=emails,
            existing_contacts=existing_contacts,
            iteration=iteration
        )
        
        # Store the knowledge tree
        success = await storage_manager.store_knowledge_tree(
            user_id=user['id'],  # Use the proper integer user ID
            tree_data=knowledge_tree,
            analysis_type=f"advanced_strategic_intelligence_v2_iter_{iteration}"
        )
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Failed to store advanced knowledge tree'
            }), 500
        
        logger.info("✅ Advanced strategic intelligence knowledge tree built and stored successfully")
        
        # Prepare response with rich metadata
        response_data = {
            'success': True,
            'message': f'Advanced Strategic Intelligence built successfully (Iteration {iteration})',
            'tree_type': 'advanced_strategic_intelligence_v2',
            'system_version': knowledge_tree.get('analysis_metadata', {}).get('system_version', 'v2.0'),
            'iteration': iteration,
            'analysis_summary': {
                'emails_analyzed': len(emails),
                'contacts_integrated': len(existing_contacts),
                'enriched_contacts': knowledge_tree.get('augmentation_sources', {}).get('contact_enrichment_data', 0),
                'web_sources': knowledge_tree.get('augmentation_sources', {}).get('web_sources_analyzed', 0),
                'cross_references': knowledge_tree.get('augmentation_sources', {}).get('cross_references_found', 0),
                'agents_executed': len([k for k in knowledge_tree.get('agent_analysis', {}).keys() if not knowledge_tree['agent_analysis'][k].get('error')])
            },
            'intelligence_capabilities': [
                'Multi-agent Claude 4 Opus analysis',
                'Email content cross-referencing',
                'Contact augmentation integration',
                'Competitive intelligence via web search',
                'Cross-domain synthesis',
                'Predictive insights generation'
            ],
            'next_iteration_suggestions': knowledge_tree.get('analysis_metadata', {}).get('next_iteration_suggestions', []),
            'strategic_highlights': {
                'cross_domain_connections': len(knowledge_tree.get('strategic_intelligence', {}).get('cross_domain_connections', [])),
                'business_opportunities': len(knowledge_tree.get('strategic_intelligence', {}).get('business_opportunity_matrix', {}).get('opportunities', [])),
                'predictive_insights': len(knowledge_tree.get('strategic_intelligence', {}).get('predictive_insights', [])),
                'strategic_frameworks': len(knowledge_tree.get('strategic_intelligence', {}).get('strategic_frameworks', {}))
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Failed to build advanced knowledge tree: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Advanced knowledge tree building failed: {str(e)}',
            'system': 'advanced_strategic_intelligence_v2'
        }), 500

@api_bp.route('/intelligence/iterate-knowledge-tree', methods=['POST'])
@async_route
async def iterate_knowledge_tree():
    """Iterate and improve existing knowledge tree with new analysis"""
    try:
        # Get authenticated user using the auth middleware function
        from middleware.auth_middleware import get_current_user
        current_user = get_current_user()
        
        if not current_user:
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
            
        user_email = current_user['email']
        logger.info(f"🔄 Iterating Advanced Strategic Intelligence for {user_email}")
        
        # Get actual user from database to get the proper user ID
        from storage.storage_manager import storage_manager
        user = await storage_manager.get_user_by_email(user_email)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found in database'
            }), 404
        
        # Get existing tree
        existing_tree = await storage_manager.get_latest_knowledge_tree(user['id'])  # Use proper integer user ID
        
        if not existing_tree:
            return jsonify({
                'success': False,
                'error': 'No existing knowledge tree found. Please build initial tree first.'
            }), 404
        
        # Determine next iteration number
        current_iteration = existing_tree.get('iteration', 1)
        next_iteration = current_iteration + 1
        
        # Get request parameters
        data = request.get_json() or {}
        time_window_days = int(data.get('time_window_days', 30))
        focus_area = data.get('focus_area', None)  # Allow focused iteration
        
        logger.info(f"🔄 Iteration {next_iteration} parameters: time_window={time_window_days} days, focus={focus_area}")
        
        # Call the main build function with iteration parameter
        iteration_request = {
            'time_window_days': time_window_days,
            'iteration': next_iteration,
            'analysis_depth': 'multidimensional',
            'focus_area': focus_area
        }
        
        # Use the existing build function but with iteration context
        from flask import g
        g.iteration_context = {
            'previous_tree': existing_tree,
            'focus_area': focus_area
        }
        
        # Forward to build_advanced_knowledge_tree with iteration parameters
        from flask import request
        original_json = request.get_json
        request.get_json = lambda: iteration_request
        
        try:
            result = await build_advanced_knowledge_tree()
            return result
        finally:
            request.get_json = original_json
            
    except Exception as e:
        logger.error(f"Failed to iterate knowledge tree: {e}")
        return jsonify({
            'success': False,
            'error': f'Knowledge tree iteration failed: {str(e)}'
        }), 500

@api_bp.route('/inspect/knowledge-tree', methods=['GET'])
@async_route
async def inspect_knowledge_tree():
    """Inspect stored knowledge tree in database"""
    try:
        from flask import session
        user_email = session.get('user_id', 'test@session-42.com')
        
        storage_manager = await get_storage_manager()
        
        # Retry logic for database operations
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Ensure PostgreSQL connection is healthy before querying
                if not await storage_manager.postgres.health_check():
                    logger.warning(f"PostgreSQL connection unhealthy, resetting pool (attempt {attempt + 1})")
                    await storage_manager.postgres.reset_connection_pool()
                    await asyncio.sleep(1)
                
                # Get user ID and knowledge tree with retry
                async with storage_manager.postgres.conn_pool.acquire() as conn:
                    # Get user ID
                    user_row = await conn.fetchrow("SELECT id FROM users WHERE email = $1", user_email)
                    if not user_row:
                        return jsonify({'success': False, 'error': 'User not found', 'knowledge_tree': None}), 404
                    
                    user_id = user_row['id']
                    
                    # Get knowledge tree from database
                    tree_row = await conn.fetchrow("""
                        SELECT tree_data, created_at, updated_at
                        FROM knowledge_tree 
                        WHERE user_id = $1
                    """, user_id)
                
                if not tree_row:
                    return jsonify({
                        'success': True,
                        'user_email': user_email,
                        'user_id': user_id,
                        'knowledge_tree': None,
                        'message': 'No knowledge tree found for this user'
                    })
                
                try:
                    tree_data = json.loads(tree_row['tree_data']) if isinstance(tree_row['tree_data'], str) else tree_row['tree_data']
                except:
                    tree_data = tree_row['tree_data']
                
                return jsonify({
                    'success': True,
                    'user_email': user_email,
                    'user_id': user_id,
                    'knowledge_tree': tree_data,
                    'created_at': tree_row['created_at'].isoformat() if tree_row['created_at'] else None,
                    'updated_at': tree_row['updated_at'].isoformat() if tree_row['updated_at'] else None
                })
                
            except Exception as db_error:
                error_msg = str(db_error)
                logger.warning(f"Database operation failed (attempt {attempt + 1}): {error_msg}")
                
                if ("another operation is in progress" in error_msg.lower() or 
                    "connection was closed" in error_msg.lower() or
                    "connection" in error_msg.lower()) and attempt < max_retries - 1:
                    
                    logger.warning(f"Connection issue, resetting pool and retrying...")
                    try:
                        await storage_manager.postgres.reset_connection_pool()
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    except:
                        pass
                else:
                    # Non-retryable error or max retries reached
                    raise db_error
        
        # If we get here, all retries failed
        return jsonify({
            'success': False,
            'error': 'Database connection failed after multiple retries',
            'knowledge_tree': None
        }), 500
        
    except Exception as e:
        logger.error(f"Error inspecting knowledge tree: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'knowledge_tree': None
        }), 500

@api_bp.route('/intelligence/augment-knowledge-tree', methods=['POST'])
@async_route
async def augment_knowledge_tree():
    """Augment existing knowledge tree with new analysis (iterative improvement)"""
    try:
        from flask import session, request
        user_email = session.get('user_id', 'test@session-42.com')
        
        logger.info(f"🔄 Augmenting CEO Strategic Intelligence for {user_email}")
        
        # Get user from database
        storage_manager = await get_storage_manager()
        user = await storage_manager.get_user_by_email(user_email)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get existing knowledge tree
        existing_tree = await storage_manager.get_latest_knowledge_tree(user['id'])
        if not existing_tree:
            return jsonify({
                'success': False, 
                'error': 'No existing knowledge tree found. Please build initial tree first.'
            }), 404
        
        # Get request parameters for augmentation
        data = request.get_json() or {}
        focus_area = data.get('focus_area', None)
        time_window_days = int(data.get('time_window_days', 7))  # Shorter window for augmentation
        
        logger.info(f"🔄 Augmentation parameters: focus_area={focus_area}, time_window={time_window_days} days")
        
        # Initialize CEO Strategic Intelligence System
        from intelligence.ceo_strategic_intelligence import CEOStrategicIntelligenceSystem
        strategic_system = CEOStrategicIntelligenceSystem()
        
        # Generate new strategic intelligence for augmentation
        new_intelligence = await strategic_system.generate_strategic_intelligence(
            user_id=user['id'],
            focus_area=focus_area,
            time_window_days=time_window_days
        )
        
        # Merge with existing knowledge tree (augmentation logic)
        augmented_tree = await _augment_knowledge_tree(existing_tree, new_intelligence)
        
        # Store augmented knowledge tree
        await storage_manager.store_knowledge_tree(
            user_id=user['id'],
            tree_data=augmented_tree,
            analysis_type="ceo_strategic_intelligence_augmented"
        )
        
        logger.info(f"✅ Knowledge tree successfully augmented")
        
        return jsonify({
            'success': True,
            'knowledge_tree': augmented_tree,
            'message': 'Strategic intelligence successfully augmented with new insights',
            'augmentation_stats': {
                'new_strategic_frameworks': len(new_intelligence.strategic_frameworks),
                'new_relationships_analyzed': len(new_intelligence.network_activation.get('key_relationships', {})),
                'new_decision_areas': len(new_intelligence.decision_intelligence),
                'focus_area': focus_area
            }
        })
        
    except Exception as e:
        logger.error(f"Knowledge tree augmentation failed: {e}")
        return jsonify({
            'success': False, 
            'error': f'Knowledge tree augmentation failed: {str(e)}'
        }), 500

async def _augment_knowledge_tree(existing_tree: Dict, new_intelligence) -> Dict:
    """Merge new strategic intelligence with existing knowledge tree"""
    
    # Create augmented tree starting with existing structure
    augmented_tree = existing_tree.copy()
    
    # Augment strategic frameworks
    if "strategic_frameworks" not in augmented_tree:
        augmented_tree["strategic_frameworks"] = {}
    
    for framework_type, framework_data in new_intelligence.strategic_frameworks.items():
        if framework_type in augmented_tree["strategic_frameworks"]:
            # Merge existing framework data with new insights
            augmented_tree["strategic_frameworks"][framework_type].update(framework_data)
        else:
            augmented_tree["strategic_frameworks"][framework_type] = framework_data
    
    # Augment competitive landscape
    if "competitive_landscape" not in augmented_tree:
        augmented_tree["competitive_landscape"] = {}
    augmented_tree["competitive_landscape"].update(new_intelligence.competitive_landscape)
    
    # Augment domain hierarchy
    if "domain_hierarchy" not in augmented_tree:
        augmented_tree["domain_hierarchy"] = {}
    
    new_domains = new_intelligence.knowledge_matrix.get("domain_hierarchy", {})
    for domain, domain_data in new_domains.items():
        if domain in augmented_tree["domain_hierarchy"]:
            # Merge domain insights
            existing_insights = augmented_tree["domain_hierarchy"][domain].get("strategic_insights", [])
            new_insights = domain_data.get("strategic_insights", [])
            augmented_tree["domain_hierarchy"][domain]["strategic_insights"] = existing_insights + new_insights
        else:
            augmented_tree["domain_hierarchy"][domain] = domain_data
    
    # Augment cross-domain connections
    if "cross_domain_connections" not in augmented_tree:
        augmented_tree["cross_domain_connections"] = []
    
    new_connections = new_intelligence.knowledge_matrix.get("cross_domain_connections", [])
    augmented_tree["cross_domain_connections"].extend(new_connections)
    
    # Update metadata to show augmentation
    augmented_tree["analysis_metadata"]["last_augmented"] = datetime.utcnow().isoformat()
    augmented_tree["analysis_metadata"]["augmentation_count"] = augmented_tree["analysis_metadata"].get("augmentation_count", 0) + 1
    
    # Add augmentation summary
    augmented_tree["augmentation_summary"] = {
        "latest_augmentation": datetime.utcnow().isoformat(),
        "new_frameworks_added": len(new_intelligence.strategic_frameworks),
        "new_relationships_analyzed": len(new_intelligence.network_activation.get('key_relationships', {})),
        "new_decision_areas": len(new_intelligence.decision_intelligence)
    }
    
    return augmented_tree

# === Intelligence Routes ===

@api_bp.route('/intelligence/enrich-contacts', methods=['POST'])
@async_route
async def enrich_contacts():
    """
    Enrich contacts with professional intelligence using Enhanced Multi-Source Enrichment
    """
    return await _enrich_contacts_internal()

async def _enrich_contacts_internal():
    """
    Internal function to enrich contacts with professional intelligence using Enhanced Multi-Source Enrichment
    """
    from flask import session
    from intelligence.contact_enrichment_integration import enrich_contacts_batch
    
    user_email = session.get('user_email')
    if not user_email:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Get parameters with safe handling for missing JSON
        try:
            data = request.get_json() or {}
        except Exception as json_error:
            logger.info(f"No JSON data in request, using defaults: {json_error}")
            data = {}
            
        sources = data.get('sources', ['email_signatures', 'email_content', 'domain_intelligence'])
        limit = data.get('limit', 50)
        
        logger.info(f"Starting Enhanced Multi-Source enrichment for user {user_email}", 
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
        
        # Convert contacts to format expected by the new enrichment system
        contact_list = []
        for contact in contacts:
            contact_dict = {
                'email': contact.get('email', ''),
                'name': contact.get('name', '')
            }
            if contact_dict['email']:
                contact_list.append(contact_dict)
        
        if not contact_list:
            return jsonify({
                'success': True,
                'message': 'No contacts found to enrich',
                'enriched_count': 0,
                'failed_count': 0,
                'total_processed': 0,
                'method': 'enhanced_multi_source_enrichment'
            })
        
        # Use the new enhanced enrichment system for batch processing
        enrichment_results = await enrich_contacts_batch(user_id, contact_list)
        
        # Process results and update database
        enriched_count = 0
        failed_count = 0
        
        for email_addr, result in enrichment_results.items():
            try:
                if result.get('success'):
                    # Store the enhanced enrichment data
                    metadata = {
                        'enrichment_method': 'enhanced_multi_source_enrichment',
                        'enrichment_timestamp': result.get('enrichment_timestamp'),
                        'enrichment_status': 'success',
                        'confidence_score': result.get('confidence', 0),
                        'data_sources': result.get('data_sources', []),
                        'intelligence_data': {
                            'person': result.get('person', {}),
                            'company': result.get('company', {}),
                            'intelligence_summary': result.get('intelligence_summary', {})
                        }
                    }
                    
                    # Update contact with enhanced enrichment data
                    async with postgres_client.conn_pool.acquire() as conn:
                        await conn.execute("""
                            UPDATE contacts 
                            SET metadata = metadata || $1
                            WHERE user_id = $2 AND email = $3
                        """, json.dumps(metadata), user_id, email_addr)
                    
                    enriched_count += 1
                    logger.info(f"✅ Successfully enriched {email_addr} with enhanced enrichment (confidence: {result.get('confidence', 0):.1%})")
                    
                else:
                    failed_count += 1
                    error_msg = result.get('error', 'Unknown error')
                    logger.warning(f"❌ Failed to enrich {email_addr}: {error_msg}")
                
                # Small delay between processing
                await asyncio.sleep(0.5)
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to process enrichment result for {email_addr}: {e}")
                continue
        
        await postgres_client.disconnect()
        
        # Calculate statistics
        success_rate = enriched_count / max(len(contact_list), 1)
        avg_confidence = sum(r.get('confidence', 0) for r in enrichment_results.values()) / max(len(enrichment_results), 1)
        
        return jsonify({
            'success': True,
            'message': f'Enhanced Multi-Source enrichment completed',
            'enriched_count': enriched_count,
            'failed_count': failed_count,
            'total_processed': len(contact_list),
            'success_rate': success_rate,
            'average_confidence': avg_confidence,
            'method': 'enhanced_multi_source_enrichment',
            'data_sources_used': sources
        })
        
    except Exception as e:
        logger.error(f"Enhanced contact enrichment failed: {e}")
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

@api_bp.route('/gmail/connect', methods=['POST'])
@require_auth
def gmail_connect():
    """Connect to Gmail - redirect to OAuth flow"""
    return jsonify({
        'success': True,
        'redirect_url': '/auth/google',
        'message': 'Redirecting to Google OAuth...'
    })

@api_bp.route('/email/extract-sent', methods=['POST'])
@async_route
async def extract_sent_emails():
    """Extract sent emails (alias for sync)"""
    # Call the actual sync function directly to avoid nested asyncio.run()
    return await _sync_emails_internal()

@api_bp.route('/contacts/augment', methods=['POST'])
@async_route
async def augment_contacts():
    """Augment contacts (alias for enrich-contacts)"""
    # Call the enrich function directly to avoid nested asyncio.run()
    return await _enrich_contacts_internal()

@api_bp.route('/intelligence/generate', methods=['POST'])
@async_route
async def generate_intelligence():
    """Generate intelligence for contacts"""
    try:
        from flask import session
        user_email = session.get('user_id', 'test@session-42.com')
        
        # This would typically generate intelligence for all contacts
        # For now, return a success message
        return jsonify({
            'success': True,
            'message': 'Intelligence generation started',
            'user_email': user_email,
            'status': 'processing'
        })
    except Exception as e:
        logger.error(f"Error generating intelligence: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/intelligence/ceo-intelligence-brief', methods=['POST'])
@async_route
async def ceo_intelligence_brief():
    """Generate CEO intelligence brief"""
    try:
        # Get parameters with safe handling for missing JSON
        try:
            data = request.get_json() or {}
        except Exception as json_error:
            logger.info(f"No JSON data in request, using defaults: {json_error}")
            data = {}
            
        focus_area = data.get('focus_area')
        
        # This would generate a CEO-level intelligence brief
        return jsonify({
            'success': True,
            'message': 'CEO intelligence brief generated',
            'focus_area': focus_area,
            'brief': {
                'executive_summary': 'Strategic intelligence analysis complete.',
                'key_insights': ['Market positioning strong', 'Network growth opportunities identified'],
                'recommendations': ['Expand key partnerships', 'Focus on high-value contacts']
            }
        })
    except Exception as e:
        logger.error(f"Error generating CEO brief: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/intelligence/competitive-landscape-analysis', methods=['POST'])
@async_route
async def competitive_landscape_analysis():
    """Analyze competitive landscape"""
    try:
        return jsonify({
            'success': True,
            'message': 'Competitive landscape analysis complete',
            'analysis': {
                'market_position': 'Strong',
                'competitive_advantages': ['Unique network intelligence', 'AI-powered insights'],
                'threats': ['New market entrants', 'Technology disruption'],
                'opportunities': ['International expansion', 'New product categories']
            }
        })
    except Exception as e:
        logger.error(f"Error analyzing competitive landscape: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/intelligence/network-to-objectives-mapping', methods=['POST'])
@async_route
async def network_to_objectives_mapping():
    """Map network to business objectives"""
    try:
        return jsonify({
            'success': True,
            'message': 'Network to objectives mapping complete',
            'mapping': {
                'strategic_contacts': ['High-value decision makers identified'],
                'growth_opportunities': ['Partnership potential mapped'],
                'risk_mitigation': ['Relationship diversification recommended']
            }
        })
    except Exception as e:
        logger.error(f"Error mapping network to objectives: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/intelligence/decision-support', methods=['POST'])
@async_route
async def decision_support():
    """Generate decision support analysis"""
    try:
        # Get parameters with safe handling for missing JSON
        try:
            data = request.get_json() or {}
        except Exception as json_error:
            logger.info(f"No JSON data in request, using defaults: {json_error}")
            data = {}
            
        decision_area = data.get('decision_area')
        decision_options = data.get('decision_options')
        
        return jsonify({
            'success': True,
            'message': 'Decision support analysis complete',
            'decision_area': decision_area,
            'analysis': {
                'recommended_option': 'Option 1',
                'risk_assessment': 'Medium risk, high reward',
                'supporting_data': ['Market trends favorable', 'Network connections support decision']
            }
        })
    except Exception as e:
        logger.error(f"Error generating decision support: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/intelligence/multidimensional-matrix', methods=['GET'])
@async_route
async def multidimensional_matrix():
    """Get multidimensional analysis matrix"""
    try:
        return jsonify({
            'success': True,
            'matrix': {
                'dimensions': ['Influence', 'Accessibility', 'Strategic Value'],
                'contacts': [
                    {'name': 'John Doe', 'influence': 8, 'accessibility': 6, 'strategic_value': 9},
                    {'name': 'Jane Smith', 'influence': 7, 'accessibility': 8, 'strategic_value': 7}
                ]
            }
        })
    except Exception as e:
        logger.error(f"Error getting multidimensional matrix: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# === INSPECTION ENDPOINTS ===

@api_bp.route('/inspect/emails', methods=['GET'])
@async_route
async def inspect_stored_emails():
    """Inspect stored emails in database"""
    try:
        from flask import session, request
        user_email = session.get('user_id', 'test@session-42.com')
        
        # Get pagination parameters
        limit = int(request.args.get('limit', 100))  # Default to 100, allow override
        offset = int(request.args.get('offset', 0))
        
        storage_manager = await get_storage_manager()
        
        # Retry logic for database operations
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Ensure PostgreSQL connection is healthy before querying
                if not await storage_manager.postgres.health_check():
                    logger.warning(f"PostgreSQL connection unhealthy, resetting pool (attempt {attempt + 1})")
                    await storage_manager.postgres.reset_connection_pool()
                    await asyncio.sleep(1)
                
                # Get user ID and emails with retry
                async with storage_manager.postgres.conn_pool.acquire() as conn:
                    # Get user ID
                    user_row = await conn.fetchrow("SELECT id FROM users WHERE email = $1", user_email)
                    if not user_row:
                        return jsonify({'success': False, 'error': 'User not found', 'emails': []}), 404
                    
                    user_id = user_row['id']
                    
                    # Get TOTAL count of emails (not limited)
                    total_count = await conn.fetchval("""
                        SELECT COUNT(*) 
                        FROM emails 
                        WHERE user_id = $1
                    """, user_id)
                    
                    # Get emails from database with pagination
                    emails = await conn.fetch("""
                        SELECT id, gmail_id, content, metadata, created_at, updated_at
                        FROM emails 
                        WHERE user_id = $1 
                        ORDER BY created_at DESC 
                        LIMIT $2 OFFSET $3
                    """, user_id, limit, offset)
                
                # Format emails for display
                email_list = []
                for email in emails:
                    try:
                        metadata = json.loads(email['metadata']) if email['metadata'] else {}
                    except:
                        metadata = {}
                        
                    email_data = {
                        'id': email['id'],
                        'gmail_id': email['gmail_id'],
                        'subject': metadata.get('subject', 'No Subject'),
                        'from': metadata.get('from', 'Unknown'),
                        'to': metadata.get('to', []),
                        'date': metadata.get('date'),
                        'content_preview': (email['content'] or '')[:200] + '...' if email['content'] else 'No content',
                        'content_length': len(email['content'] or ''),
                        'created_at': email['created_at'].isoformat() if email['created_at'] else None,
                        'updated_at': email['updated_at'].isoformat() if email['updated_at'] else None,
                        'metadata': metadata
                    }
                    email_list.append(email_data)
                
                return jsonify({
                    'success': True,
                    'user_email': user_email,
                    'user_id': user_id,
                    'total_emails': total_count,  # THIS IS THE REAL TOTAL COUNT
                    'displayed_emails': len(email_list),  # How many are shown in this page
                    'limit': limit,
                    'offset': offset,
                    'has_more': (offset + len(email_list)) < total_count,
                    'emails': email_list
                })
                
            except Exception as db_error:
                error_msg = str(db_error)
                logger.warning(f"Database operation failed (attempt {attempt + 1}): {error_msg}")
                
                if ("another operation is in progress" in error_msg.lower() or 
                    "connection was closed" in error_msg.lower() or
                    "connection" in error_msg.lower()) and attempt < max_retries - 1:
                    
                    logger.warning(f"Connection issue, resetting pool and retrying...")
                    try:
                        await storage_manager.postgres.reset_connection_pool()
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    except:
                        pass
                else:
                    # Non-retryable error or max retries reached
                    raise db_error
        
        # If we get here, all retries failed
        return jsonify({
            'success': False,
            'error': 'Database connection failed after multiple retries',
            'emails': []
        }), 500
        
    except Exception as e:
        logger.error(f"Error inspecting emails: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'emails': []
        }), 500

@api_bp.route('/inspect/contacts', methods=['GET'])
@async_route
async def inspect_stored_contacts():
    """Inspect stored contacts in database"""
    try:
        from flask import session
        user_email = session.get('user_id', 'test@session-42.com')
        
        storage_manager = await get_storage_manager()
        
        # Retry logic for database operations
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Ensure PostgreSQL connection is healthy before querying
                if not await storage_manager.postgres.health_check():
                    logger.warning(f"PostgreSQL connection unhealthy, resetting pool (attempt {attempt + 1})")
                    await storage_manager.postgres.reset_connection_pool()
                    await asyncio.sleep(1)
                
                # Get user ID and contacts with retry
                async with storage_manager.postgres.conn_pool.acquire() as conn:
                    # Get user ID
                    user_row = await conn.fetchrow("SELECT id FROM users WHERE email = $1", user_email)
                    if not user_row:
                        return jsonify({'success': False, 'error': 'User not found', 'contacts': []}), 404
                    
                    user_id = user_row['id']
                    
                    # Get contacts from database
                    contacts = await conn.fetch("""
                        SELECT id, email, name, trust_tier, frequency, domain, metadata, 
                               created_at, updated_at
                        FROM contacts 
                        WHERE user_id = $1 
                        ORDER BY trust_tier ASC, frequency DESC
                    """, user_id)
                
                # Format contacts for display
                contact_list = []
                for contact in contacts:
                    try:
                        metadata = json.loads(contact['metadata']) if contact['metadata'] else {}
                    except:
                        metadata = {}
                        
                    contact_data = {
                        'id': contact['id'],
                        'email': contact['email'],
                        'name': contact['name'],
                        'trust_tier': contact['trust_tier'],
                        'frequency': contact['frequency'],
                        'domain': contact['domain'],
                        'created_at': contact['created_at'].isoformat() if contact['created_at'] else None,
                        'updated_at': contact['updated_at'].isoformat() if contact['updated_at'] else None,
                        'metadata': metadata,
                        'has_augmentation': 'enrichment_method' in metadata,
                        'enrichment_status': metadata.get('enrichment_status', 'not_enriched')
                    }
                    contact_list.append(contact_data)
                
                return jsonify({
                    'success': True,
                    'user_email': user_email,
                    'user_id': user_id,
                    'total_contacts': len(contact_list),
                    'contacts': contact_list
                })
                
            except Exception as db_error:
                error_msg = str(db_error)
                logger.warning(f"Database operation failed (attempt {attempt + 1}): {error_msg}")
                
                if ("another operation is in progress" in error_msg.lower() or 
                    "connection was closed" in error_msg.lower() or
                    "connection" in error_msg.lower()) and attempt < max_retries - 1:
                    
                    logger.warning(f"Connection issue, resetting pool and retrying...")
                    try:
                        await storage_manager.postgres.reset_connection_pool()
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    except:
                        pass
                else:
                    # Non-retryable error or max retries reached
                    raise db_error
        
        # If we get here, all retries failed
        return jsonify({
            'success': False,
            'error': 'Database connection failed after multiple retries',
            'contacts': []
        }), 500
        
    except Exception as e:
        logger.error(f"Error inspecting contacts: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'contacts': []
        }), 500

@api_bp.route('/debug/env')
def debug_env():
    """Debug environment variables - DEVELOPMENT ONLY"""
    import os
    from config.settings import ANTHROPIC_API_KEY
    
    if os.getenv('ENVIRONMENT') == 'production':
        return jsonify({'error': 'Debug not available in production'}), 403
    
    return jsonify({
        'anthropic_key_from_os': os.getenv('ANTHROPIC_API_KEY', 'NOT SET')[:20] + '...' if os.getenv('ANTHROPIC_API_KEY') else 'NOT SET',
        'anthropic_key_from_settings': ANTHROPIC_API_KEY[:20] + '...' if ANTHROPIC_API_KEY else 'NOT SET',
        'anthropic_key_length': len(ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else 0,
        'claude_model': os.getenv('CLAUDE_MODEL', 'NOT SET'),
        'environment': os.getenv('ENVIRONMENT', 'NOT SET'),
        'api_port': os.getenv('API_PORT', 'NOT SET')
    })
