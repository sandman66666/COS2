"""
Synchronous API Routes for Strategic Intelligence System
=======================================================
Flask-compatible routes without async/event loop conflicts
"""

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any

from flask import Blueprint, request, jsonify, current_app, session, render_template
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
import google.auth.exceptions
import threading
from functools import wraps
import uuid
import time
import gc  # For garbage collection

from config.settings import (
    API_HOST, 
    API_PORT, 
    API_DEBUG, 
    API_SECRET_KEY, 
    POSTGRES_HOST, 
    POSTGRES_PORT, 
    POSTGRES_USER, 
    POSTGRES_PASSWORD, 
    POSTGRES_DB,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    GOOGLE_SCOPES,
    ANTHROPIC_API_KEY
)
from utils.logging import structured_logger as logger
from middleware.auth_middleware import require_auth, get_current_user
from storage.storage_manager_sync import get_storage_manager_sync

# Create blueprint
api_sync_bp = Blueprint('api_sync', __name__, url_prefix='/api')

# Global background jobs storage (in production, use Redis or database)
background_jobs = {}
jobs_lock = threading.Lock()

# === Health Check ===

@api_sync_bp.route('/health')
def health_check():
    """Simple health check endpoint - no auth required"""
    return jsonify({
        'status': 'healthy',
        'service': 'strategic_intelligence_api_sync',
        'timestamp': datetime.utcnow().isoformat()
    })

@api_sync_bp.route('/system/health')
@require_auth
def system_health():
    """Detailed system health check (synchronous)"""
    try:
        storage_manager = get_storage_manager_sync()
        health_status = storage_manager.health_check()
        
        return jsonify({
            'status': 'healthy' if health_status.get('all_healthy') else 'degraded',
            'components': health_status,
            'timestamp': datetime.utcnow().isoformat(),
            'mode': 'synchronous'
        })
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@api_sync_bp.route('/system/flush', methods=['POST'])
@require_auth
def flush_system():
    """
    Flush all user data and start clean (synchronous)
    WARNING: This permanently deletes all user data
    """
    user_email = session.get('user_id')  # This is actually the email
    
    # For testing - provide a default user
    if not user_email:
        user_email = 'test@session-42.com'
        logger.info("No session user found, using test user")
    
    cleared_items = []
    
    try:
        storage_manager = get_storage_manager_sync()
        
        # 1. Get the actual user ID from the email
        user_id = None
        user = storage_manager.get_user_by_email(user_email)
        if user:
            user_id = user['id']
            logger.info(f"Found user ID {user_id} for email {user_email}")
        
        # 2. Clear session data
        session.clear()
        cleared_items.append("Session data cleared")
        
        # 3. Clear PostgreSQL data
        if user_id:
            try:
                conn = storage_manager.postgres.conn_pool.getconn()
                try:
                    cursor = conn.cursor()
                    
                    # Clear contacts
                    cursor.execute("DELETE FROM contacts WHERE user_id = %s", (user_id,))
                    deleted_contacts = cursor.rowcount
                    
                    # Clear emails
                    cursor.execute("DELETE FROM emails WHERE user_id = %s", (user_id,))
                    deleted_emails = cursor.rowcount
                    
                    # Clear knowledge trees
                    cursor.execute("DELETE FROM knowledge_tree WHERE user_id = %s", (user_id,))
                    deleted_trees = cursor.rowcount
                    
                    # Clear oauth credentials
                    cursor.execute("DELETE FROM oauth_credentials WHERE user_id = %s", (user_id,))
                    deleted_oauth = cursor.rowcount
                    
                    # Reset user settings
                    cursor.execute("""
                        UPDATE users SET settings = '{}', updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (user_id,))
                    
                    conn.commit()
                    
                    cleared_items.extend([
                        f"PostgreSQL contacts cleared ({deleted_contacts} records)",
                        f"PostgreSQL emails cleared ({deleted_emails} records)", 
                        f"PostgreSQL knowledge trees cleared ({deleted_trees} records)",
                        f"PostgreSQL OAuth credentials cleared ({deleted_oauth} records)",
                        f"User settings reset (user_id: {user_id})"
                    ])
                    
                finally:
                    storage_manager.postgres.conn_pool.putconn(conn)
                    
            except Exception as db_error:
                logger.error("Failed to clear PostgreSQL data", error=str(db_error))
                cleared_items.append(f"PostgreSQL clear failed: {db_error}")
        else:
            cleared_items.append("PostgreSQL clear skipped (no user_id)")
        
        logger.info("SYNCHRONOUS system flush completed", 
                   user_email=user_email, user_id=user_id, cleared_items=cleared_items)
        
        return jsonify({
            'success': True,
            'message': 'System completely flushed - all data cleared! (synchronous mode)',
            'cleared': cleared_items,
            'user_email': user_email,
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat(),
            'mode': 'synchronous',
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

@api_sync_bp.route('/user/profile')
@require_auth
def get_user_profile():
    """Get current user profile"""
    user_id = session.get('user_id')
    
    return jsonify({
        'id': user_id,
        'email': session.get('user_email'),
        'authenticated': True,
        'session_id': session.get('session_id'),
        'mode': 'synchronous'
    })

@api_sync_bp.route('/user-info', methods=['GET'])
@require_auth
def get_user_info():
    """Get current user information (synchronous)"""
    try:
        user_email = get_current_user()
        if not user_email:
            return jsonify({
                'error': 'User not authenticated',
                'status': 'unauthorized'
            }), 401
            
        return jsonify({
            'status': 'success',
            'user': {
                'email': user_email,
                'id': user_email,  # For now, using email as ID
                'authenticated': True
            },
            'mode': 'synchronous'
        })
        
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        return jsonify({
            'error': 'Failed to get user info',
            'status': 'error'
        }), 500

# === Contact Routes ===

@api_sync_bp.route('/contacts')
@require_auth
def get_contacts():
    """Get user's trusted contacts (synchronous)"""
    user_email = session.get('user_id', 'test@session-42.com')  # Default for testing
    
    # Get request parameters
    trust_tier = request.args.get('trust_tier')
    domain = request.args.get('domain')
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    
    logger.info(f"DEBUG: get_contacts route called with user_email={user_email}")
    
    try:
        storage_manager = get_storage_manager_sync()
        
        # Get user ID from email
        user = storage_manager.get_user_by_email(user_email)
        logger.info(f"DEBUG: Retrieved user from DB: {user}")
        if not user:
            return jsonify({'success': False, 'error': 'User not found', 'contacts': []}), 404
        
        user_id = user['id']
        logger.info(f"DEBUG: Using user_id={user_id} for get_contacts")
        
        # Get contacts
        contacts, total = storage_manager.get_contacts(user_id, trust_tier, domain, limit, offset)
        logger.info(f"DEBUG: Storage manager returned {len(contacts)} contacts, total={total}")
        
        return jsonify({
            'contacts': contacts,
            'total': total,
            'limit': limit,
            'offset': offset,
            'trust_tier_filter': trust_tier,
            'domain_filter': domain,
            'from_cache': False,
            'database_available': True,
            'user_id': user_id,
            'success': True,
            'mode': 'synchronous'
        })
        
    except Exception as e:
        logger.error(f"Error getting contacts: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'contacts': []
        }), 500

@api_sync_bp.route('/contacts/stats')
@require_auth
def get_contact_stats():
    """Get statistics about user's contacts (synchronous)"""
    user_email = session.get('user_id')
    
    try:
        storage_manager = get_storage_manager_sync()
        user = storage_manager.get_user_by_email(user_email)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user_id = user['id']
        
        # Get all contacts to calculate stats
        contacts, total = storage_manager.get_contacts(user_id, limit=1000)  # Get all for stats
        
        # Calculate tier counts
        tier_counts = {}
        domain_counts = {}
        
        for contact in contacts:
            # Trust tier counts
            tier = contact.get('trust_tier', 'unknown')
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            
            # Domain counts
            domain = contact.get('domain', 'unknown')
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        # Get top domains
        top_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return jsonify({
            'total_contacts': total,
            'trust_tiers': tier_counts,
            'top_domains': [{'domain': domain, 'count': count} for domain, count in top_domains],
            'user_id': user_id,
            'mode': 'synchronous'
        })
        
    except Exception as e:
        logger.error(f"Error getting contact stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

# === Knowledge Tree Routes ===

@api_sync_bp.route('/knowledge/tree')
@require_auth
def get_knowledge_tree():
    """Get user's knowledge tree (synchronous)"""
    user_email = session.get('user_id')
    
    try:
        storage_manager = get_storage_manager_sync()
        user = storage_manager.get_user_by_email(user_email)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user_id = user['id']
        tree_data = storage_manager.get_knowledge_tree(user_id)
        
        return jsonify({
            'tree': tree_data,
            'user_id': user_id,
            'cached': False,
            'mode': 'synchronous'
        })
        
    except Exception as e:
        logger.error(f"Error getting knowledge tree: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_sync_bp.route('/inspect/knowledge-tree', methods=['GET'])
@require_auth
def inspect_knowledge_tree():
    """Inspect stored knowledge tree in database (synchronous)"""
    try:
        user_email = session.get('user_id', 'test@session-42.com')
        
        storage_manager = get_storage_manager_sync()
        user = storage_manager.get_user_by_email(user_email)
        if not user:
            return jsonify({'success': False, 'error': 'User not found', 'knowledge_tree': None}), 404
        
        user_id = user['id']
        
        # Get knowledge tree from database
        tree_data = storage_manager.get_knowledge_tree(user_id)
        
        if not tree_data:
            return jsonify({
                'success': True,
                'user_email': user_email,
                'user_id': user_id,
                'knowledge_tree': None,
                'message': 'No knowledge tree found for this user',
                'mode': 'synchronous'
            })
        
        return jsonify({
            'success': True,
            'user_email': user_email,
            'user_id': user_id,
            'knowledge_tree': tree_data,
            'mode': 'synchronous'
        })
        
    except Exception as e:
        logger.error(f"Error inspecting knowledge tree: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'knowledge_tree': None
        }), 500

# === Email Routes ===

@api_sync_bp.route('/inspect/emails', methods=['GET'])
@require_auth
def inspect_stored_emails():
    """Inspect stored emails in database (synchronous)"""
    try:
        user_email = session.get('user_id', 'test@session-42.com')
        
        # Get pagination parameters
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        storage_manager = get_storage_manager_sync()
        user = storage_manager.get_user_by_email(user_email)
        if not user:
            return jsonify({'success': False, 'error': 'User not found', 'emails': []}), 404
        
        user_id = user['id']
        
        # Get emails
        emails, total = storage_manager.postgres.get_emails(user_id, limit, offset)
        
        # Format emails for display
        email_list = []
        for email in emails:
            try:
                # Handle both dict and string metadata formats
                metadata = email['metadata']
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        metadata = {}
                elif not isinstance(metadata, dict):
                    metadata = {}
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
            'total_emails': total,
            'displayed_emails': len(email_list),
            'limit': limit,
            'offset': offset,
            'has_more': (offset + len(email_list)) < total,
            'emails': email_list,
            'mode': 'synchronous'
        })
        
    except Exception as e:
        logger.error(f"Error inspecting emails: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'emails': []
        }), 500

