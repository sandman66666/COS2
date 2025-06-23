"""
Synchronous API Routes for Strategic Intelligence System
=======================================================
Flask-compatible routes without async/event loop conflicts
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from flask import Blueprint, request, jsonify, current_app, session
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
import google.auth.exceptions

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
                'has_augmentation': 'enrichment_data' in metadata or 'enrichment_method' in metadata or metadata.get('enrichment_status') == 'enriched',
                'enrichment_status': metadata.get('enrichment_status', 'enriched' if 'enrichment_data' in metadata else 'not_enriched')
            }
            contact_list.append(contact_data)
        
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
    """Email sync with real Gmail integration (synchronous)"""
    try:
        user_email = session.get('user_id', 'test@session-42.com')
        request_data = request.get_json() or {}
        days = request_data.get('days', 30)
        
        # Import Gmail client and make it work synchronously
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        
        from datetime import datetime, timedelta
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        import time
        import base64
        import email
        
        storage_manager = get_storage_manager_sync()
        user = storage_manager.get_user_by_email(user_email)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'mode': 'synchronous'
            }), 404
        
        user_id = user['id']
        
        # Get OAuth credentials from session
        oauth_credentials = session.get('oauth_credentials')
        if not oauth_credentials:
            return jsonify({
                'success': False,
                'error': 'No Gmail credentials. Please re-authenticate.',
                'mode': 'synchronous'
            }), 401
        
        # Create credentials object
        credentials = Credentials(
            token=oauth_credentials.get('access_token'),
            refresh_token=oauth_credentials.get('refresh_token'),
            token_uri=oauth_credentials.get('token_uri', "https://oauth2.googleapis.com/token"),
            client_id=oauth_credentials.get('client_id'),
            client_secret=oauth_credentials.get('client_secret'),
            scopes=oauth_credentials.get('scopes', [])
        )
        
        # Build Gmail service
        service = build('gmail', 'v1', credentials=credentials)
        
        # Calculate date range
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = f'after:{cutoff_date.strftime("%Y/%m/%d")}'
        
        # Get messages
        messages_response = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=min(100, 500)  # Reasonable limit for sync
        ).execute()
        
        messages = messages_response.get('messages', [])
        
        processed_count = 0
        new_emails = 0
        updated_emails = 0
        
        # Process each message
        for msg in messages:
            try:
                # Get full message
                msg_data = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
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
                
                # Parse date
                try:
                    if date_str:
                        date_sent = email.utils.parsedate_to_datetime(date_str)
                    else:
                        date_sent = datetime.utcnow()
                except:
                    date_sent = datetime.utcnow()
                
                # Extract body
                body_text = ""
                if 'payload' in msg_data:
                    payload = msg_data['payload']
                    if 'parts' in payload:
                        for part in payload['parts']:
                            if part.get('mimeType') == 'text/plain' and 'body' in part and 'data' in part['body']:
                                try:
                                    body_text = base64.urlsafe_b64decode(
                                        part['body']['data'].encode('ASCII')).decode('utf-8', errors='replace')
                                    break
                                except:
                                    pass
                    elif 'body' in payload and 'data' in payload['body']:
                        if payload.get('mimeType') == 'text/plain':
                            try:
                                body_text = base64.urlsafe_b64decode(
                                    payload['body']['data'].encode('ASCII')).decode('utf-8', errors='replace')
                            except:
                                pass
                
                # Store email
                metadata = {
                    'subject': subject,
                    'from': from_addr,
                    'to': to_addr,
                    'date': date_str,
                    'headers': headers
                }
                
                # Check if email exists
                existing = storage_manager.postgres.get_email_by_gmail_id(user_id, msg['id'])
                if existing:
                    updated_emails += 1
                else:
                    # Store new email
                    storage_manager.postgres.store_email(
                        user_id=user_id,
                        gmail_id=msg['id'],
                        content=body_text,
                        metadata=metadata,
                        timestamp=date_sent
                    )
                    new_emails += 1
                
                processed_count += 1
                
                # Throttle to avoid quota issues
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error processing email {msg.get('id')}: {e}")
                continue
        
        logger.info(f"Email sync completed for user {user_email}", 
                   processed=processed_count, new=new_emails, updated=updated_emails)
        
        return jsonify({
            'success': True,
            'message': f'Successfully synced {processed_count} emails',
            'stats': {
                'processed': processed_count,
                'new_emails': new_emails,
                'updated_emails': updated_emails,
                'days_synced': days,
                'total_found': len(messages)
            },
            'mode': 'synchronous'
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
    """Sent email analysis with real Gmail integration (synchronous)"""
    try:
        user_email = session.get('user_id', 'test@session-42.com')
        request_data = request.get_json() or {}
        lookback_days = request_data.get('lookback_days', 365)
        
        # Import required modules
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        
        from datetime import datetime, timedelta
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        import time
        import base64
        import email
        import re
        
        storage_manager = get_storage_manager_sync()
        user = storage_manager.get_user_by_email(user_email)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'mode': 'synchronous'
            }), 404
        
        user_id = user['id']
        
        # Get OAuth credentials from session
        oauth_credentials = session.get('oauth_credentials')
        if not oauth_credentials:
            return jsonify({
                'success': False,
                'error': 'No Gmail credentials. Please re-authenticate.',
                'mode': 'synchronous'
            }), 401
        
        # Create credentials object
        credentials = Credentials(
            token=oauth_credentials.get('access_token'),
            refresh_token=oauth_credentials.get('refresh_token'),
            token_uri=oauth_credentials.get('token_uri', "https://oauth2.googleapis.com/token"),
            client_id=oauth_credentials.get('client_id'),
            client_secret=oauth_credentials.get('client_secret'),
            scopes=oauth_credentials.get('scopes', [])
        )
        
        # Build Gmail service
        service = build('gmail', 'v1', credentials=credentials)
        
        # Calculate date range for sent emails
        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
        query = f'in:sent after:{cutoff_date.strftime("%Y/%m/%d")}'
        
        # Get sent messages
        messages_response = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=min(500, 1000)  # Analyze more sent emails for contact extraction
        ).execute()
        
        messages = messages_response.get('messages', [])
        
        # Extract contacts from sent emails
        contacts = {}
        emails_processed = 0
        
        for msg in messages:
            try:
                # Get full message
                msg_data = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()
                
                # Parse message headers
                headers = {}
                for header in msg_data.get('payload', {}).get('headers', []):
                    name = header.get('name', '').lower()
                    value = header.get('value', '')
                    headers[name] = value
                
                # Extract recipient emails
                to_addresses = []
                cc_addresses = []
                
                # Parse TO field
                to_header = headers.get('to', '')
                if to_header:
                    to_addresses.extend(re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', to_header))
                
                # Parse CC field
                cc_header = headers.get('cc', '')
                if cc_header:
                    cc_addresses.extend(re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', cc_header))
                
                # Process all recipient addresses
                all_recipients = to_addresses + cc_addresses
                
                for email_addr in all_recipients:
                    email_addr = email_addr.lower().strip()
                    
                    # Skip own email
                    if email_addr == user_email.lower():
                        continue
                    
                    # Extract domain
                    domain = email_addr.split('@')[1] if '@' in email_addr else ''
                    
                    # Determine trust tier based on frequency and domain
                    if email_addr not in contacts:
                        contacts[email_addr] = {
                            'email': email_addr,
                            'name': '',  # Will be extracted from display name if available
                            'domain': domain,
                            'frequency': 0,
                            'trust_tier': 'tier_3',  # Default
                            'last_contact': None,
                            'metadata': {}
                        }
                    
                    contacts[email_addr]['frequency'] += 1
                    
                    # Extract name from display name
                    display_name_match = re.search(r'"?([^"<>]+)"?\s*<' + re.escape(email_addr) + '>', 
                                                  to_header + ' ' + cc_header, re.IGNORECASE)
                    if display_name_match and not contacts[email_addr]['name']:
                        contacts[email_addr]['name'] = display_name_match.group(1).strip()
                
                emails_processed += 1
                
                # Throttle to avoid quota issues
                time.sleep(0.05)
                
            except Exception as e:
                logger.error(f"Error processing sent email {msg.get('id')}: {e}")
                continue
        
        # Determine trust tiers based on frequency
        contact_list = list(contacts.values())
        contact_list.sort(key=lambda x: x['frequency'], reverse=True)
        
        # Assign trust tiers
        total_contacts = len(contact_list)
        for i, contact in enumerate(contact_list):
            if i < total_contacts * 0.1:  # Top 10%
                contact['trust_tier'] = 'tier_1'
            elif i < total_contacts * 0.3:  # Top 30%
                contact['trust_tier'] = 'tier_2'
            else:
                contact['trust_tier'] = 'tier_3'
        
        # Store contacts in database
        stored_contacts = 0
        for contact in contact_list:
            try:
                # Check if contact exists
                existing = storage_manager.postgres.get_contact_by_email(user_id, contact['email'])
                if existing:
                    # Update frequency and trust tier
                    storage_manager.postgres.update_contact(
                        contact_id=existing['id'],
                        frequency=contact['frequency'],
                        trust_tier=contact['trust_tier'],
                        metadata=contact['metadata']
                    )
                else:
                    # Create new contact
                    storage_manager.postgres.store_contact(
                        user_id=user_id,
                        email=contact['email'],
                        name=contact['name'] or contact['email'].split('@')[0],
                        trust_tier=contact['trust_tier'],
                        frequency=contact['frequency'],
                        domain=contact['domain'],
                        metadata=contact['metadata']
                    )
                
                stored_contacts += 1
                
            except Exception as e:
                logger.error(f"Error storing contact {contact['email']}: {e}")
                continue
        
        # Generate statistics
        stats = {
            'total_contacts': len(contact_list),
            'emails_processed': emails_processed,
            'domains_found': len(set(c['domain'] for c in contact_list if c['domain'])),
            'trust_tier_1': len([c for c in contact_list if c['trust_tier'] == 'tier_1']),
            'trust_tier_2': len([c for c in contact_list if c['trust_tier'] == 'tier_2']),
            'trust_tier_3': len([c for c in contact_list if c['trust_tier'] == 'tier_3']),
            'stored_contacts': stored_contacts,
            'lookback_days': lookback_days
        }
        
        logger.info(f"Sent email analysis completed for user {user_email}", stats=stats)
        
        return jsonify({
            'success': True,
            'message': f'Successfully analyzed {emails_processed} sent emails and found {len(contact_list)} contacts',
            'stats': stats,
            'contacts': contact_list[:50],  # Return first 50 for preview
            'mode': 'synchronous'
        })
        
    except Exception as e:
        logger.error(f"Sent email analysis error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'mode': 'synchronous'
        }), 500

@api_sync_bp.route('/intelligence/enrich-contacts', methods=['POST'])
@require_auth  
def enrich_contacts():
    """Contact enrichment with real processing (synchronous)"""
    try:
        user_email = session.get('user_id', 'test@session-42.com')
        request_data = request.get_json() or {}
        limit = request_data.get('limit', 50)
        
        storage_manager = get_storage_manager_sync()
        user = storage_manager.get_user_by_email(user_email)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'mode': 'synchronous'
            }), 404
        
        user_id = user['id']
        
        # Get contacts that need enrichment
        contacts, total = storage_manager.get_contacts(user_id, limit=limit)
        
        if not contacts:
            return jsonify({
                'success': True,
                'message': 'No contacts found to enrich',
                'stats': {
                    'contacts_processed': 0,
                    'successfully_enriched': 0,
                    'failed_count': 0,
                    'success_rate': 0,
                    'sources_used': 0
                },
                'mode': 'synchronous'
            })
        
        # Import the real contact enrichment service
        import sys
        import os
        import asyncio
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        
        from intelligence.d_enrichment.contact_enrichment_integration import ContactEnrichmentService
        
        # Use the real enrichment service
        async def run_real_enrichment():
            enrichment_service = ContactEnrichmentService(user_id)
            try:
                # Initialize the service
                await enrichment_service.initialize()
                
                # Convert contacts to the format expected by the enricher
                contact_list = []
                for contact in contacts:
                    contact_dict = {
                        'email': contact.get('email', ''),
                        'name': contact.get('name', ''),
                        'domain': contact.get('domain', ''),
                        'trust_tier': contact.get('trust_tier', 'tier_3'),
                        'frequency': contact.get('frequency', 0)
                    }
                    contact_list.append(contact_dict)
                
                # Perform batch enrichment with real processing
                enrichment_results = await enrichment_service.enrich_contacts_batch(
                    contact_list, 
                    max_concurrent=2  # Conservative rate limiting
                )
                
                # Calculate statistics
                successful = sum(1 for result in enrichment_results.values() if result.get('success', False))
                failed = len(enrichment_results) - successful
                success_rate = successful / len(enrichment_results) if enrichment_results else 0
                
                # Count unique data sources used
                data_sources = set()
                for result in enrichment_results.values():
                    if result.get('success') and result.get('data_sources'):
                        data_sources.update(result['data_sources'])
                
                return {
                    'contacts_processed': len(enrichment_results),
                    'successfully_enriched': successful,
                    'failed_count': failed,
                    'success_rate': success_rate,
                    'sources_used': len(data_sources),
                    'enrichment_results': enrichment_results
                }
                
            finally:
                await enrichment_service.cleanup()
        
        # Run the async enrichment in a synchronous context
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            stats = loop.run_until_complete(run_real_enrichment())
            loop.close()
        except Exception as e:
            logger.error(f"Real contact enrichment failed: {e}")
            # Fallback to basic enrichment if real one fails
            stats = {
                'contacts_processed': len(contacts),
                'successfully_enriched': 0,
                'failed_count': len(contacts),
                'success_rate': 0.0,
                'sources_used': 0,
                'error': f"Advanced enrichment failed: {str(e)}"
            }
        
        logger.info(f"Contact enrichment completed for user {user_email}", stats=stats)
        
        return jsonify({
            'success': True,
            'message': f'Successfully enriched {stats["successfully_enriched"]} of {stats["contacts_processed"]} contacts using real intelligence',
            'stats': stats,
            'mode': 'synchronous_with_real_intelligence'
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
                # Parse metadata which contains enrichment data
                metadata = json.loads(contact.get('metadata', '{}')) if contact.get('metadata') else {}
                enrichment_data = metadata.get('enrichment_data', {})
                
                if format_type == 'detailed':
                    # Detailed format with all enrichment data
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
                            'person_data': enrichment_data.get('person_data', {}),
                            'company_data': enrichment_data.get('company_data', {}),
                            'enrichment_timestamp': enrichment_data.get('enrichment_timestamp'),
                            'intelligence_summary': enrichment_data.get('intelligence_summary', {})
                        }
                    }
                else:
                    # Summary format with key insights only
                    person_data = enrichment_data.get('person_data', {})
                    company_data = enrichment_data.get('company_data', {})
                    
                    contact_result = {
                        'email': contact.get('email'),
                        'name': contact.get('name') or person_data.get('name', ''),
                        'title': person_data.get('title', ''),
                        'company': company_data.get('name', ''),
                        'industry': company_data.get('industry', ''),
                        'confidence': enrichment_data.get('confidence_score', 0),
                        'sources': len(enrichment_data.get('data_sources', [])),
                        'enriched': bool(enrichment_data)
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
                # Parse metadata which contains enrichment data
                metadata = json.loads(contact.get('metadata', '{}')) if contact.get('metadata') else {}
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
                    
                    contact_result = {
                        'email': contact.get('email'),
                        'name': contact.get('name') or person_data.get('name', ''),
                        'title': person_data.get('title', ''),
                        'company': company_data.get('name', ''),
                        'industry': company_data.get('industry', ''),
                        'seniority_level': person_data.get('seniority_level', ''),
                        'confidence_score': enrichment_data.get('confidence_score', 0),
                        'data_sources': enrichment_data.get('data_sources', []),
                        'trust_tier': contact.get('trust_tier'),
                        'frequency': contact.get('frequency'),
                        'enrichment_timestamp': enrichment_data.get('enrichment_timestamp')
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