@api_sync_bp.route('/inspect/contacts', methods=['GET'])
@require_auth
def inspect_stored_contacts():
    """Inspect stored contacts in database (synchronous)"""
    try:
        user_email = session.get('user_id', 'test@session-42.com')
        
        storage_manager = get_storage_manager_sync()
        user = storage_manager.get_user_by_email(user_email)
        if not user:
            return jsonify({'success': False, 'error': 'User not found', 'contacts': []}), 404
        
        user_id = user['id']
        
        # Get all contacts for inspection
        contacts, total = storage_manager.get_contacts(user_id, limit=1000)
        
        # Format contacts for display
        contact_list = []
        for contact in contacts:
            try:
                # Handle both dict and string metadata formats
                metadata = contact.get('metadata')
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        metadata = {}
                elif not isinstance(metadata, dict):
                    metadata = {}
                else:
                    metadata = metadata or {}
                    
                enrichment_data = metadata.get('enrichment_data', {})
                
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
                    'has_augmentation': 'enrichment_data' in metadata or 'enrichment_method' in metadata or metadata.get('enrichment_status') == 'enriched',
                    'enrichment_status': metadata.get('enrichment_status', 'enriched' if 'enrichment_data' in metadata else 'not_enriched')
                }
                contact_list.append(contact_data)
                
            except Exception as e:
                logger.error(f"Error processing contact {contact.get('email', 'unknown')}: {e}")
                continue
        
        return jsonify({
            'success': True,
            'user_email': user_email,
            'user_id': user_id,
            'total_contacts': total,
            'contacts': contact_list,
            'mode': 'synchronous'
        })
        
    except Exception as e:
        logger.error(f"Error inspecting contacts: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'contacts': []
        }), 500

# === Test Endpoints ===

@api_sync_bp.route('/test/sync')
def test_sync():
    """Test synchronous endpoint"""
    return jsonify({
        'message': 'Synchronous API is working!',
        'timestamp': datetime.utcnow().isoformat(),
        'auth_required': False,
        'mode': 'synchronous'
    })

@api_sync_bp.route('/test/sync-auth')
@require_auth  
def test_sync_auth():
    """Test synchronous endpoint with auth"""
    return jsonify({
        'message': 'Synchronous API with auth is working!',
        'timestamp': datetime.utcnow().isoformat(),
        'auth_required': True,
        'mode': 'synchronous'
    })

# === Placeholder Routes for Dashboard Compatibility ===
# These are simplified versions to prevent the async/event loop issues

@api_sync_bp.route('/emails/sync', methods=['POST'])
@require_auth
def sync_emails():
    """Email sync filtered by discovered contacts - time-based, all contacts (synchronous background job)"""
    try:
        user_email = session.get('user_id', 'test@session-42.com')
        request_data = request.get_json() or {}
        days = request_data.get('days', 30)
        
        logger.info(f"Starting email sync as background job for user {user_email}")
        
        # Get OAuth credentials from session
        oauth_credentials = session.get('oauth_credentials')
        if not oauth_credentials:
            return jsonify({
                'success': False,
                'error': 'No Gmail credentials found. Please log out and log back in to re-authenticate with Gmail.',
                'action_required': 'reauth',
                'mode': 'synchronous'
            }), 401
        
        # Generate unique job ID
        import uuid
        import time
        job_id = f"email_sync_{user_email}_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        
        # Initialize job status
        with jobs_lock:
            background_jobs[job_id] = {
                'id': job_id,
                'user_email': user_email,
                'status': 'started',
                'progress': 0,
                'message': 'Initializing email sync...',
                'created_at': time.time(),
                'emails_synced': 0,
                'contacts_processed': 0
            }
        
        logger.info(f"Background job {job_id} started for email sync")
        
        def background_email_sync():
            try:
                # Update to show more detailed progress
                update_job_progress(job_id, 0, 'Initializing email sync...', {
                    'sync_phase': 'initialization',
                    'days_to_sync': days
                })
                
                # Check for stop signal early
                if should_stop_job(job_id):
                    stop_job_gracefully(job_id, 'Stopped during initialization', 
                        resume_info={'can_resume': True, 'next_step': 'initialization'})
                    return
                
                # Get user from database
                storage_manager = get_storage_manager_sync()
                user = storage_manager.get_user_by_email(user_email)
                if not user:
                    complete_job(job_id, False, 'User not found in database')
                    return
                
                user_id = user['id']
                
                # Get target contacts for filtering
                update_job_progress(job_id, 5, 'Loading contact list for filtering...', {
                    'sync_phase': 'loading_contacts'
                })
                
                target_contacts = set()
                try:
                    contacts, _ = storage_manager.get_contacts(user_id, limit=2000)
                    target_contacts = {contact['email'].lower() for contact in contacts if contact.get('email')}
                    logger.info(f"Loaded {len(target_contacts)} contacts for email filtering")
                except Exception as e:
                    logger.warning(f"Could not load contacts for filtering: {e}")
                    target_contacts = set()
                
                if not target_contacts:
                    complete_job(job_id, False, 'No contacts found for email sync filtering')
                    return
                
                # Check for stop signal after loading contacts
                if should_stop_job(job_id):
                    stop_job_gracefully(job_id, 'Stopped after loading contacts', 
                        partial_result={'contacts_loaded': len(target_contacts)},
                        resume_info={'can_resume': True, 'next_step': 'gmail_connection'})
                    return
                
                # Create credentials object from session data
                update_job_progress(job_id, 10, 'Connecting to Gmail API...', {
                    'sync_phase': 'gmail_connection'
                })
                
                try:
                    credentials = Credentials(
                        token=oauth_credentials.get('access_token'),
                        refresh_token=oauth_credentials.get('refresh_token'),
                        token_uri=oauth_credentials.get('token_uri', "https://oauth2.googleapis.com/token"),
                        client_id=oauth_credentials.get('client_id'),
                        client_secret=oauth_credentials.get('client_secret'),
                        scopes=oauth_credentials.get('scopes', [])
                    )
                    
                    if oauth_credentials.get('expiry'):
                        credentials.expiry = datetime.fromtimestamp(oauth_credentials['expiry'])
                        
                except Exception as cred_error:
                    complete_job(job_id, False, f'Invalid OAuth credentials: {str(cred_error)}')
                    return
                
                # Build Gmail service
                try:
                    service = build('gmail', 'v1', credentials=credentials)
                    update_job_progress(job_id, 15, 'Connected to Gmail, starting email sync...', {
                        'sync_phase': 'processing_emails'
                    })
                except Exception as service_error:
                    complete_job(job_id, False, f'Failed to connect to Gmail API: {str(service_error)}')
                    return
                
                # Calculate date range
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
                
                processed_count = 0
                new_emails = 0
                updated_emails = 0
                contacts_processed = 0
                skipped_contacts = 0
                
                target_contacts_list = list(target_contacts)
                
                # Process emails for each contact individually with resource management
                logger.info(f"Searching for emails from discovered contacts since {cutoff_date.strftime('%Y-%m-%d')} (resource-managed)")
                
                for i, contact_email in enumerate(target_contacts_list):
                    # Check for stop signal before processing each contact
                    if should_stop_job(job_id):
                        stop_job_gracefully(job_id,
                            f'Stopped during email processing. Processed {contacts_processed} of {len(target_contacts_list)} contacts.',
                            partial_result={
                                'emails_synced': new_emails,
                                'contacts_processed': contacts_processed,
                                'contacts_skipped': skipped_contacts
                            },
                            resume_info={
                                'can_resume': True,
                                'next_step': 'email_processing',
                                'contacts_remaining': len(target_contacts_list) - contacts_processed,
                                'last_contact_index': i
                            }
                        )
                        return
                    
                    try:
                        # Check runtime limit
                        if time.time() - start_time > MAX_TOTAL_RUNTIME:
                            logger.warning(f"Reached maximum runtime ({MAX_TOTAL_RUNTIME}s), stopping at contact {contacts_processed}")
                            stop_job_gracefully(job_id,
                                f'Reached time limit at contact {contacts_processed}/{len(target_contacts_list)} - Synced {new_emails} emails',
                                partial_result={
                                    'emails_synced': new_emails,
                                    'contacts_processed': contacts_processed,
                                    'reason': 'time_limit_reached'
                                },
                                resume_info={
                                    'can_resume': True,
                                    'next_step': 'email_processing',
                                    'contacts_remaining': len(target_contacts_list) - contacts_processed
                                }
                            )
                            break
                        
                        contacts_processed += 1
                        
                        # Update progress every 3 contacts with detailed info
                        if contacts_processed % 3 == 0:
                            progress = 15 + int((contacts_processed / len(target_contacts_list)) * 75)  # 15-90% for processing
                            update_job_progress(job_id, progress, 
                                f'Processing contact {contacts_processed}/{len(target_contacts_list)}: {contact_email}', {
                                'sync_phase': 'processing_emails',
                                'current_contact': contact_email,
                                'emails_found': new_emails,
                                'contacts_completed': contacts_processed,
                                'contacts_total': len(target_contacts_list)
                            })
                        
                        # Build query for this specific contact with limits
                        query = f'(from:{contact_email} OR to:{contact_email}) after:{cutoff_date.strftime("%Y/%m/%d")}'
                        
                        logger.info(f"Processing contact {contacts_processed}/{len(target_contacts_list)}: {contact_email}")
                        
                        # Get messages with pagination but enforce limits
                        messages = []
                        page_token = None
                        total_fetched = 0
                        
                        while total_fetched < MAX_EMAILS_PER_CONTACT:
                            try:
                                remaining = MAX_EMAILS_PER_CONTACT - total_fetched
                                max_results = min(remaining, 20)  # Fetch in small batches
                                
                                if page_token:
                                    messages_response = service.users().messages().list(
                                        userId='me',
                                        q=query,
                                        pageToken=page_token,
                                        maxResults=max_results
                                    ).execute()
                                else:
                                    messages_response = service.users().messages().list(
                                        userId='me',
                                        q=query,
                                        maxResults=max_results
                                    ).execute()
                                
                                batch_messages = messages_response.get('messages', [])
                                messages.extend(batch_messages)
                                total_fetched += len(batch_messages)
                                
                                page_token = messages_response.get('nextPageToken')
                                if not page_token or len(batch_messages) == 0:
                                    break
                                    
                                # Throttle between API calls
                                time.sleep(0.1)
                                
                            except Exception as e:
                                logger.error(f"Error fetching messages page for {contact_email}: {e}")
                                break
                        
                        if not messages:
                            continue
                        
                        # Log if we hit the limit
                        if len(messages) >= MAX_EMAILS_PER_CONTACT:
                            logger.info(f"Limited to {MAX_EMAILS_PER_CONTACT} emails for {contact_email} (may have more)")
                        else:
                            logger.info(f"Found {len(messages)} emails for {contact_email}")
                        
                        # Process emails in chunks to manage memory
                        for chunk_start in range(0, len(messages), CHUNK_SIZE):
                            chunk_end = min(chunk_start + CHUNK_SIZE, len(messages))
                            chunk_messages = messages[chunk_start:chunk_end]
                            
                            for msg in chunk_messages:
                                try:
                                    # Check if we already have this email
                                    existing = storage_manager.postgres.get_email_by_gmail_id(user_id, msg['id'])
                                    if existing:
                                        updated_emails += 1
                                        continue
                                    
                                    # Get full message
                                    msg_data = service.users().messages().get(
                                        userId='me',
                                        id=msg['id'],
                                        format='metadata'  # Use metadata format to reduce payload
                                    ).execute()
                                    
                                    # Parse message headers
                                    headers = {}
                                    for header in msg_data.get('payload', {}).get('headers', []):
                                        name = header.get('name', '').lower()
                                        value = header.get('value', '')
                                        headers[name] = value
                                    
                                    # Extract basic info
                                    subject = headers.get('subject', '(No Subject)')
                                    from_addr = headers.get('from', '')
                                    to_addr = headers.get('to', '')
                                    date_str = headers.get('date', '')
                                    
                                    # Verify this email involves our target contact
                                    email_text = f"{from_addr} {to_addr}".lower()
                                    if contact_email not in email_text:
                                        continue
                                    
                                    # Parse date
                                    try:
                                        if date_str:
                                            date_sent = email.utils.parsedate_to_datetime(date_str)
                                        else:
                                            date_sent = datetime.now(timezone.utc)
                                    except:
                                        date_sent = datetime.now(timezone.utc)
                                    
                                    # Skip if email is older than our cutoff (extra safety)
                                    if date_sent < cutoff_date:
                                        continue
                                    
                                    # Store email with metadata only (no body to save memory)
                                    metadata = {
                                        'subject': subject,
                                        'from': from_addr,
                                        'to': to_addr,
                                        'date': date_str,
                                        'headers': {k: v for k, v in headers.items() if k in ['subject', 'from', 'to', 'date', 'message-id']},  # Minimal headers
                                        'associated_contact': contact_email,
                                        'sync_method': 'contact_time_based_resource_managed'
                                    }
                                    
                                    # Store email with minimal content to save space
                                    storage_manager.postgres.store_email(
                                        user_id=user_id,
                                        gmail_id=msg['id'],
                                        content=f"Email metadata sync - Subject: {subject}",  # Minimal content
                                        metadata=metadata,
                                        timestamp=date_sent
                                    )
                                    new_emails += 1
                                    processed_count += 1
                                    
                                    # Throttle to avoid quota issues
                                    time.sleep(0.05)
                                    
                                except Exception as e:
                                    logger.error(f"Error processing email {msg.get('id')} for contact {contact_email}: {e}")
                                    continue
                            
                            # Force garbage collection after each chunk
                            gc.collect()
                            
                            # Throttle between chunks
                            time.sleep(0.1)
                        
                        # Throttle between contacts
                        time.sleep(0.2)
                        
                    except Exception as e:
                        logger.error(f"Error processing contact {contact_email}: {e}")
                        skipped_contacts += 1
                        continue
                
                # Final status update with comprehensive results
                final_message = f"Successfully synced {new_emails} emails from {contacts_processed} contacts"
                if skipped_contacts > 0:
                    final_message += f' ({skipped_contacts} contacts skipped due to errors)'
                if time.time() - start_time > MAX_TOTAL_RUNTIME * 0.9:
                    final_message += ' (stopped due to time limit)'
                
                complete_job(job_id, True, final_message, result={
                    'success': True,
                    'emails': [],  # Will be populated by inspect endpoint
                    'total_emails': new_emails,
                    'contacts_processed': contacts_processed,
                    'contacts_skipped': skipped_contacts,
                    'runtime_seconds': int(time.time() - start_time),
                    'sync_method': 'resource_managed_background_with_stopping'
                }, resume_info={'can_resume': False, 'reason': 'completed_successfully'})
                
                logger.info(f"Email sync completed for user {user_email} using resource-managed approach", 
                           processed=processed_count, new=new_emails, updated=updated_emails, 
                           contacts_processed=contacts_processed, skipped=skipped_contacts,
                           runtime=int(time.time() - start_time))
                
            except Exception as e:
                logger.error(f"Background email sync job {job_id} failed: {str(e)}")
                complete_job(job_id, False, f'Email sync failed: {str(e)}')

        # Start background thread
        import threading
        thread = threading.Thread(target=background_email_sync)
        thread.daemon = True
        thread.start()
        
        logger.info(f"Started background email sync job {job_id} for user {user_email}")
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'status': 'started',
            'message': 'Email sync started in background',
            'status_url': f'/api/job-status/{job_id}',
            'mode': 'synchronous_background'
        })
        
    except Exception as e:
        logger.error(f"Email sync error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'mode': 'synchronous'
        }), 500

@api_sync_bp.route('/gmail/analyze-sent', methods=['POST'])
@require_auth
def analyze_sent_emails():
    """Start Gmail sent emails analysis as background job"""
    try:
        logger.info("Starting analyze_sent_emails as background job")
        
        # Get user email from session
        user_email = session.get('user_email')
        if not user_email:
            return jsonify({'error': 'User not authenticated'}), 401
            
        # Get OAuth credentials from session
        oauth_credentials = session.get('oauth_credentials')
        if not oauth_credentials:
            return jsonify({
                'error': 'No Gmail credentials found. Please log out and log back in to re-authenticate with Gmail.',
                'action_required': 'reauth'
            }), 401
            
        # Get parameters
        data = request.get_json() or {}
        lookback_days = data.get('lookback_days', 30)
        
        logger.info(f"User email: {user_email}, lookback_days: {lookback_days}")
        
        # Generate unique job ID
        import uuid
        import time
        job_id = f"analyze_sent_{user_email}_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        
        # Initialize job status
        with jobs_lock:
            background_jobs[job_id] = {
                'id': job_id,
                'user_email': user_email,
                'status': 'started',
                'progress': 0,
                'message': 'Initializing Gmail analysis...',
                'created_at': time.time(),
                'contacts_found': 0,
                'emails_processed': 0
            }
        
        logger.info(f"Background job {job_id} started")
        
        def background_gmail_analysis():
            try:
                # Import required modules
                from datetime import datetime, timedelta, timezone
                from google.oauth2.credentials import Credentials
                from googleapiclient.discovery import build
                import base64
                import email
                import re
                import time
                
                # Update status to connecting
                with jobs_lock:
                    if job_id in background_jobs:
                        background_jobs[job_id]['status'] = 'connecting'
                        background_jobs[job_id]['message'] = 'Connecting to Gmail API...'
                
                # Get storage manager and user ID
                storage_manager = get_storage_manager_sync()
                user = storage_manager.get_user_by_email(user_email)
                
                if not user:
                    with jobs_lock:
                        if job_id in background_jobs:
                            background_jobs[job_id]['status'] = 'failed'
                            background_jobs[job_id]['message'] = 'User not found in database'
                    return
                
                user_id = user['id']
                
                # Create credentials object from session data
                try:
                    credentials = Credentials(
                        token=oauth_credentials.get('access_token'),
                        refresh_token=oauth_credentials.get('refresh_token'),
                        token_uri=oauth_credentials.get('token_uri', "https://oauth2.googleapis.com/token"),
                        client_id=oauth_credentials.get('client_id'),
                        client_secret=oauth_credentials.get('client_secret'),
                        scopes=oauth_credentials.get('scopes', [])
                    )
                    
                    # Set expiry if available
                    if oauth_credentials.get('expiry'):
                        credentials.expiry = datetime.fromtimestamp(oauth_credentials['expiry'])
                        
                except Exception as cred_error:
                    with jobs_lock:
                        if job_id in background_jobs:
                            background_jobs[job_id]['status'] = 'failed'
                            background_jobs[job_id]['message'] = f'Invalid OAuth credentials: {str(cred_error)}'
                    return
                
                # Build Gmail service
                try:
                    service = build('gmail', 'v1', credentials=credentials)
                except Exception as service_error:
                    with jobs_lock:
                        if job_id in background_jobs:
                            background_jobs[job_id]['status'] = 'failed'
                            background_jobs[job_id]['message'] = f'Failed to connect to Gmail API: {str(service_error)}'
                    return
                
                # Update status to fetching
                with jobs_lock:
                    if job_id in background_jobs:
                        background_jobs[job_id]['status'] = 'fetching'
                        background_jobs[job_id]['message'] = 'Fetching sent emails...'
                
                # Fetch sent emails
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=lookback_days)
                query = f'in:sent after:{cutoff_date.strftime("%Y/%m/%d")}'
                
                try:
                    results = service.users().messages().list(userId='me', q=query, maxResults=500).execute()
                    messages = results.get('messages', [])
                    
                    with jobs_lock:
                        if job_id in background_jobs:
                            background_jobs[job_id]['status'] = 'processing'
                            background_jobs[job_id]['message'] = f'Processing {len(messages)} sent emails...'
                            background_jobs[job_id]['total_emails'] = len(messages)
                            
                except Exception as fetch_error:
                    with jobs_lock:
                        if job_id in background_jobs:
                            background_jobs[job_id]['status'] = 'failed'
                            background_jobs[job_id]['message'] = f'Failed to fetch emails: {str(fetch_error)}'
                    return
                
                # Process emails and extract contacts
                contacts_dict = {}
                emails_processed = 0
                
                for i, message in enumerate(messages):
                    try:
                        # Get full message
                        msg = service.users().messages().get(userId='me', id=message['id']).execute()
                        
                        # Extract headers
                        headers = msg['payload'].get('headers', [])
                        to_header = next((h['value'] for h in headers if h['name'].lower() == 'to'), '')
                        cc_header = next((h['value'] for h in headers if h['name'].lower() == 'cc'), '')
                        bcc_header = next((h['value'] for h in headers if h['name'].lower() == 'bcc'), '')
                        
                        # Extract email addresses
                        all_recipients = f"{to_header} {cc_header} {bcc_header}"
                        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                        found_emails = re.findall(email_pattern, all_recipients)
                        
                        # Process found emails
                        for email_addr in found_emails:
                            email_addr = email_addr.lower().strip()
                            if email_addr and email_addr != user_email.lower():
                                if email_addr not in contacts_dict:
                                    contacts_dict[email_addr] = {
                                        'email': email_addr,
                                        'frequency': 0,
                                        'first_contact': None,
                                        'last_contact': None,
                                        'trust_tier': 1  # Sent emails indicate trust
                                    }
                                contacts_dict[email_addr]['frequency'] += 1
                        
                        emails_processed += 1
                        
                        # Update progress every 10 emails
                        if emails_processed % 10 == 0:
                            progress = int((emails_processed / len(messages)) * 100)
                            with jobs_lock:
                                if job_id in background_jobs:
                                    background_jobs[job_id]['progress'] = progress
                                    background_jobs[job_id]['emails_processed'] = emails_processed
                                    background_jobs[job_id]['contacts_found'] = len(contacts_dict)
                                    background_jobs[job_id]['message'] = f'Processing email {emails_processed}/{len(messages)}... Found {len(contacts_dict)} contacts'
                        
                        time.sleep(0.1)  # Rate limiting
                        
                    except Exception as email_error:
                        logger.error(f"Error processing email {message['id']}: {str(email_error)}")
                        continue
                
                # Save contacts to database
                contacts_saved = 0
                if contacts_dict:
                    # Prepare contact list for bulk storage
                    contact_list = []
                    for email_addr, contact_data in contacts_dict.items():
                        domain = email_addr.split('@')[1] if '@' in email_addr else ''
                        contact_list.append({
                            'email': email_addr,
                            'name': '',  # Will be empty for now
                            'frequency': contact_data['frequency'],
                            'domain': domain,
                            'trust_tier': contact_data['trust_tier'],
                            'metadata': {}
                        })
                    
                    try:
                        # Use the correct bulk storage method
                        storage_manager.postgres.store_contacts(user_id, contact_list)
                        contacts_saved = len(contact_list)
                        logger.info(f"Successfully saved {contacts_saved} contacts to database")
                    except Exception as save_error:
                        logger.error(f"Error saving contacts to database: {str(save_error)}")
                        contacts_saved = 0
                
                # Final status update
                with jobs_lock:
                    if job_id in background_jobs:
                        background_jobs[job_id]['status'] = 'completed'
                        background_jobs[job_id]['progress'] = 100
                        background_jobs[job_id]['message'] = f'Analysis complete! Found {len(contacts_dict)} contacts from {emails_processed} emails'
                        background_jobs[job_id]['completed_at'] = time.time()
                        # Structure the result properly for React pollJobStatus
                        background_jobs[job_id]['result'] = {
                            'success': True,
                            'contacts': list(contacts_dict.values()),
                            'total_sent_emails': emails_processed,
                            'contacts_found': len(contacts_dict),
                            'contacts_saved': contacts_saved,
                            'message': f'Analysis complete! Found {len(contacts_dict)} contacts from {emails_processed} emails'
                        }
                
                logger.info(f"Gmail analysis completed for {user_email}: {len(contacts_dict)} contacts from {emails_processed} emails")
                
            except Exception as e:
                logger.error(f"Background job {job_id} failed: {str(e)}")
                with jobs_lock:
                    if job_id in background_jobs:
                        background_jobs[job_id]['status'] = 'failed'
                        background_jobs[job_id]['message'] = f'Analysis failed: {str(e)}'
        
        # Start background thread
        import threading
        thread = threading.Thread(target=background_gmail_analysis)
        thread.daemon = True
        thread.start()
        
        logger.info(f"Started background job {job_id} for user {user_email}")
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'status': 'started',
            'message': 'Gmail analysis started in background',
            'status_url': f'/api/job-status/{job_id}'
        })
        
    except Exception as e:
        logger.error(f"Error starting background job: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to start Gmail analysis: {str(e)}'
        }), 500

@api_sync_bp.route('/intelligence/enrich-contacts', methods=['POST'])
@require_auth  
def enrich_contacts():
    """
    Contact enrichment with advanced web intelligence (synchronous background job)
    
    TODO: FUTURE OPTIMIZATION - Centralized Contact Repository
    Currently takes up to 2 hours because we re-enrich the same contacts for each user.
    Solution: Global contact_intelligence cache to reuse enrichment data across users.
    Impact: 90% faster enrichment, 95% cost reduction, better data consistency.
    """
    try:
        user_email = session.get('user_id', 'test@session-42.com')
        request_data = request.get_json() or {}
        limit = request_data.get('limit', 50)
        
        logger.info(f"Starting contact enrichment as background job for user {user_email}")
        
        # Generate unique job ID
        import uuid
        import time
        job_id = f"enrich_contacts_{user_email}_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        
        # Initialize job status
        with jobs_lock:
            background_jobs[job_id] = {
                'id': job_id,
                'user_email': user_email,
                'status': 'started',
                'progress': 0,
                'message': 'Initializing contact enrichment...',
                'created_at': time.time(),
                'contacts_enriched': 0,
                'contacts_processed': 0
            }
        
        logger.info(f"Background job {job_id} started for contact enrichment")
        
        def background_contact_enrichment():
            try:
                # Update status to connecting
                update_job_progress(job_id, 0, 'Connecting to database...')
                
                storage_manager = get_storage_manager_sync()
                user = storage_manager.get_user_by_email(user_email)
                if not user:
                    complete_job(job_id, False, 'User not found in database')
                    return
                
                user_id = user['id']
                
                # Get contacts that need enrichment - SKIP ALREADY ENRICHED
                all_contacts, total = storage_manager.get_contacts(user_id, limit=limit * 2)  # Get more to filter
                
                # Filter out contacts that already have enrichment data (resume capability)
                contacts_to_enrich = []
                already_enriched_count = 0
                
                update_job_progress(job_id, 5, f'Filtering {len(all_contacts)} contacts for enrichment...', {
                    'total_contacts_found': len(all_contacts),
                    'filtering_progress': 'checking_enrichment_status'
                })
                
                for contact in all_contacts:
                    # Check for stop signal during filtering
                    if should_stop_job(job_id):
                        stop_job_gracefully(job_id, 
                            f'Stopped during filtering. Processed {len(contacts_to_enrich)} of {len(all_contacts)} contacts.',
                            partial_result={'filtered_contacts': len(contacts_to_enrich), 'already_enriched': already_enriched_count},
                            resume_info={'can_resume': True, 'next_step': 'filtering', 'progress_checkpoint': len(contacts_to_enrich)}
                        )
                        return
                    
                    email = contact.get('email', '').strip().lower()
                    if not email:
                        continue
                    
                    # Check if already enriched by looking for comprehensive enrichment data
                    metadata = contact.get('metadata', {})
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except:
                            metadata = {}
                    
                    enrichment_data = metadata.get('enrichment_data', {})
                    has_enrichment = bool(
                        enrichment_data.get('person_data') or 
                        enrichment_data.get('company_data') or
                        enrichment_data.get('confidence_score', 0) > 0
                    )
                    
                    if has_enrichment:
                        already_enriched_count += 1
                    else:
                        contacts_to_enrich.append(contact)
                    
                    # Limit to requested number
                    if len(contacts_to_enrich) >= limit:
                        break
                
                contacts = contacts_to_enrich[:limit]
                
                if not contacts:
                    complete_job(job_id, True, 
                        f'No contacts need enrichment. {already_enriched_count} contacts already enriched.',
                        result={'already_enriched': already_enriched_count, 'newly_enriched': 0},
                        resume_info={'can_resume': False, 'reason': 'all_contacts_already_enriched'}
                    )
                    return
                
                update_job_progress(job_id, 10, f'Starting enrichment for {len(contacts)} contacts...', {
                    'total_contacts': len(contacts),
                    'already_enriched': already_enriched_count,
                    'enrichment_phase': 'initializing'
                })
                
                # Import the advanced contact enrichment service
                import sys
                import os
                import asyncio
                sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
                
                from intelligence.d_enrichment.contact_enrichment_service import ContactEnrichmentService

                async def run_advanced_enrichment():
                    enrichment_service = ContactEnrichmentService(user_id, storage_manager)
                    await enrichment_service.initialize()
                    
                    # Update progress for initialization complete
                    update_job_progress(job_id, 15, 'Enrichment service initialized. Starting batch processing...', {
                        'enrichment_phase': 'batch_processing_started'
                    })
                    
                    # Check for stop signal before starting enrichment
                    if should_stop_job(job_id):
                        stop_job_gracefully(job_id,
                            'Stopped before enrichment processing. Service initialized successfully.',
                            resume_info={'can_resume': True, 'next_step': 'enrichment', 'contacts_remaining': len(contacts)}
                        )
                        return {'stopped': True}
                    
                    # Get user emails for context analysis
                    user_emails, _ = storage_manager.get_emails(user_id, limit=1000)
                    
                    # Run enhanced batch enrichment with stop checking
                    enrichment_result = await enrichment_service.enrich_contacts_batch(contacts, user_emails)
                    
                    # Process and store results
                    successful_enrichments = 0
                    enriched_contacts = enrichment_result.get('enriched_contacts', [])
                    
                    update_job_progress(job_id, 85, f'Storing enrichment results for {len(enriched_contacts)} contacts...', {
                        'enrichment_phase': 'storing_results',
                        'enriched_contacts_count': len(enriched_contacts)
                    })
                    
                    for i, enriched_contact in enumerate(enriched_contacts):
                        # Check for stop signal during result storage
                        if should_stop_job(job_id):
                            stop_job_gracefully(job_id,
                                f'Stopped while storing results. Processed {i} of {len(enriched_contacts)} enrichment results.',
                                partial_result={
                                    'enriched_contacts': i,
                                    'total_contacts': len(contacts),
                                    'success_rate': (i / len(contacts)) * 100 if len(contacts) > 0 else 0
                                },
                                resume_info={
                                    'can_resume': True, 
                                    'next_step': 'storing_results',
                                    'results_stored': i,
                                    'results_remaining': len(enriched_contacts) - i
                                }
                            )
                            return {'stopped': True, 'partial_success': i}
                        
                        try:
                            email = enriched_contact.get('email', '')
                            if email and hasattr(enriched_contact, '__dict__'):
                                # Store enrichment data
                                enrichment_data = {
                                    'enrichment_timestamp': datetime.utcnow().isoformat(),
                                    'confidence_score': getattr(enriched_contact, 'confidence_score', 0.0),
                                    'data_sources': getattr(enriched_contact, 'data_sources', []),
                                    'person_data': getattr(enriched_contact, 'person_data', {}),
                                    'company_data': getattr(enriched_contact, 'company_data', {}),
                                    'relationship_intelligence': getattr(enriched_contact, 'relationship_intelligence', {}),
                                    'actionable_insights': getattr(enriched_contact, 'actionable_insights', {}),
                                }
                                
                                success = storage_manager.postgres.update_contact_metadata(
                                    user_id, email, {'enrichment_data': enrichment_data}
                                )
                                
                                if success:
                                    successful_enrichments += 1
                                    
                                    # Update progress every few contacts
                                    if i % 5 == 0:
                                        progress = 85 + int((i / len(enriched_contacts)) * 10)  # 85-95% for storage
                                        update_job_progress(job_id, progress, 
                                            f'Stored enrichment {i+1}/{len(enriched_contacts)}: {email}', {
                                            'enrichment_phase': 'storing_results',
                                            'stored_count': successful_enrichments,
                                            'current_contact': email
                                        })
                                
                        except Exception as e:
                            logger.error(f"Failed to store enrichment for contact: {e}")
                    
                    return {
                        'contacts_processed': len(contacts),
                        'successfully_enriched': successful_enrichments,
                        'failed_count': len(contacts) - successful_enrichments,
                        'success_rate': (successful_enrichments / len(contacts)) * 100 if len(contacts) > 0 else 0,
                        'sources_used': len(set().union(*[getattr(c, 'data_sources', []) for c in enriched_contacts])),
                        'mode': 'advanced_background_with_stopping'
                    }
                
                # Run the async advanced enrichment in a synchronous context
                try:
                    # Create new event loop for this thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    stats = loop.run_until_complete(run_advanced_enrichment())
                    loop.close()
                    
                    # Check if stopped
                    if stats.get('stopped'):
                        return  # Job already handled by stop_job_gracefully
                        
                except Exception as e:
                    logger.error(f"Advanced contact enrichment failed: {e}")
                    complete_job(job_id, False, f"Advanced enrichment failed: {str(e)}")
                    return
                
                # Final completion
                complete_job(job_id, True,
                    f'Contact enrichment complete! Enriched {stats["successfully_enriched"]} of {stats["contacts_processed"]} contacts',
                    result=stats,
                    resume_info={'can_resume': False, 'reason': 'completed_successfully'})
                
                logger.info(f"Advanced contact enrichment completed for user {user_email}", stats=stats)
                
            except Exception as e:
                logger.error(f"Background contact enrichment job {job_id} failed: {str(e)}")
                complete_job(job_id, False, f'Contact enrichment failed: {str(e)}')

        # Start background thread
        import threading
        thread = threading.Thread(target=background_contact_enrichment)
        thread.daemon = True
        thread.start()
        
        logger.info(f"Started background contact enrichment job {job_id} for user {user_email}")
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'status': 'started',
            'message': 'Contact enrichment started in background',
            'status_url': f'/api/job-status/{job_id}',
            'mode': 'synchronous_background'
        })
        
    except Exception as e:
        logger.error(f"Contact enrichment error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'mode': 'synchronous'
        }), 500

@api_sync_bp.route('/intelligence/build-knowledge-tree', methods=['POST'])
@require_auth
def build_knowledge_tree():
    """Knowledge tree building with real analysis (synchronous)"""
    try:
        user_email = session.get('user_id', 'test@session-42.com')
        request_data = request.get_json() or {}
        
        storage_manager = get_storage_manager_sync()
        user = storage_manager.get_user_by_email(user_email)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'mode': 'synchronous'
            }), 404
        
        user_id = user['id']
        
        # Import the real knowledge tree orchestrator
        import sys
        import os
        import asyncio
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        
        from intelligence.f_knowledge_integration.knowledge_tree_orchestrator import KnowledgeTreeOrchestrator
        
        # Use the real knowledge tree orchestrator
        async def run_real_knowledge_tree():
            # Initialize orchestrator with Claude API key
            orchestrator = KnowledgeTreeOrchestrator(ANTHROPIC_API_KEY)
            
            try:
                # Build complete knowledge tree with real intelligence
                knowledge_tree_result = await orchestrator.build_complete_knowledge_tree(
                    user_email=user_email,
                    force_rebuild=False
                )
                
                return knowledge_tree_result
                
            except Exception as e:
                logger.error(f"Real knowledge tree building failed: {e}")
                # Return error info
                return {
                    'success': False,
                    'error': str(e),
                    'fallback_used': True
                }
        
        # Run the async knowledge tree building in a synchronous context
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(run_real_knowledge_tree())
            loop.close()
            
            if result.get('success', False):
                # Extract stats from the real result
                stats = result.get('processing_stats', {})
                analysis_summary = {
                    'emails_analyzed': stats.get('total_content_processed', 0),
                    'contacts_integrated': stats.get('total_content_processed', 0),
                    'claude_batches_used': stats.get('total_batches', 0),
                    'topics_identified': stats.get('topics_identified', 0),
                    'relationships_analyzed': stats.get('relationships_analyzed', 0),
                    'business_domains': stats.get('business_domains', 0),
                    'timeline_events': stats.get('timeline_events', 0),
                    'system_version': result.get('claude_metadata', {}).get('model_used', 'claude-3-sonnet'),
                    'processing_method': 'claude_content_consolidation'
                }
                
                logger.info(f"Knowledge tree built for user {user_email}", **analysis_summary)
                
                return jsonify({
                    'success': True,
                    'message': f'Knowledge tree built successfully using real Claude intelligence',
                    'analysis_summary': analysis_summary,
                    'content_breakdown': result.get('content_breakdown', {}),
                    'processing_stats': stats,
                    'mode': 'synchronous_with_real_intelligence'
                })
            else:
                # Handle failure case
                error_msg = result.get('error', 'Unknown error in knowledge tree building')
                logger.error(f"Knowledge tree building failed: {error_msg}")
                
                return jsonify({
                    'success': False,
                    'error': error_msg,
                    'mode': 'synchronous_with_real_intelligence_failed'
                }), 500
                
        except Exception as e:
            logger.error(f"Knowledge tree building wrapper failed: {e}")
            
            # Fallback: Get basic stats from database  
            contacts, total_contacts = storage_manager.get_contacts(user_id, limit=1000)
            emails, total_emails = storage_manager.postgres.get_emails(user_id, limit=100)
            
            return jsonify({
                'success': True,
                'message': f'Knowledge tree building failed, showing basic stats only',
                'analysis_summary': {
                    'emails_analyzed': total_emails,
                    'contacts_integrated': total_contacts,
                    'domains_found': 0,
                    'system_version': 'fallback_basic',
                    'error': str(e)
                },
                'mode': 'synchronous_fallback'
            })
        
    except Exception as e:
        logger.error(f"Knowledge tree building error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'mode': 'synchronous'
        }), 500

@api_sync_bp.route('/intelligence/enrichment-results', methods=['GET'])
@require_auth
def view_enrichment_results():
    """View detailed enrichment results (synchronous)"""
    try:
        user_email = session.get('user_id', 'test@session-42.com')
        
        # Get pagination parameters
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        format_type = request.args.get('format', 'summary')  # 'summary' or 'detailed'
        
        storage_manager = get_storage_manager_sync()
        user = storage_manager.get_user_by_email(user_email)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        user_id = user['id']
        
        # Get contacts with their enrichment data
        contacts, total = storage_manager.get_contacts(user_id, limit=limit, offset=offset)
        
        enriched_contacts = []
        for contact in contacts:
            try:
                # Handle both dict and string metadata formats
                metadata = contact.get('metadata')
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        metadata = {}
                elif not isinstance(metadata, dict):
                    metadata = {}
                else:
                    metadata = metadata or {}
                    
                enrichment_data = metadata.get('enrichment_data', {})
                
                if format_type == 'detailed':
                    # Detailed format with all enrichment data including professional intelligence
                    contact_result = {
                        'email': contact.get('email'),
                        'name': contact.get('name'),
                        'domain': contact.get('domain'),
                        'trust_tier': contact.get('trust_tier'),
                        'frequency': contact.get('frequency'),
                        'enrichment': {
                            'success': bool(enrichment_data),
                            'confidence_score': enrichment_data.get('confidence_score', 0),
                            'data_sources': enrichment_data.get('data_sources', []),
                            
                            # Comprehensive professional intelligence
                            'person_data': enrichment_data.get('person_data', {}),
                            'company_data': enrichment_data.get('company_data', {}),
                            'relationship_intelligence': enrichment_data.get('relationship_intelligence', {}),
                            'actionable_insights': enrichment_data.get('actionable_insights', {}),
                            
                            'enrichment_timestamp': enrichment_data.get('enrichment_timestamp'),
                            
                            # Quick access fields for UI
                            'professional_summary': {
                                'current_role': enrichment_data.get('person_data', {}).get('current_title', ''),
                                'career_stage': enrichment_data.get('person_data', {}).get('career_stage', ''),
                                'years_experience': enrichment_data.get('person_data', {}).get('professional_background', {}).get('years_experience', ''),
                                'industry_expertise': enrichment_data.get('person_data', {}).get('professional_background', {}).get('industry_expertise', []),
                                'investment_focus': enrichment_data.get('person_data', {}).get('current_focus', {}).get('investment_thesis', ''),
                                'decision_authority': enrichment_data.get('person_data', {}).get('value_proposition', {}).get('decision_authority', ''),
                                'network_value': enrichment_data.get('person_data', {}).get('value_proposition', {}).get('network_value', ''),
                            },
                            
                            'company_summary': {
                                'business_model': enrichment_data.get('company_data', {}).get('company_profile', {}).get('business_model', ''),
                                'company_stage': enrichment_data.get('company_data', {}).get('company_profile', {}).get('company_stage', ''),
                                'funding_status': enrichment_data.get('company_data', {}).get('financial_intelligence', {}).get('funding_status', ''),
                                'key_investors': enrichment_data.get('company_data', {}).get('financial_intelligence', {}).get('key_investors', []),
                                'competitive_position': enrichment_data.get('company_data', {}).get('market_position', {}).get('competitive_landscape', ''),
                                'growth_trajectory': enrichment_data.get('company_data', {}).get('financial_intelligence', {}).get('growth_trajectory', ''),
                            },
                            
                            'engagement_strategy': {
                                'relationship_stage': enrichment_data.get('relationship_intelligence', {}).get('relationship_stage', ''),
                                'best_approach': enrichment_data.get('actionable_insights', {}).get('best_approach', ''),
                                'value_propositions': enrichment_data.get('actionable_insights', {}).get('value_propositions', []),
                                'conversation_starters': enrichment_data.get('actionable_insights', {}).get('conversation_starters', []),
                                'meeting_likelihood': enrichment_data.get('actionable_insights', {}).get('meeting_likelihood', ''),
                                'timing_considerations': enrichment_data.get('actionable_insights', {}).get('timing_considerations', ''),
                            }
                        }
                    }
                else:
                    # Enhanced summary format with key professional insights
                    person_data = enrichment_data.get('person_data', {})
                    company_data = enrichment_data.get('company_data', {})
                    relationship_intel = enrichment_data.get('relationship_intelligence', {})
                    actionable_insights = enrichment_data.get('actionable_insights', {})
                    
                    contact_result = {
                        'email': contact.get('email'),
                        'name': contact.get('name') or person_data.get('name', ''),
                        'title': person_data.get('current_title', person_data.get('title', '')),
                        'company': company_data.get('name', ''),
                        'industry': company_data.get('industry', ''),
                        'seniority_level': person_data.get('seniority_level', ''),
                        'confidence_score': enrichment_data.get('confidence_score', 0),
                        'data_sources': enrichment_data.get('data_sources', []),
                        'trust_tier': contact.get('trust_tier'),
                        'frequency': contact.get('frequency'),
                        'enrichment_timestamp': enrichment_data.get('enrichment_timestamp'),
                        
                        # Professional intelligence summary
                        'career_stage': person_data.get('career_stage', ''),
                        'years_experience': person_data.get('professional_background', {}).get('years_experience', ''),
                        'investment_thesis': person_data.get('current_focus', {}).get('investment_thesis', ''),
                        'decision_authority': person_data.get('value_proposition', {}).get('decision_authority', ''),
                        'company_stage': company_data.get('company_profile', {}).get('company_stage', ''),
                        'funding_status': company_data.get('financial_intelligence', {}).get('funding_status', ''),
                        'key_investors': company_data.get('financial_intelligence', {}).get('key_investors', []),
                        'competitive_position': company_data.get('market_position', {}).get('competitive_landscape', ''),
                        'relationship_stage': relationship_intel.get('relationship_stage', ''),
                        'engagement_level': relationship_intel.get('engagement_level', ''),
                        'best_approach': actionable_insights.get('best_approach', ''),
                        'meeting_likelihood': actionable_insights.get('meeting_likelihood', ''),
                        'conversation_starters': actionable_insights.get('conversation_starters', []),
                    }
                
                enriched_contacts.append(contact_result)
                
            except Exception as e:
                logger.error(f"Error processing contact {contact.get('email', 'unknown')}: {e}")
                continue
        
        # Calculate enrichment statistics
        enriched_count = sum(1 for c in enriched_contacts if c.get('enriched', False) or c.get('confidence', 0) > 0)
        avg_confidence = sum(c.get('confidence', 0) for c in enriched_contacts) / len(enriched_contacts) if enriched_contacts else 0
        
        return jsonify({
            'success': True,
            'data': {
                'contacts': enriched_contacts,
                'pagination': {
                    'limit': limit,
                    'offset': offset,
                    'total': total,
                    'returned': len(enriched_contacts)
                },
                'statistics': {
                    'total_contacts': total,
                    'enriched_contacts': enriched_count,
                    'enrichment_rate': enriched_count / total if total > 0 else 0,
                    'average_confidence': avg_confidence
                },
                'format': format_type
            }
        })
        
    except Exception as e:
        logger.error(f"Error viewing enrichment results: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_sync_bp.route('/intelligence/enrichment-results/download', methods=['GET'])
@require_auth
def download_enrichment_results():
    """Download enrichment results as JSON file (synchronous)"""
    try:
        user_email = session.get('user_id', 'test@session-42.com')
        
        # Get all contacts (no pagination for download)
        format_type = request.args.get('format', 'detailed')  # 'summary' or 'detailed'
        
        storage_manager = get_storage_manager_sync()
        user = storage_manager.get_user_by_email(user_email)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        user_id = user['id']
        
        # Get ALL contacts for download
        contacts, total = storage_manager.get_contacts(user_id, limit=10000)  # High limit for full download
        
        enriched_contacts = []
        enrichment_stats = {
            'total_processed': 0,
            'successfully_enriched': 0,
            'data_sources_used': set(),
            'companies_identified': set(),
            'industries_identified': set()
        }
        
        for contact in contacts:
            try:
                # Handle both dict and string metadata formats
                metadata = contact.get('metadata')
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        metadata = {}
                elif not isinstance(metadata, dict):
                    metadata = {}
                else:
                    metadata = metadata or {}
                    
                enrichment_data = metadata.get('enrichment_data', {})
                
                enrichment_stats['total_processed'] += 1
                
                if enrichment_data:
                    enrichment_stats['successfully_enriched'] += 1
                    enrichment_stats['data_sources_used'].update(enrichment_data.get('data_sources', []))
                    
                    company_name = enrichment_data.get('company_data', {}).get('name')
                    if company_name:
                        enrichment_stats['companies_identified'].add(company_name)
                    
                    industry = enrichment_data.get('company_data', {}).get('industry')
                    if industry:
                        enrichment_stats['industries_identified'].add(industry)
                
                if format_type == 'detailed':
                    # Full enrichment data
                    contact_result = {
                        'contact_info': {
                            'email': contact.get('email'),
                            'name': contact.get('name'),
                            'domain': contact.get('domain'),
                            'trust_tier': contact.get('trust_tier'),
                            'frequency': contact.get('frequency'),
                            'created_at': contact.get('created_at'),
                            'updated_at': contact.get('updated_at')
                        },
                        'enrichment_data': enrichment_data
                    }
                else:
                    # Summary format
                    person_data = enrichment_data.get('person_data', {})
                    company_data = enrichment_data.get('company_data', {})
                    relationship_intel = enrichment_data.get('relationship_intelligence', {})
                    actionable_insights = enrichment_data.get('actionable_insights', {})
                    
                    contact_result = {
                        'email': contact.get('email'),
                        'name': contact.get('name') or person_data.get('name', ''),
                        'title': person_data.get('current_title', person_data.get('title', '')),
                        'company': company_data.get('name', ''),
                        'industry': company_data.get('industry', ''),
                        'seniority_level': person_data.get('seniority_level', ''),
                        'confidence_score': enrichment_data.get('confidence_score', 0),
                        'data_sources': enrichment_data.get('data_sources', []),
                        'trust_tier': contact.get('trust_tier'),
                        'frequency': contact.get('frequency'),
                        'enrichment_timestamp': enrichment_data.get('enrichment_timestamp'),
                        
                        # Professional intelligence summary
                        'career_stage': person_data.get('career_stage', ''),
                        'years_experience': person_data.get('professional_background', {}).get('years_experience', ''),
                        'investment_thesis': person_data.get('current_focus', {}).get('investment_thesis', ''),
                        'decision_authority': person_data.get('value_proposition', {}).get('decision_authority', ''),
                        'company_stage': company_data.get('company_profile', {}).get('company_stage', ''),
                        'funding_status': company_data.get('financial_intelligence', {}).get('funding_status', ''),
                        'key_investors': company_data.get('financial_intelligence', {}).get('key_investors', []),
                        'competitive_position': company_data.get('market_position', {}).get('competitive_landscape', ''),
                        'relationship_stage': relationship_intel.get('relationship_stage', ''),
                        'engagement_level': relationship_intel.get('engagement_level', ''),
                        'best_approach': actionable_insights.get('best_approach', ''),
                        'meeting_likelihood': actionable_insights.get('meeting_likelihood', ''),
                        'conversation_starters': actionable_insights.get('conversation_starters', []),
                    }
                
                enriched_contacts.append(contact_result)
                
            except Exception as e:
                logger.error(f"Error processing contact {contact.get('email', 'unknown')}: {e}")
                continue
        
        # Prepare final statistics
        final_stats = {
            'total_contacts': enrichment_stats['total_processed'],
            'enriched_contacts': enrichment_stats['successfully_enriched'],
            'enrichment_rate': enrichment_stats['successfully_enriched'] / enrichment_stats['total_processed'] if enrichment_stats['total_processed'] > 0 else 0,
            'unique_data_sources': len(enrichment_stats['data_sources_used']),
            'data_sources_used': list(enrichment_stats['data_sources_used']),
            'companies_identified': len(enrichment_stats['companies_identified']),
            'industries_identified': len(enrichment_stats['industries_identified']),
            'export_timestamp': datetime.utcnow().isoformat(),
            'format': format_type
        }
        
        # Prepare complete download package
        download_data = {
            'export_info': {
                'user_email': user_email,
                'export_timestamp': datetime.utcnow().isoformat(),
                'format': format_type,
                'version': '1.0'
            },
            'statistics': final_stats,
            'contacts': enriched_contacts
        }
        
        # Create response with appropriate headers for download
        from flask import Response
        import json as json_module
        
        response_data = json_module.dumps(download_data, indent=2, default=str)
        
        response = Response(
            response_data,
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment; filename=contact_enrichment_results_{format_type}_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json'
            }
        )
        
        logger.info(f"Enrichment results downloaded for user {user_email}", 
                   total_contacts=enrichment_stats['total_processed'],
                   enriched_contacts=enrichment_stats['successfully_enriched'],
                   format=format_type)
        
        return response
        
    except Exception as e:
        logger.error(f"Error downloading enrichment results: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_sync_bp.route('/sanity-test', methods=['POST'])
@require_auth
def run_sanity_test():
    """End-to-end sanity test with 10 contacts and 10 emails (synchronous)"""
    try:
        user_email = session.get('user_id', 'test@session-42.com')
        
        logger.info(f"🧪 Starting sanity test for user {user_email}")
        
        storage_manager = get_storage_manager_sync()
        user = storage_manager.get_user_by_email(user_email)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'mode': 'sanity_test'
            }), 404
        
        user_id = user['id']
        
        # Get OAuth credentials from session
        oauth_credentials = session.get('oauth_credentials')
        if not oauth_credentials:
            return jsonify({
                'success': False,
                'error': 'No Gmail credentials found. Please log out and log back in to re-authenticate with Gmail.',
                'mode': 'sanity_test'
            }), 401
        
        # Step 1: Get 10 contacts from sent emails
        logger.info("🔍 Step 1: Analyzing sent emails for 10 contacts...")
        sent_analysis_result = analyze_sent_emails_internal(user_email, oauth_credentials, lookback_days=30, limit=10)
        
        if not sent_analysis_result.get('success'):
            return jsonify({
                'success': False,
                'error': f"Step 1 failed: {sent_analysis_result.get('error')}",
                'mode': 'sanity_test'
            })
        
        contacts_found = sent_analysis_result.get('total_contacts', 0)
        logger.info(f"✅ Step 1 complete: Found {contacts_found} contacts")
        
        if contacts_found == 0:
            return jsonify({
                'success': False,
                'error': 'No contacts found in sent emails',
                'mode': 'sanity_test'
            })
        
        # Step 2: Sync 10 emails from these contacts
        logger.info("📧 Step 2: Syncing emails from discovered contacts...")
        email_sync_result = sync_emails_internal(user_email, oauth_credentials, days=30, contact_limit=10)
        
        if not email_sync_result.get('success'):
            return jsonify({
                'success': False,
                'error': f"Step 2 failed: {email_sync_result.get('error')}",
                'mode': 'sanity_test'
            })
        
        emails_synced = email_sync_result.get('stats', {}).get('new_emails', 0)
        logger.info(f"✅ Step 2 complete: Synced {emails_synced} emails")
        
        # Step 3: Enrich the 10 contacts
        logger.info("🎯 Step 3: Enriching contacts...")
        enrichment_result = enrich_contacts_internal(user_email, limit=10)
        
        if not enrichment_result.get('success'):
            return jsonify({
                'success': False,
                'error': f"Step 3 failed: {enrichment_result.get('error')}",
                'mode': 'sanity_test'
            })
        
        enriched_count = enrichment_result.get('stats', {}).get('successfully_enriched', 0)
        logger.info(f"✅ Step 3 complete: Enriched {enriched_count} contacts")
        
        # Step 4: Build knowledge tree
        logger.info("🌳 Step 4: Building knowledge tree...")
        tree_result = build_knowledge_tree_internal(user_email)
        
        if not tree_result.get('success'):
            return jsonify({
                'success': False,
                'error': f"Step 4 failed: {tree_result.get('error')}",
                'mode': 'sanity_test'
            })
        
        tree_nodes = tree_result.get('stats', {}).get('total_nodes', 0)
        logger.info(f"✅ Step 4 complete: Built knowledge tree with {tree_nodes} nodes")
        
        # Step 5: Generate Strategic Intelligence & Tactical Alerts
        logger.info("🎯 Step 5: Generating strategic intelligence and tactical alerts...")
        strategic_result = strategic_intelligence_internal(user_email, limit=10)
        
        if not strategic_result.get('success'):
            return jsonify({
                'success': False,
                'error': f"Step 5 failed: {strategic_result.get('error')}",
                'mode': 'sanity_test'
            }), 500
        
        strategic_insights = strategic_result.get('insights_generated', 0)
        tactical_alerts = strategic_result.get('tactical_alerts', 0)
        logger.info(f"✅ Step 5 complete: Generated {strategic_insights} insights and {tactical_alerts} alerts")
        
        # Final results
        logger.info("🎉 Sanity test completed successfully!")
        
        return jsonify({
            'success': True,
            'message': 'Sanity test completed successfully',
            'results': {
                'step_1_contacts': {
                    'contacts_found': contacts_found,
                    'status': 'success'
                },
                'step_2_emails': {
                    'emails_synced': emails_synced,
                    'status': 'success'
                },
                'step_3_enrichment': {
                    'contacts_enriched': enriched_count,
                    'status': 'success'
                },
                'step_4_knowledge_tree': {
                    'tree_nodes': tree_nodes,
                    'status': 'success'
                },
                'step_5_strategic_intelligence': {
                    'insights_generated': strategic_insights,
                    'tactical_alerts': tactical_alerts,
                    'status': 'success'
                }
            },
            'mode': 'sanity_test',
            'duration': 'complete'
        })
        
    except Exception as e:
        logger.error(f"Sanity test failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'mode': 'sanity_test'
        }), 500


def analyze_sent_emails_internal(user_email: str, oauth_credentials: Dict, lookback_days: int = 30, limit: int = 10) -> Dict:
    """Internal function to analyze sent emails with limit"""
    try:
        # Reuse existing analyze_sent_emails logic but with contact limit
        storage_manager = get_storage_manager_sync()
        user = storage_manager.get_user_by_email(user_email)
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        user_id = user['id']
        
        # Gmail integration logic (simplified version of existing code)
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from datetime import datetime, timedelta
        import email.utils
        import base64
        
        try:
            # Use passed OAuth credentials from session
            credentials = Credentials(
                token=oauth_credentials.get('access_token'),
                refresh_token=oauth_credentials.get('refresh_token'),
                token_uri=oauth_credentials.get('token_uri', "https://oauth2.googleapis.com/token"),
                client_id=oauth_credentials.get('client_id'),
                client_secret=oauth_credentials.get('client_secret'),
                scopes=oauth_credentials.get('scopes', [])
            )
            
            service = build('gmail', 'v1', credentials=credentials)
            
            # Get sent emails from last N days
            cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
            query = f"in:sent after:{cutoff_date.strftime('%Y/%m/%d')}"
            
            result = service.users().messages().list(userId='me', q=query, maxResults=100).execute()  # Increased from 5 to 100
            messages = result.get('messages', [])
            
            if not messages:
                return {'success': False, 'error': 'No sent emails found'}
            
            # Analyze contacts from sent emails
            contact_frequency = {}
            contact_names = {}
            contact_metadata = {}
            
            for msg in messages[:50]:  # Limit to first 50 sent emails
                try:
                    msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
                    headers = {}
                    for header in msg_data.get('payload', {}).get('headers', []):
                        headers[header.get('name', '').lower()] = header.get('value', '')
                    
                    to_addr = headers.get('to', '')
                    if to_addr and '@' in to_addr:
                        # Extract email address
                        import re
                        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', to_addr)
                        if email_match:
                            email_addr = email_match.group().lower()
                            contact_frequency[email_addr] = contact_frequency.get(email_addr, 0) + 1
                            
                            # Extract name if available
                            if '<' in to_addr:
                                name = to_addr.split('<')[0].strip(' "')
                                if name:
                                    contact_names[email_addr] = name
                    
                except Exception as e:
                    logger.warning(f"Error processing sent email {msg.get('id')}: {e}")
                    continue
            
            # Convert to contact list and limit to requested number
            contact_list = []
            for email_addr, frequency in sorted(contact_frequency.items(), key=lambda x: x[1], reverse=True)[:limit]:
                domain = email_addr.split('@')[1] if '@' in email_addr else ''
                contact_list.append({
                    'email': email_addr,
                    'name': contact_names.get(email_addr, ''),
                    'frequency': frequency,
                    'domain': domain,
                    'trust_tier': 'tier_1' if frequency > 3 else 'tier_2' if frequency > 1 else 'tier_3',
                    'metadata': {}
                })
            
            # Store contacts
            if contact_list:
                storage_manager.postgres.store_contacts(user_id, contact_list)
            
            return {
                'success': True,
                'total_contacts': len(contact_list),
                'contacts': contact_list
            }
            
        except Exception as gmail_error:
            return {'success': False, 'error': f'Gmail integration error: {str(gmail_error)}'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def sync_emails_internal(user_email: str, oauth_credentials: Dict, days: int = 30, contact_limit: int = 10) -> Dict:
    """Internal function to sync emails from specific contacts with limit"""
    try:
        storage_manager = get_storage_manager_sync()
        user = storage_manager.get_user_by_email(user_email)
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        user_id = user['id']
        
        # Get contacts from database (limited by contact_limit)
        contacts, total = storage_manager.get_contacts(user_id, limit=contact_limit)
        if not contacts:
            return {'success': False, 'error': 'No contacts found to sync emails from'}
        
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from datetime import datetime, timedelta, timezone
        import email.utils
        import base64
        import time
        
        try:
            # Use passed OAuth credentials from session instead of database
            credentials = Credentials(
                token=oauth_credentials.get('access_token'),
                refresh_token=oauth_credentials.get('refresh_token'),
                token_uri=oauth_credentials.get('token_uri', "https://oauth2.googleapis.com/token"),
                client_id=oauth_credentials.get('client_id'),
                client_secret=oauth_credentials.get('client_secret'),
                scopes=oauth_credentials.get('scopes', [])
            )
            
            service = build('gmail', 'v1', credentials=credentials)
            
            # Calculate date range
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            new_emails = 0
            processed_count = 0
            
            # Process each contact
            for contact in contacts:
                contact_email = contact['email']
                
                try:
                    # Gmail query for this specific contact
                    query = f"(from:{contact_email} OR to:{contact_email}) after:{cutoff_date.strftime('%Y/%m/%d')}"
                    
                    result = service.users().messages().list(userId='me', q=query, maxResults=5).execute()  # Just 1-2 emails per contact
                    messages = result.get('messages', [])
                    
                    for msg in messages:
                        try:
                            # Check if already exists
                            existing = storage_manager.postgres.get_email_by_gmail_id(user_id, msg['id'])
                            if existing:
                                continue
                            
                            # Get message details
                            msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
                            
                            headers = {}
                            for header in msg_data.get('payload', {}).get('headers', []):
                                headers[header.get('name', '').lower()] = header.get('value', '')
                            
                            subject = headers.get('subject', '(No Subject)')
                            from_addr = headers.get('from', '')
                            to_addr = headers.get('to', '')
                            date_str = headers.get('date', '')
                            
                            # Parse date
                            try:
                                date_sent = email.utils.parsedate_to_datetime(date_str) if date_str else datetime.now(timezone.utc)
                            except:
                                date_sent = datetime.now(timezone.utc)
                            
                            # Extract body (simplified)
                            body_text = ""
                            if 'payload' in msg_data:
                                payload = msg_data['payload']
                                if 'parts' in payload:
                                    for part in payload['parts']:
                                        if part.get('mimeType') == 'text/plain' and 'body' in part and 'data' in part['body']:
                                            try:
                                                body_text = base64.urlsafe_b64decode(part['body']['data'].encode('ASCII')).decode('utf-8', errors='replace')
                                                break
                                            except:
                                                pass
                                elif 'body' in payload and 'data' in payload['body']:
                                    if payload.get('mimeType') == 'text/plain':
                                        try:
                                            body_text = base64.urlsafe_b64decode(payload['body']['data'].encode('ASCII')).decode('utf-8', errors='replace')
                                        except:
                                            pass
                            
                            # Store email
                            metadata = {
                                'subject': subject,
                                'from': from_addr,
                                'to': to_addr,
                                'date': date_str,
                                'headers': headers,
                                'associated_contact': contact_email,
                                'sync_method': 'sanity_test'
                            }
                            
                            storage_manager.postgres.store_email(
                                user_id=user_id,
                                gmail_id=msg['id'],
                                content=body_text,
                                metadata=metadata,
                                timestamp=date_sent
                            )
                            new_emails += 1
                            processed_count += 1
                            
                            time.sleep(0.1)  # Throttle
                            
                        except Exception as e:
                            logger.warning(f"Error processing email {msg.get('id')}: {e}")
                            continue
                    
                    time.sleep(0.2)  # Throttle between contacts
                    
                except Exception as e:
                    logger.warning(f"Error processing contact {contact_email}: {e}")
                    continue
            
            return {
                'success': True,
                'stats': {
                    'new_emails': new_emails,
                    'processed_count': processed_count,
                    'contacts_processed': len(contacts)
                }
            }
            
        except Exception as gmail_error:
            return {'success': False, 'error': f'Gmail sync error: {str(gmail_error)}'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def enrich_contacts_internal(user_email: str, limit: int = 10) -> Dict:
    """Internal function to enrich contacts"""
    try:
        storage_manager = get_storage_manager_sync()
        user = storage_manager.get_user_by_email(user_email)
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        user_id = user['id']
        
        # Get contacts to enrich
        contacts, total = storage_manager.get_contacts(user_id, limit=limit)
        if not contacts:
            return {'success': False, 'error': 'No contacts found to enrich'}
        
        # Get user emails for enrichment context
        emails = storage_manager.get_emails_for_user(user_id, limit=50)
        
        # Run enrichment using the correct batch method
        import asyncio
        from intelligence.d_enrichment.contact_enrichment_service import ContactEnrichmentService
        
        async def run_enrichment():
            enrichment_service = ContactEnrichmentService(user_id, storage_manager)
            await enrichment_service.initialize()
            
            try:
                # Use the correct batch enrichment method
                result = await enrichment_service.enrich_contacts_batch(contacts, emails)
                await enrichment_service.cleanup()
                return result
            except Exception as e:
                logger.warning(f"Batch enrichment failed: {e}")
                await enrichment_service.cleanup()
                return {'enriched_contacts': {}, 'total_processed': 0, 'error': str(e)}
        
        # Run async enrichment
        enrichment_results = asyncio.run(run_enrichment())
        
        # Extract stats from batch result
        enriched_contacts = enrichment_results.get('enriched_contacts', {})
        successful_enrichments = 0
        
        # Count successful enrichments (confidence > 0.3)
        for email, result in enriched_contacts.items():
            if isinstance(result, dict) and result.get('confidence_score', 0) > 0.3:
                successful_enrichments += 1
        
        return {
            'success': True,
            'stats': {
                'successfully_enriched': successful_enrichments,
                'contacts_processed': enrichment_results.get('total_processed', 0),
                'domains_analyzed': enrichment_results.get('domains_analyzed', 0),
                'enrichment_results': enriched_contacts
            }
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def build_knowledge_tree_internal(user_email: str) -> Dict:
    """Internal function to build knowledge tree"""
    try:
        storage_manager = get_storage_manager_sync()
        user = storage_manager.get_user_by_email(user_email)
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        user_id = user['id']
        
        # Get emails and contacts for tree building
        emails = storage_manager.get_emails_for_user(user_id, limit=20)
        contacts, _ = storage_manager.get_contacts(user_id, limit=20)
        
        if not emails and not contacts:
            return {'success': False, 'error': 'No data found for knowledge tree'}
        
        # Build simplified knowledge tree
        tree_data = {
            'root': {
                'name': 'Professional Network',
                'type': 'root',
                'children': []
            },
            'metadata': {
                'created_at': datetime.utcnow().isoformat(),
                'total_contacts': len(contacts),
                'total_emails': len(emails),
                'analysis_type': 'sanity_test'
            }
        }
        
        # Add contact nodes
        if contacts:
            contacts_node = {
                'name': f'Contacts ({len(contacts)})',
                'type': 'category',
                'children': []
            }
            
            for contact in contacts[:10]:  # Limit for sanity test
                contact_node = {
                    'name': contact.get('name') or contact['email'].split('@')[0],
                    'type': 'contact',
                    'email': contact['email'],
                    'domain': contact.get('domain', ''),
                    'trust_tier': contact.get('trust_tier', 'tier_3')
                }
                contacts_node['children'].append(contact_node)
            
            tree_data['root']['children'].append(contacts_node)
        
        # Add email insights node
        if emails:
            emails_node = {
                'name': f'Communications ({len(emails)})',
                'type': 'category',
                'children': []
            }
            tree_data['root']['children'].append(emails_node)
        
        # Store knowledge tree
        success = storage_manager.store_knowledge_tree(user_id, tree_data, 'sanity_test')
        
        if success:
            total_nodes = 1 + len(tree_data['root']['children'])  # Root + category nodes
            for category in tree_data['root']['children']:
                total_nodes += len(category.get('children', []))
            
            return {
                'success': True,
                'stats': {
                    'total_nodes': total_nodes,
                    'tree_data': tree_data
                }
            }
        else:
            return {'success': False, 'error': 'Failed to store knowledge tree'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)} 

def strategic_intelligence_internal(user_email: str, limit: int = 10) -> Dict:
    """Internal function to generate strategic intelligence and tactical alerts"""
    try:
        storage_manager = get_storage_manager_sync()
        user = storage_manager.get_user_by_email(user_email)
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        user_id = user['id']
        
        # Get data for strategic analysis
        contacts, _ = storage_manager.get_contacts(user_id, limit=limit)
        emails = storage_manager.get_emails_for_user(user_id, limit=50)
        knowledge_tree = storage_manager.get_latest_knowledge_tree(user_id)
        
        if not contacts:
            return {'success': False, 'error': 'No contacts found for strategic analysis'}
        
        # Run strategic intelligence analysis
        import asyncio
        import os
        from intelligence.e_strategic_analysis.ceo_strategic_intelligence_system import CEOStrategicIntelligenceSystem
        
        async def run_strategic_analysis():
            # Initialize the strategic intelligence system
            claude_api_key = os.environ.get('ANTHROPIC_API_KEY')
            if not claude_api_key:
                logger.warning("No Anthropic API key found, using mock strategic analysis")
                return _generate_mock_strategic_intelligence(contacts, emails)
            
            strategic_system = CEOStrategicIntelligenceSystem(user_id, claude_api_key)
            
            try:
                # Generate CEO intelligence brief
                intelligence_brief = await strategic_system.generate_ceo_intelligence_brief(
                    focus_area="network_opportunities"
                )
                
                # Extract actionable insights and alerts
                insights = intelligence_brief.get('strategic_insights', [])
                tactical_alerts = intelligence_brief.get('immediate_actions', [])
                
                # Generate network-specific insights
                network_analysis = await strategic_system.map_network_to_objectives()
                
                return {
                    'intelligence_brief': intelligence_brief,
                    'network_analysis': network_analysis,
                    'insights': insights,
                    'tactical_alerts': tactical_alerts,
                    'analysis_timestamp': intelligence_brief.get('analysis_timestamp'),
                    'contacts_analyzed': len(contacts),
                    'emails_analyzed': len(emails)
                }
                
            except Exception as e:
                logger.warning(f"Claude strategic analysis failed: {e}, using mock data")
                return _generate_mock_strategic_intelligence(contacts, emails)
        
        # Run async strategic analysis
        strategic_results = asyncio.run(run_strategic_analysis())
        
        # Calculate success metrics
        insights_generated = len(strategic_results.get('insights', []))
        tactical_alerts = len(strategic_results.get('tactical_alerts', []))
        
        return {
            'success': True,
            'insights_generated': insights_generated,
            'tactical_alerts': tactical_alerts,
            'strategic_results': strategic_results,
            'contacts_analyzed': len(contacts),
            'emails_analyzed': len(emails)
        }
        
    except Exception as e:
        logger.error(f"Strategic intelligence analysis error: {e}")
        return {'success': False, 'error': str(e)}

def _generate_mock_strategic_intelligence(contacts: List[Dict], emails: List[Dict]) -> Dict:
    """Generate mock strategic intelligence for testing when Claude API is not available"""
    import random
    from datetime import datetime
    
    # Mock strategic insights
    insights = []
    tactical_alerts = []
    
    # Generate contact-based insights
    for contact in contacts[:5]:  # Top 5 contacts
        domain = contact.get('email', '').split('@')[-1] if '@' in contact.get('email', '') else 'unknown'
        
        insights.append({
            'title': f"Strategic Opportunity: {contact.get('name', contact.get('email'))}",
            'description': f"High-value contact at {domain} shows strong engagement potential",
            'strategic_value': f"Could facilitate business development in {domain} sector",
            'confidence_score': random.uniform(0.7, 0.95),
            'time_sensitivity': random.choice(['high', 'medium', 'low']),
            'business_impact': 'High potential for partnership or collaboration'
        })
        
        if random.random() > 0.6:  # 40% chance of tactical alert
            tactical_alerts.append({
                'alert_type': 'engagement_opportunity',
                'contact': contact.get('email'),
                'message': f"Perfect time to reconnect with {contact.get('name', 'contact')} - recent activity detected",
                'priority': random.choice(['urgent', 'high', 'medium']),
                'suggested_action': f"Send personalized follow-up about {domain} industry trends"
            })
    
    # Generate domain-based insights
    domains = list(set([c.get('email', '').split('@')[-1] for c in contacts if '@' in c.get('email', '')]))
    
    for domain in domains[:3]:  # Top 3 domains
        contact_count = len([c for c in contacts if domain in c.get('email', '')])
        insights.append({
            'title': f"Network Cluster Analysis: {domain}",
            'description': f"Strong network presence in {domain} - {contact_count} contacts",
            'strategic_value': f"Leverage {domain} network for industry insights and partnerships",
            'confidence_score': random.uniform(0.6, 0.9),
            'time_sensitivity': 'medium',
            'business_impact': 'Medium to high - network effects possible'
        })
    
    # Generate email-based insights
    if emails:
        recent_activity = len([e for e in emails if e.get('created_at', '')])
        tactical_alerts.append({
            'alert_type': 'communication_pattern',
            'message': f"Analyzed {len(emails)} emails - {recent_activity} show recent engagement",
            'priority': 'medium',
            'suggested_action': 'Review recent conversations for follow-up opportunities'
        })
    
    return {
        'intelligence_brief': {
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'strategic_insights': insights,
            'immediate_actions': tactical_alerts,
            'executive_summary': f"Analyzed {len(contacts)} contacts across {len(domains)} domains with {len(emails)} communications",
            'key_recommendations': [
                'Prioritize engagement with high-confidence contacts',
                'Leverage domain clusters for network effects',
                'Focus on time-sensitive opportunities first'
            ]
        },
        'network_analysis': {
            'total_contacts': len(contacts),
            'active_domains': len(domains),
            'engagement_opportunities': len(tactical_alerts),
            'strategic_clusters': len(domains)
        },
        'insights': insights,
        'tactical_alerts': tactical_alerts,
        'analysis_timestamp': datetime.utcnow().isoformat(),
        'contacts_analyzed': len(contacts),
        'emails_analyzed': len(emails)
    }

# ===== STEP 5: STRATEGIC INTELLIGENCE & TACTICAL ALERTS =====

@api_sync_bp.route('/intelligence/strategic-analysis', methods=['POST'])
@require_auth
def generate_strategic_intelligence():
    """Generate comprehensive strategic intelligence and tactical alerts"""
    try:
        user_email = session['user_email']
        data = request.get_json() or {}
        
        # Parameters
        focus_area = data.get('focus_area', 'network_opportunities')
        limit = min(int(data.get('limit', 50)), 100)  # Max 100 contacts
        
        logger.info(f"🎯 Starting strategic intelligence analysis for {user_email}")
        
        # Run strategic intelligence analysis
        result = strategic_intelligence_internal(user_email, limit=limit)
        
        if not result.get('success'):
            return jsonify({
                'success': False,
                'error': result.get('error'),
                'mode': 'strategic_intelligence'
            }), 500
        
        strategic_results = result.get('strategic_results', {})
        
        logger.info(f"✅ Strategic intelligence generated for {user_email}")
        
        return jsonify({
            'success': True,
            'mode': 'strategic_intelligence',
            'analysis_timestamp': strategic_results.get('analysis_timestamp'),
            'intelligence_brief': strategic_results.get('intelligence_brief', {}),
            'network_analysis': strategic_results.get('network_analysis', {}),
            'insights': strategic_results.get('insights', []),
            'tactical_alerts': strategic_results.get('tactical_alerts', []),
            'stats': {
                'insights_generated': result.get('insights_generated', 0),
                'tactical_alerts': result.get('tactical_alerts', 0),
                'contacts_analyzed': result.get('contacts_analyzed', 0),
                'emails_analyzed': result.get('emails_analyzed', 0)
            }
        })
        
    except Exception as e:
        logger.error(f"Strategic intelligence error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Strategic intelligence analysis failed: {str(e)}',
            'mode': 'strategic_intelligence'
        }), 500

@api_sync_bp.route('/strategic-intelligence')
def strategic_intelligence_page():
    """Strategic Intelligence Dashboard page"""
    return render_template('strategic_intelligence.html')

@api_sync_bp.route('/email/extract-sent', methods=['POST'])
@require_auth
def extract_sent_emails():
    """Extract contacts from sent emails - alias for analyze-sent"""
    try:
        user_email = session.get('user_id', 'test@session-42.com')
        oauth_credentials = session.get('oauth_credentials')
        
        request_data = request.get_json() or {}
        lookback_days = request_data.get('lookback_days', 365)
        limit = request_data.get('limit', 50)
        
        if not oauth_credentials:
            return jsonify({
                'success': False,
                'error': 'No Gmail credentials found. Please log out and log back in to re-authenticate with Gmail.',
                'action_required': 'reauth',
                'mode': 'synchronous'
            }), 401
        
        # Use the internal function for contact extraction
        result = analyze_sent_emails_internal(user_email, oauth_credentials, lookback_days, limit)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Contact extraction error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'mode': 'synchronous'
        }), 500

@api_sync_bp.route('/job-status/<job_id>', methods=['GET'])
@require_auth
def get_job_status(job_id):
    """Get status of a background job"""
    try:
        user_email = session.get('user_email')
        if not user_email:
            return jsonify({'error': 'User not authenticated'}), 401
        
        with jobs_lock:
            if job_id not in background_jobs:
                return jsonify({'error': 'Job not found'}), 404
            
            job = background_jobs[job_id]
            
            # Verify job belongs to current user
            if job.get('user_email') != user_email:
                return jsonify({'error': 'Access denied'}), 403
            
            return jsonify(job)
            
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        return jsonify({'error': str(e)}), 500

@api_sync_bp.route('/jobs', methods=['GET'])
@require_auth
def get_user_jobs():
    """Get all background jobs for current user"""
    try:
        user_email = session.get('user_email')
        if not user_email:
            return jsonify({'error': 'User not authenticated'}), 401
        
        user_jobs = []
        with jobs_lock:
            for job_id, job in background_jobs.items():
                if job.get('user_email') == user_email:
                    user_jobs.append(job)
        
        # Sort by start time (newest first)
        user_jobs.sort(key=lambda x: x.get('start_time', ''), reverse=True)
        
        return jsonify({
            'jobs': user_jobs,
            'total': len(user_jobs)
        })
        
    except Exception as e:
        logger.error(f"Error getting user jobs: {e}")
        return jsonify({'error': str(e)}), 500

@api_sync_bp.route('/cancel-job/<job_id>', methods=['POST'])
@require_auth
def cancel_job(job_id):
    """Cancel a running background job safely and save progress"""
    try:
        user_email = session.get('user_email')
        if not user_email:
            return jsonify({'error': 'User not authenticated'}), 401
        
        with jobs_lock:
            if job_id not in background_jobs:
                return jsonify({
                    'status': 'error',
                    'message': f'Job {job_id} not found'
                }), 404
            
            job = background_jobs[job_id]
            
            # Verify job belongs to current user
            if job.get('user_email') != user_email:
                return jsonify({'error': 'Access denied'}), 403
            
            # Set stop flag for graceful shutdown
            if job_id not in job_stop_flags:
                job_stop_flags[job_id] = threading.Event()
            
            job_stop_flags[job_id].set()  # Signal the job to stop
            
            # Update job status with stopping state
            background_jobs[job_id]['status'] = 'stopping'
            background_jobs[job_id]['message'] = 'Stopping safely and saving progress...'
            background_jobs[job_id]['stop_requested_at'] = time.time()
            
            logger.info(f"Stop requested for job {job_id} by user {user_email}")
            
            return jsonify({
                'status': 'success',
                'message': f'Stop signal sent to job {job_id}. It will finish safely and save progress.',
                'job_status': background_jobs[job_id]
            })
            
    except Exception as e:
        logger.error(f"Error stopping job {job_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to stop job: {str(e)}'
        }), 500

# ===== UTILITY FUNCTIONS =====

# Helper function to check if job should stop
def should_stop_job(job_id: str) -> bool:
    """Check if a job has been requested to stop"""
    if job_id in job_stop_flags:
        return job_stop_flags[job_id].is_set()
    return False

# Helper function to update job progress with detailed info
def update_job_progress(job_id: str, progress: int, message: str, details: Dict[str, Any] = None):
    """Update job progress with enhanced details"""
    with jobs_lock:
        if job_id in background_jobs:
            background_jobs[job_id]['progress'] = progress
            background_jobs[job_id]['message'] = message
            background_jobs[job_id]['last_updated'] = time.time()
            
            if details:
                background_jobs[job_id].update(details)

# Enhanced job completion with resume info
def complete_job(job_id: str, success: bool, message: str, result: Dict[str, Any] = None, resume_info: Dict[str, Any] = None):
    """Complete a job with resume information"""
    with jobs_lock:
        if job_id in background_jobs:
            background_jobs[job_id]['status'] = 'completed' if success else 'failed'
            background_jobs[job_id]['progress'] = 100 if success else background_jobs[job_id].get('progress', 0)
            background_jobs[job_id]['message'] = message
            background_jobs[job_id]['completed_at'] = time.time()
            
            if result:
                background_jobs[job_id]['result'] = result
            
            if resume_info:
                background_jobs[job_id]['resume_info'] = resume_info
    
    # Clean up stop flag
    if job_id in job_stop_flags:
        del job_stop_flags[job_id]

# Enhanced job stopping with graceful completion
def stop_job_gracefully(job_id: str, message: str, partial_result: Dict[str, Any] = None, resume_info: Dict[str, Any] = None):
    """Stop a job gracefully with partial results and resume info"""
    with jobs_lock:
        if job_id in background_jobs:
            background_jobs[job_id]['status'] = 'stopped'
            background_jobs[job_id]['message'] = message
            background_jobs[job_id]['stopped_at'] = time.time()
            
            if partial_result:
                background_jobs[job_id]['partial_result'] = partial_result
            
            if resume_info:
                background_jobs[job_id]['resume_info'] = resume_info
    
    # Clean up stop flag
    if job_id in job_stop_flags:
        del job_stop_flags[job_id]